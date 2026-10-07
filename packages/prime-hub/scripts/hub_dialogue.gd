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
	"npc:scribe": "Scribe de la mairie. Dis « chronique » — j'archive ta session. Pas de légendes inventées.",
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
		{"id": "move:perle_eau", "label": "Eau filtrée (8)", "utterance": "Une eau filtrée, prix affiché.", "kind": "ui", "action": {"name": "trade_offer", "sku_id": "drink:eau_filtree", "offer_price": 8}},
		{"id": "move:perle_nego", "label": "Cactus à 22", "utterance": "Le Cactus Noir à 22 Cr ?", "kind": "ui", "action": {"name": "trade_offer", "sku_id": "drink:cactus_noir", "offer_price": 22}},
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
	["ferraille", "Si le board parle de débris de convoi, sors porte est — pile de scrap avant les chacals."],
	["scrap", "Ferraille hors palissade : board Daan quand l'event tourne. Sinon, rien à ramasser."],
	["convoi", "Convoi Zalem — frein lâché. Board des missions si l'offre est encore affichée."],
	["rumeur", "Au marché et à La Perle on en parle — mais le board tranche."],
	["chronique", "Le Scribe à la mairie archive ta session — demande-lui une chronique."],
	["archive", "Archives à la mairie. Le Scribe note les faits, pas les légendes."],
]

var _registry: Dictionary = {}  # id -> entry
var events = null


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


var economy = null


func attach_events(events_svc) -> void:
	events = events_svc


func attach_economy(economy_svc) -> void:
	economy = economy_svc


func _event_rumor() -> String:
	if events == null or not events.has_method("is_active") or not bool(events.is_active()):
		return ""
	if events.has_method("rumor_hint"):
		return str(events.rumor_hint()).strip_edges()
	return ""


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


func _session_memory_line(ss: Dictionary, npc_name: String) -> String:
	## C2 — uniquement des faits utiles (quête, autre PNJ, demande joueur).
	## Pas de « on s'est déjà croisés » ni de recycle de la réplique PNJ.
	var bits: Array = []
	var last := str(ss.get("last_npc", "")).strip_edges()
	var quest := str(ss.get("tracked_quest", "")).strip_edges()
	var note := str(ss.get("player_note", ss.get("memory_hint", ""))).strip_edges()
	var same_npc := not last.is_empty() and last.to_lower() == npc_name.to_lower()
	# Autre PNJ croisé récemment — utile pour orientation sociale.
	if not last.is_empty() and not same_npc:
		bits.append("vient de voir %s" % last)
	# Quête suivie — toujours pertinent.
	if not quest.is_empty():
		var qlabel := quest
		if qlabel.begins_with("lh_"):
			qlabel = qlabel.substr(3).replace("_", " ")
		bits.append("piste « %s »" % qlabel.substr(0, 40))
	# Note = dernière demande JOUEUR (ignorer anciens dumps « Dernier échange : »).
	if not note.is_empty() and not note.to_lower().begins_with("dernier échange"):
		# Même PNJ : ne rappeler la demande que si ce n'est pas un simple salut.
		bits.append("a dit : « %s »" % note.substr(0, 56))
	if bits.is_empty():
		return ""
	return " · ".join(bits)


func _history_for_llm(history: Variant, max_turns: int = 4) -> Array:
	## Derniers tours client → messages Ollama (user/assistant). Cap court (budget 600 ms).
	var out: Array = []
	if typeof(history) != TYPE_ARRAY:
		return out
	var start := maxi(0, history.size() - max_turns)
	for i in range(start, history.size()):
		var turn = history[i]
		if typeof(turn) != TYPE_DICTIONARY:
			continue
		var role := str(turn.get("role", "")).strip_edges().to_lower()
		var content := str(turn.get("content", turn.get("text", ""))).strip_edges()
		if content.is_empty():
			continue
		if content.length() > 160:
			content = content.substr(0, 157) + "…"
		if role in ["assistant", "npc", "bot"]:
			out.append({"role": "assistant", "content": content})
		else:
			out.append({"role": "user", "content": content})
	return out


