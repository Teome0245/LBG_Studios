extends RefCounted
class_name HubEconomy
const _HubPaths = preload("res://scripts/hub_paths.gd")
const HubDbScript = preload("res://scripts/hub_db.gd")

## Inventaire / board / quêtes / craft — contrats peel C10/C11.
## Ticket 2.1 : état joueur (inventaire, quêtes, chronique session_log)
## persisté en SQLite transactionnel (table player_state), export JSON conservé.

const DEFAULT_INV := [
	{"id": "scrap_metal", "name": "Ferraille", "qty": 4, "icon": "copper"},
	{"id": "binding_tape", "name": "Ruban de liaison", "qty": 2, "icon": "screw"},
	{"id": "dried_grain", "name": "Grain séché", "qty": 4, "icon": "ration"},
	{"id": "water_capsule", "name": "Capsule d'eau", "qty": 2, "icon": "kit"},
]
const DEFAULT_SKILLS := [
	"prospecteur_r1", "artisan_rue_r1", "medecine_camp_r1", "pilotage_shuttle_r1",
]

var _templates: Array = []
var _by_id: Dictionary = {}
var _players: Dictionary = {}
var _path: String = ""
var db: HubDbScript = null
var events = null
var _salvage_cfg: Dictionary = {}
var _salvage_cd: Dictionary = {}  # player -> unix until
var _rng := RandomNumberGenerator.new()
var _recipes_by_id: Dictionary = {}
var _chronicle_cfg: Dictionary = {}
var _vendor_jax: Dictionary = {}


func setup() -> void:
	_path = _HubPaths.data_file("players_state.json")
	_rng.randomize()
	db = HubDbScript.get_shared()
	reload_templates()
	_load_players()
	_load_salvage()
	_load_recipes()
	_load_chronicle()
	_load_vendor_jax()


func attach_events(events_svc) -> void:
	events = events_svc


func _load_salvage() -> void:
	_salvage_cfg.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("salvage_lh_scrap_pile.json"))
	if typeof(raw) == TYPE_DICTIONARY:
		_salvage_cfg = raw


func _load_recipes() -> void:
	_recipes_by_id.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("catalog_recipes.json"))
	if typeof(raw) == TYPE_DICTIONARY:
		var items = raw.get("items", [])
		if typeof(items) == TYPE_ARRAY:
			for it in items:
				if typeof(it) == TYPE_DICTIONARY and str(it.get("id", "")) != "":
					_recipes_by_id[str(it["id"])] = it
	var scrap_raw: Variant = _HubPaths.read_json(_HubPaths.data_file("craft/schematics_scrap.json"))
	if typeof(scrap_raw) == TYPE_DICTIONARY:
		var schematics = scrap_raw.get("schematics", [])
		if typeof(schematics) == TYPE_ARRAY:
			for sc in schematics:
				if typeof(sc) == TYPE_DICTIONARY and str(sc.get("id", "")) != "":
					_recipes_by_id[str(sc["id"])] = sc


func _load_chronicle() -> void:
	_chronicle_cfg.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("chronicle_scribe.json"))
	if typeof(raw) == TYPE_DICTIONARY:
		_chronicle_cfg = raw


func _load_vendor_jax() -> void:
	_vendor_jax.clear()
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("vendor_negotiation_jax.json"))
	if typeof(raw) == TYPE_DICTIONARY:
		_vendor_jax = raw


func _ensure_session_log(p: Dictionary) -> Array:
	if typeof(p.get("session_log")) != TYPE_ARRAY:
		p["session_log"] = []
	return p["session_log"]


func log_session_event(player: String, kind: String, text: String, meta: Dictionary = {}) -> void:
	## C5 — faits utiles pour la chronique Scribe (pas de fluff).
	var p := _player(player)
	var log := _ensure_session_log(p)
	var line := text.strip_edges()
	if line.is_empty():
		return
	if line.length() > 160:
		line = line.substr(0, 157) + "…"
	log.append({
		"t": int(Time.get_unix_time_from_system()),
		"kind": kind.strip_edges(),
		"text": line,
		"meta": meta.duplicate(true) if typeof(meta) == TYPE_DICTIONARY else {},
	})
	while log.size() > 24:
		log.remove_at(0)
	p["session_log"] = log
	_save_players()


func chronicle(player: String, cosmetic_title: bool = true) -> Dictionary:
	## Export 5–10 lignes + titre optionnel (C5).
	if _chronicle_cfg.is_empty():
		_load_chronicle()
	var key := player.strip_edges()
	if key.is_empty():
		key = "Voyageur"
	var p := _player(key)
	var log := _ensure_session_log(p)
	var lines: Array = []
	var open = _chronicle_cfg.get("frame_open", [])
	if typeof(open) == TYPE_ARRAY:
		for o in open:
			lines.append(str(o))
	# Faits session (plus récents en dernier dans le corps).
	var facts: Array = []
	for e in log:
		if typeof(e) != TYPE_DICTIONARY:
			continue
		var tx := str(e.get("text", "")).strip_edges()
		if not tx.is_empty():
			facts.append(tx)
	# Garder les 6 derniers faits max.
	if facts.size() > 6:
		facts = facts.slice(facts.size() - 6, facts.size())
	for f in facts:
		lines.append(f)
	if facts.is_empty():
		lines.append("%s a foulé Lost Heaven — encore peu de faits à graver." % key)
		lines.append("Daan Oth tient le board ; Jax la Perle ; le désert attend hors porte est.")
	var close = _chronicle_cfg.get("frame_close", [])
	if typeof(close) == TYPE_ARRAY and not close.is_empty():
		lines.append(str(close[0]))
	var mn := int(_chronicle_cfg.get("line_count_min", 5))
	var mx := int(_chronicle_cfg.get("line_count_max", 10))
	while lines.size() < mn:
		lines.append("Le hub respire — shuttleport, marché, remparts.")
	if lines.size() > mx:
		lines = lines.slice(0, mx)
	var title := ""
	if cosmetic_title:
		var tmpl := str(_chronicle_cfg.get("title_template", "Chronique du voyageur — {player_name}"))
		title = tmpl.replace("{player_name}", key)
	return {
		"ok": true,
		"player": key,
		"title": title,
		"lines": lines,
		"line_count": lines.size(),
		"events_used": facts.size(),
		"scribe_npc_id": str(_chronicle_cfg.get("scribe_npc_id", "npc:scribe")),
		"source": "prime_hub",
		"ticket": "C5",
	}


