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
const _SwgHamHudScript = preload("res://scripts/swg_ham_hud.gd")
const _SwgRadialMenuScript = preload("res://scripts/swg_radial_menu.gd")
const _SwgSkillsPanelScript = preload("res://scripts/swg_skills_panel.gd")
const _SwgSurveyPanelScript = preload("res://scripts/swg_survey_panel.gd")
const _SwgExperimentPanelScript = preload("res://scripts/swg_experiment_panel.gd")
const _SwgDatapadPanelScript = preload("res://scripts/swg_datapad_panel.gd")
const _SwgCharacterSheetScript = preload("res://scripts/swg_character_sheet.gd")
const _SwgBazaarPanelScript = preload("res://scripts/swg_bazaar_panel.gd")
const _SwgStructurePanelScript = preload("res://scripts/swg_structure_panel.gd")
const _SwgTargetFrameScript = preload("res://scripts/swg_target_frame.gd")
const _SwgChatBoxScript = preload("res://scripts/swg_chat_box.gd")
const _SwgCraftingScript = preload("res://scripts/swg_crafting_panel.gd")
const _SwgInventoryScript = preload("res://scripts/swg_inventory_paperdoll.gd")
const _SwgAudioSynthesizerScript = preload("res://scripts/swg_audio_synthesizer.gd")
const _SwgFactionSystemScript = preload("res://scripts/swg_faction_system.gd")
const _SwgFactionDialogScript = preload("res://scripts/swg_faction_dialog.gd")
const _SwgSpeciesSystemScript = preload("res://scripts/swg_species_system.gd")
const _SwgSpeciesDialogScript = preload("res://scripts/swg_species_dialog.gd")

var gameplay_ops: RefCounted = null
var quest_ops: RefCounted = null
var net_world: RefCounted = null
var ui_dialogue: RefCounted = null

var swg_ham_hud: Node = null
var swg_radial_menu: Node = null
var swg_skills_panel: Node = null
var swg_survey_panel: Node = null
var swg_experiment_panel: Node = null
var swg_datapad_panel: Node = null
var swg_character_sheet: Node = null
var swg_bazaar_panel: Node = null
var swg_structure_panel: Node = null
var swg_target_frame: Node = null
var swg_chat_box: Node = null
var swg_crafting_panel: Node = null
var swg_inventory_paperdoll: Node = null
var swg_audio: Node = null
var swg_faction_system: Node = null
var swg_faction_dialog: Node = null
var swg_species_dialog: Node = null
var _swg_action_http: HTTPRequest = null

const COLOR_PLAYER_OFFICIAL := Color(0.2, 0.4, 1.0, 1.0)
## Alias historique — même teinte que joueur officiel (C1).
const COLOR_PLAYER_BOT := Color(0.2, 0.4, 1.0, 1.0)
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
var _toast_label: Label = null
var _toast_timer: Timer = null

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
	if hotbar and hotbar.has_signal("item_assigned"):
		hotbar.item_assigned.connect(_on_hotbar_item_assigned)

	if _creation_panel and _creation_panel.has_signal("character_created"):
		_creation_panel.character_created.connect(_on_second_character_created_in_game)

	net_world.wire_login_ws()
	quest_ops.wire_m10_craft_inventory()
	quest_ops.wire_mission_board()
	ui_dialogue.ensure_dialogue_bridge()

	_focus_lost_heaven_hub()
	_maybe_demo_spawn()
	_ensure_wiki_panel()
	_ensure_swg_ui()
	_ensure_toast_ui()
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
		if swg_ham_hud and swg_ham_hud.has_method("set_target_entity"):
			swg_ham_hud.set_target_entity("")
		if swg_target_frame and swg_target_frame.has_method("clear_target"):
			swg_target_frame.clear_target()
		return
	var e: Node = entity_manager.get_entity(oid)
	if e:
		e.set_selected(true)
		if swg_ham_hud and swg_ham_hud.has_method("set_target_entity"):
			var t_name := str(e.get_display_name()) if e.has_method("get_display_name") else str(e.get("label_text"))
			var t_kind := str(e.get("kind"))
			var dist := -1.0
			var my_xz := _player_world_xz()
			if my_xz != Vector2.INF and "core3_pos" in e:
				var ep: Vector3 = e.core3_pos
				dist = my_xz.distance_to(Vector2(ep.x, ep.z))
			swg_ham_hud.set_target_entity(t_name, t_kind, dist)
		if swg_target_frame and swg_target_frame.has_method("set_target"):
			var pc: Node = get_node_or_null("PlayerController")
			var pid: int = int(pc.get_player_id()) if (pc and pc.has_method("get_player_id")) else 0
			var me: Node = entity_manager.get_entity(pid) if (entity_manager and pid > 0) else null
			swg_target_frame.set_target(e, me)


