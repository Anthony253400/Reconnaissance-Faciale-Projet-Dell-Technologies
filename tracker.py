import numpy as np
from scipy.optimize import linear_sum_assignment

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
    
    iou = intersection / float(union) 
    return iou

def iou_matrix(face_boxes, body_faces):
    """
    Computes the Intersection over Union (IoU) 
    matrix between detected face boxes and body boxes.
    Args:
        face_boxes (list): A list of face bounding boxes in the format [x1, y1, x2, y2].
        body_faces (list): A list of body bounding boxes in the format [x1, y1, x2, y2].
    Returns:
        numpy.ndarray: An IoU matrix of shape (n_faces, n_bodies) where each element [i, j] 
        contains the IoU between face_boxes[i] and body_faces[j].
    """
    n_faces = len(face_boxes)
    n_bodies = len(body_faces)
    matrix = np.zeros((n_faces, n_bodies))

    for i, face in enumerate(face_boxes):
        for j, body in enumerate(body_faces):
            matrix[i, j] = compute_iou(face, body)
    return matrix

def assign_faces_to_bodies(face_boxes, body_faces, threshold=0.3):
    """
    Assigns detected face boxes to body boxes based on the IoU matrix.
    Args:
        face_boxes (list): A list of face bounding boxes in the format [x1, y1, x2, y2].
        body_faces (list): A list of body bounding boxes in the format [x1, y1, x2, y2].
        threshold (float): The minimum IoU required to consider a valid assignment.
    Returns:
        dict: A dictionary mapping each body index to the assigned face index. 
        If a body has no assigned face, it will not be included in the dictionary.
    """
    if not face_boxes or not body_faces:
        return {}

    matrix = iou_matrix(face_boxes, body_faces)
    
    #Hungarian algorithm or Munkres algorithm
    row_ind, col_ind = linear_sum_assignment(-matrix) # maximize IoU by negating the matrix

    assignments = {}
    for face_id, body_id in zip(row_ind, col_ind):
        if matrix[face_id, body_id] >= threshold:
            assignments[body_id] = face_id  # link body index to face index
    return assignments

def get_centroid(box):
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    return (cx, cy)

def centroid_distance(box1, box2):
    c1 = get_centroid(box1)
    c2 = get_centroid(box2)
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

class BodyTracker:
    def __init__(self, iou_threshold=0.1, max_distance=80, max_lost_frames=30):
        """
        Initializes the BodyTracker with specified parameters.
        Args:   iou_threshold (float): The minimum IoU required to consider a valid assignment between face and body.  
                max_distance (float): The maximum distance in pixels to consider for matching a face to a body.  
                max_lost_frames (int): The maximum number of consecutive frames a track can be lost before it is removed.
        """
        self.iou_threshold = iou_threshold
        self.max_distance = max_distance
        self.max_lost_frames = max_lost_frames
        self.tracks = {}  # {track_id: {'box': [x1, y1, x2, y2], 'lost_frames': int}}

    def update(self, face_boxes, body_boxes, face_names):
        """
        Updates the tracker with new detections and assigns face names to body tracks.
        Args:
            face_boxes (list): A list of face bounding boxes in the format [x1, y1, x2, y2].
            body_boxes (list): A list of body bounding boxes in the format [x1, y1, x2, y2].
            face_names (list): A list of names corresponding to each detected face box.
        Returns:
            dict: A dictionary mapping each body index to the assigned face name. 
            If a body has no assigned face, it will be mapped to "Inconnu".
        """
        result_names= [""] * len(body_boxes)

        #link face to body via Hungarian algorithm
        assignments = assign_faces_to_bodies(face_boxes, body_boxes, self.iou_threshold)

        confirmed_body_indices = set()
        
        for body_id, face_id in assignments.items():
            name = face_names[face_id]
            if name:
                result_names[body_id] = name
                confirmed_body_indices.add(body_id)
                self.tracks[name] = {
                    "last_box": body_boxes[body_id],
                    "lost_frames": 0
                }
        
        # identify remaining bodies via centroid distance
        unmatched_body_indices =[
            i for i in range(len(body_boxes)) 
            if i not in confirmed_body_indices
            ]
        for body_id in unmatched_body_indices:
            best_match = None
            best_distance = self.max_distance

            for name, track in self.tracks.items():
                dist = centroid_distance(body_boxes[body_id], track["last_box"])
                if dist < best_distance:
                    best_distance = dist
                    best_match = name
            
            if best_match:
                result_names[body_id] = best_match
                self.tracks[best_match] = {
                    "last_box": body_boxes[body_id],   
                    "lost_frames": 0
                }
        
        # remove old tracks
        names_to_delete = []
        for name, track in self.tracks.items():
            if name not in result_names:
                self.tracks[name]["lost_frames"] += 1
                if self.tracks[name]["lost_frames"] > self.max_lost_frames:
                    names_to_delete.append(name)
        for name in names_to_delete:
            del self.tracks[name]
        return result_names
    
