/**
 * Module d'intégration Campus / Studio — Topologie Second Brain & Graphe de Connaissances.
 * Inspiré du visual web crawler et du mapping en graphe interactif.
 */
import "../../topology/topology_graph.js";

export function installTopologyModule() {
  // L'initialisation se fait via les hooks de route de pilot_router.js
  if (typeof window.topologyGraphInit === "function") {
    // Si la page est déjà sur #topology au chargement
    const hash = window.location.hash || "";
    if (hash.includes("topology")) {
      window.topologyGraphInit();
    }
  }
}

