const MIRROR = true;        // front camera is mirrored
const SEND_W = 640;         // resolution sent to the server (smaller = faster)
const SEND_H = 480;

async function init() {
    await startWebcam();
    startDetection();
}

// Start the webcam and feed it into the <video> element
async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 960 }, audio: false
        });
        document.getElementById('webcam').srcObject = stream;
    } catch (error) {
        alert("Cannot access camera: " + error.message);
    }
}

function startDetection() {
    const video   = document.getElementById('webcam');
    const overlay = document.getElementById('overlay');
    const capture = document.getElementById('capture');
    const ctxOver = overlay.getContext('2d');
    const ctxCap  = capture.getContext('2d');

    // the capture canvas defines the coordinate space the server works in
    capture.width  = SEND_W;
    capture.height = SEND_H;

    const ws = new WebSocket('ws://localhost:8000/ws/detect');

    ws.onopen = () => { console.log("WebSocket connected"); sendFrame(); };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // match the overlay to the video's displayed size, but keep drawing
        // in the SEND_W x SEND_H coordinate space the server used
        overlay.width  = SEND_W;
        overlay.height = SEND_H;
        ctxOver.clearRect(0, 0, overlay.width, overlay.height);

        // --- faces ---
        for (let i = 0; i < data.faces.length; i++) {
            const [x1, y1, x2, y2] = data.faces[i];
            const dX1 = MIRROR ? overlay.width - x2 : x1;
            const dX2 = MIRROR ? overlay.width - x1 : x2;

            const name  = data.names[i] || "";
            const score = data.scores[i] || 0;
            const color = score >= 0.70 ? "#10b981" : score >= 0.50 ? "#facc15" : "#9ca3af";

            drawBox(ctxOver, dX1, y1, dX2 - dX1, y2 - y1, color,
                    name && name !== "inconnu" ? `${name}  ${score.toFixed(2)}` : "inconnu");
        }

        // --- bodies ---
        for (let i = 0; i < data.body.length; i++) {
            const [x1, y1, x2, y2] = data.body[i];
            const dX1 = MIRROR ? overlay.width - x2 : x1;
            const dX2 = MIRROR ? overlay.width - x1 : x2;
            drawBox(ctxOver, dX1, y1, dX2 - dX1, y2 - y1, "#ef4444",
                    data.body_names[i] || "");
        }

        sendFrame();
    };

    ws.onclose = () => console.log("WebSocket disconnected");
    ws.onerror = (e) => console.error("WebSocket error:", e);

    // grab the current video frame, scale it to SEND_W x SEND_H, send as JPEG
    function sendFrame() {
        if (ws.readyState === WebSocket.OPEN && ws.bufferedAmount === 0) {
            ctxCap.drawImage(video, 0, 0, capture.width, capture.height);
            ctxCap.drawImage(video, 0, 0, capture.width, capture.height);
            capture.toBlob((blob) => { if (blob) ws.send(blob); }, 'image/jpeg', 0.8);
        }
    }
}

// draw one box with a filled label tag (canvas handles accents natively)
function drawBox(ctx, x, y, w, h, color, label) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);

    if (label) {
        ctx.font = "16px Arial";
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = color;
        ctx.fillRect(x, y - 22, tw + 12, 22);
        ctx.fillStyle = "#fff";
        ctx.fillText(label, x + 6, y - 6);
    }
}

init();