extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Gestion Foncière & Cités de Joueurs :
## 1. État & Maintenance : solde du pool crédits, consommation horaire, jours restants, dépôt.
## 2. Permissions & Accès (ACL) : statut Public/Privé, liste d'accès (Entry List), liste de bannissement.
## 3. Cité & Municipalité : rang civique (Campement -> Métropole), taxes, maire en exercice.

signal maintenance_paid(structure_id: String, amount: int)
signal panel_closed()

const _HubRuntimeCfg := preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_name: String = "Voyageur"
var player_credits: int = 15000
var panel_visible: bool = false

var _current_tab: int = 0 # 0=Maintenance, 1=ACL, 2=City

# Structure active
var _structure_data: Dictionary = {
	"id": "house_lh_001",
	"name": "Maison Modulaire des Sables - Secteur Est",
	"kind": "small_plaster_house",
	"planet": "Lost Heaven",
	"pos": [5210.4, 0.0, -810.0],
	"maintenance_credits": 4800,
	"maintenance_rate_hourly": 15,
	"condition_pct": 100,
	"is_public": true,
	"entry_list": ["Lia", "Nix"],
	"ban_list": [],
	"items_placed": 14,
	"items_capacity": 50,
	"city_name": "Oasis de Scrapaltai",
	"city_rank": "Village (Rang 3)",
	"city_mayor": "Odo Merr",
	"property_tax_pct": 4
}

# Références UI
var _lbl_struct_name: Label = null
var _lbl_struct_type: Label = null
var _lbl_struct_pos: Label = null
var _lbl_maint_pool: Label = null
var _lbl_maint_time: Label = null
var _bar_maint: ProgressBar = null
var _input_deposit: SpinBox = null
var _btn_deposit: Button = null

var _btn_privacy_toggle: Button = null
var _entry_list_ui: ItemList = null
var _input_add_resident: LineEdit = null

var _lbl_city_name: Label = null
var _lbl_city_rank: Label = null
var _lbl_city_mayor: Label = null
var _lbl_city_tax: Label = null

var _box_maint: VBoxContainer = null
var _box_acl: VBoxContainer = null
var _box_city: VBoxContainer = null

var _http: HTTPRequest = null


func _ready() -> void:
	visible = panel_visible
	custom_minimum_size = Vector2(580, 460)
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)
	refresh_structure()


func _ensure_ui() -> void:
	_build_ui()


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_name = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.015, 0.08, 0.12, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.85, 0.95, 0.95)
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
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	btn.add_theme_stylebox_override("normal", sb)
	return btn


func _build_ui() -> void:
	for c in get_children():
		if c != _http:
			c.queue_free()

	var root_vbox := VBoxContainer.new()
	root_vbox.add_theme_constant_override("separation", 8)
	add_child(root_vbox)

	# --- En-tête ---
	var header := HBoxContainer.new()
	var title_lbl := Label.new()
	title_lbl.text = "◈ TERMINAL DE GESTION FONCIÈRE & CITÉ ◈"
	title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_lbl.add_theme_font_size_override("font_size", 13)
	title_lbl.add_theme_color_override("font_color", Color(0.96, 0.86, 0.38, 1.0))
	header.add_child(title_lbl)

	var close_btn := Button.new()
	close_btn.text = " ✕ "
	close_btn.add_theme_font_size_override("font_size", 11)
	close_btn.pressed.connect(close_panel)
	header.add_child(close_btn)
	root_vbox.add_child(header)

	var hsep1 := HSeparator.new()
	root_vbox.add_child(hsep1)

	# --- Barre d'onglets SWG ---
	var tab_row := HBoxContainer.new()
	tab_row.add_theme_constant_override("separation", 8)

	var btn_tab_maint := _make_swg_btn(" 🛠 État & Maintenance ", _current_tab == 0)
	btn_tab_maint.pressed.connect(func() -> void: _switch_tab(0))
	tab_row.add_child(btn_tab_maint)

	var btn_tab_acl := _make_swg_btn(" 🔐 Accès & Permissions (ACL) ", _current_tab == 1)
	btn_tab_acl.pressed.connect(func() -> void: _switch_tab(1))
	tab_row.add_child(btn_tab_acl)

	var btn_tab_city := _make_swg_btn(" 🏛 Cité & Municipalité ", _current_tab == 2)
	btn_tab_city.pressed.connect(func() -> void: _switch_tab(2))
	tab_row.add_child(btn_tab_city)

	root_vbox.add_child(tab_row)

	# --- Onglets ---
	# 1. Maintenance
	_box_maint = VBoxContainer.new()
	_box_maint.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_maint.add_theme_constant_override("separation", 8)
	_build_maint_tab(_box_maint)
	root_vbox.add_child(_box_maint)

	# 2. ACL
	_box_acl = VBoxContainer.new()
	_box_acl.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_acl.add_theme_constant_override("separation", 8)
	_build_acl_tab(_box_acl)
	root_vbox.add_child(_box_acl)

	# 3. City
	_box_city = VBoxContainer.new()
	_box_city.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_city.add_theme_constant_override("separation", 8)
	_build_city_tab(_box_city)
	root_vbox.add_child(_box_city)

	_switch_tab(_current_tab)
	_update_views()


