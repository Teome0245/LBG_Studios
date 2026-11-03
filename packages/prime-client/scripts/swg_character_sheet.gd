extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Fiche de Personnage & 9 Attributs HAM :
## 1. En-tête : Nom, Titre honorifique, Faction/Statut, Posture actuelle, Jauge de Battle Fatigue (0-1000).
## 2. 9 Attributs HAM répartis en 3 colonnes :
##    - Santé : Health (barre rouge + Wounds), Strength (réduction coûts), Constitution (regen).
##    - Action : Action (barre verte + Wounds), Quickness (vitesse/coûts), Stamina (regen).
##    - Esprit : Mind (barre bleue + Wounds), Focus (réduction coûts Mind), Willpower (regen).
## 3. Panneau des Résistances (Armure) et explications des blessures.

signal sheet_closed()

const _HubRuntimeCfg := preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_name: String = "Voyageur"
var panel_visible: bool = false

var _title: String = "Pionnier des Sables"
var _citizenship: String = "Citoyen Libre de Lost Heaven"
var _posture_label: String = "Debout"
var _battle_fatigue: int = 0
var _medical_efficiency: float = 1.0

# 9 Attributs SWG : Health, Strength, Constitution, Action, Quickness, Stamina, Mind, Focus, Willpower
var _stats: Dictionary = {
	"health": {"current": 1000, "base_max": 1000, "wounds": 0, "buff": 0},
	"strength": {"current": 650, "base_max": 650, "wounds": 0, "buff": 0},
	"constitution": {"current": 650, "base_max": 650, "wounds": 0, "buff": 0},
	"action": {"current": 1000, "base_max": 1000, "wounds": 0, "buff": 0},
	"quickness": {"current": 650, "base_max": 650, "wounds": 0, "buff": 0},
	"stamina": {"current": 650, "base_max": 650, "wounds": 0, "buff": 0},
	"mind": {"current": 1000, "base_max": 1000, "wounds": 0, "buff": 0},
	"focus": {"current": 650, "base_max": 650, "wounds": 0, "buff": 0},
	"willpower": {"current": 650, "base_max": 650, "wounds": 0, "buff": 0},
}

# Résistances d'armure (%)
var _resistances: Dictionary = {
	"cinetique": 25,
	"energie": 20,
	"chaleur": 10,
	"froid": 10,
	"acide": 5,
	"electricite": 15
}

# Références UI
var _lbl_name: Label = null
var _lbl_title: Label = null
var _lbl_posture: Label = null
var _lbl_fatigue: Label = null
var _bar_fatigue: ProgressBar = null
var _stat_labels: Dictionary = {}
var _stat_bars: Dictionary = {}
var _http: HTTPRequest = null


func _ready() -> void:
	visible = panel_visible
	custom_minimum_size = Vector2(560, 480)
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)
	refresh_from_server()


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
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 10
	sb.content_margin_bottom = 14
	add_theme_stylebox_override("panel", sb)


