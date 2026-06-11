const MIRROR = true; // set to true if your webcam feed is mirrored (front camera)

/**
    * INITIALISATION the webcam and start the detection loop
    * called automatically when the page loads
    * mirrors the webcam if mirror is set to true
*/  
async function init() {
    document.getElementById('webcam').style.transform = MIRROR ? 'scaleX(-1)' : '';
    await startWebcam();
    startDetection();
}

/**
    * WEBCAM
    * starts the webcam and connects the stream to the <video> tag
*/  
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


/**
    * FACE DETECTION
    * opens websocket connection to server and starts the detection loop.
    * on each frame captures current video frame and sends it to the server a s a jpeg blob
    * resceives detection result ( bounding boxes, names and scores)
    * clears and draws them on the overlay canvas
    * 
    * The face bounding boxes are color coded based on the confidence score:
    * - green for scores >= 0.70 (high confidence)
    * - yellow for scores >= 0.50 and < 0.70 (medium confidence)
    * - gray for scores < 0.50 (low confidence)
    * 
    * the body boxes are drawn in red. a new socket is sent only when the socket is open and the send buffer is emplty ( avoid flooding server)
*/  
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
    ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
    ctxOver.clearRect(0, 0, overlay.width, overlay.height);

    //box and name for face detected
    for (let i = 0; i < data.faces.length; i++) {
        const [x1, y1, x2, y2] = data.faces[i];
        const drawX1 = MIRROR ? overlay.width - x2 : x1;
        const drawX2 = MIRROR ? overlay.width - x1 : x2;

        const name = data.names[i] || "";
        const score = data.scores[i];
        const color = score >= 0.70 ? "green" : score >= 0.50 ? "yellow" : "gray";
        
        ctxOver.strokeStyle = color;
        ctxOver.lineWidth = 2;
        ctxOver.strokeRect(drawX1, y1, drawX2 - drawX1, y2 - y1);

        ctxOver.fillStyle = color;
        ctxOver.font = "16px Arial";
        ctxOver.fillText(name, drawX1, y1 - 5);

    }
    //box and name for body detected
    for (let i = 0; i < data.body.length; i++) {
        const [x1, y1, x2, y2] = data.body[i];
        const drawX1 = MIRROR ? overlay.width - x2 : x1;
        const drawX2 = MIRROR ? overlay.width - x1 : x2;
        ctxOver.strokeStyle = "red";
        ctxOver.lineWidth = 2;
        ctxOver.strokeRect(drawX1, y1, drawX2 - drawX1, y2 - y1);

        const name = data.body_names[i] || "";
        ctxOver.fillStyle = "red";
        ctxOver.font = "16px Arial";
        ctxOver.fillText(name, drawX1, y1 - 5);
    }
    sendFrame();
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

init();