func _build_maint_tab(parent: VBoxContainer) -> void:
	# Info Bâtiment
	var inf_panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.12, 0.16, 0.85)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.24, 0.72, 0.82, 0.7)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 8
	sb.content_margin_bottom = 8
	inf_panel.add_theme_stylebox_override("panel", sb)

	var inf_vbox := VBoxContainer.new()
	inf_vbox.add_theme_constant_override("separation", 4)

	_lbl_struct_name = Label.new()
	_lbl_struct_name.text = str(_structure_data.get("name", "Structure"))
	_lbl_struct_name.add_theme_font_size_override("font_size", 12)
	_lbl_struct_name.add_theme_color_override("font_color", Color(0.96, 0.88, 0.42, 1.0))
	inf_vbox.add_child(_lbl_struct_name)

	_lbl_struct_type = Label.new()
	_lbl_struct_type.text = "Modèle : %s | Décorations : %d / %d" % [
		str(_structure_data.get("kind", "")),
		int(_structure_data.get("items_placed", 0)),
		int(_structure_data.get("items_capacity", 50))
	]
	_lbl_struct_type.add_theme_font_size_override("font_size", 10)
	_lbl_struct_type.add_theme_color_override("font_color", Color(0.7, 0.88, 0.95, 0.9))
	inf_vbox.add_child(_lbl_struct_type)

	var pos_arr: Array = _structure_data.get("pos", [0.0, 0.0, 0.0])
	_lbl_struct_pos = Label.new()
	_lbl_struct_pos.text = "Coordonnées : Lost Heaven (X: %.1f, Z: %.1f)" % [float(pos_arr[0]), float(pos_arr[2] if pos_arr.size() > 2 else 0.0)]
	_lbl_struct_pos.add_theme_font_size_override("font_size", 9)
	_lbl_struct_pos.add_theme_color_override("font_color", Color(0.5, 0.75, 0.85, 0.8))
	inf_vbox.add_child(_lbl_struct_pos)

	inf_panel.add_child(inf_vbox)
	parent.add_child(inf_panel)

	# Bloc Maintenance Pool
	var maint_panel := PanelContainer.new()
	maint_panel.add_theme_stylebox_override("panel", sb)

	var maint_vbox := VBoxContainer.new()
	maint_vbox.add_theme_constant_override("separation", 6)

	var hdr_maint := Label.new()
	hdr_maint.text = "RÉSERVOIR DE MAINTENANCE (MAINTENANCE POOL) :"
	hdr_maint.add_theme_font_size_override("font_size", 10)
	hdr_maint.add_theme_color_override("font_color", Color(0.4, 0.85, 0.95, 0.9))
	maint_vbox.add_child(hdr_maint)

	var pool_row := HBoxContainer.new()
	_lbl_maint_pool = Label.new()
	_lbl_maint_pool.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_lbl_maint_pool.add_theme_font_size_override("font_size", 11)
	_lbl_maint_pool.add_theme_color_override("font_color", Color(0.35, 0.92, 0.55, 1.0))
	pool_row.add_child(_lbl_maint_pool)

	_lbl_maint_time = Label.new()
	_lbl_maint_time.add_theme_font_size_override("font_size", 10)
	_lbl_maint_time.add_theme_color_override("font_color", Color(0.95, 0.85, 0.4, 1.0))
	pool_row.add_child(_lbl_maint_time)
	maint_vbox.add_child(pool_row)

	_bar_maint = ProgressBar.new()
	_bar_maint.custom_minimum_size = Vector2(0, 10)
	_bar_maint.min_value = 0
	_bar_maint.max_value = 100
	_bar_maint.value = 100
	_bar_maint.show_percentage = false
	maint_vbox.add_child(_bar_maint)

	# Dépôt de crédits
	var dep_row := HBoxContainer.new()
	dep_row.add_theme_constant_override("separation", 8)

	var dep_lbl := Label.new()
	dep_lbl.text = "Déposer crédits :"
	dep_lbl.add_theme_font_size_override("font_size", 10)
	dep_row.add_child(dep_lbl)

	_input_deposit = SpinBox.new()
	_input_deposit.min_value = 100
	_input_deposit.max_value = 100000
	_input_deposit.step = 100
	_input_deposit.value = 1500
	dep_row.add_child(_input_deposit)

	_btn_deposit = Button.new()
	_btn_deposit.text = " Verser au Pool "
	_btn_deposit.add_theme_font_size_override("font_size", 10)
	_btn_deposit.pressed.connect(_on_deposit_pressed)
	dep_row.add_child(_btn_deposit)

	maint_vbox.add_child(dep_row)
	maint_panel.add_child(maint_vbox)
	parent.add_child(maint_panel)

	var warn_lbl := Label.new()
	warn_lbl.text = "⚠ Si le réservoir de maintenance tombe à 0, la structure se dégrade progressivement\net peut être saisie ou démolie conformément aux lois foncières de Lost Heaven."
	warn_lbl.add_theme_font_size_override("font_size", 9)
	warn_lbl.add_theme_color_override("font_color", Color(0.95, 0.6, 0.35, 0.85))
	parent.add_child(warn_lbl)


