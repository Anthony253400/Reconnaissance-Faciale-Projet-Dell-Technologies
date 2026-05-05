const video = document.getElementById('webcam');

async function startWebcam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        
        video.srcObject = stream;
    } catch (error) {
        console.error("Erreur d'accès à la webcam : ", error);
        alert("Impossible d'accéder à la caméra. Vérifiez les permissions.");
    }
}

startWebcam();