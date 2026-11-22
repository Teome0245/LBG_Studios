# swg_spellbook_panel.gd — Grimoire T4C & Arcanes pour Prime
# Fusionne le Grimoire de sorts (La 4ème Prophétie) avec l'interface Holo SWG.
# Permet de visualiser les sorts, leurs prérequis (INT/SAG/Karma), les coûts en Mind,
# de lancer les sorts en 1 clic ou de les assigner à la barre d'action.
extends PanelContainer
class_name SwgSpellbookPanel

signal spell_cast_requested(spell_id: String)
signal spell_assign_requested(spell_id: String, spell_data: Dictionary)
signal panel_closed()

const _HubRuntimeCfg := preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_name: String = "Voyageur"
var panel_visible: bool = false

# Données T4C du joueur
var player_karma: int = 0
var karma_rank: String = "Neutre"
var stats_t4c: Dictionary = {
	"strength": 20,
	"endurance": 20,
	"dexterity": 20,
	"intelligence": 20,
	"wisdom": 20,
	"unspent_stat_points": 5,
	"level": 1,
	"seraph_wings": 0
}

# Catalogue canonique des sorts T4C (aligné sur hub_t4c_system.gd)
var spells_catalog: Dictionary = {
	"etincelle": {
		"id": "etincelle",
		"name": "Étincelle Arcanique",
		"school": "feu_air",
		"color": Color(1.0, 0.45, 0.2),
		"req_intelligence": 20,
		"req_wisdom": 0,
		"mind_cost": 30,
		"power": 65,
		"desc": "Projette une gerbe d'étincelles énergétiques sur la cible."
	},
	"guerison_mineure": {
		"id": "guerison_mineure",
		"name": "Guérison Mineure",
		"school": "lumiere",
		"color": Color(0.3, 0.95, 0.45),
		"req_intelligence": 0,
		"req_wisdom": 25,
		"mind_cost": 35,
		"heal_amount": 120,
		"desc": "Canalise la foi bienveillante pour refermer les plaies légères (+120 Santé)."
	},
	"bouclier_de_terre": {
		"id": "bouclier_de_terre",
		"name": "Bouclier de Silice",
		"school": "terre",
		"color": Color(0.85, 0.7, 0.3),
		"req_intelligence": 25,
		"req_endurance": 30,
		"mind_cost": 50,
		"buff_armor": 20,
		"desc": "Durcit les poussières de Scrapaltai autour du corps (+20% armure)."
	},
	"eclair_de_plasma": {
		"id": "eclair_de_plasma",
		"name": "Éclair de Plasma",
		"school": "feu_air",
		"color": Color(0.4, 0.75, 1.0),
		"req_intelligence": 45,
		"req_wisdom": 15,
		"mind_cost": 75,
		"power": 240,
		"desc": "Foudroie la cible avec un arc électrique ionisé à haute température."
	},
	"priere_seraphin": {
		"id": "priere_seraphin",
		"name": "Prière du Séraphin",
		"school": "divin",
		"color": Color(1.0, 0.9, 0.35),
		"req_wisdom": 50,
		"req_intelligence": 20,
		"min_karma": 200,
		"mind_cost": 110,
		"heal_amount": 380,
		"desc": "[Séraphin / Pur] Soigne intensément (+380 Santé) et traite les blessures HAM."
	},
	"souffle_de_l_abyme": {
		"id": "souffle_de_l_abyme",
		"name": "Souffle de l'Abyme",
		"school": "necro",
		"color": Color(0.8, 0.2, 0.9),
		"req_intelligence": 50,
		"req_wisdom": 10,
		"max_karma": -200,
		"mind_cost": 120,
		"power": 360,
		"desc": "[Terreur des Sables] Draine la vitalité vitale en ignorant 50% d'armure adverse."
	}
}

var _selected_spell_id: String = "etincelle"
var _http: HTTPRequest = null
var _lbl_karma: Label = null
var _lbl_stats_summary: Label = null
var _spell_detail_box: VBoxContainer = null
var _cast_button: Button = null