func _build_acl_tab(parent: VBoxContainer) -> void:
	var top_row := HBoxContainer.new()
	var priv_lbl := Label.new()
	priv_lbl.text = "Statut d'accès à la porte :"
	priv_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	priv_lbl.add_theme_font_size_override("font_size", 10)
	top_row.add_child(priv_lbl)

	_btn_privacy_toggle = Button.new()
	_btn_privacy_toggle.text = " PUBLIC (Visiteurs bienvenus) "
	_btn_privacy_toggle.add_theme_font_size_override("font_size", 10)
	_btn_privacy_toggle.pressed.connect(_toggle_privacy)
	top_row.add_child(_btn_privacy_toggle)
	parent.add_child(top_row)

	var hdr_list := Label.new()
	hdr_list.text = "LISTE D'ACCÈS DES RÉSIDENTS AUTORISÉS (ENTRY LIST) :"
	hdr_list.add_theme_font_size_override("font_size", 10)
	hdr_list.add_theme_color_override("font_color", Color(0.4, 0.85, 0.95, 0.9))
	parent.add_child(hdr_list)

	_entry_list_ui = ItemList.new()
	_entry_list_ui.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_entry_list_ui.add_theme_font_size_override("font_size", 10)
	parent.add_child(_entry_list_ui)

	var add_row := HBoxContainer.new()
	add_row.add_theme_constant_override("separation", 6)

	_input_add_resident = LineEdit.new()
	_input_add_resident.placeholder_text = "Nom du résident à autoriser..."
	_input_add_resident.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_input_add_resident.add_theme_font_size_override("font_size", 10)
	add_row.add_child(_input_add_resident)

	var btn_add := Button.new()
	btn_add.text = " Ajouter "
	btn_add.add_theme_font_size_override("font_size", 10)
	btn_add.pressed.connect(_on_add_resident_pressed)
	add_row.add_child(btn_add)

	var btn_del := Button.new()
	btn_del.text = " Révoquer "
	btn_del.add_theme_font_size_override("font_size", 10)
	btn_del.pressed.connect(_on_del_resident_pressed)
	add_row.add_child(btn_del)

	parent.add_child(add_row)