func _cycle_swg_target() -> void:
	if entity_manager == null or not entity_manager.has_method("get_all_entities"):
		return
	var entities: Array = entity_manager.get_all_entities()
	if entities.is_empty():
		return

	var pc: Node = get_node_or_null("PlayerController")
	var pid: int = int(pc.get_player_id()) if (pc and pc.has_method("get_player_id")) else 0
	var my_xz := _player_world_xz()

	var candidates: Array = []
	for ent in entities:
		if ent == null or not is_instance_valid(ent):
			continue
		var oid: int = int(ent.get("oid")) if "oid" in ent else 0
		if oid == pid or oid == 0:
			continue
		var dist := 9999.0
		if my_xz != Vector2.INF and "core3_pos" in ent:
			var ep: Vector3 = ent.core3_pos
			dist = my_xz.distance_to(Vector2(ep.x, ep.z))
		candidates.append({"oid": oid, "node": ent, "dist": dist})

	if candidates.is_empty():
		return

	candidates.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a["dist"]) < float(b["dist"])
	)

	var next_idx := 0
	for i in range(candidates.size()):
		if candidates[i]["oid"] == _selected_entity_id:
			next_idx = (i + 1) % candidates.size()
			break

	_set_selected_entity(candidates[next_idx]["oid"])
	if swg_audio and swg_audio.has_method("play_droid"):
		swg_audio.play_droid()