func reload_templates() -> void:
	_templates.clear()
	_by_id.clear()
	var qpath := OS.get_environment("LBG_HUB_QUESTS_JSON").strip_edges()
	if qpath.is_empty():
		qpath = _HubPaths.data_file("quests_lbg_templates.json")
	var raw: Variant = _HubPaths.read_json(qpath)
	if typeof(raw) == TYPE_DICTIONARY:
		var arr = raw.get("templates", [])
		if typeof(arr) == TYPE_ARRAY:
			for t in arr:
				if typeof(t) == TYPE_DICTIONARY and str(t.get("id", "")) != "":
					_templates.append(t)
					_by_id[str(t["id"])] = t
	if _templates.is_empty():
		var fb := {
			"id": "lh_survey_dunes",
			"title": "Relevé hors palissade",
			"template": "survey",
			"objective": "Sortir porte est et revenir.",
			"progress": [{"id": "exit", "label": "Sortir vers la porte est", "poi": "poi:lost_heaven_gate", "radius_m": 70}],
			"rewards": {"credits": 25, "items": [{"id": "scrap_metal", "qty": 2}]},
			"giver_ids": ["npc:core3_daan_oth"],
			"default_giver": "Daan Oth",
			"next_steps": ["Sortir porte est", "Revenir"],
		}
		_templates.append(fb)
		_by_id[str(fb["id"])] = fb


func _load_players() -> void:
	_players.clear()
	if db != null and db.available:
		var rows := db.query_rows("SELECT player,data FROM player_state;")
		if rows.size() > 0:
			for r in rows:
				var blob: Variant = JSON.parse_string(str(r.get("data", "")))
				if typeof(blob) == TYPE_DICTIONARY:
					_players[str(r.get("player", ""))] = blob
			return
		# Table vide → migration depuis le JSON legacy si présent.
		if _read_legacy_players():
			_save_players()
		return
	_read_legacy_players()


func _read_legacy_players() -> bool:
	_players.clear()
	var raw: Variant = _HubPaths.read_json(_path)
	if typeof(raw) != TYPE_DICTIONARY:
		return false
	var players = raw.get("players", {})
	if typeof(players) == TYPE_DICTIONARY:
		for k in players.keys():
			var v = players[k]
			if typeof(v) == TYPE_DICTIONARY:
				_players[str(k)] = v
	return _players.size() > 0


func _save_players() -> void:
	if db != null and db.available:
		_save_players_db()
		return
	_write_players_json()


func _save_players_db() -> void:
	var stmts: Array = []
	var now := int(Time.get_unix_time_from_system())
	for key in _players.keys():
		var row: Dictionary = _players[key]
		stmts.append(
			"INSERT INTO player_state(player,data,updated_at) VALUES('%s','%s',%d) "
			% [
				HubDbScript.escape_sql(str(key)),
				HubDbScript.json_literal(row),
				now,
			]
			+ "ON CONFLICT(player) DO UPDATE SET data=excluded.data,updated_at=excluded.updated_at;"
		)
	db.enqueue(stmts)
	_write_players_json()


func _write_players_json() -> void:
	_HubPaths.write_json(_path, {
		"schema_version": 2,
		"backend": "sqlite" if (db != null and db.available) else "json",
		"players": _players,
		"saved_at": int(Time.get_unix_time_from_system()),
	})


func _player(name: String) -> Dictionary:
	var key := name.strip_edges()
	if key.is_empty():
		key = "Voyageur"
	if not _players.has(key):
		_players[key] = {
			"inventory": DEFAULT_INV.duplicate(true),
			"skills": DEFAULT_SKILLS.duplicate(),
			"credits": 50,
			"active": [],
			"completed": [],
			"session_log": [],
			"relation_memory": [],
		}
	var p: Dictionary = _players[key]
	if typeof(p.get("session_log")) != TYPE_ARRAY:
		p["session_log"] = []
	if typeof(p.get("relation_memory")) != TYPE_ARRAY:
		p["relation_memory"] = []
	return p


func inventory(player: String) -> Dictionary:
	var p := _player(player)
	return {
		"ok": true,
		"player": player if not player.strip_edges().is_empty() else "Voyageur",
		"skills": (p["skills"] as Array).duplicate(),
		"inventory": (p["inventory"] as Array).duplicate(true),
		"source": "prime_hub",
		"core3_live": false,
		"persisted": FileAccess.file_exists(_path),
	}


func _event_allows(t: Dictionary) -> bool:
	var gate := str(t.get("event_gated", "")).strip_edges()
	if gate.is_empty():
		return true
	if events == null or not events.has_method("is_active"):
		return false
	return bool(events.is_active(gate))


func board(giver: String, player: String) -> Dictionary:
	var quests: Array = []
	for t in _templates:
		if not _event_allows(t):
			continue
		var row := {
			"id": t["id"],
			"title": t.get("title", t["id"]),
			"template": t.get("template", ""),
			"objective": t.get("objective", ""),
			"next_steps": (t.get("next_steps", []) as Array).duplicate(),
			"progress": (t.get("progress", []) as Array).duplicate(true),
			"rewards": (t.get("rewards", {}) as Dictionary).duplicate(true),
			"default_giver": t.get("default_giver", ""),
			"giver_ids": (t.get("giver_ids", []) as Array).duplicate(),
			"generated": false,
		}
		var gate := str(t.get("event_gated", "")).strip_edges()
		if not gate.is_empty():
			row["event_id"] = gate
			row["event_offer"] = true
		quests.append(row)
	var ev_snap := {}
	if events != null and events.has_method("snapshot"):
		ev_snap = events.snapshot()
	return {
		"ok": true,
		"hub": "lost_heaven",
		"giver_id": giver if not giver.is_empty() else "npc:core3_daan_oth",
		"player": player if not player.is_empty() else "Voyageur",
		"quests": quests,
		"active_event": ev_snap,
		"source": "prime_hub",
	}


func _normalize_active_entry(a: Dictionary) -> Dictionary:
	## Client attend progress_steps[].done (alias de progress + steps_done).
	var out: Dictionary = a.duplicate(true)
	var done: Array = out.get("steps_done", [])
	if typeof(done) != TYPE_ARRAY:
		done = []
	var steps = out.get("progress", [])
	if typeof(steps) != TYPE_ARRAY:
		steps = []
	var ps: Array = []
	var label_for := ""
	for s in steps:
		if typeof(s) != TYPE_DICTIONARY:
			continue
		var step: Dictionary = (s as Dictionary).duplicate(true)
		var sid := str(step.get("id", ""))
		var is_done := sid != "" and sid in done
		step["done"] = is_done
		ps.append(step)
		if label_for.is_empty() and not is_done:
			label_for = str(step.get("label", sid))
	out["progress_steps"] = ps
	out["progress"] = steps.duplicate(true)
	out["steps_done"] = done.duplicate()
	if not label_for.is_empty():
		out["next_label"] = label_for
	return out


