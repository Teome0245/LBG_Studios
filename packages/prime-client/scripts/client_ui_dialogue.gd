# client_ui_dialogue.gd — Entrées utilisateur, Modales UI, Chat Hub & Dialogue PNJ
extends RefCounted

const _DialogueBridgeScript = preload("res://scripts/dialogue_bridge.gd")
const _NpcAnchorResolver = preload("res://scripts/npc_anchor_resolver.gd")
const _EntityScript = preload("res://scripts/entity.gd")

const HUB_CHAT_MAX_LINES := 8
const FOCUS_BOTS: Array[String] = ["Lia", "Nix", "Mira"]
const DIALOGUE_DEMO_EXPRESSIONS: Array[String] = [
	"neutral",
	"happy",
	"determined",
	"talk_1",
	"talk_2",
	"angry",
	"sad",
	"surprised",
]

var main: Node = null
var dialogue_bridge: Node = null
var dialogue_demo_expression_index: int = 0
var dialogue_world_npc_id: String = ""
var dialogue_npc_name: String = ""
var dialogue_npc_role: String = ""
var hub_chat_log: RichTextLabel = null
var hub_chat_input: LineEdit = null
var hub_chat_root: Control = null
var hub_chat_lines: PackedStringArray = PackedStringArray()


func setup(p_main: Node) -> void:
	main = p_main


func unhandled_input(event: InputEvent) -> void:
	if main == null:
		return
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			main._zoom_camera(main.CAM_ZOOM_STEP)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			main._zoom_camera(-main.CAM_ZOOM_STEP)
		elif event.button_index == MOUSE_BUTTON_LEFT:
			main._handle_world_left_click(main._canvas_mouse_pos())
			main.get_viewport().set_input_as_handled()
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_F1:
				main._focus_bot("Lia")
			KEY_F2:
				main._focus_bot("Nix")
			KEY_F3:
				main._focus_bot("Mira")
			KEY_H:
				if main.quest_ops:
					main.quest_ops.toggle_echo_hammat()
			KEY_R:
				if main.net_world:
					main.net_world.focus_lost_heaven_hub()
			KEY_F:
				var e: Node = main.entity_manager.get_entity(0x0000_0001_0000_0002)
				if e and main.camera:
					main.camera.position = e.position
			KEY_T:
				toggle_talents()
			KEY_I:
				toggle_inventory()
			KEY_J:
				toggle_missions()
			KEY_P:
				if main.net_world and main.net_world.hub_runtime_enabled():
					if main._dialogue_panel and main._dialogue_panel.get("visible") and main._dialogue_panel.has_method("hide_portrait"):
						main._dialogue_panel.hide_portrait()
					focus_hub_chat_input()
				else:
					toggle_dialogue_demo()
			KEY_O:
				cycle_dialogue_expression()
			KEY_L:
				_EntityScript.toggle_nameplates()
				for e in main.entity_manager.get_all_entities():
					if e:
						e.queue_redraw()
				print("[Main] nameplates=%s" % _EntityScript.show_nameplates)
			KEY_ENTER, KEY_KP_ENTER:
				if main.net_world and main.net_world.hub_runtime_enabled():
					if main._dialogue_panel and main._dialogue_panel.get("visible") and main._dialogue_panel.has_method("hide_portrait"):
						main._dialogue_panel.hide_portrait()
					focus_hub_chat_input()
					main.get_viewport().set_input_as_handled()
			KEY_F9:
				main.show_debug_hud = not main.show_debug_hud
				apply_debug_hud()
			KEY_ESCAPE:
				if hub_chat_input and hub_chat_input.has_focus():
					hub_chat_input.release_focus()
					hub_chat_input.text = ""
					main.get_viewport().set_input_as_handled()
					return
				if main._game_menu and main._game_menu.get("visible") and main._game_menu.has_method("close_menu"):
					main._game_menu.close_menu()
				elif main._mission_board and main._mission_board.get("visible") and main._mission_board.has_method("toggle"):
					main._mission_board.toggle()
				elif main._talents_panel and main._talents_panel.get("visible") and main._talents_panel.has_method("toggle"):
					main._talents_panel.toggle()
				elif main.inventory_panel and main.inventory_panel.get("visible") and main.inventory_panel.has_method("toggle"):
					main.inventory_panel.toggle()
				elif main._login_panel and main._login_panel.visible and main._is_connected:
					main._login_panel.visible = false
				elif main._login_panel and not main._login_panel.visible and not main._is_connected:
					main._login_panel.visible = true
				elif main._game_menu and main._game_menu.has_method("toggle"):
					main._game_menu.toggle()
				else:
					main.get_tree().quit()
			KEY_F10:
				if main._login_panel:
					main._login_panel.visible = not main._login_panel.visible


