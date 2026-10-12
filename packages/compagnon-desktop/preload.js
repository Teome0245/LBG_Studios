const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("compagnonDesktop", {
  getConfig: () => ipcRenderer.invoke("compagnon:get-config"),
  openChat: () => ipcRenderer.send("compagnon:open-chat"),
  openChatWithAgir: (payload) => ipcRenderer.send("compagnon:open-chat-agir", payload || {}),
  setMood: (mood) => ipcRenderer.send("compagnon:overlay-mood", mood),
  onMood: (cb) => {
    ipcRenderer.on("compagnon:mood", (_e, mood) => {
      try {
        cb(mood);
      } catch (_) {}
    });
  },
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
