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

    <script>
    const API = "http://localhost:8000";  // adjust the port if needed

    async function loadPeople() {
        const ul = document.getElementById("people-list");
        const status = document.getElementById("status");
        ul.innerHTML = "";
        status.textContent = "Loading…";
        try {
            const res = await fetch(`${API}/people`);
            const data = await res.json();
            if (!data.people.length) {
                status.textContent = "No people registered.";
                return;
            }
            status.textContent = "";
            data.people.forEach(p => {
                const li = document.createElement("li");
                li.className = "person-row";

                const info = document.createElement("div");
                info.className = "person-info";
                const nameEl = document.createElement("span");
                nameEl.className = "person-name";
                nameEl.textContent = p.name;
                const meta = document.createElement("span");
                meta.className = "person-meta";
                meta.textContent = `${p.samples} photo${p.samples > 1 ? "s" : ""}`;
                info.append(nameEl, meta);

                const actions = document.createElement("div");
                actions.className = "person-actions";

                const renameBtn = document.createElement("button");
                renameBtn.className = "btn";
                renameBtn.textContent = "Rename";
                renameBtn.onclick = () => renamePerson(p.name, renameBtn);

                const delBtn = document.createElement("button");
                delBtn.className = "btn btn-danger";
                delBtn.textContent = "Delete";
                delBtn.onclick = () => deletePerson(p.name, delBtn);

                actions.append(renameBtn, delBtn);
                li.append(info, actions);
                ul.appendChild(li);
            });
        } catch (e) {
            status.textContent = "Could not connect to the server.";
        }
    }

    async function renamePerson(name, btn) {
        const newName = prompt(`Rename « ${name} » to:`, name);
        if (newName === null) return;            // cancelled
        const clean = newName.trim();
        if (!clean || clean === name) return;     // empty or unchanged
        btn.disabled = true;
        btn.textContent = "Renaming…";
        try {
            await fetch(`${API}/people/${encodeURIComponent(name)}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ new_name: clean }),
            });
            loadPeople();
            loadViz();
        } catch (e) {
            btn.disabled = false;
            btn.textContent = "Rename";
        }
    }

    async function deletePerson(name, btn) {
        if (!confirm(`Delete all data for « ${name} »?`)) return;
        btn.disabled = true;
        btn.textContent = "Deleting…";
        try {
            await fetch(`${API}/people/${encodeURIComponent(name)}`, { method: "DELETE" });
            loadPeople();
            loadViz();
        } catch (e) {
            btn.disabled = false;
            btn.textContent = "Delete";
        }
    }

    // ── 3D embedding visualization ──────────────────────────────────
    // distinct colors per person, assigned on the fly
    const VIZ_PALETTE = [
        "#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed",
        "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5",
    ];

    async function loadViz() {
        const status = document.getElementById("viz-status");
        const plot = document.getElementById("viz-plot");
        status.textContent = "Computing projection…";
        try {
            const res = await fetch(`${API}/embeddings_3d`);
            const data = await res.json();
            const pts = data.points || [];
            if (!pts.length) {
                status.textContent = "No embeddings to display.";
                Plotly.purge(plot);
                return;
            }
            status.textContent = "";

            // group points by name -> one trace per person (own color + legend)
            const groups = {};
            pts.forEach(p => {
                (groups[p.name] = groups[p.name] || []).push(p);
            });

            const traces = Object.keys(groups).map((name, idx) => {
                const g = groups[name];
                return {
                    type: "scatter3d",
                    mode: "markers",
                    name: name,
                    x: g.map(p => p.x),
                    y: g.map(p => p.y),
                    z: g.map(p => p.z),
                    marker: {
                        size: 5,
                        color: VIZ_PALETTE[idx % VIZ_PALETTE.length],
                        opacity: 0.85,
                    },
                    hovertemplate: `${name}<extra></extra>`,
                };
            });

            const layout = {
                margin: { l: 0, r: 0, t: 0, b: 0 },
                showlegend: true,
                legend: { font: { size: 12 } },
                scene: {
                    xaxis: { title: "", showticklabels: false },
                    yaxis: { title: "", showticklabels: false },
                    zaxis: { title: "", showticklabels: false },
                },
                paper_bgcolor: "rgba(0,0,0,0)",
            };

            Plotly.newPlot(plot, traces, layout, { responsive: true, displaylogo: false });
        } catch (e) {
            status.textContent = "Could not load the projection.";
        }
    }

    document.getElementById("reload-viz").onclick = loadViz;

    loadPeople();
    loadViz();
    </script>

    <?php include("components/footer.php"); ?>
</body>
</html>