func _enrich_session_summary(ss: Dictionary, player: String) -> Dictionary:
	## C2 léger : injecte tracked_quest depuis l'économie hub si le client ne l'a pas.
	var out := ss.duplicate(true)
	if str(out.get("tracked_quest", "")).strip_edges() != "":
		return out
	if economy == null or not economy.has_method("status"):
		return out
	var st: Dictionary = economy.status(player)
	var active = st.get("active", [])
	if typeof(active) != TYPE_ARRAY or active.is_empty():
		return out
	var first = active[0]
	if typeof(first) != TYPE_DICTIONARY:
		return out
	var title := str(first.get("title", first.get("id", ""))).strip_edges()
	if not title.is_empty():
		out["tracked_quest"] = title
	return out


func _llm_line(
	npc_name: String,
	role_hint: String,
	player_text: String,
	place: String,
	memory: String = "",
	history: Array = []
) -> String:
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
	if not memory.is_empty():
		system += (
			" Contexte utile (une allusion max, naturelle, jamais recopier mot à mot) : %s."
			% memory.substr(0, 140)
		)
	var messages: Array = [{"role": "system", "content": system}]
	for h in history:
		messages.append(h)
	messages.append({
		"role": "user",
		"content": player_text if not player_text.is_empty() else "bonjour",
	})
	var body := JSON.stringify({
		"model": model,
		"messages": messages,
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
	# Budget court : même process que la sim WS — un LLM bloquant = saccades jeu.
	var deadline := Time.get_ticks_msec() + 600
	while http.get_status() == HTTPClient.STATUS_CONNECTING or http.get_status() == HTTPClient.STATUS_RESOLVING:
		http.poll()
		if Time.get_ticks_msec() > deadline:
			return ""
		OS.delay_usec(500)
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
		OS.delay_usec(500)
	if not http.has_response():
		return ""
	var rb := PackedByteArray()
	while http.get_status() == HTTPClient.STATUS_BODY:
		http.poll()
		var chunk := http.read_response_body_chunk()
		if chunk.size() == 0:
			OS.delay_usec(500)
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


func _scribe_chronicle_line(player: String) -> String:
	if economy == null or not economy.has_method("chronicle"):
		return ""
	var ch: Dictionary = economy.chronicle(player if not player.is_empty() else "Voyageur", true)
	var lines = ch.get("lines", [])
	if typeof(lines) != TYPE_ARRAY or lines.is_empty():
		return ""
	var title := str(ch.get("title", "")).strip_edges()
	var body_bits: PackedStringArray = PackedStringArray()
	var n := mini(4, lines.size())
	for i in range(n):
		body_bits.append(str(lines[i]))
	var more := ""
	if lines.size() > n:
		more = " (+%d lignes — GET /v1/chronicle)" % (lines.size() - n)
	if not title.is_empty():
		return "Scribe — « %s ». %s%s" % [title, " ".join(body_bits), more]
	return "Scribe — %s%s" % [" ".join(body_bits), more]


func _pick_reply(
	npc_id: String,
	npc_name: String,
	player_text: String,
	memory: String = "",
	player: String = "Voyageur",
	history: Array = []
) -> String:
	var t := player_text.strip_edges().to_lower()
	var entry = _registry.get(npc_id, {})
	var role := "habitant hub"
	var place := "Lost Heaven"
	if typeof(entry) == TYPE_DICTIONARY:
		role = str(entry.get("role", entry.get("summary", role)))
		place = str(entry.get("zone", place))
		if npc_name.is_empty():
			npc_name = str(entry.get("name", ""))
	var is_greet := t.is_empty() or t in ["bonjour", "bonjour.", "salut", "hello", "hey"] or t.begins_with("bonjour")
	# C5 — Scribe avant LLM : chronique de session.
	if npc_id == "npc:scribe":
		var wants_ch := (
			is_greet or "chronique" in t or "archive" in t or "session" in t
			or "noter" in t or "écrire" in t or "ecrire" in t or "lire" in t
		)
		if wants_ch:
			var ch_line := _scribe_chronicle_line(player)
			if not ch_line.is_empty():
				return ch_line
	var llm := _llm_line(
		npc_name if not npc_name.is_empty() else "PNJ",
		role.substr(0, 120),
		player_text,
		place,
		memory,
		history
	)
	if not llm.is_empty():
		return llm
	var rumor := _event_rumor()
	var rumor_npcs := [
		"npc:core3_daan_oth", "npc:core3_barman_jax", "npc:rumeuriste", "npc:sergent_rue",
	]
	var wants_rumor := (
		"rumeur" in t or "scrap" in t or "ferraille" in t or "convoi" in t
		or "débris" in t or "debris" in t
	)
	if not rumor.is_empty() and npc_id in rumor_npcs and wants_rumor:
		if npc_id == "npc:core3_daan_oth":
			return "Daan Oth : %s Prends « Débris de convoi » au board tant que ça tient." % rumor
		if npc_id == "npc:sergent_rue":
			return "Sergent : %s Porte est, puis pile de ferraille — ne traîne pas." % rumor
		return "%s : %s" % [npc_name if not npc_name.is_empty() else "PNJ", rumor]
	if is_greet and GREETINGS.has(npc_id):
		var greet := str(GREETINGS[npc_id])
		# Salut : une accroche utile max — jamais de parenthèse « au fait » ni de recycle.
		if "piste" in memory:
			return "%s Pour ta piste en cours : dis-moi ce dont tu as besoin ici." % greet
		if "vient de voir" in memory:
			return "%s Tu tournes sur le hub — je t'écoute." % greet
		if not rumor.is_empty() and npc_id in ["npc:core3_barman_jax", "npc:rumeuriste"]:
			return "%s On dit : %s" % [greet, rumor]
		return greet
	for pair in FALLBACK_REPLIES:
		if str(pair[0]) in t:
			return str(pair[1])
	var who := npc_name if not npc_name.is_empty() else "PNJ"
	if "a dit" in memory:
		return "%s : oui — à ce sujet, dis-moi ce qu'il te faut concrètement." % who
	return "%s : je suis là. Qu'est-ce qu'il te faut à Lost Heaven ?" % who


func invoke(body: Dictionary) -> Dictionary:
	var ctx = body.get("context", {})
	if typeof(ctx) != TYPE_DICTIONARY:
		ctx = {}
	var npc_id := _normalize_npc_id(str(ctx.get("world_npc_id", body.get("world_npc_id", ""))))
	var npc_name := str(ctx.get("npc_name", body.get("npc_name", ""))).strip_edges()
	var player_text := str(body.get("text", "")).strip_edges()
	var player := str(ctx.get("player", body.get("player", "Voyageur"))).strip_edges()
	if player.is_empty():
		player = "Voyageur"
	var ss = ctx.get("session_summary", {})
	if typeof(ss) != TYPE_DICTIONARY:
		ss = {}
	ss = _enrich_session_summary(ss, player)
	var history := _history_for_llm(ctx.get("history", body.get("history", [])))
	if npc_name.is_empty() and _registry.has(npc_id):
		npc_name = str((_registry[npc_id] as Dictionary).get("name", ""))
	if npc_id.is_empty() and not npc_name.is_empty():
		for eid in _registry.keys():
			var ent: Dictionary = _registry[eid]
			if str(ent.get("name", "")).to_lower() == npc_name.to_lower():
				npc_id = str(eid)
				break
	var memory := _session_memory_line(ss, npc_name)
	var reply := _pick_reply(npc_id, npc_name, player_text, memory, player, history)
	var moves := _suggested_moves(npc_id)
	var meta := {
		"lyra_engagement_resolved": "prime_hub",
		"dialogue_profile_resolved": "prime_hub_native",
		"suggested_moves_source": "registry_template" if not moves.is_empty() else "none",
		"world_npc_id": npc_id,
		"npc_name": npc_name,
		"source": "prime_hub",
		"session_memory": memory,
		"session_memory_used": not memory.is_empty(),
		"history_turns": history.size(),
		"tracked_quest": str(ss.get("tracked_quest", "")),
	}
	if npc_id == "npc:scribe" and economy != null and economy.has_method("chronicle"):
		meta["chronicle"] = economy.chronicle(player, true)
	var structured := {
		"reply": reply,
		"suggested_moves": moves,
		"world_npc_id": npc_id,
		"npc_name": npc_name,
		"session_summary": ss,
		"source": "prime_hub",
	}
	return {
		"ok": true,
		"reply": reply,
		"result": reply,
		"suggested_moves": moves,
		"structuredContent": structured,
		"meta": meta,
	}
