extends Node
## EchoHammatController — 1 actif + 1 écho max. Spawn local à côté du joueur + follow.

signal state_changed(state: Dictionary)
signal action_message(message: String)

const MAX_SIMULTANEOUS := 2
const ECHO_OID := 0x0E000001
const COLOR_ECHO := Color(0.25, 0.92, 0.88, 1.0)
const FOLLOW_DIST_M := 3.2
const FOLLOW_SIDE_M := 1.4
const FOLLOW_SPEED := 11.0
const SNAP_DIST_M := 14.0

var active_character_id: String = ""
var active_character_name: String = ""
var echo_character_id: String = ""
var echo_character_name: String = ""
var noyau_id: String = ""
var particule_seed: String = ""
var account_roster: Array = []

var _ws: Node = null
var _em: Node = null
var _pc: Node = null
var _invoke_cooldown_s: float = 8.0
var _switch_cooldown_s: float = 5.0
var _last_invoke_at: float = -999.0
var _last_switch_at: float = -999.0
var _last_player_pos: Vector3 = Vector3.INF
var _follow_back: Vector3 = Vector3(0.0, 0.0, -1.0)


func bind_ws_client(ws: Node) -> void:
	_ws = ws
	if _ws != null and _ws.has_signal("echo_state_changed"):
		if not _ws.echo_state_changed.is_connected(_on_ws_echo_state):
			_ws.echo_state_changed.connect(_on_ws_echo_state)


func bind_world(entity_manager: Node, player_controller: Node) -> void:
	_em = entity_manager
	_pc = player_controller
	set_process(true)


func echo_object_id() -> int:
	return ECHO_OID


func set_roster(chars: Array, active_id: String = "", active_name: String = "") -> void:
	account_roster = chars.duplicate()
	if not active_id.is_empty():
		active_character_id = active_id
	if not active_name.is_empty():
		active_character_name = active_name
	_sync_noyau_from_roster()
	_emit_state()


func has_echo() -> bool:
	return not echo_character_id.is_empty()


func can_invoke() -> bool:
	if has_echo():
		return false
	if _cooldown_remaining(_last_invoke_at, _invoke_cooldown_s) > 0.0:
		return false
	return not _invoke_candidates().is_empty()


func can_switch() -> bool:
	if not has_echo():
		return false
	return _cooldown_remaining(_last_switch_at, _switch_cooldown_s) <= 0.0


func invoke_candidates() -> Array:
	return _invoke_candidates()


func invoke_echo(character_id: String) -> void:
	if has_echo():
		action_message.emit("Un écho est déjà présent — renvoie-le d'abord.")
		return
	var cd := _cooldown_remaining(_last_invoke_at, _invoke_cooldown_s)
	if cd > 0.0:
		action_message.emit("Invocation disponible dans %.0f s." % cd)
		return
	var picked := _find_roster_entry(character_id)
	if picked.is_empty():
		action_message.emit("Personnage inconnu.")
		return
	if str(picked.get("character_id", "")) == active_character_id:
		action_message.emit("Impossible d'invoquer le perso actif.")
		return
	_send_or_stub("invoke_echo", {"character_id": character_id})


func dismiss_echo() -> void:
	if not has_echo():
		action_message.emit("Aucun écho à renvoyer.")
		return
	_send_or_stub("dismiss_echo", {})


func switch_active() -> void:
	if not has_echo():
		action_message.emit("Aucun écho — invocation requise.")
		return
	var cd := _cooldown_remaining(_last_switch_at, _switch_cooldown_s)
	if cd > 0.0:
		action_message.emit("Switch disponible dans %.0f s." % cd)
		return
	_send_or_stub("switch_active", {})


func echo_order(order: String) -> void:
	if not has_echo():
		action_message.emit("Aucun écho — ordre ignoré.")
		return
	_send_or_stub("echo_order", {"order": order})


func hammat_trade(items: Array, credits: int = 0) -> void:
	if not has_echo():
		action_message.emit("Échange Amas : écho requis à proximité.")
		return
	_send_or_stub("hammat_trade", {"items": items, "credits": credits})


func _send_or_stub(msg_type: String, extra: Dictionary) -> void:
	if _ws != null and _ws.has_method("send_echo_message") and not bool(_ws.get("echo_ws_stub")):
		var payload := {"type": msg_type, "proto": "lbg-ws/2"}
		payload.merge(extra)
		_ws.send_echo_message(payload)
		return
	call_deferred("_apply_stub_response", msg_type, extra)


func _apply_stub_response(msg_type: String, extra: Dictionary) -> void:
	match msg_type:
		"invoke_echo":
			var cid := str(extra.get("character_id", ""))
			var entry := _find_roster_entry(cid)
			if entry.is_empty():
				action_message.emit("Stub : personnage introuvable.")
				return
			echo_character_id = cid
			echo_character_name = str(entry.get("name", cid))
			_last_invoke_at = Time.get_ticks_msec() / 1000.0
			_spawn_echo_beside_player()
			action_message.emit("Écho invoqué : %s — il te suit" % echo_character_name)
		"dismiss_echo":
			var old := echo_character_name
			echo_character_id = ""
			echo_character_name = ""
			_despawn_echo_visual()
			action_message.emit("Écho renvoyé : %s" % (old if old else "?"))
		"switch_active":
			var tmp_id := active_character_id
			var tmp_name := active_character_name
			active_character_id = echo_character_id
			active_character_name = echo_character_name
			echo_character_id = tmp_id
			echo_character_name = tmp_name
			_last_switch_at = Time.get_ticks_msec() / 1000.0
			action_message.emit("Switch → actif : %s" % active_character_name)
		"echo_order":
			action_message.emit("Ordre écho (%s) → %s" % [extra.get("order", "?"), echo_character_name])
		"hammat_trade":
			action_message.emit("Échange Amas (stub) avec %s" % echo_character_name)
	_emit_state()