func _normalized_active(player_active: Array) -> Array:
	var out: Array = []
	for a in player_active:
		if typeof(a) == TYPE_DICTIONARY:
			out.append(_normalize_active_entry(a))
	return out


func status(player: String) -> Dictionary:
	var p := _player(player)
	return {
		"ok": true,
		"player": player if not player.is_empty() else "Voyageur",
		"credits": int(p["credits"]),
		"active": _normalized_active(p["active"] as Array),
		"completed": (p["completed"] as Array).duplicate(),
		"generated_offers": [],
		"generated_by_id": {},
		"board_rotation": 0,
		"source": "prime_hub",
		"persisted": FileAccess.file_exists(_path),
	}


func accept(player: String, quest_id: String, giver_id: String = "") -> Dictionary:
	var p := _player(player)
	var qid := quest_id.strip_edges()
	if not _by_id.has(qid):
		return {"ok": false, "error": "unknown_quest", "quest_id": qid}
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == qid:
			var already := _normalize_active_entry(a)
			return {
				"ok": true,
				"already": true,
				"quest_id": qid,
				"accepted": already,
				"active": _normalized_active(p["active"] as Array),
			}
	if qid in (p["completed"] as Array):
		return {"ok": false, "error": "already_completed", "quest_id": qid}
	var tmpl: Dictionary = _by_id[qid]
	var entry := {
		"id": qid,
		"title": tmpl.get("title", qid),
		"giver_id": giver_id if not giver_id.is_empty() else "npc:core3_daan_oth",
		"steps_done": [],
		"progress": (tmpl.get("progress", []) as Array).duplicate(true),
	}
	(p["active"] as Array).append(entry)
	var giver := str(entry.get("giver_id", "npc:core3_daan_oth"))
	var qtitle := str(tmpl.get("title", qid))
	remember_relation(
		player,
		giver,
		"quest",
		"%s t'a confié « %s »." % [_npc_short(giver), qtitle.substr(0, 48)],
		{"quest_id": qid, "value": qid}
	)
	_save_players()
	var accepted := _normalize_active_entry(entry)
	log_session_event(player, "quest_accept", "Mission prise : %s." % qtitle, {"quest_id": qid})
	return {
		"ok": true,
		"quest_id": qid,
		"accepted": accepted,
		"active": _normalized_active(p["active"] as Array),
		"source": "prime_hub",
	}


func _ordered_step_ids(progress_arr: Array) -> Array:
	var ids: Array = []
	for s in progress_arr:
		if typeof(s) == TYPE_DICTIONARY and str(s.get("id", "")) != "":
			ids.append(str(s["id"]))
	return ids


func _backfill_prior_steps(done: Array, ordered: Array, reached_id: String) -> Array:
	## Si le joueur valide une étape tardive (ex. meute), les étapes précédentes
	## (porte) sont considérées faites — il a forcément passé le POI.
	var out: Array = done.duplicate()
	var idx := ordered.find(reached_id)
	if idx < 0:
		if reached_id != "" and reached_id not in out:
			out.append(reached_id)
		return out
	for i in range(idx + 1):
		var sid := str(ordered[i])
		if sid not in out:
			out.append(sid)
	return out


func progress(player: String, quest_id: String, step_id: String, hunt_victory: bool = false) -> Dictionary:
	var p := _player(player)
	var qid := quest_id.strip_edges()
	var sid := step_id.strip_edges()
	# P5a — étape meute exige une victoire cour de chasse (sauf claim-quest).
	if qid == "lh_hunt_chacal" and sid == "meute" and not hunt_victory:
		return {
			"ok": false,
			"error": "hunt_required",
			"quest_id": qid,
			"step_id": sid,
			"hint": "Victoire cour de chasse requise — POST /v1/hunt-yard/claim-quest après combat",
			"source": "prime_hub",
		}
	for a in p["active"]:
		if typeof(a) != TYPE_DICTIONARY or str(a.get("id", "")) != qid:
			continue
		var ordered := _ordered_step_ids(a.get("progress", []) as Array)
		var done: Array = _backfill_prior_steps(a.get("steps_done", []) as Array, ordered, sid)
		a["steps_done"] = done
		_save_players()
		var norm := _normalize_active_entry(a)
		var step_label := sid
		for s in norm.get("progress_steps", []):
			if typeof(s) == TYPE_DICTIONARY and str(s.get("id", "")) == sid:
				step_label = str(s.get("label", sid))
				break
		var ready := true
		for n in ordered:
			if n not in done:
				ready = false
				break
		return {
			"ok": true,
			"quest_id": qid,
			"step_id": sid,
			"label": step_label,
			"steps_done": done.duplicate(),
			"ready_to_turn_in": ready,
			"active": _normalized_active(p["active"] as Array),
			"source": "prime_hub",
		}
	return {"ok": false, "error": "not_active", "quest_id": qid}


func claim_hunt_quest(player: String, quest_id: String = "lh_hunt_chacal", hunt_yard = null) -> Dictionary:
	## Valide l'étape « meute » après victoire hunt_yard.
	if hunt_yard == null or not hunt_yard.has_method("snapshot"):
		return {"ok": false, "error": "hunt_yard_unavailable", "source": "prime_hub"}
	var snap: Dictionary = hunt_yard.snapshot()
	if str(snap.get("status", "")) != "victory":
		return {
			"ok": false,
			"error": "hunt_ongoing",
			"hunt_status": snap.get("status"),
			"tick": snap.get("tick"),
			"kills": snap.get("kills"),
			"heals": snap.get("heals"),
			"hint": "Termine la cour de chasse (tick/run) avant de réclamer l'étape",
			"source": "prime_hub",
		}
	# Accepte la quête si absente (bots / smoke).
	var st := status(player)
	var active = st.get("active", [])
	var has := false
	if typeof(active) == TYPE_ARRAY:
		for a in active:
			if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == quest_id:
				has = true
				break
	if not has:
		var acc := accept(player, quest_id, "npc:core3_daan_oth")
		if not bool(acc.get("ok")):
			return acc
	var result := progress(player, quest_id, "meute", true)
	if bool(result.get("ok")):
		result["hunt"] = {
			"status": snap.get("status"),
			"tick": snap.get("tick"),
			"kills": snap.get("kills"),
			"heals": snap.get("heals"),
		}
	return result


