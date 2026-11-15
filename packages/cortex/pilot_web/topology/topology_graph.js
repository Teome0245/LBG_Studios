/**
 * Topology Graph — Second Brain & Knowledge Explorer (LBG Studios)
 * Inspiré du visual web crawler et du réseau de neurones / graphe de connaissances.
 */

(function () {
  let canvas, ctx;
  let animId = null;
  let nodes = [];
  let edges = [];
  let nodeMap = {};
  let selectedNode = null;
  let hoveredNode = null;
  let activeFilter = "all";

  // Transform (pan & zoom)
  let transform = { x: 0, y: 0, k: 1 };
  let isDragging = false;
  let dragNode = null;
  let lastMouse = { x: 0, y: 0 };

  // Spider pulse animation packets
  let packets = [];

  const COLOR_PALETTE = {
    planet: { main: "#f59e0b", glow: "rgba(245, 158, 11, 0.4)", radius: 24, label: "Planète" },
    city: { main: "#ec4899", glow: "rgba(236, 72, 153, 0.4)", radius: 21, label: "Ville / Lieu" },
    npc: { main: "#10b981", glow: "rgba(16, 185, 129, 0.4)", radius: 18, label: "PNJ" },
    faction: { main: "#a855f7", glow: "rgba(168, 85, 247, 0.4)", radius: 20, label: "Faction" },
    mechanic: { main: "#06b6d4", glow: "rgba(6, 182, 212, 0.4)", radius: 16, label: "Mécanique" },
    bot: { main: "#38bdf8", glow: "rgba(56, 189, 248, 0.7)", radius: 17, label: "Joueur IA (Live)" },
    default: { main: "#94a3b8", glow: "rgba(148, 163, 184, 0.3)", radius: 15, label: "Document" },
  };

  async function loadTopologyData() {
    try {
      const resp = await fetch("/v1/pilot/topology").catch(() => null);
      if (resp && resp.ok) return await resp.json();
    } catch (_) {}

    try {
      const resp2 = await fetch("assets/topology_data.json");
      if (resp2.ok) return await resp2.json();
    } catch (_) {}

    return null;
  }

  function initGraphData(data) {
    if (!data || !data.nodes) return;
    nodes = [];
    nodeMap = {};
    edges = [];

    const rawNodes = data.nodes;
    const rawEdges = data.edges || [];

    const width = canvas.width;
    const height = canvas.height;
    const nodeKeys = Object.keys(rawNodes);

    // Initial positioning in concentric circle
    nodeKeys.forEach((key, idx) => {
      const n = rawNodes[key];
      const angle = (idx / nodeKeys.length) * 2 * Math.PI;
      const dist = 180 + (idx % 3) * 60;
      const nodeObj = {
        id: n.id || key,
        title: n.title || key,
        type: n.type || "default",
        path: n.path || "",
        links_to: n.links_to || [],
        play_mode: n.play_mode,
        goal: n.goal,
        quest_id: n.quest_id,
        pos: n.pos,
        linked_studio: n.linked_studio,
        is_live: n.is_live,
        x: width / 2 + Math.cos(angle) * dist + (Math.random() - 0.5) * 40,
        y: height / 2 + Math.sin(angle) * dist + (Math.random() - 0.5) * 40,
        vx: 0,
        vy: 0,
        radius: (COLOR_PALETTE[n.type] || COLOR_PALETTE.default).radius,
      };
      nodes.push(nodeObj);
      nodeMap[nodeObj.id] = nodeObj;
    });

    rawEdges.forEach((e) => {
      if (nodeMap[e.source] && nodeMap[e.target]) {
        edges.push({
          source: nodeMap[e.source],
          target: nodeMap[e.target],
        });
      }
    });

    // Populate stats
    const elNodes = document.getElementById("topo-stat-nodes");
    const elEdges = document.getElementById("topo-stat-edges");
    const elBots = document.getElementById("topo-stat-bots");
    if (elNodes) elNodes.textContent = nodes.length;
    if (elEdges) elEdges.textContent = edges.length;
    if (elBots) elBots.textContent = data.live_bots_count || 0;
  }

  function updateGraphData(data) {
    if (!data || !data.nodes) return;
    const rawNodes = data.nodes;
    const rawEdges = data.edges || [];

    Object.keys(rawNodes).forEach((key) => {
      const n = rawNodes[key];
      if (nodeMap[key]) {
        Object.assign(nodeMap[key], {
          play_mode: n.play_mode,
          goal: n.goal,
          quest_id: n.quest_id,
          pos: n.pos,
          linked_studio: n.linked_studio,
          is_live: n.is_live,
          links_to: n.links_to || nodeMap[key].links_to,
        });
      } else {
        const angle = Math.random() * 2 * Math.PI;
        const dist = 220;
        const nodeObj = {
          id: n.id || key,
          title: n.title || key,
          type: n.type || "default",
          path: n.path || "",
          links_to: n.links_to || [],
          play_mode: n.play_mode,
          goal: n.goal,
          quest_id: n.quest_id,
          pos: n.pos,
          linked_studio: n.linked_studio,
          is_live: n.is_live,
          x: canvas.width / 2 + Math.cos(angle) * dist,
          y: canvas.height / 2 + Math.sin(angle) * dist,
          vx: 0,
          vy: 0,
          radius: (COLOR_PALETTE[n.type] || COLOR_PALETTE.default).radius,
        };
        nodes.push(nodeObj);
        nodeMap[nodeObj.id] = nodeObj;
      }
    });

    edges = [];
    rawEdges.forEach((e) => {
      if (nodeMap[e.source] && nodeMap[e.target]) {
        edges.push({
          source: nodeMap[e.source],
          target: nodeMap[e.target],
        });
      }
    });

    const elNodes = document.getElementById("topo-stat-nodes");
    const elEdges = document.getElementById("topo-stat-edges");
    const elBots = document.getElementById("topo-stat-bots");
    if (elNodes) elNodes.textContent = nodes.length;
    if (elEdges) elEdges.textContent = edges.length;
    if (elBots) elBots.textContent = data.live_bots_count || 0;

    // Refresh drawer if selected node is a live bot
    if (selectedNode && selectedNode.type === "bot" && nodeMap[selectedNode.id]) {
      showDetails(nodeMap[selectedNode.id]);
    }
  }

  function simulate() {
    // Force physics
    const repulsion = 1200;
    const springLen = 140;
    const springK = 0.04;
    const damping = 0.85;

    // Repulsion
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const distSq = dx * dx + dy * dy + 100;
        const dist = Math.sqrt(distSq);
        const force = repulsion / distSq;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx -= fx;
        a.vy -= fy;
        b.vx += fx;
        b.vy += fy;
      }
    }

    // Spring attraction along edges
    edges.forEach((e) => {
      const a = e.source;
      const b = e.target;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - springLen) * springK;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    });

    // Center gravity & update
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    nodes.forEach((n) => {
      if (n === dragNode) return;
      n.vx += (cx - n.x) * 0.002;
      n.vy += (cy - n.y) * 0.002;
      n.vx *= damping;
      n.vy *= damping;
      n.x += n.vx;
      n.y += n.vy;
    });

    // Update packets
    for (let i = packets.length - 1; i >= 0; i--) {
      const p = packets[i];
      p.t += p.speed;
      if (p.t >= 1) packets.splice(i, 1);
    }
  }

  function render() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    // 1. Draw Edges
    edges.forEach((e) => {
      const isHighlighted =
        hoveredNode && (e.source === hoveredNode || e.target === hoveredNode);
      ctx.beginPath();
      ctx.moveTo(e.source.x, e.source.y);
      ctx.lineTo(e.target.x, e.target.y);
      ctx.strokeStyle = isHighlighted
        ? "rgba(56, 189, 248, 0.8)"
        : "rgba(56, 189, 248, 0.15)";
      ctx.lineWidth = isHighlighted ? 2.5 : 1;
      ctx.stroke();
    });

    // 2. Draw Packets (Spider pulse)
    packets.forEach((p) => {
      const x = p.source.x + (p.target.x - p.source.x) * p.t;
      const y = p.source.y + (p.target.y - p.source.y) * p.t;
      ctx.beginPath();
      ctx.arc(x, y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#38bdf8";
      ctx.shadowColor = "#38bdf8";
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // 3. Draw Nodes
    nodes.forEach((n) => {
      if (activeFilter !== "all" && n.type !== activeFilter) return;

      const style = COLOR_PALETTE[n.type] || COLOR_PALETTE.default;
      const isSel = selectedNode === n;
      const isHov = hoveredNode === n;

      // Glow halo
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + (isHov || isSel ? 8 : 4), 0, Math.PI * 2);
      ctx.fillStyle = isSel ? "rgba(255, 255, 255, 0.3)" : style.glow;
      ctx.fill();

      // Core circle
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = style.main;
      ctx.fill();
      ctx.lineWidth = isSel ? 3 : 1.5;
      ctx.strokeStyle = isSel ? "#ffffff" : "rgba(255,255,255,0.7)";
      ctx.stroke();

      // Label
      ctx.font = isSel ? "bold 13px system-ui" : "11px system-ui";
      ctx.fillStyle = isSel ? "#ffffff" : "#cbd5e1";
      ctx.textAlign = "center";
      ctx.fillText(n.title, n.x, n.y + n.radius + 15);
    });

    ctx.restore();
  }

  function loop() {
    simulate();
    render();
    animId = requestAnimationFrame(loop);
  }

  function triggerSpiderPulse() {
    if (!edges.length) return;
    edges.forEach((e) => {
      packets.push({
        source: e.source,
        target: e.target,
        t: 0,
        speed: 0.012 + Math.random() * 0.015,
      });
    });
  }

  function screenToWorld(sx, sy) {
    return {
      x: (sx - transform.x) / transform.k,
      y: (sy - transform.y) / transform.k,
    };
  }

  function getNodeAt(x, y) {
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      if (activeFilter !== "all" && n.type !== activeFilter) continue;
      const dx = n.x - x;
      const dy = n.y - y;
      if (dx * dx + dy * dy <= (n.radius + 5) * (n.radius + 5)) {
        return n;
      }
    }
    return null;
  }

  function showDetails(node) {
    selectedNode = node;
    const drawer = document.getElementById("topology-drawer");
    if (!drawer) return;

    if (!node) {
      drawer.classList.remove("open");
      return;
    }

    const badge = document.getElementById("topo-drawer-badge");
    const title = document.getElementById("topo-drawer-title");
    const pathEl = document.getElementById("topo-drawer-path");
    const linksList = document.getElementById("topo-drawer-links");

    const style = COLOR_PALETTE[node.type] || COLOR_PALETTE.default;
    if (badge) {
      badge.textContent = style.label;
      badge.className = `topology-drawer-badge badge-${node.type}`;
    }
    if (title) title.textContent = node.title;
    if (pathEl) {
      if (node.type === "bot") {
        let botHtml = `<div style="background:rgba(2,132,199,0.2);border:1px solid #38bdf8;border-radius:6px;padding:10px;margin-bottom:8px;">`;
        botHtml += `<div style="color:#38bdf8;font-weight:700;margin-bottom:6px;display:flex;align-items:center;gap:6px;"><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#38bdf8;box-shadow:0 0 8px #38bdf8;"></span> En direct sur .246:8787</div>`;
        botHtml += `<div style="font-size:0.82rem;color:#cbd5e1;margin-bottom:3px;"><strong>Mode :</strong> <span style="color:#f8fafc;">${node.play_mode || 'hub'}</span></div>`;
        botHtml += `<div style="font-size:0.82rem;color:#cbd5e1;margin-bottom:3px;"><strong>Objectif :</strong> <span style="color:#f8fafc;">${node.goal || 'exploration'}</span></div>`;
        if (node.quest_id) {
          botHtml += `<div style="font-size:0.82rem;color:#fde047;margin-bottom:3px;"><strong>Quête active :</strong> ${node.quest_id}</div>`;
        }
        if (node.pos && node.pos.length >= 3) {
          botHtml += `<div style="font-size:0.75rem;color:#94a3b8;font-family:monospace;margin-top:4px;">Coordonnées: [${Math.round(node.pos[0])}, ${Math.round(node.pos[1])}, ${Math.round(node.pos[2])}]</div>`;
        }
        if (node.linked_studio) {
          botHtml += `<div style="font-size:0.75rem;color:#c084fc;margin-top:4px;"><strong>Liaison Studio :</strong> ${node.linked_studio}</div>`;
        }
        botHtml += `</div>`;
        pathEl.innerHTML = botHtml;
      } else if (node.desc) {
        pathEl.innerHTML = `<div style="background:rgba(30,41,59,0.5);border:1px solid rgba(148,163,184,0.2);border-radius:6px;padding:10px;margin-bottom:8px;"><div style="font-size:0.86rem;color:#f1f5f9;line-height:1.45;margin-bottom:6px;">${node.desc}</div>${node.zone ? `<div style="font-size:0.78rem;color:#38bdf8;"><strong>Zone :</strong> ${node.zone}</div>` : ''}</div><div style="font-size:0.75rem;color:#94a3b8;">Fiche : docs/lore/${node.path}</div>`;
      } else {
        pathEl.textContent = `Fichier : docs/lore/${node.path}`;
      }
    }

    if (linksList) {
      linksList.innerHTML = "";
      (node.links_to || []).forEach((targetId) => {
        const btn = document.createElement("button");
        btn.className = "topology-chip-link";
        const targetNode = nodeMap[targetId];
        btn.textContent = targetNode ? targetNode.title : targetId;
        btn.onclick = () => {
          if (targetNode) {
            focusOnNode(targetNode);
            showDetails(targetNode);
          }
        };
        linksList.appendChild(btn);
      });
      if (!node.links_to || !node.links_to.length) {
        linksList.innerHTML = "<span style='color:#64748b;font-size:0.8rem;'>Aucun lien sortant direct</span>";
      }
    }

    drawer.classList.add("open");
  }

  function focusOnNode(node) {
    transform.x = canvas.width / 2 - node.x * transform.k;
    transform.y = canvas.height / 2 - node.y * transform.k;
  }

  function resetView() {
    transform = { x: 0, y: 0, k: 1 };
  }

  function resizeCanvas() {
    if (!canvas) return;
    const container = canvas.parentElement;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }
  }

  function bindEvents() {
    const container = document.getElementById("topology-container");
    if (!container) return;

    container.addEventListener("mousedown", (ev) => {
      const rect = canvas.getBoundingClientRect();
      const pos = screenToWorld(ev.clientX - rect.left, ev.clientY - rect.top);
      const hit = getNodeAt(pos.x, pos.y);

      if (hit) {
        dragNode = hit;
      } else {
        isDragging = true;
        container.classList.add("grabbing");
      }
      lastMouse = { x: ev.clientX, y: ev.clientY };
    });

    window.addEventListener("mousemove", (ev) => {
      const rect = canvas.getBoundingClientRect();
      const pos = screenToWorld(ev.clientX - rect.left, ev.clientY - rect.top);

      if (dragNode) {
        dragNode.x = pos.x;
        dragNode.y = pos.y;
        dragNode.vx = 0;
        dragNode.vy = 0;
      } else if (isDragging) {
        const dx = ev.clientX - lastMouse.x;
        const dy = ev.clientY - lastMouse.y;
        transform.x += dx;
        transform.y += dy;
        lastMouse = { x: ev.clientX, y: ev.clientY };
      } else {
        hoveredNode = getNodeAt(pos.x, pos.y);
      }
    });

    window.addEventListener("mouseup", (ev) => {
      if (dragNode) {
        const rect = canvas.getBoundingClientRect();
        const pos = screenToWorld(ev.clientX - rect.left, ev.clientY - rect.top);
        if (Math.hypot(ev.clientX - lastMouse.x, ev.clientY - lastMouse.y) < 5) {
          showDetails(dragNode);
        }
      }
      dragNode = null;
      isDragging = false;
      container.classList.remove("grabbing");
    });

    container.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const zoomFactor = ev.deltaY < 0 ? 1.1 : 0.9;
      const rect = canvas.getBoundingClientRect();
      const mouseX = ev.clientX - rect.left;
      const mouseY = ev.clientY - rect.top;

      transform.x = mouseX - (mouseX - transform.x) * zoomFactor;
      transform.y = mouseY - (mouseY - transform.y) * zoomFactor;
      transform.k *= zoomFactor;
    }, { passive: false });

    // Filter buttons
    document.querySelectorAll(".topology-filter-btn").forEach((btn) => {
      btn.onclick = () => {
        document.querySelectorAll(".topology-filter-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeFilter = btn.dataset.filter || "all";
      };
    });

    // Action buttons
    const btnPulse = document.getElementById("topo-btn-pulse");
    if (btnPulse) btnPulse.onclick = triggerSpiderPulse;

    const btnReset = document.getElementById("topo-btn-reset");
    if (btnReset) btnReset.onclick = resetView;

    const btnCloseDrawer = document.getElementById("topo-drawer-close");
    if (btnCloseDrawer) btnCloseDrawer.onclick = () => showDetails(null);

    window.addEventListener("resize", resizeCanvas);
  }

  let livePollTimer = null;

  window.topologyGraphInit = async function () {
    canvas = document.getElementById("topology-canvas");
    if (!canvas) return;
    ctx = canvas.getContext("2d");
    resizeCanvas();
    bindEvents();

    const data = await loadTopologyData();
    initGraphData(data);

    if (!animId) loop();
    setTimeout(triggerSpiderPulse, 600);

    // Polling des 10 bots en direct toutes les 4 secondes
    if (livePollTimer) clearInterval(livePollTimer);
    livePollTimer = setInterval(async () => {
      const freshData = await loadTopologyData();
      if (freshData) updateGraphData(freshData);
    }, 4000);
  };

  window.topologyGraphStop = function () {
    if (livePollTimer) {
      clearInterval(livePollTimer);
      livePollTimer = null;
    }
    if (animId) {
      cancelAnimationFrame(animId);
      animId = null;
    }
  };
})();