func _ensure_swg_ui() -> void:
	var hud_layer := get_node_or_null("UI/HudLayer") as Control
	var modal_layer := get_node_or_null("UI/ModalLayer") as Control
	var old_state := get_node_or_null("UI/HudLayer/StatePanel") as Control
	if old_state:
		old_state.visible = false
	if hud_layer and swg_ham_hud == null:
		swg_ham_hud = _SwgHamHudScript.new()
		swg_ham_hud.name = "SwgHamHud"
		swg_ham_hud.position = Vector2(12, 12)
		hud_layer.add_child(swg_ham_hud)
		if swg_ham_hud.has_signal("quick_panel_requested"):
			swg_ham_hud.quick_panel_requested.connect(_on_swg_quick_panel_requested)
	if hud_layer and swg_target_frame == null:
		swg_target_frame = _SwgTargetFrameScript.new()
		swg_target_frame.name = "SwgTargetFrame"
		swg_target_frame.target_cleared.connect(func() -> void:
			_set_selected_entity(0)
		)
		hud_layer.add_child(swg_target_frame)
	if hud_layer and swg_chat_box == null:
		swg_chat_box = _SwgChatBoxScript.new()
		swg_chat_box.name = "SwgChatBox"
		swg_chat_box.command_executed.connect(_on_swg_chat_command)
		hud_layer.add_child(swg_chat_box)
	if modal_layer and swg_inventory_paperdoll == null:
		swg_inventory_paperdoll = _SwgInventoryScript.new()
		swg_inventory_paperdoll.name = "SwgInventoryPaperdoll"
		swg_inventory_paperdoll.item_used.connect(_on_swg_inventory_item_used)
		modal_layer.add_child(swg_inventory_paperdoll)
	if modal_layer and swg_crafting_panel == null:
		swg_crafting_panel = _SwgCraftingScript.new()
		swg_crafting_panel.name = "SwgCraftingPanel"
		swg_crafting_panel.inventory_ref = swg_inventory_paperdoll
		modal_layer.add_child(swg_crafting_panel)
	if swg_audio == null:
		swg_audio = _SwgAudioSynthesizerScript.new()
		swg_audio.name = "SwgAudioSynthesizer"
		add_child(swg_audio)
	if modal_layer and swg_radial_menu == null:
		swg_radial_menu = _SwgRadialMenuScript.new()
		swg_radial_menu.name = "SwgRadialMenu"
		modal_layer.add_child(swg_radial_menu)
		swg_radial_menu.radial_action_selected.connect(_on_swg_radial_action)
	if modal_layer and swg_skills_panel == null:
		swg_skills_panel = _SwgSkillsPanelScript.new()
		swg_skills_panel.name = "SwgSkillsPanel"
		modal_layer.add_child(swg_skills_panel)
	if modal_layer and swg_survey_panel == null:
		swg_survey_panel = _SwgSurveyPanelScript.new()
		swg_survey_panel.name = "SwgSurveyPanel"
		modal_layer.add_child(swg_survey_panel)
	if modal_layer and swg_experiment_panel == null:
		swg_experiment_panel = _SwgExperimentPanelScript.new()
		swg_experiment_panel.name = "SwgExperimentPanel"
		modal_layer.add_child(swg_experiment_panel)
	if modal_layer and swg_datapad_panel == null:
		swg_datapad_panel = _SwgDatapadPanelScript.new()
		swg_datapad_panel.name = "SwgDatapadPanel"
		modal_layer.add_child(swg_datapad_panel)
	if modal_layer and swg_character_sheet == null:
		swg_character_sheet = _SwgCharacterSheetScript.new()
		swg_character_sheet.name = "SwgCharacterSheet"
		modal_layer.add_child(swg_character_sheet)
	if modal_layer and swg_bazaar_panel == null:
		swg_bazaar_panel = _SwgBazaarPanelScript.new()
		swg_bazaar_panel.name = "SwgBazaarPanel"
		modal_layer.add_child(swg_bazaar_panel)
	if modal_layer and swg_structure_panel == null:
		swg_structure_panel = _SwgStructurePanelScript.new()
		swg_structure_panel.name = "SwgStructurePanel"
		modal_layer.add_child(swg_structure_panel)
	if swg_faction_system == null:
		swg_faction_system = _SwgFactionSystemScript.new()
		add_child(swg_faction_system)
	if modal_layer and swg_faction_dialog == null:
		swg_faction_dialog = _SwgFactionDialogScript.new()
		swg_faction_dialog.name = "SwgFactionDialog"
		swg_faction_dialog.set_faction_system(swg_faction_system)
		modal_layer.add_child(swg_faction_dialog)
	if modal_layer and swg_species_dialog == null:
		swg_species_dialog = _SwgSpeciesDialogScript.new()
		swg_species_dialog.name = "SwgSpeciesDialog"
		swg_species_dialog.species_selected.connect(Callable(self, "_on_swg_species_selected"))
		modal_layer.add_child(swg_species_dialog)
	if _swg_action_http == null:
		_swg_action_http = HTTPRequest.new()
		_swg_action_http.name = "SwgActionHttp"
		add_child(_swg_action_http)
		_swg_action_http.request_completed.connect(_on_swg_action_http_done)


func _on_swg_chat_command(cmd: String, _args: String) -> void:
	match cmd:
		"dance":
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff77ee]♫ Vous esquissez les pas de danse d'artiste de cantina ![/color]", "spatial")
		"kneel":
			_on_swg_radial_action("posture_kneel", {})
		"prone":
			_on_swg_radial_action("posture_prone", {})
		"stand":
			_on_swg_radial_action("posture_upright", {})
		"camp":
			_on_swg_radial_action("deploy_camp", {})
		"harvester":
			_on_swg_radial_action("deploy_harvester", {})
		"flourish":
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff66dd]✨ Flourish d'Entertainer exécuté ! L'assistance est transportée par la performance.[/color]", "spatial")
			if swg_audio and swg_audio.has_method("play_mission_complete"):
				swg_audio.play_mission_complete()
			if swg_ham_hud:
				swg_ham_hud.heal_pool("mind", 150)
		"species", "race":
			if swg_species_dialog:
				swg_species_dialog.open_panel()
		"faction":
			if swg_faction_dialog:
				swg_faction_dialog.open_panel("recruiter_imperial_kren")
		"house", "placehouse":
			_on_swg_radial_action("deploy_house", {})
		"clone", "suicide":
			if swg_chat_box:
				swg_chat_box.add_log("[color=#44ffcc]🏥 Rapatriement au Centre Médical de Lost Heaven.[/color]", "system")
		_:
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ff9999]Commande : /%s. Tapez /help pour l'aide.[/color]" % cmd, "system")


