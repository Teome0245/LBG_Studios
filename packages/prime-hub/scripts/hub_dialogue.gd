extends RefCounted
class_name HubDialogue
const _HubPaths = preload("res://scripts/hub_paths.gd")

## Dialogue PNJ — stubs + LLM Ollama optionnel (timeout court).

const GREETINGS := {
	"npc:core3_daan_oth": "Daan Oth. Bureau des missions — contrats de survie, chasse, courses. Dis-moi ce que tu cherches.",
	"npc:core3_barman_jax": "Bienvenue à La Perle. Jax au comptoir — un verre, une rumeur, ou juste t'asseoir ?",
	"npc:guide_quartier": "Guide de quartier. Starport à l'ouest, marché au sud, porte est vers le désert. Tu te perds, tu cries.",
	"npc:core3_medic_trainer_c": "Odo Merr — clinique. Kits de terrain, stabilisation. Tu saignes, tu rentres.",
	"npc:core3_scout_trainer_c": "Yara Nis. Prospection et pistes hors remparts. Le désert ne pardonne pas.",
	"npc:core3_artisan_trainer_c": "Kell Asa. Atelier — outils, kits, pièces. Rien de neuf ici, tout se récupère.",
	"npc:core3_talen_ress": "Talen Ress. Formation scène à l'auberge — danse, musique, moral. Pas Kisreudi.",
	"npc:scribe": "Scribe de la mairie. Chroniques de session, pas de légendes inventées. Tu notes ?",
	"npc:habitue_cantina": "Toujours la même table à La Perle. Qu'est-ce que tu bois ?",
	"npc:videur": "Pas de bagarre devant La Perle. Jax s'occupe du verre, moi de la porte.",
	"npc:sergent_rue": "Sergent de rue. Porte est sous surveillance — meute ou pas.",
	"npc:rumeuriste": "Au marché on entend tout. Tu veux une rumeur… ou un prix ?",
}

const DEFAULT_MOVES := {
	"npc:core3_daan_oth": [
		{"id": "move:daan_offres", "label": "Voir les offres", "utterance": "Quelles missions as-tu ?", "kind": "ui", "action": {"name": "open_mission_board"}},
		{"id": "move:daan_desert", "label": "Survivre au désert", "utterance": "Un conseil pour tenir hors des murs ?", "kind": "info"},
	],
	"npc:core3_barman_jax": [
		{"id": "move:perle_boisson", "label": "Une boisson", "utterance": "Un verre, Jax — qu'est-ce que tu sers ce soir ?", "kind": "social"},
		{"id": "move:perle_show", "label": "Spectacle ce soir", "utterance": "Il y a un spectacle à La Perle ce soir ?", "kind": "info"},
	],
	"npc:guide_quartier": [
		{"id": "move:guide_map", "label": "Orientation", "utterance": "Où est le marché ?", "kind": "info"},
	],
}

const FALLBACK_REPLIES := [
	["mission", "Le board a des offres près du bureau. Daan Oth te dira lesquelles tiennent."],
	["désert", "Hors murs : eau, ombre, et ne reste pas seul après le crépuscule."],
	["desert", "Hors murs : eau, ombre, et ne reste pas seul après le crépuscule."],
	["boisson", "À La Perle, Jax sert ce qu'on a — chaud, amer, honnête."],
	["verre", "Un verre ? Jax te fixe ça au comptoir de La Perle."],
	["spectacle", "La scène, c'est Talen Ress et l'artiste de La Perle — pas le scientifique."],
	["craft", "Kell Asa à l'atelier : combine ce que tu ramasses."],
	["soin", "Clinique, Odo Merr. Pas de miracle — des kits."],
	["porte", "Porte est = désert. Porte ouest = Zalem. Les remparts tiennent… pour l'instant."],
]

var _registry: Dictionary = {}  # id -> entry


