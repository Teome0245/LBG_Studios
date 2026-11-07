extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Fenêtre d'Arbres de Compétences 4×4 Boxes
## Style authentique SWG Holo-Teal : cadre cyan biseauté, pyramide Master / 4×4 / Novice
## avec états visuels (Learned Émeraude/Or, Available Teal, Locked Sombre) & barre 250 SP.

signal box_learned(result: Dictionary)
signal box_surrendered(result: Dictionary)

const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_id: String = "Voyageur"
var panel_visible: bool = false

var _professions: Array = []
var _learned_boxes: Array = []
var _xp_pools: Dictionary = {}
var _skill_mods: Dictionary = {}
var _used_sp: int = 30
var _max_sp: int = 250
var _selected_prof_idx: int = 0
var _selected_box_id: String = "artisan_novice"

var _http_tree: HTTPRequest = null
var _http_action: HTTPRequest = null

var _sp_label: Label = null
var _sp_bar: ProgressBar = null
var _status_label: Label = null
var _prof_list: ItemList = null
var _master_btn: Button = null
var _grid_4x4: GridContainer = null
var _novice_btn: Button = null
var _selected_box_lbl: Label = null
var _xp_mods_lbl: Label = null
var _learn_btn: Button = null
var _surrender_btn: Button = null


func _ready() -> void:
	visible = panel_visible
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_apply_local_fallback()
	_http_tree = HTTPRequest.new()
	add_child(_http_tree)
	_http_tree.request_completed.connect(_on_tree_http_done)
	_http_action = HTTPRequest.new()
	add_child(_http_action)
	_http_action.request_completed.connect(_on_action_http_done)


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_id = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.11, 0.14, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.28, 0.82, 0.90, 0.92)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 14
	sb.content_margin_top = 10
	sb.content_margin_right = 14
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func _make_box_style(state: String, is_selected: bool) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 6
	sb.content_margin_top = 4
	sb.content_margin_right = 6
	sb.content_margin_bottom = 4
	if state == "learned":
		sb.bg_color = Color(0.08, 0.36, 0.32, 0.96)
		sb.set_border_width_all(2 if is_selected else 1)
		sb.border_color = Color(0.98, 0.86, 0.32, 1.0) if is_selected else Color(0.32, 0.92, 0.72, 0.95)
	elif state == "available":
		sb.bg_color = Color(0.04, 0.21, 0.27, 0.95)
		sb.set_border_width_all(2 if is_selected else 1)
		sb.border_color = Color(0.98, 0.86, 0.32, 1.0) if is_selected else Color(0.26, 0.74, 0.86, 0.85)
	else:
		sb.bg_color = Color(0.015, 0.07, 0.09, 0.92)
		sb.set_border_width_all(2 if is_selected else 1)
		sb.border_color = Color(0.95, 0.78, 0.28, 0.95) if is_selected else Color(0.12, 0.34, 0.40, 0.65)
	return sb


func _style_box_button(btn: Button, state: String, is_selected: bool) -> void:
	var sb_norm := _make_box_style(state, is_selected)
	var sb_hov := _make_box_style(state, true)
	sb_hov.bg_color = sb_norm.bg_color.lightened(0.12)
	btn.add_theme_stylebox_override("normal", sb_norm)
	btn.add_theme_stylebox_override("hover", sb_hov)
	btn.add_theme_stylebox_override("pressed", sb_hov)
	if state == "learned":
		btn.add_theme_color_override("font_color", Color(0.95, 0.98, 0.78, 1.0))
	elif state == "available":
		btn.add_theme_color_override("font_color", Color(0.72, 0.94, 0.98, 1.0))
	else:
		btn.add_theme_color_override("font_color", Color(0.45, 0.64, 0.68, 0.90))


func _make_subpanel_style() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.01, 0.06, 0.08, 0.92)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.18, 0.56, 0.64, 0.80)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 8
	sb.content_margin_top = 6
	sb.content_margin_right = 8
	sb.content_margin_bottom = 6
	return sb


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE
	if panel_visible:
		refresh_tree()


func open_panel() -> void:
	panel_visible = true
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	refresh_tree()


