<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Smoke Density Estimation & Air Quality Monitor</title>
  <link rel="stylesheet" href="/static/css/style.css" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>

<div class="app">

  <!-- ── HEADER ── -->
  <header>
    <div class="header-inner">
      <div class="badge">Image Processing &amp; Computer Vision — Final Year Project</div>
      <h1>Smoke Density Estimation<br><span>&amp; Air Quality Monitoring</span></h1>
      <p class="subline">Laplacian Variance Clarity Metric &nbsp;|&nbsp; Otsu Threshold Segmentation &nbsp;|&nbsp; AQI Estimation</p>
    </div>
  </header>

  <!-- ── UPLOAD ── -->
  <section class="upload-section">
    <div id="drop-zone" class="drop-zone">
      <div class="drop-icon">📷</div>
      <p class="drop-title">Drop an image here or click to browse</p>
      <p class="drop-sub">Supports PNG, JPG, BMP, TIFF — max 16 MB</p>
      <label class="browse-btn">
        Choose Image
        <input type="file" id="file-input" accept="image/*" hidden />
      </label>
    </div>
  </section>

  <!-- ── LOADING ── -->
  <div id="loading" class="loading hidden">
    <div class="spinner"></div>
    <p>Running algorithms...</p>
  </div>

  <!-- ── RESULTS ── -->
  <section id="results" class="results hidden">

    <!-- Metric Cards -->
    <div class="metrics-grid">
      <div class="metric-card aqi">
        <div class="metric-label">AQI Index</div>
        <div class="metric-val" id="r-aqi">—</div>
        <div class="metric-cat" id="r-aqi-cat">—</div>
      </div>
      <div class="metric-card lap">
        <div class="metric-label">Laplacian Variance</div>
        <div class="metric-val" id="r-lap">—</div>
        <div class="metric-cat">clarity score</div>
      </div>
      <div class="metric-card dens">
        <div class="metric-label">Smoke Density</div>
        <div class="metric-val" id="r-dens">—</div>
        <div class="metric-cat">pixel coverage</div>
      </div>
      <div class="metric-card thr">
        <div class="metric-label">Otsu Threshold</div>
        <div class="metric-val" id="r-thr">—</div>
        <div class="metric-cat">optimal T*</div>
      </div>
      <div class="metric-card mean">
        <div class="metric-label">Mean Intensity</div>
        <div class="metric-val" id="r-mean">—</div>
        <div class="metric-cat">brightness level</div>
      </div>
    </div>

    <!-- AQI Bar -->
    <div class="aqi-bar-section">
      <div class="aqi-bar-labels">
        <span>0 Good</span><span>100 Moderate</span><span>200 Unhealthy</span><span>300 Very Unhealthy</span><span>500 Hazardous</span>
      </div>
      <div class="aqi-track">
        <div id="aqi-bar-fill" class="aqi-bar-fill"></div>
        <div id="aqi-marker" class="aqi-marker"></div>
      </div>
    </div>

    <!-- Image Grid -->
    <div class="img-grid">
      <div class="img-panel">
        <div class="img-label">Original Image</div>
        <img id="img-original" src="" alt="Original" />
      </div>
      <div class="img-panel">
        <div class="img-label">Laplacian Edge Map</div>
        <img id="img-lap" src="" alt="Laplacian" />
        <div class="img-note">High-frequency detail loss indicates smoke/haze</div>
      </div>
      <div class="img-panel">
        <div class="img-label">Otsu Threshold Mask</div>
        <img id="img-thresh" src="" alt="Threshold" />
        <div class="img-note">White = smoke pixels, Black = clear background</div>
      </div>
      <div class="img-panel">
        <div class="img-label">Smoke Density Overlay</div>
        <img id="img-density" src="" alt="Density map" />
        <div class="img-note">Red regions = detected smoke / haze areas</div>
      </div>
    </div>

    <!-- Histogram -->
    <div class="histogram-section">
      <div class="section-title">Pixel Intensity Histogram
        <span class="section-note">Blue = below threshold (clear) &nbsp;|&nbsp; Red = above threshold (smoke) &nbsp;|&nbsp; Yellow line = Otsu T*</span>
      </div>
      <div class="hist-wrap">
        <canvas id="histogram-chart"></canvas>
      </div>
    </div>

    <!-- Algorithm Explanation -->
    <div class="algo-section">
      <div class="algo-card">
        <div class="algo-title">Algorithm 1 — Laplacian Variance Clarity Metric</div>
        <div class="algo-formula">Var(∇²I) = Σ(L(x,y) − μ)² / N</div>
        <p>The Laplacian operator computes the second-order spatial derivative of the grayscale image.
           In clear images, edges are sharp, producing high variance. Smoke scatters light and blurs
           edges, reducing variance. A low Laplacian variance directly indicates poor image clarity
           due to haze or smoke.</p>
        <div class="algo-kernel">
          Kernel: &nbsp;
          <code>[ 0  1  0 ]<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ 1 -4  1 ]<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ 0  1  0 ]</code>
        </div>
      </div>
      <div class="algo-card">
        <div class="algo-title">Algorithm 2 — Otsu Threshold Segmentation</div>
        <div class="algo-formula">T* = argmax [ω₀(t)·ω₁(t)·(μ₀(t)−μ₁(t))²]</div>
        <p>Otsu's method automatically finds the optimal threshold T* by maximising the
           inter-class variance between smoke pixels (bright, high intensity) and background
           pixels (darker). No manual tuning required. The binary mask separates haze regions
           from clear areas, enabling accurate density measurement.</p>
        <div class="algo-kernel">
          <code>σ²_B(t) = ω₀·ω₁·(μ₀ − μ₁)²</code>
        </div>
      </div>
    </div>

    <!-- Reset -->
    <div class="reset-row">
      <button id="reset-btn" onclick="resetApp()">↩ Analyze Another Image</button>
    </div>

  </section>
</div>

<script src="/static/js/main.js"></script>
</body>
</html>
