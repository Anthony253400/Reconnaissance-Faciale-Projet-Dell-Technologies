document.addEventListener("DOMContentLoaded", () => {

    const currentPath = window.location.pathname.split("/").pop() || "index.php";

    // Ciblage strict des liens situés dans le conteneur principal 
    // (cela évite d'affecter le logo nav-brand qui pointe aussi vers index.php)
    const navLinks = document.querySelectorAll(".nav-links .nav-link");

    navLinks.forEach(link => {
        // Réinitialisation globale de l'état
        link.classList.remove("active");

        const linkHref = link.getAttribute("href");

        // Correspondance établie : activation du marqueur
        if (linkHref === currentPath) {
            link.classList.add("active");
        }
    });
});