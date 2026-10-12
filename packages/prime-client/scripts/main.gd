# main.gd — Scene principale Prime Client (Godot 4.6)
# Découpage modulaire Ticket 2.2 : client_gameplay_ops, client_quest_ops, client_net_world, client_ui_dialogue.
extends Node2D

@onready var camera:         Camera2D      = $Camera2D
@onready var entity_manager: Node          = $EntityManager
@onready var info_label:     Label         = $UI/HudLayer/InfoPanel/VBox/InfoLabel
@onready var stats_label:    Label         = $UI/HudLayer/InfoPanel/VBox/StatsLabel
@onready var state_label:    Label         = $UI/HudLayer/StatePanel/StateLabel
@onready var hotbar:         Node          = $UI/HudLayer/Hotbar
@onready var inventory_panel: Node         = $UI/ModalLayer/InventoryPanel
@onready var _talents_panel: Node          = $UI/ModalLayer/TalentsCraftPanel
@onready var _mission_board: Node          = $UI/ModalLayer/MissionBoardPanel
@onready var _game_menu:     Node          = $UI/ModalLayer/GameMenuPanel
@onready var _echo_panel:    Node          = $UI/ModalLayer/EchoHammatPanel
@onready var _initiation_panel: Node       = $UI/ModalLayer/InitiationQuestPanel
@onready var _creation_panel: Control      = $UI/ModalLayer/CharacterCreationPanel
@onready var _dialogue_panel: Node         = $UI/ModalLayer/DialoguePortraitPanel
@onready var _login_panel:   Control       = $UI/LoginPanel
@onready var _ws:            Node          = get_node_or_null("%LbgWsClient")

# Modules spécialisés Ticket 2.2
const _GameplayOpsScript = preload("res://scripts/client_gameplay_ops.gd")
const _QuestOpsScript = preload("res://scripts/client_quest_ops.gd")
const _NetWorldScript = preload("res://scripts/client_net_world.gd")
const _UiDialogueScript = preload("res://scripts/client_ui_dialogue.gd")

# Scripts helpers préchargés
const _Projection3D2D = preload("res://scripts/projection.gd")
const _Crc32Util = preload("res://scripts/crc32_util.gd")
const _EntityScript = preload("res://scripts/entity.gd")
const _LastPos = preload("res://scripts/last_position_store.gd")
const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")

var gameplay_ops: RefCounted = null
var quest_ops: RefCounted = null
var net_world: RefCounted = null
var ui_dialogue: RefCounted = null

const COLOR_PLAYER_OFFICIAL := Color(0.2, 0.4, 1.0, 1.0)
const COLOR_PLAYER_BOT := Color(0.0, 0.9, 0.4, 1.0)
const COLOR_NPC := Color(1.0, 0.5, 0.1, 1.0)

const CAM_SPEED:     float   = 400.0
const CAM_ZOOM_STEP: float   = 0.15
const CAM_ZOOM_MIN:  Vector2 = Vector2(0.05, 0.05)
const CAM_ZOOM_MAX:  Vector2 = Vector2(8.0, 8.0)

const LOST_HEAVEN_HUB := Vector3(4749.0, 0.0, -737.0)
const LOST_HEAVEN_ZOOM: Vector2 = Vector2(3.0, 3.0)
const FOCUS_ZOOM: Vector2 = Vector2(2.0, 2.0)
const HUMAN_CFG := "res://config/human_player.json"

@export var allow_demo_fallback: bool = false
@export var camera_free_pan: bool = true
@export var show_debug_hud: bool = false
@export var show_login_on_start: bool = true

var _cam_target:   Vector2 = Vector2.ZERO
var _play_mode:    bool    = false
var _frame_count:  int     = 0
var _planet_name:  String  = ""
var _loco_state:   String  = "STANDING"
var _is_connected: bool    = false
var _snapshot_live: bool   = false
var _udp_live:     bool    = false
var _ws_live:      bool    = false
var _ws_handoff_busy: bool = false
var _last_ws_url:  String  = ""
var _local_character_name: String = ""
var _online_players: Array = []
var _selected_entity_id: int = 0
var _world_entry_done: bool = false
var _possessed_id: int = 0
var _beast_telegraph_seen: Dictionary = {}

