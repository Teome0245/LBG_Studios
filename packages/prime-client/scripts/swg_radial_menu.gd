extends Control
## Interface SWG Pre-CU (2D Top-Down) — Vrai Menu Radial Circulaire Holo-Teal :
## Anneau réticulé central autour du point cliqué + branches radiales numérotées (1..5)
## disposées en couronne autour de la cible, calqué sur le Radial Menu de Star Wars Galaxies.

signal radial_action_selected(action_id: String, context: Dictionary)

const RING_RADIUS := 30.0
const SPOKE_RADIUS := 98.0

var _current_options: Array = []
var _current_context: Dictionary = {}
var _btn_nodes: Array = []
var _center_pos: Vector2 = Vector2(180, 140)


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(360, 280)
	size = Vector2(360, 280)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ensure_ui() -> void:
	pass


func _get_spoke_angles(count: int) -> Array[float]:
	var angles: Array[float] = []
	if count <= 6:
		var base: Array[float] = [-90.0, 0.0, 90.0, 180.0, -45.0, 45.0]
		for i in range(count):
			angles.append(base[i])
	else:
		var step := 360.0 / float(count)
		for i in range(count):
			angles.append(-90.0 + float(i) * step)
	return angles


func build_options_for_context(ctx: Dictionary) -> Array:
	var kind := str(ctx.get("kind", "ground")).to_lower()
	var t_name := str(ctx.get("name", "")).to_lower()
	var is_dead := bool(ctx.get("is_dead", false)) or bool(ctx.get("is_corpse", false)) or kind == "corpse"
	var opts: Array = []

	if is_dead or kind == "corpse":
		opts.append({"id": "examine", "label": "Examiner Cadavre"})
		opts.append({"id": "harvest_meat", "label": "🥩 Dépecer Viande"})
		opts.append({"id": "harvest_hide", "label": "🥋 Dépecer Cuir"})
		opts.append({"id": "harvest_bone", "label": "🦴 Dépecer Os"})
	elif kind == "pet":
		opts.append({"id": "examine", "label": "Examiner Compagnon"})
		opts.append({"id": "pet_follow", "label": "👣 Suivre Maître"})
		opts.append({"id": "pet_stay", "label": "🛑 Rester sur Place"})
		opts.append({"id": "pet_feed", "label": "🍖 Nourrir Bête"})
		opts.append({"id": "pet_store", "label": "📦 Ranger au Chenil"})
	elif kind == "vendor":
		opts.append({"id": "examine", "label": "Examiner Vendeur"})
		opts.append({"id": "vendor_browse", "label": "🛒 Ouvrir Boutique"})
		opts.append({"id": "vendor_manage", "label": "💼 Gérer Stock / Caisse"})
	elif kind == "structure" or kind == "housing" or kind == "building":
		opts.append({"id": "examine", "label": "Examiner Structure"})
		opts.append({"id": "house_enter", "label": "🚪 Entrer Bâtiment"})
		opts.append({"id": "house_manage", "label": "📜 Droits & ACL"})
		opts.append({"id": "house_maintenance", "label": "💰 Banque & Entretien"})
		opts.append({"id": "house_decorate", "label": "🎨 Décoration 3D"})
	elif kind == "npc" or kind == "player":
		opts.append({"id": "examine", "label": "Examiner"})
		if kind == "npc":
			opts.append({"id": "converse", "label": "Discuter"})
		if "lia" in t_name or "talen" in t_name or "bige" in t_name or "lyra" in t_name or "perle" in t_name or "artiste" in t_name:
			opts.append({"id": "watch_entertainer", "label": "Observer (Soigner Fatigue)"})
		if "odo" in t_name or "med" in t_name or kind == "player":
			opts.append({"id": "treat_wounds", "label": "Soigner Blessures (Méd.)"})
		if "kell" in t_name or "yara" in t_name or "odo" in t_name or "talen" in t_name or "tobin" in t_name or "unar" in t_name:
			opts.append({"id": "open_skills", "label": "Entraîner Compétences"})
		if kind == "player":
			opts.append({"id": "tactical_strike", "label": "⚔ Duel Tactique HAM"})
	elif kind == "beast":
		opts.append({"id": "examine", "label": "Examiner Créature"})
		opts.append({"id": "harvest_fauna", "label": "Prélever Ressources"})
		opts.append({"id": "tame_creature", "label": "🐾 Apprivoiser (Tame)"})
		opts.append({"id": "tactical_strike", "label": "⚔ Attaquer (HAM Strike)"})
	else:
		opts.append({"id": "teleport_here", "label": "⚡ Téléporter ici (Dev)"})
		opts.append({"id": "move_here", "label": "Marcher ici"})
		opts.append({"id": "survey_ping", "label": "Sonder Gisement"})
		opts.append({"id": "survey_sample", "label": "Extraire Échantillon"})
		opts.append({"id": "deploy_harvester", "label": "Poser Extracteur"})
		opts.append({"id": "deploy_camp", "label": "⛺ Dresser Camp Scout"})
		opts.append({"id": "posture_kneel", "label": "🧎 Posture: Accroupi"})
		opts.append({"id": "posture_prone", "label": "🛌 Posture: Couché"})
		opts.append({"id": "posture_stand", "label": "🚶 Posture: Debout"})
		opts.append({"id": "open_skills", "label": "Compétences [K]"})

	# Option Dev téléportation toujours accessible sur n'importe quelle cible
	if kind != "ground":
		opts.append({"id": "teleport_here", "label": "⚡ Téléporter ici (Dev)"})

	return opts


