const img = document.getElementById('feed');
 
function refresh() {
    const next = new Image();
    next.onload = () => { img.src = next.src; };
    next.src = 'http://localhost:8000/frame?t=' + Date.now();
}
 
setInterval(refresh, 100);
refresh();
 