# Accesseurs de compatibilité pour sous-modules et vues externes
var _echo_controller: Node:
	get: return quest_ops.echo_controller if quest_ops else null
var _initiation_controller: Node:
	get: return quest_ops.initiation_controller if quest_ops else null
var _dialogue_bridge: Node:
	get: return ui_dialogue.dialogue_bridge if ui_dialogue else null
var _wiki_panel: Node:
	get: return gameplay_ops.wiki_panel if gameplay_ops else null
var _salvage_http: HTTPRequest:
	get: return gameplay_ops.salvage_http if gameplay_ops else null
var _hunt_http: HTTPRequest:
	get: return gameplay_ops.hunt_http if gameplay_ops else null
var _density_http: HTTPRequest:
	get: return gameplay_ops.density_http if gameplay_ops else null
var _hub_chat_root: Control:
	get: return ui_dialogue.hub_chat_root if ui_dialogue else null


func _ready() -> void:
	add_to_group("prime_main")
	_init_modules()

	if hotbar and hotbar.has_signal("slot_activated"):
		hotbar.slot_activated.connect(_on_hotbar_slot)
	if hotbar and hotbar.has_signal("slot_clicked"):
		hotbar.slot_clicked.connect(_on_hotbar_slot)

	if _creation_panel and _creation_panel.has_signal("character_created"):
		_creation_panel.character_created.connect(_on_second_character_created_in_game)

	net_world.wire_login_ws()
	quest_ops.wire_m10_craft_inventory()
	quest_ops.wire_mission_board()
	ui_dialogue.ensure_dialogue_bridge()

	_focus_lost_heaven_hub()
	_maybe_demo_spawn()
	_ensure_wiki_panel()
	_apply_debug_hud()
	_log_build_info()
	_update_info()


func _init_modules() -> void:
	gameplay_ops = _GameplayOpsScript.new()
	quest_ops = _QuestOpsScript.new()
	net_world = _NetWorldScript.new()
	ui_dialogue = _UiDialogueScript.new()

	gameplay_ops.setup(self)
	quest_ops.setup(self)
	net_world.setup(self)
	ui_dialogue.setup(self)


func _process(delta: float) -> void:
	_handle_camera_move(delta)
	_frame_count += 1
	if _frame_count % 60 == 0:
		_update_info()


func _handle_camera_move(delta: float) -> void:
	if camera == null or _play_mode or not camera_free_pan:
		return
	var dir := Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_Z) or Input.is_physical_key_pressed(KEY_W):
		dir.y -= 1.0
	if Input.is_physical_key_pressed(KEY_S):
		dir.y += 1.0
	if Input.is_physical_key_pressed(KEY_Q) or Input.is_physical_key_pressed(KEY_A):
		dir.x -= 1.0
	if Input.is_physical_key_pressed(KEY_D):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_EQUAL):
		_zoom_camera(CAM_ZOOM_STEP * delta * 4.0)
	if Input.is_key_pressed(KEY_MINUS):
		_zoom_camera(-CAM_ZOOM_STEP * delta * 4.0)
	if dir != Vector2.ZERO:
		camera.position += dir.normalized() * CAM_SPEED * delta / camera.zoom.x


func _zoom_camera(step: float) -> void:
	if camera == null:
		return
	camera.zoom = (camera.zoom + Vector2(step, step)).clamp(CAM_ZOOM_MIN, CAM_ZOOM_MAX)


func _unhandled_input(event: InputEvent) -> void:
	if ui_dialogue:
		ui_dialogue.unhandled_input(event)


func _canvas_mouse_pos() -> Vector2:
	return get_global_mouse_position()


func _screen_click_to_core3(canvas_pos: Vector2) -> Vector3:
	return _Projection3D2D.from_screen(canvas_pos)