func _on_swg_inventory_item_used(item_id: String) -> void:
	if swg_audio and swg_audio.has_method("play_consume"):
		swg_audio.play_consume()
	match item_id:
		"medpack_a", "medpack_adv":
			if swg_ham_hud:
				swg_ham_hud.heal_pool("health", 250)
				swg_ham_hud.heal_pool("action", 250)
			if swg_chat_box:
				swg_chat_box.add_log("[color=#44ff88]💉 Stimpack Bacta appliqué (+250 Santé / +250 Action) ![/color]", "combat")
		"ration_lh":
			if swg_ham_hud:
				swg_ham_hud.heal_pool("health", 150)
				swg_ham_hud.heal_pool("mind", 200)
			if swg_chat_box:
				swg_chat_box.add_log("[color=#ffdd44]🍖 Ration de survie consommée (+150 S / +200 M) ![/color]", "spatial")
		"blue_milk":
			if swg_ham_hud:
				swg_ham_hud.heal_pool("action", 300)
				swg_ham_hud.heal_pool("mind", 300)
			if swg_chat_box:
				swg_chat_box.add_log("[color=#66ddff]🥛 Lait Bleu de Tatooine consommé (+300 Action / +300 Mental) ![/color]", "spatial")


func _on_swg_species_selected(sp: Dictionary) -> void:
	var s_name := str(sp.get("name", "Humain"))
	var s_title := str(sp.get("title", ""))
	var bonus: Dictionary = sp.get("ham_bonus", {})
	if swg_chat_box:
		swg_chat_box.add_log("[color=#44ffcc]🧬 Image Designer : Vous avez adopté l'espèce %s %s ![/color]" % [s_name, s_title], "spatial")
	if swg_ham_hud:
		swg_ham_hud.heal_pool("health", int(bonus.get("health", 100)))
		swg_ham_hud.heal_pool("action", int(bonus.get("action", 100)))
		swg_ham_hud.heal_pool("mind", int(bonus.get("mind", 100)))


func _on_swg_quick_panel_requested(panel_key: String) -> void:
	_ensure_swg_ui()
	match panel_key:
		"character", "sheet":
			if swg_character_sheet and swg_character_sheet.has_method("toggle"):
				swg_character_sheet.toggle()
		"datapad":
			if swg_datapad_panel and swg_datapad_panel.has_method("toggle"):
				swg_datapad_panel.toggle()
		"skills":
			if swg_skills_panel and swg_skills_panel.has_method("toggle"):
				swg_skills_panel.toggle()
		"inventory":
			if swg_inventory_paperdoll and swg_inventory_paperdoll.has_method("toggle"):
				swg_inventory_paperdoll.toggle()
		"crafting", "talents":
			if swg_crafting_panel and swg_crafting_panel.has_method("toggle"):
				swg_crafting_panel.toggle()
		"survey":
			if swg_survey_panel and swg_survey_panel.has_method("toggle"):
				var xz: Vector2 = _player_world_xz()
				if xz != Vector2.INF:
					swg_survey_panel.player_pos_xz = xz
				swg_survey_panel.toggle()
		"experiment":
			if swg_experiment_panel and swg_experiment_panel.has_method("toggle"):
				swg_experiment_panel.toggle()
		"inventory":
			_toggle_inventory()
		"talents":
			_toggle_talents()
		"missions":
			_toggle_missions()
		"map":
			var map_panel: Node = get_node_or_null("UI/ModalLayer/PlanetMapPanel")
			if map_panel and map_panel.has_method("toggle_map"):
				map_panel.call("toggle_map")
		"vendors":
			if swg_bazaar_panel and swg_bazaar_panel.has_method("toggle"):
				swg_bazaar_panel.toggle()
			else:
				var base_url := _HubRuntimeCfg.http_url() if _HubRuntimeCfg.enabled() else "http://192.168.0.246:8787"
				_hotbar_feedback("Datapad : Consultation du Réseau Commercial & Bazar...")
				if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
					_swg_action_http.request(base_url.rstrip("/") + "/v1/bazaar/browse?category=all&limit=5", [], HTTPClient.METHOD_GET)
		"housing":
			if swg_structure_panel and swg_structure_panel.has_method("toggle"):
				swg_structure_panel.toggle()
			else:
				var base_url := _HubRuntimeCfg.http_url() if _HubRuntimeCfg.enabled() else "http://192.168.0.246:8787"
				var p_name := _local_character_name if not _local_character_name.is_empty() else _HubRuntimeCfg.player_name("Voyageur")
				_hotbar_feedback("Datapad : Registre Foncier & Villes de Joueurs...")
				if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
					_swg_action_http.request(base_url.rstrip("/") + "/v1/housing/structures?owner=" + p_name.uri_encode(), [], HTTPClient.METHOD_GET)