func _build_city_tab(parent: VBoxContainer) -> void:
	var c_panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.12, 0.16, 0.85)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.24, 0.72, 0.82, 0.7)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	c_panel.add_theme_stylebox_override("panel", sb)

	var cvbox := VBoxContainer.new()
	cvbox.add_theme_constant_override("separation", 8)

	_lbl_city_name = Label.new()
	_lbl_city_name.text = "Municipalité : %s" % str(_structure_data.get("city_name", "Oasis de Scrapaltai"))
	_lbl_city_name.add_theme_font_size_override("font_size", 12)
	_lbl_city_name.add_theme_color_override("font_color", Color(0.96, 0.88, 0.42, 1.0))
	cvbox.add_child(_lbl_city_name)

	_lbl_city_rank = Label.new()
	_lbl_city_rank.text = "Rang Municipal : %s" % str(_structure_data.get("city_rank", "Village"))
	_lbl_city_rank.add_theme_font_size_override("font_size", 10)
	_lbl_city_rank.add_theme_color_override("font_color", Color(0.7, 0.88, 0.95, 0.9))
	cvbox.add_child(_lbl_city_rank)

	_lbl_city_mayor = Label.new()
	_lbl_city_mayor.text = "Maire en exercice : %s (Élections ouvertes tous les 21 jours)" % str(_structure_data.get("city_mayor", "Odo Merr"))
	_lbl_city_mayor.add_theme_font_size_override("font_size", 10)
	_lbl_city_mayor.add_theme_color_override("font_color", Color(0.5, 0.85, 0.65, 0.9))
	cvbox.add_child(_lbl_city_mayor)

	_lbl_city_tax = Label.new()
	_lbl_city_tax.text = "Taxes Foncières : %d%% prélevés sur chaque heure de maintenance." % int(_structure_data.get("property_tax_pct", 4))
	_lbl_city_tax.add_theme_font_size_override("font_size", 10)
	_lbl_city_tax.add_theme_color_override("font_color", Color(0.85, 0.75, 0.5, 0.85))
	cvbox.add_child(_lbl_city_tax)

	c_panel.add_child(cvbox)
	parent.add_child(c_panel)

	var info := Label.new()
	info.text = "ℹ Les citoyens de la ville bénéficient de bonus de régénération, de terminaux de clonage\net de banques de quartier. Vous pouvez voter pour les prochaines élections municipales."
	info.add_theme_font_size_override("font_size", 9)
	info.add_theme_color_override("font_color", Color(0.65, 0.85, 0.95, 0.8))
	parent.add_child(info)


func _switch_tab(tab_idx: int) -> void:
	_current_tab = tab_idx
	if _box_maint:
		_box_maint.visible = (_current_tab == 0)
	if _box_acl:
		_box_acl.visible = (_current_tab == 1)
	if _box_city:
		_box_city.visible = (_current_tab == 2)


