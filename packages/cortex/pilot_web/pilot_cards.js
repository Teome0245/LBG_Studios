    const OFFICE_ZONE_META = {
      zone_core: { ico: "⌂", ip: "192.168.0.140", short: "Core" },
      zone_front: { ico: "▣", ip: "192.168.0.100", short: "Front" },
      zone_llm: { ico: "⚡", ip: ".110 / .111", short: "LLM" },
      zone_mmo_lab: { ico: "⚒", ip: "192.168.0.245", short: "Lab" },
      zone_prime: { ico: "◉", ip: "192.168.0.246", short: "Prime" },
      zone_games: { ico: "▶", ip: "personas out-game", short: "Jeux" },
      zone_coffee: { ico: "☕", ip: "pause", short: "Café" },
    };

    function officeEsc(s) {
      return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
        return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
      });
    }

    function cssEscape(s) {
      return String(s == null ? "" : s).replace(/["\\]/g, "\\$&");
    }

    function officeInitials(name) {
      const parts = String(name || "?").trim().split(/\s+/).filter(Boolean);
      if (!parts.length) return "?";
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }

    function officeSetConn(htmlOrText, asHtml) {
      const el = document.getElementById("office-conn-text");
      if (!el) return;
      if (asHtml) el.innerHTML = htmlOrText;
      else el.textContent = htmlOrText;
    }

    function officePlayerIaChipHtml(bot) {
      const online = !!(bot && bot.online);
      const inWorld = !!(bot && bot.in_world);
      const name = (bot && (bot.display_name || bot.id)) || "?";
      const zone = bot && (bot.zone_display || bot.zone) ? String(bot.zone_display || bot.zone) : "";
      const age = bot && bot.age_s != null ? Number(bot.age_s) : null;
      const state = !online ? "offline" : (inWorld ? "online" : "stale");
      const label = !online ? "hors jeu" : (zone || (inWorld ? "en jeu" : "snapshot vieux"));
      const ageTxt = age != null && !Number.isNaN(age) ? (" · " + (age < 10 ? age.toFixed(1) : Math.round(age)) + "s") : "";
      const title = name + " — " + label + ageTxt + " (prime-hub · lecture seule)";
      return (
        '<span class="office-pia-chip office-pia-chip--' + state + '" title="' + officeEsc(title) + '">' +
          '<span class="office-pia-dot" aria-hidden="true"></span>' +
          '<span class="office-pia-name">' + officeEsc(name) + "</span>" +
          '<span class="office-pia-meta">' + officeEsc(label) + "</span>" +
        "</span>"
      );
    }

    function officeBridgeChipHtml(agent) {
      const bot = officeHubBotForBridge(agent);
      const login = (agent && (agent.account_login || agent.persona)) || "";
      const ig = (agent && agent.mmo_player) || "";
      const studio = (agent && agent.linked_studio_display) || "";
      const name = (agent && (agent.display_name || agent.agent_id)) || "?";
      const online = !!(bot && bot.online);
      const zone = bot && (bot.zone_display || bot.zone || bot.play_mode) ? String(bot.zone_display || bot.zone || bot.play_mode) : "";
      const state = online ? "online" : "offline";
      const label = studio
        ? ("↔ " + studio)
        : (online ? (zone || "en hub") : "hors hub");
      const title =
        name +
        (login ? " · " + login : "") +
        (ig ? " → IG " + ig : "") +
        (studio ? " ↔ " + studio : "") +
        " — " + (online ? (zone || "en hub") : "hors hub") +
        " (persona out-game)";
      return (
        '<span class="office-pia-chip office-pia-chip--' + state + ' office-bridge-chip" title="' + officeEsc(title) +
          '" data-office-bridge="' + officeEsc(agent.agent_id || "") + '">' +
          '<span class="office-pia-dot" aria-hidden="true"></span>' +
          '<span class="office-pia-name">' + officeEsc(ig || name) + "</span>" +
          '<span class="office-pia-meta">' + officeEsc(label) + "</span>" +
        "</span>"
      );
    }
