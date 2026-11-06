extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Datapad Personnel Authentique :
## 1. Onglet Waypoints : balises actives, navigation boussole, création/suppression.
## 2. Onglet Familiers & Droïdes (PCD) : cartes de contrôle (PCD), invocation (/call), rangement (/store), ordres.
## 3. Onglet Schémas & Données : blueprints d'artisanat débloqués, ingrédients requis.

signal waypoint_toggled(wp_name: String, active: bool)
signal pet_action_requested(action_name: String, pet_id: String)

const _HubRuntimeCfg := preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_id: String = "Voyageur"
var panel_visible: bool = false

var _current_tab: int = 0 # 0=Waypoints, 1=Pets, 2=Schematics
var _waypoints: Array = [
	{"name": "Cantina La Perle", "x": 5105.0, "z": -795.0, "color": "cyan", "active": true},
	{"name": "Centre Médical d'Odo", "x": 5080.0, "z": -820.0, "color": "cyan", "active": false},
	{"name": "Bazar Public de Lost Heaven", "x": 5120.0, "z": -780.0, "color": "orange", "active": true},
	{"name": "Campement des Dunes Est", "x": 5600.0, "z": -1050.0, "color": "green", "active": false},
]

var _pets: Array = [
	{
		"pet_id": "pcd_speeder_x34",
		"name": "Landspeeder X-34 Personnel",
		"species": "Véhicule Répulseur Léger (28 m/s)",
		"level": 1,
		"health": 1500,
		"max_health": 1500,
		"loyalty": 100,
		"hunger": 0,
		"active_in_world": false,
		"commands_learned": ["mount", "store", "repair", "cruise"]
	},
	{
		"pet_id": "pcd_swoop_bike",
		"name": "Swoop Bike Rapide",
		"species": "Moto-Jet Haute Vitesse (36 m/s)",
		"level": 1,
		"health": 1200,
		"max_health": 1200,
		"loyalty": 100,
		"hunger": 0,
		"active_in_world": false,
		"commands_learned": ["mount", "store", "turbo"]
	},
	{
		"pet_id": "pcd_dewback_mount",
		"name": "Dewback Dressé de Selle",
		"species": "Monture Reptilienne des Dunes",
		"level": 5,
		"health": 2200,
		"max_health": 2200,
		"loyalty": 95,
		"hunger": 10,
		"active_in_world": false,
		"commands_learned": ["mount", "follow", "stay", "feed", "store"]
	},
	{
		"pet_id": "pcd_chacal_01",
		"name": "Chiot des Sables",
		"species": "Chacal Doré (Juvénile)",
		"level": 3,
		"health": 180,
		"max_health": 180,
		"loyalty": 92,
		"hunger": 20,
		"active_in_world": false,
		"commands_learned": ["follow", "stay", "attack", "trick1"]
	}
]

var _schematics: Array = [
	{"id": "kit_reparation_meca", "name": "Kit de Réparation Mécatronique", "craft_xp": 120, "ingredients": "Ferraille ×10, Composant d'Énergie ×2"},
	{"id": "tente_nomade_toile", "name": "Kit de Campement en Toile", "craft_xp": 250, "ingredients": "Cuir épais ×8, Barres métalliques ×4"},
	{"id": "injecteur_stimpack_a", "name": "Stimpack Médical Léger", "craft_xp": 90, "ingredients": "Substance organique ×6, Solution saline ×3"}
]

var _wp_list: ItemList = null
var _pet_list: ItemList = null
var _pet_detail_lbl: Label = null
var _schem_list: ItemList = null
var _schem_detail_lbl: Label = null

var _btn_tab_wp: Button = null
var _btn_tab_pets: Button = null
var _btn_tab_schem: Button = null

var _box_wp: VBoxContainer = null
var _box_pets: VBoxContainer = null
var _box_schem: VBoxContainer = null

var _http: HTTPRequest = null


func _ready() -> void:
	visible = panel_visible
	custom_minimum_size = Vector2(460, 420)
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)
	refresh_datapad()