func close_panel() -> void:
	panel_visible = false
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func open_for_trainer(prof_id: String) -> void:
	open_panel()
	var target_p := prof_id.to_lower()
	for i in range(_professions.size()):
		var p: Dictionary = _professions[i]
		var pid: String = str(p.get("id", "")).to_lower()
		var pnm: String = str(p.get("name", "")).to_lower()
		if pid == target_p or pid.contains(target_p) or pnm.contains(target_p):
			_selected_prof_idx = i
			if _prof_list:
				_prof_list.select(i)
			_paint_pyramid()
			_paint_details()
			if _status_label:
				_status_label.text = "◈ Entraînement PNJ : Profession %s sélectionnée" % str(p.get("name", pid))
			break


func learn_box_direct(box_id: String) -> void:
	_selected_box_id = box_id
	if not (box_id in _learned_boxes):
		_learned_boxes.append(box_id)
		_used_sp += 15
		_paint_all()
		if _status_label:
			_status_label.text = "✓ Compétence apprise auprès du Formateur : %s" % box_id
		box_learned.emit({"ok": true, "learned_box": box_id})
		learn_selected_box()


func _ensure_ui() -> void:
	if _grid_4x4 != null:
		return
	custom_minimum_size = Vector2(820, 470)
	position = Vector2(160, 80)
	size = Vector2(820, 470)

	var root := VBoxContainer.new()
	root.name = "SkillsRootVBox"
	root.add_theme_constant_override("separation", 8)
	add_child(root)

	# Bandeau de titre Holo-Teal SWG
	var header_panel := PanelContainer.new()
	var sb_hdr := StyleBoxFlat.new()
	sb_hdr.bg_color = Color(0.05, 0.24, 0.30, 0.96)
	sb_hdr.set_border_width_all(1)
	sb_hdr.border_color = Color(0.38, 0.90, 0.96, 0.90)
	sb_hdr.set_corner_radius_all(4)
	sb_hdr.content_margin_left = 10
	sb_hdr.content_margin_top = 4
	sb_hdr.content_margin_right = 8
	sb_hdr.content_margin_bottom = 4
	header_panel.add_theme_stylebox_override("panel", sb_hdr)
	root.add_child(header_panel)

	var top_bar := HBoxContainer.new()
	top_bar.add_theme_constant_override("separation", 12)
	header_panel.add_child(top_bar)

	var title := Label.new()
	title.text = "◈  ARBRES DE COMPÉTENCES & PROFESSIONS  —  SWG PRE-CU (4×4)"
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(0.68, 0.98, 1.0, 1.0))
	top_bar.add_child(title)

	_sp_label = Label.new()
	_sp_label.name = "SkillPointsLabel"
	_sp_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_sp_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_sp_label.add_theme_font_size_override("font_size", 11)
	_sp_label.add_theme_color_override("font_color", Color(0.98, 0.86, 0.35, 1.0))
	top_bar.add_child(_sp_label)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.custom_minimum_size = Vector2(26, 22)
	close_btn.pressed.connect(toggle)
	top_bar.add_child(close_btn)

	_status_label = Label.new()
	_status_label.text = "Sélectionne une boîte de compétence dans la pyramide 4×4 pour inspecter ou apprendre."
	_status_label.add_theme_font_size_override("font_size", 10)
	_status_label.add_theme_color_override("font_color", Color(0.66, 0.88, 0.92, 0.95))
	root.add_child(_status_label)

	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 10)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(body)

	# Colonne gauche : Professions + Jauge SP
	var left_col := VBoxContainer.new()
	left_col.custom_minimum_size = Vector2(180, 0)
	left_col.add_theme_constant_override("separation", 6)
	body.add_child(left_col)

	var prof_hdr := Label.new()
	prof_hdr.text = "PROFESSIONS"
	prof_hdr.add_theme_font_size_override("font_size", 10)
	prof_hdr.add_theme_color_override("font_color", Color(0.45, 0.88, 0.95, 1.0))
	left_col.add_child(prof_hdr)

	_prof_list = ItemList.new()
	_prof_list.name = "ProfessionsList"
	_prof_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_prof_list.add_theme_stylebox_override("panel", _make_subpanel_style())
	_prof_list.add_theme_color_override("font_color", Color(0.75, 0.92, 0.95, 1.0))
	_prof_list.add_theme_color_override("font_selected_color", Color(0.98, 0.88, 0.35, 1.0))
	_prof_list.item_selected.connect(_on_profession_selected)
	left_col.add_child(_prof_list)

	var sp_title := Label.new()
	sp_title.text = "POINTS DE COMPÉTENCE (MAX 250)"
	sp_title.add_theme_font_size_override("font_size", 9)
	sp_title.add_theme_color_override("font_color", Color(0.92, 0.80, 0.35, 1.0))
	left_col.add_child(sp_title)

	_sp_bar = ProgressBar.new()
	_sp_bar.max_value = 250.0
	_sp_bar.value = 45.0
	_sp_bar.custom_minimum_size = Vector2(0, 14)
	_sp_bar.show_percentage = false
	var sb_sp_bg := StyleBoxFlat.new()
	sb_sp_bg.bg_color = Color(0.01, 0.05, 0.07, 0.95)
	sb_sp_bg.set_border_width_all(1)
	sb_sp_bg.border_color = Color(0.25, 0.68, 0.78, 0.85)
	var sb_sp_fill := StyleBoxFlat.new()
	sb_sp_fill.bg_color = Color(0.92, 0.74, 0.22, 0.95)
	_sp_bar.add_theme_stylebox_override("background", sb_sp_bg)
	_sp_bar.add_theme_stylebox_override("fill", sb_sp_fill)
	left_col.add_child(_sp_bar)

	# Colonne centrale : Pyramide SWG (Master en haut -> 4×4 -> Novice en bas)
	var tree_panel := PanelContainer.new()
	tree_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tree_panel.add_theme_stylebox_override("panel", _make_subpanel_style())
	body.add_child(tree_panel)

	var tree_col := VBoxContainer.new()
	tree_col.add_theme_constant_override("separation", 6)
	tree_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tree_panel.add_child(tree_col)

	_master_btn = Button.new()
	_master_btn.name = "MasterBoxBtn"
	_master_btn.custom_minimum_size = Vector2(0, 34)
	_master_btn.add_theme_font_size_override("font_size", 11)
	tree_col.add_child(_master_btn)

	_grid_4x4 = GridContainer.new()
	_grid_4x4.name = "Grid4x4"
	_grid_4x4.columns = 4
	_grid_4x4.add_theme_constant_override("h_separation", 6)
	_grid_4x4.add_theme_constant_override("v_separation", 6)
	_grid_4x4.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_grid_4x4.size_flags_vertical = Control.SIZE_EXPAND_FILL
	tree_col.add_child(_grid_4x4)

	_novice_btn = Button.new()
	_novice_btn.name = "NoviceBoxBtn"
	_novice_btn.custom_minimum_size = Vector2(0, 34)
	_novice_btn.add_theme_font_size_override("font_size", 11)
	tree_col.add_child(_novice_btn)

	# Colonne droite : Détail box, XP Pools, Mods & Actions
	var right_col := VBoxContainer.new()
	right_col.custom_minimum_size = Vector2(215, 0)
	right_col.add_theme_constant_override("separation", 6)
	body.add_child(right_col)

	var sel_panel := PanelContainer.new()
	sel_panel.add_theme_stylebox_override("panel", _make_subpanel_style())
	right_col.add_child(sel_panel)

	_selected_box_lbl = Label.new()
	_selected_box_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_selected_box_lbl.add_theme_font_size_override("font_size", 10)
	_selected_box_lbl.add_theme_color_override("font_color", Color(0.96, 0.90, 0.68, 1.0))
	sel_panel.add_child(_selected_box_lbl)

	var mods_panel := PanelContainer.new()
	mods_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	mods_panel.add_theme_stylebox_override("panel", _make_subpanel_style())
	right_col.add_child(mods_panel)

	_xp_mods_lbl = Label.new()
	_xp_mods_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_xp_mods_lbl.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_xp_mods_lbl.add_theme_font_size_override("font_size", 10)
	_xp_mods_lbl.add_theme_color_override("font_color", Color(0.72, 0.92, 0.88, 0.95))
	mods_panel.add_child(_xp_mods_lbl)

	_learn_btn = Button.new()
	_learn_btn.name = "LearnBoxBtn"
	_learn_btn.text = "▲ APPRENDRE LA COMPÉTENCE"
	_learn_btn.custom_minimum_size = Vector2(0, 28)
	_style_box_button(_learn_btn, "learned", false)
	_learn_btn.pressed.connect(learn_selected_box)
	right_col.add_child(_learn_btn)

	_surrender_btn = Button.new()
	_surrender_btn.name = "SurrenderBoxBtn"
	_surrender_btn.text = "▼ OUBLIER LA COMPÉTENCE"
	_surrender_btn.custom_minimum_size = Vector2(0, 26)
	_style_box_button(_surrender_btn, "locked", false)
	_surrender_btn.pressed.connect(surrender_selected_box)
	right_col.add_child(_surrender_btn)


