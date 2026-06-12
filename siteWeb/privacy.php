<?php $current = "privacy"; ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition Privacy policy</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">

    <script src="assets/js/navbar.js"></script>

    <style>
        /* le texte occupe toute la largeur de la carte */
        .privacy-body h3 {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: var(--text-muted);
            margin-top: 1.75rem;
            margin-bottom: 0.5rem;
        }
        .privacy-body h3:first-child { margin-top: 0; }
        .privacy-body p {
            font-size: 0.9375rem;
            font-weight: 300;
            line-height: 1.8;
            color: var(--text);
        }
        .privacy-body ul {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.375rem;
            margin-top: 0.5rem;
        }
        .privacy-body ul li {
            font-size: 0.9375rem;
            font-weight: 300;
            line-height: 1.6;
            padding-left: 1rem;
            position: relative;
            color: var(--text);
        }
        .privacy-body ul li::before {
            content: '—';
            position: absolute;
            left: 0;
            color: var(--text-muted);
        }
        .privacy-body a {
            color: var(--dell-blue);
            text-decoration: underline;
            text-underline-offset: 2px;
        }
    </style>

</head>
<body>

<?php include("components/navbar.php"); ?>

<div class="container">

    <header class="page-header">
        <h1>Privacy policy</h1>
        <p class="subtitle">Dell Technologies Montpellier Curricular internship 2026</p>
    </header>

    <div class="section-card">
        <div class="privacy-body">

            <h3>Who are we?</h3>
            <p>This application was developed by Anthony Miranda and Lea Carminati as part of a curricular internship project on face recognition at Dell Technologies Montpellier.</p>

            <h3>What data do we collect?</h3>
            <p>We collect the following data:</p>
            <ul>
                <li>First name and last name</li>
                <li>Biometric facial data derived from your photo</li>
            </ul>

            <h3>Why do we collect this data?</h3>
            <p>This data is collected for the purpose of developing a face recognition application as part of this internship project.</p>

            <h3>How is your data stored?</h3>
            <p>Photos submitted on the site are not stored in our database. Only the biometric vectors derived from the processing of your photo are retained. This data will be kept for the duration of the project.</p>

            <h3>Who has access to your data?</h3>
            <p>Only the creators of this project (Anthony Miranda and Lea Carminati) have access to your biometric data. No data is shared with third parties.</p>

            <h3>Consent</h3>
            <p>In accordance with the GDPR, the processing of your biometric data requires your explicit consent. You can provide it by checking the "I agree to the privacy policy" box on our site.</p>

            <h3>Your rights</h3>
            <p>You have the right to request the deletion of your data from our database at any time. To exercise your rights, you can contact us at the following email addresses:</p>
            <ul>
                <li>Anthony Miranda : <a href="mailto:anthony.miranda@etu.univ-mtp3.fr">anthony.miranda@etu.univ-mtp3.fr</a></li>
                <li>Lea Carminati : <a href="mailto:lea.carminati@etu.univ-mtp3.fr">lea.carminati@etu.univ-mtp3.fr</a></li>
            </ul>

        </div>
    </div>

<?php include("components/footer.php") ;?>

</div>
</body>
</html>