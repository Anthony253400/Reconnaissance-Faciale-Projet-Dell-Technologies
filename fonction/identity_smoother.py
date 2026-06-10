from collections import deque, Counter


class IdentitySmoother:
    """
    Stabilizza nome E score visualizzati per un volto.

    Nome  : voto a maggioranza con isteresi — per cambiare nome servono
            `min_votes` voti a favore del nuovo nella finestra.
    Score : media mobile esponenziale (EMA), ma il valore MOSTRATO viene
            aggiornato solo ogni `score_hold` riconoscimenti → il numero
            resta fermo a schermo invece di ballare a ogni ciclo.
    """

    def __init__(self, window=20, min_votes=10, min_score=0.45,
                 score_alpha=0.10, score_hold=15):
        self.window = window
        self.min_votes = min_votes
        self.min_score = min_score
        self.score_alpha = score_alpha   # peso del nuovo score nell'EMA
        self.score_hold = score_hold     # ogni quanti voti rinfrescare il display

        self.votes = deque(maxlen=window)
        self.stable_name = None
        self._ema = None                 # score interno, aggiornato sempre
        self._shown = None               # score mostrato, aggiornato raramente
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
            # nessun voto valido in tutta la finestra → identità persa
            self.stable_name = None
            self._ema = self._shown = None

        # EMA interna: segue lo score reale ma lentamente
        if vote == self.stable_name and vote is not None:
            self._ema = (raw_score if self._ema is None
                         else self.score_alpha * raw_score
                              + (1 - self.score_alpha) * self._ema)

        # rinfresca il valore mostrato solo ogni score_hold voti
        self._since_refresh += 1
        if self._since_refresh >= self.score_hold and self._ema is not None:
            self._shown = self._ema
            self._since_refresh = 0
        if self._shown is None:
            self._shown = self._ema

        return self.stable_name, self._shown


class SmootherBank:
    """Uno smoother per volto (indicizzato per posizione — vedi nota multi-persona)."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.smoothers = {}

    def update(self, face_idx, raw_name, raw_score):
        if face_idx not in self.smoothers:
            self.smoothers[face_idx] = IdentitySmoother(**self.kwargs)
        return self.smoothers[face_idx].update(raw_name, raw_score)

    def prune(self, n_faces):
        self.smoothers = {k: v for k, v in self.smoothers.items() if k < n_faces}