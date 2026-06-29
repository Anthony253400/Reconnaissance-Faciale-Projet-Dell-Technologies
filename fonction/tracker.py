import numpy as np
from scipy.optimize import linear_sum_assignment
import sys
from fonction.bodyEmbeddings import get_body_embedding


sys.path.append('../')


# CONFIGURABLE PARAMETERS
REENTRY_EMBEDDING_THRESHOLD = 0.75  # (unused now) kept for backward compatibility
MAX_LOST_FRAMES = 1800              # hard cap before forgetting (safety net)


def compute_iou(boxA, boxB):
    """IoU between two boxes [x1, y1, x2, y2]."""
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
    matrix = np.zeros((len(face_boxes), len(body_boxes)))
    for i, face in enumerate(face_boxes):
        for j, body in enumerate(body_boxes):
            matrix[i, j] = compute_iou(face, body)
    return matrix


def assign_faces_to_bodies(face_boxes, body_boxes, threshold=0.3):
    """Hungarian assignment face->body. Returns {body_index: face_index}."""
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
    return np.sqrt((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2)


def box_diagonal(box):
    return np.sqrt((box[2] - box[0]) ** 2 + (box[3] - box[1]) ** 2)


def touches_border(box, frame_w, frame_h, margin=12):
    """True if the box is at the edge of the frame (person leaving the scene)."""
    x1, y1, x2, y2 = box
    return (x1 <= margin or y1 <= margin or
            x2 >= frame_w - margin or y2 >= frame_h - margin)


class BodyTracker:
    def __init__(
        self,
        iou_threshold=0.1,
        max_distance=120,
        max_lost_frames=MAX_LOST_FRAMES,
        reentry_threshold=REENTRY_EMBEDDING_THRESHOLD,
        size_tolerance=0.85,
        grace_frames=15,
        frame_w=640,
        frame_h=480,
    ):
        """
        Args:
            iou_threshold (float): Min IoU to link a face to a body.
            max_distance (float): Max centroid shift (px) between frames to treat
                two body boxes as the SAME person. Real matches measured at 1-7px,
                wrong cross-pairs at 200+px, so 120 is a very safe middle ground.
            size_tolerance (float): Max relative box-size change still accepted
                while tracking. Turning the body changes YOLO's box shape a lot
                (measured up to ~0.85), so this is intentionally loose.
            grace_frames (int): How many frames a name survives WITHOUT any body
                detection (YOLO drop-outs) before it disappears, as long as the
                person did not leave through the border.
            frame_w, frame_h (int): Frame size, to detect border exits.
        """
        self.iou_threshold   = iou_threshold
        self.max_distance    = max_distance
        self.max_lost_frames = max_lost_frames
        self.size_tolerance  = size_tolerance
        self.grace_frames    = grace_frames
        self.frame_w         = frame_w
        self.frame_h         = frame_h

        # {name: {"last_box": [...], "lost_frames": int, "at_border": bool}}
        self.tracks = {}

    def update(self, face_boxes, body_boxes, face_names, body_crops=None):
        """
        STEP 1 - recognised face overlapping a body  -> assign + confirm name.
        STEP 2 - body without a face this frame: keep a known name if it is
                 essentially where that same body was last frame (small shift,
                 loosely similar size). Bridges head-turns.
        Forgetting:
          - body detected but moved off through the border -> forget now.
          - body NOT detected at all (YOLO drop): keep the name for up to
            grace_frames, UNLESS its last position was at the border (it left).
        Returns: name (or "") per body box, same order as body_boxes.
        """
        result_names = [""] * len(body_boxes)
        used_names = set()

        # ---- STEP 1: recognised face -> body -------------------------------
        assignments = assign_faces_to_bodies(face_boxes, body_boxes, self.iou_threshold)
        for body_id, face_id in assignments.items():
            name = face_names[face_id]
            if name and name not in used_names:
                result_names[body_id] = name
                used_names.add(name)
                self._touch(name, body_boxes[body_id])

        # ---- STEP 2: position continuity for un-named bodies ---------------
        unmatched = [i for i in range(len(body_boxes)) if not result_names[i]]
        candidates = []
        for body_id in unmatched:
            body_box = body_boxes[body_id]
            body_diag = box_diagonal(body_box)
            for name, track in self.tracks.items():
                if name in used_names:
                    continue
                dist = centroid_distance(body_box, track["last_box"])
                if dist > self.max_distance:
                    continue
                ref_diag = box_diagonal(track["last_box"])
                if ref_diag > 0 and abs(body_diag - ref_diag) / ref_diag > self.size_tolerance:
                    continue
                candidates.append((dist, body_id, name))

        candidates.sort(key=lambda c: c[0])
        for dist, body_id, name in candidates:
            if result_names[body_id] or name in used_names:
                continue
            result_names[body_id] = name
            used_names.add(name)
            self._touch(name, body_boxes[body_id])

        # ---- forgetting logic ----------------------------------------------
        to_delete = []
        for name, track in self.tracks.items():
            if name in result_names:
                continue   # confirmed this frame, already refreshed
            # not seen this frame
            track["lost_frames"] += 1
            left_scene = track["at_border"]
            if left_scene:
                # person was at the edge and is now gone -> forget immediately
                to_delete.append(name)
            elif track["lost_frames"] > self.grace_frames:
                to_delete.append(name)
            elif track["lost_frames"] > self.max_lost_frames:
                to_delete.append(name)
        for name in to_delete:
            del self.tracks[name]

        return result_names

    def _touch(self, name, box):
        """Refresh a track with the current box."""
        self.tracks[name] = {
            "last_box":   box,
            "lost_frames": 0,
            "at_border":   touches_border(box, self.frame_w, self.frame_h),
        }