func _ensure_ui() -> void:
	_build_ui()


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_id = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.015, 0.09, 0.12, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.84, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 8
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func _make_swg_btn(txt: String, active: bool = false) -> Button:
	var btn := Button.new()
	btn.text = txt
	btn.add_theme_font_size_override("font_size", 10)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.32, 0.40, 0.95) if active else Color(0.02, 0.15, 0.19, 0.90)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.95, 0.84, 0.32, 1.0) if active else Color(0.22, 0.78, 0.88, 0.85)
	sb.set_corner_radius_all(3)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	btn.add_theme_stylebox_override("normal", sb)
	var sb_h := sb.duplicate() as StyleBoxFlat
	sb_h.bg_color = Color(0.10, 0.44, 0.54, 0.98)
	btn.add_theme_stylebox_override("hover", sb_h)
	return btn


func _build_ui() -> void:
	for c in get_children():
		if c != _http:
			c.queue_free()

	var root_vbox := VBoxContainer.new()
	root_vbox.add_theme_constant_override("separation", 8)
	add_child(root_vbox)

	# 1. Header Holo-Teal
	var hdr := HBoxContainer.new()
	var title_lbl := Label.new()
	title_lbl.text = "◈ DATAPAD PERSONNEL (SWG ARCHIVE) — %s" % player_id.to_upper()
	title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_lbl.add_theme_font_size_override("font_size", 11)
	title_lbl.add_theme_color_override("font_color", Color(0.55, 0.96, 1.0, 1.0))
	hdr.add_child(title_lbl)

	var close_btn := Button.new()
	close_btn.text = " ✕ "
	close_btn.add_theme_font_size_override("font_size", 10)
	close_btn.pressed.connect(toggle)
	hdr.add_child(close_btn)
	root_vbox.add_child(hdr)

	# 2. Barre d'onglets SWG
	var tabs_bar := HBoxContainer.new()
	tabs_bar.add_theme_constant_override("separation", 6)

	_btn_tab_wp = _make_swg_btn("◎ WAYPOINTS (%d)" % _waypoints.size(), _current_tab == 0)
	_btn_tab_wp.pressed.connect(func() -> void: _switch_tab(0))
	tabs_bar.add_child(_btn_tab_wp)

	_btn_tab_pets = _make_swg_btn("🐾 FAMILIERS / PCD (%d)" % _pets.size(), _current_tab == 1)
	_btn_tab_pets.pressed.connect(func() -> void: _switch_tab(1))
	tabs_bar.add_child(_btn_tab_pets)

	_btn_tab_schem = _make_swg_btn("⚙ SCHÉMAS & DATA (%d)" % _schematics.size(), _current_tab == 2)
	_btn_tab_schem.pressed.connect(func() -> void: _switch_tab(2))
	tabs_bar.add_child(_btn_tab_schem)

	root_vbox.add_child(tabs_bar)

	# 3. Conteneur dynamique d'onglets
	# TAB 0 : WAYPOINTS
	_box_wp = VBoxContainer.new()
	_box_wp.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_wp.visible = (_current_tab == 0)
	root_vbox.add_child(_box_wp)

	var wp_hdr := Label.new()
	wp_hdr.text = "Balises planétaires enregistrées (Boussole HUD active) :"
	wp_hdr.add_theme_font_size_override("font_size", 9)
	wp_hdr.add_theme_color_override("font_color", Color(0.75, 0.90, 0.95, 0.85))
	_box_wp.add_child(wp_hdr)

	_wp_list = ItemList.new()
	_wp_list.custom_minimum_size = Vector2(430, 240)
	_wp_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_wp.add_child(_wp_list)

	var wp_btns := HBoxContainer.new()
	var btn_toggle_wp := _make_swg_btn("Activer / Masquer")
	btn_toggle_wp.pressed.connect(_on_toggle_waypoint)
	wp_btns.add_child(btn_toggle_wp)

	var btn_add_wp := _make_swg_btn("Nouveau Waypoint Ici")
	btn_add_wp.pressed.connect(_on_add_current_waypoint)
	wp_btns.add_child(btn_add_wp)

	var btn_del_wp := _make_swg_btn("Supprimer Balise")
	btn_del_wp.pressed.connect(_on_delete_waypoint)
	wp_btns.add_child(btn_del_wp)
	_box_wp.add_child(wp_btns)

	# TAB 1 : PETS (PCD)
	_box_pets = VBoxContainer.new()
	_box_pets.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_pets.visible = (_current_tab == 1)
	root_vbox.add_child(_box_pets)

	var pet_split := HBoxContainer.new()
	pet_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_pets.add_child(pet_split)

	_pet_list = ItemList.new()
	_pet_list.custom_minimum_size = Vector2(180, 240)
	_pet_list.item_selected.connect(_on_pet_selected)
	pet_split.add_child(_pet_list)

	var pet_right := VBoxContainer.new()
	pet_right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pet_split.add_child(pet_right)

	_pet_detail_lbl = Label.new()
	_pet_detail_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD
	_pet_detail_lbl.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_pet_detail_lbl.add_theme_font_size_override("font_size", 9)
	_pet_detail_lbl.add_theme_color_override("font_color", Color(0.85, 0.98, 1.0, 1.0))
	pet_right.add_child(_pet_detail_lbl)

	var pet_orders_grid := GridContainer.new()
	pet_orders_grid.columns = 2
	var b_call := _make_swg_btn("Invoquer (/call)")
	b_call.pressed.connect(func() -> void: _trigger_pet_action("call"))
	pet_orders_grid.add_child(b_call)

	var b_store := _make_swg_btn("Ranger (/store)")
	b_store.pressed.connect(func() -> void: _trigger_pet_action("store"))
	pet_orders_grid.add_child(b_store)

	var b_follow := _make_swg_btn("Suivre (/follow)")
	b_follow.pressed.connect(func() -> void: _trigger_pet_action("follow"))
	pet_orders_grid.add_child(b_follow)

	var b_stay := _make_swg_btn("Rester (/stay)")
	b_stay.pressed.connect(func() -> void: _trigger_pet_action("stay"))
	pet_orders_grid.add_child(b_stay)

	var b_trick := _make_swg_btn("Tour (/trick 1)")
	b_trick.pressed.connect(func() -> void: _trigger_pet_action("trick1"))
	pet_orders_grid.add_child(b_trick)

	var b_feed := _make_swg_btn("Nourrir Bête")
	b_feed.pressed.connect(func() -> void: _trigger_pet_action("feed"))
	pet_orders_grid.add_child(b_feed)
	pet_right.add_child(pet_orders_grid)

	# TAB 2 : SCHEMATICS
	_box_schem = VBoxContainer.new()
	_box_schem.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_schem.visible = (_current_tab == 2)
	root_vbox.add_child(_box_schem)

	_schem_list = ItemList.new()
	_schem_list.custom_minimum_size = Vector2(430, 160)
	_schem_list.item_selected.connect(_on_schem_selected)
	_box_schem.add_child(_schem_list)

	_schem_detail_lbl = Label.new()
	_schem_detail_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD
	_schem_detail_lbl.custom_minimum_size = Vector2(430, 80)
	_schem_detail_lbl.add_theme_font_size_override("font_size", 9)
	_schem_detail_lbl.add_theme_color_override("font_color", Color(0.85, 0.98, 1.0, 1.0))
	_box_schem.add_child(_schem_detail_lbl)

	_refresh_wp_list()
	_refresh_pet_list()
	_refresh_schem_list()