func _build_ui() -> void:
	for c in get_children():
		if c != _http:
			c.queue_free()

	var root_vbox := VBoxContainer.new()
	root_vbox.add_theme_constant_override("separation", 8)
	add_child(root_vbox)

	# --- En-tête de fenêtre ---
	var header := HBoxContainer.new()
	var title_lbl := Label.new()
	title_lbl.text = "◈ FICHE DU PERSONNAGE & ATTRIBUTS HAM ◈"
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

	# Ligne séparatrice
	var hsep1 := HSeparator.new()
	root_vbox.add_child(hsep1)

	# --- Bloc Profil & Citoyenneté ---
	var prof_box := HBoxContainer.new()
	prof_box.add_theme_constant_override("separation", 16)

	var left_info := VBoxContainer.new()
	left_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	_lbl_name = Label.new()
	_lbl_name.text = "Nom : %s" % player_name
	_lbl_name.add_theme_font_size_override("font_size", 12)
	_lbl_name.add_theme_color_override("font_color", Color(0.85, 0.96, 1.0, 1.0))
	left_info.add_child(_lbl_name)

	_lbl_title = Label.new()
	_lbl_title.text = "Titre : « %s » | %s" % [_title, _citizenship]
	_lbl_title.add_theme_font_size_override("font_size", 10)
	_lbl_title.add_theme_color_override("font_color", Color(0.65, 0.88, 0.95, 0.85))
	left_info.add_child(_lbl_title)
	prof_box.add_child(left_info)

	var right_info := VBoxContainer.new()
	right_info.custom_minimum_size = Vector2(210, 0)

	_lbl_posture = Label.new()
	_lbl_posture.text = "Posture : %s" % _posture_label.to_upper()
	_lbl_posture.add_theme_font_size_override("font_size", 11)
	_lbl_posture.add_theme_color_override("font_color", Color(0.35, 0.92, 0.55, 1.0))
	right_info.add_child(_lbl_posture)

	# Battle Fatigue
	_lbl_fatigue = Label.new()
	_lbl_fatigue.text = "Fatigue de Combat : %d / 1000 (Efficacité: %d%%)" % [_battle_fatigue, int(_medical_efficiency * 100.0)]
	_lbl_fatigue.add_theme_font_size_override("font_size", 10)
	_lbl_fatigue.add_theme_color_override("font_color", Color(1.0, 0.65, 0.25, 1.0))
	right_info.add_child(_lbl_fatigue)

	_bar_fatigue = ProgressBar.new()
	_bar_fatigue.custom_minimum_size = Vector2(200, 10)
	_bar_fatigue.min_value = 0
	_bar_fatigue.max_value = 1000
	_bar_fatigue.value = _battle_fatigue
	_bar_fatigue.show_percentage = false
	right_info.add_child(_bar_fatigue)

	prof_box.add_child(right_info)
	root_vbox.add_child(prof_box)

	var hsep2 := HSeparator.new()
	root_vbox.add_child(hsep2)

	# --- Les 9 Attributs du HAM SWG en 3 Colonnes ---
	var cols_box := HBoxContainer.new()
	cols_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	cols_box.add_theme_constant_override("separation", 12)

	# 1. Colonne Santé (Rouge)
	var col_health := _build_stat_column("SANTÉ (CORPS)", Color(0.92, 0.22, 0.25, 1.0), [
		{"k": "health", "lbl": "Santé (Health)", "desc": "Réserve vitale. Épuisée = Étourdissement/Mort."},
		{"k": "strength", "lbl": "Force (Strength)", "desc": "Réduit le coût en Action et Santé."},
		{"k": "constitution", "lbl": "Constitution", "desc": "Accélère la régénération passive de Santé."}
	])
	cols_box.add_child(col_health)

	# 2. Colonne Action (Verte)
	var col_action := _build_stat_column("ACTION (ÉNERGIE)", Color(0.22, 0.88, 0.35, 1.0), [
		{"k": "action", "lbl": "Action (Action)", "desc": "Énergie physique requise pour frapper/courir."},
		{"k": "quickness", "lbl": "Vivacité (Quickness)", "desc": "Réduit les délais et temps de réaction."},
		{"k": "stamina", "lbl": "Résistance (Stamina)", "desc": "Accélère la régénération passive d'Action."}
	])
	cols_box.add_child(col_action)

	# 3. Colonne Mental (Bleue)
	var col_mind := _build_stat_column("ESPRIT (MENTAL)", Color(0.22, 0.65, 0.95, 1.0), [
		{"k": "mind", "lbl": "Esprit (Mind)", "desc": "Concentration mentale. Épuisée = Perte de conscience."},
		{"k": "focus", "lbl": "Focus (Concentration)", "desc": "Réduit le coût en Mind des crafts/tirs."},
		{"k": "willpower", "lbl": "Volonté (Willpower)", "desc": "Accélère la régénération passive d'Esprit."}
	])
	cols_box.add_child(col_mind)

	root_vbox.add_child(cols_box)

	# --- Résistances et Explications Wounds ---
	var bot_box := HBoxContainer.new()
	bot_box.add_theme_constant_override("separation", 12)

	var res_box := VBoxContainer.new()
	res_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var res_hdr := Label.new()
	res_hdr.text = "RÉSISTANCES D'ARMURE (COMPOSITE SC-4) :"
	res_hdr.add_theme_font_size_override("font_size", 9)
	res_hdr.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.9))
	res_box.add_child(res_hdr)

	var res_txt := Label.new()
	res_txt.text = "Cinétique: %d%% | Énergie: %d%% | Chaleur: %d%% | Froid: %d%% | Acide: %d%% | Élec: %d%%" % [
		_resistances["cinetique"], _resistances["energie"], _resistances["chaleur"],
		_resistances["froid"], _resistances["acide"], _resistances["electricite"]
	]
	res_txt.add_theme_font_size_override("font_size", 9)
	res_txt.add_theme_color_override("font_color", Color(0.70, 0.85, 0.95, 0.8))
	res_box.add_child(res_txt)
	bot_box.add_child(res_box)

	var note_lbl := Label.new()
	note_lbl.text = "ℹ Les Blessures (Wounds) bloquent le pool max.\nSoins possibles uniquement en Camp Scout ou Centre Médical."
	note_lbl.add_theme_font_size_override("font_size", 9)
	note_lbl.add_theme_color_override("font_color", Color(0.95, 0.75, 0.35, 0.9))
	bot_box.add_child(note_lbl)

	root_vbox.add_child(bot_box)

	# --- Barre d'actions du bas ---
	var act_row := HBoxContainer.new()
	act_row.add_theme_constant_override("separation", 10)

	var refresh_btn := Button.new()
	refresh_btn.text = " ↻ Actualiser Données "
	refresh_btn.add_theme_font_size_override("font_size", 10)
	refresh_btn.pressed.connect(refresh_from_server)
	act_row.add_child(refresh_btn)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	act_row.add_child(spacer)

	var done_btn := Button.new()
	done_btn.text = " Fermer [Échap] "
	done_btn.add_theme_font_size_override("font_size", 10)
	done_btn.pressed.connect(close_panel)
	act_row.add_child(done_btn)

	root_vbox.add_child(act_row)