func _handle_world_right_click(screen_pos: Vector2) -> void:
	_ensure_swg_ui()
	if swg_radial_menu == null:
		return
	var ui_pos := get_viewport().get_mouse_position() if get_viewport() else screen_pos
	var picked: Node = entity_manager.pick_entity_at_screen(screen_pos) if entity_manager else null
	if picked:
		_set_selected_entity(picked.object_id)
		var e_name := str(picked.get_display_name()) if picked.has_method("get_display_name") else str(picked.get("label_text"))
		var ctx := {
			"kind": str(picked.get("kind")),
			"name": e_name,
			"object_id": int(picked.object_id),
			"entity_key": str(picked.get("entity_key")),
		}
		swg_radial_menu.open_at(ui_pos, ctx)
		return
	var c3 := _screen_click_to_core3(screen_pos)
	var g_ctx := {
		"kind": "ground",
		"name": "Terrain (%.0f, %.0f)" % [c3.x, c3.z],
		"x": c3.x,
		"z": c3.z,
	}
	swg_radial_menu.open_at(ui_pos, g_ctx)


func _on_swg_radial_action(action_id: String, ctx: Dictionary) -> void:
	var base_url := _HubRuntimeCfg.http_url() if _HubRuntimeCfg.enabled() else "http://192.168.0.246:8787"
	var p_name := _local_character_name if not _local_character_name.is_empty() else _HubRuntimeCfg.player_name("Voyageur")
	match action_id:
		"examine":
			_hotbar_feedback("Inspection SWG : %s (%s)" % [str(ctx.get("name", "?")), str(ctx.get("kind", "entité"))])
		"converse":
			var oid := int(ctx.get("object_id", 0))
			var ent: Node = entity_manager.get_entity(oid) if (entity_manager and oid > 0) else null
			if ent:
				_open_npc_dialogue(ent)
		"watch_entertainer":
			var perf := str(ctx.get("name", "Lia"))
			_hotbar_feedback("Cantina : écoute %s (soin Battle Fatigue)..." % perf)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/show/watch",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"listener": p_name, "performer": perf, "ticks": 3, "in_cantina": true})
				)
		"treat_wounds":
			var target_p := str(ctx.get("name", p_name))
			if str(ctx.get("kind", "")) == "npc":
				target_p = p_name
			_hotbar_feedback("Medcenter : soin des blessures (Wounds) sur %s..." % target_p)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/medical/treat_wounds",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"medic": p_name, "patient": target_p, "pool": "health", "in_medcenter": true})
				)
		"open_skills":
			if swg_skills_panel and swg_skills_panel.has_method("toggle"):
				swg_skills_panel.toggle()
		"survey_ping", "survey_sample", "deploy_harvester":
			if swg_survey_panel:
				if ctx.has("x") and ctx.has("z"):
					swg_survey_panel.player_pos_xz = Vector2(float(ctx.get("x", 4795.0)), float(ctx.get("z", -565.0)))
				if not swg_survey_panel.visible and swg_survey_panel.has_method("toggle"):
					swg_survey_panel.toggle()
				if action_id == "survey_ping" and swg_survey_panel.has_method("ping_selected_spawn"):
					swg_survey_panel.ping_selected_spawn()
				elif action_id == "survey_sample" and swg_survey_panel.has_method("sample_selected_spawn"):
					swg_survey_panel.sample_selected_spawn()
				elif action_id == "deploy_harvester" and swg_survey_panel.has_method("deploy_harvester_on_selected"):
					swg_survey_panel.deploy_harvester_on_selected()
		"move_here":
			var pc: Node = get_node_or_null("PlayerController")
			if pc and pc.enabled and _play_mode:
				pc.request_move_to(float(ctx.get("x", 4758.0)), float(ctx.get("z", -545.0)))
		"teleport_here":
			var pc: Node = get_node_or_null("PlayerController")
			if pc and pc.enabled and _play_mode and pc.has_method("teleport_to"):
				var tx := float(ctx.get("x", 4758.0))
				var tz := float(ctx.get("z", -545.0))
				pc.teleport_to(tx, tz)
				_hotbar_feedback("⚡ Téléportation (Dev) : %.0f, %.0f" % [tx, tz])
		"harvest_meat", "harvest_hide", "harvest_bone":
			var res_type := "meat" if action_id == "harvest_meat" else ("hide" if action_id == "harvest_hide" else "bone")
			var cid := str(ctx.get("corpse_id", ctx.get("entity_key", "corpse_default")))
			_hotbar_feedback("Dépeçage Scout : prélèvement de %s sur %s..." % [res_type, str(ctx.get("name", "bête"))])
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/harvest",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "corpse_id": cid, "resource_type": res_type})
				)
		"tame_creature":
			var beast_id := str(ctx.get("entity_key", ctx.get("object_id", "beast_01")))
			_hotbar_feedback("Creature Handler : tentative d'apprivoisement sur %s..." % str(ctx.get("name", "bête")))
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/tame",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "creature_id": beast_id})
				)
		"pet_follow", "pet_stay", "pet_store":
			var order_name := "follow" if action_id == "pet_follow" else ("stay" if action_id == "pet_stay" else "store")
			var pet_id := str(ctx.get("pet_id", ctx.get("name", "compagnon")))
			_hotbar_feedback("Ordre Bête (%s) : %s" % [pet_id, order_name.to_upper()])
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/pet_order",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "pet_id": pet_id, "order": order_name})
				)
		"pet_feed":
			var pet_id := str(ctx.get("pet_id", ctx.get("name", "compagnon")))
			_hotbar_feedback("Nourrissage du compagnon %s..." % pet_id)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/pet_feed",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "pet_id": pet_id, "food_item": "meat_dune_crawler", "qty": 1})
				)
		"attack_lair":
			var lid := str(ctx.get("lair_id", ctx.get("entity_key", "lair_jackals_west")))
			_hotbar_feedback("⚔ Assaut de Nid de Créatures : Tir concentré sur %s !" % lid)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/lair/attack",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "lair_id": lid, "damage": 250})
				)
		"harvest_debris":
			var lid := str(ctx.get("lair_id", ctx.get("entity_key", "lair_jackals_west")))
			_hotbar_feedback("Fouille des décombres du nid %s..." % lid)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/lair/harvest",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "lair_id": lid})
				)
		"enlist_faction":
			if swg_faction_dialog:
				var rec_id := str(ctx.get("entity_key", "recruiter_imperial_kren"))
				swg_faction_dialog.open_panel(rec_id)
		"open_species":
			if swg_species_dialog:
				swg_species_dialog.open_panel()
		"call_pcd":
			var pcd_id := str(ctx.get("pcd_id", "pcd_speeder_x34"))
			_hotbar_feedback("Datapad PCD : Déploiement de %s !" % pcd_id)
			if swg_chat_box:
				swg_chat_box.add_log("[color=#44ffcc]🚀 Appareil invoqué : %s disponible.[/color]" % pcd_id, "spatial")
			if swg_audio and swg_audio.has_method("play_speeder"):
				swg_audio.play_speeder()
		"deploy_camp":
			var xz: Vector2 = _player_world_xz()
			if xz == Vector2.INF:
				xz = Vector2(float(ctx.get("x", 4758.0)), float(ctx.get("z", -545.0)))
			_hotbar_feedback("Dresseur / Scout : montage du campement de survie...")
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/creatures/camp/deploy",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "pos": [xz.x, 0.15, xz.y], "camp_tier": 1})
				)
		"posture_kneel", "posture_prone", "posture_stand":
			var post := "kneeling" if action_id == "posture_kneel" else ("prone" if action_id == "posture_prone" else "upright")
			var post_lbl := "Accroupi" if post == "kneeling" else ("Couché" if post == "prone" else "Debout")
			if swg_ham_hud:
				swg_ham_hud.set_posture(post_lbl)
			_hotbar_feedback("Changement de Posture SWG : %s" % post_lbl)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/combat/posture",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"player": p_name, "posture": post})
				)
		"tactical_strike":
			var tgt := str(ctx.get("name", "cible"))
			_hotbar_feedback("⚔ Frappe Tactique HAM engagée contre %s..." % tgt)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(
					base_url.rstrip("/") + "/v1/combat/strike",
					PackedStringArray(["Content-Type: application/json"]),
					HTTPClient.METHOD_POST,
					JSON.stringify({"attacker": p_name, "target": tgt, "strike_id": "leg_sweep", "force_hit": true})
				)
		"vendor_browse", "vendor_manage":
			var v_id := str(ctx.get("entity_key", ctx.get("name", "vendeur")))
			_hotbar_feedback("Boutique / Vendeur %s : consultation du stock..." % v_id)
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(base_url.rstrip("/") + "/v1/vendors/catalog?vendor_id=" + v_id.uri_encode(), [], HTTPClient.METHOD_GET)
		"house_enter", "house_manage", "house_maintenance", "house_decorate":
			var s_id := str(ctx.get("entity_key", ctx.get("name", "structure")))
			_hotbar_feedback("Housing SWG : %s sur %s" % [action_id.to_upper(), s_id])
			if _swg_action_http and _swg_action_http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
				_swg_action_http.request(base_url.rstrip("/") + "/v1/housing/structure?structure_id=" + s_id.uri_encode(), [], HTTPClient.METHOD_GET)


