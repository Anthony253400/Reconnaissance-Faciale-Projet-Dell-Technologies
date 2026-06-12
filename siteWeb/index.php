<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Recognition — Home</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="assets/css/navbar.css">
    <link rel="stylesheet" href="assets/css/footer.css">
    <link rel="stylesheet" href="assets/css/scanner.css">

    <script src="assets/js/scanner.js"></script>
    <script src="assets/js/navbar.js"></script>

    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont/dist/tabler-icons.min.css">


    <style>
        @import url('assets/css/variables/variables.css');


        .steps-section {
            padding: 5rem 1.5rem;
            max-width: 1100px;
            margin: 0 auto;
        }
        .steps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 5rem;
            position: relative;
        }
 
        /* connector line between cards (desktop only) */
        @media (min-width: 768px) {
            .steps-grid::before {
                content: '';
                position: absolute;
                top: 38px;
                left: calc(12.5% + 28px);
                right: calc(12.5% + 28px);
                height: 2px;
                background: linear-gradient(90deg, var(--blue-light), var(--blue-mid), var(--blue-light));
                z-index: 0;
            }
        }
 
        .step-card {
            background: var(--white);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.75rem 1.5rem;
            text-align: center;
            transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
            position: relative;
            z-index: 1;
        
        }
        .step-card:hover {
            box-shadow: 0 8px 28px rgb(var(--dell-blue) / 0.6);
            transform: translateY(-4px);
            border-color: var(--dell-blue);
            background: color-mix(in srgb, var(--dell-blue-soft) 50%, transparent);        
        }
        .step-icon-wrap {
            width: 64px; height: 64px;
            border-radius: 50%;
            background: var(--blue-light);
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 1.25rem;
            position: relative;
        }
        .step-icon-wrap i { font-size: 1.6rem; color: var(--blue-main); }
        .step-number {
            position: absolute;
            top: -6px; right: -6px;
            width: 22px; height: 22px;
            background: var(--blue-main);
            color: #fff;
            font-size: 0.7rem;
            font-weight: 800;
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            border: 2px solid var(--white);
        }
        .step-card h4 {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
            color: var(--text-dark);
        }
        .step-card p {
            font-size: 0.88rem;
            color: var(--text-muted);
            line-height: 1.65;
            margin-bottom: 1.25rem;
        }
        .btn-step {
            display: inline-block;
            background: var(--blue-light);
            color: var(--blue-main);
            border: 1px solid var(--blue-mid);
            padding: 7px 20px;
            border-radius: 999px;
            font-size: 0.83rem;
            font-weight: 700;
            text-decoration: none;
            transition: background 0.15s, color 0.15s;
        }
        .btn-step:hover { background: var(--blue-main); color: #fff; border-color: var(--blue-main); }
        </style>
</head>
<body>

<?php include("components/navbar.php"); ?>

<div class="ui-layer">
    <div class="container">

        <div class="hero">
            <div id="hero-scanner-bg">
                <?php include("components/scanner.php"); ?>
            </div>

            <div class="hero-content">
                <div class="hero-badge">Dell Technologies Montpellier</div>
                <h1 class="hero-title">Real time face recognition</h1>
                <p class="hero-sub">Register a person once, then let the camera recognise them automatically even from behind or at a distance.</p>
                <div class="btn-row centered">
                    <a href="register.php" class="btn btn-primary">Register a person</a>
                    <a href="detection.php" class="btn btn-secondary">Start detection</a>
                </div>
            </div>
        </div>

        <div class="home-divider"></div>

        <div class="home-section">
            <p class="section-label">About the project</p>
            <p class="home-text">This application was built as part of a curricular internship at Dell Technologies Montpellier. The goal: recognise people in real time using only a webcam.</p>
            <p class="home-text">You register someone once by recording their face for a few seconds. From then on, the camera can identify them automatically.</p>
        </div>

        <div class="home-section">

        <section class="steps-section">
            <div class="section-eyebrow">
                <p class="eyebrow">Get started</p>
                <h2>How to use the platform</h2>
                <p class="desc">Follow these steps to register faces and run live detection in just a few minutes.</p>
            </div>
         
            <div class="steps-grid">
                <a href="register.php" class="step-card">
                    
                    <div class="step-icon-wrap">
                            <i class="ti ti-user-plus"></i>
                        <span class="step-number">1</span>
                    </div>
                    <h4>Register</h4>
                    <p>Add a person to the database using your webcam or by uploading a photo. The system captures multiple angles for better accuracy.</p>
                </a>

                <a href="detection.php"  class="step-card">
                    <div class="step-icon-wrap">
                        <i class="ti ti-scan"></i>
                        <span class="step-number">2</span>
                    </div>
                    <h4>Detect</h4>
                    <p>Point your webcam at any registered person. The AI identifies faces in real time and displays the match with a confidence score.</p>
                </a>
         
                <a href="manage.php" class="step-card">
                    <div class="step-icon-wrap">
                        <i class="ti ti-database"></i>
                        <span class="step-number">3</span>
                    </div>
                    <h4>Manage</h4>
                    <p>Browse the database of registered people, remove entries, or update records. Keep control over who the system can recognize.</p>
                </a>


            </div>

        <?php /*  
        </section>
            <div class="hiw-list">
                <div class="hiw-item">
                    <div class="hiw-icon">01</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Register a person</h3>
                        <p class="hiw-desc">Go to the Register page. Point the webcam at someone, press the button, and move your head slowly in all directions for about 7 seconds. Then enter their name and click "Add to database".</p>
                    </div>
                </div>
                <div class="hiw-item">
                    <div class="hiw-icon">02</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Start detection</h3>
                        <p class="hiw-desc">Go to the Detect page. The camera starts automatically and identifies registered people in real time. A coloured box appears around each person, green if recognised with high confidence, yellow if uncertain.</p>
                    </div>
                </div>
                <div class="hiw-item">
                    <div class="hiw-icon">03</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Works even from behind</h3>
                        <p class="hiw-desc">If someone turns away from the camera, the system can still identify them using their body shape and appearance no face needed.</p>
                    </div>
                </div>
                <div class="hiw-item">
                    <div class="hiw-icon">04</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Privacy first</h3>
                        <p class="hiw-desc">No photos are ever saved. Your explicit consent is required before anything is stored. You can ask for your data to be deleted at any time.</p>
                    </div>
                </div>
            </div>
        </div>

        */;?>
        
        <div class="home-divider"></div>


        <div class="home-divider"></div>

        <div class="home-section">
            <p class="section-label">Under the hood</p>
            <div class="hiw-list">
                <div class="hiw-item">
                    <div class="hiw-icon">01</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Face detection & embedding</h3>
                        <p class="hiw-desc">Faces are detected using MediaPipe BlazeFace. Each face is then aligned and passed through ArcFace, which produces a unique 512-dimensional vector (embedding) representing that person's facial features.</p>
                    </div>
                </div>
                <div class="hiw-item">
                    <div class="hiw-icon">02</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Body re-identification</h3>
                        <p class="hiw-desc">Body detection is handled by YOLOv8. A custom tracker links body detections to previously identified faces, allowing re-identification even when the face is not visible.</p>
                    </div>
                </div>
                <div class="hiw-item">
                    <div class="hiw-icon">03</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Vector database & matching</h3>
                        <p class="hiw-desc">Embeddings are stored in Qdrant, a vector database. At inference time, the live embedding is compared against stored ones using cosine similarity. A score above 0.70 is considered a confident match; between 0.50 and 0.70 it is flagged as uncertain.</p>
                    </div>
                </div>
                <div class="hiw-item">
                    <div class="hiw-icon">04</div>
                    <div class="hiw-body">
                        <h3 class="hiw-title">Real-time pipeline</h3>
                        <p class="hiw-desc">Frames are streamed from the browser to a FastAPI backend via WebSocket. Detection, embedding and matching happen server-side on each frame, and results are sent back instantly to update the overlay.</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="home-divider"></div>

        <div class="cta-grid">
            <div class="cta-card cta-main">
                <p class="cta-label">Step 1</p>
                <h3 class="cta-title">Register a person</h3>
                <p class="cta-desc">Point the webcam at someone, press the button, and move your head slowly for a few seconds. Fill in their name and you're done.</p>
                <a href="register.php" class="btn btn-primary">Go to Register</a>
            </div>
            <div class="cta-card">
                <p class="cta-label">Step 2</p>
                <h3 class="cta-title">Start detection</h3>
                <p class="cta-desc">Open the live camera view. Registered people will be identified automatically with a coloured box around their face.</p>
                <a href="detection.php" class="btn btn-secondary">Go to Detect</a>
            </div>
            <div class="cta-card">
                <p class="cta-desc">Curious about how we evaluate the model?</p>
                <a href="statistics.php" class="btn btn-secondary">View Evaluation Statistics</a>
            </div>
        </div>



    </div>

    <?php include("components/footer.php") ;?>

</div>
</body>
</html>