func _apply_local_fallback() -> void:
	_learned_boxes = ["artisan_novice", "prospecteur_novice", "medecin_novice"]
	_used_sp = 45
	_max_sp = 250
	_xp_pools = {"xp_artisanat": 1500, "xp_prospection": 1500, "xp_medecine": 1000, "xp_scene": 1000, "xp_combat": 1500}
	_skill_mods = {"assembly_bonus": 10, "experimentation_points": 2, "survey_range": 48.0, "wound_heal_efficiency": 25}
	_professions = [
		{
			"id": "artisan",
			"name": "Artisan de rue",
			"xp": "xp_artisanat",
			"boxes": {
				"novice": "artisan_novice",
				"branches": [
					{"id": "outils", "label": "Outils", "boxes": ["artisan_outils_01", "artisan_outils_02", "artisan_outils_03", "artisan_outils_04"]},
					{"id": "conso", "label": "Synthèse", "boxes": ["artisan_conso_01", "artisan_conso_02", "artisan_conso_03", "artisan_conso_04"]},
					{"id": "pieces", "label": "Composants", "boxes": ["artisan_pieces_01", "artisan_pieces_02", "artisan_pieces_03", "artisan_pieces_04"]},
					{"id": "survey", "label": "Raffinage", "boxes": ["artisan_survey_01", "artisan_survey_02", "artisan_survey_03", "artisan_survey_04"]},
				],
				"master": "artisan_master",
			},
		},
		{
			"id": "prospecteur",
			"name": "Prospecteur",
			"xp": "xp_prospection",
			"boxes": {
				"novice": "prospecteur_novice",
				"branches": [
					{"id": "survey", "label": "Sondage", "boxes": ["prospecteur_survey_01", "prospecteur_survey_02", "prospecteur_survey_03", "prospecteur_survey_04"]},
					{"id": "piste", "label": "Pistes", "boxes": ["prospecteur_piste_01", "prospecteur_piste_02", "prospecteur_piste_03", "prospecteur_piste_04"]},
					{"id": "camp", "label": "Campement", "boxes": ["prospecteur_camp_01", "prospecteur_camp_02", "prospecteur_camp_03", "prospecteur_camp_04"]},
					{"id": "faune", "label": "Faune", "boxes": ["prospecteur_faune_01", "prospecteur_faune_02", "prospecteur_faune_03", "prospecteur_faune_04"]},
				],
				"master": "prospecteur_master",
			},
		},
	]
	_paint_all()


