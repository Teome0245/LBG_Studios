/**
 * Avatar expressif Pilot — modèle féminin riggé (avatar_app) + humeurs procédurales.
 * API : init, setMood, say, setTalking, destroy.
 *
 * Note : les GLB féminins locaux n'ont pas de morph targets faciaux (contrairement
 * à RobotExpressive). On anime donc le squelette (tête, cou, épaules, bras, mâchoire
 * via mesh bouche) pour coller aux tons orchestrateur.
 */
(function (global) {
  "use strict";

  const MOOD_TO_EXPRESSION = {
    serene: "neutral",
    curious: "surprised",
    vigilant: "neutral",
    tense: "angry",
    waiting: "sad",
    off: "neutral",
  };

  let scene, camera, renderer, clock, mixer, model, faceMesh, mouthMesh;
  let bones = {};
  let actions = {};
  let activeAction = null;
  let containerEl = null;
  let animId = null;
  let talkUntil = 0;
  let currentExpression = "neutral";
  let currentTone = "serene";
  let basePosition = null;
  let useProcedural = true;

  function defaultModelUrl() {
    try {
      const scripts = global.document && global.document.getElementsByTagName("script");
      if (scripts) {
        for (let i = scripts.length - 1; i >= 0; i--) {
          const src = scripts[i].src || "";
          if (src.indexOf("orchestrator_avatar.js") >= 0) {
            return new URL("models/base_female.glb", src).href;
          }
        }
      }
    } catch (_) {}
    try {
      const u = new URL(global.location.href);
      let dir = u.pathname || "/";
      if (!dir.endsWith("/")) dir = dir.replace(/\/[^/]*$/, "/") || "/";
      return u.origin + dir + "orchestrator_avatar/models/base_female.glb";
    } catch (_) {
      return "orchestrator_avatar/models/base_female.glb";
    }
  }

  function showStatus(msg) {
    if (!containerEl) return;
    let el = containerEl.querySelector(".orch-avatar-status");
    if (!el) {
      el = global.document.createElement("div");
      el.className = "orch-avatar-status";
      el.style.cssText =
        "position:absolute;inset:0;display:flex;align-items:center;justify-content:center;" +
        "padding:0.5rem;font-size:0.72rem;color:#94a3b8;text-align:center;pointer-events:none;z-index:1";
      containerEl.style.position = containerEl.style.position || "relative";
      containerEl.appendChild(el);
    }
    el.textContent = msg || "";
    el.style.display = msg ? "flex" : "none";
  }

  function findBone(root, predicates) {
    let found = null;
    root.traverse(function (node) {
      if (found || !node.isBone) return;
      const name = String(node.name || "").toLowerCase();
      for (let i = 0; i < predicates.length; i++) {
        if (predicates[i](name)) {
          found = node;
          return;
        }
      }
    });
    return found;
  }

  function cacheBones(root) {
    bones = {
      hips: findBone(root, [function (n) { return n.indexOf("hips") >= 0; }]),
      spine: findBone(root, [
        function (n) { return n.indexOf("spine2") >= 0; },
        function (n) { return n.indexOf("spine1") >= 0; },
        function (n) { return n.indexOf("spine") >= 0; },
      ]),
      neck: findBone(root, [function (n) { return n.indexOf("neck") >= 0; }]),
      head: findBone(root, [
        function (n) { return n.indexOf("head") >= 0 && n.indexOf("end") < 0; },
      ]),
      shoulderL: findBone(root, [
        function (n) { return n.indexOf("shoulder") >= 0 && (n.indexOf(".l") >= 0 || n.indexOf("left") >= 0); },
      ]),
      shoulderR: findBone(root, [
        function (n) { return n.indexOf("shoulder") >= 0 && (n.indexOf(".r") >= 0 || n.indexOf("right") >= 0); },
      ]),
      armL: findBone(root, [
        function (n) {
          return n.indexOf("arm") >= 0 && n.indexOf("fore") < 0 && (n.indexOf(".l") >= 0 || n.indexOf("left") >= 0);
        },
      ]),
      armR: findBone(root, [
        function (n) {
          return n.indexOf("arm") >= 0 && n.indexOf("fore") < 0 && (n.indexOf(".r") >= 0 || n.indexOf("right") >= 0);
        },
      ]),
      foreL: findBone(root, [
        function (n) { return n.indexOf("forearm") >= 0 && (n.indexOf(".l") >= 0 || n.indexOf("left") >= 0); },
      ]),
      foreR: findBone(root, [
        function (n) { return n.indexOf("forearm") >= 0 && (n.indexOf(".r") >= 0 || n.indexOf("right") >= 0); },
      ]),
    };
    Object.keys(bones).forEach(function (k) {
      const b = bones[k];
      if (b && b.userData.originalRotation === undefined) {
        b.userData.originalRotation = b.rotation.clone();
      }
    });
  }

  function restoreBone(b) {
    if (b && b.userData.originalRotation) b.rotation.copy(b.userData.originalRotation);
  }

  function setMorph(expression) {
    if (!faceMesh || !faceMesh.morphTargetDictionary || !faceMesh.morphTargetInfluences) return false;
    const dict = faceMesh.morphTargetDictionary;
    const inf = faceMesh.morphTargetInfluences;
    for (const key in dict) {
      inf[dict[key]] = 0;
    }
    const targets = {
      angry: ["angry", "Angry"],
      sad: ["sad", "Sad"],
      surprised: ["surprised", "Surprised", "happy", "Happy", "smile", "Smile"],
      neutral: [],
    };
    const names = targets[expression] || [];
    for (let i = 0; i < names.length; i++) {
      if (dict[names[i]] !== undefined) {
        inf[dict[names[i]]] = 0.85;
        return true;
      }
    }
    return expression === "neutral";
  }

  function fadeToAction(name, duration) {
    const next = actions[name];
    if (!next) return false;
    if (activeAction && activeAction !== next) activeAction.fadeOut(duration);
    activeAction = next
      .reset()
      .setEffectiveTimeScale(1)
      .setEffectiveWeight(1)
      .fadeIn(duration)
      .play();
    useProcedural = false;
    return true;
  }

  function moodPose(time, talking) {
    if (!model || !useProcedural) return;

    Object.keys(bones).forEach(function (k) {
      restoreBone(bones[k]);
    });

    const head = bones.head;
    const neck = bones.neck;
    const spine = bones.spine;
    const hips = bones.hips;
    const armL = bones.armL;
    const armR = bones.armR;
    const foreL = bones.foreL;
    const foreR = bones.foreR;
    const shL = bones.shoulderL;
    const shR = bones.shoulderR;

    const breath = Math.sin(time * 1.4) * 0.015;
    if (spine) spine.rotation.x += breath;
    if (hips) hips.rotation.y += Math.sin(time * 0.7) * 0.01;

    const expr = currentExpression;
    if (expr === "surprised") {
      if (head) {
        head.rotation.x += -0.12 + Math.sin(time * 2.2) * 0.03;
        head.rotation.z += 0.18;
      }
      if (neck) neck.rotation.x += -0.08;
      if (spine) spine.rotation.x += -0.06;
      if (shL) shL.rotation.z += 0.12;
      if (shR) shR.rotation.z -= 0.12;
      if (armL) armL.rotation.x += 0.15;
      if (armR) armR.rotation.x += 0.1;
    } else if (expr === "angry") {
      if (head) {
        head.rotation.x += 0.14;
        head.rotation.z += Math.sin(time * 12) * 0.02;
      }
      if (neck) neck.rotation.x += 0.08;
      if (spine) spine.rotation.x += 0.05;
      if (shL) shL.rotation.z -= 0.22;
      if (shR) shR.rotation.z += 0.22;
      if (armL) {
        armL.rotation.x += 0.35;
        armL.rotation.z -= 0.25;
      }
      if (armR) {
        armR.rotation.x += 0.35;
        armR.rotation.z += 0.25;
      }
      if (foreL) foreL.rotation.x += 0.4;
      if (foreR) foreR.rotation.x += 0.4;
    } else if (expr === "sad") {
      if (head) {
        head.rotation.x += 0.28;
        head.rotation.z += -0.12;
      }
      if (neck) neck.rotation.x += 0.12;
      if (spine) spine.rotation.x += 0.12;
      if (armL) {
        armL.rotation.x += 0.2;
        armL.rotation.z += 0.15;
      }
      if (armR) {
        armR.rotation.x += 0.2;
        armR.rotation.z -= 0.15;
      }
      if (model && basePosition) {
        model.position.y = basePosition.y - 0.03;
      }
    } else {
      // neutral / serene — idle vivant
      if (head) {
        head.rotation.y += Math.sin(time * 0.55) * 0.06;
        head.rotation.x += Math.sin(time * 0.4) * 0.02;
      }
      if (armL) armL.rotation.z += Math.sin(time * 0.9) * 0.03;
      if (armR) armR.rotation.z -= Math.sin(time * 0.9 + 0.4) * 0.03;
    }

    if (talking) {
      const jaw = Math.max(0, Math.sin(time * 16) * 0.22);
      if (head) head.rotation.x += jaw * 0.35;
      if (mouthMesh) {
        if (!mouthMesh.userData.origScale) {
          mouthMesh.userData.origScale = mouthMesh.scale.clone();
        }
        mouthMesh.scale.y = mouthMesh.userData.origScale.y * (1 + jaw * 0.55);
      }
      if (foreR) foreR.rotation.x += Math.sin(time * 5) * 0.12;
      if (armR) armR.rotation.x += 0.18 + Math.sin(time * 4) * 0.08;
    } else if (mouthMesh && mouthMesh.userData.origScale) {
      mouthMesh.scale.copy(mouthMesh.userData.origScale);
    }

    if (expr !== "sad" && model && basePosition) {
      model.position.y = basePosition.y;
    }
  }

  function frameCameraToBust() {
    if (!camera || !containerEl) return;
    // Plan buste fixe (même logique que avatar_app : caméra face au haut du corps)
    // Modèle normalisé : pieds ~ y=-1, tête ~ y=1
    camera.fov = 30;
    camera.near = 0.05;
    camera.far = 40;
    camera.position.set(0, 0.72, 2.35);
    camera.lookAt(0, 0.62, 0);
    camera.updateProjectionMatrix();
    onResize();
  }

  function onResize() {
    if (!containerEl || !renderer || !camera) return;
    const w = Math.max(containerEl.clientWidth || 0, 160);
    const h = Math.max(containerEl.clientHeight || 0, 180);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
  }

  function animate() {
    animId = global.requestAnimationFrame(animate);
    const delta = clock ? clock.getDelta() : 0.016;
    const elapsed = clock ? clock.getElapsedTime() : 0;
    if (mixer) mixer.update(delta);
    const talking = Date.now() < talkUntil;
    moodPose(elapsed, talking);
    if (renderer && scene && camera) renderer.render(scene, camera);
  }

  function loadModel(url) {
    if (!global.THREE || !global.THREE.GLTFLoader) {
      console.warn("OrchestratorAvatar: Three.js / GLTFLoader manquant");
      showStatus("Three.js indisponible");
      return;
    }
    showStatus("Chargement avatar…");
    const loader = new global.THREE.GLTFLoader();
    loader.load(
      url,
      function (gltf) {
        model = gltf.scene;
        scene.add(model);

        // Normalisation identique à avatar_app/app.js
        const tempBox = new global.THREE.Box3();
        let hasMesh = false;
        model.traverse(function (child) {
          if (child.isMesh) {
            tempBox.expandByObject(child);
            hasMesh = true;
          }
        });
        if (!hasMesh) tempBox.setFromObject(model);

        const size = tempBox.getSize(new global.THREE.Vector3());
        const height = size.y;
        const center = tempBox.getCenter(new global.THREE.Vector3());
        if (height > 0) {
          const targetHeight = 2.0;
          const scaleFactor = targetHeight / height;
          model.scale.set(scaleFactor, scaleFactor, scaleFactor);
          model.position.set(
            -center.x * scaleFactor,
            -1.0 - (center.y - height / 2) * scaleFactor,
            -center.z * scaleFactor
          );
        } else {
          model.position.set(0, -1.0, 0);
        }
        basePosition = model.position.clone();

        faceMesh = null;
        mouthMesh = null;
        model.traverse(function (child) {
          if (child.isMesh) {
            const n = String(child.name || "").toLowerCase();
            if (child.morphTargetInfluences && child.morphTargetDictionary) {
              faceMesh = child;
            }
            if (n.indexOf("mouth") >= 0 || n.indexOf("bouche") >= 0) {
              mouthMesh = child;
            }
            child.castShadow = false;
            child.receiveShadow = false;
            if (child.material) {
              const mats = Array.isArray(child.material) ? child.material : [child.material];
              mats.forEach(function (m) {
                if (m) {
                  m.side = global.THREE.DoubleSide;
                  m.needsUpdate = true;
                }
              });
            }
          }
        });

        cacheBones(model);
        frameCameraToBust();

        if (gltf.animations && gltf.animations.length) {
          mixer = new global.THREE.AnimationMixer(model);
          gltf.animations.forEach(function (clip) {
            actions[clip.name] = mixer.clipAction(clip);
            const short = clip.name.split("|").pop();
            if (short && !actions[short]) actions[short] = actions[clip.name];
          });
          const idle =
            actions.Idle ||
            actions.idle ||
            actions.Standing ||
            actions.TPose ||
            null;
          if (idle) {
            activeAction = idle;
            idle.play();
            useProcedural = !actions.Wave && !actions.Dance && !actions.Talking;
          } else {
            useProcedural = true;
          }
        } else {
          useProcedural = true;
        }

        setMorph(currentExpression);
        showStatus("");
        global.setTimeout(frameCameraToBust, 100);
        global.setTimeout(frameCameraToBust, 500);
      },
      undefined,
      function (err) {
        console.warn("OrchestratorAvatar: chargement GLB échoué", url, err);
        showStatus("Échec chargement modèle");
      }
    );
  }

  const OrchestratorAvatar = {
    ready: false,

    init: function (containerId, opts) {
      opts = opts || {};
      if (!global.THREE) return false;
      containerEl = typeof containerId === "string" ? document.getElementById(containerId) : containerId;
      if (!containerEl) return false;
      if (this.ready) return true;

      containerEl.innerHTML = "";
      clock = new global.THREE.Clock();
      scene = new global.THREE.Scene();
      scene.background = new global.THREE.Color(0x0f172a);

      const w = containerEl.clientWidth || 220;
      const h = containerEl.clientHeight || 220;
      camera = new global.THREE.PerspectiveCamera(32, w / h, 0.1, 100);
      camera.position.set(0, 0.55, 2.15);
      camera.lookAt(0, 0.45, 0);

      renderer = new global.THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
      renderer.setSize(w, h);
      containerEl.appendChild(renderer.domElement);

      const amb = new global.THREE.AmbientLight(0xffffff, 0.7);
      scene.add(amb);
      const key = new global.THREE.DirectionalLight(0xfff4e6, 0.95);
      key.position.set(2, 3, 2);
      scene.add(key);
      const fill = new global.THREE.DirectionalLight(0x93c5fd, 0.4);
      fill.position.set(-2, 1, 1);
      scene.add(fill);
      const rim = new global.THREE.DirectionalLight(0xf472b6, 0.25);
      rim.position.set(0, 1.5, -2);
      scene.add(rim);

      global.addEventListener("resize", onResize);
      if (typeof global.ResizeObserver === "function") {
        try {
          const ro = new global.ResizeObserver(function () {
            onResize();
            if (model) frameCameraToBust();
          });
          ro.observe(containerEl);
        } catch (_) {}
      }
      loadModel(opts.modelUrl || defaultModelUrl());
      animate();
      this.ready = true;
      return true;
    },

    setMood: function (mood) {
      if (!mood || typeof mood !== "object") return;
      const tone = mood.tone || "off";
      currentTone = tone;
      const expr = MOOD_TO_EXPRESSION[tone] || "neutral";
      currentExpression = expr;
      setMorph(expr);
      if (!OrchestratorAvatar._framedOnce && model) {
        OrchestratorAvatar._framedOnce = true;
        try {
          frameCameraToBust();
        } catch (_) {}
      }

      if (!useProcedural) {
        if (tone === "tense" && actions.Wave) fadeToAction("Wave", 0.3);
        else if (tone === "curious" && actions.Yes) fadeToAction("Yes", 0.3);
        else if (actions.Idle || actions.idle) fadeToAction(actions.Idle ? "Idle" : "idle", 0.4);
      }

      const bubble = document.getElementById("orch-avatar-bubble");
      if (bubble && mood.voice) {
        bubble.textContent = mood.voice;
        bubble.hidden = false;
      }
    },

    say: function (text) {
      const bubble = document.getElementById("orch-avatar-bubble");
      if (bubble) {
        const t = String(text || "").trim();
        if (t) {
          bubble.textContent = t.length > 180 ? t.slice(0, 177) + "…" : t;
          bubble.hidden = false;
        }
      }
      this.setTalking(true, 2800);
    },

    setTalking: function (on, ms) {
      talkUntil = on ? Date.now() + (ms || 2500) : 0;
      if (!useProcedural) {
        if (on && actions.Talking) fadeToAction("Talking", 0.15);
        else if (on && actions.Yes) fadeToAction("Yes", 0.15);
        else if (!on && (actions.Idle || actions.idle)) fadeToAction(actions.Idle ? "Idle" : "idle", 0.25);
      }
    },

    destroy: function () {
      if (animId) global.cancelAnimationFrame(animId);
      global.removeEventListener("resize", onResize);
      if (renderer) renderer.dispose();
      scene = camera = renderer = mixer = model = faceMesh = mouthMesh = containerEl = null;
      bones = {};
      actions = {};
      this.ready = false;
    },
  };

  global.OrchestratorAvatar = OrchestratorAvatar;
})(window);
