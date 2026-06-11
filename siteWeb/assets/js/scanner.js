/**
 * SCANNER ANIMATION — Reconnaissance faciale
 * ─────────────────────────────────────────────────────────
 * Initialise et pilote tous les composants visuels du scanner :
 *   • Coins du cadre
 *   • Points de landmark (repères du visage)
 *   • Badge d'état (scanning / matched / uncertain)
 *   • Overlay de résultat
 *   • Transition vers l'état "reconnu"
 *
 * Usage :
 *   const scanner = new FaceScanner('#my-wrapper');
 *   scanner.init();
 *   scanner.setMatched('Jean Dupont', 0.94);
 *   scanner.reset();
 */
class FaceScanner {

  /**
   * @param {string|Element} target  Sélecteur CSS ou élément DOM du .scanner-wrapper
   * @param {Object}         options
   * @param {number}  options.landmarkCount   Nombre de points de repère (défaut : 12)
   * @param {number}  options.scanDelay       Délai avant de lancer le scan auto (ms, défaut : 800)
   * @param {boolean} options.showGrid        Afficher la grille HUD (défaut : true)
   * @param {boolean} options.autoDemo        Lancer un cycle démo automatique (défaut : false)
   */
  constructor(target, options = {}) {
    this.wrapper = typeof target === 'string'
      ? document.querySelector(target)
      : target;

    if (!this.wrapper) {
      console.warn('[FaceScanner] Élément introuvable :', target);
      return;
    }

    this.opts = Object.assign({
      landmarkCount: 12,
      scanDelay:     800,
      showGrid:      true,
      autoDemo:      false,
    }, options);

    this.state      = 'idle';
    this._landmarks = [];
    this._timers    = [];
  }

  /* ══════════════════════════════════════════════════════
     INIT — construit le DOM interne et démarre
     ══════════════════════════════════════════════════════ */
  init() {
    this._buildDOM();
    if (this.opts.showGrid) this._addGrid();

    const delay = this.opts.scanDelay;
    this._timers.push(setTimeout(() => this._startScan(), delay));

    if (this.opts.autoDemo) this._runDemo();

    return this;
  }

  /* ── Construit les éléments internes ─────────────────── */
  _buildDOM() {
    // Cadre
    this.frame = this.wrapper.querySelector('.scan-frame');
    if (!this.frame) {
      this.frame = document.createElement('div');
      this.frame.className = 'scan-frame';
      this.wrapper.appendChild(this.frame);
    }

    // Ligne de scan
    this.scanLine = this.frame.querySelector('.scan-line');
    if (!this.scanLine) {
      this.scanLine = document.createElement('div');
      this.scanLine.className = 'scan-line';
      this.frame.appendChild(this.scanLine);
    }

    // Badge d'état
    this.badge = this.wrapper.querySelector('.scan-badge');
    if (!this.badge) {
      this.badge = document.createElement('div');
      this.badge.className = 'scan-badge scan-badge--scanning';
      this.badge.innerHTML = '<span class="scan-badge-dot"></span><span class="scan-badge-text">Analyse en cours…</span>';
      this.badge.style.cssText = 'position:absolute;top:-36px;left:50%;transform:translateX(-50%)';
      this.wrapper.appendChild(this.badge);
    }

    this.badgeText = this.badge.querySelector('.scan-badge-text');

    // Overlay résultat
    this.result = this.wrapper.querySelector('.scan-result');
    if (!this.result) {
      this.result = document.createElement('div');
      this.result.className = 'scan-result';
      this.result.innerHTML = '<div class="scan-result-name"></div><div class="scan-result-score"></div>';
      this.wrapper.appendChild(this.result);
    }

    this.resultName  = this.result.querySelector('.scan-result-name');
    this.resultScore = this.result.querySelector('.scan-result-score');
  }

  /* ── Ajoute les coins bas du cadre ───────────────────── */
  _addCorners() {
    ['bl', 'br'].forEach(pos => {
      if (!this.frame.querySelector(`.scan-corner.${pos}`)) {
        const corner = document.createElement('span');
        corner.className = `scan-corner ${pos}`;
        this.frame.appendChild(corner);
      }
    });
  }

  /* ── Ajoute la grille HUD ────────────────────────────── */
  _addGrid() {
    if (!this.frame.querySelector('.scan-grid')) {
      const grid = document.createElement('div');
      grid.className = 'scan-grid';
      this.frame.appendChild(grid);
    }
  }

  /* ══════════════════════════════════════════════════════
     ÉTATS
     ══════════════════════════════════════════════════════ */

  /* ── Démarre le scan (état : scanning) ───────────────── */
  _startScan() {
    this.state = 'scanning';
    this._setBadge('scanning', 'Analyse en cours…');
    this._spawnLandmarks();
  }

  /* ── Affiche les points de landmark progressivement ──── */
  _spawnLandmarks() {
    this._clearLandmarks();

    const positions = this._getLandmarkPositions(this.opts.landmarkCount);

    positions.forEach((pos, i) => {
      const t = setTimeout(() => {
        if (this.state !== 'scanning') return;
        const dot = document.createElement('div');
        dot.className = 'scan-landmark';
        dot.style.left = pos.x + '%';
        dot.style.top  = pos.y + '%';
        dot.style.animationDelay = '0s';
        this.frame.appendChild(dot);
        this._landmarks.push(dot);
      }, i * 80);
      this._timers.push(t);
    });
  }

