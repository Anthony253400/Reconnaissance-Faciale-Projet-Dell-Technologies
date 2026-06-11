let capturedPhotos = [];
let recording = false;
let recordingInterval = null;
const MIRROR = true; // set to true if your webcam feed is mirrored (front camera)
const TARGET_FRAMES = 50; // number of frames to capture 
const INTERVAL_MS = 100; // interval between captures in milliseconds 
const RING_CIRCUMFERENCE = 2 * Math.PI * 32; // circumference of the capture ring (r=32) 2*phi*32, used to animate the progress ring during capture

/**
    * WEBCAM
    * starts the webcam and connects the stream to the <video> tag
*/  
async function startWebcam() {
    try {
        // ask the browser for camera access
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

        // connect the stream to the <video> tag
        const video = document.getElementById('webcam');
        video.srcObject = stream;
        video.style.transform = MIRROR ? 'scaleX(-1)' : '';

    } catch (error) {
        alert("Cannot access camera: " + error.message);
    }
}

// start the webcam automatically when the page loads
startWebcam();


/**
 * COUNTDOWN
 * displays a 3-2-1 countdown overlay on the webcam feed before recording starts.
 * the numbers appear centered on the video, large and visible.
 * the last number (1) is displayed in green to signal the imminent start.
 * once the countdown ends, the overlay is hidden and beginCapture() is called.
 */
function startRecording() {
    if (recording) return;

    const overlay = document.getElementById('countdown-overlay');
    const numEl   = document.getElementById('countdown-num');
    numEl.style.background = 'none';
    numEl.style.border = 'none';
    numEl.style.color = 'white';
    numEl.style.padding = '0';
    numEl.style.borderRadius = '0';
    numEl.style.fontSize = '120px';
    const nums = [3, 2, 1];
    let i = 0;

    overlay.style.display = 'flex';
    document.getElementById('countdown-msg').style.display = 'none';
    document.getElementById('countdown-num').style.display = 'block';

    function tick() {
        numEl.textContent = nums[i];
        numEl.style.color = 'rgba(0,118,206,0.5)';
        i++;
        if (i < nums.length) {
            setTimeout(tick, 900);
        } else {
            setTimeout(() => {
                overlay.style.display = 'none';
                beginCapture(overlay, numEl);
            }, 900);
        }
    }
    tick();
}

/**
 * FRAME CAPTURE
 * called automatically by startRecording() once the countdown is complete.
 * captures frames from the webcam at regular intervals (INTERVAL_MS) until TARGET_FRAMES is reached.
 * each frame is stored in the capturedPhotos array as a JPEG File object (frame_0.jpg, frame_1.jpg, ...).
 * during capture, the progress is displayed as text and visually with the circular ring around the record button.
 * once done, the button is re-enabled and the user is prompted to fill in the name and submit.
 */
function beginCapture(overlay, numEl) {
    capturedPhotos = [];
    recording = true;
    document.getElementById('btn-record').disabled = true;
    document.getElementById('progress').textContent = `Capturing... 0 / ${TARGET_FRAMES}`;

    const ring = document.getElementById('capture-ring');
    if (ring) ring.style.strokeDashoffset = RING_CIRCUMFERENCE;

    const video  = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx    = canvas.getContext('2d');

    recordingInterval = setInterval(() => {
        canvas.width  = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
            capturedPhotos.push(new File([blob], `frame_${capturedPhotos.length}.jpg`, { type: "image/jpeg" }));
            document.getElementById('progress').textContent = `Capturing... ${capturedPhotos.length} / ${TARGET_FRAMES}`;

            if (ring) ring.style.strokeDashoffset = RING_CIRCUMFERENCE * (1 - capturedPhotos.length / TARGET_FRAMES);

            if (capturedPhotos.length >= TARGET_FRAMES) {
                clearInterval(recordingInterval);
                recording = false;
                document.getElementById('btn-record').disabled = false;
                document.getElementById('progress').textContent = '';

            document.getElementById('countdown-num').style.display = 'none';
            const msg = document.getElementById('countdown-msg');
            msg.textContent = 'Done! Click "Add to database" below.';
            msg.style.display = 'inline';
            overlay.style.display = 'flex';            }
        }, 'image/jpeg');
    }, INTERVAL_MS);
}

