<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition — Register</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">

    <script src="assets/js/navbar.js"></script>

</head>
<body>
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
            <li><strong>Choose a method:</strong> we highly recommend using the webcam for better recognition accuracy. Upload from your device is available as an alternative.</li>
            <li><strong>Webcam:</strong> press the button and slowly move your head left, right, up and down. Keep your face centered and well lit.</li>
            <li><strong>Upload:</strong> select a clear, front-facing photo with good lighting. Recognition may be less accurate.</li>
            <li><strong>Fill in the name:</strong> enter the first and last name of the person to register.</li>
            <li><strong>Accept the privacy policy</strong>and click "Add to database". Then go to Detect to test recognition.</li>
        </ol>
    </div>

    <!-- SENDING METHOD -->
    <div class="section-card">
        <h2>Choose a method</h2>

        <div class="method-toggle">
            <button class="method-btn active" id="btn-cam" onclick="switchMethod('cam')">
                <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0ZM18.75 10.5h.008v.008h-.008V10.5Z"/></svg>
                Use webcam  (Recommended)
            </button>
            <?php /*
            <button class="method-btn" id="btn-upload" onclick="switchMethod('upload')">
                <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5"/></svg>
                Upload a photo
            </button>
            */ ;?>
        </div>

        <!-- WEBCAM PANEL -->
        <div id="panel-cam">
            <div class="webcam-wrapper">
                <video id="webcam" autoplay playsinline style="transform: scaleX(-1);"></video>
                <div class="cam-overlay">
                    <div class="cam-overlay-top">
                        <p class="cam-instruction-overlay">Press the button below, start recording and move your head in all directions</p>
                        <p class="cam-step-overlay" id="progress"></p>
                    </div>
                    <div id="countdown-overlay" style="display:none; position:absolute; inset:0; display:none; align-items:center; justify-content:center; pointer-events:none;">
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
<script>
function switchMethod(method) {
    document.getElementById('panel-cam').style.display    = method === 'cam'    ? 'block' : 'none';
    document.getElementById('panel-upload').style.display = method === 'upload' ? 'block' : 'none';
    document.getElementById('btn-cam').classList.toggle('active', method === 'cam');
    document.getElementById('btn-upload').classList.toggle('active', method === 'upload');
    if (method === 'cam') startWebcam();
}
</script>
</body>
</html>