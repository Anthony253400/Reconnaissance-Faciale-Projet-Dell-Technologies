<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Face Recognition — Detect</title>
    <link rel="stylesheet" href="style.css">

    <script src="navbar.js"></script>

    <style>
:root {
  --bg:           #f4f4f1;
  --surface:      #ffffff;
  --border:       #e4e4e0;
  --border-focus: #1a1a1a;
  --text:         #1a1a1a;
  --text-muted:   #888884;
  --accent:       #1a1a1a;
  --accent-hover: #333333;
  --accent-light: #f0f0ec;
  --dell-blue:    #0076CE;
  --dell-blue-soft: #e6f4fc;
  --dell-blue-bg: #e8f3fb;
  --success:      #16a34a;
  --radius:       12px;
  --radius-sm:    7px;
  --shadow:       0 1px 3px rgba(0,0,0,.05), 0 4px 16px rgba(0,0,0,.04);
  --font:         'DM Sans', sans-serif;
  --ease:         140ms ease;
  --navbar-h:     60px;
}
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: var(--navbar-h);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 1.25rem; 
}

.navbar-inner {
  max-width: 1500px; 
  width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  color: var(--dell-blue);
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex;
  gap: 6px;
}

.nav-link {
  font-size: 0.9375rem;
  font-weight: 400;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  color: var(--text-muted);
  text-decoration: none;
  transition: background var(--ease), color var(--ease), border-color var(--ease);
}

.nav-link:hover {
  background: var(--accent-light);
  color: var(--text);
}

.nav-link.active {
  background: var(--dell-blue-bg);
  color: var(--dell-blue);
  border-color: rgba(0, 118, 206, 0.2);
  font-weight: 500;
}

.nav-brand-link:hover {
  background: transparent;
}@import url('variables/variables.css');

.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: var(--navbar-h);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 1.25rem; 
}

.navbar-inner {
  max-width: 1500px; 
  width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  color: var(--dell-blue);
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex;
  gap: 6px;
}

.nav-link {
  font-size: 0.9375rem;
  font-weight: 400;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  color: var(--text-muted);
  text-decoration: none;
  transition: background var(--ease), color var(--ease), border-color var(--ease);
}

.nav-link:hover {
  background: var(--accent-light);
  color: var(--text);
}

.nav-link.active {
  background: var(--dell-blue-bg);
  color: var(--dell-blue);
  border-color: rgba(0, 118, 206, 0.2);
  font-weight: 500;
}

.nav-brand-link:hover {
  background: transparent;
}@import url('variables/variables.css');

.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: var(--navbar-h);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 1.25rem; 
}

.navbar-inner {
  max-width: 1500px; 
  width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  color: var(--dell-blue);
  font-size: 1.0625rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex;
  gap: 6px;
}

.nav-link {
  font-size: 0.9375rem;
  font-weight: 400;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  color: var(--text-muted);
  text-decoration: none;
  transition: background var(--ease), color var(--ease), border-color var(--ease);
}

.nav-link:hover {
  background: var(--accent-light);
  color: var(--text);
}

.nav-link.active {
  background: var(--dell-blue-bg);
  color: var(--dell-blue);
  border-color: rgba(0, 118, 206, 0.2);
  font-weight: 500;
}

.nav-brand-link:hover {
  background: transparent;
}



        .detection-wrapper {
            position: relative;
            width: 1100px;
            height: 620px;
            margin: 0 auto ;
        }
        .detection-wrapper video,
        .detection-wrapper canvas {
            position: absolute;
            top: 0; left: 0;
            pointer-events: none;
        }
    </style>
</head>
<body>
<div class="container">
    <nav class="navbar">
    <div class="navbar-inner">
        <a  href="index.php" class = nav-link> <span class="nav-brand">Face Recognition</span> </a>
        
        <div class="nav-links">
            <a href="index.php" class="nav-link">Home</a>
            <a href="register.php" class="nav-link active">Register</a>
            <a href="statistics.php" class="nav-link">Statistics</a>
            <a href="detection.php" class="nav-link">Detect</a>

        </div>
    </div>
</nav>




    <div class="section-card">
        <h2>Detect Faces</h2>


        <div class="detection-wrapper">
            <img id="feed" style="border-radius: 8px; width:20 ;height:20 ;max-width: 100%;">
        </div>


        <canvas id="capture" width="20" height="20" style="display:none;"></canvas>


        <div class="btn-row">
            <a href="index.html" class="btn btn-secondary">Back to Add Person</a>
        </div>
    </div>


    <div class="footer">
        <p>Project curricular internship 2026 by Anthony Miranda and Lea Carminati for Dell Technologies Montpellier</p>  
    </div>


</div>
<script src="vidéo.js"></script>
</body>
</html>



