extends RefCounted
class_name HubEscort
## Escorte hub — civil suivable pour `lh_escort_gate_clinic` (O-OPS-3 / polish O2).
## Phases : waiting_pickup → escorting → delivered | failed.

const QUEST_ID := "lh_escort_gate_clinic"
const CIVIL_NAME := "Civil blessé"
const FAIL_RADIUS_M := 40.0
const FAIL_GRACE_S := 8.0
const CLINIC_RADIUS_M := 55.0
const FOLLOW_OFFSET_X := 4.0
const FOLLOW_OFFSET_Z := 3.0
const CIVIL_SPEED := 11.0
const OID_BASE := 920001
const GATE := Vector3(5813.6, 0.15, -982.5)
const CLINIC := Vector3(4679.0, 0.15, -672.0)

## player_key -> session dict
var sessions: Dictionary = {}
var _oid_seq: int = 0


func clear() -> void:
	sessions.clear()
	_oid_seq = 0


func is_escort_quest(quest_id: String) -> bool:
	return quest_id.strip_edges() == QUEST_ID


func session_for(player: String) -> Dictionary:
	var key := _key(player)
	if sessions.has(key):
		return sessions[key] as Dictionary
	return {}


func on_accept(sim, player: String) -> Dictionary:
	## Spawn civil à la porte est ; phase waiting_pickup.
	if sim == null:
		return {"ok": false, "error": "sim_unavailable"}
	var key := _key(player)
	_despawn(sim, key)
	var eid := "npc:escort_civil:%s" % key
	_oid_seq += 1
	var oid := OID_BASE + (_oid_seq % 8000)
	var wz: Vector2 = _walkable(sim, GATE.x, GATE.z)
	var ent := {
		"eid": eid,
		"oid": oid,
		"kind": "npc",
		"name": CIVIL_NAME,
		"pos": Vector3(wz.x, GATE.y, wz.y),
		"target": Vector3.ZERO,
		"speed": CIVIL_SPEED,
		"is_bot": false,
		"goal": "escort_wait",
		"play_mode": "escort",
		"quest_id": QUEST_ID,
		"linger_until": 0.0,
		"stuck_ticks": 0,
		"home_x": wz.x,
		"home_z": wz.y,
		"wander_r": 0.0,
		"ambient": "J'ai besoin d'aller à la clinique… tu peux m'escorter ?",
		"active": true,
		"escort_player": key,
	}
	sim.entities[eid] = ent
	sessions[key] = {
		"player": key,
		"eid": eid,
		"oid": oid,
		"phase": "waiting_pickup",
		"fail_accum_s": 0.0,
		"quest_id": QUEST_ID,
	}
	_stream(sim, "escort.spawn", "%s attend à la porte est." % CIVIL_NAME, CIVIL_NAME, key)
	return {"ok": true, "eid": eid, "oid": oid, "phase": "waiting_pickup", "pos": [wz.x, GATE.y, wz.y]}


func on_progress(sim, player: String, step_id: String) -> Dictionary:
	## pickup → démarre le suivi ; dropoff → exige civil près de la clinique.
	var key := _key(player)
	var sid := step_id.strip_edges()
	if not sessions.has(key):
		# Accept sans sim (tests economy seuls) : autoriser pickup, bloquer dropoff.
		if sid == "dropoff":
			return {"ok": false, "error": "escort_civil_missing", "hint": "Le civil n'est pas en escorte"}
		return {"ok": true, "phase": "no_session"}
	var sess: Dictionary = sessions[key]
	if sid == "pickup":
		sess["phase"] = "escorting"
		sess["fail_accum_s"] = 0.0
		var eid := str(sess.get("eid", ""))
		if sim != null and sim.entities.has(eid):
			sim.entities[eid]["goal"] = "escort_follow"
			sim.entities[eid]["ambient"] = "Reste près de moi — la clinique n'est pas loin."
		_stream(sim, "escort.follow", "%s suit %s." % [CIVIL_NAME, key], CIVIL_NAME, key)
		return {"ok": true, "phase": "escorting"}
	if sid == "dropoff":
		if not _civil_near_clinic(sim, sess):
			return {
				"ok": false,
				"error": "escort_civil_lagging",
				"hint": "Le civil doit arriver à la clinique avec toi (reste à < %.0f m)" % FAIL_RADIUS_M,
				"phase": str(sess.get("phase", "")),
			}
		sess["phase"] = "delivered"
		var eid2 := str(sess.get("eid", ""))
		if sim != null and sim.entities.has(eid2):
			sim.entities[eid2]["goal"] = "escort_done"
			sim.entities[eid2]["target"] = Vector3.ZERO
			sim.entities[eid2]["ambient"] = "Merci… Odo Merr va s'occuper de moi."
		_stream(sim, "escort.delivered", "%s est arrivé à la clinique." % CIVIL_NAME, CIVIL_NAME, key)
		return {"ok": true, "phase": "delivered"}
	return {"ok": true, "phase": str(sess.get("phase", ""))}


func on_complete(sim, player: String) -> void:
	_despawn(sim, _key(player))


