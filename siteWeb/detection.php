<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Face Recognition — Detect</title>
    <link rel="stylesheet" href="style.css">
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
        .detection-wrapper video { transform: scaleX(-1); } /* mirror selfie view */
        .detection-wrapper { aspect-ratio: 4 / 3; }
    </style>
</head>
<body>

<?php include("navbar.php"); ?>

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
    </div>

    <div class="footer">
        <p>Project curricular internship 2026 by Anthony Miranda and Lea Carminati for Dell Technologies Montpellier</p>
    </div>

</div>

<script src="detection.js"></script>
</body>
</html>