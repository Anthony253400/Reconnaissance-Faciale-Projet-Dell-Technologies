# eval_tools.py
import cv2
import numpy as np
from collections import defaultdict
from sklearn.metrics import auc
import plotly.express as px
import matplotlib.pyplot as plt



# ── Pipeline ──

def numpy_to_bytes(img_array):
    """Convert a float32 numpy image (LFW format) to JPEG bytes."""
    img_uint8 = (img_array * 255).astype(np.uint8)
    img_bgr = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', img_bgr)
    return buffer.tobytes()


def run_pipeline(image_bytes, detector, client, collection_name, label_true, is_genuine,
                 align_crop_fn, get_embedding_fn, FacesDetects_fn, arcface_model):
    """
    Run the full recognition pipeline on a single image.
    Always returns a dict with a 'status' field:
      - "ok"                 -> match completed (contains label/score/...)
      - "no_detection"       -> MediaPipe did not detect any face
      - "rejected_alignment" -> face detected but discarded by the frontality gate
      - "bad_embedding"      -> embedding is not finite (NaN/inf)
      - "qdrant_error"       -> error on the Qdrant side
    """
    boxes, detection_result, image = FacesDetects_fn(image_bytes, "mediapipe", detector)

    if not detection_result or not detection_result.detections:
        return {"status": "no_detection", "label_true": label_true, "is_genuine": is_genuine}

    crops = align_crop_fn(image, detection_result, method="mediapipe")
    if not crops:
        # Face detected but no crop produced -> discarded by the _YAW_MAX gate
        return {"status": "rejected_alignment", "label_true": label_true, "is_genuine": is_genuine}

    embedding = get_embedding_fn(crops[0], arcface_model)

    if not np.isfinite(embedding).all():
        return {"status": "bad_embedding", "label_true": label_true, "is_genuine": is_genuine}

    try:
        raw = client.query_points(
            collection_name=collection_name,
            query=embedding.tolist(),
            limit=1
        ).points
    except Exception as e:
        print(f"Qdrant error for {label_true}: {e}")
        return {"status": "qdrant_error", "label_true": label_true, "is_genuine": is_genuine}

    if not raw:
        score, predicted_name = 0.0, "unknown"
    else:
        score = raw[0].score
        predicted_name = raw[0].payload["name"]

    return {
        "status": "ok",
        "label_true": label_true,
        "predicted_name": predicted_name,
        "score": score,
        "is_genuine": is_genuine,
    }
# ── Metrics ──

def true_accept_rate(genuine_results, t):
    """TAR = fraction of genuine attempts correctly accepted at threshold t."""
    correct = sum(1 for r in genuine_results
                  if r["score"] >= t and r["predicted_name"] == r["label_true"])
    return correct / len(genuine_results)


def false_accept_rate(impostor_results, t):
    """FAR = fraction of impostor attempts incorrectly accepted at threshold t."""
    wrong = sum(1 for r in impostor_results if r["score"] >= t)
    return wrong / len(impostor_results)


def false_reject_rate(genuine_results, t):
    """FRR = fraction of genuine attempts incorrectly rejected at threshold t."""
    wrong = sum(1 for r in genuine_results if r["score"] < t or r["predicted_name"] != r["label_true"])
    return wrong / len(genuine_results)


def compute_metrics(genuine_results, impostor_results, thresholds):
    """
    Compute TAR, FAR, FRR and EER over a range of thresholds.
    Returns a dict with arrays and EER info.
    """
    tar_list = np.array([true_accept_rate(genuine_results, t) for t in thresholds])
    far_list = np.array([false_accept_rate(impostor_results, t) for t in thresholds])
    frr_list = np.array([false_reject_rate(genuine_results, t) for t in thresholds])

    eer_idx       = np.argmin(np.abs(far_list - frr_list))
    eer_value     = (far_list[eer_idx] + frr_list[eer_idx]) / 2
    eer_threshold = thresholds[eer_idx]

    return {
        "tar": tar_list,
        "far": far_list,
        "frr": frr_list,
        "eer_value": eer_value,
        "eer_threshold": eer_threshold,
        "eer_idx": eer_idx,
        "auc": auc(far_list, tar_list)
    }

