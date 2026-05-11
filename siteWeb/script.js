const instructions = [
    "Look straight ahead",
    "Look to the right",
    "Look to the left",
    "Look up",
    "Look down"
];

let currentStep = 0;
let capturedPhotos = [null, null, null, null, null];

// ── WEBCAM ──
// starts the webcam and connects the stream to the <video> tag
async function startWebcam() {
    try {
        // ask the browser for camera access
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

        // connect the stream to the <video> tag
        document.getElementById('webcam').srcObject = stream;

    } catch (error) {
        alert("Cannot access camera: " + error.message);
    }
}

// start the webcam automatically when the page loads
startWebcam();


// ── TAKE PICTURE ──
// captures the current video frame and saves it as a file

function takePicture() {
    // trova il primo slot vuoto
    const slotIndex = capturedPhotos.findIndex(p => p === null);
    if (slotIndex === -1) return;  // tutti e 5 pieni

    const video  = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx    = canvas.getContext('2d');

    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        const file = new File([blob], `photo_${slotIndex}.jpg`, { type: "image/jpeg" });
        capturedPhotos[slotIndex] = file;

        const preview = document.getElementById(`preview-${slotIndex}`);
        preview.src = URL.createObjectURL(blob);
        preview.style.display = 'block';

        document.getElementById(`delete-${slotIndex}`).style.display = 'block';

        const filled = capturedPhotos.filter(p => p !== null).length;
        if (filled < 5) {
            const nextEmpty = capturedPhotos.findIndex(p => p === null);
            document.getElementById('instruction').textContent = instructions[nextEmpty];
            document.getElementById('step').textContent = `Photo ${filled + 1} / 5`;
        } else {
            document.getElementById('instruction').textContent = "All photos taken!";
            document.getElementById('step').textContent = "You can now add to database";
        }
    }, 'image/jpeg');
}

function deletePhoto(index) {
    capturedPhotos[index] = null;

    document.getElementById(`preview-${index}`).style.display = 'none';
    document.getElementById(`delete-${index}`).style.display = 'none';

    const filled = capturedPhotos.filter(p => p !== null).length;
    const nextEmpty = capturedPhotos.findIndex(p => p === null);
    document.getElementById('instruction').textContent = instructions[nextEmpty];
    document.getElementById('step').textContent = `Photo ${filled + 1} / 5`;
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
    if (capturedPhotos.length < 5) {
        alert("Please take all 5 photos first.");
        return;
    }

    try {
        for (let i = 0; i < capturedPhotos.length; i++) {
            const formData = new FormData();
            formData.append('firstName', firstName);
            formData.append('lastName', lastName);
            formData.append('photo', capturedPhotos[i]);

            await fetch('http://localhost:8000/add', {
                method: 'POST',
                body: formData
            });
        }

        document.getElementById('message').textContent = "Person added successfully!";

        // reset
        currentStep = 0;
        capturedPhotos = [];
        document.getElementById('instruction').textContent = instructions[0];
        document.getElementById('step').textContent = "Photo 1 / 5";
        for (let i = 0; i < 5; i++) {
            const preview = document.getElementById(`preview-${i}`);
            preview.src = '';
            preview.style.display = 'none';
        }

    } catch (error) {
        document.getElementById('message').textContent = "Error: server not available";
    }
}