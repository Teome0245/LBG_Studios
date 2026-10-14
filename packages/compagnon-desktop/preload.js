const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("compagnonDesktop", {
  getConfig: () => ipcRenderer.invoke("compagnon:get-config"),
  openChat: () => ipcRenderer.send("compagnon:open-chat"),
  openChatWithAgir: (payload) => ipcRenderer.send("compagnon:open-chat-agir", payload || {}),
  setMood: (mood) => ipcRenderer.send("compagnon:overlay-mood", mood),
  /** SPA chat → bridge avatar (TTS lip-sync, say, idle). */
  notifyPresence: (payload) => ipcRenderer.send("compagnon:avatar-presence", payload || {}),
  onMood: (cb) => {
    ipcRenderer.on("compagnon:mood", (_e, mood) => {
      try {
        cb(mood);
      } catch (_) {}
    });
  },
  onTalking: (cb) => {
    ipcRenderer.on("compagnon:talking", (_e, payload) => {
      try {
        cb(payload);
      } catch (_) {}
    });
  },
  onVrmFlip: (cb) => {
    ipcRenderer.on("compagnon:vrm-flip", () => {
      try {
        cb();
      } catch (_) {}
    });
  },
  onVrmFraming: (cb) => {
    ipcRenderer.on("compagnon:vrm-framing", (_e, framing) => {
      try {
        cb(framing);
      } catch (_) {}
    });
  },
  onVrmPose: (cb) => {
    ipcRenderer.on("compagnon:vrm-pose", (_e, payload) => {
      try {
        cb(payload);
      } catch (_) {}
    });
  },
  onGuide: (cb) => {
    ipcRenderer.on("compagnon:guide", (_e, payload) => {
      try {
        cb(payload);
      } catch (_) {}
    });
  },
  moveOverlay: (x, y) => ipcRenderer.send("compagnon:overlay-move", { x, y }),
  getOverlayBounds: () => ipcRenderer.invoke("compagnon:overlay-get-bounds"),
  onInitiative: (cb) => {
    ipcRenderer.on("compagnon:initiative", (_e, payload) => {
      try {
        cb(payload);
      } catch (_) {}
    });
  },
  onSessionEvent: (cb) => {
    ipcRenderer.on("compagnon:session-event", (_e, payload) => {
      try {
        cb(payload);
      } catch (_) {}
    });
  },
  sessionDecision: (body) => ipcRenderer.invoke("compagnon:session-decision", body || {}),
});