func tick(sim, dt: float, economy = null) -> void:
	if sim == null or sessions.is_empty():
		return
	dt = clampf(dt, 0.001, 0.25)
	var to_fail: Array = []
	for key in sessions.keys():
		var sess: Dictionary = sessions[key]
		var phase := str(sess.get("phase", ""))
		var eid := str(sess.get("eid", ""))
		if not sim.entities.has(eid):
			continue
		var civil: Dictionary = sim.entities[eid]
		if phase == "waiting_pickup":
			continue
		if phase != "escorting":
			continue
		var player_ent = _find_player(sim, key)
		if player_ent == null:
			# Pas de joueur online : grace timer ne court pas.
			continue
		var pp: Vector3 = player_ent["pos"]
		var cp: Vector3 = civil["pos"]
		var sep := Vector2(pp.x - cp.x, pp.z - cp.z).length()
		if sep > FAIL_RADIUS_M:
			sess["fail_accum_s"] = float(sess.get("fail_accum_s", 0.0)) + dt
			if float(sess["fail_accum_s"]) >= FAIL_GRACE_S:
				to_fail.append(key)
				continue
		else:
			sess["fail_accum_s"] = 0.0
		# Suivre le joueur (offset walkable).
		var tx := pp.x + FOLLOW_OFFSET_X
		var tz := pp.z + FOLLOW_OFFSET_Z
		var wz: Vector2 = _walkable(sim, tx, tz)
		civil["target"] = Vector3(wz.x, pp.y, wz.y)
		civil["goal"] = "escort_follow"
		_step_civil(sim, civil, dt)
	for fk in to_fail:
		_fail_session(sim, economy, str(fk))


func can_dropoff(sim, player: String) -> bool:
	var sess := session_for(player)
	if sess.is_empty():
		return false
	return _civil_near_clinic(sim, sess)


func snapshot(player: String = "") -> Dictionary:
	if player.strip_edges() != "":
		var s := session_for(player)
		return {"ok": true, "quest_id": QUEST_ID, "session": s}
	var rows: Array = []
	for k in sessions.keys():
		rows.append((sessions[k] as Dictionary).duplicate(true))
	return {"ok": true, "quest_id": QUEST_ID, "count": rows.size(), "sessions": rows}


func _fail_session(sim, economy, key: String) -> void:
	var sess: Dictionary = sessions.get(key, {})
	sess["phase"] = "failed"
	_stream(sim, "escort.failed", "%s a perdu de vue %s." % [CIVIL_NAME, key], CIVIL_NAME, key)
	if economy != null and economy.has_method("abandon"):
		economy.abandon(key, QUEST_ID, "escort_separated")
	_despawn(sim, key)


func _despawn(sim, key: String) -> void:
	if sessions.has(key):
		var eid := str((sessions[key] as Dictionary).get("eid", ""))
		if sim != null and eid != "" and sim.entities.has(eid):
			sim.entities.erase(eid)
		sessions.erase(key)


func _civil_near_clinic(sim, sess: Dictionary) -> bool:
	if sim == null:
		return false
	var eid := str(sess.get("eid", ""))
	if not sim.entities.has(eid):
		return false
	var p: Vector3 = sim.entities[eid]["pos"]
	return Vector2(p.x - CLINIC.x, p.z - CLINIC.z).length() <= CLINIC_RADIUS_M


func _find_player(sim, key: String):
	var want := key.to_lower()
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "player" or bool(e.get("is_bot", false)):
			continue
		if str(e.get("name", "")).strip_edges().to_lower() == want:
			return e
	return null


func _step_civil(sim, civil: Dictionary, dt: float) -> void:
	var target: Vector3 = civil.get("target", Vector3.ZERO)
	if target == Vector3.ZERO:
		return
	var pos: Vector3 = civil["pos"]
	var dx := target.x - pos.x
	var dz := target.z - pos.z
	var dist := sqrt(dx * dx + dz * dz)
	if dist < 2.5:
		return
	var speed := float(civil.get("speed", CIVIL_SPEED))
	var step_len := minf(dist, speed * dt)
	var nx := pos.x + (dx / dist) * step_len
	var nz := pos.z + (dz / dist) * step_len
	if sim.collision != null:
		var c: Vector2 = sim.collision.clamp_move(pos.x, pos.z, nx, nz) as Vector2
		nx = c.x
		nz = c.y
	civil["pos"] = Vector3(nx, pos.y, nz)


func _walkable(sim, x: float, z: float) -> Vector2:
	if sim != null and sim.has_method("_walkable_xz"):
		return sim._walkable_xz(x, z) as Vector2
	if sim != null and sim.collision != null and sim.collision.has_method("nearest_walkable"):
		return sim.collision.nearest_walkable(x, z) as Vector2
	return Vector2(x, z)


func _key(player: String) -> String:
	return player.strip_edges()


func _stream(sim, kind: String, text: String, actor: String, zone_player: String) -> void:
	if sim != null and sim.has_method("_stream"):
		sim._stream(kind, text, actor, "escort:%s" % zone_player, {"quest_id": QUEST_ID})