/**
 * ADD PERSON
 * Validates the form, then sends all blobs to the server
 * via WebSocket for registration.
 *
 * Validation checks:
 *   - privacy policy checkbox must be accepted
 *   - first and last name must be filled in and contain only letters
 *   - at least one photo or frame must be available
 *
 * Once the WebSocket is open, the person's name is sent first as JSON,
 * followed by all blobs as JPEG data.
 *
 * A progress bar appears below the submit button and advances with
 * each server acknowledgement. On completion it turns green and
 * disappears after 2 seconds.
 *
 * On success, the form is reset: captured photos, name fields,
 * consent checkbox and the progress ring are all cleared.
 */
async function addPerson() {

    if (!document.getElementById('consent').checked) {
        alert("You must accept the privacy policy.");
        return;
    }

    const firstName = document.getElementById('firstName').value;
    const lastName  = document.getElementById('lastName').value;
    const nameRegex = /^[a-zA-ZÀ-ÿ]{1,}$/;

    if (!firstName || !lastName) { alert("Please fill in all fields."); return; }
    if (!nameRegex.test(firstName) || !nameRegex.test(lastName)) {
        alert("Names can only contain letters.");
        return;
    }

    const blobs = getBlobs();
    if (blobs.length === 0) { alert('Please capture or upload at least one photo.'); return; }

    const btn = document.querySelector('.btn.btn-primary');
    const msg = document.getElementById('message');
    btn.disabled = true;
    msg.textContent = 'Sending...';

    // Progress bar indeterminata (un solo invio)
    const bar = document.createElement('div');
    bar.style.cssText = 'height:3px;background:#e4e4e0;border-radius:99px;margin-top:8px;overflow:hidden;';
    const fill = document.createElement('div');
    fill.style.cssText = 'height:100%;width:0%;background:#0076CE;border-radius:99px;transition:width 1.5s ease;';
    bar.appendChild(fill);
    msg.after(bar);

    // Anima verso 90% subito — il 100% arriva con la risposta del server
    requestAnimationFrame(() => { fill.style.width = '90%'; });

    // Un solo FormData con tutti i frame
    const formData = new FormData();
    formData.append('firstName', firstName);
    formData.append('lastName',  lastName);
    blobs.forEach((blob, i) => formData.append('photos', blob, `frame_${i}.jpg`));

    try {
        const res = await fetch('http://localhost:8000/add', {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            fill.style.transition = 'width 0.2s ease';
            fill.style.width      = '100%';
            fill.style.background = '#16a34a';
            msg.textContent       = 'Person added successfully!';

            const testBtn = document.createElement('a');
            testBtn.href        = 'detection.php';
            testBtn.textContent = 'Test detection →';
            testBtn.style.cssText = 'display:inline-block;margin-top:10px;font-size:0.875rem;font-weight:500;color:#0076CE;text-decoration:none;';
            msg.after(testBtn);

        } else {
            const err = await res.text();
            msg.textContent       = `Error: ${err}`;
            fill.style.background = '#dc2626';
            fill.style.width      = '100%';
        }

    } catch (e) {
        msg.textContent       = 'Error: server not available';
        fill.style.background = '#dc2626';
        fill.style.width      = '100%';
    }

    setTimeout(() => bar.remove(), 2000);

    // Reset form
    capturedPhotos = [];
    document.getElementById('progress').textContent = '';
    document.getElementById('btn-record').disabled  = false;
    document.getElementById('firstName').value      = '';
    document.getElementById('lastName').value       = '';
    document.getElementById('consent').checked      = false;
    const ring = document.getElementById('capture-ring');
    if (ring) ring.style.strokeDashoffset = RING_CIRCUMFERENCE;
    btn.disabled = false;
}

/**
 * Returns the list of blobs to send to the server depending on the active input method.
 * - webcam : returns the array of captured frames (capturedPhotos)
 * - upload : returns a single-element array with the selected file
 */
function getBlobs() {
    const method = document.getElementById('panel-upload').style.display === 'block' ? 'upload' : 'cam';
    if (method === 'cam') {
        return capturedPhotos;
    } else {
        const file = document.getElementById('photo').files[0];
        return file ? [file] : [];
    }
}