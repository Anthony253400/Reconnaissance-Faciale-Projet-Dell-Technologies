<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Licence</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">
    <link rel="stylesheet" href="assets/css/licence.css">


    <script src="assets/js/navbar.js"></script>
    <script src="assets/js/footer.js"></script>

</head>
<body>
    <?php include("components/navbar.php") ;?>
<div class="license-container">
    
    <header class="license-header">
        <h1>Academic & Non-Commercial License</h1>
        <p class="copyright">Copyright &copy; 2026 Anthony Miranda & Lea Carminati</p>
        <div class="badge">Restricted Use</div>
    </header>

    <hr class="separator">

    <div class="license-grid">
        
        <div class="license-card card-allowed">
            <h3>What is permitted</h3>
            <p>Permission is hereby granted to use, copy, and modify this software solely for specific frameworks:</p>
            <ul>
                <li>Educational projects</li>
                <li>Academic research</li>
                <li>Personal use</li>
            </ul>
        </div>

        <div class="license-card card-conditions">
            <h3>Required conditions</h3>
            <p>For any use or modification of the software, you must complies with the following:</p>
            <ul>
                <li>The above copyright notice and this license must be included in all copies or substantial portions of the Software.</li>
                <li>Any academic publication, report, or derivative work based on this Software must explicitly cite the original authors and this project.</li>
            </ul>
        </div>

        <div class="license-card card-prohibited">
            <h3>What is strictly prohibited</h3>
            <p>Any commercial exploitation or production use is strictly forbidden:</p>
            <ul>
                <li>You may NOT use this software, or any modifications of it, for any commercial, corporate, or production purposes.</li>
                <li>You may NOT monetize this software directly or indirectly.</li>
                <li>This project integrates third-party components (e.g., <strong>ArcFace</strong>, <strong>YOLOv8</strong>). You are strictly bound by their respective original licenses, which explicitly prohibit commercial use or dictate specific distribution terms.</li>
            </ul>
        </div>

    </div>

    <section class="rgpd-section">
        <div class="rgpd-badge">GDPR Compliance</div>
        <h2>Data Protection & Consent</h2>
        <p>This website and its image processing algorithms strictly comply with the <strong>General Data Protection Regulation (GDPR)</strong>.</p>
        <div class="rgpd-alert">
            <p><strong>Golden Rule:</strong> It is strictly forbidden to register, detect, or store biometric data of any individual in the database <strong>without their explicit and informed consent</strong>.</p>
        </div>
    </section>

    <section class="disclaimer-section">
        <h3>Disclaimer</h3>
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p>
    </section>

    <footer class="license-footer">
        <h3>Contact & Questions</h3>
        <p>For any questions regarding licensing or secondary rights authorization, please contact:</p>
        <div class="contacts-wrap">
            <div class="contact-box">
                <strong>Anthony Miranda</strong>
                <a href="mailto:anthony.miranda@etu.univ-mtp3.fr">anthony.miranda@etu.univ-mtp3.fr</a>
            </div>
            <div class="contact-box">
                <strong>Lea Carminati</strong>
                <a href="mailto:lea.carminati@etu.univ-mtp3.fr">lea.carminati@etu.univ-mtp3.fr</a>
            </div>
        </div>
    </footer>

</div>
    </div>    <?php include("components/footer.php") ;?>

</body>
</html>