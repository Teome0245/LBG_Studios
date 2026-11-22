# defeat_overlay_panel.gd — Interface de Défaite & Capture Alternative (Prime Client)
# Mécanique mature 18+ (Defeat System façon Wicked Island) : Lutte QTE, Rançon ou Soumission.
extends Control
class_name DefeatOverlayPanel

signal struggle_requested(effort: float)
signal submit_requested()
signal ransom_requested()
signal closed()

var _panel: Panel = null
var _title_lbl: Label = null
var _narrative_lbl: Label = null
var _struggle_bar: ProgressBar = null
var _struggle_lbl: Label = null
var _timer_lbl: Label = null

var _btn_struggle: Button = null
var _btn_submit: Button = null
var _btn_ransom: Button = null

var current_session: Dictionary = {}
var time_left: float = 30.0
var struggle_val: float = 0.0


func _init() -> void:
	name = "DefeatOverlayPanel"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	_build_ui()


func _build_ui() -> void:
	# Fond assombri d'ambiance défaite / vignette
	var backdrop := ColorRect.new()
	backdrop.name = "Backdrop"
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	backdrop.color = Color(0.04, 0.02, 0.05, 0.78)
	add_child(backdrop)

	_panel = Panel.new()
	_panel.name = "DefeatPanel"
	_panel.set_anchors_preset(Control.PRESET_CENTER)
	_panel.offset_left = -260
	_panel.offset_top = -180
	_panel.offset_right = 260
	_panel.offset_bottom = 180

	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.12, 0.05, 0.08, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.85, 0.22, 0.35, 0.9)
	sb.set_corner_radius_all(8)
	sb.shadow_color = Color(0.6, 0.05, 0.15, 0.4)
	sb.shadow_size = 12
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	# Titre d'état
	_title_lbl = Label.new()
	_title_lbl.name = "TitleLabel"
	_title_lbl.position = Vector2(16, 12)
	_title_lbl.size = Vector2(488, 28)
	_title_lbl.text = "HORS DE COMBAT — CAPTURÉ"
	_title_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title_lbl.add_theme_font_size_override("font_size", 16)
	_title_lbl.add_theme_color_override("font_color", Color(1.0, 0.35, 0.45))
	_panel.add_child(_title_lbl)

	# Texte descriptif / narratif
	_narrative_lbl = Label.new()
	_narrative_lbl.name = "NarrativeLabel"
	_narrative_lbl.position = Vector2(24, 46)
	_narrative_lbl.size = Vector2(472, 70)
	_narrative_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_narrative_lbl.text = "Vos forces vous abandonnent. Vos assaillants vous maîtrisent au sol et s'apprêtent à vous emmener comme trophée..."
	_narrative_lbl.add_theme_font_size_override("font_size", 13)
	_narrative_lbl.add_theme_color_override("font_color", Color(0.92, 0.85, 0.88))
	_panel.add_child(_narrative_lbl)

	# Barre de lutte (QTE)
	_struggle_bar = ProgressBar.new()
	_struggle_bar.name = "StruggleBar"
	_struggle_bar.position = Vector2(30, 125)
	_struggle_bar.size = Vector2(460, 24)
	_struggle_bar.min_value = 0.0
	_struggle_bar.max_value = 100.0
	_struggle_bar.value = 0.0
	_struggle_bar.show_percentage = false
	_panel.add_child(_struggle_bar)

	_struggle_lbl = Label.new()
	_struggle_lbl.name = "StruggleLabel"
	_struggle_lbl.position = Vector2(30, 127)
	_struggle_lbl.size = Vector2(460, 20)
	_struggle_lbl.text = "Lutte d'évasion : 0%"
	_struggle_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_struggle_lbl.add_theme_font_size_override("font_size", 12)
	_panel.add_child(_struggle_lbl)

	# Timer restant
	_timer_lbl = Label.new()
	_timer_lbl.name = "TimerLabel"
	_timer_lbl.position = Vector2(30, 155)
	_timer_lbl.size = Vector2(460, 20)
	_timer_lbl.text = "Temps avant soumission forcée : 30 s"
	_timer_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_timer_lbl.add_theme_font_size_override("font_size", 11)
	_timer_lbl.add_theme_color_override("font_color", Color(0.75, 0.65, 0.70))
	_panel.add_child(_timer_lbl)

	# Conteneur des boutons d'actions
	var btn_box := HBoxContainer.new()
	btn_box.position = Vector2(24, 210)
	btn_box.size = Vector2(472, 40)
	btn_box.alignment = BoxContainer.ALIGNMENT_CENTER
	btn_box.add_theme_constant_override("separation", 16)
	_panel.add_child(btn_box)

	# Bouton Lutter (QTE)
	_btn_struggle = Button.new()
	_btn_struggle.text = "Lutter [Espace]"
	_btn_struggle.custom_minimum_size = Vector2(130, 36)
	_btn_struggle.pressed.connect(_on_struggle_pressed)
	btn_box.add_child(_btn_struggle)

	# Bouton Rançon
	_btn_ransom = Button.new()
	_btn_ransom.text = "Payer Rançon (150 Cr)"
	_btn_ransom.custom_minimum_size = Vector2(160, 36)
	_btn_ransom.pressed.connect(_on_ransom_pressed)
	btn_box.add_child(_btn_ransom)

	# Bouton Soumission
	_btn_submit = Button.new()
	_btn_submit.text = "Se Soumettre"
	_btn_submit.custom_minimum_size = Vector2(120, 36)
	_btn_submit.pressed.connect(_on_submit_pressed)
	btn_box.add_child(_btn_submit)


func show_defeat(session: Dictionary) -> void:
	current_session = session
	time_left = float(session.get("time_left", 30.0))
	struggle_val = float(session.get("struggle_progress", 0.0))
	var captor: String = str(session.get("captor_id", "Ennemi"))
	var camp: String = str(session.get("camp_name", "Camp ennemi"))
	var r_cost: int = int(session.get("ransom_cost", 100))

	_narrative_lbl.text = "%s vous a neutralisé au sol. Sans résistance immédiate, vous serez conduit de force au %s." % [captor, camp]
	_btn_ransom.text = "Payer Rançon (%d Cr)" % r_cost
	_btn_ransom.disabled = (r_cost <= 0)

	_update_struggle_ui()
	visible = true


func _update_struggle_ui() -> void:
	_struggle_bar.value = struggle_val
	_struggle_lbl.text = "Lutte d'évasion : %d%%" % int(struggle_val)
	_timer_lbl.text = "Temps restant : %d s" % int(time_left)


func update_progress(new_progress: float, new_time_left: float) -> void:
	struggle_val = new_progress
	time_left = new_time_left
	_update_struggle_ui()


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE:
			_on_struggle_pressed()


func _on_struggle_pressed() -> void:
	struggle_requested.emit(15.0)


func _on_submit_pressed() -> void:
	submit_requested.emit()


func _on_ransom_pressed() -> void:
	ransom_requested.emit()


func hide_defeat() -> void:
	visible = false
	closed.emit()
