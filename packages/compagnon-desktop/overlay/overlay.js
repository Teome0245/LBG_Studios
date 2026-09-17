(function () {
  "use strict";

  const host = document.getElementById("face-host");
  const wrap = document.getElementById("face-wrap");
  const statusEl = document.getElementById("status");
  const bubble = document.getElementById("bubble");
  const bubbleMsg = document.getElementById("bubble-msg");
  const btnAgir = document.getElementById("btn-agir");
  const btnLater = document.getElementById("btn-later");

  let currentInitiative = null;

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

  function hideBubble() {
    currentInitiative = null;
    if (bubble) bubble.classList.remove("visible");
    if (statusEl) statusEl.textContent = "Compagnon";
    if (wrap) wrap.classList.remove("alert");
  }

  function showInitiative(payload) {
    currentInitiative = payload || null;
    const msg =
      (payload && (payload.message || payload.body || payload.label)) ||
      "Je vois quelque chose — on agit ?";
    if (bubbleMsg) bubbleMsg.textContent = String(msg).slice(0, 140);
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
      if (face && face.ready) {
        face.setMood("tense");
        if (face.pulse) face.pulse("alert");
        if (face.say) face.say(String(msg).slice(0, 80));
      }
    } catch (_) {}
  }

  if (wrap) {
    wrap.addEventListener("click", function () {
      if (window.compagnonDesktop && window.compagnonDesktop.openChat) {
        window.compagnonDesktop.openChat();
      }
    });
  }

  if (btnLater) {
    btnLater.addEventListener("click", function (e) {
      e.stopPropagation();
      hideBubble();
      try {
        const face = window.__petFace || window.FaceRig;
        if (face && face.ready) face.setMood("serene");
      } catch (_) {}
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
        if (face && face.ready) face.setMood(mood || "serene");
      } catch (_) {}
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onInitiative) {
    window.compagnonDesktop.onInitiative(function (payload) {
      showInitiative(payload);
    });
  }
})();