func apply_tree_snapshot(snap: Dictionary) -> void:
	_ensure_ui()
	if snap.has("professions") and typeof(snap.get("professions")) == TYPE_ARRAY and not (snap["professions"] as Array).is_empty():
		_professions = (snap["professions"] as Array).duplicate(true)
	if snap.has("learned_boxes") and typeof(snap.get("learned_boxes")) == TYPE_ARRAY:
		_learned_boxes = (snap["learned_boxes"] as Array).duplicate()
	if snap.has("xp_pools") and typeof(snap.get("xp_pools")) == TYPE_DICTIONARY:
		_xp_pools = (snap["xp_pools"] as Dictionary).duplicate(true)
	if snap.has("skill_mods") and typeof(snap.get("skill_mods")) == TYPE_DICTIONARY:
		_skill_mods = (snap["skill_mods"] as Dictionary).duplicate(true)
	_used_sp = int(snap.get("used_skill_points", _used_sp))
	_max_sp = int(snap.get("max_skill_points", 250))
	_paint_all()


func refresh_tree() -> void:
	_apply_runtime_cfg()
	if _http_tree == null or not is_inside_tree():
		return
	var url := "%s/v1/skills/tree?player=%s" % [sidecar_base_url.rstrip("/"), player_id.uri_encode()]
	if _http_tree.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http_tree.cancel_request()
	_http_tree.request(url, [], HTTPClient.METHOD_GET)