func complete(player: String, quest_id: String) -> Dictionary:
	var p := _player(player)
	var qid := quest_id.strip_edges()
	if not _by_id.has(qid):
		return {"ok": false, "error": "unknown_quest"}
	var tmpl: Dictionary = _by_id[qid]
	var found = null
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == qid:
			found = a
			break
	if found == null:
		return {"ok": false, "error": "not_active"}
	var needed := _ordered_step_ids(tmpl.get("progress", []) as Array)
	var done: Array = found.get("steps_done", [])
	# Backfill : si une étape tardive est faite, les antérieures aussi.
	var furthest := -1
	for i in range(needed.size()):
		if str(needed[i]) in done:
			furthest = i
	if furthest >= 0:
		done = _backfill_prior_steps(done, needed, str(needed[furthest]))
		found["steps_done"] = done
	for n in needed:
		if n not in done:
			return {
				"ok": false,
				"error": "incomplete",
				"hint": "objectifs incomplets — approche les POI (porte / meute / bureau)",
				"needed": needed,
				"steps_done": done.duplicate(),
			}
	var active: Array = []
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) != qid:
			active.append(a)
	p["active"] = active
	if qid not in (p["completed"] as Array):
		(p["completed"] as Array).append(qid)
	var rewards: Dictionary = tmpl.get("rewards", {})
	var credits := int(rewards.get("credits", 0))
	p["credits"] = int(p["credits"]) + credits
	var granted: Array = []
	for it in rewards.get("items", []):
		if typeof(it) != TYPE_DICTIONARY:
			continue
		var iid := str(it.get("id", ""))
		var qty := int(it.get("qty", 1))
		if iid.is_empty():
			continue
		_add_item(p, iid, qty, str(it.get("name", iid)))
		granted.append({"id": iid, "qty": qty})
	_save_players()
	var qtitle := str(tmpl.get("title", qid))
	log_session_event(player, "quest_complete", "Mission achevée : %s (+%d Cr)." % [qtitle, credits], {"quest_id": qid})
	return {
		"ok": true,
		"quest_id": qid,
		"title": qtitle,
		"credits": int(p["credits"]),
		"credits_gained": credits,
		"reward_applied": {"credits_gained": credits, "items": granted},
		"items": granted,
		"inventory": (p["inventory"] as Array).duplicate(true),
		"active": _normalized_active(p["active"] as Array),
		"completed": (p["completed"] as Array).duplicate(),
		"chronicle": chronicle(player),
		"source": "prime_hub",
	}


func abandon(player: String, quest_id: String, reason: String = "") -> Dictionary:
	## Retire une quête active sans reward (ex. escorte séparée).
	var p := _player(player)
	var qid := quest_id.strip_edges()
	var found := false
	var active: Array = []
	for a in p["active"]:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == qid:
			found = true
			continue
		active.append(a)
	if not found:
		return {"ok": false, "error": "not_active", "quest_id": qid}
	p["active"] = active
	_save_players()
	var why := reason.strip_edges()
	var msg := "Mission abandonnée : %s." % qid
	if why != "":
		msg = "Mission abandonnée (%s) : %s." % [why, qid]
	log_session_event(player, "quest_abandon", msg, {"quest_id": qid, "reason": why})
	return {
		"ok": true,
		"quest_id": qid,
		"reason": why,
		"active": _normalized_active(p["active"] as Array),
		"source": "prime_hub",
	}


func tip(player: String, quest_id: String, amount: int = 2) -> Dictionary:
	var p := _player(player)
	var amt := maxi(0, amount)
	if int(p["credits"]) < amt:
		return {"ok": false, "error": "insufficient_credits", "credits": int(p["credits"])}
	p["credits"] = int(p["credits"]) - amt
	remember_relation(
		player,
		"npc:core3_artiste_scene",
		"gift",
		"Tu as tippé %d Cr pour la scène à La Perle." % amt,
		{"value": amt, "quest_id": quest_id}
	)
	# Jax voit passer le geste (comptoir).
	remember_relation(
		player,
		"npc:core3_barman_jax",
		"gift",
		"Pourboire scène noté au comptoir (%d Cr)." % amt,
		{"value": amt, "quest_id": quest_id}
	)
	_save_players()
	log_session_event(player, "tip_stage", "Tip scène à La Perle — %d Cr." % amt, {"quest_id": quest_id})
	return {
		"ok": true,
		"quest_id": quest_id,
		"amount": amt,
		"tipped": amt,
		"credits": int(p["credits"]),
		"message": "Scène",
		"chronicle": chronicle(player),
		"source": "prime_hub",
	}


const CONSUMABLE_IDS := ["water_capsule", "kit_reparation", "dried_grain", "bandage_antivenin"]


func _cost_summary(inputs: Array, outputs: Array) -> String:
	## Pastille lisible : « a×2 + b×1 → c×1 » (D1 transparence coûts).
	var in_bits: PackedStringArray = PackedStringArray()
	for inp in inputs:
		if typeof(inp) != TYPE_DICTIONARY:
			continue
		var iid := str(inp.get("id", "")).strip_edges()
		if iid.is_empty():
			continue
		in_bits.append("%s×%d" % [iid, int(inp.get("qty", 1))])
	var out_bits: PackedStringArray = PackedStringArray()
	for out in outputs:
		if typeof(out) != TYPE_DICTIONARY:
			continue
		var oid := str(out.get("id", "")).strip_edges()
		if oid.is_empty():
			continue
		out_bits.append("%s×%d" % [oid, int(out.get("qty", 1))])
	var left := ", ".join(in_bits) if in_bits.size() > 0 else "(rien)"
	if out_bits.is_empty():
		return "consomme %s" % left
	return "%s → %s" % [left, ", ".join(out_bits)]


func _craft_cost_block(recipe: Dictionary) -> Dictionary:
	## Bloc `cost` attaché aux réponses craft (succès / échec inputs).
	var inputs: Array = []
	for inp in recipe.get("inputs", []):
		if typeof(inp) == TYPE_DICTIONARY:
			inputs.append({
				"id": str(inp.get("id", "")),
				"qty": int(inp.get("qty", 1)),
			})
	var outputs: Array = []
	var out = recipe.get("output", {})
	if typeof(out) == TYPE_DICTIONARY and str(out.get("id", "")).strip_edges() != "":
		outputs.append({
			"id": str(out.get("id", "")),
			"qty": int(out.get("qty", 1)),
			"name": str(out.get("name", out.get("id", ""))),
		})
	var sources: Array = []
	var rid := str(recipe.get("id", "")).strip_edges()
	if not rid.is_empty():
		sources.append({"kind": "schematic", "id": rid})
	var skill := str(recipe.get("requires_skill", "")).strip_edges()
	if not skill.is_empty():
		sources.append({"kind": "skill", "id": skill})
	var box := str(recipe.get("requires_box", "")).strip_edges()
	if not box.is_empty():
		sources.append({"kind": "box", "id": box})
	var cat := str(recipe.get("category", "")).strip_edges()
	if not cat.is_empty():
		sources.append({"kind": "category", "id": cat})
	return {
		"inputs": inputs,
		"outputs": outputs,
		"sources": sources,
		"summary": _cost_summary(inputs, outputs),
		"ticket": "D1",
	}


