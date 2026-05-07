// -- WEBCAM --
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


// -- FACE DETECTION --

async function startDetection() {
    const video = document.getElementById('webcam');
    const overlay = document.getElementById('overlay');
    const capture = document.getElementById('capture');
    const ctxOver = overlay.getContext('2d');
    const ctxCap = capture.getContext('2d');

    const ws = new WebSocket('ws://localhost:8000/ws/detect');

    //open WebSocket connection and start sending frames 
    ws.onopen =() =>  {
        console.log("WebSocket connected");
        sendFrame();
    };
    // receive detection results from the server and draw bounding boxes
    ws.onmessage =(event) => {
        const data = JSON.parse(event.data);
        console.log(data);
        //clear canvas before drawing new boxes
        ctxOver.clearRect(0, 0, overlay.width, overlay.height);
        
        for (const [x, y, w, h] of data.faces) {
            ctxOver.strokeStyle = "green";
            ctxOver.lineWidth = 2;
            ctxOver.strokeRect(x, y, w, h);
        }
        sendFrame();
    };

    ws.onclose =() => console.log("WebSocket disconnected");
    ws.onerror =(error) => console.error("WebSocket error:", error);

    function sendFrame() {

        ctxCap.drawImage(video, 0, 0, capture.width, capture.height);
        capture.toBlob((blob) => {
            ws.send(blob);
        }, 'image/jpeg');
    }   
}


async function init() {
    // start the webcam automatically when the page loads
    await startWebcam();

    // start face detection after webcam is ready
    startDetection();
}
init();