func _on_swg_action_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d := parsed as Dictionary
	if bool(d.get("ok", false)):
		if d.has("fatigue_cured"):
			_hotbar_feedback("Cantina : -%d Battle Fatigue, +%d Buff Mind" % [int(d.get("fatigue_cured", 0)), int(d.get("mind_buff", 0))])
		elif d.has("wounds_cured"):
			_hotbar_feedback("Medcenter : -%d Wounds soignées !" % int(d.get("wounds_cured", 0)))
		elif d.has("harvested"):
			_hotbar_feedback("Dépeçage réussi : +%d %s ! Expérience Scout reçue." % [int(d.get("qty", 0)), str(d.get("item", "ressource"))])
		elif d.has("pet"):
			_hotbar_feedback("🐾 Créature apprivoisée avec succès ! Ajoutée à votre datapad.")
		elif d.has("camp_id"):
			_hotbar_feedback("⛺ Campement établi ! Régénération accélérée à proximité.")
		elif d.has("posture"):
			_hotbar_feedback("Posture confirmée par le serveur : %s" % str(d.get("posture")).to_upper())
			if swg_ham_hud:
				swg_ham_hud.set_posture(str(d.get("posture")))
		elif d.has("strike"):
			var st: Dictionary = d.get("strike", {}) if typeof(d.get("strike")) == TYPE_DICTIONARY else {}
			_hotbar_feedback("⚔ Frappe %s infligée ! Dégâts: %s" % [str(st.get("strike_id", "")), str(st.get("raw_damage", 0))])
		elif d.has("items") and typeof(d.get("items")) == TYPE_ARRAY:
			var it_arr: Array = d.get("items", [])
			_hotbar_feedback("Bazar Public : %d lots disponibles à la vente" % it_arr.size())
		elif d.has("structure"):
			var st_dict: Dictionary = d.get("structure", {}) if typeof(d.get("structure")) == TYPE_DICTIONARY else {}
			_hotbar_feedback("Structure : %s (%s) — Solde: %d cr" % [str(st_dict.get("id", "")), str(st_dict.get("kind", "")), int(st_dict.get("maintenance_credits", 0))])
		if d.has("status") and typeof(d.get("status")) == TYPE_DICTIONARY and swg_ham_hud:
			swg_ham_hud.apply_ham_payload(d["status"] as Dictionary)
		if d.has("active_statuses") and typeof(d.get("active_statuses")) == TYPE_DICTIONARY and swg_ham_hud:
			swg_ham_hud.apply_combat_status(d)
	else:
		_hotbar_feedback("Action SWG refusée : %s" % str(d.get("error", code)))