func select_box(box_id: String) -> void:
	_selected_box_id = box_id.strip_edges()
	_paint_pyramid()
	_paint_details()


func learn_selected_box() -> void:
	if _selected_box_id.is_empty():
		return
	if _http_action != null and is_inside_tree():
		var url := "%s/v1/skills/learn" % sidecar_base_url.rstrip("/")
		var body := JSON.stringify({"player": player_id, "box_id": _selected_box_id})
		if _http_action.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
			_http_action.cancel_request()
		_http_action.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, body)


func surrender_selected_box() -> void:
	if _selected_box_id.is_empty():
		return
	if _http_action != null and is_inside_tree():
		var url := "%s/v1/skills/surrender" % sidecar_base_url.rstrip("/")
		var body := JSON.stringify({"player": player_id, "box_id": _selected_box_id})
		if _http_action.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
			_http_action.cancel_request()
		_http_action.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, body)


func _on_tree_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) == TYPE_DICTIONARY and bool((parsed as Dictionary).get("ok", false)):
		apply_tree_snapshot(parsed as Dictionary)


func _on_action_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d := parsed as Dictionary
	if bool(d.get("ok", false)):
		if d.has("learned_box"):
			if _status_label:
				_status_label.text = "✓ Box apprise : %s" % str(d.get("learned_box", ""))
			box_learned.emit(d)
		elif d.has("surrendered_box"):
			if _status_label:
				_status_label.text = "↺ Box abandonnée : %s" % str(d.get("surrendered_box", ""))
			box_surrendered.emit(d)
		refresh_tree()
	else:
		if _status_label:
			_status_label.text = "⚠ Refus : %s" % str(d.get("error", code))


func _on_profession_selected(idx: int) -> void:
	if idx < 0 or idx >= _professions.size():
		return
	_selected_prof_idx = idx
	_paint_pyramid()
	_paint_details()


func _paint_all() -> void:
	if _sp_label:
		_sp_label.text = "SP : %d / %d  (Restant : %d)" % [_used_sp, _max_sp, maxi(0, _max_sp - _used_sp)]
	if _sp_bar:
		_sp_bar.max_value = float(maxi(1, _max_sp))
		_sp_bar.value = float(_used_sp)
	if _prof_list:
		_prof_list.clear()
		for p in _professions:
			if typeof(p) == TYPE_DICTIONARY:
				_prof_list.add_item("◈ " + str(p.get("name", p.get("id", "?"))))
		if _prof_list.item_count > 0:
			_selected_prof_idx = clampi(_selected_prof_idx, 0, _prof_list.item_count - 1)
			_prof_list.select(_selected_prof_idx)
	_paint_pyramid()
	_paint_details()


