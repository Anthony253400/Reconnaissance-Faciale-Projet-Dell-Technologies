document.addEventListener('DOMContentLoaded', () => {
        // On cible spécifiquement la boîte qu'on vient de créer
        const bgScanner = new FaceScanner('#hero-scanner-bg .scanner-wrapper', {
            landmarkCount: 24, 
            scanDelay: 500, // Démarre presque immédiatement
            showGrid: true,
            autoDemo: true     
        });
        bgScanner.init();
    });
