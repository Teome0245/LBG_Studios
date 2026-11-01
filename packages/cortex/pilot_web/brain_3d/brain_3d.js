/**
 * Cerveau 3D Cybernétique — Visualisation volumétrique du Studio Brain & Réseau Synaptique V2
 * LBG Studios (Inspiration @ccodelabfr - "J'ai donné un cerveau à mon IA 🧠⚡").
 *
 * Moteur Three.js hyper-dynamique avec :
 * - 1500 neurones scintillants (modulation EEG par onde cérébrale)
 * - 180 influx synaptiques vifs (Action Potentials / Sparks) qui parcourent les axones à haute vitesse
 * - Arcs électriques synaptiques crépitants (Lightning Arcs) reliant les Pôles cognitifs réels
 * - Onde volumétrique de balayage IRMf / EEG (Scan Wave)
 * - Télémétrie infra en temps réel (Fréquence Hz, influx/sec, activité des VMs et de la Team)
 *
 * Exposé sur : window.LbgBrain3d = { start, stop, sync, triggerPulse, triggerSurge, focusPole, setFilter, isRunning }
 */
(function (global) {
  "use strict";

  let _container = null;
  let _scene = null;
  let _camera = null;
  let _renderer = null;
  let _animId = null;
  let _running = false;
  let _onSelectPole = null;

  // Objets 3D principaux
  let _brainGroup = null;
  let _neuronPoints = null;
  let _neuronPositionsOrig = null;
  let _neuronColorsOrig = null;
  let _synapseLines = null;
  let _synapseEdges = []; // Paires de Vector3 pour les axones

  // Influx synaptiques actifs (Action Potentials / Sparks 3D)
  let _pulsesPoints = null;
  let _pulseData = [];
  const PULSE_COUNT = 300;

  // Arcs électriques dynamiques entre pôles (Neural Lightning)
  let _arcsGroup = null;
  let _lightningArcs = [];

  // Pôle récemment stimulé par l'infra
  let _activeInfraPoles = new Map();

  // Onde de scan IRMf
  let _scanWave = null;
  let _scanWaveZ = -1.8;

  // Pôles cognitifs
  let _polesGroup = null;
  let _polesMap = new Map();

  // Contrôles interactifs (Orbit & Drag)
  let _isDragging = false;
  let _prevMousePos = { x: 0, y: 0 };
  let _targetRot = { x: 0.15, y: -0.4 };
  let _currentRot = { x: 0.15, y: -0.4 };
  let _cameraDist = 5.6;
  let _targetCameraDist = 5.6;
  let _autoRotate = true;
  let _lastInteractionTs = 0;

  // Raycaster & Interaction
  let _raycaster = null;
  let _mouseNorm = { x: -999, y: -999 };
  let _hoveredPole = null;
  let _selectedPoleKey = null;

  // Caméra lerp focus
  let _targetLookAt = { x: 0, y: 0, z: 0 };
  let _currentLookAt = { x: 0, y: 0, z: 0 };
  let _tempFocusTimer = 0;
  let _isTempFocused = false;

  // Dynamique cérébrale & Activité
  let _activityLevel = 1.0; // 1.0 = nominal, 2.5 = surge, 0.4 = veille
  let _surgeTimer = 0;
  let _eegHz = 38.4;
  let _synapseRate = 165;

  // Données de télémétrie du Brain
  let _brainData = {
    enabled: true,
    intent: "monitor",
    narrative: "",
    gauges: { confidence: 75, curiosity: 45, stress: 15, fatigue: 10 },
  };

  /** Définition des Pôles Cognitifs réels de l'IA LBG Studios */
  const POLES = {
    cortex: {
      key: "cortex",
      name: "Cortex Frontal",
      sub: "Orchestrateur & Intent (VM 140)",
      pos: [0, 0.95, 1.35],
      color: 0x00f5d4, // Cyan néon
      icon: "⚡",
      desc: "Centre décisionnel et planification des intentions Studio (POST /v1/pilot/route).",
    },
    limbic: {
      key: "limbic",
      name: "Système Limbique",
      sub: "Homéostasie & Jauges",
      pos: [0, -0.25, 0.15],
      color: 0xf59e0b, // Or / Ambre
      icon: "💖",
      desc: "Régulation des jauges intérieures : curiosité, confiance, stress et fatigue.",
    },
    hippo: {
      key: "hippo",
      name: "Hippocampe & RAG",
      sub: "Mémoire & Philo (VM 110 LLM)",
      pos: [0.95, -0.45, -0.45],
      color: 0xa855f7, // Violet améthyste
      icon: "📚",
      desc: "Mémoire long-terme, corpus Stoïcien / Mec Chill et inférences Ollama E4b-qat.",
    },
    fleet: {
      key: "fleet",
      name: "Noyau Campus & Fleet",
      sub: "7 Agents de la Team",
      pos: [-1.05, 0.4, 0.55],
      color: 0x10b981, // Vert émeraude
      icon: "🤖",
      desc: "Supervision des agents spécialisés (Chef, Infra, Front, LLM, Prime, Outgame).",
    },
    world: {
      key: "world",
      name: "Perception Monde",
      sub: "Godot Prime (VM 246 :8787)",
      pos: [-0.9, 0.55, -0.95],
      color: 0x38bdf8, // Ciel / Saphir
      icon: "🌐",
      desc: "Connexion autoritaire Godot hub .246:8787, signaux météo et économie.",
    },
    lyra: {
      key: "lyra",
      name: "Lobe Compagnon",
      sub: "Lyra Desktop Pet (SDS .10)",
      pos: [0.95, 0.5, 0.65],
      color: 0xf43f5e, // Rose cyber
      icon: "🎭",
      desc: "Pont d'incarnation avec le Desktop Pet SDS .10 et dialogue compagnon.",
    },
  };

  /** Liens majeurs d'arcs électriques entre pôles */
  const POLE_CONNECTIONS = [
    ["cortex", "hippo"],
    ["cortex", "fleet"],
    ["cortex", "limbic"],
    ["limbic", "lyra"],
    ["fleet", "world"],
    ["hippo", "lyra"],
  ];

  /** Texture de particule luminescente circulaire */
  function createGlowTexture(THREE) {
    const canvas = document.createElement("canvas");
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext("2d");
    const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, "rgba(255, 255, 255, 1)");
    grad.addColorStop(0.25, "rgba(0, 245, 212, 0.95)");
    grad.addColorStop(0.6, "rgba(56, 189, 248, 0.45)");
    grad.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(canvas);
  }

  /** Texture d'étincelle synaptique vive */
  function createSparkTexture(THREE) {
    const canvas = document.createElement("canvas");
    canvas.width = 32;
    canvas.height = 32;
    const ctx = canvas.getContext("2d");
    const grad = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
    grad.addColorStop(0, "rgba(255, 255, 255, 1)");
    grad.addColorStop(0.3, "rgba(254, 240, 138, 0.95)");
    grad.addColorStop(0.7, "rgba(0, 245, 212, 0.5)");
    grad.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 32, 32);
    return new THREE.CanvasTexture(canvas);
  }

  /**
   * Construit les deux hémisphères neuronaux et les synapses
   */
  function buildBrainModel(THREE) {
    const group = new THREE.Group();
    const particleCount = 1500;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    _neuronPositionsOrig = new Float32Array(particleCount * 3);
    _neuronColorsOrig = new Float32Array(particleCount * 3);

    const neuronCoords = [];

    // Paramètres anatomiques stylisés
    for (let i = 0; i < particleCount; i++) {
      const hemisphere = Math.random() < 0.5 ? -1 : 1;

      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);

      const rx = 1.05;
      const ry = 1.25;
      const rz = 1.65;

      // Plissements corticaux (gyri & sulci)
      const sulci = 1.0 +
        0.14 * Math.sin(5.0 * theta) * Math.cos(6.0 * phi) +
        0.09 * Math.cos(10.0 * phi) +
        0.07 * Math.sin(8.0 * theta);

      const depth = Math.pow(Math.random(), 0.35);
      const r = depth * sulci;

      let x = rx * r * Math.sin(phi) * Math.cos(theta);
      let y = ry * r * Math.sin(phi) * Math.sin(theta);
      let z = rz * r * Math.cos(phi);

      // Scissure inter-hémisphérique centrale
      const gap = 0.22;
      x = hemisphere * (Math.abs(x) * 0.92 + gap);

      if (y < -0.3) y *= 0.85;
      if (z < -0.8 && y < -0.2) {
        y -= 0.25;
        x *= 0.82;
      }

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      _neuronPositionsOrig[i * 3] = x;
      _neuronPositionsOrig[i * 3 + 1] = y;
      _neuronPositionsOrig[i * 3 + 2] = z;

      neuronCoords.push(new THREE.Vector3(x, y, z));

      // Nuances de couleur par hémisphère
      const col = new THREE.Color();
      if (hemisphere < 0) {
        // Hémisphère gauche (Logique / Code / Fleet / Infra) : Cyan à Cobalt
        col.setHSL(0.52 + Math.random() * 0.08, 0.95, 0.65);
      } else {
        // Hémisphère droit (Créatif / Philo / RAG / Lyra) : Ambre, Magenta & Rose
        col.setHSL(0.78 + Math.random() * 0.15, 0.9, 0.68);
      }

      colors[i * 3] = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;

      _neuronColorsOrig[i * 3] = col.r;
      _neuronColorsOrig[i * 3 + 1] = col.g;
      _neuronColorsOrig[i * 3 + 2] = col.b;
    }

    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const pMat = new THREE.PointsMaterial({
      size: 0.18,
      map: createGlowTexture(THREE),
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    _neuronPoints = new THREE.Points(geom, pMat);
    group.add(_neuronPoints);

    // Calcul des axones synaptiques et paires de propagation
    _synapseEdges = [];
    const linePositions = [];
    const lineColors = [];
    const maxConnectDist = 0.40;
    const maxNeighbors = 4;

    for (let i = 0; i < neuronCoords.length; i += 2) {
      let connections = 0;
      const p1 = neuronCoords[i];

      for (let j = i + 1; j < neuronCoords.length; j += 3) {
        const p2 = neuronCoords[j];
        const dist = p1.distanceTo(p2);

        if (dist < maxConnectDist) {
          linePositions.push(p1.x, p1.y, p1.z);
          linePositions.push(p2.x, p2.y, p2.z);

          _synapseEdges.push([p1, p2]);

          const alpha = 1.0 - dist / maxConnectDist;
          lineColors.push(0.0, 0.95 * alpha, 0.85 * alpha);
          lineColors.push(0.2 * alpha, 0.6 * alpha, 1.0 * alpha);

          connections++;
          if (connections >= maxNeighbors) break;
        }
      }
    }

    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    lineGeom.setAttribute("color", new THREE.Float32BufferAttribute(lineColors, 3));

    const lineMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.32,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    _synapseLines = new THREE.LineSegments(lineGeom, lineMat);
    group.add(_synapseLines);

    // Initialisation des VRAIES étincelles synaptiques 3D en mouvement (Action Potentials)
    buildSynapsePulses(THREE, group);

    // Onde de balayage volumétrique IRMf
    buildScanWave(THREE, group);

    return group;
  }

  /**
   * Construit le système de particules mobiles d'influx synaptiques
   */
  function buildSynapsePulses(THREE, parentGroup) {
    _pulseData = [];
    const pulsePositions = new Float32Array(PULSE_COUNT * 3);
    const pulseColors = new Float32Array(PULSE_COUNT * 3);

    for (let k = 0; k < PULSE_COUNT; k++) {
      const edge = _synapseEdges[Math.floor(Math.random() * _synapseEdges.length)] || [
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 0, 0),
      ];

      const pA = edge[0];
      const pB = edge[1];
      const prog = Math.random();

      _pulseData.push({
        pA,
        pB,
        progress: prog,
        speed: 0.015 + Math.random() * 0.035, // vitesse vive
        hue: Math.random() > 0.4 ? 0.5 : 0.12, // cyan ou ambre
      });

      const curr = pA.clone().lerp(pB, prog);
      pulsePositions[k * 3] = curr.x;
      pulsePositions[k * 3 + 1] = curr.y;
      pulsePositions[k * 3 + 2] = curr.z;

      const col = new THREE.Color().setHSL(_pulseData[k].hue, 1.0, 0.7);
      pulseColors[k * 3] = col.r;
      pulseColors[k * 3 + 1] = col.g;
      pulseColors[k * 3 + 2] = col.b;
    }

    const pulseGeom = new THREE.BufferGeometry();
    pulseGeom.setAttribute("position", new THREE.BufferAttribute(pulsePositions, 3));
    pulseGeom.setAttribute("color", new THREE.BufferAttribute(pulseColors, 3));

    const pulseMat = new THREE.PointsMaterial({
      size: 0.32,
      map: createSparkTexture(THREE),
      vertexColors: true,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    _pulsesPoints = new THREE.Points(pulseGeom, pulseMat);
    parentGroup.add(_pulsesPoints);
  }

  /**
   * Onde lumineuse de balayage IRMf / EEG
   */
  function buildScanWave(THREE, parentGroup) {
    const ringGeom = new THREE.TorusGeometry(1.6, 0.02, 16, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x00f5d4,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
    });
    _scanWave = new THREE.Mesh(ringGeom, ringMat);
    _scanWave.rotation.x = Math.PI * 0.5;
    parentGroup.add(_scanWave);
  }

  /**
   * Construit les 6 Pôles Cognitifs Interactifs et les Arcs Électriques
   */
  function buildPoles(THREE) {
    const group = new THREE.Group();
    _polesMap.clear();

    Object.values(POLES).forEach((def) => {
      const poleRoot = new THREE.Group();
      poleRoot.position.set(def.pos[0], def.pos[1], def.pos[2]);

      // Sphère centrale émissive
      const sphereGeom = new THREE.SphereGeometry(0.13, 24, 24);
      const sphereMat = new THREE.MeshBasicMaterial({
        color: def.color,
      });
      const sphere = new THREE.Mesh(sphereGeom, sphereMat);
      sphere.userData = { poleKey: def.key, isPole: true };
      poleRoot.add(sphere);

      // Halo externe pulsant
      const haloGeom = new THREE.SphereGeometry(0.22, 16, 16);
      const haloMat = new THREE.MeshBasicMaterial({
        color: def.color,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending,
      });
      const halo = new THREE.Mesh(haloGeom, haloMat);
      poleRoot.add(halo);

      // Anneau orbital 1
      const ring1Geom = new THREE.TorusGeometry(0.28, 0.014, 8, 32);
      const ring1Mat = new THREE.MeshBasicMaterial({
        color: def.color,
        transparent: true,
        opacity: 0.85,
      });
      const ring1 = new THREE.Mesh(ring1Geom, ring1Mat);
      ring1.rotation.x = Math.PI * 0.35;
      poleRoot.add(ring1);

      // Anneau orbital 2
      const ring2Geom = new THREE.TorusGeometry(0.35, 0.01, 8, 32);
      const ring2Mat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.6,
      });
      const ring2 = new THREE.Mesh(ring2Geom, ring2Mat);
      ring2.rotation.y = Math.PI * 0.4;
      poleRoot.add(ring2);

      group.add(poleRoot);

      _polesMap.set(def.key, {
        root: poleRoot,
        sphere,
        halo,
        ring1,
        ring2,
        def,
        baseScale: 1.0,
      });
    });

    // Construction des arcs électriques dynamiques reliant les pôles
    buildLightningArcs(THREE, group);

    return group;
  }

  /**
   * Construit les lignes d'arcs électriques entre pôles connectés
   */
  function buildLightningArcs(THREE, parentGroup) {
    _arcsGroup = new THREE.Group();
    _lightningArcs = [];

    const segmentsPerArc = 14;

    POLE_CONNECTIONS.forEach(([k1, k2]) => {
      const p1 = POLES[k1];
      const p2 = POLES[k2];
      if (!p1 || !p2) return;

      const geom = new THREE.BufferGeometry();
      const pos = new Float32Array((segmentsPerArc + 1) * 3);
      geom.setAttribute("position", new THREE.BufferAttribute(pos, 3));

      const mat = new THREE.LineBasicMaterial({
        color: 0x00f5d4,
        transparent: true,
        opacity: 0.75,
        blending: THREE.AdditiveBlending,
        linewidth: 2,
      });

      const line = new THREE.Line(geom, mat);
      _arcsGroup.add(line);

      _lightningArcs.push({
        line,
        geom,
        posAttr: geom.attributes.position,
        vStart: new THREE.Vector3(p1.pos[0], p1.pos[1], p1.pos[2]),
        vEnd: new THREE.Vector3(p2.pos[0], p2.pos[1], p2.pos[2]),
        segments: segmentsPerArc,
        pulseOffset: Math.random() * 10,
      });
    });

    parentGroup.add(_arcsGroup);
  }

  /**
   * Mise à jour de la forme des arcs électriques à chaque frame
   */
  function updateLightningArcs(time) {
    if (!_lightningArcs || _lightningArcs.length === 0) return;

    for (let a = 0; a < _lightningArcs.length; a++) {
      const arc = _lightningArcs[a];
      const pAttr = arc.posAttr;
      const count = arc.segments;

      // Pulsation d'intensité
      const flash = Math.sin(time * 8.0 + arc.pulseOffset);
      arc.line.material.opacity = flash > 0.2 ? 0.85 : 0.25;

      for (let s = 0; s <= count; s++) {
        const t = s / count;
        // Interpolation de base
        const x = arc.vStart.x + (arc.vEnd.x - arc.vStart.x) * t;
        const y = arc.vStart.y + (arc.vEnd.y - arc.vStart.y) * t;
        const z = arc.vStart.z + (arc.vEnd.z - arc.vStart.z) * t;

        // Déviation fractale électrique (nulle aux extrémités)
        const envelope = Math.sin(t * Math.PI);
        const jitter = (Math.random() - 0.5) * 0.16 * envelope * _activityLevel;

        pAttr.setXYZ(s, x + jitter, y + jitter, z + jitter);
      }
      pAttr.needsUpdate = true;
    }
  }

  /**
   * Animation Frame
   */
  function animate(THREE) {
    if (!_running) return;
    _animId = requestAnimationFrame(() => animate(THREE));

    const time = performance.now() * 0.001;

    // Décroissance douce du mode Surge
    if (_surgeTimer > 0) {
      _surgeTimer -= 0.016;
      if (_surgeTimer <= 0) _activityLevel = 1.0;
    }

    // Décroissance douce du focus temporaire
    if (_isTempFocused && _tempFocusTimer > 0) {
      _tempFocusTimer -= 0.016;
      if (_tempFocusTimer <= 0) {
        _isTempFocused = false;
        _targetLookAt.x = 0;
        _targetLookAt.y = 0;
        _targetLookAt.z = 0;
        _targetCameraDist = 5.6;
        _autoRotate = true;
        if (_selectedPoleKey && _polesMap.has(_selectedPoleKey)) {
          _polesMap.get(_selectedPoleKey).baseScale = 1.0;
        }
      }
    }

    // Rotation automatique douce
    if (_autoRotate && (Date.now() - _lastInteractionTs > 2800)) {
      _targetRot.y += 0.0035 * _activityLevel;
    }

    _currentRot.x += (_targetRot.x - _currentRot.x) * 0.08;
    _currentRot.y += (_targetRot.y - _currentRot.y) * 0.08;

    if (_brainGroup) {
      _brainGroup.rotation.x = _currentRot.x;
      _brainGroup.rotation.y = _currentRot.y;
    }

    _cameraDist += (_targetCameraDist - _cameraDist) * 0.1;
    _camera.position.z = _cameraDist;

    _currentLookAt.x += (_targetLookAt.x - _currentLookAt.x) * 0.08;
    _currentLookAt.y += (_targetLookAt.y - _currentLookAt.y) * 0.08;
    _currentLookAt.z += (_targetLookAt.z - _currentLookAt.z) * 0.08;
    _camera.lookAt(_currentLookAt.x, _currentLookAt.y, _currentLookAt.z);

    // 1. Déplacement des INFLUX SYNAPTIQUES (Sparks) le long des axones
    if (_pulsesPoints && _pulseData.length > 0) {
      const posAttr = _pulsesPoints.geometry.attributes.position;
      const speedMult = _activityLevel * 1.35;

      for (let k = 0; k < _pulseData.length; k++) {
        const p = _pulseData[k];
        p.progress += p.speed * speedMult;

        if (p.progress >= 1.0) {
          p.progress = 0;
          // Choisir une nouvelle synapse aléatoire
          const edge = _synapseEdges[Math.floor(Math.random() * _synapseEdges.length)];
          if (edge) {
            p.pA = edge[0];
            p.pB = edge[1];
          }
        }

        const px = p.pA.x + (p.pB.x - p.pA.x) * p.progress;
        const py = p.pA.y + (p.pB.y - p.pA.y) * p.progress;
        const pz = p.pA.z + (p.pB.z - p.pA.z) * p.progress;

        posAttr.setXYZ(k, px, py, pz);
      }
      posAttr.needsUpdate = true;
    }

    // 2. Balayage de l'Onde IRMf / EEG
    if (_scanWave) {
      _scanWaveZ += 0.015 * _activityLevel;
      if (_scanWaveZ > 1.8) _scanWaveZ = -1.8;
      _scanWave.position.z = _scanWaveZ;
      _scanWave.scale.setScalar(1.0 + 0.15 * Math.sin(time * 3.0));
    }

    // 3. Mise à jour des Arcs Électriques inter-pôles
    updateLightningArcs(time);

    // 4. Scintillement neuronal dynamique (ondes cérébrales EEG)
    if (_neuronPoints && _neuronColorsOrig) {
      const colAttr = _neuronPoints.geometry.attributes.color;
      const freq = _eegHz * 0.12;
      const wavePhase = time * freq;

      // Onde volumétrique sinusoïdale continue sur l'ensemble du cortex
      for (let i = 0; i < 1500; i++) {
        const x = _neuronPositionsOrig[i * 3];
        const z = _neuronPositionsOrig[i * 3 + 2];
        const wave = Math.sin(wavePhase + x * 2.5 + z * 3.2);
        const flicker = 0.75 + 0.38 * wave * _activityLevel;

        colAttr.setXYZ(
          i,
          Math.min(1.0, _neuronColorsOrig[i * 3] * flicker),
          Math.min(1.0, _neuronColorsOrig[i * 3 + 1] * flicker),
          Math.min(1.0, _neuronColorsOrig[i * 3 + 2] * flicker)
        );
      }
      colAttr.needsUpdate = true;
    }

    // 5. Animation des anneaux orbitaux et halos des Pôles (avec survoltage infra)
    _polesMap.forEach((entry, key) => {
      let infraBoost = 1.0;
      if (_activeInfraPoles.has(key)) {
        let timer = _activeInfraPoles.get(key);
        timer -= 0.016;
        if (timer <= 0) {
          _activeInfraPoles.delete(key);
        } else {
          _activeInfraPoles.set(key, timer);
          infraBoost = 1.0 + timer * 1.5; // Halo jusqu'à 2.5x plus grand lors d'un signal !
        }
      }

      entry.ring1.rotation.z += 0.035 * _activityLevel * infraBoost;
      entry.ring2.rotation.x += 0.025 * _activityLevel * infraBoost;

      const pulse = 1.0 + 0.15 * Math.sin(time * 5.0 + entry.root.position.x * 3.0);
      const scale = entry.baseScale * pulse * infraBoost;
      entry.halo.scale.set(scale, scale, scale);
    });

    // 6. Raycasting de la souris
    if (_raycaster && _camera && _polesGroup) {
      _raycaster.setFromCamera(new THREE.Vector2(_mouseNorm.x, _mouseNorm.y), _camera);
      const meshes = Array.from(_polesMap.values()).map((p) => p.sphere);
      const intersects = _raycaster.intersectObjects(meshes, false);

      const tooltip = document.getElementById("brain-3d-tooltip");

      if (intersects.length > 0) {
        const hit = intersects[0].object;
        const key = hit.userData.poleKey;
        const pole = _polesMap.get(key);

        if (_hoveredPole !== key) {
          _hoveredPole = key;
          if (pole) pole.baseScale = 1.35;
        }

        if (tooltip && _container) {
          const screenPos = hit.getWorldPosition(new THREE.Vector3()).project(_camera);
          const rect = _container.getBoundingClientRect();
          const px = ((screenPos.x + 1) * 0.5) * rect.width;
          const py = ((-screenPos.y + 1) * 0.5) * rect.height;

          tooltip.style.left = px + "px";
          tooltip.style.top = py + "px";
          tooltip.style.opacity = "1";

          const def = pole.def;
          tooltip.innerHTML = `
            <div class="brain-tooltip-title">${def.icon} ${def.name}</div>
            <div style="font-size:0.72rem; color:#94a3b8; margin-bottom:0.25rem;">${def.sub}</div>
            <div style="font-size:0.75rem; color:#cbd5e1;">${def.desc}</div>
          `;
        }
      } else {
        if (_hoveredPole) {
          const old = _polesMap.get(_hoveredPole);
          if (old && _selectedPoleKey !== _hoveredPole) old.baseScale = 1.0;
          _hoveredPole = null;
        }
        if (tooltip) {
          tooltip.style.opacity = "0";
        }
      }
    }

    _renderer.render(_scene, _camera);
  }

  /**
   * Initialisation des écouteurs de souris et de redimensionnement
   */
  function bindEvents(container, THREE) {
    const onPointerDown = (e) => {
      _isDragging = true;
      _autoRotate = false;
      _lastInteractionTs = Date.now();
      _prevMousePos.x = e.clientX;
      _prevMousePos.y = e.clientY;
    };

    const onPointerMove = (e) => {
      const rect = container.getBoundingClientRect();
      _mouseNorm.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      _mouseNorm.y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);

      if (_isDragging) {
        const dx = e.clientX - _prevMousePos.x;
        const dy = e.clientY - _prevMousePos.y;
        _targetRot.y += dx * 0.007;
        _targetRot.x += dy * 0.007;
        _targetRot.x = Math.max(-Math.PI * 0.45, Math.min(Math.PI * 0.45, _targetRot.x));
        _prevMousePos.x = e.clientX;
        _prevMousePos.y = e.clientY;
        _lastInteractionTs = Date.now();
      }
    };

    const onPointerUp = () => {
      if (_isDragging) {
        _isDragging = false;
        _lastInteractionTs = Date.now();
      }
    };

    const onWheel = (e) => {
      e.preventDefault();
      _lastInteractionTs = Date.now();
      _targetCameraDist += e.deltaY * 0.0035;
      _targetCameraDist = Math.max(3.2, Math.min(8.5, _targetCameraDist));
    };

    const onClick = () => {
      if (_hoveredPole) {
        selectPole(_hoveredPole);
      }
    };

    const onResize = () => {
      if (!_container || !_camera || !_renderer) return;
      const w = _container.clientWidth;
      const h = _container.clientHeight;
      if (w > 0 && h > 0) {
        _camera.aspect = w / h;
        _camera.updateProjectionMatrix();
        _renderer.setSize(w, h);
      }
    };

    container.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    container.addEventListener("wheel", onWheel, { passive: false });
    container.addEventListener("click", onClick);
    window.addEventListener("resize", onResize);

    container._cleanupEvents = () => {
      container.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      container.removeEventListener("wheel", onWheel);
      container.removeEventListener("click", onClick);
      window.removeEventListener("resize", onResize);
    };
  }

  /**
   * Sélectionne et focalise un Pôle de façon persistante
   */
  function selectPole(poleKey) {
    const pole = _polesMap.get(poleKey);
    if (!pole) return;

    if (_selectedPoleKey && _polesMap.has(_selectedPoleKey)) {
      _polesMap.get(_selectedPoleKey).baseScale = 1.0;
    }

    _selectedPoleKey = poleKey;
    _isTempFocused = false;
    _tempFocusTimer = 0;
    pole.baseScale = 1.45;
    triggerPulse(poleKey);

    const pos = pole.def.pos;
    _targetLookAt.x = pos[0] * 0.45;
    _targetLookAt.y = pos[1] * 0.45;
    _targetLookAt.z = pos[2] * 0.45;
    _targetCameraDist = 4.2;

    if (typeof _onSelectPole === "function") {
      _onSelectPole(pole.def);
    }
  }

  /**
   * Focalise temporairement un Pôle lors d'un événement infra puis revient en vue globale
   */
  function tempFocusPole(poleKey, durationSec = 3.5) {
    const pole = _polesMap.get(poleKey);
    if (!pole) return;

    if (_selectedPoleKey && _polesMap.has(_selectedPoleKey) && _selectedPoleKey !== poleKey) {
      _polesMap.get(_selectedPoleKey).baseScale = 1.0;
    }

    _selectedPoleKey = poleKey;
    pole.baseScale = 1.45;
    triggerPulse(poleKey);

    const pos = pole.def.pos;
    _targetLookAt.x = pos[0] * 0.45;
    _targetLookAt.y = pos[1] * 0.45;
    _targetLookAt.z = pos[2] * 0.45;
    _targetCameraDist = 4.2;
    _autoRotate = false;
    _lastInteractionTs = Date.now();

    _tempFocusTimer = durationSec;
    _isTempFocused = true;

    if (typeof _onSelectPole === "function") {
      _onSelectPole(pole.def);
    }
  }

  /**
   * Recentrer la vue globale
   */
  function resetView() {
    if (_selectedPoleKey && _polesMap.has(_selectedPoleKey)) {
      _polesMap.get(_selectedPoleKey).baseScale = 1.0;
      _selectedPoleKey = null;
    }
    _isTempFocused = false;
    _tempFocusTimer = 0;
    _targetLookAt = { x: 0, y: 0, z: 0 };
    _targetCameraDist = 5.6;
    _targetRot = { x: 0.15, y: -0.4 };
    _autoRotate = true;
    _lastInteractionTs = Date.now();
  }

  /**
   * Déclenche une onde lumineuse synaptique concentrique
   */
  function triggerPulse(sourcePoleKey) {
    if (!_brainGroup) return;

    _activityLevel = 2.2;
    _surgeTimer = 1.8;

    if (_neuronPoints && _neuronPoints.material) {
      _neuronPoints.material.size = 0.28;
      setTimeout(() => {
        if (_neuronPoints && _neuronPoints.material) _neuronPoints.material.size = 0.18;
      }, 400);
    }

    if (_synapseLines && _synapseLines.material) {
      _synapseLines.material.opacity = 0.85;
      setTimeout(() => {
        if (_synapseLines && _synapseLines.material) _synapseLines.material.opacity = 0.32;
      }, 500);
    }

    if (_pulsesPoints && _pulsesPoints.material) {
      _pulsesPoints.material.size = 0.48;
      setTimeout(() => {
        if (_pulsesPoints && _pulsesPoints.material) _pulsesPoints.material.size = 0.32;
      }, 600);
    }
  }

  /**
   * Mode Surcharge Cognitive (Hyper-activité)
   */
  function triggerSurge() {
    _activityLevel = 3.2;
    _surgeTimer = 5.0;
    triggerPulse();
  }

  /**
   * Injection d'un signal d'activité réel depuis l'infrastructure
   * @param {string} poleKey - clé du pôle concerné (cortex, hippo, world, fleet, limbic, lyra)
   * @param {string} [label] - description de l'événement (pour télémétrie)
   * @param {boolean} [autoFocus] - déclenche un focus caméra temporaire vers le pôle
   */
  function injectInfraSignal(poleKey, label, autoFocus = false) {
    if (!poleKey || !_polesMap.has(poleKey)) return;

    // Déclencher le boost du pôle (halo x2, anneaux accélérés)
    _activeInfraPoles.set(poleKey, 1.4);

    // Hausse ponctuelle de la fréquence EEG et de l'activité
    _activityLevel = Math.min(2.8, _activityLevel + 0.35);
    _surgeTimer = Math.max(_surgeTimer, 1.5);
    _eegHz = Math.min(58, _eegHz + 1.8);

    if (autoFocus) {
      tempFocusPole(poleKey, 3.5);
    }

    // Faire converger une gerbe d'influx synaptiques depuis ce pôle
    const pole = _polesMap.get(poleKey);
    if (pole && _pulsesPoints && _pulseData.length > 0) {
      const polePos = pole.root.position;
      const countToReorient = Math.min(35, Math.floor(_pulseData.length * 0.15));

      for (let i = 0; i < countToReorient; i++) {
        const idx = Math.floor(Math.random() * _pulseData.length);
        const p = _pulseData[idx];
        p.pA = polePos.clone();
        p.progress = 0;
        p.speed = 0.035 + Math.random() * 0.04;
      }
    }
  }

  /**
   * Démarrage du moteur
   */
  function start(opts) {
    opts = opts || {};
    _container = opts.host;
    _onSelectPole = opts.onSelect;

    if (!_container) {
      return Promise.reject(new Error("Container host 3D manquant"));
    }

    const THREE = globalThis.THREE || window.THREE;
    if (!THREE) {
      return Promise.reject(new Error("Three.js non chargé"));
    }

    stop();

    const w = _container.clientWidth || 800;
    const h = _container.clientHeight || 600;

    _scene = new THREE.Scene();
    _camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    _camera.position.set(0, 0, _cameraDist);

    _renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    _renderer.setSize(w, h);
    _renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    _container.innerHTML = "";
    _container.appendChild(_renderer.domElement);

    const tooltip = document.createElement("div");
    tooltip.id = "brain-3d-tooltip";
    tooltip.className = "brain-tooltip";
    tooltip.style.opacity = "0";
    _container.appendChild(tooltip);

    _brainGroup = new THREE.Group();
    _scene.add(_brainGroup);

    const modelGroup = buildBrainModel(THREE);
    _brainGroup.add(modelGroup);

    _polesGroup = buildPoles(THREE);
    _brainGroup.add(_polesGroup);

    _raycaster = new THREE.Raycaster();
    _raycaster.params.Points.threshold = 0.2;

    bindEvents(_container, THREE);

    _running = true;
    _lastInteractionTs = Date.now();
    animate(THREE);

    return Promise.resolve();
  }

  /**
   * Arrêt et nettoyage mémoire WebGL
   */
  function stop() {
    _running = false;
    if (_animId) {
      cancelAnimationFrame(_animId);
      _animId = null;
    }
    if (_container && _container._cleanupEvents) {
      _container._cleanupEvents();
      _container._cleanupEvents = null;
    }
    if (_renderer) {
      _renderer.dispose();
      if (_renderer.domElement && _renderer.domElement.parentElement) {
        _renderer.domElement.parentElement.removeChild(_renderer.domElement);
      }
      _renderer = null;
    }
    _scene = null;
    _camera = null;
    _brainGroup = null;
    _neuronPoints = null;
    _synapseLines = null;
    _pulsesPoints = null;
    _arcsGroup = null;
    _lightningArcs = [];
    _polesGroup = null;
    _polesMap.clear();
  }

  /**
   * Synchronisation télémétrique temps réel
   */
  function sync(data) {
    if (!data || typeof data !== "object") return;
    _brainData = { ..._brainData, ...data };

    const gauges = _brainData.gauges || {};
    const stress = Number(gauges.stress || 15);
    const conf = Number(gauges.confidence || 70);

    // Modulation de l'activité cérébrale et des fréquences EEG
    _eegHz = 32 + (stress / 100) * 22; // 32 Hz à 54 Hz (ondes Gamma)
    _synapseRate = 120 + Math.round((conf / 100) * 80);

    if (_synapseLines && _synapseLines.material) {
      _synapseLines.material.opacity = 0.25 + (stress / 100) * 0.35;
    }
  }

  /**
   * Changement de filtre de vue
   */
  function setFilter(mode) {
    if (mode === "analytical") {
      _targetRot.x = 0.1;
      _targetRot.y = -Math.PI * 0.45;
      _targetCameraDist = 4.8;
      _targetLookAt = { x: -0.6, y: 0, z: 0 };
    } else if (mode === "emotional") {
      _targetRot.x = 0.1;
      _targetRot.y = Math.PI * 0.45;
      _targetCameraDist = 4.8;
      _targetLookAt = { x: 0.6, y: 0, z: 0 };
    } else {
      _targetRot.x = 0.15;
      _targetRot.y = -0.4;
      _targetCameraDist = 5.6;
      _targetLookAt = { x: 0, y: 0, z: 0 };
    }
    _autoRotate = false;
    _lastInteractionTs = Date.now();
  }

  /**
   * Reconstitue l'état visuel du cerveau à un instant passé de la timeline (Ticket 5.1 Phase 3)
   * @param {Object} frame - { poleKey/pole_key, message, cognitive_load, gauges, level }
   */
  function replaySnapshot(frame) {
    if (!frame || typeof frame !== "object") return;
    const poleKey = frame.poleKey || frame.pole_key || "cortex";
    if (frame.gauges && typeof frame.gauges === "object") {
      sync({ gauges: frame.gauges });
    }
    const load = Number(frame.cognitive_load || 0.6);
    _activityLevel = 1.0 + load * 1.8;
    if (_polesMap.has(poleKey)) {
      injectInfraSignal(poleKey, frame.message || "Replay synaptique", false);
      selectPole(poleKey);
    } else {
      triggerPulse();
    }
  }

  // API publique
  global.LbgBrain3d = {
    start,
    stop,
    sync,
    triggerPulse,
    triggerSurge,
    injectInfraSignal,
    replaySnapshot,
    focusPole: selectPole,
    tempFocusPole,
    resetView,
    setFilter,
    isRunning: () => _running,
    POLES,
  };
})(typeof window !== "undefined" ? window : globalThis);