func _handle_world_left_click(screen_pos: Vector2) -> void:
	var picked: Node = entity_manager.pick_entity_at_screen(screen_pos)
	if picked:
		var was_already_selected: bool = (_selected_entity_id == int(picked.get("object_id")))
		_set_selected_entity(picked.object_id)
		var my_xz := _player_world_xz()
		var dist := 999.0
		if my_xz != Vector2.INF and "core3_pos" in picked:
			var ep: Vector3 = picked.core3_pos
			dist = my_xz.distance_to(Vector2(ep.x, ep.z))

		# Ouvre le dialogue UNIQUEMENT au contact immédiat (< 5.0m)
		if dist <= 5.0:
			if picked.is_interactable():
				_open_npc_dialogue(picked)
				return
			elif str(picked.kind) == "player" and was_already_selected:
				_open_player_inspect(picked)
				return

		# À distance (> 5.0m) : sélectionne et fait marcher le joueur vers le PNJ/joueur sans bloquer avec une fenêtre intempestive
		var pc_walk: Node = get_node_or_null("PlayerController")
		if pc_walk and pc_walk.enabled and _play_mode and "core3_pos" in picked:
			var target_pos: Vector3 = picked.core3_pos
			pc_walk.request_move_to(target_pos.x, target_pos.z)
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
		# Ne pas forcer les étiquettes de tous les PNJ distants pour éviter l'empilement illisible
		_EntityScript.show_nameplates = false
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