func _use_cost_block(item_id: String, item_name: String = "") -> Dictionary:
	var iid := item_id.strip_edges()
	var inputs := [{"id": iid, "qty": 1, "name": item_name if not item_name.is_empty() else iid}]
	var sources: Array = [{"kind": "consumable", "id": iid}]
	if iid in CONSUMABLE_IDS:
		sources.append({"kind": "hotbar", "id": "slot_objet"})
	return {
		"inputs": inputs,
		"outputs": [],
		"sources": sources,
		"summary": _cost_summary(inputs, []),
		"ticket": "D1",
	}


func use_item(player: String, item_id: String = "") -> Dictionary:
	## Consomme 1 objet utilisable (hotbar objet / inventaire).
	var p := _player(player)
	var want := item_id.strip_edges()
	var chosen = null
	for it in p["inventory"]:
		if typeof(it) != TYPE_DICTIONARY:
			continue
		var iid := str(it.get("id", ""))
		var qty := int(it.get("qty", 0))
		if qty <= 0:
			continue
		if want != "" and iid != want:
			continue
		if want == "" and iid not in CONSUMABLE_IDS:
			continue
		chosen = it
		break
	if chosen == null:
		var miss_cost := {}
		if want != "":
			miss_cost = _use_cost_block(want)
		return {
			"ok": false,
			"error": "no_usable_item",
			"hint": "Pas d'objet utilisable (eau / kit / grain) — craft ou salvage d'abord.",
			"inventory": (p["inventory"] as Array).duplicate(true),
			"cost": miss_cost,
		}
	var iid2 := str(chosen.get("id", ""))
	var qty2 := int(chosen.get("qty", 0)) - 1
	var label := str(chosen.get("name", iid2))
	var cost := _use_cost_block(iid2, label)
	if qty2 <= 0:
		var inv: Array = []
		for it2 in p["inventory"]:
			if typeof(it2) == TYPE_DICTIONARY and str(it2.get("id", "")) == iid2:
				continue
			inv.append(it2)
		p["inventory"] = inv
	else:
		chosen["qty"] = qty2
	var effect := "used"
	match iid2:
		"water_capsule":
			effect = "Tu bois une capsule d'eau — gorge moins sèche."
		"kit_reparation":
			effect = "Kit de réparation appliqué — tu te remets d'aplomb."
		"dried_grain":
			effect = "Grain séché — un peu d'énergie pour la route."
		"bandage_antivenin":
			effect = "Bandage antivenin — la brûlure se calme."
		_:
			effect = "Tu utilises %s." % label
	_save_players()
	log_session_event(player, "item_use", effect, {"item_id": iid2})
	return {
		"ok": true,
		"item_id": iid2,
		"name": label,
		"qty_left": maxi(0, qty2),
		"effect": effect,
		"message": effect,
		"cost": cost,
		"inventory": (p["inventory"] as Array).duplicate(true),
		"chronicle": chronicle(player),
		"source": "prime_hub",
	}


func _add_item(p: Dictionary, item_id: String, qty: int, item_name: String = "") -> void:
	for it in p["inventory"]:
		if typeof(it) == TYPE_DICTIONARY and str(it.get("id", "")) == item_id:
			it["qty"] = int(it.get("qty", 0)) + qty
			return
	(p["inventory"] as Array).append({
		"id": item_id,
		"name": item_name if not item_name.is_empty() else item_id,
		"qty": qty,
		"icon": "copper",
	})


func grant_world_loot(player: String, loot: Array, credits: int = 0) -> Dictionary:
	## Loot combat open-world (bêtes densités).
	var p := _player(player)
	var granted: Array = []
	for it in loot:
		if typeof(it) != TYPE_DICTIONARY:
			continue
		var iid := str(it.get("id", "")).strip_edges()
		if iid.is_empty():
			continue
		var qty := int(it.get("qty", 1))
		_add_item(p, iid, qty, str(it.get("name", iid)))
		granted.append({"id": iid, "qty": qty, "name": str(it.get("name", iid))})
	if credits > 0:
		p["credits"] = int(p.get("credits", 0)) + credits
	_save_players()
	log_session_event(player, "beast_loot", "Butin anneau (+%d Cr)." % credits, {"credits": credits})
	return {
		"ok": true,
		"player": player if not player.is_empty() else "Voyageur",
		"credits": int(p["credits"]),
		"credits_gained": credits,
		"loot": granted,
		"source": "prime_hub",
	}


func _inv_qty(p: Dictionary, item_id: String) -> int:
	for i in p["inventory"]:
		if typeof(i) == TYPE_DICTIONARY and str(i.get("id", "")) == item_id:
			return int(i.get("qty", 0))
	return 0


func _consume(p: Dictionary, item_id: String, qty: int) -> void:
	for it in p["inventory"]:
		if typeof(it) == TYPE_DICTIONARY and str(it.get("id", "")) == item_id:
			it["qty"] = int(it.get("qty", 0)) - qty
			break
	var cleaned: Array = []
	for i in p["inventory"]:
		if typeof(i) == TYPE_DICTIONARY and int(i.get("qty", 0)) > 0:
			cleaned.append(i)
	p["inventory"] = cleaned


func craft_combine(player: String, recipe_id: String = "") -> Dictionary:
	var p := _player(player)
	var rid := recipe_id.strip_edges()
	if rid.is_empty():
		rid = "kit_reparation"
	var recipe: Dictionary = {}
	if _recipes_by_id.has(rid):
		recipe = _recipes_by_id[rid]
	else:
		# Fallback historique
		recipe = {
			"id": "kit_reparation",
			"name": "Kit de réparation",
			"requires_skill": "artisan_rue_r1",
			"inputs": [{"id": "scrap_metal", "qty": 2}, {"id": "binding_tape", "qty": 1}],
			"output": {"id": "kit_reparation", "qty": 1, "name": "Kit de réparation"},
		}
		rid = "kit_reparation"
	var cost := _craft_cost_block(recipe)
	var req_skill := str(recipe.get("requires_skill", "")).strip_edges()
	if not req_skill.is_empty():
		var skills: Array = p.get("skills", [])
		if req_skill not in skills:
			return {
				"ok": false,
				"error": "missing_skill",
				"requires_skill": req_skill,
				"cost": cost,
			}
	for inp in recipe.get("inputs", []):
		if typeof(inp) != TYPE_DICTIONARY:
			continue
		var iid := str(inp.get("id", ""))
		var need := int(inp.get("qty", 1))
		var have := _inv_qty(p, iid)
		if have < need:
			return {
				"ok": false,
				"error": "missing_inputs",
				"item_id": iid,
				"have": have,
				"need": need,
				"cost": cost,
			}
	for inp2 in recipe.get("inputs", []):
		if typeof(inp2) != TYPE_DICTIONARY:
			continue
		_consume(p, str(inp2.get("id", "")), int(inp2.get("qty", 1)))
	var out = recipe.get("output", {})
	if typeof(out) != TYPE_DICTIONARY:
		out = {"id": rid, "qty": 1}
	var oid := str(out.get("id", rid))
	var oqty := int(out.get("qty", 1))
	var oname := str(out.get("name", recipe.get("name", oid)))
	_add_item(p, oid, oqty, oname)
	_save_players()
	var crafted := {"id": oid, "name": oname, "qty": oqty, "icon": "kit"}
	log_session_event(player, "craft", "Craft : %s ×%d." % [oname, oqty], {"recipe_id": rid})
	return {
		"ok": true,
		"recipe_id": rid,
		"schematic_id": rid,
		"crafted": crafted,
		"cost": cost,
		"inventory": (p["inventory"] as Array).duplicate(true),
		"source": "prime_hub",
	}


