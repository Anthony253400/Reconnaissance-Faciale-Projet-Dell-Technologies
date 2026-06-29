<?php $current = "detection"; ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition Detect</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">


    <script src="assets/js/navbar.js"></script>
    <script src="assets/js/detection.js"></script>


    <style>
        .detection-wrapper {
            position: relative;
            width: 960px;
            max-width: 100%;
            margin: 0 auto;
        }
        /* video and overlay are stacked exactly on top of each other */
        .detection-wrapper video,
        .detection-wrapper canvas#overlay {
            position: absolute;
            top: 0; left: 0;
            width: 100%;
            border-radius: 8px;
        }
        .detection-wrapper video {transform: scaleX(-1); } /* mirror selfie view */
        .detection-wrapper { aspect-ratio: 4 / 3; }
    </style>
</head>
<body>

<?php include("components/navbar.php"); ?>

<div class="container">

    <header class="page-header">
        <h1>Face Recognition</h1>
        <p class="subtitle">Real-time face detection</p>
    </header>

    

    <div class="section-card">
        <h2>Detect Faces</h2>

        <div class="detection-wrapper">
            <video id="webcam" autoplay playsinline muted></video>
            <canvas id="overlay"></canvas>
        </div>

        <!-- hidden canvas used to grab frames and send them to the server -->
        <canvas id="capture" style="display:none;"></canvas>

        <div class="btn-row" style="margin-top: 1rem;">
            <a href="register.php" class="btn btn-secondary">Back to Register</a>
        </div>
        
        <p class="home-text" style="margin-top:1rem; font-size:0.85rem;">
        <strong>Privacy:</strong> the video stream and images are never stored on our server.
        Each frame is analysed on the fly and immediately discarded. For more details,
        see our <a href="privacy.php" target="_blank">privacy policy</a>.
        </p>
    </div>
<!-- HOW IT WORKS + LEGEND -->
    <div class="section-card">
        <h2>How detection works</h2>
        <p class="home-text">
            Your webcam streams to the server, which analyses each frame in real time:
            it detects faces, compares them against the registered people, and draws a
            box around each face with the matched name and a confidence score (0 to 1).
        </p>

        <div class="legend">
            <div class="legend-item">
                <span class="legend-dot" style="background:#10b981;"></span>
                Recognised - confident match (score &ge; 0.70)
            </div>
            <div class="legend-item">
                <span class="legend-dot" style="background:#facc15;"></span>
                Uncertain - possible match, low confidence (0.50&ndash;0.70)
            </div>
            <div class="legend-item">
                <span class="legend-dot" style="background:#9ca3af;"></span>
                Not recognised - shown as "unknown" (score &lt; 0.50)
            </div>
        </div>

        <p class="home-text" style="margin-top:1rem;">
            Make sure at least one person has been added from the
            <a href="register.php">Register</a> page first, and stand in good, even lighting.
        </p>        
    
    </div>

<?php include("components/footer.php") ;?>


</div>

<script src="/assets/js/detection.js"></script>
</body>
</html>