func _update_views() -> void:
	var cur_pool: int = int(_structure_data.get("maintenance_credits", 0))
	var rate: int = maxi(1, int(_structure_data.get("maintenance_rate_hourly", 15)))
	var hours_left: float = float(cur_pool) / float(rate)
	var days_left: float = hours_left / 24.0

	if _lbl_maint_pool:
		_lbl_maint_pool.text = "Solde : %d cr (Coût : %d cr / h)" % [cur_pool, rate]
	if _lbl_maint_time:
		_lbl_maint_time.text = "Autonomie : %.1f jours (%.0f heures)" % [days_left, hours_left]
	if _bar_maint:
		_bar_maint.value = clampf(days_left / 30.0 * 100.0, 5.0, 100.0)

	var is_pub: bool = bool(_structure_data.get("is_public", true))
	if _btn_privacy_toggle:
		_btn_privacy_toggle.text = " PUBLIC (Visiteurs bienvenus) " if is_pub else " PRIVÉ (Résidents autorisés uniquement) "

	if _entry_list_ui:
		_entry_list_ui.clear()
		var el: Array = _structure_data.get("entry_list", [])
		for r in el:
			_entry_list_ui.add_item("◈ %s" % str(r))


func _on_deposit_pressed() -> void:
	var amt := int(_input_deposit.value) if _input_deposit else 100
	if player_credits < amt:
		return
	player_credits -= amt
	var cur := int(_structure_data.get("maintenance_credits", 0))
	_structure_data["maintenance_credits"] = cur + amt
	_update_views()

	var s_id := str(_structure_data.get("id", "house_01"))
	maintenance_paid.emit(s_id, amt)

	if _http and _http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
		var url := "%s/v1/housing/maintenance/pay" % sidecar_base_url.rstrip("/")
		_http.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({
			"player": player_name,
			"structure_id": s_id,
			"amount": amt
		}))


func _toggle_privacy() -> void:
	var cur: bool = bool(_structure_data.get("is_public", true))
	_structure_data["is_public"] = not cur
	_update_views()

	var s_id := str(_structure_data.get("id", "house_01"))
	if _http and _http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
		var url := "%s/v1/housing/acl" % sidecar_base_url.rstrip("/")
		_http.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({
			"player": player_name,
			"structure_id": s_id,
			"is_public": _structure_data["is_public"]
		}))


func _on_add_resident_pressed() -> void:
	var r_name := _input_add_resident.text.strip_edges() if _input_add_resident else ""
	if r_name.is_empty():
		return
	var el: Array = _structure_data.get("entry_list", [])
	if not el.has(r_name):
		el.append(r_name)
		_structure_data["entry_list"] = el
		_update_views()
	if _input_add_resident:
		_input_add_resident.text = ""


func _on_del_resident_pressed() -> void:
	var sel: PackedInt32Array = _entry_list_ui.get_selected_items() if _entry_list_ui else PackedInt32Array()
	var el: Array = _structure_data.get("entry_list", [])
	if sel.is_empty() or sel[0] >= el.size():
		return
	el.remove_at(sel[0])
	_structure_data["entry_list"] = el
	_update_views()


func toggle() -> void:
	if visible:
		close_panel()
	else:
		open_panel()


func open_panel() -> void:
	visible = true
	panel_visible = true
	refresh_structure()


func close_panel() -> void:
	visible = false
	panel_visible = false
	panel_closed.emit()


func refresh_structure() -> void:
	_apply_runtime_cfg()
	if _http == null or not is_inside_tree():
		return
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	var s_id := str(_structure_data.get("id", "house_lh_001"))
	var url := "%s/v1/housing/structure?structure_id=%s" % [sidecar_base_url.rstrip("/"), s_id.uri_encode()]
	_http.request(url, [], HTTPClient.METHOD_GET)


func _on_http_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) == TYPE_DICTIONARY and (parsed as Dictionary).has("structure"):
		var st_dict: Dictionary = (parsed as Dictionary)["structure"]
		for k in st_dict.keys():
			_structure_data[k] = st_dict[k]
		_update_views()