func salvage_loot(player: String, poi_id: String = "", x: float = NAN, z: float = NAN) -> Dictionary:
	## C8 — loot pile scrap → inventaire M10 (cooldown).
	if _salvage_cfg.is_empty():
		_load_salvage()
	if _salvage_cfg.is_empty():
		return {"ok": false, "error": "salvage_unconfigured"}
	var want := str(_salvage_cfg.get("poi_id", "poi:lh_scrap_pile"))
	var pid := poi_id.strip_edges()
	if not pid.is_empty() and pid != want:
		return {"ok": false, "error": "wrong_poi", "expected": want}
	var sx := float(_salvage_cfg.get("x", 6042.0))
	var sz := float(_salvage_cfg.get("z", -1065.0))
	var rad := float(_salvage_cfg.get("radius_m", 90.0))
	if not is_nan(x) and not is_nan(z):
		var dist := Vector2(x, z).distance_to(Vector2(sx, sz))
		if dist > rad:
			return {
				"ok": false,
				"error": "too_far",
				"hint": "approche la pile de ferraille (hors palissade est)",
				"distance_m": snappedf(dist, 0.1),
				"radius_m": rad,
			}
	var key := player.strip_edges()
	if key.is_empty():
		key = "Voyageur"
	var now := Time.get_unix_time_from_system()
	var until := float(_salvage_cd.get(key, 0.0))
	if now < until:
		return {
			"ok": false,
			"error": "cooldown",
			"retry_in_s": int(ceil(until - now)),
			"hint": "laisse la pile « refroidir » quelques secondes",
		}
	var table = _salvage_cfg.get("loot_table", [])
	if typeof(table) != TYPE_ARRAY or table.is_empty():
		return {"ok": false, "error": "empty_loot_table"}
	var event_on := false
	var ev_id := str(_salvage_cfg.get("event_id", ""))
	if events != null and events.has_method("is_active") and not ev_id.is_empty():
		event_on = bool(events.is_active(ev_id))
	var bonus := int(_salvage_cfg.get("event_bonus_qty", 1)) if event_on else 0
	var granted: Array = []
	var p0 := _player(key)
	var need_tape := _inv_qty(p0, "binding_tape") < 1
	# Toujours scrap ; ruban garanti si inventaire à sec (boucle craft C8).
	for entry in table:
		if typeof(entry) != TYPE_DICTIONARY:
			continue
		var eid := str(entry.get("id", ""))
		if eid.is_empty():
			continue
		var w := int(entry.get("weight", 0))
		var qmin := int(entry.get("qty_min", 0))
		var qmax := int(entry.get("qty_max", qmin))
		var roll_ok := eid == "scrap_metal" or (eid == "binding_tape" and need_tape) \
			or (w > 0 and _rng.randi_range(1, 100) <= w)
		if not roll_ok:
			continue
		var qty := _rng.randi_range(mini(qmin, qmax), maxi(qmin, qmax))
		if eid == "scrap_metal":
			qty = maxi(1, qty) + bonus
		elif eid == "binding_tape" and need_tape:
			qty = maxi(1, qty)
		if qty <= 0:
			continue
		_add_item(p0, eid, qty, str(entry.get("name", eid)))
		granted.append({"id": eid, "name": str(entry.get("name", eid)), "qty": qty})
		if eid == "binding_tape":
			need_tape = false
	if granted.is_empty():
		_add_item(p0, "scrap_metal", 1 + bonus, "Ferraille")
		granted.append({"id": "scrap_metal", "name": "Ferraille", "qty": 1 + bonus})
	# Filet : kit_reparation exige scrap×2 + tape×1.
	if _inv_qty(p0, "binding_tape") < 1:
		_add_item(p0, "binding_tape", 1, "Ruban de liaison")
		granted.append({"id": "binding_tape", "name": "Ruban de liaison", "qty": 1})

	var cd := float(_salvage_cfg.get("cooldown_s", 40))
	if event_on:
		cd = maxf(20.0, cd * 0.75)
	_salvage_cd[key] = now + cd
	_save_players()
	var p := _player(key)
	var loot_bits: PackedStringArray = PackedStringArray()
	for g in granted:
		if typeof(g) == TYPE_DICTIONARY:
			loot_bits.append("%s×%d" % [str(g.get("name", g.get("id", "?"))), int(g.get("qty", 1))])
	log_session_event(key, "salvage", "Salvage hors palissade : %s." % ", ".join(loot_bits), {"poi_id": want})
	return {
		"ok": true,
		"poi_id": want,
		"player": key,
		"loot": granted,
		"event_boost": event_on,
		"cooldown_s": int(cd),
		"inventory": (p["inventory"] as Array).duplicate(true),
		"hint": "Craft kit_reparation à l'atelier / panneau Talents (T)",
		"source": "prime_hub",
	}


func _vendor_rep(p: Dictionary, vendor_id: String) -> int:
	var reps = p.get("reputation", {})
	if typeof(reps) != TYPE_DICTIONARY:
		return 0
	return int(reps.get(vendor_id, 0))


func _set_vendor_rep(p: Dictionary, vendor_id: String, value: int) -> void:
	if typeof(p.get("reputation")) != TYPE_DICTIONARY:
		p["reputation"] = {}
	(p["reputation"] as Dictionary)[vendor_id] = value