func _make_swg_pill_btn(idx: int, txt: String) -> Button:
	var btn := Button.new()
	btn.text = " %d   %s " % [idx + 1, txt.to_upper()]
	btn.custom_minimum_size = Vector2(150, 24)
	btn.add_theme_font_size_override("font_size", 10)
	btn.add_theme_color_override("font_color", Color(0.86, 0.98, 1.0, 1.0))

	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.16, 0.21, 0.94)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.24, 0.86, 0.96, 0.95)
	sb.set_corner_radius_all(10)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 3
	sb.content_margin_bottom = 3
	btn.add_theme_stylebox_override("normal", sb)

	var sb_h := sb.duplicate() as StyleBoxFlat
	sb_h.bg_color = Color(0.08, 0.38, 0.46, 0.98)
	sb_h.border_color = Color(0.98, 0.84, 0.32, 1.0)
	btn.add_theme_stylebox_override("hover", sb_h)
	return btn


func open_at(screen_pos: Vector2, context: Dictionary) -> void:
	_current_context = context.duplicate(true)
	_current_options = build_options_for_context(_current_context)

	for b in _btn_nodes:
		if is_instance_valid(b):
			b.queue_free()
	_btn_nodes.clear()

	var count := _current_options.size()
	var spoke_r := SPOKE_RADIUS if count <= 6 else (SPOKE_RADIUS + 32.0)
	var extent := spoke_r + 90.0
	custom_minimum_size = Vector2(extent * 2.0, extent * 2.0)
	size = custom_minimum_size
	_center_pos = Vector2(extent, extent)

	position = screen_pos - _center_pos
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP

	var angles_deg := _get_spoke_angles(count)
	for i in range(count):
		var opt: Dictionary = _current_options[i]
		var ang := deg_to_rad(angles_deg[i])
		var dir := Vector2(cos(ang), sin(ang))
		var anchor_pt := _center_pos + dir * spoke_r
		var btn := _make_swg_pill_btn(i, str(opt.get("label", opt.get("id", "Action"))))
		var bw := 156.0
		var bh := 24.0
		btn.position = anchor_pt - Vector2(bw * 0.5, bh * 0.5)
		var captured_i := i
		btn.pressed.connect(func() -> void: trigger_option(captured_i))
		add_child(btn)
		_btn_nodes.append(btn)

	queue_redraw()


func _draw() -> void:
	if not visible:
		return
	var c := _center_pos
	# Anneau réticulé central SWG (Holo-Teal)
	draw_circle(c, RING_RADIUS, Color(0.02, 0.14, 0.18, 0.72))
	draw_arc(c, RING_RADIUS, 0.0, TAU, 48, Color(0.24, 0.88, 0.98, 0.95), 2.0)
	draw_arc(c, RING_RADIUS - 5.0, 0.0, TAU, 36, Color(0.18, 0.64, 0.76, 0.65), 1.0)

	# Réticules cardinaux sur l'anneau
	for a_deg in [0.0, 90.0, 180.0, 270.0]:
		var a: float = deg_to_rad(float(a_deg))
		var d := Vector2(cos(a), sin(a))
		draw_line(c + d * (RING_RADIUS - 7.0), c + d * (RING_RADIUS + 4.0), Color(0.55, 0.96, 1.0, 0.9), 1.5)

	# Rayons vectoriels reliant l'anneau central à chaque option radiale
	var count := _current_options.size()
	var spoke_r := SPOKE_RADIUS if count <= 6 else (SPOKE_RADIUS + 32.0)
	var angles_deg := _get_spoke_angles(count)
	for i in range(count):
		var ang := deg_to_rad(angles_deg[i])
		var dir := Vector2(cos(ang), sin(ang))
		var p0 := c + dir * RING_RADIUS
		var p1 := c + dir * (spoke_r - 14.0)
		draw_line(p0, p1, Color(0.24, 0.86, 0.96, 0.85), 1.5)
		draw_circle(p0, 3.0, Color(0.95, 0.82, 0.35, 1.0))

	var font := ThemeDB.fallback_font
	if font:
		var t_name := str(_current_context.get("name", "TARGET")).to_upper()
		if t_name.length() > 18:
			t_name = t_name.substr(0, 16) + ".."
		draw_string(font, c + Vector2(-40, 4), t_name, HORIZONTAL_ALIGNMENT_CENTER, 80, 9, Color(0.95, 0.92, 0.65, 1.0))


func trigger_option(index: int) -> void:
	if index < 0 or index >= _current_options.size():
		return
	var opt: Dictionary = _current_options[index]
	var action_id := str(opt.get("id", ""))
	var ctx_copy := _current_context.duplicate(true)
	close_menu()
	radial_action_selected.emit(action_id, ctx_copy)


func close_menu() -> void:
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	queue_redraw()
