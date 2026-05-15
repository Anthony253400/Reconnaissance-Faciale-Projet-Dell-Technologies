import numpy as np
from scipy.optimize import linear_sum_assignment

# CONFIGURABLE PARAMETERS 
REENTRY_EMBEDDING_THRESHOLD = 0.75  # minimum cosine similarity to recognise a returning person
MAX_LOST_FRAMES = 1800  # frames before forgetting a person (1 min at 30fps, 2 min at 15fps)


def compute_iou(boxA, boxB):
    """
    Computes the Intersection over Union (IoU) between two bounding boxes.
    Args:
        boxA (list): A bounding box in the format [x1, y1, x2, y2].
        boxB (list): Another bounding box in the format [x1, y1, x2, y2].
    Returns:
        float: The IoU value between 0 and 1, where 0 means no overlap and 1 means perfect overlap.
    """
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    intersection = max(0, xB - xA) * max(0, yB - yA)
    if intersection == 0:
        return 0.0

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union = areaA + areaB - intersection

    if union == 0:
        return 0.0

    return intersection / float(union)


def iou_matrix(face_boxes, body_boxes):
    """
    Computes the IoU matrix between detected face boxes and body boxes.
    Args:
        face_boxes (list): A list of face bounding boxes in the format [x1, y1, x2, y2].
        body_boxes (list): A list of body bounding boxes in the format [x1, y1, x2, y2].
    Returns:
        numpy.ndarray: An IoU matrix of shape (n_faces, n_bodies).
    """
    matrix = np.zeros((len(face_boxes), len(body_boxes)))
    for i, face in enumerate(face_boxes):
        for j, body in enumerate(body_boxes):
            matrix[i, j] = compute_iou(face, body)
    return matrix


def assign_faces_to_bodies(face_boxes, body_boxes, threshold=0.3):
    """
    Assigns face boxes to body boxes using the Hungarian algorithm.
    Args:
        face_boxes (list): Face bounding boxes [x1, y1, x2, y2].
        body_boxes (list): Body bounding boxes [x1, y1, x2, y2].
        threshold (float): Minimum IoU to consider a valid assignment.
    Returns:
        dict: {body_index: face_index}
    """
    if not face_boxes or not body_boxes:
        return {}

    matrix = iou_matrix(face_boxes, body_boxes)
    row_ind, col_ind = linear_sum_assignment(-matrix)

    assignments = {}
    for face_id, body_id in zip(row_ind, col_ind):
        if matrix[face_id, body_id] >= threshold:
            assignments[body_id] = face_id
    return assignments


def get_centroid(box):
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def centroid_distance(box1, box2):
    c1 = get_centroid(box1)
    c2 = get_centroid(box2)
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)


class BodyTracker:
    def __init__(
        self,
        iou_threshold=0.1,
        max_distance=80,
        max_lost_frames=MAX_LOST_FRAMES,
        reentry_threshold=REENTRY_EMBEDDING_THRESHOLD,
    ):
        """
        Initializes the BodyTracker.
        Args:
            iou_threshold (float): Min IoU to link a face to a body.
            max_distance (float): Max centroid distance (px) for short-term tracking.
            max_lost_frames (int): Frames before forgetting a person (1-2 min at 15-30fps).
            reentry_threshold (float): Min cosine similarity to recognise a returning person.
        """
        self.iou_threshold    = iou_threshold
        self.max_distance     = max_distance
        self.max_lost_frames  = max_lost_frames
        self.reentry_threshold = reentry_threshold

        # {name: {"last_box": [...], "lost_frames": int, "embedding": np.ndarray|None}}
        self.tracks = {}

    def update(self, face_boxes, body_boxes, face_names, body_crops=None):
        """
        Updates the tracker with new detections.

        Priority order for each unidentified body:
          1. IoU match with a known face  →  use face name
          2. Centroid distance (short-term, person still in frame)
          3. Embedding similarity  (re-entry after leaving the camera)

        Args:
            face_boxes (list): Face bounding boxes [x1, y1, x2, y2].
            body_boxes (list): Body bounding boxes [x1, y1, x2, y2].
            face_names (list): Names for each face box (can be "" if unknown).
            body_crops (list|None): BGR crops for each body box (same order).
                                    Required for re-entry recognition.
        Returns:
            list: Name assigned to each body box (same order as body_boxes).
        """
        from bodyEmbeddings import get_body_embedding

        result_names = [""] * len(body_boxes)
        confirmed_body_indices = set()

        # STEP 1: IoU face to body 
        assignments = assign_faces_to_bodies(face_boxes, body_boxes, self.iou_threshold)

        for body_id, face_id in assignments.items():
            name = face_names[face_id]
            if name:
                result_names[body_id] = name
                confirmed_body_indices.add(body_id)

                # compute body embedding and update the track
                embedding = None
                if body_crops is not None and body_id < len(body_crops):
                    embedding = get_body_embedding(body_crops[body_id])

                self.tracks[name] = {
                    "last_box":   body_boxes[body_id],
                    "lost_frames": 0,
                    "embedding":  embedding,
                }

        # STEP 2 bodies not yet identified 
        unmatched = [i for i in range(len(body_boxes)) if i not in confirmed_body_indices]

        for body_id in unmatched:
            best_name     = None
            best_distance = self.max_distance

            # STEP 2 — centroid distance (person still in frame)
            for name, track in self.tracks.items():
                dist = centroid_distance(body_boxes[body_id], track["last_box"])
                if dist < best_distance:
                    best_distance = dist
                    best_name     = name

            # STEP 3 embedding similarity (re-entry after leaving the camera)
            if best_name is None and body_crops is not None and body_id < len(body_crops):
                query_emb = get_body_embedding(body_crops[body_id])
                best_sim  = self.reentry_threshold

                for name, track in self.tracks.items():
                    ref_emb = track.get("embedding")
                    if ref_emb is None:
                        continue
                    sim = float(np.dot(query_emb, ref_emb))
                    if sim > best_sim:
                        best_sim  = sim
                        best_name = name

            if best_name:
                result_names[body_id] = best_name

                # update the track (embedding only if crop is available)
                embedding = self.tracks[best_name].get("embedding")
                if body_crops is not None and body_id < len(body_crops):
                    embedding = get_body_embedding(body_crops[body_id])

                self.tracks[best_name] = {
                    "last_box":    body_boxes[body_id],
                    "lost_frames": 0,
                    "embedding":   embedding,
                }

        #remove lost tracks 
        names_to_delete = []
        for name, track in self.tracks.items():
            if name not in result_names:
                self.tracks[name]["lost_frames"] += 1
                if self.tracks[name]["lost_frames"] > self.max_lost_frames:
                    names_to_delete.append(name)
        for name in names_to_delete:
            del self.tracks[name]

        return result_names