func apply_debug_hud() -> void:
	if main == null:
		return
	var info := main.get_node_or_null("UI/HudLayer/InfoPanel") as Control
	if info:
		info.visible = main.show_debug_hud


func toggle_talents() -> void:
	if main and main._talents_panel:
		main._talents_panel.toggle()


func toggle_inventory() -> void:
	if main and main.inventory_panel:
		main.inventory_panel.toggle()


func toggle_missions() -> void:
	if main and main._mission_board:
		main._mission_board.toggle()


func toggle_game_menu() -> void:
	if main and main._game_menu:
		main._game_menu.toggle()


func on_hotbar_slot(index: int) -> void:
	if main == null:
		return
	match index:
		0:
			var pos: Vector2 = main._player_world_xz()
			if pos == Vector2.INF:
				main._hotbar_feedback("Attaque — position joueur inconnue")
				return
			if main.gameplay_ops == null:
				return
			var d_salvage := pos.distance_to(main.gameplay_ops.salvage_poi_xz)
			var d_hunt := pos.distance_to(main.gameplay_ops.hunt_poi_xz)
			var near_salvage: bool = d_salvage <= main.gameplay_ops.SALVAGE_RADIUS_M
			var near_hunt: bool = d_hunt <= main.gameplay_ops.HUNT_RADIUS_M
			if near_salvage and near_hunt:
				if d_hunt <= d_salvage:
					main.gameplay_ops.try_hunt_yard()
				else:
					main.gameplay_ops.try_salvage_scrap()
			elif near_hunt:
				main.gameplay_ops.try_hunt_yard()
			elif near_salvage:
				main.gameplay_ops.try_salvage_scrap()
			else:
				main.gameplay_ops.try_beast_engage(pos)
		1:
			main._hotbar_feedback("Compétence — à brancher")
		2:
			main._hotbar_feedback("Objet rapide — à brancher")
		3:
			main._hotbar_feedback("Emote — à brancher")
		4:
			var map_panel: Node = main.get_node_or_null("UI/ModalLayer/PlanetMapPanel")
			if map_panel and map_panel.has_method("toggle_map"):
				map_panel.call("toggle_map")
				main._hotbar_feedback("Carte planétaire")
		5:
			toggle_talents()
			main._hotbar_feedback("Talents / craft")
		6:
			toggle_inventory()
			main._hotbar_feedback("Inventaire")
		7:
			if main._dialogue_panel and main._dialogue_panel.get("visible") and main._dialogue_panel.has_method("hide_portrait"):
				main._dialogue_panel.hide_portrait()
			focus_hub_chat_input()
			main._hotbar_feedback("Chat — Entrée pour parler")
		8:
			main._hotbar_feedback("Monture — à brancher")
		9:
			toggle_game_menu()
			main._hotbar_feedback("Menu")
		_:
			main._hotbar_feedback("Slot %d" % index)