func _player_world_xz() -> Vector2:
	var pc: Node = get_node_or_null("PlayerController")
	if pc == null or not pc.has_method("get_player_id"):
		return Vector2.INF
	var pid: int = int(pc.get_player_id())
	if pid == 0:
		return Vector2.INF
	if entity_manager == null or not entity_manager.has_method("get_entity"):
		return Vector2.INF
	var e: Node = entity_manager.get_entity(pid)
	if e == null:
		return Vector2.INF
	var p: Vector3 = e.get("core3_pos")
	return Vector2(p.x, p.z)


func _set_selected_entity(oid: int) -> void:
	if _selected_entity_id == oid:
		return
	if _selected_entity_id != 0:
		var prev: Node = entity_manager.get_entity(_selected_entity_id)
		if prev:
			prev.set_selected(false)
	_selected_entity_id = oid
	if oid == 0:
		return
	var e: Node = entity_manager.get_entity(oid)
	if e:
		e.set_selected(true)


func _handle_world_left_click(screen_pos: Vector2) -> void:
	var picked: Node = entity_manager.pick_entity_at_screen(screen_pos)
	if picked:
		_set_selected_entity(picked.object_id)
		if picked.is_interactable():
			_open_npc_dialogue(picked)
		elif str(picked.kind) == "player":
			_open_player_inspect(picked)
		elif _dialogue_panel and _dialogue_panel.visible:
			_dialogue_panel.hide_portrait()
		return
	_set_selected_entity(0)
	if _dialogue_panel and _dialogue_panel.visible:
		_dialogue_panel.hide_portrait()
	var pc: Node = get_node_or_null("PlayerController")
	if pc == null or not pc.enabled or not _play_mode:
		return
	var core3: Vector3 = _screen_click_to_core3(screen_pos)
	var pid: int = int(pc.get_player_id())
	if pid <= 0:
		return
	var me: Node = entity_manager.get_entity(pid)
	if me:
		core3.y = me.core3_pos.y
		var zones: Node = get_node_or_null("WorldMap/ZoneLayers")
		if zones:
			core3 = zones.clamp_move(me.core3_pos, core3)
	pc.request_move_to(core3.x, core3.z)


func _open_player_inspect(entity: Node) -> void:
	if entity == null or _dialogue_panel == null:
		return
	if ui_dialogue:
		ui_dialogue.dialogue_world_npc_id = ""
		ui_dialogue.dialogue_npc_name = ""
		ui_dialogue.dialogue_npc_role = ""
		ui_dialogue.dialogue_demo_expression_index = 0
	var speaker: String = str(entity.get_display_name())
	var is_self := false
	var pc: Node = get_node_or_null("PlayerController")
	if pc and pc.get_player_id() == entity.object_id:
		is_self = true
	var body := "%s — personnage joueur." % speaker
	if is_self or (_local_character_name != "" and speaker.to_lower() == _local_character_name.to_lower()):
		body = "%s — ton personnage (toi)." % speaker
	_dialogue_panel.show_portrait(
		speaker,
		"player",
		"neutral",
		body,
		entity.entity_key if entity.entity_key != "" else "player:human",
		false
	)
	_hotbar_feedback("Portrait %s" % speaker)


func _update_info() -> void:
	if camera == null or not show_debug_hud:
		return
	var center := camera.get_screen_center_position()
	var core3 := _hud_reference_core3(center)
	if info_label:
		var mode := "PLAY" if _play_mode else ("WS LIVE" if _ws_live else ("UDP LIVE" if _udp_live else ("PRIME" if _snapshot_live else "ATTENTE")))
		var players: int = int(entity_manager.count())
		var me := _local_character_name if _local_character_name != "" else "?"
		var online_n := _online_players.size()
		var ws_hint := "  |  %s" % _last_ws_url if _last_ws_url != "" else ""
		var online_hint := "  |  online:%d (%s)" % [online_n, me] if online_n > 0 else ""
		info_label.text = (
			"Prime Client v0.2  |  %s  |  Entités: %d%s%s\n" % [mode, players, ws_hint, online_hint] +
			"Zoom: %.2fx   %s" % [camera.zoom.x, _Projection3D2D.format_hud_coordinates(core3, false)]
		)
	if stats_label:
		if _play_mode:
			stats_label.text = "[ZQSD/flèches] move · clic sol · [T/I] panels · [L] labels · [1-0] hotbar"
		else:
			stats_label.text = "[H/R] hub  [M] minimap  [Ctrl+M] carte  [L] labels  [1-0] hotbar"


