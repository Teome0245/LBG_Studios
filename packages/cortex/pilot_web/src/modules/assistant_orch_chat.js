/** P2 — Assistant produit via POST /v1/pilot/orch/ask + historique serveur.
 *  Repli automatique vers legacy `/v1/pilot/route` si Orch /ask timeout ou erreur.
 */

const STORAGE_CONV_ID = "lbg_orch_conversation_id"; // même clé que Orch UI 5174
const STORAGE_ORCH_CHAT_MODE = "lbg_pilot_assistant_orch_chat_v1";
const ASK_TIMEOUT_MS = 55000;

function getBase() {
  const App = globalThis.PilotApp;
  if (App && typeof App.getBase === "function") return App.getBase();
  try {
    return String(window.location.origin || "").replace(/\/$/, "") || "http://127.0.0.1:8000";
  } catch (_) {
    return "http://127.0.0.1:8000";
  }
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function orchChatEnabled() {
  try {
    const v = localStorage.getItem(STORAGE_ORCH_CHAT_MODE);
    if (v === "0") return false;
    if (v === "1") return true;
  } catch (_) {}
  return true;
}

function newConversationId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return "orch-" + crypto.randomUUID();
  }
  return "orch-" + Date.now() + "-" + Math.random().toString(36).slice(2, 9);
}

function getConversationId() {
  try {
    const v = localStorage.getItem(STORAGE_CONV_ID);
    if (v && String(v).trim()) return String(v).trim();
  } catch (_) {}
  const id = newConversationId();
  persistConversationId(id);
  return id;
}

function persistConversationId(id) {
  try {
    localStorage.setItem(STORAGE_CONV_ID, String(id || ""));
  } catch (_) {}
}

function stripOrchReply(text) {
  return String(text || "")
    .replace(/<think>[\s\S]*?<\/think>\s*/gi, "")
    .replace(/<\/?think>/gi, "")
    .trim();
}

function extractOrchAskReply(data) {
  const resp = data && data.response ? data.response : data;
  if (!resp) return "";
  if (typeof resp === "string") return stripOrchReply(resp);
  if (typeof resp !== "object") return "";
  if (typeof resp.content === "string") return stripOrchReply(resp.content);
  if (typeof resp.response === "string") return stripOrchReply(resp.response);
  if (typeof resp.message === "string") return stripOrchReply(resp.message);
  if (typeof resp.reply === "string") return stripOrchReply(resp.reply);
  return "";
}

function formatRelTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const diff = Date.now() - d.getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return "à l'instant";
    if (m < 60) return m + "m";
    const h = Math.floor(m / 60);
    if (h < 48) return h + "h";
    const j = Math.floor(h / 24);
    return j + "j";
  } catch (_) {
    return "";
  }
}

