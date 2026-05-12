import os
import uuid
import json
import numpy as np
import cv2
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────
#  ALGORITHM 1: Laplacian Variance Clarity Metric
# ─────────────────────────────────────────────
def laplacian_variance(gray):
    """
    Compute the Laplacian variance of a grayscale image.
    High variance = sharp/clear image.
    Low variance  = blurry / smoke-filled image.

    Laplacian kernel:  [ 0  1  0 ]
                       [ 1 -4  1 ]
                       [ 0  1  0 ]
    """
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = laplacian.var()
    return round(float(variance), 4), laplacian


# ─────────────────────────────────────────────
#  ALGORITHM 2: Otsu Threshold Segmentation
# ─────────────────────────────────────────────
def otsu_threshold(gray):
    """
    Otsu's method: finds optimal threshold T* by maximising
    inter-class variance between smoke pixels and background.

    σ²_B(t) = ω₀(t) · ω₁(t) · [μ₀(t) − μ₁(t)]²
    T* = argmax σ²_B(t)
    """
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    otsu_val, binary = cv2.threshold(
        blur, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return int(otsu_val), binary


# ─────────────────────────────────────────────
#  Smoke Density Estimation
# ─────────────────────────────────────────────
def estimate_smoke_density(gray, binary_mask):
    """
    Smoke pixels are bright (high intensity) and detected by threshold.
    Density = fraction of pixels classified as smoke.
    """
    smoke_pixels = np.sum(binary_mask > 0)
    total_pixels = gray.shape[0] * gray.shape[1]
    density = smoke_pixels / total_pixels
    return round(float(density) * 100, 2)


# ─────────────────────────────────────────────
#  AQI Estimation from Density
# ─────────────────────────────────────────────
def estimate_aqi(smoke_density_pct, lap_variance):
    """
    Heuristic AQI model combining smoke density and clarity loss.
    - More smoke density → higher AQI
    - Lower Laplacian variance → more haze → higher AQI
    """
    clarity_penalty = max(0, 1 - min(lap_variance / 500, 1))
    raw = (smoke_density_pct / 100) * 350 + clarity_penalty * 150
    aqi = int(np.clip(raw, 0, 500))

    if aqi <= 50:
        category, color = "Good", "#00e400"
    elif aqi <= 100:
        category, color = "Moderate", "#ffff00"
    elif aqi <= 150:
        category, color = "Unhealthy for Sensitive Groups", "#ff7e00"
    elif aqi <= 200:
        category, color = "Unhealthy", "#ff0000"
    elif aqi <= 300:
        category, color = "Very Unhealthy", "#8f3f97"
    else:
        category, color = "Hazardous", "#7e0023"

    return aqi, category, color


# ─────────────────────────────────────────────
#  Histogram Data
# ─────────────────────────────────────────────
def compute_histogram(gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    return hist.flatten().tolist()


# ─────────────────────────────────────────────
#  Save processed output images
# ─────────────────────────────────────────────
def save_processed_images(gray, laplacian, binary, original_bgr, uid):
    results = {}

    # Laplacian edge map — normalised to 0-255, coloured purple
    lap_norm = cv2.normalize(np.abs(laplacian), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    lap_colour = cv2.applyColorMap(lap_norm, cv2.COLORMAP_MAGMA)
    lap_path = f"static/uploads/{uid}_laplacian.jpg"
    cv2.imwrite(lap_path, lap_colour)
    results['laplacian'] = lap_path

    # Threshold binary mask — blue tint
    thresh_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    thresh_path = f"static/uploads/{uid}_threshold.jpg"
    cv2.imwrite(thresh_path, thresh_bgr)
    results['threshold'] = thresh_path

    # Smoke density overlay — red highlight on detected smoke regions
    overlay = original_bgr.copy()
    smoke_region = binary > 0
    overlay[smoke_region] = (overlay[smoke_region] * 0.3 + np.array([0, 0, 220]) * 0.7).clip(0, 255)
    density_path = f"static/uploads/{uid}_density.jpg"
    cv2.imwrite(density_path, overlay)
    results['density'] = density_path

    return results


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    uid = str(uuid.uuid4())[:8]
    filename = f"{uid}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Load image
    img_bgr = cv2.imread(filepath)
    if img_bgr is None:
        return jsonify({'error': 'Could not read image'}), 400

    # Resize for consistent processing (keeps aspect ratio)
    h, w = img_bgr.shape[:2]
    max_dim = 800
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # ── Run algorithms ──
    lap_var, laplacian_map = laplacian_variance(gray)
    otsu_val, binary_mask  = otsu_threshold(gray)
    smoke_density          = estimate_smoke_density(gray, binary_mask)
    aqi, category, color   = estimate_aqi(smoke_density, lap_var)
    histogram              = compute_histogram(gray)
    processed_paths        = save_processed_images(gray, laplacian_map, binary_mask, img_bgr, uid)

    # Mean pixel intensity (used to gauge brightness / haze level)
    mean_intensity = round(float(gray.mean()), 2)

    return jsonify({
        'original': filepath,
        'laplacian_img': processed_paths['laplacian'],
        'threshold_img': processed_paths['threshold'],
        'density_img':   processed_paths['density'],
        'metrics': {
            'laplacian_variance': lap_var,
            'otsu_threshold':     otsu_val,
            'smoke_density':      smoke_density,
            'mean_intensity':     mean_intensity,
            'aqi':                aqi,
            'aqi_category':       category,
            'aqi_color':          color,
        },
        'histogram': histogram,
    })


@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('static/uploads', filename)


if __name__ == '__main__':
    print("\n🌫️  Smoke Density Estimation & Air Quality Monitor")
    print("   Running at → http://127.0.0.1:5000\n")
    app.run(debug=True)