func _ready() -> void:
	visible = panel_visible
	custom_minimum_size = Vector2(580, 440)
	_apply_runtime_cfg()
	_apply_style()
	_build_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)
	refresh_grimoire()


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_name = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.08, 0.14, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.2, 0.85, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 10
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	if visible:
		refresh_grimoire()


func close_panel() -> void:
	panel_visible = false
	visible = false
	panel_closed.emit()


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
	title_lbl.text = "◈ GRIMOIRE DES SORTS T4C & POUVOIRS DE L'ESPRIT ◈"
	title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_lbl.add_theme_font_size_override("font_size", 13)
	title_lbl.add_theme_color_override("font_color", Color(0.95, 0.82, 0.35, 1.0))
	header.add_child(title_lbl)

	var close_btn := Button.new()
	close_btn.text = " ✕ "
	close_btn.add_theme_font_size_override("font_size", 11)
	close_btn.pressed.connect(close_panel)
	header.add_child(close_btn)
	root_vbox.add_child(header)

	var hsep1 := HSeparator.new()
	root_vbox.add_child(hsep1)

	# --- Barre de Résumé Karma & Attributs ---
	var bar_summary := HBoxContainer.new()
	bar_summary.add_theme_constant_override("separation", 16)

	_lbl_karma = Label.new()
	_lbl_karma.text = "Karma : %d (%s)" % [player_karma, karma_rank]
	_lbl_karma.add_theme_font_size_override("font_size", 11)
	_lbl_karma.add_theme_color_override("font_color", Color(0.35, 0.9, 0.95, 1.0))
	bar_summary.add_child(_lbl_karma)

	_lbl_stats_summary = Label.new()
	_lbl_stats_summary.text = "INT: %d  |  SAG: %d  |  Pts Libres: %d" % [
		int(stats_t4c.get("intelligence", 20)),
		int(stats_t4c.get("wisdom", 20)),
		int(stats_t4c.get("unspent_stat_points", 0))
	]
	_lbl_stats_summary.add_theme_font_size_override("font_size", 11)
	_lbl_stats_summary.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85, 1.0))
	bar_summary.add_child(_lbl_stats_summary)

	root_vbox.add_child(bar_summary)

	# --- Corps Principal (2 Colonnes : Liste des Sorts / Détails & Lancement) ---
	var body_box := HBoxContainer.new()
	body_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body_box.add_theme_constant_override("separation", 12)

	# Colonne de Gauche : Liste des Sorts
	var list_scroll := ScrollContainer.new()
	list_scroll.custom_minimum_size = Vector2(240, 0)
	list_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL

	var list_vbox := VBoxContainer.new()
	list_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list_vbox.add_theme_constant_override("separation", 4)

	for spell_id: String in spells_catalog.keys():
		var s: Dictionary = spells_catalog[spell_id]
		var btn := Button.new()
		btn.text = "✦ " + str(s.get("name", spell_id))
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.add_theme_font_size_override("font_size", 11)
		var scol: Color = s.get("color", Color.WHITE)
		btn.add_theme_color_override("font_color", scol)
		btn.pressed.connect(func() -> void:
			_select_spell(spell_id)
		)
		list_vbox.add_child(btn)

	list_scroll.add_child(list_vbox)
	body_box.add_child(list_scroll)

	# Colonne de Droite : Fiche Technique & Lancement
	_spell_detail_box = VBoxContainer.new()
	_spell_detail_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_spell_detail_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_spell_detail_box.add_theme_constant_override("separation", 6)
	body_box.add_child(_spell_detail_box)

	root_vbox.add_child(body_box)

	_update_spell_details()


func _select_spell(spell_id: String) -> void:
	_selected_spell_id = spell_id
	_update_spell_details()