# ── Bootstrap ──

def bootstrap_metric(genuine_results, impostor_results, thresholds,
                     metric_key="eer_value", n_boot=1000, seed=42):
    """
    Estimate a 95% confidence interval for a metric via bootstrap.

    Resamples WITH REPLACEMENT the two groups (genuine and impostor)
    SEPARATELY, keeping each group size fixed, and recomputes the metric
    on every synthetic sample.

    Parameters
    ----------
    genuine_results, impostor_results : list[dict]
        Observed results (the same lists passed to compute_metrics).
    thresholds : np.ndarray
        Threshold grid used for the metrics.
    metric_key : str
        Which scalar value to extract from the compute_metrics dict,
        e.g. "eer_value" or "auc".
    n_boot : int
        Number of bootstrap samples (B).
    seed : int
        Seed for reproducibility.

    Returns
    -------
    dict with: point (value on the original data, NOT the bootstrap mean),
    ci_low, ci_high (2.5th and 97.5th percentiles), mean, std, and the full
    array of bootstrap values.
    """
    rng = np.random.default_rng(seed)

    genuine = np.array(genuine_results, dtype=object)
    impostor = np.array(impostor_results, dtype=object)
    n_g = len(genuine)
    n_i = len(impostor)

    # point estimate on the real data (NOT the bootstrap mean)
    point = compute_metrics(genuine_results, impostor_results, thresholds)[metric_key]

    boot_values = np.empty(n_boot)
    for b in range(n_boot):
        # separate resampling, with replacement
        idx_g = rng.integers(0, n_g, size=n_g)
        idx_i = rng.integers(0, n_i, size=n_i)
        g_sample = genuine[idx_g].tolist()
        i_sample = impostor[idx_i].tolist()

        m = compute_metrics(g_sample, i_sample, thresholds)
        boot_values[b] = m[metric_key]

    return {
        "point":   point,
        "ci_low":  np.percentile(boot_values, 2.5),
        "ci_high": np.percentile(boot_values, 97.5),
        "mean":    boot_values.mean(),
        "std":     boot_values.std(),
        "values":  boot_values,
    }



def tar_at_far(metrics, thresholds, target_far):
    """
    Maximum TAR while keeping FAR under a fixed budget.

    Picks the most permissive threshold (i.e. the one with the highest TAR)
    among all thresholds that keep FAR <= target_far. This is the typical
    operating point of a biometric system: "given the FAR we allow, how much
    do we correctly recognize?".

    Parameters
    ----------
    metrics : dict
        Output of compute_metrics (uses the 'far' and 'tar' keys).
    thresholds : np.ndarray
        The same threshold grid passed to compute_metrics.
    target_far : float
        Maximum allowed FAR (e.g. 0.01 for 1%).

    Returns
    -------
    dict with 'tar', 'far', 'threshold' at the chosen point, or None if no
    threshold satisfies the FAR budget.
    """
    far = metrics["far"]
    tar = metrics["tar"]
    ok = np.where(far <= target_far)[0]   # thresholds within the FAR budget
    if len(ok) == 0:
        return None
    best = ok[np.argmax(tar[ok])]         # among those, the one with highest TAR
    return {"tar": tar[best], "far": far[best], "threshold": thresholds[best]}

def get_condition(filename):
    """Extract the acquisition condition from a filename following the
    convention `<name>_<condition><index>.<ext>` (e.g. 'lea_glasses1.jpg'
    -> 'glasses'). Returns 'unknown' if the name does not match."""
    try:
        return filename.split('_')[1].split('.')[0].rstrip('0123456789')
    except (IndexError, AttributeError):
        return 'unknown'
    