func _paint_pyramid() -> void:
	if _grid_4x4 == null or _professions.is_empty():
		return
	var prof: Dictionary = _professions[_selected_prof_idx]
	var boxes_dict: Dictionary = prof.get("boxes", {}) if typeof(prof.get("boxes")) == TYPE_DICTIONARY else {}
	var novice_id := str(boxes_dict.get("novice", "artisan_novice"))
	var master_id := str(boxes_dict.get("master", "artisan_master"))
	var branches: Array = boxes_dict.get("branches", []) if typeof(boxes_dict.get("branches")) == TYPE_ARRAY else []

	var n_learned := novice_id in _learned_boxes
	var m_learned := master_id in _learned_boxes

	if _master_btn:
		_master_btn.text = "%s  MAÎTRE DE PROFESSION  —  %s" % ["★" if m_learned else "◇", master_id.to_upper()]
		_style_box_button(_master_btn, "learned" if m_learned else "locked", _selected_box_id == master_id)
		for conn in _master_btn.pressed.get_connections():
			_master_btn.pressed.disconnect(conn["callable"])
		_master_btn.pressed.connect(func() -> void: select_box(master_id))

	if _novice_btn:
		_novice_btn.text = "%s  NOVICE DE PROFESSION  —  %s" % ["✓" if n_learned else "○", novice_id.to_upper()]
		_style_box_button(_novice_btn, "learned" if n_learned else "available", _selected_box_id == novice_id)
		for conn in _novice_btn.pressed.get_connections():
			_novice_btn.pressed.disconnect(conn["callable"])
		_novice_btn.pressed.connect(func() -> void: select_box(novice_id))

	for child in _grid_4x4.get_children():
		child.queue_free()

	# En SWG Pre-CU, la rangée du haut est le Tier IV (index 3) et la rangée du bas est le Tier I (index 0)
	for tier_idx in [3, 2, 1, 0]:
		for col in range(4):
			var bid := ""
			var br_label := "Br.%d" % (col + 1)
			var prev_learned := n_learned
			if col < branches.size() and typeof(branches[col]) == TYPE_DICTIONARY:
				var br: Dictionary = branches[col]
				br_label = str(br.get("label", br.get("id", br_label)))
				var b_arr: Array = br.get("boxes", []) if typeof(br.get("boxes")) == TYPE_ARRAY else []
				if tier_idx < b_arr.size():
					bid = str(b_arr[tier_idx])
				if tier_idx > 0 and (tier_idx - 1) < b_arr.size():
					prev_learned = str(b_arr[tier_idx - 1]) in _learned_boxes
			var cell_btn := Button.new()
			cell_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			cell_btn.custom_minimum_size = Vector2(98, 44)
			var is_learned := bid in _learned_boxes
			var state := "learned" if is_learned else ("available" if prev_learned else "locked")
			var rom: String = ["I", "II", "III", "IV"][tier_idx]
			cell_btn.text = "%s %s %s\n%s" % ["■" if is_learned else ("▫" if prev_learned else "·"), br_label.to_upper(), rom, bid]
			cell_btn.add_theme_font_size_override("font_size", 9)
			_style_box_button(cell_btn, state, _selected_box_id == bid)
			if not bid.is_empty():
				var captured_bid := bid
				cell_btn.pressed.connect(func() -> void: select_box(captured_bid))
			_grid_4x4.add_child(cell_btn)


func _paint_details() -> void:
	if _selected_box_lbl:
		var is_l := _selected_box_id in _learned_boxes
		_selected_box_lbl.text = "COMPÉTENCE SÉLECTIONNÉE :\n▸ %s\nÉTAT : %s" % [
			_selected_box_id,
			"✓ APPRISE (ACTIVE)" if is_l else "○ NON APPRISE"
		]
	if _xp_mods_lbl:
		var lines := PackedStringArray()
		lines.append("◈ RÉSERVES D'EXPÉRIENCE (XP)")
		for k in _xp_pools.keys():
			lines.append("  • %s : %d XP" % [str(k).replace("xp_", "").to_upper(), int(_xp_pools[k])])
		lines.append("\n◈ MODIFICATEURS PASSIFS")
		lines.append("  • Bonus Assemblage  : +%d" % int(_skill_mods.get("assembly_bonus", 10)))
		lines.append("  • Pts Expérimentat. : +%d" % int(_skill_mods.get("experimentation_points", 2)))
		lines.append("  • Portée Prospection: %.0fm" % float(_skill_mods.get("survey_range", 48.0)))
		lines.append("  • Soin Blessures    : +%d" % int(_skill_mods.get("wound_heal_efficiency", 25)))
		lines.append("  • Extracteurs Max   : %d" % int(_skill_mods.get("harvester_slots", 1)))
		_xp_mods_lbl.text = "\n".join(lines)