func ensure_hub_chat_ui() -> void:
	if hub_chat_root != null and is_instance_valid(hub_chat_root):
		return
	if main == null:
		return
	var hud := main.get_node_or_null("UI/HudLayer") as Control
	if hud == null:
		return
	var root := PanelContainer.new()
	root.name = "HubChatPanel"
	root.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	root.offset_left = 8.0
	root.offset_top = -220.0
	root.offset_right = 420.0
	root.offset_bottom = -72.0
	root.mouse_filter = Control.MOUSE_FILTER_STOP
	var vbox := VBoxContainer.new()
	vbox.name = "VBox"
	root.add_child(vbox)
	var log := RichTextLabel.new()
	log.name = "ChatLog"
	log.bbcode_enabled = true
	log.fit_content = false
	log.scroll_following = true
	log.custom_minimum_size = Vector2(0, 120)
	log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	log.add_theme_font_size_override("normal_font_size", 13)
	log.text = "[center][color=#8899aa]Chat hub — Entrée[/color][/center]"
	vbox.add_child(log)
	var inp := LineEdit.new()
	inp.name = "ChatInput"
	inp.placeholder_text = "Dire quelque chose…"
	inp.max_length = 200
	inp.clear_button_enabled = true
	inp.text_submitted.connect(on_hub_chat_submitted)
	vbox.add_child(inp)
	hud.add_child(root)
	hub_chat_root = root
	hub_chat_log = log
	hub_chat_input = inp
	refresh_hub_chat_visibility()


func refresh_hub_chat_visibility() -> void:
	if hub_chat_root == null or main == null:
		return
	if not hub_chat_root.visible and main.net_world and main.net_world.hub_runtime_enabled():
		hub_chat_root.visible = true


func focus_hub_chat_input() -> void:
	ensure_hub_chat_ui()
	if hub_chat_root:
		hub_chat_root.visible = true
	refresh_hub_chat_visibility()
	if hub_chat_input == null:
		push_warning("[Main] HubChat input absent")
		return
	hub_chat_input.grab_focus()


func on_hub_chat_submitted(text: String) -> void:
	var t := text.strip_edges()
	if hub_chat_input:
		hub_chat_input.text = ""
		hub_chat_input.release_focus()
	if t.is_empty() or main == null:
		return
	if main._ws and main._ws.has_method("send_chat") and main._ws_live:
		main._ws.call("send_chat", t)
	else:
		append_hub_chat_line("toi", t)


func on_hub_chat_received(from_name: String, text: String, _from_oid: int, source: String = "human") -> void:
	append_hub_chat_line(from_name, text, source)


func append_hub_chat_line(from_name: String, text: String, source: String = "human") -> void:
	ensure_hub_chat_ui()
	refresh_hub_chat_visibility()
	var who := from_name.strip_edges()
	if who.is_empty():
		who = "?"
	var safe := text.replace("[", "(").replace("]", ")")
	var src := source.strip_edges().to_lower()
	var line: String
	if src == "ia":
		line = "[color=#5ec8a8][b]%s[/b][/color]: %s" % [who, safe]
	elif src == "system":
		line = "[color=#8899aa]%s[/color]" % safe
	else:
		line = "[color=#c9d4e8][b]%s[/b][/color]: %s" % [who, safe]
	hub_chat_lines.append(line)
	while hub_chat_lines.size() > HUB_CHAT_MAX_LINES:
		hub_chat_lines.remove_at(0)
	if hub_chat_log:
		hub_chat_log.text = "\n".join(hub_chat_lines)


func toggle_dialogue_demo() -> void:
	if main == null or main._dialogue_panel == null:
		return
	if main._dialogue_panel.visible:
		main._dialogue_panel.hide_portrait()
		return
	var expr: String = DIALOGUE_DEMO_EXPRESSIONS[dialogue_demo_expression_index % DIALOGUE_DEMO_EXPRESSIONS.size()]
	main._dialogue_panel.show_portrait(
		"Odo le guide",
		"npc",
		expr,
		"Bienvenue à Lost Heaven. Le portrait dialogue est en place ; il reste à brancher les vraies interactions PNJ.",
		"npc:odo_guide"
	)
	main._hotbar_feedback("Portrait %s" % expr)


func cycle_dialogue_expression() -> void:
	if main == null or main._dialogue_panel == null:
		return
	dialogue_demo_expression_index = (dialogue_demo_expression_index + 1) % DIALOGUE_DEMO_EXPRESSIONS.size()
	if not main._dialogue_panel.visible:
		return
	var expr: String = DIALOGUE_DEMO_EXPRESSIONS[dialogue_demo_expression_index]
	main._dialogue_panel.set_expression(expr)
	main._dialogue_panel.set_body_text("Expression active : %s" % expr)
	main._hotbar_feedback("Expression %s" % expr)


