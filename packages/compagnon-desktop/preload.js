const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("compagnonDesktop", {
  getConfig: () => ipcRenderer.invoke("compagnon:get-config"),
  openChat: () => ipcRenderer.send("compagnon:open-chat"),
  setMood: (mood) => ipcRenderer.send("compagnon:overlay-mood", mood),
  onMood: (cb) => {
    ipcRenderer.on("compagnon:mood", (_e, mood) => {
      try {
        cb(mood);
      } catch (_) {}
    });
  },
});