func _switch_tab(idx: int) -> void:
	_current_tab = idx
	if _btn_tab_wp:
		_btn_tab_wp.button_pressed = (idx == 0)
	if _btn_tab_pets:
		_btn_tab_pets.button_pressed = (idx == 1)
	if _btn_tab_schem:
		_btn_tab_schem.button_pressed = (idx == 2)
	if _box_wp:
		_box_wp.visible = (idx == 0)
	if _box_pets:
		_box_pets.visible = (idx == 1)
	if _box_schem:
		_box_schem.visible = (idx == 2)


func _refresh_wp_list() -> void:
	if _wp_list == null:
		return
	_wp_list.clear()
	for i in range(_waypoints.size()):
		var wp: Dictionary = _waypoints[i]
		var act_str := " [ACTIF]" if bool(wp.get("active", false)) else ""
		var line := "%s (%.0f, %.0f)%s" % [str(wp.get("name", "Balise")), float(wp.get("x", 0.0)), float(wp.get("z", 0.0)), act_str]
		_wp_list.add_item(line)
		if bool(wp.get("active", false)):
			_wp_list.set_item_custom_fg_color(i, Color(0.35, 0.95, 1.0, 1.0))
		else:
			_wp_list.set_item_custom_fg_color(i, Color(0.70, 0.75, 0.80, 0.80))


func _refresh_pet_list() -> void:
	if _pet_list == null:
		return
	_pet_list.clear()
	for i in range(_pets.size()):
		var p: Dictionary = _pets[i]
		var status_str := " (Terrain)" if bool(p.get("active_in_world", false)) else " (Datapad)"
		_pet_list.add_item("%s%s" % [str(p.get("name", "Familier")), status_str])
	if _pets.size() > 0:
		_pet_list.select(0)
		_on_pet_selected(0)