func _update_spell_details() -> void:
	if _spell_detail_box == null:
		return

	for c in _spell_detail_box.get_children():
		c.queue_free()

	var s: Dictionary = spells_catalog.get(_selected_spell_id, {})
	if s.is_empty():
		return

	var s_name := Label.new()
	s_name.text = str(s.get("name", "Sort inconnu"))
	s_name.add_theme_font_size_override("font_size", 14)
	s_name.add_theme_color_override("font_color", s.get("color", Color.WHITE))
	_spell_detail_box.add_child(s_name)

	var s_school := Label.new()
	s_school.text = "École de Magie : %s  |  Coût : %d Mind (HAM)" % [str(s.get("school", "")).to_upper(), int(s.get("mind_cost", 0))]
	s_school.add_theme_font_size_override("font_size", 10)
	s_school.add_theme_color_override("font_color", Color(0.65, 0.85, 0.95, 1.0))
	_spell_detail_box.add_child(s_school)

	var s_desc := Label.new()
	s_desc.text = str(s.get("desc", ""))
	s_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	s_desc.add_theme_font_size_override("font_size", 11)
	s_desc.add_theme_color_override("font_color", Color(0.9, 0.9, 0.9, 1.0))
	_spell_detail_box.add_child(s_desc)

	# Prérequis
	var req_lbl := Label.new()
	var req_text := "Prérequis stricts T4C :"
	var req_int: int = int(s.get("req_intelligence", 0))
	var req_wis: int = int(s.get("req_wisdom", 0))
	var req_end: int = int(s.get("req_endurance", 0))
	if req_int > 0: req_text += " INT ≥ %d" % req_int
	if req_wis > 0: req_text += " SAG ≥ %d" % req_wis
	if req_end > 0: req_text += " END ≥ %d" % req_end
	if s.has("min_karma"): req_text += " | Karma ≥ %d" % int(s["min_karma"])
	if s.has("max_karma"): req_text += " | Karma ≤ %d" % int(s["max_karma"])
	req_lbl.text = req_text
	req_lbl.add_theme_font_size_override("font_size", 10)
	req_lbl.add_theme_color_override("font_color", Color(1.0, 0.75, 0.25, 1.0))
	_spell_detail_box.add_child(req_lbl)

	_spell_detail_box.add_spacer(false)

	# Boutons d'Action
	var act_box := HBoxContainer.new()
	act_box.add_theme_constant_override("separation", 10)

	_cast_button = Button.new()
	_cast_button.text = "⚡ Incanter le Sort"
	_cast_button.custom_minimum_size = Vector2(140, 32)
	_cast_button.pressed.connect(_cast_current_spell)
	act_box.add_child(_cast_button)

	var assign_btn := Button.new()
	assign_btn.text = "📥 Placer sur la Hotbar"
	assign_btn.custom_minimum_size = Vector2(150, 32)
	assign_btn.pressed.connect(func() -> void:
		spell_assign_requested.emit(_selected_spell_id, s)
	)
	act_box.add_child(assign_btn)

	_spell_detail_box.add_child(act_box)


func _cast_current_spell() -> void:
	if _selected_spell_id.is_empty():
		return
	spell_cast_requested.emit(_selected_spell_id)
	if _http == null:
		return

	var url := sidecar_base_url.rstrip("/") + "/v1/t4c/cast"
	var body_dict := {
		"player": player_name,
		"spell_id": _selected_spell_id,
		"target": ""
	}
	var headers := PackedStringArray(["Content-Type: application/json"])
	_http.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(body_dict))


func refresh_grimoire() -> void:
	if _http == null:
		return
	var url := sidecar_base_url.rstrip("/") + "/v1/t4c/stats?player=" + player_name.uri_encode()
	_http.request(url, PackedStringArray([]), HTTPClient.METHOD_GET)


func _on_http_completed(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200:
		return
	var json_str := body.get_string_from_utf8()
	var parsed: Variant = JSON.parse_string(json_str)
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d: Dictionary = parsed

	if d.has("karma"):
		player_karma = int(d["karma"])
	if d.has("karma_rank"):
		karma_rank = str(d["karma_rank"])
	if d.has("stats"):
		stats_t4c = d["stats"]

	if _lbl_karma != null:
		_lbl_karma.text = "Karma : %d (%s)" % [player_karma, karma_rank]
	if _lbl_stats_summary != null:
		_lbl_stats_summary.text = "INT: %d  |  SAG: %d  |  Pts Libres: %d" % [
			int(stats_t4c.get("intelligence", 20)),
			int(stats_t4c.get("wisdom", 20)),
			int(stats_t4c.get("unspent_stat_points", 0))
		]
