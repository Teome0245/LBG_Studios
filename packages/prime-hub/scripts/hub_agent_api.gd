extends RefCounted
class_name HubAgentApi
## Surface « LLM branche et joue » — LAN only (pas d’ouverture publique).

const _HubPaths = preload("res://scripts/hub_paths.gd")

var skill_md: String = ""
var fleet_meta: Dictionary = {}


func setup() -> void:
	fleet_meta = {}
	skill_md = ""
	var skill_path := _HubPaths.data_file("agent/skill.md")
	if FileAccess.file_exists(skill_path):
		var f := FileAccess.open(skill_path, FileAccess.READ)
		if f != null:
			skill_md = f.get_as_text()
			f.close()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("life/ai_players.json"))
	if typeof(raw) == TYPE_DICTIONARY:
		fleet_meta = {
			"scope": str(raw.get("scope", "lan_only")),
			"max_ai_players": int(raw.get("max_ai_players", 10)),
			"hard_cap": int(raw.get("hard_cap", 20)),
			"roles": raw.get("roles", {}),
			"configured": _count_players(raw, true),
			"ready_disabled": _count_players(raw, false),
		}


func _count_players(raw: Dictionary, want_enabled: bool) -> int:
	var n := 0
	var arr = raw.get("players", [])
	if typeof(arr) != TYPE_ARRAY:
		return 0
	for p in arr:
		if typeof(p) != TYPE_DICTIONARY:
			continue
		if bool(p.get("enabled", false)) == want_enabled:
			n += 1
	return n


func effective_max() -> int:
	var env := OS.get_environment("LBG_MAX_AI_PLAYERS").strip_edges()
	var cap := int(fleet_meta.get("max_ai_players", 10))
	if not env.is_empty():
		cap = int(env)
	var hard := int(fleet_meta.get("hard_cap", 20))
	return clampi(cap, 0, hard)


func skill_payload(format_md: bool = false) -> Dictionary:
	if format_md:
		return {
			"ok": true,
			"format": "markdown",
			"skill": skill_md if not skill_md.is_empty() else "# skill missing",
			"source": "prime_hub",
		}
	return {
		"ok": true,
		"format": "json",
		"title": "Lost Heaven — manuel joueur IA (LAN)",
		"scope": str(fleet_meta.get("scope", "lan_only")),
		"roles": fleet_meta.get("roles", {}),
		"skill_md": skill_md,
		"endpoints": _endpoints(),
		"source": "prime_hub",
	}


func bootstrap(sim) -> Dictionary:
	var used := 0
	if sim != null and sim.has_method("bot_count"):
		used = int(sim.bot_count())
	var mx := effective_max()
	return {
		"ok": true,
		"service": "prime_hub",
		"scope": str(fleet_meta.get("scope", "lan_only")),
		"note": "LAN / Studio only — PNJ tiennent le monde ; joueurs le font évoluer.",
		"roles": fleet_meta.get("roles", {
			"npc": "Tenir le monde fonctionnel.",
			"player": "Faire évoluer le monde.",
		}),
		"seats": {
			"used": used,
			"max": mx,
			"hard_cap": int(fleet_meta.get("hard_cap", 20)),
			"configured_enabled": int(fleet_meta.get("configured", 0)),
			"ready_disabled": int(fleet_meta.get("ready_disabled", 0)),
		},
		"proto": "lbg-ws/2",
		"endpoints": _endpoints(),
		"source": "prime_hub",
	}


func _endpoints() -> Dictionary:
	return {
		"skill": "/v1/agent/skill",
		"bootstrap": "/v1/agent/bootstrap",
		"healthz": "/healthz",
		"catalog": "/v1/catalog?type=skills|recipes|npcs|poi",
		"guide": "/v1/guide?playstyle=…",
		"tick_matrix": "/v1/tick-matrix",
		"quests_board": "/v1/quests/board",
		"quests_status": "/v1/quests/status",
		"inventory": "/v1/inventory?player=…",
		"bots": "/v1/bots",
		"move_to": "POST /v1/bots/move_to",
		"say": "POST /v1/say",
		"world_suggestions": "/v1/dev/world_suggestions",
		"ws": "/ws",
	}