func _on_hotbar_item_assigned(slot_idx: int, item: Dictionary) -> void:
	var name_item := str(item.get("name", item.get("id", "Objet")))
	_show_toast("Assigné : %s → Slot %d" % [name_item, (slot_idx + 1) % 10])
	if slot_idx == 2 and gameplay_ops:
		gameplay_ops.set_quick_item_id(str(item.get("id", "")))

func _hotbar_feedback(msg: String) -> void:
	_show_toast(msg)

func _ensure_toast_ui() -> void:
	if _toast_label != null:
		return
	var hud := get_node_or_null("UI/HudLayer") as Control
	if hud == null:
		return
	var panel := PanelContainer.new()
	panel.name = "ToastPanel"
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	panel.offset_left = -220.0
	panel.offset_right = 220.0
	panel.offset_top = -118.0
	panel.offset_bottom = -78.0
	panel.visible = false
	var label := Label.new()
	label.name = "ToastLabel"
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", Color(0.95, 0.88, 0.55, 1.0))
	panel.add_child(label)
	hud.add_child(panel)
	_toast_label = label
	_toast_timer = Timer.new()
	_toast_timer.name = "ToastTimer"
	_toast_timer.one_shot = true
	_toast_timer.wait_time = 2.5
	_toast_timer.timeout.connect(_hide_toast)
	add_child(_toast_timer)

func _show_toast(msg: String) -> void:
	_ensure_toast_ui()
	if _toast_label == null:
		if state_label:
			state_label.text = msg
			state_label.add_theme_color_override("font_color", Color(0.95, 0.82, 0.45, 1))
		return
	_toast_label.text = msg
	(_toast_label.get_parent() as CanvasItem).visible = true
	if _toast_timer:
		_toast_timer.start()

func _hide_toast() -> void:
	if _toast_label == null:
		return
	var panel := _toast_label.get_parent() as CanvasItem
	if panel:
		panel.visible = false

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
