# client_quest_ops.gd — Quêtes, Roster Echo Hammat, Craft & Progression joueur
extends RefCounted

const _EchoHammatControllerScript = preload("res://scripts/echo_hammat_controller.gd")
const _InitiationQuestControllerScript = preload("res://scripts/initiation_quest_controller.gd")

var main: Node = null
var echo_controller: Node = null
var initiation_controller: Node = null


func setup(p_main: Node) -> void:
	main = p_main


func wire_m10_craft_inventory() -> void:
	if main == null:
		return
	var talents = main._talents_panel
	var inv = main.inventory_panel
	if talents == null or inv == null:
		return
	if talents.has_signal("craft_completed"):
		if not talents.craft_completed.is_connected(on_m10_craft_completed):
			talents.craft_completed.connect(on_m10_craft_completed)


func wire_mission_board() -> void:
	if main == null or main._mission_board == null:
		return
	var mb = main._mission_board
	if mb.has_signal("quest_completed"):
		if not mb.quest_completed.is_connected(on_mission_completed):
			mb.quest_completed.connect(on_mission_completed)
	if mb.has_signal("quest_accepted"):
		if not mb.quest_accepted.is_connected(on_mission_accepted):
			mb.quest_accepted.connect(on_mission_accepted)


func on_mission_accepted(result: Dictionary) -> void:
	if main == null:
		return
	var title := str((result.get("accepted") or {}).get("title", "mission"))
	main._hotbar_feedback("Mission acceptée — %s" % title)


func on_mission_completed(result: Dictionary) -> void:
	if main == null:
		return
	var title := str(result.get("title", "mission"))
	var cr := int((result.get("reward_applied") or {}).get("credits_gained", 0))
	var ch = result.get("chronicle", {})
	if typeof(ch) == TYPE_DICTIONARY and int(ch.get("line_count", 0)) > 0:
		main._hotbar_feedback("Mission OK — %s (+%d Cr) · chronique Scribe prête" % [title, cr])
	else:
		main._hotbar_feedback("Mission OK — %s (+%d Cr)" % [title, cr])
	if main.inventory_panel and main.inventory_panel.has_method("refresh_inventory"):
		main.inventory_panel.refresh_inventory()
	# C5 — pousse un extrait chat hub si disponible.
	if typeof(ch) == TYPE_DICTIONARY:
		var lines = ch.get("lines", [])
		var ctitle := str(ch.get("title", "")).strip_edges()
		if typeof(lines) == TYPE_ARRAY and lines.size() > 0:
			var preview := str(lines[0])
			if not ctitle.is_empty():
				main._append_hub_chat_line("Scribe", "%s — %s" % [ctitle, preview], "ia")
			else:
				main._append_hub_chat_line("Scribe", preview, "ia")


func on_m10_craft_completed(result: Dictionary) -> void:
	if main == null:
		return
	if main.inventory_panel:
		if main.inventory_panel.has_method("toggle") and not bool(main.inventory_panel.get("visible")):
			main.inventory_panel.toggle()
		elif "visible" in main.inventory_panel:
			main.inventory_panel.visible = true
		if main.inventory_panel.has_method("apply_craft_result"):
			main.inventory_panel.apply_craft_result(result)
		elif main.inventory_panel.has_method("refresh_inventory"):
			main.inventory_panel.refresh_inventory()
	main._hotbar_feedback("Craft OK — inventaire mis à jour")


func ensure_echo_hammat() -> void:
	if echo_controller == null:
		echo_controller = _EchoHammatControllerScript.new()
		echo_controller.name = "EchoHammatController"
		main.add_child(echo_controller)
	if main._ws != null:
		echo_controller.bind_ws_client(main._ws)
	echo_controller.bind_world(main.entity_manager, main.get_node_or_null("PlayerController"))
	if main._echo_panel != null and main._echo_panel.has_method("bind_controller"):
		main._echo_panel.bind_controller(echo_controller)
	if echo_controller.has_signal("state_changed"):
		if not echo_controller.state_changed.is_connected(on_echo_state_changed):
			echo_controller.state_changed.connect(on_echo_state_changed)


func on_echo_state_changed(state: Dictionary) -> void:
	if initiation_controller == null:
		return
	var step: Dictionary = initiation_controller.get_current_step()
	if str(step.get("id", "")) != "invocation":
		return
	if str(state.get("echo_character_id", "")).is_empty():
		return
	if initiation_controller.has_method("mark_echo_practiced"):
		initiation_controller.mark_echo_practiced()
	if main._initiation_panel and main._initiation_panel.has_method("_paint_step"):
		main._initiation_panel.call("_paint_step")


func sync_echo_roster() -> void:
	if echo_controller == null or main == null:
		return
	var roster: Array = []
	var meta: Dictionary = {}
	if main._login_panel:
		if main._login_panel.has_method("get_account_roster"):
			roster = main._login_panel.call("get_account_roster")
		if main._login_panel.has_method("get_selected_character_meta"):
			meta = main._login_panel.call("get_selected_character_meta")
	var active_id := str(meta.get("character_id", meta.get("id", "")))
	var active_name := str(meta.get("name", main._local_character_name))
	echo_controller.set_roster(roster, active_id, active_name)


func toggle_echo_hammat() -> void:
	if main == null or main._echo_panel == null:
		return
	sync_echo_roster()
	if main._echo_panel.has_method("toggle"):
		main._echo_panel.toggle()