func _hud_reference_core3(cam_screen: Vector2) -> Vector3:
	var pc: Node = get_node_or_null("PlayerController")
	if pc and pc.has_method("get_player_id") and bool(pc.get("enabled")):
		var oid: int = int(pc.call("get_player_id"))
		if oid > 0:
			var e: Node = entity_manager.get_entity(oid)
			if e and "core3_pos" in e:
				return _Projection3D2D.normalize_core3_pos(e.core3_pos as Vector3)
	return _Projection3D2D.normalize_core3_pos(_Projection3D2D.from_screen(cam_screen))


func on_data_transform(object_id: int, x: float, y: float, z: float) -> void:
	entity_manager.move(object_id, Vector3(x, y, z))


func on_object_destroy(object_id: int) -> void:
	entity_manager.despawn(object_id)


func on_zone_change() -> void:
	entity_manager.clear()
	_is_connected = false


func on_mirror_udp_active() -> void:
	_udp_live = true
	_snapshot_live = true
	_update_info()


func on_snapshot_feed_active() -> void:
	if _hub_runtime_enabled():
		return
	_snapshot_live = true
	_update_info()
	call_deferred("_focus_lost_heaven_hub")
	print("[Main] flux snapshot actif — Ctrl+H hub · F1/F2/F3 bots")


func _focus_bot(name: String) -> bool:
	if camera == null:
		return false
	var oid: int = _Crc32Util.entity_oid("player:%s" % name)
	var e: Node = entity_manager.get_entity(oid)
	if e == null:
		print("[Main] focus %s : absent — lance run_m3_mirror.sh ?" % name)
		return false
	camera.position = e.position
	camera.zoom = FOCUS_ZOOM
	_cam_target = e.position
	print("[Main] focus %s" % name)
	return true


func _focus_first_bot() -> void:
	for name in ["Lia", "Nix", "Mira"]:
		if _focus_bot(name):
			return


func on_player_connected(obj_id: int, planet: String) -> void:
	_possess_local_player(obj_id, planet, true)
	if not _world_entry_done:
		net_world.on_world_entered(obj_id, planet)
	print("[Main] Joueur humain 0x%016x connecté sur %s (name=%s)" % [obj_id, planet, _local_character_name])


func _possess_local_player(obj_id: int, planet: String, force_camera: bool = false) -> void:
	if obj_id <= 0:
		return
	var first := _possessed_id != obj_id
	_possessed_id = obj_id
	_is_connected = true
	_play_mode = true
	camera_free_pan = false
	_ws_handoff_busy = false
	if planet != "":
		_planet_name = planet
	var pc: Node = get_node_or_null("PlayerController")
	if pc:
		pc.enabled = true
		pc.set_player_id(obj_id)
	var sb := get_node_or_null("SnapshotBridge")
	if sb and sb.has_method("set_paused"):
		sb.call("set_paused", true)
	if first:
		_despawn_local_player_ghosts(obj_id)
	var wm: Node = get_node_or_null("WorldMap")
	if wm and planet != "":
		wm.set_planet(planet.to_lower())
	var cfg := _load_human_cfg()
	if first and bool(cfg.get("hide_npc_nameplates_on_play", true)):
		_EntityScript.show_nameplates = false
		for e in entity_manager.get_all_entities():
			if e:
				e.queue_redraw()
	if _hub_runtime_enabled():
		_EntityScript.show_nameplates = true
		for e in entity_manager.get_all_entities():
			if e and e.has_method("set_force_nameplate"):
				e.call("set_force_nameplate", true)
				e.queue_redraw()
	if (first or force_camera) and bool(cfg.get("auto_focus_on_connect", true)):
		var e: Node = entity_manager.get_entity(obj_id)
		if e and camera:
			camera.position = e.position
			var zf := float(cfg.get("play_zoom", 2.2))
			camera.zoom = Vector2(zf, zf)
			_cam_target = e.position
	if first and bool(cfg.get("walk_home_on_far", true)):
		_maybe_walk_local_to_hub(obj_id)
	if first:
		call_deferred("_ensure_companion_visible")
	if first:
		_refresh_connection_hud()
	_update_info()


