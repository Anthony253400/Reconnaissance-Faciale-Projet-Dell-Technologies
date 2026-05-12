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
        setInterval(sendFrame, 100); // send frame every 100ms
    };
    // receive detection results from the server and draw bounding boxes
    ws.onmessage =(event) => {
        const data = JSON.parse(event.data);
        ctxOver.clearRect(0, 0, overlay.width, overlay.height);

        for (let i = 0; i < data.faces.length; i++) {
            const [x1, y1, x2, y2] = data.faces[i];
            ctxOver.strokeStyle = "green";
            ctxOver.lineWidth = 2;
            ctxOver.strokeRect(x1, y1, x2 - x1, y2 - y1);

            const name = data.names[i] || "";
            ctxOver.fillStyle = "green";
            ctxOver.font = "16px Arial";
            ctxOver.fillText(name, x1, y1 - 5);
        }
    };

    ws.onclose =() => console.log("WebSocket disconnected");
    ws.onerror =(error) => console.error("WebSocket error:", error);

    // capture the current video frame and send it to the server 
    // if the WebSocket is open and there are no pending messages in the buffer
    function sendFrame() {
    if (ws.readyState === WebSocket.OPEN && ws.bufferedAmount === 0) {
        ctxCap.drawImage(video, 0, 0, capture.width, capture.height);
        capture.toBlob((blob) => {
            ws.send(blob);
        }, 'image/jpeg');
    }
}  
}


async function init() {
    // start the webcam automatically when the page loads
    await startWebcam();

    // start face detection after webcam is ready
    startDetection();
}
init();
