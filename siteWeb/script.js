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
 * RECORDING AND FRAME CAPTURE
 * when the user clicks the record button, starts capturing frames from the webcam at regular intervals (INTERVAL_MS) until TARGET_FRAMES is reached
 * the captured frames are stored in the capturedPhotos array as File objects (with name frame_0.jpg, frame_1.jpg, etc.)
 * during capture, the progress is displayed as text and visually with a circular progress ring around the record button
 * once done, the user can click "add to database" to send the captured photos to the server
 */
function startRecording() {
    if (recording) return;
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
                document.getElementById('progress').textContent = `Done! You can now add to database!`;
            }
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

    if (!document.getElementById('consent').checked) { alert("You must accept the privacy policy."); return; }

    const firstName = document.getElementById('firstName').value;
    const lastName  = document.getElementById('lastName').value;
    const nameRegex = /^[a-zA-ZÀ-ÿ]{1,}$/;

    if (!firstName || !lastName) { alert("Please fill in all fields."); return; }
    if (!nameRegex.test(firstName) || !nameRegex.test(lastName)) { alert("Names can only contain letters."); return; }

    const blobs = getBlobs();
    if (blobs.length === 0) { alert('Please capture or upload at least one photo.'); return; }

    const btn = document.querySelector('.btn.btn-primary');
    const msg = document.getElementById('message');
    btn.disabled = true;

    const bar = document.createElement('div');
    bar.style.cssText = 'height:3px;background:#e4e4e0;border-radius:99px;margin-top:8px;overflow:hidden;';
    const fill = document.createElement('div');
    fill.style.cssText = 'height:100%;width:0%;background:#0076CE;border-radius:99px;transition:width 0.15s ease;';
    bar.appendChild(fill);
    msg.after(bar);

    const total = blobs.length;
    let received = 0;

    const ws = new WebSocket('ws://localhost:8000/ws/add');

    ws.onopen = () => {
        ws.send(JSON.stringify({ firstName, lastName }));
        blobs.forEach(blob => ws.send(blob));
    };

    ws.onmessage = () => {
        received++;
        fill.style.width = Math.round(received / total * 100) + '%';
        msg.textContent = `Sending... ${received} / ${total}`;

        if (received >= total) {
            ws.close();
            msg.textContent = 'Person added successfully!';
            const testBtn = document.createElement('a');
            testBtn.href = 'detection.html';
            testBtn.textContent = 'Test detection →';
            testBtn.style.cssText = 'display:inline-block;margin-top:10px;font-size:0.875rem;font-weight:500;color:#0076CE;text-decoration:none;';
            msg.after(testBtn);
            fill.style.background = '#16a34a';
            setTimeout(() => {
                bar.remove();
                testBtn.remove();
            }, 2000);

            capturedPhotos = [];
            document.getElementById('progress').textContent = '';
            document.getElementById('btn-record').disabled = false;
            document.getElementById('firstName').value = '';
            document.getElementById('lastName').value  = '';
            document.getElementById('consent').checked = false;
            const ring = document.getElementById('capture-ring');
            if (ring) ring.style.strokeDashoffset = RING_CIRCUMFERENCE;
            btn.disabled = false;
        }
    };

    ws.onerror = () => {
        msg.textContent = 'Error: server not available';
        bar.remove();
        btn.disabled = false;
    };
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