func _on_pet_selected(idx: int) -> void:
	if idx < 0 or idx >= _pets.size() or _pet_detail_lbl == null:
		return
	var p: Dictionary = _pets[idx]
	_pet_detail_lbl.text = (
		"◈ FICHE FAMILIER PCD :\n"
		+ "• Nom : %s\n" % str(p.get("name", "Familier"))
		+ "• Espèce : %s\n" % str(p.get("species", "Faune"))
		+ "• Niveau : %d  |  Santé : %d/%d\n" % [int(p.get("level", 1)), int(p.get("health", 100)), int(p.get("max_health", 100))]
		+ "• Loyauté : %d%%  |  Faim : %d%%\n" % [int(p.get("loyalty", 100)), int(p.get("hunger", 0))]
		+ "• Ordres appris : %s" % ", ".join(p.get("commands_learned", []))
	)


func _refresh_schem_list() -> void:
	if _schem_list == null:
		return
	_schem_list.clear()
	for s in _schematics:
		_schem_list.add_item(str(s.get("name", "Plan")))
	if _schematics.size() > 0:
		_schem_list.select(0)
		_on_schem_selected(0)


func _on_schem_selected(idx: int) -> void:
	if idx < 0 or idx >= _schematics.size() or _schem_detail_lbl == null:
		return
	var s: Dictionary = _schematics[idx]
	_schem_detail_lbl.text = (
		"◈ SCHÉMA MANUFACTURÉ SWG :\n"
		+ "• Nom : %s\n" % str(s.get("name", ""))
		+ "• Ingrédients requis : %s\n" % str(s.get("ingredients", "Ressources"))
		+ "• XP Artisanat octroyée : +%d XP" % int(s.get("craft_xp", 50))
	)


func _on_toggle_waypoint() -> void:
	var sel := _wp_list.get_selected_items() if _wp_list else PackedInt32Array()
	if sel.is_empty():
		return
	var idx := sel[0]
	var cur: bool = bool(_waypoints[idx].get("active", false))
	_waypoints[idx]["active"] = not cur
	_refresh_wp_list()
	waypoint_toggled.emit(str(_waypoints[idx]["name"]), not cur)


func _on_add_current_waypoint() -> void:
	var new_wp := {
		"name": "Point Retenu #%d" % (_waypoints.size() + 1),
		"x": 5100.0,
		"z": -800.0,
		"color": "cyan",
		"active": true
	}
	_waypoints.append(new_wp)
	_refresh_wp_list()


func _on_delete_waypoint() -> void:
	var sel := _wp_list.get_selected_items() if _wp_list else PackedInt32Array()
	if sel.is_empty():
		return
	_waypoints.remove_at(sel[0])
	_refresh_wp_list()


func _trigger_pet_action(action_name: String) -> void:
	var sel := _pet_list.get_selected_items() if _pet_list else PackedInt32Array()
	if sel.is_empty():
		return
	var p: Dictionary = _pets[sel[0]]
	var pid := str(p.get("pet_id", ""))
	if action_name == "call":
		p["active_in_world"] = true
	elif action_name == "store":
		p["active_in_world"] = false
	_refresh_pet_list()
	pet_action_requested.emit(action_name, pid)
	# Requête HTTP vers /v1/creatures/pet_order ou /call
	if _http and _http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
		var ep := "/v1/creatures/pet/order" if action_name != "call" else "/v1/creatures/pet/call"
		var url := "%s%s" % [sidecar_base_url.rstrip("/"), ep]
		var payload := {"player": player_id, "pet_id": pid, "order": action_name}
		_http.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify(payload))


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	if visible:
		refresh_datapad()


func refresh_datapad() -> void:
	_apply_runtime_cfg()
	if _http == null or not is_inside_tree():
		return
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	var url := "%s/v1/creatures/pets?player=%s" % [sidecar_base_url.rstrip("/"), player_id.uri_encode()]
	_http.request(url, [], HTTPClient.METHOD_GET)


func _on_http_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code < 200 or response_code >= 300 or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d := parsed as Dictionary
	if d.has("pets") and typeof(d["pets"]) == TYPE_ARRAY:
		var arr: Array = d["pets"]
		if not arr.is_empty():
			_pets = arr.duplicate(true)
			_refresh_pet_list()
