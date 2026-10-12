extends RefCounted
class_name HubPresence
## Gestion des dials de présence et résolutions d'ambiances pour les bots IA — Ticket 2.2.

const _HubPaths = preload("res://scripts/hub_paths.gd")

var _presence_dials_pack: Dictionary = {}
var _presence_defaults: Dictionary = {}
var _presence_by_persona: Dictionary = {}
var _presence_templates: Dictionary = {}
var _presence_thresholds: Dictionary = {}


func load_presence_dials() -> void:
	_presence_dials_pack.clear()
	_presence_defaults.clear()
	_presence_by_persona.clear()
	_presence_templates.clear()
	_presence_thresholds.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/presence_dials.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		_presence_defaults = {"chaleur": 0.45, "humeur": 0.4, "humour": 0.3, "initiative": 0.4}
		return
	_presence_dials_pack = raw
	var defs = raw.get("defaults", {})
	if typeof(defs) == TYPE_DICTIONARY:
		_presence_defaults = defs.duplicate(true)
	var by = raw.get("by_persona", {})
	if typeof(by) == TYPE_DICTIONARY:
		_presence_by_persona = by.duplicate(true)
	var tpl = raw.get("ambient_templates", {})
	if typeof(tpl) == TYPE_DICTIONARY:
		_presence_templates = tpl.duplicate(true)
	var th = raw.get("thresholds", {})
	if typeof(th) == TYPE_DICTIONARY:
		_presence_thresholds = th.duplicate(true)


func dials_for_persona(name: String) -> Dictionary:
	if _presence_defaults.is_empty() and _presence_by_persona.is_empty():
		load_presence_dials()
	var key := name.strip_edges()
	var row = _presence_by_persona.get(key, null)
	if typeof(row) != TYPE_DICTIONARY:
		for k in _presence_by_persona.keys():
			if str(k).to_lower() == key.to_lower():
				row = _presence_by_persona[k]
				break
	var out := _presence_defaults.duplicate(true) if not _presence_defaults.is_empty() else {
		"chaleur": 0.45, "humeur": 0.4, "humour": 0.3, "initiative": 0.4
	}
	if typeof(row) == TYPE_DICTIONARY:
		for dk in ["chaleur", "humeur", "humour", "initiative"]:
			if row.has(dk):
				out[dk] = clampf(float(row[dk]), 0.0, 1.0)
	return out


func presence_line_for(bot: Dictionary, who: String) -> String:
	## Une phrase d'ambiance selon dials (B2) — observable sans LLM.
	var dials: Dictionary = bot.get("presence_dials", {})
	if dials.is_empty():
		dials = dials_for_persona(str(bot.get("name", "")))
	var chaleur := float(dials.get("chaleur", 0.45))
	var initiative := float(dials.get("initiative", 0.4))
	var tpl_key := "high_chaleur" if chaleur >= 0.6 else ("low_chaleur" if chaleur <= 0.35 else "")
	if tpl_key.is_empty():
		tpl_key = "high_initiative" if initiative >= 0.6 else ("low_initiative" if initiative <= 0.35 else "")
	if tpl_key.is_empty():
		return ""
	var tpl := str(_presence_templates.get(tpl_key, "")).strip_edges()
	if tpl.is_empty():
		match tpl_key:
			"high_chaleur":
				tpl = "{who} te salue franchement — chaleur haute."
			"low_chaleur":
				tpl = "{who} reste à distance, ton mesuré."
			"high_initiative":
				tpl = "{who} propose déjà le prochain pas."
			_:
				tpl = "{who} attend que tu mènes."
	var nm := str(bot.get("name", "IA"))
	return tpl.replace("{who}", nm if who.is_empty() else who)


