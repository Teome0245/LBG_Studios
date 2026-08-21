    function pilotApplyRoute() {
      try {
        assistantLbgiaPollStop();
      } catch (_) {}
      try { jobsPollStop(); } catch (_) {}
      const r = pilotParseRoute();
      document.body.dataset.pilotRoute = r;
      const home = document.getElementById("pilot-page-home");
      const work = document.getElementById("pilot-page-work");
      const assistantPage = document.getElementById("pilot-page-assistant");
      const jobsPage = document.getElementById("pilot-page-jobs");
      const teamPage = document.getElementById("pilot-page-team");
      const teamOfficePage = document.getElementById("pilot-page-team-office");
      const teamMetricsPage = document.getElementById("pilot-page-team-metrics");
      const pm = document.getElementById("pilot-page-pm");
      const ly = document.getElementById("pilot-page-lyra");
      const de = document.getElementById("pilot-page-desktop");
      if (home) home.hidden = r !== "home";
      if (work) work.hidden = r !== "chat" && r !== "ops";
      if (assistantPage) assistantPage.hidden = r !== "assistant";
      if (jobsPage) jobsPage.hidden = r !== "jobs";
      if (teamPage) teamPage.hidden = r !== "team";
      if (teamOfficePage) teamOfficePage.hidden = r !== "team_office";
      if (teamMetricsPage) teamMetricsPage.hidden = r !== "team_metrics";
      if (pm) pm.hidden = r !== "pm";
      if (ly) ly.hidden = r !== "lyra";
      if (de) de.hidden = r !== "desktop";
      if (r === "jobs") {
        try { jobsBindPage(); } catch (_) {}
        try { jobsLoadModels(); } catch (_) {}
        try { jobsListRefresh(); } catch (_) {}
        try { jobsPollStart(); } catch (_) {}
      }
      if (r === "team") {
        try { teamBindPage(); } catch (_) {}
        const deepTask = (pilotHashQuery().get("task") || "").trim();
        try {
          teamListRefresh().then(function () {
            if (deepTask) return teamSelect(deepTask, { skipHash: true });
          }).catch(function () {});
        } catch (_) {}
      }
      if (r === "team_metrics") {
        try { teamMetricsBindPage(); } catch (_) {}
      }
      if (r === "team_office") {
        try { officeBindPage(); } catch (_) {}
      } else {
        try { officeStop(); } catch (_) {}
      }
      if (r === "desktop") {
        try { pilotDesktopRefreshConfigHint(); } catch (_) {}
        try { pilotDesktopLoadMmoSummaryFromStorage(); } catch (_) {}
        try { pilotDesktopLoadDryRunToggleFromStorage(); } catch (_) {}
        try { pilotDesktopApplyPipelinePrefsToUi(); } catch (_) {}
        try { pilotDesktopBindPipelinePrefs(); } catch (_) {}
        try { pilotDesktopBindDryRunTogglePersist(); } catch (_) {}
        try { pilotDesktopSetupSpeech(); } catch (_) {}
        try { pilotDesktopApplyHomeLaunchPreset(); } catch (_) {}
      }
      if (r === "assistant") {
        try { assistantBindAssistantPage(); } catch (_) {}
        try { assistantApplyPrefsToUi(); } catch (_) {}
        try { assistantSyncAdvancedPanel(); } catch (_) {}
        try { assistantSessionNotesLoad(); } catch (_) {}
        try { assistantMmoImportSilentLoad(); } catch (_) {}
        try { assistantRenderLyraPanel(); } catch (_) {}
        try { assistantHistoryRender(); } catch (_) {}
        try { assistantRenderSuggestions([]); } catch (_) {}
        try { assistantRenderDocRefs(); } catch (_) {}
        try { assistantRenderSessionState(); } catch (_) {}
        try { assistantCapsRefresh(); } catch (_) {}
        try {
          assistantLbgiaRefresh();
          __assistantLbgiaPoll = window.setInterval(assistantLbgiaRefresh, 2800);
        } catch (_) {}
        try {
          orchestratorAvatarInit();
          faceRigInit();
          assistantOrchMoodRefresh();
          __assistantOrchMoodPoll = window.setInterval(assistantOrchMoodRefresh, 5000);
        } catch (_) {}
      }
      const title = document.getElementById("pilot-work-title");
      const sub = document.getElementById("pilot-work-sub");
      if (title && sub && (r === "chat" || r === "ops")) {
        if (r === "ops") {
          title.textContent = "Ops & santé";
          sub.textContent =
            "Benchmark, cache, monitoring agrégé, capabilities, métriques — même backend que la barre du haut.";
          try {
            const rt = document.getElementById("toggle-right");
            const cr = document.getElementById("col-right");
            if (rt && cr) {
              rt.checked = true;
              cr.style.display = "";
            }
          } catch (_) {}
        } else {
          title.textContent = "Chat & presets";
          sub.textContent =
            "Studio — intention agents (POST /v1/pilot/route). Lab sandbox WS / commits monde : Legacy lab.";
        }
      }
      document.querySelectorAll("#pilot-nav a").forEach(function (a) {
        const route = a.getAttribute("data-nav-route") || "";
        let active = false;
        if (route === "home") active = r === "home";
        else if (route === "team_office") active = r === "team_office";
        else if (route === "team_metrics") active = r === "team_metrics";
        else if (route) active = r === route;
        a.classList.toggle("pilot-nav-active", !!active);
      });
      const groupOf = {
        chat: "studio",
        assistant: "studio",
        jobs: "studio",
        team: "campus",
        team_office: "campus",
        team_metrics: "campus",
        ops: "ops",
        desktop: "ops",
        pm: "projet",
        lyra: "projet",
      };
      const gActive = groupOf[r] || "";
      document.querySelectorAll("#pilot-nav .pilot-nav-group").forEach(function (g) {
        const gid = g.getAttribute("data-nav-group") || "";
        g.classList.toggle("pilot-nav-active", !!gActive && gid === gActive);
      });
    }

    (function pilotNavMenus() {
      const nav = document.getElementById("pilot-nav");
      if (!nav || nav._menusBound) return;
      nav._menusBound = true;
      nav.querySelectorAll(".pilot-nav-group").forEach(function (g) {
        g.addEventListener("toggle", function () {
          if (!g.open) return;
          nav.querySelectorAll(".pilot-nav-group").forEach(function (other) {
            if (other !== g) other.open = false;
          });
        });
      });
      document.addEventListener("click", function (ev) {
        if (nav.contains(ev.target)) return;
        nav.querySelectorAll(".pilot-nav-group").forEach(function (g) { g.open = false; });
      });
    })();

    function escapeHtmlPm(s) {
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;");
    }

