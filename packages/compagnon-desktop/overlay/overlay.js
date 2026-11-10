(function () {
  "use strict";

  const host = document.getElementById("face-host");
  const wrap = document.getElementById("face-wrap");
  const statusEl = document.getElementById("status");
  const bubble = document.getElementById("bubble");
  const bubbleMsg = document.getElementById("bubble-msg");
  const btnAgir = document.getElementById("btn-agir");
  const btnLater = document.getElementById("btn-later");
  const pointerEl = document.getElementById("pointer");

  let currentInitiative = null;
  let currentApprovalId = null;
  let hideSessionTimer = null;
  let guideHideTimer = null;
  let overlayMode = "face"; // face | vrm
  let vrmModelUrl = "./vrm/default.vrm";
  let vrmFraming = "full"; // full | bust

  const sessionPill = document.getElementById("session-pill");
  const sessionAgent = document.getElementById("session-agent");
  const sessionTicker = document.getElementById("session-ticker");
  const btnAllow = document.getElementById("btn-allow");
  const btnDeny = document.getElementById("btn-deny");
  const chipLyra = document.getElementById("chip-lyra");
  const chipCline = document.getElementById("chip-cline");
  const chipHub = document.getElementById("chip-hub");

  function updateTeamChips(agentName, state) {
    const name = String(agentName || "").toLowerCase();
    let target = chipLyra;
    if (name.includes("cline") || name.includes("opencode") || name.includes("code")) {
      target = chipCline;
    } else if (name.includes("hub") || name.includes("godot") || name.includes("mmo")) {
      target = chipHub;
    }
    if (!target) return;
    target.classList.remove("active", "asking");
    if (state === "active") target.classList.add("active");
    else if (state === "asking") target.classList.add("asking");
  }

  function showSession(ev) {
    if (!sessionPill || !ev) return;
    const agentName = String(ev.agent || "agent");
    if (sessionAgent) sessionAgent.textContent = agentName;
    if (sessionTicker)
      sessionTicker.textContent = String(ev.summary || ev.event || "").slice(0, 240);
    sessionPill.classList.add("visible");
    if (ev.event === "session.approval_needed" && ev.approval_id) {
      currentApprovalId = ev.approval_id;
      sessionPill.classList.add("needs-approval");
      if (statusEl) statusEl.textContent = "Arbitrage : " + agentName;
      updateTeamChips(agentName, "asking");
      try {
        const face = window.__petFace;
        if (face) {
          if (typeof face.setMood === "function") face.setMood("curious");
          if (typeof face.setPose === "function") face.setPose("think", 5000);
          if (typeof face.say === "function") face.say(agentName + " demande ton arbitrage");
        }
      } catch (_) {}
    } else {
      sessionPill.classList.remove("needs-approval");
      if (statusEl) statusEl.textContent = agentName;
      updateTeamChips(agentName, "active");
    }
    if (ev.event === "session.stop" || ev.event === "session.error") {
      updateTeamChips(agentName, "idle");
      if (hideSessionTimer) clearTimeout(hideSessionTimer);
      hideSessionTimer = setTimeout(function () {
        sessionPill.classList.remove("visible");
        sessionPill.classList.remove("needs-approval");
        currentApprovalId = null;
        if (statusEl) statusEl.textContent = "Compagnon";
        try {
          const face = window.__petFace;
          if (face && typeof face.setPose === "function") face.setPose("idle");
          if (face && typeof face.setMood === "function") face.setMood("serene");
        } catch (_) {}
      }, 5000);
    }
  }

  function sendDecision(decision) {
    if (!currentApprovalId) return;
    const body = {
      v: 1,
      approval_id: currentApprovalId,
      decision: decision,
      scope: "once",
    };
    if (window.compagnonDesktop && window.compagnonDesktop.sessionDecision) {
      window.compagnonDesktop.sessionDecision(body);
    }
    currentApprovalId = null;
    if (sessionPill) sessionPill.classList.remove("needs-approval");
    if (statusEl) statusEl.textContent = decision === "allow" ? "Validé" : "Refusé";

    // Réaction vivante et expressive de l'avatar au retour humain (Axial / Blobs canon)
    try {
      const face = window.__petFace;
      if (face) {
        if (decision === "allow") {
          if (typeof face.setMood === "function") face.setMood("happy");
          if (typeof face.setPose === "function") face.setPose("approve", 2500);
          if (typeof face.say === "function") face.say("C'est validé !");
        } else {
          if (typeof face.setMood === "function") face.setMood("tense");
          if (typeof face.setPose === "function") face.setPose("crossArms", 2500);
          if (typeof face.say === "function") face.say("Action refusée.");
        }
      }
    } catch (_) {}
  }


  if (btnAllow) {
    btnAllow.addEventListener("click", function (e) {
      e.stopPropagation();
      sendDecision("allow");
    });
  }
  if (btnDeny) {
    btnDeny.addEventListener("click", function (e) {
      e.stopPropagation();
      sendDecision("deny");
    });
  }

  function initFace() {
    if (!window.FaceRig || !host) return;
    try {
      const inst =
        typeof FaceRig.create === "function" ? FaceRig.create() : FaceRig;
      window.__petFace = inst;
      Promise.resolve(inst.init("face-host", { characterId: "lyra_assistant" })).then(
        function () {
          inst.setMood("serene");
        }
      );
    } catch (e) {
      console.warn("FaceRig init", e);
    }
  }

  function initVrm() {
    document.body.classList.add("mode-vrm");
    if (statusEl) statusEl.textContent = "VRM…";
    function fallbackFace(reason) {
      console.warn("VRM fallback FaceRig:", reason || "");
      document.body.classList.remove("mode-vrm");
      overlayMode = "face";
      if (statusEl) statusEl.textContent = "FaceRig";
      initFace();
    }
    function start() {
      if (!window.__createVrmPet || !host) return false;
      try {
        if (window.__petFace && window.__petFace.destroy) {
          try {
            window.__petFace.destroy();
          } catch (_) { }
        }
        host.innerHTML = "";
        document.body.classList.toggle("framing-bust", vrmFraming === "bust");
        document.body.classList.toggle("framing-full", vrmFraming !== "bust");
        window.__petFace = window.__createVrmPet(host, {
          modelUrl: vrmModelUrl,
          framing: vrmFraming,
        });
        if (statusEl) statusEl.textContent = "Compagnon VRM";
        // Si le modele ne charge pas en 12s -> FaceRig
        setTimeout(function () {
          const pet = window.__petFace;
          if (pet && !pet.ready) {
            fallbackFace(pet.error || "timeout");
          }
        }, 12000);
        return true;
      } catch (e) {
        console.warn("VRM init", e);
        fallbackFace(String(e && e.message ? e.message : e));
        return true;
      }
    }
    if (start()) return;
    window.__onVrmPetReady = function () {
      start();
    };
    let n = 0;
    const t = setInterval(function () {
      n += 1;
      if (start() || n > 40) {
        clearInterval(t);
        if (n > 40 && !window.__petFace) fallbackFace("module timeout");
      }
    }, 100);
  }

  function bootAvatar() {
    if (overlayMode === "vrm") {
      initVrm();
      return;
    }
    document.body.classList.remove("mode-vrm");
    if (window.FaceRig) {
      initFace();
    } else {
      let n = 0;
      const t = setInterval(function () {
        n += 1;
        if (window.FaceRig || n > 20) {
          clearInterval(t);
          initFace();
        }
      }, 50);
    }
  }

  function applyConfig(cfg) {
    const o = (cfg && cfg.overlay) || {};
    const mode = String(o.mode || "face").toLowerCase();
    overlayMode = mode === "vrm" ? "vrm" : "face";
    if (o.vrmModel) vrmModelUrl = String(o.vrmModel);
    vrmFraming = String(o.vrmFraming || "full").toLowerCase() === "bust" ? "bust" : "full";
    bootAvatar();
  }

  if (window.compagnonDesktop && window.compagnonDesktop.getConfig) {
    window.compagnonDesktop
      .getConfig()
      .then(applyConfig)
      .catch(function () {
        bootAvatar();
      });
  } else {
    bootAvatar();
  }

  function hideBubble() {
    currentInitiative = null;
    if (bubble) {
      bubble.classList.remove("visible");
      bubble.classList.remove("guide");
    }
    if (statusEl) statusEl.textContent = "Compagnon";
    if (wrap) wrap.classList.remove("alert");
    clearGuideVisual();
  }

  function clearGuideVisual() {
    document.body.classList.remove("guiding");
    if (pointerEl) {
      pointerEl.classList.remove("visible", "left", "right");
    }
    if (guideHideTimer) {
      clearTimeout(guideHideTimer);
      guideHideTimer = null;
    }
  }

  function showGuide(payload) {
    const msg =
      (payload && (payload.message || payload.label)) ||
      "Regarde ici…";
    if (bubbleMsg) bubbleMsg.textContent = String(msg).slice(0, 240);
    if (bubble) {
      bubble.classList.add("visible", "guide");
    }
    if (statusEl) statusEl.textContent = "Guide";
    document.body.classList.add("guiding");
    const side = payload && payload.pointSide;
    if (pointerEl) {
      pointerEl.classList.remove("visible", "left", "right");
      if (side === "left" || side === "right") {
        pointerEl.classList.add("visible", side);
      }
    }
    try {
      const face = window.__petFace || window.FaceRig;
      if (face) {
        if (face.setMood) face.setMood("curious");
        if (face.setPose) {
          // Cible à gauche de l'avatar → pointe à gauche, etc.
          if (side === "left") face.setPose("pointLeft", 0);
          else if (side === "right") face.setPose("pointRight", 0);
          else face.setPose("wave", 2500);
        } else if (face.pulse) {
          face.pulse("alert");
        }
        if (face.say) face.say(String(msg).slice(0, 240));
      }
    } catch (_) { }
    if (guideHideTimer) clearTimeout(guideHideTimer);
    const hold = Math.max(2500, Number(payload && payload.holdMs) || 8000);
    guideHideTimer = setTimeout(function () {
      clearGuideVisual();
      if (bubble) {
        bubble.classList.remove("visible");
        bubble.classList.remove("guide");
      }
      if (statusEl) statusEl.textContent = "Compagnon";
      try {
        const face = window.__petFace || window.FaceRig;
        if (face) {
          if (face.setPose) face.setPose("idle");
          if (face.setMood) face.setMood("serene");
        }
      } catch (_) { }
    }, hold);
  }

  function showInitiative(payload) {
    clearGuideVisual();
    if (bubble) bubble.classList.remove("guide");
    currentInitiative = payload || null;
    const msg =
      (payload && (payload.message || payload.body || payload.label)) ||
      "Je vois quelque chose — on agit ?";
    if (bubbleMsg) bubbleMsg.textContent = String(msg).slice(0, 240);
    if (bubble) bubble.classList.add("visible");
    if (statusEl) statusEl.textContent = "Initiative";
    if (wrap) {
      wrap.classList.add("alert");
      setTimeout(function () {
        wrap.classList.remove("alert");
      }, 2800);
    }
    try {
      const face = window.__petFace || window.FaceRig;
      if (face) {
        if (face.setMood) face.setMood("tense");
        if (face.pulse) face.pulse("alert");
        if (face.say) face.say(String(msg).slice(0, 240));
      }
    } catch (_) { }
  }

  if (wrap) {
    let clickTimeout = null;
    wrap.addEventListener("click", function (e) {
      // Ignorer si le clic provient de la poignée de déplacement ou d'un bouton de bulle
      if (e.target.closest(".drag-handle") || e.target.closest(".bubble")) return;
      if (clickTimeout) {
        // Double-clic : ouvrir la fenêtre de chat principal
        clearTimeout(clickTimeout);
        clickTimeout = null;
        if (window.compagnonDesktop && window.compagnonDesktop.openChat) {
          window.compagnonDesktop.openChat();
        }
      } else {
        // Simple-clic : réaction vivante (poke / interaction amicale)
        clickTimeout = setTimeout(function () {
          clickTimeout = null;
          if (window.compagnonDesktop && window.compagnonDesktop.pokeAvatar) {
            window.compagnonDesktop.pokeAvatar();
          }
        }, 260);
      }
    });

    wrap.addEventListener("contextmenu", function (e) {
      e.preventDefault();
      if (clickTimeout) {
        clearTimeout(clickTimeout);
        clickTimeout = null;
      }
      if (window.compagnonDesktop && window.compagnonDesktop.showOverlayContextMenu) {
        window.compagnonDesktop.showOverlayContextMenu();
      }
    });
  }

  if (btnLater) {
    btnLater.addEventListener("click", function (e) {
      e.stopPropagation();
      hideBubble();
      try {
        const face = window.__petFace || window.FaceRig;
        if (face && face.setMood) face.setMood("serene");
      } catch (_) { }
    });
  }

  if (btnAgir) {
    btnAgir.addEventListener("click", function (e) {
      e.stopPropagation();
      const intent = currentInitiative && currentInitiative.primary;
      const text =
        (intent && intent.sourceText) ||
        (currentInitiative && currentInitiative.sourceText) ||
        "";
      if (window.compagnonDesktop && window.compagnonDesktop.openChatWithAgir) {
        window.compagnonDesktop.openChatWithAgir({
          sourceText: text,
          label: (intent && intent.label) || "Initiative",
          message: currentInitiative && currentInitiative.message,
        });
      } else if (window.compagnonDesktop && window.compagnonDesktop.openChat) {
        window.compagnonDesktop.openChat();
      }
      hideBubble();
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onMood) {
    window.compagnonDesktop.onMood(function (mood) {
      try {
        const face = window.__petFace || window.FaceRig;
        if (!face || !face.setMood) return;
        const tone =
          mood && typeof mood === "object"
            ? mood.tone || mood.mood || "serene"
            : mood || "serene";
        face.setMood(tone);
      } catch (_) { }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onTalking) {
    window.compagnonDesktop.onTalking(function (payload) {
      try {
        const face = window.__petFace || window.FaceRig;
        if (!face) return;
        const ms = payload && Number(payload.ms);
        if (payload && payload.talking === false) {
          if (face.setTalking) face.setTalking(false);
          return;
        }
        if (face.setTalking && Number.isFinite(ms)) face.setTalking(ms);
        else if (face.say && payload && payload.text) face.say(String(payload.text).slice(0, 240));
      } catch (_) { }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onInitiative) {
    window.compagnonDesktop.onInitiative(function (payload) {
      showInitiative(payload);
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onGuide) {
    window.compagnonDesktop.onGuide(function (payload) {
      showGuide(payload);
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onSessionEvent) {
    window.compagnonDesktop.onSessionEvent(function (ev) {
      showSession(ev);
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onVrmFlip) {
    window.compagnonDesktop.onVrmFlip(function () {
      try {
        const face = window.__petFace;
        if (face && typeof face.flip === "function") face.flip();
      } catch (_) { }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onVrmFraming) {
    window.compagnonDesktop.onVrmFraming(function (framing) {
      vrmFraming = String(framing || "").toLowerCase() === "bust" ? "bust" : "full";
      document.body.classList.toggle("framing-bust", vrmFraming === "bust");
      document.body.classList.toggle("framing-full", vrmFraming !== "bust");
      try {
        const face = window.__petFace;
        if (face && typeof face.setFraming === "function") face.setFraming(vrmFraming);
      } catch (_) { }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onVrmPose) {
    window.compagnonDesktop.onVrmPose(function (payload) {
      try {
        const face = window.__petFace;
        if (!face || typeof face.setPose !== "function") return;
        const pose = (payload && payload.pose) || "idle";
        const hold = payload && Number(payload.holdMs);
        face.setPose(pose, Number.isFinite(hold) ? hold : 2500, payload && payload.heading);
      } catch (_) { }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onVrmHeading) {
    window.compagnonDesktop.onVrmHeading(function (heading) {
      try {
        const face = window.__petFace;
        if (face && typeof face.setHeading === "function") {
          face.setHeading(heading);
        }
      } catch (_) { }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onVrmModel) {
    window.compagnonDesktop.onVrmModel(function (modelUrl) {
      if (modelUrl) {
        vrmModelUrl = String(modelUrl);
        if (overlayMode === "vrm") {
          initVrm();
        }
      }
    });
  }

  // Accessoires 3D modulaires (visière, datapad, écouteurs)
  if (window.compagnonDesktop && window.compagnonDesktop.onVrmAccessory) {
    window.compagnonDesktop.onVrmAccessory(function (payload) {
      try {
        const face = window.__petFace;
        if (!face) return;
        const type = payload && (payload.type || payload.accessory);
        const equip = payload && payload.equip !== undefined ? Boolean(payload.equip) : undefined;
        if (typeof face.equipAccessory === "function") {
          if (equip !== undefined) face.equipAccessory(type, equip);
          else if (typeof face.toggleAccessory === "function") face.toggleAccessory(type);
        }
      } catch (_) { }
    });
  }

  // Mode fantôme : écoute des changements de clic traversant (VSeeFace canon)
  if (window.compagnonDesktop && window.compagnonDesktop.onClickThroughChanged) {
    window.compagnonDesktop.onClickThroughChanged(function (active) {
      document.body.classList.toggle("mode-ghost", Boolean(active));
      if (statusEl) {
        statusEl.textContent = active ? "👻 Mode Fantôme (Ctrl+Shift+F)" : "Compagnon";
      }
    });
  }

  // ShowRoutineManager : écoute des spectacles continus (iStripper canon)
  if (window.compagnonDesktop && window.compagnonDesktop.onShowEvent) {
    window.compagnonDesktop.onShowEvent(function (payload) {
      try {
        const face = window.__petFace;
        if (!face) return;
        if (payload && payload.action === "start") {
          const showName = (typeof face.startShow === "function")
            ? face.startShow(payload.routine || "idol", function () {
                if (statusEl) statusEl.textContent = "Compagnon";
              })
            : "Show";
          if (statusEl) statusEl.textContent = "🎭 " + (showName || "Show en cours");
        } else if (payload && payload.action === "stop") {
          if (typeof face.stopShow === "function") face.stopShow();
          if (statusEl) statusEl.textContent = "Compagnon";
        }
      } catch (err) {
        console.warn("[overlay] show event", err);
      }
    });
  }

  // Drag fenetre via barre (multi-ecran)
  (function setupDrag() {
    const handle = document.getElementById("drag-handle");
    if (!handle || !window.compagnonDesktop || !window.compagnonDesktop.moveOverlay) return;
    let dragging = false;
    let ox = 0;
    let oy = 0;
    let bx = 0;
    let by = 0;
    handle.addEventListener("mousedown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      ox = e.screenX;
      oy = e.screenY;
      Promise.resolve(window.compagnonDesktop.getOverlayBounds()).then(function (b) {
        if (!b) return;
        bx = b.x;
        by = b.y;
        dragging = true;
      });
    });
    window.addEventListener("mousemove", function (e) {
      if (!dragging) return;
      window.compagnonDesktop.moveOverlay(bx + (e.screenX - ox), by + (e.screenY - oy));
    });
    window.addEventListener("mouseup", function () {
      dragging = false;
    });
  })();
})();