func trade_catalog(vendor_id: String = "npc:core3_barman_jax") -> Dictionary:
	if _vendor_jax.is_empty():
		_load_vendor_jax()
	if _vendor_jax.is_empty():
		return {"ok": false, "error": "vendor_unconfigured"}
	var vid := str(_vendor_jax.get("vendor_id", "npc:core3_barman_jax"))
	if not vendor_id.is_empty() and vendor_id != vid:
		return {"ok": false, "error": "unknown_vendor", "vendor_id": vendor_id}
	return {
		"ok": true,
		"vendor_id": vid,
		"display_name": str(_vendor_jax.get("display_name", "Jax Moro")),
		"bounds": (_vendor_jax.get("bounds", {}) as Dictionary).duplicate(true),
		"catalog": (_vendor_jax.get("catalog", []) as Array).duplicate(true),
		"source": "prime_hub",
		"ticket": "C7",
	}


func trade_offer(player: String, vendor_id: String, sku_id: String, offer_price: int) -> Dictionary:
	## C7 — négo bornée Jax (pas de LLM sur le prix).
	if _vendor_jax.is_empty():
		_load_vendor_jax()
	if _vendor_jax.is_empty():
		return {"ok": false, "error": "vendor_unconfigured"}
	var vid := str(_vendor_jax.get("vendor_id", "npc:core3_barman_jax"))
	if not vendor_id.is_empty() and vendor_id != vid:
		return {"ok": false, "error": "unknown_vendor", "vendor_id": vendor_id}
	var sku := sku_id.strip_edges()
	# Alias accent / underscore
	if sku == "drink:eau_filtrée":
		sku = "drink:eau_filtree"
	var item: Dictionary = {}
	for row in _vendor_jax.get("catalog", []):
		if typeof(row) == TYPE_DICTIONARY and str(row.get("sku_id", "")) == sku:
			item = row
			break
	if item.is_empty():
		return {"ok": false, "error": "unknown_sku", "sku_id": sku_id}
	var list_price := int(item.get("list_price", 0))
	var offer := offer_price
	if offer <= 0:
		offer = list_price
	var p := _player(player)
	var rep := _vendor_rep(p, vid)
	var bounds: Dictionary = _vendor_jax.get("bounds", {})
	var max_pct := float(bounds.get("price_delta_pct_max", 15))
	var low_th := int(bounds.get("low_reputation_threshold", 0))
	if rep < low_th:
		max_pct = float(bounds.get("price_delta_pct_max_low_rep", 8))
	var delta_pct := 0.0
	if list_price > 0:
		delta_pct = (float(offer) - float(list_price)) / float(list_price) * 100.0
	if absf(delta_pct) > max_pct + 0.01:
		return {
			"ok": false,
			"error": "offer_out_of_bounds",
			"reason": "offer_out_of_bounds",
			"outcome": "reject",
			"list_price": list_price,
			"offer_price": offer,
			"price_delta_pct": snappedf(delta_pct, 0.1),
			"max_delta_pct": max_pct,
			"reputation": rep,
			"hint": "Jax refuse — reste dans ±%.0f %% du prix affiché" % max_pct,
			"source": "prime_hub",
		}
	if int(p["credits"]) < offer:
		return {
			"ok": false,
			"error": "insufficient_credits",
			"credits": int(p["credits"]),
			"offer_price": offer,
			"hint": "Pas assez de crédits",
			"source": "prime_hub",
		}
	p["credits"] = int(p["credits"]) - offer
	var item_id := str(item.get("item_id", sku.replace(":", "_")))
	var label := str(item.get("label", item_id))
	_add_item(p, item_id, 1, label)
	var rep_delta := 0
	if offer < list_price:
		rep_delta = 1
	elif offer > list_price:
		rep_delta = 1
	var rmin := int(bounds.get("reputation_delta_min", -5))
	var rmax := int(bounds.get("reputation_delta_max", 5))
	rep_delta = clampi(rep_delta, rmin, rmax)
	var new_rep := clampi(rep + rep_delta, -50, 50)
	_set_vendor_rep(p, vid, new_rep)
	remember_relation(
		player,
		vid,
		"gift",
		"Tu as acheté « %s » chez Jax pour %d Cr." % [label.substr(0, 40), offer],
		{"value": offer, "item_id": item_id}
	)
	_save_players()
	log_session_event(
		player,
		"trade",
		"Chez Jax : %s pour %d Cr (liste %d)." % [label, offer, list_price],
		{"sku_id": sku, "price_paid": offer}
	)
	return {
		"ok": true,
		"outcome": "accept",
		"vendor_id": vid,
		"sku_id": sku,
		"label": label,
		"list_price": list_price,
		"offer_price": offer,
		"price_paid": offer,
		"price_delta_pct": snappedf(delta_pct, 0.1),
		"reputation": new_rep,
		"reputation_delta": rep_delta,
		"credits": int(p["credits"]),
		"inventory": (p["inventory"] as Array).duplicate(true),
		"commit_flags": {
			"trade_sku": sku,
			"price_paid": offer,
			"reputation_delta": rep_delta,
		},
		"message": "Jax : marché conclu — %s." % label,
		"source": "prime_hub",
		"ticket": "C7",
	}


const _REL_KIND_PREFIX := {
	"debt": "Dette",
	"met": "Rencontre",
	"gift": "Cadeau",
	"quest": "Quête",
}


func _npc_short(npc_id: String) -> String:
	var nid := npc_id.strip_edges()
	match nid:
		"npc:core3_daan_oth":
			return "Daan"
		"npc:core3_barman_jax":
			return "Jax"
		"npc:scribe":
			return "le Scribe"
		"npc:guide_quartier":
			return "le Guide"
		_:
			if nid.begins_with("npc:"):
				return nid.substr(4).replace("core3_", "").replace("_", " ")
			return nid if not nid.is_empty() else "PNJ"


func _iso_now() -> String:
	## ISO 8601 approximatif (UTC) pour schéma C2.
	var t := Time.get_datetime_dict_from_system(true)
	return "%04d-%02d-%02dT%02d:%02d:%02dZ" % [
		int(t.get("year", 2026)), int(t.get("month", 1)), int(t.get("day", 1)),
		int(t.get("hour", 0)), int(t.get("minute", 0)), int(t.get("second", 0)),
	]


