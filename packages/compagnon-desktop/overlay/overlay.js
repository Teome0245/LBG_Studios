(function () {
  "use strict";

  const host = document.getElementById("face-host");

  function initFace() {
    if (!window.FaceRig || !host) return;
    try {
      FaceRig.init("face-host", { characterId: "lyra_assistant" });
      FaceRig.setMood({ tone: "serene", label: "Serein" });
    } catch (e) {
      console.warn("FaceRig init", e);
    }
  }

  if (window.FaceRig) {
    initFace();
  } else {
    // face_rig.js is sync script — should exist; retry briefly
    let n = 0;
    const t = setInterval(function () {
      n += 1;
      if (window.FaceRig || n > 20) {
        clearInterval(t);
        initFace();
      }
    }, 50);
  }

  if (host) {
    host.addEventListener("click", function () {
      if (window.compagnonDesktop && window.compagnonDesktop.openChat) {
        window.compagnonDesktop.openChat();
      }
    });
  }

  if (window.compagnonDesktop && window.compagnonDesktop.onMood) {
    window.compagnonDesktop.onMood(function (mood) {
      try {
        if (window.FaceRig && FaceRig.ready) FaceRig.setMood(mood || { tone: "serene" });
      } catch (_) {}
    });
  }
})();