async function orchFetchJson(path, options) {
  const opts = options || {};
  const ctrl = opts.signal ? null : new AbortController();
  const timer =
    ctrl && ASK_TIMEOUT_MS
      ? setTimeout(function () {
          try {
            ctrl.abort();
          } catch (_) {}
        }, opts.timeoutMs != null ? opts.timeoutMs : ASK_TIMEOUT_MS)
      : null;
  try {
    const r = await fetch(getBase() + "/v1/pilot/orch" + path, {
      ...opts,
      signal: opts.signal || (ctrl && ctrl.signal),
    });
    const j = await r.json().catch(function () {
      return {};
    });
    if (!r.ok) {
      const err = (j && (j.error || j.detail || j.body)) || "HTTP " + r.status;
      throw new Error(String(err).slice(0, 280));
    }
    if (j && j.disabled === true) throw new Error(j.detail || "Proxies Orch désactivés");
    if (j && j.ok === false) throw new Error(j.error || j.detail || "orch ok:false");
    return j;
  } catch (e) {
    if (e && e.name === "AbortError") {
      throw new Error("Timeout Orch /ask (" + Math.round((opts.timeoutMs || ASK_TIMEOUT_MS) / 1000) + "s)");
    }
    throw e;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

function turnsToHistoryItems(turns) {
  const items = [];
  const arr = Array.isArray(turns) ? turns : [];
  for (let i = 0; i < arr.length; i += 1) {
    const t = arr[i];
    if (!t || typeof t !== "object") continue;
    const role = t.role === "user" ? "chat_user" : "chat_assistant";
    const text = stripOrchReply(t.content || "");
    if (!text) continue;
    items.push({
      ts: t.ts || t.created_at || new Date().toISOString(),
      kind: role,
      text: text.slice(0, 8000),
    });
  }
  return items.slice(-40);
}

function renderConversationList(conversations, activeId) {
  const el = document.getElementById("assistant-conv-list");
  if (!el) return;
  const rows = Array.isArray(conversations) ? conversations : [];
  const active = rows.filter(function (c) {
    return !c.archived;
  });
  const archived = rows.filter(function (c) {
    return c.archived;
  });
  function row(c) {
    const id = c.id || "";
    const title = (c.title || id || "Sans titre").slice(0, 72);
    const rel = formatRelTime(c.updated_at);
    const activeCls = id === activeId ? " assistant-conv-item--active" : "";
    return (
      '<button type="button" class="assistant-conv-item' +
      activeCls +
      '" data-conv-id="' +
      esc(id) +
      '" title="' +
      esc(c.title || "") +
      '">' +
      '<span class="assistant-conv-title">' +
      esc(title) +
      "</span>" +
      '<span class="assistant-conv-meta">' +
      esc(rel) +
      (c.turn_count != null ? " · " + esc(String(c.turn_count)) + " tours" : "") +
      "</span></button>"
    );
  }
  let html = active.length
    ? active.map(row).join("")
    : '<p class="muted" style="padding:0.5rem">Aucune discussion.</p>';
  if (archived.length) {
    html +=
      '<details class="assistant-conv-archived" style="margin-top:0.5rem"><summary class="muted">Archivées (' +
      archived.length +
      ")</summary>" +
      archived.map(row).join("") +
      "</details>";
  }
  el.innerHTML = html;
}

async function loadConversations() {
  const hint = document.getElementById("assistant-conv-hint");
  try {
    const j = await orchFetchJson("/chat/conversations?limit=40&include_archived=true", {
      timeoutMs: 12000,
    });
    const list = j.conversations || [];
    renderConversationList(list, getConversationId());
    if (hint) hint.textContent = list.length + " discussion(s)";
    return list;
  } catch (e) {
    if (hint) hint.textContent = String(e);
    return [];
  }
}

async function loadOrchComposerOptions() {
  const agentEl = document.getElementById("assistant-orch-agent");
  const modelEl = document.getElementById("assistant-orch-model");
  if (!agentEl && !modelEl) return;
  const agentVal = agentEl ? agentEl.value : "auto";
  const modelVal = modelEl ? modelEl.value : "auto";
  try {
    const map = await orchFetchJson("/agents/map", { timeoutMs: 12000 });
    const agents = Array.isArray(map.agents) ? map.agents : [];
    if (agentEl) {
      agentEl.innerHTML =
        '<option value="auto">auto (RouterIA)</option>' +
        agents
          .slice(0, 48)
          .map(function (a) {
            const id = a.id || a.name || "";
            const label = (a.name || a.id || id).slice(0, 48);
            return '<option value="' + esc(id) + '">' + esc(label) + "</option>";
          })
          .join("");
      try {
        agentEl.value = agentVal;
      } catch (_) {}
    }
  } catch (_) {}
  try {
    const prov = await orchFetchJson("/providers/catalog", { timeoutMs: 20000 });
    const providers = Array.isArray(prov.providers) ? prov.providers : [];
    const models = [];
    for (let i = 0; i < providers.length; i += 1) {
      const p = providers[i];
      const pid = p.id || p.name || "";
      const ms = Array.isArray(p.models) ? p.models : [];
      for (let j = 0; j < ms.length; j += 1) {
        const m = ms[j];
        const mid = typeof m === "string" ? m : m.id || m.name || "";
        if (mid) models.push({ id: mid, label: (pid ? pid + "/" : "") + mid });
      }
    }
    if (modelEl) {
      modelEl.innerHTML =
        '<option value="auto">auto</option>' +
        models
          .slice(0, 64)
          .map(function (m) {
            return '<option value="' + esc(m.id) + '">' + esc(m.label) + "</option>";
          })
          .join("");
      try {
        modelEl.value = modelVal;
      } catch (_) {}
    }
  } catch (_) {}
}

async function loadConversationContext(conversationId) {
  const App = globalThis.PilotApp;
  const cid = conversationId || getConversationId();
  const j = await orchFetchJson("/chat/context/" + encodeURIComponent(cid), {
    timeoutMs: 12000,
  });
  const items = turnsToHistoryItems(j.turns);
  if (App && typeof App.assistantHistorySave === "function") {
    App.assistantHistorySave(items);
    App.assistantHistoryRender();
  }
  return j;
}

async function switchConversation(id) {
  if (!id) return;
  persistConversationId(id);
  await loadConversationContext(id);
  renderConversationList(await loadConversations(), id);
}

function startNewChat() {
  const id = newConversationId();
  persistConversationId(id);
  const App = globalThis.PilotApp;
  if (App && typeof App.assistantHistorySave === "function") {
    App.assistantHistorySave([]);
    App.assistantHistoryRender();
  }
  loadConversations().then(function (list) {
    renderConversationList(list, id);
  });
}

function readOrchComposer() {
  const agentEl = document.getElementById("assistant-orch-agent");
  const modelEl = document.getElementById("assistant-orch-model");
  const profileEl = document.getElementById("assistant-orch-profile");
  const agent = agentEl && agentEl.value ? String(agentEl.value) : "auto";
  const model = modelEl && modelEl.value ? String(modelEl.value) : "auto";
  const profile = profileEl && profileEl.value ? String(profileEl.value) : "compagnon";
  return {
    agent: agent === "auto" ? null : agent,
    model: model === "auto" ? null : model,
    profile: profile,
  };
}

function setOrchBadge(resp) {
  const el = document.getElementById("assistant-dialogue-badge");
  if (!el || !resp || typeof resp !== "object") return;
  el.hidden = false;
  el.className = "assistant-route-badge assistant-route-badge--llm";
  const src = resp.source || "orch";
  el.textContent = String(src).slice(0, 14);
  const bits = [resp.source, resp.model || resp.model_used, resp.provider].filter(Boolean);
  if (resp.latency != null) bits.push(resp.latency + " ms");
  el.title = bits.join(" · ");
}

async function assistantOrchConverse(legacyFn) {
  const App = globalThis.PilotApp;
  const textEl = document.getElementById("assistant-text");
  const rawEl = document.getElementById("assistant-raw");
  const prettyEl = document.getElementById("assistant-pretty");
  const text = textEl && textEl.value ? String(textEl.value).trim() : "";
  if (!text) {
    if (App && App.assistantUiHint) App.assistantUiHint("Message vide", true);
    return;
  }
  let channelMode = "discuter";
  try {
    if (typeof App.assistantApplyChannelModeForMessage === "function") {
      channelMode = App.assistantApplyChannelModeForMessage(text) || "discuter";
    }
  } catch (_) {}
  if (App && App.assistantClearDialogueRouteBadge) App.assistantClearDialogueRouteBadge();
  if (App && App.assistantUiHint) {
    App.assistantUiHint(
      channelMode === "piloter" ? "Ops · Orch /ask…" : "Réflexion · Orch /ask…",
      false
    );
  }

  const cid = getConversationId();
  const comp = readOrchComposer();
  const body = {
    prompt: text,
    mode: "auto",
    profile: comp.profile,
    conversation_id: cid,
  };
  if (comp.agent) body.agent = comp.agent;
  if (comp.model) body.model = comp.model;

  if (textEl) textEl.value = "";

  let out;
  try {
    out = await orchFetchJson("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      timeoutMs: ASK_TIMEOUT_MS,
    });
  } catch (e) {
    const msg = String(e);
    if (App && App.assistantUiHint) {
      App.assistantUiHint("Orch /ask KO — repli legacy… (" + msg.slice(0, 80) + ")", true);
    }
    if (textEl) textEl.value = text;
    if (typeof legacyFn === "function") {
      try {
        await legacyFn();
        if (App && App.assistantUiHint) {
          App.assistantUiHint("Repli legacy OK (Orch /ask indisponible)", false);
        }
        return;
      } catch (e2) {
        if (App && App.assistantUiHint) App.assistantUiHint("Legacy aussi KO: " + e2, true);
        return;
      }
    }
    if (App && App.assistantUiHint) App.assistantUiHint(msg, true);
    return;
  }

  const resp = out.response || out;
  const reply = extractOrchAskReply(out) || "(réponse vide)";
  if (rawEl) rawEl.textContent = JSON.stringify(out, null, 2);
  if (prettyEl) {
    prettyEl.innerHTML =
      '<pre style="margin:0;white-space:pre-wrap">' + esc(reply.slice(0, 4000)) + "</pre>";
  }
  setOrchBadge(resp && typeof resp === "object" ? resp : { source: "orch" });

  try {
    await loadConversationContext(cid);
    await loadConversations();
  } catch (_) {
    if (App && typeof App.assistantHistoryAdd === "function") {
      App.assistantHistoryAdd({ kind: "chat_user", text: text });
      App.assistantHistoryAdd({ kind: "chat_assistant", text: reply });
    }
  }
  try {
    if (App && App.assistantAvatarSay) App.assistantAvatarSay(reply);
  } catch (_) {}
  if (App && App.assistantUiHint) {
    const src = resp && typeof resp === "object" ? resp.source || "ask" : "ask";
    App.assistantUiHint("Orch · " + src, false);
  }
}

function bindConversationSidebar() {
  const root = document.getElementById("assistant-conv-sidebar");
  if (!root || root.dataset.bound) return;
  root.dataset.bound = "1";

  const btnNew = document.getElementById("btn-assistant-conv-new");
  if (btnNew) btnNew.addEventListener("click", function () { startNewChat(); });
  const btnRef = document.getElementById("btn-assistant-conv-refresh");
  if (btnRef) btnRef.addEventListener("click", function () { loadConversations(); });

  root.addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-conv-id]");
    if (!btn) return;
    const id = btn.getAttribute("data-conv-id");
    if (id) {
      switchConversation(id).catch(function (e) {
        const App = globalThis.PilotApp;
        if (App && App.assistantUiHint) App.assistantUiHint(String(e), true);
      });
    }
  });

  const legacyCb = document.getElementById("assistant-pref-legacy-route");
  if (legacyCb) {
    legacyCb.checked = !orchChatEnabled();
    legacyCb.addEventListener("change", function () {
      try {
        localStorage.setItem(STORAGE_ORCH_CHAT_MODE, legacyCb.checked ? "0" : "1");
      } catch (_) {}
    });
  }
}

