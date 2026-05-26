const instructions = [
    "Look straight ahead",
    "Look to the right",
    "Look to the left",
    "Look up",
    "Look down"
];
let capturedPhotos = [];
let recording = false;
let recordingInterval = null;
const MIRROR = true; // set to true if your webcam feed is mirrored (front camera)
const TARGET_FRAMES = 50; // number of frames to capture 
const INTERVAL_MS = 150; // interval between captures in milliseconds 

// WEBCAM
// starts the webcam and connects the stream to the <video> tag
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


// TAKE FRAME PICTURE
// captures the current video frame and saves it as a file

function startRecording() {
    if (recording) return;
    capturedPhotos = [];
    recording = true;
    document.getElementById('btn-record').disabled = true;
    document.getElementById('progress').textContent = `Capturing... 0 / ${TARGET_FRAMES}`;

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
            if (capturedPhotos.length >= TARGET_FRAMES) {
                clearInterval(recordingInterval);
                recording = false;
                document.getElementById('btn-record').disabled = false;
                document.getElementById('progress').textContent = `Done! You can now add to database!`;
            }
        }, 'image/jpeg');
    }, INTERVAL_MS);
}


async function addPerson() {

    if (!document.getElementById('consent').checked) {
        alert("You must accept the privacy policy.");
        return;
    }

    const firstName = document.getElementById('firstName').value;
    const lastName  = document.getElementById('lastName').value;
    const nameRegex = /^[a-zA-ZÀ-ÿ]{1,}$/;

    if (!firstName || !lastName) {
        alert("Please fill in all fields.");
        return;
    }
    if (!nameRegex.test(firstName) || !nameRegex.test(lastName)) {
        alert("Names can only contain letters.");
        return;
    }
    if (capturedPhotos.length < TARGET_FRAMES) {
        alert(`Please take all ${TARGET_FRAMES} photos first.`);
        return;
    }

    try {
        for (let i = 0; i < capturedPhotos.length; i++) {
            const formData = new FormData();
            formData.append('firstName', firstName);
            formData.append('lastName', lastName);
            formData.append('photo', capturedPhotos[i]);
            await fetch('http://localhost:8000/add', { method: 'POST', body: formData });
            document.getElementById('message').textContent = `Sending... ${i + 1} / ${TARGET_FRAMES}`;
        }

        document.getElementById('message').textContent = "Person added successfully!";
        capturedPhotos = [];
        document.getElementById('progress').textContent = '';
        document.getElementById('btn-record').disabled = false;

        document.getElementById('firstName').value = '';
        document.getElementById('lastName').value  = '';
        document.getElementById('consent').checked = false;


    } catch (error) {
        console.error("Errore:", error);
        document.getElementById('message').textContent = "Error: server not available";
    }
}