func _refresh_connection_hud() -> void:
	if state_label == null:
		return
	if not _hub_runtime_enabled() and not _ws_live:
		return
	var me := _local_character_name if _local_character_name != "" else "Voyageur"
	var n := _online_players.size()
	if n <= 0 and _is_connected:
		n = 1
	var others: PackedStringArray = PackedStringArray()
	for p: Variant in _online_players:
		if not p is Dictionary:
			continue
		var nm := str((p as Dictionary).get("name", "")).strip_edges()
		if nm == "" or nm.to_lower() == me.to_lower():
			continue
		others.append(nm)
	var extra := " · +" + ", ".join(others) if others.size() > 0 else ""
	if _hub_runtime_enabled():
		state_label.text = "CONNECTED · %s · %d joueur%s%s" % [me, max(n, 1), "s" if n > 1 else "", extra]
	elif _ws_live:
		state_label.text = "CONNECTED · %s" % me
	state_label.add_theme_color_override("font_color", Color(0.45, 1.0, 0.55, 1))


func _ensure_companion_visible() -> void:
	if _hub_runtime_enabled():
		var cfg_h := _load_human_cfg()
		var bot := str(cfg_h.get("companion_bot_id", "Nix")).strip_edges()
		var key_want := ("player:%s" % bot).to_lower()
		for e in entity_manager.get_all_entities():
			if e == null:
				continue
			var lab := str(e.label_text).strip_edges().to_lower()
			var ekey := str(e.entity_key).strip_edges().to_lower()
			if lab == bot.to_lower() or ekey == key_want or ekey.ends_with(":" + bot.to_lower()):
				if e.has_method("set_force_nameplate") and bool(cfg_h.get("companion_force_nameplate", true)):
					e.call("set_force_nameplate", true)
					e.queue_redraw()
				print("[Main] C3 companion live nameplate → %s" % bot)
				return
		return
	var cfg := _load_human_cfg()
	if not bool(cfg.get("spawn_companion", false)):
		return
	var bot_id := str(cfg.get("companion_bot_id", "Nix")).strip_edges()
	if bot_id.is_empty():
		bot_id = "Nix"
	var entity_key := "player:%s" % bot_id
	var force_np := bool(cfg.get("companion_force_nameplate", true))
	var found: Node = null
	for e in entity_manager.get_all_entities():
		if e == null:
			continue
		var key := str(e.entity_key).strip_edges()
		var label := str(e.label_text).strip_edges()
		if key == entity_key or label.to_lower() == bot_id.to_lower():
			found = e
			break
	if found == null:
		var stub_oid := 900001
		var x := float(cfg.get("companion_stub_x", 4758.0))
		var y := float(cfg.get("companion_stub_y", 0.15))
		var z := float(cfg.get("companion_stub_z", -545.0))
		found = entity_manager.spawn(
			stub_oid,
			Vector3(x, y, z),
			Color(0.0, 0.9, 0.4, 1.0),
			bot_id,
			"player",
			entity_key
		)
		if found:
			print("[Main] C3 companion stub spawn %s at (%.0f, %.0f)" % [entity_key, x, z])
	if found and force_np and found.has_method("set_force_nameplate"):
		found.call("set_force_nameplate", true)
		found.queue_redraw()
		print("[Main] C3 companion nameplate on %s" % entity_key)