function rebindConverseTriggers(runConverse) {
  const btn = document.getElementById("btn-assistant-converse");
  if (btn) {
    const clone = btn.cloneNode(true);
    btn.parentNode.replaceChild(clone, btn);
    clone.addEventListener("click", function () {
      runConverse().catch(function (e) {
        const App = globalThis.PilotApp;
        if (App && App.assistantUiHint) App.assistantUiHint(String(e), true);
      });
    });
  }
  const ta = document.getElementById("assistant-text");
  if (ta && !ta.dataset.orchComposerKeys) {
    ta.dataset.orchComposerKeys = "1";
    ta.addEventListener(
      "keydown",
      function (e) {
        if (e.key !== "Enter" || e.shiftKey || e.ctrlKey || e.metaKey) return;
        if (!orchChatEnabled()) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        runConverse().catch(function (err) {
          const App = globalThis.PilotApp;
          if (App && App.assistantUiHint) App.assistantUiHint(String(err), true);
        });
      },
      true
    );
  }
}

export function installAssistantOrchChat() {
  const App = globalThis.PilotApp || (globalThis.PilotApp = {});
  bindConversationSidebar();

  const origConverse = App.assistantConverse;
  async function runConverse() {
    if (orchChatEnabled()) {
      return assistantOrchConverse(origConverse);
    }
    if (typeof origConverse === "function") return origConverse();
  }
  App.assistantConverse = runConverse;
  rebindConverseTriggers(runConverse);

  const origClear = App.assistantHistoryClear;
  App.assistantHistoryClear = function wrappedHistoryClear() {
    if (typeof origClear === "function") origClear();
    if (orchChatEnabled()) startNewChat();
  };

  const origApply = App.pilotApplyRoute;
  App.pilotApplyRoute = function assistantOrchApplyRoute() {
    if (typeof origApply === "function") origApply();
    const r = App.pilotParseRoute ? App.pilotParseRoute() : "";
    if (r === "assistant" && orchChatEnabled()) {
      loadOrchComposerOptions().catch(function () {});
      loadConversations()
        .then(function () {
          return loadConversationContext(getConversationId());
        })
        .catch(function () {});
    }
  };

  App.assistantOrchLoadConversations = loadConversations;
  App.assistantOrchStartNewChat = startNewChat;
}
