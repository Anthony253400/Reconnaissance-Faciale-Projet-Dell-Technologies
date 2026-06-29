const MIRROR = true;
const SMOOTH = 0.5;   // 0 = nessun movimento, 1 = salta subito al target. Più basso = più fluido ma più lag. Regola questo.
const MATCH_DIST = 120; // px: distanza max per considerare due box "la stessa faccia" tra frame

async function init() {
    await startWebcam();
    startDetection();
}

async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        const video = document.getElementById('webcam');
        video.srcObject = stream;
        await new Promise(r => video.onloadedmetadata = r);
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

    const vw = video.videoWidth  || 640;
    const vh = video.videoHeight || 480;
    const scale = 640 / vw;
    const SEND_W = Math.round(vw * scale);
    const SEND_H = Math.round(vh * scale);

    capture.width  = SEND_W;  capture.height = SEND_H;
    overlay.width  = SEND_W;  overlay.height = SEND_H;

    // operational threshold from injected config (single source of truth)
    const T = window.APP_CONFIG.THRESHOLD;

    // tracked boxes: ogni elemento ha posizione "current" (disegnata) e "target" (dal server)
    // { cx, cy, cw, ch (current), tx, ty, tw, th (target), name, score, color, kind, seen }
    let tracked = [];

    // WebSocket URL from injected config (no hardcoded host/port)
    const ws = new WebSocket(`${window.APP_CONFIG.WS_BASE}/ws/detect`);
    ws.onopen = () => { console.log("WebSocket connected"); sendFrame(); };
    ws.onclose = () => console.log("WebSocket disconnected");
    ws.onerror = (e) => console.error("WebSocket error:", e);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // costruisci la lista di target da questo messaggio (facce + corpi)
        const incoming = [];
        for (let i = 0; i < data.faces.length; i++) {
            const [x1, y1, x2, y2] = data.faces[i];
            const dX1 = MIRROR ? overlay.width - x2 : x1;
            const score = data.scores[i] || 0;
            const name  = data.names[i] || "";
            incoming.push({
                tx: dX1, ty: y1, tw: x2 - x1, th: y2 - y1,
                name, score,
                // green = match (>= threshold), grey = below threshold
                color: score >= T ? "#10b981" : "#9ca3af",
                label: (name && name !== "inconnu") ? `${name}  ${score.toFixed(2)}` : "inconnu",
                kind: "face"
            });
        }
        for (let i = 0; i < data.body.length; i++) {
            const [x1, y1, x2, y2] = data.body[i];
            const dX1 = MIRROR ? overlay.width - x2 : x1;
            incoming.push({
                tx: dX1, ty: y1, tw: x2 - x1, th: y2 - y1,
                color: "#ef4444",
                label: data.body_names[i] || "",
                kind: "body"
            });
        }

        // associa ogni target alla box tracked più vicina dello stesso tipo (greedy nearest)
        const used = new Array(tracked.length).fill(false);
        for (const inc of incoming) {
            let best = -1, bestD = MATCH_DIST;
            for (let j = 0; j < tracked.length; j++) {
                if (used[j] || tracked[j].kind !== inc.kind) continue;
                const d = Math.hypot(tracked[j].tx - inc.tx, tracked[j].ty - inc.ty);
                if (d < bestD) { bestD = d; best = j; }
            }
            if (best >= 0) {
                // stessa box: aggiorna solo il target, current resta dov'è (interpolerà)
                used[best] = true;
                Object.assign(tracked[best], inc, { seen: true });
            } else {
                // box nuova: appare già in posizione (no slide dal nulla)
                tracked.push({ ...inc, cx: inc.tx, cy: inc.ty, cw: inc.tw, ch: inc.th, seen: true });
                used.push(true);
            }
        }
        // marca come non viste le box senza match (verranno rimosse al prossimo giro)
        for (let j = 0; j < tracked.length; j++) {
            if (!used[j]) tracked[j].seen = false;
        }
        tracked = tracked.filter(b => b.seen);

        sendFrame();
    };

    // RENDER LOOP: gira a 60 FPS sempre, indipendente dai dati
    function render() {
        ctxOver.clearRect(0, 0, overlay.width, overlay.height);
        for (const b of tracked) {
            // interpola current verso target
            b.cx += (b.tx - b.cx) * SMOOTH;
            b.cy += (b.ty - b.cy) * SMOOTH;
            b.cw += (b.tw - b.cw) * SMOOTH;
            b.ch += (b.th - b.ch) * SMOOTH;
            drawBox(ctxOver, b.cx, b.cy, b.cw, b.ch, b.color, b.label);
        }
        requestAnimationFrame(render);
    }
    requestAnimationFrame(render);

    function sendFrame() {
        if (ws.readyState === WebSocket.OPEN && ws.bufferedAmount === 0) {
            ctxCap.drawImage(video, 0, 0, capture.width, capture.height);
            capture.toBlob((blob) => { if (blob) ws.send(blob); }, 'image/jpeg', 0.8);
        }
    }
}

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