func _build_stat_column(header_text: String, col_color: Color, stats_meta: Array) -> VBoxContainer:
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 6)

	var hdr := Label.new()
	hdr.text = header_text
	hdr.add_theme_font_size_override("font_size", 11)
	hdr.add_theme_color_override("font_color", col_color)
	col.add_child(hdr)

	for item in stats_meta:
		var d: Dictionary = item
		var k := str(d["k"])
		var s_data: Dictionary = _stats.get(k, {"current": 1000, "base_max": 1000, "wounds": 0, "buff": 0})

		var item_box := VBoxContainer.new()
		item_box.add_theme_constant_override("separation", 2)

		var line := HBoxContainer.new()
		var name_lbl := Label.new()
		name_lbl.text = str(d["lbl"])
		name_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_lbl.add_theme_font_size_override("font_size", 10)
		name_lbl.add_theme_color_override("font_color", Color(0.9, 0.95, 1.0, 1.0))
		line.add_child(name_lbl)

		var val_lbl := Label.new()
		val_lbl.text = "%d / %d" % [int(s_data.get("current", 1000)), int(s_data.get("base_max", 1000))]
		val_lbl.add_theme_font_size_override("font_size", 10)
		val_lbl.add_theme_color_override("font_color", col_color)
		_stat_labels[k] = val_lbl
		line.add_child(val_lbl)
		item_box.add_child(line)

		var bar := ProgressBar.new()
		bar.custom_minimum_size = Vector2(120, 8)
		bar.min_value = 0
		bar.max_value = maxi(10, int(s_data.get("base_max", 1000)))
		bar.value = int(s_data.get("current", 1000))
		bar.show_percentage = false
		_stat_bars[k] = bar
		item_box.add_child(bar)

		var sub_lbl := Label.new()
		var w: int = int(s_data.get("wounds", 0))
		var b: int = int(s_data.get("buff", 0))
		sub_lbl.text = "Blessures: %d | Buff: +%d" % [w, b]
		sub_lbl.add_theme_font_size_override("font_size", 8)
		sub_lbl.add_theme_color_override("font_color", Color(0.85, 0.5, 0.5, 0.8) if w > 0 else Color(0.6, 0.7, 0.75, 0.6))
		item_box.add_child(sub_lbl)

		col.add_child(item_box)

	return col


