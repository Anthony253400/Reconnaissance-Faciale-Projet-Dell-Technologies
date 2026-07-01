<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manage</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/manage.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">

    <script src="assets/js/navbar.js"></script>
    <script src="assets/js/footer.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
    <script src="assets/js/manage.js"></script>
</head>
<body>
    <?php include("components/navbar.php"); ?>

    <div class="container">
        <header class="page-header">
            <h1>Manage people</h1>
            <p class="subtitle">View, rename and delete people registered in the database.</p>
        </header>

        <section class="section-card">
            <h2>Registered people</h2>
            <p id="status" class="people-status"></p>
            <ul id="people-list" class="people-list"></ul>
        </section>

        <section class="section-card">
            <div class="viz-header">
                <h2>Embeddings (3D)</h2>
                <button id="reload-viz" class="btn btn-rename">Reload</button>
            </div>
            <p id="viz-status" class="people-status"></p>
            <div id="viz-plot" class="viz-plot"></div>
        </section>
    </div>



    <?php include("components/footer.php"); ?>
</body>
</html>