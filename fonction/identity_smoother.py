from collections import deque, Counter


class IdentitySmoother:
    """
    Stabilizes the displayed NAME and SCORE for a single face.

    Name  : majority vote with hysteresis — to switch to a new name it needs
            `min_votes` votes in its favor within the window.
    Score : exponential moving average (EMA), but the DISPLAYED value is only
            refreshed every `score_hold` recognitions -> the number stays
            steady on screen instead of flickering on every cycle.
    """

    def __init__(self, window=20, min_votes=10, min_score=0.45,
                 score_alpha=0.10, score_hold=15):
        self.window = window
        self.min_votes = min_votes
        self.min_score = min_score
        self.score_alpha = score_alpha   # weight of the new score in the EMA
        self.score_hold = score_hold     # how many votes between display refreshes

        self.votes = deque(maxlen=window)
        self.stable_name = None
        self._ema = None                 # internal score, always updated
        self._shown = None               # displayed score, rarely updated
        self._since_refresh = 0

    def update(self, raw_name, raw_score):
        vote = raw_name if (raw_name and raw_score is not None
                            and raw_score >= self.min_score) else None
        self.votes.append(vote)

        counts = Counter(v for v in self.votes if v is not None)
        if counts:
            best, n = counts.most_common(1)[0]
            if best != self.stable_name and n >= self.min_votes:
                self.stable_name = best
                self._ema = raw_score if vote == best else None
                self._shown = self._ema
                self._since_refresh = 0
        elif len(self.votes) == self.window:
            # no valid vote in the whole window -> identity lost
            self.stable_name = None
            self._ema = self._shown = None

        # internal EMA: follows the real score, but slowly
        if vote == self.stable_name and vote is not None:
            self._ema = (raw_score if self._ema is None
                         else self.score_alpha * raw_score
                              + (1 - self.score_alpha) * self._ema)

        # refresh the displayed value only every score_hold votes
        self._since_refresh += 1
        if self._since_refresh >= self.score_hold and self._ema is not None:
            self._shown = self._ema
            self._since_refresh = 0
        if self._shown is None:
            self._shown = self._ema

        return self.stable_name, self._shown


class SmootherBank:
    """
    One smoother per PERSON, keyed by spatial continuity instead of by position
    in the array (MediaPipe does not guarantee a stable face ordering between
    frames). Each face in the current frame is matched to the nearest face from
    the previous frame (nearest-centroid); that stable ID is the smoother key.
    This way one person's votes never end up in another person's slot, which is
    exactly what was causing the names to swap.
    """

    def __init__(self, match_dist=120, **kwargs):
        self.kwargs = kwargs
        self.match_dist = match_dist     # max px to treat two boxes as the "same person"
        self.smoothers = {}              # {track_id: IdentitySmoother}
        self.prev_centroids = {}         # {track_id: (cx, cy)}
        self._next_id = 0

    @staticmethod
    def _centroid(box):
        x1, y1, x2, y2 = box
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def update_frame(self, face_boxes, raw_names, raw_scores):
        """
        Process ALL faces of the frame in a single call.
        Args:
            face_boxes: list of boxes [x1,y1,x2,y2], same order as raw_names/raw_scores
            raw_names, raw_scores: raw output of search_embedding for each face
        Returns:
            (names, scores) lists aligned with face_boxes, with stabilized identities.
        """
        n = len(face_boxes)
        names = [None] * n
        scores = [None] * n

        # 1. match each current face to the nearest track ID from the previous frame
        assigned = {}                      # face_index -> track_id
        used_tracks = set()
        for i, box in enumerate(face_boxes):
            cx, cy = self._centroid(box)
            best_id, best_d = None, self.match_dist
            for tid, (pcx, pcy) in self.prev_centroids.items():
                if tid in used_tracks:
                    continue
                d = ((cx - pcx) ** 2 + (cy - pcy) ** 2) ** 0.5
                if d < best_d:
                    best_d, best_id = d, tid
            if best_id is None:
                # new face: create a fresh stable track
                best_id = self._next_id
                self._next_id += 1
                self.smoothers[best_id] = IdentitySmoother(**self.kwargs)
            assigned[i] = best_id
            used_tracks.add(best_id)

        # 2. update the correct smoother for each face
        new_centroids = {}
        for i, box in enumerate(face_boxes):
            tid = assigned[i]
            name, score = self.smoothers[tid].update(raw_names[i], raw_scores[i])
            names[i] = name
            scores[i] = score
            new_centroids[tid] = self._centroid(box)

        # 3. keep only the tracks seen in this frame (the others have left)
        self.prev_centroids = new_centroids
        self.smoothers = {tid: s for tid, s in self.smoothers.items()
                          if tid in new_centroids}

        return names, scores