func _on_ws_echo_state(payload: Dictionary) -> void:
	if payload.has("active_character_id"):
		active_character_id = str(payload.get("active_character_id", active_character_id))
	if payload.has("active_character_name"):
		active_character_name = str(payload.get("active_character_name", active_character_name))
	echo_character_id = str(payload.get("echo_character_id", ""))
	echo_character_name = str(payload.get("echo_character_name", ""))
	if payload.has("noyau_id"):
		noyau_id = str(payload.get("noyau_id", noyau_id))
	if payload.has("particule_seed"):
		particule_seed = str(payload.get("particule_seed", particule_seed))
	var msg := str(payload.get("message", ""))
	if not msg.is_empty():
		action_message.emit(msg)
	if has_echo():
		_spawn_echo_beside_player()
	else:
		_despawn_echo_visual()
	_emit_state()


func _player_entity() -> Node:
	if _em == null or _pc == null or not _pc.has_method("get_player_id"):
		return null
	var pid := int(_pc.get_player_id())
	if pid <= 0:
		return null
	return _em.get_entity(pid)


func _follow_target(me: Node) -> Vector3:
	var pos: Vector3 = me.core3_pos
	if _last_player_pos != Vector3.INF:
		var delta := pos - _last_player_pos
		delta.y = 0.0
		if delta.length() > 0.08:
			_follow_back = -delta.normalized()
	_last_player_pos = pos
	var side := Vector3(-_follow_back.z, 0.0, _follow_back.x)
	return pos + _follow_back * FOLLOW_DIST_M + side * FOLLOW_SIDE_M


func _spawn_echo_beside_player() -> void:
	if _em == null or not has_echo():
		return
	var me := _player_entity()
	if me == null:
		return
	var at := _follow_target(me)
	var label := "%s (écho)" % (echo_character_name if echo_character_name else "Écho")
	if _em.get_entity(ECHO_OID) == null:
		_em.spawn(ECHO_OID, at, COLOR_ECHO, label, "player", "player:echo")
	else:
		_em.move(ECHO_OID, at)
		var e: Node = _em.get_entity(ECHO_OID)
		if e and e.has_method("set_label"):
			e.set_label(label)
		if e and e.has_method("set_color"):
			e.set_color(COLOR_ECHO)


func _despawn_echo_visual() -> void:
	if _em and _em.get_entity(ECHO_OID) != null:
		_em.despawn(ECHO_OID)
	_last_player_pos = Vector3.INF


func _process(delta: float) -> void:
	if not has_echo() or _em == null:
		return
	var me := _player_entity()
	if me == null:
		return
	if _em.get_entity(ECHO_OID) == null:
		_spawn_echo_beside_player()
		return
	var target := _follow_target(me)
	var echo: Node = _em.get_entity(ECHO_OID)
	if echo == null:
		return
	var cur: Vector3 = echo.core3_pos
	var to := target - cur
	to.y = 0.0
	var dist := to.length()
	if dist < 0.12:
		return
	if dist > SNAP_DIST_M:
		_em.move(ECHO_OID, target)
		return
	var step := minf(dist, FOLLOW_SPEED * delta)
	_em.move(ECHO_OID, cur + to / dist * step)


func _invoke_candidates() -> Array:
	var out: Array = []
	for c in account_roster:
		if c is Dictionary:
			var cid := str(c.get("character_id", ""))
			if cid.is_empty():
				cid = str(c.get("id", ""))
			if cid.is_empty() or cid == active_character_id or cid == echo_character_id:
				continue
			if str(c.get("id", "")) != "" and str(c.get("id", "")) == active_character_id:
				continue
			out.append(c)
	if out.is_empty() and not has_echo():
		out.append({
			"id": "echo_local",
			"character_id": "echo_local",
			"name": "Éclat",
			"archetype": "écho",
		})
	return out


func _find_roster_entry(character_id: String) -> Dictionary:
	for c in _invoke_candidates():
		if c is Dictionary:
			if str(c.get("character_id", "")) == character_id or str(c.get("id", "")) == character_id:
				return c
	for c in account_roster:
		if c is Dictionary:
			if str(c.get("character_id", "")) == character_id or str(c.get("id", "")) == character_id:
				return c
	return {}


func _sync_noyau_from_roster() -> void:
	for c in account_roster:
		if c is Dictionary:
			if str(c.get("noyau_id", "")) != "":
				noyau_id = str(c.get("noyau_id"))
				particule_seed = str(c.get("particule_seed", particule_seed))
				return


func _cooldown_remaining(since: float, duration: float) -> float:
	if since < 0.0:
		return 0.0
	var now := Time.get_ticks_msec() / 1000.0
	return maxf(0.0, duration - (now - since))


func _emit_state() -> void:
	state_changed.emit({
		"active_character_id": active_character_id,
		"active_character_name": active_character_name,
		"echo_character_id": echo_character_id,
		"echo_character_name": echo_character_name,
		"noyau_id": noyau_id,
		"particule_seed": particule_seed,
		"simultaneous_count": (1 if active_character_id != "" else 0) + (1 if has_echo() else 0),
		"max_simultaneous": MAX_SIMULTANEOUS,
	})