def d_prime(genuine, impostor):
    """Separability index between genuine and impostor score distributions.
    d' = (mean_g - mean_i) / sqrt((var_g + var_i) / 2).
    Assumes roughly normal distributions; used here as a separability indicator,
    not an exact measure (our custom distribution is not perfectly gaussian)."""
    g = np.array([r["score"] for r in genuine])
    i = np.array([r["score"] for r in impostor])
    return (g.mean() - i.mean()) / np.sqrt((g.var() + i.var()) / 2)

def reduce_3d(X, method="pca", random_state=42):
    """Project 512D embeddings down to 3D. method in {'pca','tsne','umap'}.
    ArcFace embeddings are L2-normalised -> use the cosine metric where possible."""
    X = np.asarray(X, dtype=np.float32)
    if method == "pca":
        from sklearn.decomposition import PCA
        return PCA(n_components=3, random_state=random_state).fit_transform(X)
    if method == "tsne":
        from sklearn.manifold import TSNE
        # perplexity must stay < n_samples
        perp = min(30, max(5, (len(X) - 1) // 3))
        return TSNE(n_components=3, metric="cosine", init="pca",
                    perplexity=perp, random_state=random_state).fit_transform(X)
    if method == "umap":
        try:
            import umap
        except ImportError:
            print("umap-learn not installed -> falling back to PCA. "
                  "Install with: pip install umap-learn")
            return reduce_3d(X, method="pca", random_state=random_state)
        n_neighbors = min(15, max(2, len(X) - 1))
        return umap.UMAP(n_components=3, metric="cosine",
                         n_neighbors=n_neighbors, random_state=random_state).fit_transform(X)
    raise ValueError(f"unknown method: {method}")

def plot_embeddings_3d(X, y, method="tsne", title=None):
    """Interactive 3D scatter plot, one colour per identity."""
    coords = reduce_3d(X, method=method)
    y = np.asarray(y)
    fig = px.scatter_3d(
        x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
        color=y, hover_name=y,
        title=title or f"3D embeddings ({method.upper()}) — {len(X)} vectors, "
                       f"{len(np.unique(y))} identities",
        labels={"x": "dim 1", "y": "dim 2", "z": "dim 3", "color": "person"},
    )
    fig.update_traces(marker=dict(size=4, opacity=0.8,
                                  line=dict(width=0.5, color="white")))
    fig.update_layout(legend=dict(itemsizing="constant"), height=650)
    fig.show()
    return coords

# === Retrieve vectors from the Qdrant database ===
def fetch_db_vectors(client, collection, name_field="name"):
    """Download every stored point with its vector and the label from the payload."""
    X, y = [], []
    next_page = None
    while True:
        points, next_page = client.scroll(
            collection_name=collection,
            with_vectors=True, with_payload=True,
            limit=256, offset=next_page,
        )
        for p in points:
            vec = p.vector
            if isinstance(vec, dict):          # named vectors -> take the first one
                vec = next(iter(vec.values()))
            X.append(vec)
            y.append(p.payload.get(name_field, "unknown"))
        if next_page is None:
            break
    return np.array(X, dtype=np.float32), np.array(y)

def plot_roc(m, title="ROC Curve"):
    """Plot a single ROC curve (FAR vs TAR) with the EER point marked.
    m: dict returned by compute_metrics."""
    plt.figure(figsize=(7, 5))
    plt.plot(m['far'], m['tar'], color='steelblue', lw=2,
             label=f"ROC (AUC = {m['auc']:.3f})")
    plt.plot([0, 1], [0, 1], 'k--', lw=1, label='Random')
    plt.scatter(m['far'][m['eer_idx']], m['tar'][m['eer_idx']],
                color='red', zorder=5, label=f"EER = {m['eer_value']:.3f}")
    plt.xlabel('False Accept Rate')
    plt.ylabel('True Accept Rate')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()