func open_npc_dialogue(entity: Node) -> void:
	if entity == null or main == null or main._dialogue_panel == null:
		return
	ensure_dialogue_bridge()
	var speaker: String = str(entity.get_display_name())
	var anchor: Dictionary = _NpcAnchorResolver.resolve(entity.entity_key, speaker)
	var role := str(anchor.get("role", ""))
	var world_npc_id := _NpcAnchorResolver.normalize_pilot_id(entity.entity_key)
	if world_npc_id.is_empty():
		world_npc_id = "npc:unknown"
	dialogue_world_npc_id = world_npc_id
	dialogue_npc_name = speaker
	dialogue_npc_role = role
	dialogue_demo_expression_index = 0
	main._dialogue_panel.show_portrait(
		speaker,
		entity.kind,
		"neutral",
		"…",
		entity.entity_key,
		true
	)
	main._hotbar_feedback("Interaction %s" % speaker)
	if dialogue_bridge == null or not bool(dialogue_bridge.call("is_enabled")):
		main._dialogue_panel.set_body_text(
			"%s\n\n(pont dialogue désactivé — stub)" % npc_dialogue_stub(role, speaker)
		)
		return
	if bool(dialogue_bridge.call("is_busy")):
		main._dialogue_panel.set_body_text("Un échange est déjà en cours…")
		main._dialogue_panel.set_chat_busy(true)
		return
	dialogue_bridge.call("touch_npc", speaker, world_npc_id)
	dialogue_bridge.call("update_session", {"last_npc": speaker})
	main._dialogue_panel.set_chat_busy(true)
	var ok: bool = bool(
		dialogue_bridge.call(
			"request_npc_reply",
			"",
			world_npc_id,
			speaker,
			"prime:%s" % (main._local_character_name if main._local_character_name != "" else "client")
		)
	)
	if not ok:
		main._dialogue_panel.set_chat_busy(false)
		main._dialogue_panel.set_body_text(
			"Impossible de joindre le Pilot (HTTP). Stub : %s" % npc_dialogue_stub(role, speaker)
		)


func on_dialogue_followup(text: String) -> void:
	if dialogue_bridge == null or main == null or main._dialogue_panel == null:
		return
	if dialogue_world_npc_id.is_empty():
		return
	if bool(dialogue_bridge.call("is_busy")):
		main._dialogue_panel.set_body_text("Un échange est déjà en cours…")
		return
	main._dialogue_panel.set_chat_busy(true)
	main._dialogue_panel.set_body_text("…")
	var ok: bool = bool(
		dialogue_bridge.call(
			"request_npc_reply",
			text,
			dialogue_world_npc_id,
			dialogue_npc_name,
			"prime:%s" % (main._local_character_name if main._local_character_name != "" else "client")
		)
	)
	if not ok:
		main._dialogue_panel.set_chat_busy(false)
		main._dialogue_panel.set_body_text(
			"Impossible d'envoyer la suite. Stub : %s"
			% npc_dialogue_stub(dialogue_npc_role, dialogue_npc_name)
		)


func on_dialogue_suggestion_activated(move: Dictionary) -> void:
	if move.is_empty() or main == null:
		return
	var kind := str(move.get("kind", "")).strip_edges().to_lower()
	if kind != "ui":
		return
	var action: Variant = move.get("action", {})
	var action_name := ""
	var action_dict: Dictionary = {}
	if action is Dictionary:
		action_dict = action
		action_name = str(action_dict.get("name", "")).strip_edges()
	if action_name == "open_mission_board":
		if main._mission_board and main._mission_board.has_method("toggle"):
			if not bool(main._mission_board.get("visible")):
				main._mission_board.toggle()
			print("[Main] C1 suggestion UI → open_mission_board")
		return
	if action_name == "open_wiki":
		if main.gameplay_ops:
			main.gameplay_ops.toggle_wiki()
		return
	if action_name == "trade_offer":
		if main.gameplay_ops:
			main.gameplay_ops.try_trade_offer(
				str(action_dict.get("sku_id", "")),
				int(action_dict.get("offer_price", 0))
			)
		return
	if action_name == "tip_stage":
		if main._mission_board and main._mission_board.has_method("_tip_scene"):
			main._mission_board._tip_scene()
			print("[Main] C1 suggestion UI → tip_stage")
		return
	if action_name == "show_train":
		if main._mission_board and main._mission_board.has_method("request_show_train"):
			main._mission_board.request_show_train()
			print("[Main] C1 suggestion UI → show_train")
		return