func _maybe_walk_local_to_hub(obj_id: int) -> void:
	var e: Node = entity_manager.get_entity(obj_id)
	if e == null:
		return
	var hub := LOST_HEAVEN_HUB
	var dx: float = e.core3_pos.x - hub.x
	var dz: float = e.core3_pos.z - hub.z
	if absf(e.core3_pos.x) < 50.0 and absf(e.core3_pos.z) < 50.0:
		entity_manager.move(obj_id, Vector3(hub.x, 0.15, hub.z))
		if camera:
			var e2: Node = entity_manager.get_entity(obj_id)
			if e2:
				camera.position = e2.position
				_cam_target = e2.position
		var pc0: Node = get_node_or_null("PlayerController")
		if pc0 and pc0.has_method("send_initial_position"):
			pc0.send_initial_position(hub.x, 0.15, hub.z)
		print("[Main] rescue spawn Lost Heaven (était en 0,0)")
		return
	var far_m := 400.0
	var cfg := _load_human_cfg()
	far_m = float(cfg.get("walk_home_far_m", far_m))
	if dx * dx + dz * dz < far_m * far_m:
		return
	var pc: Node = get_node_or_null("PlayerController")
	if pc and pc.has_method("request_move_to"):
		pc.request_move_to(hub.x, hub.z)
		print("[Main] marche vers Lost Heaven (%.0f, %.0f) — pas de téléport" % [hub.x, hub.z])


func _despawn_local_player_ghosts(your_id: int) -> void:
	var names: Array[String] = []
	if _local_character_name != "":
		names.append(_local_character_name.to_lower())
	names.append("vous (godot)")
	names.append("voyageur")
	var to_kill: Array[int] = []
	for e in entity_manager.get_all_entities():
		if e == null or int(e.object_id) == your_id:
			continue
		if quest_ops and quest_ops.echo_controller and e.object_id == int(quest_ops.echo_controller.echo_object_id()):
			continue
		if str(e.entity_key).begins_with("player:echo") or str(e.kind) != "player":
			continue
		var label := str(e.label_text).strip_edges().to_lower()
		var key := str(e.entity_key).strip_edges().to_lower()
		var hit := false
		for n in names:
			if n == "":
				continue
			if label.begins_with(n) or key == ("player:%s" % n) or key.ends_with(":%s" % n):
				hit = true
				break
		if hit:
			to_kill.append(int(e.object_id))
	for oid in to_kill:
		entity_manager.despawn(oid)
		print("[Main] ghost joueur despawn oid=%d" % oid)


func _load_human_cfg() -> Dictionary:
	if not FileAccess.file_exists(HUMAN_CFG):
		return {}
	var f := FileAccess.open(HUMAN_CFG, FileAccess.READ)
	if f == null:
		return {}
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	return raw if raw is Dictionary else {}


func on_locomotion_state(state: String) -> void:
	_loco_state = state.to_upper()
	if state_label:
		state_label.text = _loco_state
		match _loco_state:
			"RUNNING":           state_label.add_theme_color_override("font_color", Color(0.4, 1.0, 0.4, 1))
			"JUMPING","FALLING": state_label.add_theme_color_override("font_color", Color(1.0, 0.9, 0.2, 1))
			"SWIMMING":          state_label.add_theme_color_override("font_color", Color(0.2, 0.8, 1.0, 1))
			"WALKING":           state_label.add_theme_color_override("font_color", Color(0.5, 1.0, 0.5, 1))
			_:                   state_label.add_theme_color_override("font_color", Color(0.4, 1.0, 0.5, 1))


func _log_build_info() -> void:
	const path := "res://assets/build_info.json"
	if not FileAccess.file_exists(path):
		print("[Main] build_info absent — sync J: via tools/sync_prime_client_to_j.sh")
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if raw is Dictionary:
		var d: Dictionary = raw
		var stamp := str(d.get("synced_at", "?"))
		var schema := int(d.get("map_config_schema", 0))
		print("[Main] prime-client build synced_at=%s map_schema=%d" % [stamp, schema])
		if info_label and OS.is_debug_build():
			info_label.text = "build %s · map v%d" % [stamp.substr(0, min(19, stamp.length())), schema]


# ===========================================================================
# Délégations publiques / passerelles transparentes
# ===========================================================================
func open_initiation_quest() -> void:
	quest_ops.open_initiation_quest()

func open_character_creation(from_menu: bool = false) -> void:
	quest_ops.open_character_creation(from_menu)

func _on_second_character_created_in_game(entry: Dictionary) -> void:
	quest_ops.on_second_character_created_in_game(entry)