func toggle() -> void:
	if visible:
		close_panel()
	else:
		open_panel()


func open_panel() -> void:
	visible = true
	panel_visible = true
	refresh_from_server()


func close_panel() -> void:
	visible = false
	panel_visible = false
	sheet_closed.emit()


func apply_character_data(d: Dictionary) -> void:
	if d.has("player_name"):
		player_name = str(d["player_name"])
	if d.has("title"):
		_title = str(d["title"])
	if d.has("citizenship"):
		_citizenship = str(d["citizenship"])
	if d.has("posture"):
		_posture_label = str(d["posture"])
	if d.has("battle_fatigue"):
		_battle_fatigue = int(d["battle_fatigue"])
	if d.has("medical_efficiency_ratio"):
		_medical_efficiency = float(d["medical_efficiency_ratio"])
	if d.has("stats") and typeof(d["stats"]) == TYPE_DICTIONARY:
		for k in (d["stats"] as Dictionary).keys():
			_stats[str(k)] = d["stats"][k]
	elif d.has("ham") and typeof(d["ham"]) == TYPE_DICTIONARY:
		var ham: Dictionary = d["ham"]
		for k in ["health", "action", "mind"]:
			if ham.has(k) and typeof(ham[k]) == TYPE_DICTIONARY:
				_stats[k] = ham[k]
		if ham.has("battle_fatigue"):
			_battle_fatigue = int(ham["battle_fatigue"])

	_update_views()


func _update_views() -> void:
	if _lbl_name:
		_lbl_name.text = "Nom : %s" % player_name
	if _lbl_title:
		_lbl_title.text = "Titre : « %s » | %s" % [_title, _citizenship]
	if _lbl_posture:
		_lbl_posture.text = "Posture : %s" % _posture_label.to_upper()
	if _lbl_fatigue:
		_lbl_fatigue.text = "Fatigue de Combat : %d / 1000 (Efficacité: %d%%)" % [_battle_fatigue, int(_medical_efficiency * 100.0)]
	if _bar_fatigue:
		_bar_fatigue.value = _battle_fatigue

	for k in _stats.keys():
		var s_data: Dictionary = _stats[k]
		if _stat_labels.has(k) and _stat_labels[k] != null:
			var cur: int = int(s_data.get("current", 1000))
			var b_max: int = int(s_data.get("base_max", 1000))
			var w: int = int(s_data.get("wounds", 0))
			var eff_max: int = maxi(10, b_max - w)
			(_stat_labels[k] as Label).text = "%d / %d" % [cur, eff_max]
		if _stat_bars.has(k) and _stat_bars[k] != null:
			var b: ProgressBar = _stat_bars[k]
			b.max_value = maxi(10, int(s_data.get("base_max", 1000)))
			b.value = int(s_data.get("current", 1000))


func refresh_from_server() -> void:
	_apply_runtime_cfg()
	if _http == null or not is_inside_tree():
		return
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	var url := "%s/v1/medical/status?player=%s" % [sidecar_base_url.rstrip("/"), player_name.uri_encode()]
	_http.request(url, [], HTTPClient.METHOD_GET)


func _on_http_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) == TYPE_DICTIONARY:
		apply_character_data(parsed as Dictionary)
