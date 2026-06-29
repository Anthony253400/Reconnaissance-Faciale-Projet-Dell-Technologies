<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition  Register</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">

    <script src="assets/js/navbar.js"></script>
    

    <style>
        .btn-capture-wrap { position: relative; width: 72px; height: 72px; display: flex; align-items: center; justify-content: center; }
        .capture-ring { position: absolute; top: 0; left: 0; width: 72px; height: 72px; transform: rotate(-90deg); pointer-events: none; }
        .capture-ring-bg { fill: none; stroke: rgba(255,255,255,0.25); stroke-width: 3; }
        .capture-ring-prog { fill: none; stroke: #0076CE; stroke-width: 7; stroke-linecap: round; stroke-dasharray: 201.06; stroke-dashoffset: 201.06; transition: stroke-dashoffset 0.12s linear; }
        .steps-list li strong {
            white-space: nowrap;
            color: var(--text);
            font-weight: 500;
        }
        #countdown-num {
            background: rgba(0, 118, 206, 0.5);
            border: 2px solid rgba(147, 197, 253, 0.8);
            color: #bfdbfe;
            padding: 10px 28px;
            border-radius: 999px;
        }
    </style>
</head>
<body>

<?php include("components/navbar.php"); ?>

<div class="container">

    <header class="page-header">
        <h1>Register a person</h1>
        <p class="subtitle">Add someone to the recognition database</p>
    </header>

    <!-- HOW TO USE -->
    <div class="section-card">
        <h2>How to use</h2>
        <ol class="steps-list">
            <li><strong>Allow camera access:</strong> when your browser asks, click "Allow". You should see yourself in the video below.</li>
            <li><strong>Center your face:</strong> position yourself so your face fills the middle of the frame, with good, even lighting and no strong backlight.</li>
            <li><strong>Press the round button to start.</strong> A 3-second countdown will appear, so get ready.</li>
            <li><strong>Move your head slowly</strong> during the recording (about 5 seconds): turn left, then right, then look up and down. This lets us capture your face from every angle for better recognition.</li>
            <li><strong>Fill in the name:</strong> enter the first and last name of the person being registered.</li>
            <li><strong>Accept the privacy policy</strong> and click "Add to database". Then go to Detect page to test recognition.</li>
        </ol>
    </div>

    <!-- REGISTRATION -->
    <div class="section-card">
        <h2>Registration</h2>

        <!-- WEBCAM PANEL -->
        <div id="panel-cam">
            <div class="webcam-wrapper">
                <video id="webcam" autoplay playsinline style="transform: scaleX(-1);"></video>
                <div class="cam-overlay">
                    <div class="cam-overlay-top">
                        <p class="cam-instruction-overlay">Press the button, wait for the countdown, then turn your head left, right, up and down (5 sec)</p>
                        <p class="cam-step-overlay" id="progress"></p>
                    </div>
                    <div id="countdown-overlay" style="display:none; position:absolute; inset:0; align-items:center; justify-content:center; pointer-events:none;">
                        <span id="countdown-num" style="font-size:120px; font-weight:500; color:white; line-height:1;"></span>
                        <span id="countdown-msg" style="display:none; background:rgba(0,118,206,0.5); border:2px solid rgba(147,197,253,0.8); color:#bfdbfe; font-size:16px; font-weight:500; padding:10px 28px; border-radius:999px;"></span>
                    </div>
                    <div class="cam-overlay-bottom">
                        <div class="btn-capture-wrap">
                            <svg class="capture-ring" viewBox="0 0 72 72" aria-hidden="true">
                                <circle class="capture-ring-bg" cx="36" cy="36" r="32"/>
                                <circle class="capture-ring-prog" id="capture-ring" cx="36" cy="36" r="32"/>
                            </svg>
                            <button class="btn-capture" id="btn-record" onclick="startRecording()"></button>
                        </div>
                    </div>
                </div>
            </div>
            <canvas id="canvas" style="display:none;"></canvas>
            <p id="progress" style="text-align:center; margin-top:0.75rem; font-weight:500;"></p>
        </div>

        <!-- UPLOAD PANEL -->
        <?php /* 
        <div id="panel-upload" style="display:none;">
            <div class="upload-zone">
                <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"/></svg>
                <p class="upload-title">Select a photo from your device</p>
                <p class="upload-hint">JPG, PNG - clear face, good lighting</p>
                <div class="form-group" style="margin-top: 0.75rem; margin-bottom: 0;">
                    <input type="file" id="photo" accept="image/*" />
                </div>
            </div>
            
        </div>
        */ ?>
    </div>

    <!-- PERSON DETAILS -->
    <div class="section-card">
        <h2>Person details</h2>
        <div class="name-grid">
            <div class="form-group">
                <label for="firstName">First name</label>
                <input type="text" id="firstName" placeholder="John" />
            </div>
            <div class="form-group">
                <label for="lastName">Last name</label>
                <input type="text" id="lastName" placeholder="Doe" />
            </div>
        </div>
    </div>

    <!-- PRIVACY + SUBMIT -->
    <div class="consent-row">
        <input type="checkbox" id="consent" />
        <label for="consent">I have read and agree to the <a href="privacy.php" target="_blank">privacy policy</a>. My biometric data will only be used for this recognition project.</label>
    </div>

    <div class="btn-row">
        <button class="btn btn-primary" onclick="addPerson()">Add to database</button>
    </div>

    <p id="message"></p>

<?php include("components/footer.php") ;?>

</div>

<script src="assets/js/script.js"></script>
</body>
</html>