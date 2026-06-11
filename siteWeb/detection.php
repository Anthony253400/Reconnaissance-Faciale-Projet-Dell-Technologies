<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Face Recognition — Detect</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">


    <script src="assets/js/navbar.js"></script>

    <style>
        /* {border : red dotted 1px}
        /* riquadro originale — invariato */
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

<?php include("components/navbar.php"); ?>

<div class="container">



    <header class="page-header">
        <h1>Face Recognition</h1>
        <p class="subtitle">Real-time face detection</p>
    </header>


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


<?php include("components/footer.php") ;?>



</div>
<script src="vidéo.js"></script>
</body>
</html>