func remember_relation(
	player: String,
	npc_id: String,
	kind: String,
	note: String,
	extra: Dictionary = {}
) -> Dictionary:
	## C2 — persiste une entrée relation dans players_state (schéma Vague A).
	var nid := npc_id.strip_edges()
	var k := kind.strip_edges().to_lower()
	var n := note.strip_edges().replace("\n", " ")
	if nid.is_empty() or n.is_empty():
		return {"ok": false, "error": "invalid_entry"}
	if k not in ["debt", "met", "gift", "quest"]:
		return {"ok": false, "error": "invalid_kind", "kind": kind}
	if n.length() > 512:
		n = n.substr(0, 509) + "…"
	var p := _player(player)
	var rows: Array = p["relation_memory"]
	# Dédup met : une seule rencontre par PNJ.
	if k == "met":
		for row in rows:
			if typeof(row) != TYPE_DICTIONARY:
				continue
			if str(row.get("npc_id", "")) == nid and str(row.get("kind", "")) == "met":
				return {"ok": true, "already": true, "entry": row}
	# Dédup récente même kind+note (évite spam tip/trade).
	for row2 in rows:
		if typeof(row2) != TYPE_DICTIONARY:
			continue
		if str(row2.get("npc_id", "")) == nid and str(row2.get("kind", "")) == k:
			if str(row2.get("note", "")).strip_edges() == n:
				return {"ok": true, "already": true, "entry": row2}
	var entry := {
		"player_id": player.strip_edges() if not player.strip_edges().is_empty() else "Voyageur",
		"npc_id": nid,
		"kind": k,
		"note": n,
		"ts": _iso_now(),
	}
	if extra.has("value"):
		entry["value"] = extra["value"]
	if extra.has("quest_id") and str(extra.get("quest_id", "")).strip_edges() != "":
		entry["quest_id"] = str(extra["quest_id"]).strip_edges()
	elif k == "quest" and extra.has("value"):
		entry["quest_id"] = str(extra["value"])
	if extra.has("item_id") and str(extra.get("item_id", "")).strip_edges() != "":
		entry["item_id"] = str(extra["item_id"]).strip_edges()
	if k == "quest" and str(entry.get("quest_id", "")).is_empty():
		entry["quest_id"] = "unknown"
	rows.append(entry)
	while rows.size() > 48:
		rows.remove_at(0)
	p["relation_memory"] = rows
	_save_players()
	return {"ok": true, "entry": entry, "count": rows.size()}


func relation_memory(player: String, npc_id: String = "") -> Dictionary:
	## Lecture C2 — entrées filtrées (npc optionnel), plus récent d'abord.
	var p := _player(player)
	var nid := npc_id.strip_edges()
	var out: Array = []
	for row in p["relation_memory"]:
		if typeof(row) != TYPE_DICTIONARY:
			continue
		if not nid.is_empty() and str(row.get("npc_id", "")) != nid:
			continue
		out.append((row as Dictionary).duplicate(true))
	out.sort_custom(func(a, b): return str(a.get("ts", "")) > str(b.get("ts", "")))
	return {
		"ok": true,
		"player": player.strip_edges() if not player.strip_edges().is_empty() else "Voyageur",
		"npc_id": nid,
		"entries": out,
		"count": out.size(),
		"source": "prime_hub",
		"ticket": "C2",
	}


func relation_memory_hint(player: String, npc_id: String, max_len: int = 160, max_notes: int = 2) -> String:
	## Phrase courte pour session_memory / world_hint (miroir Python relation_memory).
	var pack: Dictionary = relation_memory(player, npc_id)
	var rows = pack.get("entries", [])
	if typeof(rows) != TYPE_ARRAY or rows.is_empty():
		return ""
	var parts: PackedStringArray = PackedStringArray()
	var n := mini(maxi(1, max_notes), rows.size())
	for i in range(n):
		var row: Dictionary = rows[i]
		var note := str(row.get("note", "")).strip_edges().replace("\n", " ")
		if note.is_empty():
			continue
		var kind := str(row.get("kind", "")).strip_edges()
		var prefix := str(_REL_KIND_PREFIX.get(kind, kind))
		if not prefix.is_empty():
			parts.append("%s: %s" % [prefix, note])
		else:
			parts.append(note)
	if parts.is_empty():
		return ""
	var text := " · ".join(parts)
	if text.length() > max_len:
		text = text.substr(0, max_len - 1) + "…"
	return text


func item_quantity(player: String, item_id: String) -> int:
	var p := _player(player)
	return _inv_qty(p, item_id.strip_edges())


func atomic_barter_swap(
	sender: String,
	receiver: String,
	give_item_id: String,
	give_qty: int,
	receive_item_id: String,
	receive_qty: int,
	give_item_name: String = "",
	receive_item_name: String = ""
) -> Dictionary:
	## Ticket 3.2 — Échange P2P atomique sous autorité serveur (zéro duplication, zéro mutation libre).
	var s_name := sender.strip_edges()
	var r_name := receiver.strip_edges()
	var g_id := give_item_id.strip_edges()
	var r_id := receive_item_id.strip_edges()
	if s_name.is_empty() or r_name.is_empty() or s_name == r_name:
		return {"ok": false, "error": "invalid_participants"}
	if g_id.is_empty() or r_id.is_empty() or give_qty <= 0 or receive_qty <= 0:
		return {"ok": false, "error": "invalid_trade_quantities"}

	var p_sender := _player(s_name)
	var p_receiver := _player(r_name)

	var have_give := _inv_qty(p_sender, g_id)
	if have_give < give_qty:
		return {
			"ok": false,
			"error": "sender_insufficient_items",
			"player": s_name,
			"item_id": g_id,
			"have": have_give,
			"need": give_qty,
		}

	var have_recv := _inv_qty(p_receiver, r_id)
	if have_recv < receive_qty:
		return {
			"ok": false,
			"error": "receiver_insufficient_items",
			"player": r_name,
			"item_id": r_id,
			"have": have_recv,
			"need": receive_qty,
		}

	var g_label := give_item_name if not give_item_name.is_empty() else g_id
	var r_label := receive_item_name if not receive_item_name.is_empty() else r_id

	# Retrait bilatéral puis ajout bilatéral atomique + persistance SQLite
	_consume(p_sender, g_id, give_qty)
	_consume(p_receiver, r_id, receive_qty)
	_add_item(p_sender, r_id, receive_qty, r_label)
	_add_item(p_receiver, g_id, give_qty, g_label)

	_save_players()
	log_session_event(
		s_name,
		"barter_p2p",
		"Troc P2P avec %s : -%d %s / +%d %s." % [r_name, give_qty, g_label, receive_qty, r_label],
		{"partner": r_name, "give_id": g_id, "give_qty": give_qty, "recv_id": r_id, "recv_qty": receive_qty}
	)
	log_session_event(
		r_name,
		"barter_p2p",
		"Troc P2P avec %s : -%d %s / +%d %s." % [s_name, receive_qty, r_label, give_qty, g_label],
		{"partner": s_name, "give_id": r_id, "give_qty": receive_qty, "recv_id": g_id, "recv_qty": give_qty}
	)
	return {
		"ok": true,
		"sender": s_name,
		"receiver": r_name,
		"gave": {"id": g_id, "qty": give_qty, "name": g_label},
		"received": {"id": r_id, "qty": receive_qty, "name": r_label},
		"sender_inventory": (p_sender["inventory"] as Array).duplicate(true),
		"receiver_inventory": (p_receiver["inventory"] as Array).duplicate(true),
	}