  /* ── Positions réalistes pour les landmarks faciaux ──── */
  _getLandmarkPositions(n) {
    const base = [
      { x: 32, y: 38 }, { x: 50, y: 36 }, { x: 68, y: 38 },
      { x: 26, y: 50 }, { x: 74, y: 50 },
      { x: 32, y: 55 }, { x: 50, y: 53 }, { x: 68, y: 55 },
      { x: 38, y: 64 }, { x: 50, y: 68 }, { x: 62, y: 64 },
      { x: 50, y: 80 }, { x: 38, y: 75 }, { x: 62, y: 75 },
    ];
    return base.slice(0, Math.min(n, base.length)).map(p => ({
      x: p.x + (Math.random() - 0.5) * 4,
      y: p.y + (Math.random() - 0.5) * 4,
    }));
  }

  /* ── Efface les landmarks ────────────────────────────── */
  _clearLandmarks() {
    this._landmarks.forEach(el => el.remove());
    this._landmarks = [];
  }

  /* ══════════════════════════════════════════════════════
     API PUBLIQUE
     ══════════════════════════════════════════════════════ */

  /**
   * Passe en état "match confirmé"
   * @param {string} name   Nom de la personne reconnue
   * @param {number} score  Score de confiance (0–1)
   */
  setMatched(name, score = 0.94) {
    this.state = 'matched';
    this._setBadge('matched', 'Identifié');
    this.frame.classList.add('scan-frame--matched');
    this.frame.classList.remove('scan-frame--uncertain');

    // Fige la ligne de scan
    this.scanLine.style.animationPlayState = 'paused';

    // Affiche le résultat
    this.resultName.textContent  = name;
    this.resultScore.textContent = `Score : ${(score * 100).toFixed(1)} %`;
    this.result.classList.add('visible');

    return this;
  }

  /**
   * Passe en état "match incertain"
   * @param {string} name   Nom probable
   * @param {number} score  Score entre 0.50 et 0.70
   */
  setUncertain(name, score = 0.58) {
    this.state = 'uncertain';
    this._setBadge('uncertain', 'Incertain');
    this.frame.classList.add('scan-frame--uncertain');
    this.frame.classList.remove('scan-frame--matched');

    this.resultName.textContent  = name + ' ?';
    this.resultScore.textContent = `Score : ${(score * 100).toFixed(1)} %`;
    this.result.classList.add('visible');

    return this;
  }

  /**
   * Repasse en état "scanning" (efface le résultat)
   */
  reset() {
    this.state = 'scanning';
    this._clearLandmarks();
    this.frame.classList.remove('scan-frame--matched', 'scan-frame--uncertain');
    this.result.classList.remove('visible');
    this.scanLine.style.animationPlayState = 'running';
    this._setBadge('scanning', 'Analyse en cours…');
    this._spawnLandmarks();
    return this;
  }

  /**
   * Stoppe toutes les animations et timers
   */
  destroy() {
    this._timers.forEach(clearTimeout);
    this._timers = [];
    this._clearLandmarks();
    this.state = 'idle';
  }

  /* ── Met à jour le badge ─────────────────────────────── */
  _setBadge(state, text) {
    this.badge.className = `scan-badge scan-badge--${state}`;
    this.badge.style.cssText = 'position:absolute;top:-36px;left:50%;transform:translateX(-50%)';
    if (!this.badge.querySelector('.scan-badge-dot')) {
      const dot = document.createElement('span');
      dot.className = 'scan-badge-dot';
      this.badge.prepend(dot);
    }
    if (this.badgeText) this.badgeText.textContent = text;
  }

  /* ══════════════════════════════════════════════════════
     MODE DÉMO AUTOMATIQUE
     Cycle : scan → match → reset → …
     ══════════════════════════════════════════════════════ */
  _runDemo() {
    const names  = ['Lucas Martin', 'Sarah Dupont', 'Théo Bernard'];
    const scores = [0.94, 0.62, 0.88];
    let   idx    = 0;

    const cycle = () => {
      this.reset();

      // Après 3 s de scan, afficher le match
      const t1 = setTimeout(() => {
        const s = scores[idx % scores.length];
        if (s >= 0.70) this.setMatched(names[idx % names.length], s);
        else           this.setUncertain(names[idx % names.length], s);
        idx++;
      }, 3000);

      // Après 2 s supplémentaires, recommencer
      const t2 = setTimeout(() => cycle(), 5200);

      this._timers.push(t1, t2);
    };

    const t0 = setTimeout(() => cycle(), this.opts.scanDelay + 200);
    this._timers.push(t0);
  }
}

/* ══════════════════════════════════════════════════════════
   UTILISATION SIMPLE (sans instanciation)
   ══════════════════════════════════════════════════════════

  // Instancier
  const scanner = new FaceScanner('.scanner-wrapper', {
    landmarkCount: 12,
    scanDelay: 600,
    showGrid: true,
    autoDemo: false,
  });
  scanner.init();

  // Résultat depuis votre backend WebSocket :
  socket.onmessage = (e) => {
    const { name, score } = JSON.parse(e.data);
    if (score >= 0.70)      scanner.setMatched(name, score);
    else if (score >= 0.50) scanner.setUncertain(name, score);
    else                    scanner.reset();
  };

  // Lancer le mode démo visuel (sans backend) :
  const demo = new FaceScanner('.scanner-wrapper', { autoDemo: true });
  demo.init();

══════════════════════════════════════════════════════════ */

/* Export pour modules ES / CommonJS */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FaceScanner;
}