func ensure_initiation_quest() -> void:
	if initiation_controller == null:
		initiation_controller = _InitiationQuestControllerScript.new()
		initiation_controller.name = "InitiationQuestController"
		main.add_child(initiation_controller)
	if main._initiation_panel != null and main._initiation_panel.has_method("bind_controller"):
		main._initiation_panel.bind_controller(initiation_controller)
	if initiation_controller.has_signal("request_create_character"):
		if not initiation_controller.request_create_character.is_connected(on_initiation_create_character):
			initiation_controller.request_create_character.connect(on_initiation_create_character)
	if initiation_controller.has_signal("request_open_echo_panel"):
		if not initiation_controller.request_open_echo_panel.is_connected(on_initiation_open_echo):
			initiation_controller.request_open_echo_panel.connect(on_initiation_open_echo)
	if initiation_controller.has_signal("step_changed"):
		if not initiation_controller.step_changed.is_connected(on_initiation_step_changed):
			initiation_controller.step_changed.connect(on_initiation_step_changed)
	if initiation_controller.has_signal("quest_completed"):
		if not initiation_controller.quest_completed.is_connected(on_initiation_quest_completed):
			initiation_controller.quest_completed.connect(on_initiation_quest_completed)


func get_roster_size() -> int:
	if main and main._login_panel and main._login_panel.has_method("get_account_roster"):
		return (main._login_panel.call("get_account_roster") as Array).size()
	return 1


func count_hammat_characters() -> int:
	if main == null or main._login_panel == null or not main._login_panel.has_method("get_account_roster"):
		return 0
	var roster: Array = main._login_panel.call("get_account_roster")
	var n := 0
	for c in roster:
		if str(c.get("noyau_id", "")).strip_edges() != "":
			n += 1
	return n


func get_particule_info() -> Dictionary:
	if main and main._login_panel and main._login_panel.has_method("get_selected_character_meta"):
		return main._login_panel.call("get_selected_character_meta")
	return {}


func maybe_start_initiation_quest() -> void:
	if initiation_controller == null or main == null:
		return
	var hammat_n := count_hammat_characters()
	if not initiation_controller.should_auto_start(hammat_n):
		return
	var meta := get_particule_info()
	if main._initiation_panel and main._initiation_panel.has_method("set_particule_info"):
		main._initiation_panel.set_particule_info(
			str(meta.get("noyau_id", "")),
			str(meta.get("particule_seed", "")),
		)
	initiation_controller.start_quest()
	if main._initiation_panel:
		if main._initiation_panel.has_method("open_panel"):
			main._initiation_panel.open_panel()
		if main._initiation_panel.has_method("refresh_step"):
			main._initiation_panel.refresh_step()
		elif main._initiation_panel.has_method("_paint_step"):
			main._initiation_panel.call("_paint_step")


func open_initiation_quest() -> void:
	if initiation_controller == null or main == null:
		return
	if initiation_controller.is_done():
		return
	var meta := get_particule_info()
	if main._initiation_panel and main._initiation_panel.has_method("set_particule_info"):
		main._initiation_panel.set_particule_info(
			str(meta.get("noyau_id", "")),
			str(meta.get("particule_seed", "")),
		)
	if not bool(initiation_controller.active):
		initiation_controller.start_quest()
	if main._initiation_panel:
		if main._initiation_panel.has_method("open_panel"):
			main._initiation_panel.open_panel()
		if main._initiation_panel.has_method("refresh_step"):
			main._initiation_panel.refresh_step()


func open_character_creation(from_menu: bool = false) -> void:
	if main == null:
		return
	if main._login_panel and main._login_panel.has_method("open_character_creation_in_game"):
		main._login_panel.call("open_character_creation_in_game")
	elif main._creation_panel and main._creation_panel.has_method("open_panel"):
		main._creation_panel.call("open_panel", from_menu)


func on_initiation_step_changed(_step_id: String, _idx: int) -> void:
	if main and main._initiation_panel and main._initiation_panel.has_method("_paint_step"):
		main._initiation_panel.call("_paint_step")


func on_initiation_create_character() -> void:
	if main and main._login_panel and main._login_panel.has_method("open_character_creation_in_game"):
		main._login_panel.call("open_character_creation_in_game")


func on_initiation_open_echo() -> void:
	toggle_echo_hammat()


func on_initiation_quest_completed(_quest_id: String) -> void:
	if main and main.state_label:
		main.state_label.text = "Initiation terminée — Écho Amas débloqué"
	if main and main._initiation_panel and main._initiation_panel.has_method("close_panel"):
		main._initiation_panel.close_panel()


func on_second_character_created_in_game(entry: Dictionary) -> void:
	sync_echo_roster()
	if main and main._initiation_panel and main._initiation_panel.has_method("set_particule_info"):
		main._initiation_panel.set_particule_info(
			str(entry.get("noyau_id", "")),
			str(entry.get("particule_seed", "")),
		)
	if initiation_controller and initiation_controller.has_method("on_second_character_created"):
		initiation_controller.on_second_character_created()
	if main and main._initiation_panel and main._initiation_panel.has_method("_paint_step"):
		main._initiation_panel.call("_paint_step")
	restore_local_control()


func restore_local_control() -> void:
	if main == null:
		return
	var vp := main.get_viewport()
	if vp:
		vp.gui_release_focus()
	var pid: int = main._possessed_id
	var pc: Node = main.get_node_or_null("PlayerController")
	if pid <= 0 and pc and pc.has_method("get_player_id"):
		pid = int(pc.get_player_id())
	if pid <= 0 and main._ws != null and "your_character_id" in main._ws:
		pid = int(main._ws.your_character_id)
	if pid > 0:
		main._possess_local_player(pid, main._planet_name, true)