func setup() -> void:
	_registry.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("npc_registry.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var npcs = raw.get("npcs", [])
	if typeof(npcs) != TYPE_ARRAY:
		return
	for n in npcs:
		if typeof(n) == TYPE_DICTIONARY and str(n.get("id", "")) != "":
			_registry[str(n["id"])] = n


func _normalize_npc_id(raw: String) -> String:
	var s := raw.strip_edges()
	while s.begins_with("npc:npc:"):
		s = "npc:" + s.substr(8)
	if s.begins_with("core3_") and not s.begins_with("npc:"):
		s = "npc:" + s
	return s


func _suggested_moves(npc_id: String) -> Array:
	var out: Array = []
	var entry = _registry.get(npc_id, {})
	if typeof(entry) == TYPE_DICTIONARY:
		var raw = entry.get("suggestion_templates", [])
		if typeof(raw) == TYPE_ARRAY:
			for item in raw:
				if typeof(item) != TYPE_DICTIONARY:
					continue
				var mid := str(item.get("id", "")).strip_edges()
				var label := str(item.get("label", "")).strip_edges()
				if mid.is_empty() or label.is_empty():
					continue
				var move := {
					"id": mid,
					"label": label.substr(0, mini(28, label.length())),
					"utterance": str(item.get("utterance", label)).strip_edges().substr(0, 160),
				}
				var kind := str(item.get("kind", "")).strip_edges()
				if not kind.is_empty():
					move["kind"] = kind
				if typeof(item.get("action", null)) == TYPE_DICTIONARY:
					move["action"] = item["action"]
				out.append(move)
				if out.size() >= 3:
					break
	if not out.is_empty():
		return out
	var fb = DEFAULT_MOVES.get(npc_id, [])
	if typeof(fb) == TYPE_ARRAY:
		for item in fb:
			out.append((item as Dictionary).duplicate(true))
			if out.size() >= 3:
				break
	return out


func _llm_line(npc_name: String, role_hint: String, player_text: String, place: String) -> String:
	var disabled := OS.get_environment("LBG_HUB_LLM_DISABLED").strip_edges().to_lower()
	if disabled in ["1", "true", "yes"]:
		return ""
	var base := OS.get_environment("LBG_HUB_LLM_BASE_URL").strip_edges()
	if base.is_empty():
		base = OS.get_environment("LBG_DIALOGUE_LLM_BASE_URL").strip_edges()
	if base.is_empty():
		base = "http://192.168.0.110:11434"
	base = base.rstrip("/")
	if base.ends_with("/v1"):
		base = base.substr(0, base.length() - 3)
	var model := OS.get_environment("LBG_HUB_LLM_MODEL").strip_edges()
	if model.is_empty():
		model = OS.get_environment("LBG_DIALOGUE_LLM_MODEL").strip_edges()
	if model.is_empty():
		model = "huihui_ai/gemma-4-abliterated:e2b"
	var system := (
		"Tu es %s, %s à %s (Lost Heaven). Réponds en français, 1 phrase courte, ton PNJ, pas de markdown."
		% [npc_name, role_hint, place]
	)
	var body := JSON.stringify({
		"model": model,
		"messages": [
			{"role": "system", "content": system},
			{"role": "user", "content": player_text if not player_text.is_empty() else "bonjour"},
		],
		"stream": false,
		"think": false,
		"options": {"num_predict": 80, "temperature": 0.7},
	})
	var http := HTTPClient.new()
	var host := base.replace("http://", "").replace("https://", "").split("/")[0]
	var port := 80
	if ":" in host:
		var hp := host.split(":")
		host = hp[0]
		port = int(hp[1])
	elif base.begins_with("https://"):
		port = 443
	else:
		port = 11434 if port == 80 else port
	if http.connect_to_host(host, port) != OK:
		return ""
	var deadline := Time.get_ticks_msec() + 2500
	while http.get_status() == HTTPClient.STATUS_CONNECTING or http.get_status() == HTTPClient.STATUS_RESOLVING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			return ""
		OS.delay_usec(2000)
	if http.get_status() != HTTPClient.STATUS_CONNECTED:
		return ""
	var err := http.request(
		HTTPClient.METHOD_POST,
		"/api/chat",
		PackedStringArray(["Content-Type: application/json"]),
		body
	)
	if err != OK:
		return ""
	while http.get_status() == HTTPClient.STATUS_REQUESTING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			return ""
		OS.delay_usec(2000)
	if not http.has_response():
		return ""
	var rb := PackedByteArray()
	while http.get_status() == HTTPClient.STATUS_BODY:
		http.poll()
		var chunk := http.read_response_body_chunk()
		if chunk.size() == 0:
			OS.delay_usec(2000)
		else:
			rb.append_array(chunk)
		if Time.get_ticks_msec() > deadline:
			break
	var parsed: Variant = JSON.parse_string(rb.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return ""
	var msg = parsed.get("message", {})
	var text := ""
	if typeof(msg) == TYPE_DICTIONARY:
		text = str(msg.get("content", "")).strip_edges()
	if text.is_empty():
		return ""
	text = text.replace("\n", " ").strip_edges()
	if text.length() > 200:
		text = text.substr(0, 197) + "…"
	return text


func _pick_reply(npc_id: String, npc_name: String, player_text: String) -> String:
	var t := player_text.strip_edges().to_lower()
	var entry = _registry.get(npc_id, {})
	var role := "habitant hub"
	var place := "Lost Heaven"
	if typeof(entry) == TYPE_DICTIONARY:
		role = str(entry.get("role", entry.get("summary", role)))
		place = str(entry.get("zone", place))
		if npc_name.is_empty():
			npc_name = str(entry.get("name", ""))
	var llm := _llm_line(npc_name if not npc_name.is_empty() else "PNJ", role.substr(0, 120), player_text, place)
	if not llm.is_empty():
		return llm
	var is_greet := t.is_empty() or t in ["bonjour", "bonjour.", "salut", "hello", "hey"] or t.begins_with("bonjour")
	if is_greet and GREETINGS.has(npc_id):
		return str(GREETINGS[npc_id])
	for pair in FALLBACK_REPLIES:
		if str(pair[0]) in t:
			return str(pair[1])
	var who := npc_name if not npc_name.is_empty() else "PNJ"
	return "%s : je suis là. Qu'est-ce qu'il te faut à Lost Heaven ?" % who


func invoke(body: Dictionary) -> Dictionary:
	var ctx = body.get("context", {})
	if typeof(ctx) != TYPE_DICTIONARY:
		ctx = {}
	var npc_id := _normalize_npc_id(str(ctx.get("world_npc_id", body.get("world_npc_id", ""))))
	var npc_name := str(ctx.get("npc_name", body.get("npc_name", ""))).strip_edges()
	var player_text := str(body.get("text", "")).strip_edges()
	if npc_name.is_empty() and _registry.has(npc_id):
		npc_name = str((_registry[npc_id] as Dictionary).get("name", ""))
	if npc_id.is_empty() and not npc_name.is_empty():
		for eid in _registry.keys():
			var ent: Dictionary = _registry[eid]
			if str(ent.get("name", "")).to_lower() == npc_name.to_lower():
				npc_id = str(eid)
				break
	var reply := _pick_reply(npc_id, npc_name, player_text)
	var moves := _suggested_moves(npc_id)
	return {
		"ok": true,
		"reply": reply,
		"suggested_moves": moves,
		"meta": {
			"lyra_engagement_resolved": "prime_hub",
			"dialogue_profile_resolved": "prime_hub_native",
			"suggested_moves_source": "registry_template" if not moves.is_empty() else "none",
			"world_npc_id": npc_id,
			"npc_name": npc_name,
			"source": "prime_hub",
		},
	}