func presence_resolve_action(bot: Dictionary, distance_m: float) -> Dictionary:
	## B3 — action autorisée (ignore/ambient/greet/escort/tip_ack) selon dials × distance.
	if _presence_thresholds.is_empty():
		load_presence_dials()
	var dials: Dictionary = bot.get("presence_dials", {})
	if dials.is_empty():
		dials = dials_for_persona(str(bot.get("name", "")))
	var chaleur := float(dials.get("chaleur", 0.45))
	var initiative := float(dials.get("initiative", 0.4))
	var d := maxf(0.0, distance_m)
	var th: Dictionary = _presence_thresholds
	var ign: Dictionary = th.get("ignore", {}) if typeof(th.get("ignore", null)) == TYPE_DICTIONARY else {}
	var esc: Dictionary = th.get("escort", {}) if typeof(th.get("escort", null)) == TYPE_DICTIONARY else {}
	var gre: Dictionary = th.get("greet", {}) if typeof(th.get("greet", null)) == TYPE_DICTIONARY else {}
	var amb: Dictionary = th.get("ambient", {}) if typeof(th.get("ambient", null)) == TYPE_DICTIONARY else {}
	var tip: Dictionary = th.get("tip_ack", {}) if typeof(th.get("tip_ack", null)) == TYPE_DICTIONARY else {}

	var action := "ambient"
	var reason := "default"
	if (
		chaleur <= float(ign.get("max_chaleur", -1.0))
		and initiative <= float(ign.get("max_initiative", -1.0))
		and d <= float(ign.get("max_distance_m", 40.0))
	):
		action = "ignore"
		reason = "low_dials"
	elif (
		chaleur >= float(esc.get("min_chaleur", 0.55))
		and initiative >= float(esc.get("min_initiative", 0.5))
		and d <= float(esc.get("max_distance_m", 24.0))
	):
		action = "escort"
		reason = "high_chaleur_initiative"
	elif (
		chaleur >= float(gre.get("min_chaleur", 0.35))
		and initiative >= float(gre.get("min_initiative", 0.3))
		and d <= float(gre.get("max_distance_m", 32.0))
	):
		action = "greet"
		reason = "greet_ok"
	elif (
		chaleur >= float(tip.get("min_chaleur", 0.4))
		and d <= float(tip.get("max_distance_m", 18.0))
	):
		action = "tip_ack"
		reason = "near_tip"
	elif chaleur >= float(amb.get("min_chaleur", 0.28)) and d <= float(amb.get("max_distance_m", 28.0)):
		action = "ambient"
		reason = "ambient_ok"
	elif d > float(amb.get("max_distance_m", 28.0)):
		action = "ignore"
		reason = "too_far"
	else:
		action = "ignore"
		reason = "below_ambient"

	var dur := 0.0
	if action == "escort":
		dur = float(esc.get("duration_s_high", 28.0)) if chaleur >= 0.7 else float(esc.get("duration_s_base", 14.0))
	return {
		"action": action,
		"reason": reason,
		"distance_m": snappedf(d, 0.1),
		"chaleur": chaleur,
		"initiative": initiative,
		"escort_duration_s": dur,
		"persona": str(bot.get("name", "")),
	}


func presence_dials_payload(bot_defs: Array) -> Dictionary:
	if _presence_defaults.is_empty() and _presence_by_persona.is_empty():
		load_presence_dials()
	var bots: Array = []
	for b in bot_defs:
		var nm := str(b.get("name", ""))
		var dials: Dictionary = b.get("presence_dials", dials_for_persona(nm))
		var row := {
			"name": nm,
			"eid": str(b.get("eid", "")),
			"oid": int(b.get("oid", 0)),
			"presence_dials": dials,
			"presence_line": presence_line_for(b, "Voyageur"),
		}
		row["actions_at_m"] = {
			"12": presence_resolve_action(b, 12.0),
			"20": presence_resolve_action(b, 20.0),
			"35": presence_resolve_action(b, 35.0),
		}
		bots.append(row)
	return {
		"ok": true,
		"schema_version": int(_presence_dials_pack.get("schema_version", 1)),
		"defaults": _presence_defaults,
		"thresholds": _presence_thresholds,
		"bots": bots,
		"count": bots.size(),
		"source": "prime_hub",
		"ticket": "B2+B3",
	}
