"use strict";

/**
 * Bridge local avatar présence v1 — SSE loopback pour FaceRig + adaptateurs externes.
 * Contrat : packages/cortex/docs/avatar_presence_events_v1.md
 */

const http = require("http");

const DEFAULTS = {
  enabled: false,
  host: "127.0.0.1",
  port: 8765,
  heartbeatMs: 30_000,
};

/**
 * @param {{ enabled?: boolean, host?: string, port?: number, heartbeatMs?: number }} opts
 * @param {{ onCommand?: (cmd: object) => object | Promise<object> }} hooks
 */
function createAvatarBridge(opts, hooks) {
  const cfg = { ...DEFAULTS, ...(opts || {}) };
  /** @type {import("http").Server | null} */
  let server = null;
  /** @type {Set<import("http").ServerResponse>} */
  const clients = new Set();
  let heartbeatTimer = null;
  let lastState = {
    v: 1,
    event: "avatar.idle",
    ts: new Date().toISOString(),
    source: "compagnon-desktop",
    mood: "serene",
    talking: false,
    text: null,
    ms: null,
    initiative: null,
    detail: {},
  };

  function envelope(partial) {
    const ev = {
      ...lastState,
      ...partial,
      v: 1,
      ts: new Date().toISOString(),
      source: "compagnon-desktop",
    };
    lastState = {
      v: 1,
      event: ev.event,
      ts: ev.ts,
      source: ev.source,
      mood: ev.mood != null ? ev.mood : lastState.mood,
      talking: Boolean(ev.talking),
      text: ev.text != null ? ev.text : null,
      ms: ev.ms != null ? ev.ms : null,
      initiative: ev.initiative != null ? ev.initiative : null,
      detail: ev.detail && typeof ev.detail === "object" ? ev.detail : {},
    };
    return lastState;
  }

  function writeSse(res, data) {
    try {
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    } catch (_) {
      clients.delete(res);
    }
  }

  function publish(partial) {
    if (!cfg.enabled) return lastState;
    const ev = envelope(partial);
    for (const res of clients) writeSse(res, ev);
    return ev;
  }

  function publishMood(mood) {
    let tone = "serene";
    if (mood && typeof mood === "object") {
      tone = String(mood.tone || mood.mood || mood.label || "serene");
    } else if (mood != null) {
      tone = String(mood);
    }
    return publish({
      event: "avatar.mood",
      mood: tone.slice(0, 40),
      talking: false,
      text: null,
      ms: null,
      initiative: null,
    });
  }

  function publishTalking({ text, ms, talking }) {
    const on = talking !== false;
    const est = Number(ms);
    return publish({
      event: on ? "avatar.talking" : "avatar.idle",
      talking: on,
      text: text != null ? String(text).slice(0, 140) : null,
      ms: Number.isFinite(est) ? Math.max(0, Math.min(20000, est)) : null,
      initiative: null,
    });
  }

  function publishSay(text) {
    const t = String(text || "").slice(0, 140);
    return publish({
      event: "avatar.say",
      talking: true,
      text: t,
      ms: Math.min(12000, Math.max(900, 55 * t.length)),
      initiative: null,
    });
  }

  function publishInitiative(payload) {
    return publish({
      event: "avatar.initiative",
      mood: "tense",
      talking: false,
      text: payload && payload.message ? String(payload.message).slice(0, 140) : null,
      ms: null,
      initiative: payload || null,
    });
  }

  function readBody(req) {
    return new Promise((resolve) => {
      let data = "";
      req.on("data", (c) => {
        data += c;
        if (data.length > 64_000) req.destroy();
      });
      req.on("end", () => {
        try {
          resolve(data ? JSON.parse(data) : {});
        } catch (_) {
          resolve({});
        }
      });
      req.on("error", () => resolve({}));
    });
  }

  function json(res, status, body) {
    const raw = JSON.stringify(body);
    res.writeHead(status, {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Length": Buffer.byteLength(raw),
      "Access-Control-Allow-Origin": "*",
    });
    res.end(raw);
  }

  async function handle(req, res) {
    const url = new URL(req.url || "/", `http://${cfg.host}:${cfg.port}`);
    const path = url.pathname;

    if (req.method === "OPTIONS") {
      res.writeHead(204, {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      });
      res.end();
      return;
    }

    if (req.method === "GET" && path === "/avatar/state") {
      json(res, 200, { ok: true, state: lastState });
      return;
    }

    if (req.method === "GET" && (path === "/avatar/stream" || path === "/avatar/events")) {
      res.writeHead(200, {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
        "Access-Control-Allow-Origin": "*",
      });
      writeSse(res, lastState);
      clients.add(res);
      req.on("close", () => clients.delete(res));
      return;
    }

    if (req.method === "GET" && (path === "/healthz" || path === "/avatar/healthz")) {
      json(res, 200, {
        ok: true,
        service: "avatar-bridge",
        clients: clients.size,
        port: cfg.port,
      });
      return;
    }

    if (req.method === "POST" && path === "/avatar/command") {
      const body = await readBody(req);
      const cmd = String((body && body.cmd) || "").trim();
      if (!cmd) {
        json(res, 400, { ok: false, error: "cmd manquant" });
        return;
      }
      try {
        const result =
          hooks && typeof hooks.onCommand === "function"
            ? await hooks.onCommand({ ...body, cmd, v: 1 })
            : { ok: false, error: "no handler" };
        json(res, 200, result && typeof result === "object" ? result : { ok: true });
      } catch (e) {
        json(res, 500, { ok: false, error: String((e && e.message) || e).slice(0, 160) });
      }
      return;
    }

    json(res, 404, { ok: false, error: "not found" });
  }

  function start() {
    if (!cfg.enabled) return { ok: false, reason: "disabled" };
    if (server) return { ok: true, port: cfg.port, already: true };
    server = http.createServer((req, res) => {
      handle(req, res).catch(() => {
        try {
          res.statusCode = 500;
          res.end();
        } catch (_) {}
      });
    });
    server.listen(cfg.port, cfg.host, () => {
      console.log(`[avatar-bridge] http://${cfg.host}:${cfg.port}/avatar/stream`);
    });
    server.on("error", (err) => {
      console.warn("[avatar-bridge]", err && err.message ? err.message : err);
    });
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    heartbeatTimer = setInterval(() => {
      publish({
        event: "avatar.heartbeat",
        talking: lastState.talking,
        text: null,
        ms: null,
        initiative: null,
      });
    }, cfg.heartbeatMs || 30_000);
    return { ok: true, port: cfg.port };
  }

  function stop() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
    for (const res of clients) {
      try {
        res.end();
      } catch (_) {}
    }
    clients.clear();
    if (server) {
      try {
        server.close();
      } catch (_) {}
      server = null;
    }
  }

  return {
    start,
    stop,
    publish,
    publishMood,
    publishTalking,
    publishSay,
    publishInitiative,
    getState: () => ({ ...lastState }),
    enabled: () => Boolean(cfg.enabled),
  };
}

module.exports = { createAvatarBridge, DEFAULTS };