func _ensure_wiki_panel() -> void:
	gameplay_ops.ensure_wiki_panel()

func _toggle_wiki() -> void:
	gameplay_ops.toggle_wiki()

func _ensure_salvage_http() -> void:
	gameplay_ops.ensure_salvage_http()

func _try_salvage_scrap() -> void:
	gameplay_ops.try_salvage_scrap()

func _try_hunt_yard() -> void:
	gameplay_ops.try_hunt_yard()

func _try_beast_engage(pos: Vector2) -> void:
	gameplay_ops.try_beast_engage(pos)

func _try_trade_offer(sku_id: String, offer_price: int) -> void:
	gameplay_ops.try_trade_offer(sku_id, offer_price)

func _prime_wahou_hunt_beat() -> void:
	gameplay_ops.prime_wahou_hunt_beat()

func _ensure_east_gate_hunt_waypoint() -> void:
	gameplay_ops.ensure_east_gate_hunt_waypoint()

func _apply_debug_hud() -> void:
	ui_dialogue.apply_debug_hud()

func _toggle_talents() -> void:
	ui_dialogue.toggle_talents()

func _toggle_inventory() -> void:
	ui_dialogue.toggle_inventory()

func _toggle_missions() -> void:
	ui_dialogue.toggle_missions()

func _toggle_game_menu() -> void:
	ui_dialogue.toggle_game_menu()

func _on_hotbar_slot(index: int) -> void:
	ui_dialogue.on_hotbar_slot(index)

func _hotbar_feedback(msg: String) -> void:
	if state_label:
		state_label.text = msg
		state_label.add_theme_color_override("font_color", Color(0.95, 0.82, 0.45, 1))

func _ensure_hub_chat_ui() -> void:
	ui_dialogue.ensure_hub_chat_ui()

func _refresh_hub_chat_visibility() -> void:
	ui_dialogue.refresh_hub_chat_visibility()

func _focus_hub_chat_input() -> void:
	ui_dialogue.focus_hub_chat_input()

func _on_hub_chat_submitted(text: String) -> void:
	ui_dialogue.on_hub_chat_submitted(text)

func _on_hub_chat_received(from_name: String, text: String, from_oid: int, source: String = "human") -> void:
	ui_dialogue.on_hub_chat_received(from_name, text, from_oid, source)

func _append_hub_chat_line(from_name: String, text: String, source: String = "human") -> void:
	ui_dialogue.append_hub_chat_line(from_name, text, source)

func _toggle_dialogue_demo() -> void:
	ui_dialogue.toggle_dialogue_demo()

func _cycle_dialogue_expression() -> void:
	ui_dialogue.cycle_dialogue_expression()

func _open_npc_dialogue(entity: Node) -> void:
	ui_dialogue.open_npc_dialogue(entity)

func _on_dialogue_followup(text: String) -> void:
	ui_dialogue.on_dialogue_followup(text)

func _on_dialogue_suggestion_activated(move: Dictionary) -> void:
	ui_dialogue.on_dialogue_suggestion_activated(move)

func _on_dialogue_bridge_busy(busy: bool) -> void:
	ui_dialogue.on_dialogue_bridge_busy(busy)

func _on_dialogue_bridge_reply(ok: bool, reply: String, meta: Dictionary) -> void:
	ui_dialogue.on_dialogue_bridge_reply(ok, reply, meta)

func _on_ws_handoff_started(ws_url: String, character_id: int, session_token: String, ws: Node) -> void:
	net_world.on_ws_handoff_started(ws_url, character_id, session_token, ws)

func _on_enter_world_requested(ws_url: String, character_id: int, session_token: String) -> void:
	net_world.on_enter_world_requested(ws_url, character_id, session_token)

func _on_ws_zone_state(payload: Dictionary) -> void:
	net_world.on_ws_zone_state(payload)

func _focus_lost_heaven_hub() -> void:
	net_world.focus_lost_heaven_hub()

func _maybe_demo_spawn() -> void:
	net_world.maybe_demo_spawn()

func _hub_runtime_enabled() -> bool:
	return net_world.hub_runtime_enabled()
