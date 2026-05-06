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

// global variable to store the captured photo
let capturedPhoto = null;

function takePicture() {
    const video  = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const ctx    = canvas.getContext('2d');

    // draw the current video frame onto the canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // show a preview of the captured photo
    const preview = document.getElementById('preview');
    preview.src = canvas.toDataURL('image/jpeg');
    preview.style.display = 'block';

    // convert the canvas to a File object (like a real uploaded file)
    canvas.toBlob((blob) => {
        capturedPhoto = new File([blob], "photo.jpg", { type: "image/jpeg" });
    }, 'image/jpeg');
}


// ── ADD PERSON ──
// collects form data and sends it to FastAPI
async function addPerson() {
    const firstName = document.getElementById('firstName').value;
    const lastName  = document.getElementById('lastName').value;

    // use the captured photo if available, otherwise use the uploaded file
    const photo = capturedPhoto || document.getElementById('photo').files[0];

    // basic validation
    const nameRegex = /^[a-zA-ZÀ-ÿ]{1,}$/;

    // check if all fields are filled and if the photo is valid
    if (!firstName || !lastName || !photo) {
        alert("Please fill in all fields and provide a photo.");
        return;
    }
    if (!nameRegex.test(firstName) || !nameRegex.test(lastName)) {
        alert("Names can only contain letters.");
        return;
    }
    if (!photo.type.startsWith('image/')) {
        alert("Please upload a valid image file.");
        return;
    }
    
    // FormData lets us send text + file together in one request
    const formData = new FormData();
    formData.append('firstName', firstName);
    formData.append('lastName', lastName);
    formData.append('photo', photo);

    // send the data to FastAPI with fetch()
    try {
        const response = await fetch('http://localhost:8000/add', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        document.getElementById('message').textContent =  data.message;

    } catch (error) {
        document.getElementById('message').textContent = "Error: server not available";
    }
}