func ensure_dialogue_bridge() -> void:
	if dialogue_bridge != null and is_instance_valid(dialogue_bridge):
		return
	if main == null:
		return
	dialogue_bridge = _DialogueBridgeScript.new()
	dialogue_bridge.name = "DialogueBridge"
	main.add_child(dialogue_bridge)
	if dialogue_bridge.has_signal("reply_ready"):
		dialogue_bridge.reply_ready.connect(on_dialogue_bridge_reply)
	if dialogue_bridge.has_signal("busy_changed"):
		dialogue_bridge.busy_changed.connect(on_dialogue_bridge_busy)
	if main._dialogue_panel and main._dialogue_panel.has_signal("followup_submitted"):
		if not main._dialogue_panel.followup_submitted.is_connected(on_dialogue_followup):
			main._dialogue_panel.followup_submitted.connect(on_dialogue_followup)
	if main._dialogue_panel and main._dialogue_panel.has_signal("suggestion_clicked"):
		if not main._dialogue_panel.suggestion_clicked.is_connected(on_dialogue_followup):
			main._dialogue_panel.suggestion_clicked.connect(on_dialogue_followup)
	if main._dialogue_panel and main._dialogue_panel.has_signal("suggestion_activated"):
		if not main._dialogue_panel.suggestion_activated.is_connected(on_dialogue_suggestion_activated):
			main._dialogue_panel.suggestion_activated.connect(on_dialogue_suggestion_activated)


func on_dialogue_bridge_busy(busy: bool) -> void:
	if main and main._dialogue_panel and main._dialogue_panel.visible:
		main._dialogue_panel.set_chat_busy(busy)


func on_dialogue_bridge_reply(ok: bool, reply: String, meta: Dictionary) -> void:
	if main == null or main._dialogue_panel == null or not main._dialogue_panel.visible:
		return
	main._dialogue_panel.set_chat_busy(false)
	if ok and not reply.is_empty():
		main._dialogue_panel.set_body_text(reply)
		var moves: Variant = meta.get("suggested_moves", [])
		if moves is Array and main._dialogue_panel.has_method("set_suggested_moves"):
			main._dialogue_panel.call("set_suggested_moves", moves)
		elif main._dialogue_panel.has_method("clear_suggested_moves"):
			main._dialogue_panel.call("clear_suggested_moves")
		var eng := str(meta.get("lyra_engagement_resolved", ""))
		var turns := int(meta.get("history_turns", 0))
		if eng != "":
			main._hotbar_feedback("Persona %s · tours %d" % [eng, turns])
		return
	if main._dialogue_panel.has_method("clear_suggested_moves"):
		main._dialogue_panel.call("clear_suggested_moves")
	main._dialogue_panel.set_body_text(
		"Le pont dialogue est indisponible (%s). Réessaie plus tard." % str(meta.get("status", "?"))
	)


func npc_dialogue_stub(role: String, speaker: String) -> String:
	match role:
		"guide", "quest_giver", "archivist", "rumormonger":
			return "%s : bienvenue à Lost Heaven. Nous brancherons ici les vraies lignes de dialogue et les expressions." % speaker
		"bartender", "host", "performer", "patron", "cantina_fallback":
			return "%s : un portrait vivant type Warcraft 3 fonctionne bien pour les échanges courts et lisibles." % speaker
		"merchant", "resident":
			return "%s : le panneau dialogue est prêt ; il reste à relier l'inventaire, les quêtes ou le commerce." % speaker
		_:
			return "%s : interaction PNJ MVP active." % speaker
