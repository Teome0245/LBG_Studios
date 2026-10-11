    function getMetricsBearer() {
      const el = document.getElementById("metrics-bearer");
      const v = (el && el.value) ? el.value.trim() : "";
      try {
        if (v) localStorage.setItem(STORAGE_METRICS_BEARER_KEY, v);
        else localStorage.removeItem(STORAGE_METRICS_BEARER_KEY);
      } catch (_) {}
      return v;
    }

    function loadStoredMetricsBearer() {
      try {
        const v = localStorage.getItem(STORAGE_METRICS_BEARER_KEY);
        if (v) document.getElementById("metrics-bearer").value = v;
      } catch (_) {}
    }

    function renderMetricsLinks() {
      const el = document.getElementById("metrics-links");
      if (!el) return;
      const base = getBase();
      const j = window.__last_health_json;
      const orchRaw = j && typeof j.orchestrator_url === "string" ? j.orchestrator_url.trim() : "";
      const orch = orchRaw.replace(/\/$/, "");
      const internalEl = document.getElementById("ws-internal-http");
      const internal = internalEl && internalEl.value ? internalEl.value.trim().replace(/\/$/, "") : "";
      const items = [];
      items.push(
        "<li><a href=\"" + escapeHtml(base + "/metrics") + "\" target=\"_blank\" rel=\"noreferrer\"><code>backend</code> /metrics</a></li>"
      );
      if (orch) {
        items.push(
          "<li><a href=\"" + escapeHtml(orch + "/metrics") + "\" target=\"_blank\" rel=\"noreferrer\"><code>orchestrator</code> /metrics</a> <span class=\"muted\">(URL depuis santé)</span></li>"
        );
      } else {
        items.push("<li class=\"muted\"><code>orchestrator</code> /metrics — recharge la santé (bouton Rafraîchir) pour afficher le lien.</li>");
      }
      if (internal) {
        items.push(
          "<li><a href=\"" + escapeHtml(internal + "/metrics") + "\" target=\"_blank\" rel=\"noreferrer\"><code>HTTP interne WS</code> /metrics</a> <span class=\"muted\">(champ WS → HTTP interne)</span></li>"
        );
      } else {
        items.push("<li class=\"muted\"><code>HTTP interne</code> /metrics — renseigne l’URL snapshot (colonne WS).</li>");
      }
      el.innerHTML = "<ul style=\"margin:0.25rem 0;padding-left:1.25rem\">" + items.join("") + "</ul>";
    }

    async function probeBackendMetrics() {
      const out = document.getElementById("metrics-probe-out");
      if (!out) return;
      out.textContent = "…";
      const base = getBase();
      const url = base + "/metrics";
      const tok = getMetricsBearer();
      const headers = {};
      if (tok) headers["Authorization"] = "Bearer " + tok;
      try {
        const r = await fetch(url, { headers });
        const t = await r.text();
        out.textContent = "HTTP " + r.status + " " + url + "\n" + t.slice(0, 6000);
      } catch (e) {
        out.textContent = "Erreur: " + e;
      }
    }

    function openOrchestratorMetrics() {
      const j = window.__last_health_json;
      const orchRaw = j && typeof j.orchestrator_url === "string" ? j.orchestrator_url.trim() : "";
      const orch = orchRaw.replace(/\/$/, "");
      if (!orch) {
        alert("Recharge d'abord la santé (Rafraîchir) pour obtenir orchestrator_url.");
        return;
      }
      window.open(orch + "/metrics", "_blank", "noopener,noreferrer");
    }

    function openInternalHttpMetrics() {
      const internalEl = document.getElementById("ws-internal-http");
      const internal = internalEl && internalEl.value ? internalEl.value.trim().replace(/\/$/, "") : "";
      if (!internal) {
        alert("Renseigne l'URL HTTP interne (colonne WS).");
        return;
      }
      window.open(internal + "/metrics", "_blank", "noopener,noreferrer");
    }

    function sleep(ms) { return new Promise((res) => setTimeout(res, ms)); }

    function percentile(sortedNums, p) {
      if (!sortedNums.length) return null;
      const idx = Math.min(sortedNums.length - 1, Math.max(0, Math.ceil(p * sortedNums.length) - 1));
      return sortedNums[idx];
    }

    function loadCacheLatencyStats() {
      try {
        const raw = localStorage.getItem(STORAGE_CACHE_LAT_KEY);
        if (!raw) return { hit: [], miss: [] };
        const j = JSON.parse(raw);
        const hit = Array.isArray(j.hit) ? j.hit.filter((x) => typeof x === "number") : [];
        const miss = Array.isArray(j.miss) ? j.miss.filter((x) => typeof x === "number") : [];
        return { hit, miss };
      } catch (_) {
        return { hit: [], miss: [] };
      }
    }

    function saveCacheLatencyStats(st) {
      try {
        localStorage.setItem(STORAGE_CACHE_LAT_KEY, JSON.stringify(st));
      } catch (_) {}
    }

    function recordCacheLatencySample(resp) {
      if (!resp || typeof resp !== "object") return;
      if (typeof resp.elapsed_ms !== "number") return;
      const res = resp.result;
      const out = res && res.output;
      const remote = out && out.remote;
      const meta = remote && typeof remote === "object" ? remote.meta : null;
      const cacheHit = meta && typeof meta === "object" ? (meta.cache_hit === true) : false;
      const st = loadCacheLatencyStats();
      const bucket = cacheHit ? st.hit : st.miss;
      bucket.push(resp.elapsed_ms);
      // conserver les 200 derniers samples par bucket
      if (bucket.length > 200) bucket.splice(0, bucket.length - 200);
      saveCacheLatencyStats(st);
      renderCacheLatencyPanel();
    }

    function renderCacheLatencyPanel() {
      const el = document.getElementById("cache-lat-out");
      if (!el) return;
      const st = loadCacheLatencyStats();
      const hit = [...st.hit].sort((a, b) => a - b);
      const miss = [...st.miss].sort((a, b) => a - b);
      const summary = {
        hit: {
          n: hit.length,
          p50_ms: percentile(hit, 0.50),
          p95_ms: percentile(hit, 0.95),
          min_ms: hit.length ? hit[0] : null,
          max_ms: hit.length ? hit[hit.length - 1] : null,
        },
        miss: {
          n: miss.length,
          p50_ms: percentile(miss, 0.50),
          p95_ms: percentile(miss, 0.95),
          min_ms: miss.length ? miss[0] : null,
          max_ms: miss.length ? miss[miss.length - 1] : null,
        },
      };
      el.textContent = JSON.stringify(summary, null, 2);
    }

    function resetCacheLatencyPanel() {
      saveCacheLatencyStats({ hit: [], miss: [] });
      renderCacheLatencyPanel();
    }

    async function runBenchmark() {
      saveBase();
      const out = document.getElementById("bench-out");
      out.textContent = "…";

      const nRaw = document.getElementById("bench-n").value.trim();
      const sleepRaw = document.getElementById("bench-sleep-ms").value.trim();
      const n = Math.max(1, Math.min(200, parseInt(nRaw || "10", 10)));
      const pauseMs = Math.max(0, Math.min(5000, parseInt(sleepRaw || "0", 10)));

      const times = [];
      const errors = [];
      for (let i = 0; i < n; i++) {
        out.textContent = "Run " + (i + 1) + "/" + n + "…";
        try {
          const request = buildPilotRouteRequest();
          const r = await fetch(getBase() + "/v1/pilot/route", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(request),
          });
          const j = await r.json();
          if (!j || typeof j !== "object") throw new Error("réponse JSON invalide");
          if (j.ok !== true) throw new Error("ok=false: " + (j.error || "erreur inconnue"));
          if (typeof j.elapsed_ms !== "number") throw new Error("elapsed_ms manquant");
          times.push(j.elapsed_ms);
        } catch (e) {
          errors.push(String(e));
        }
        if (pauseMs) await sleep(pauseMs);
      }

      const sorted = [...times].sort((a, b) => a - b);
      const p50 = percentile(sorted, 0.50);
      const p95 = percentile(sorted, 0.95);
      const min = sorted.length ? sorted[0] : null;
      const max = sorted.length ? sorted[sorted.length - 1] : null;

      const summary = {
        n_requested: n,
        n_ok: times.length,
        n_errors: errors.length,
        min_ms: min,
        p50_ms: p50,
        p95_ms: p95,
        max_ms: max,
        target_vm: { p50_ms_lt: 2000, p95_ms_lt: 6000 },
        errors: errors.slice(0, 5),
        samples_ms: sorted.slice(0, 50),
      };
      out.textContent = JSON.stringify(summary, null, 2);
    }