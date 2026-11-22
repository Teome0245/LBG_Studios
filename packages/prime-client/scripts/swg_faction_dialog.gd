class_name SwgFactionDialog
extends Control
## Interface de Dialogue & Bureau de Liaison des Factions du Multivers (Prime / Lost Heaven)
## Repose sur les règles d'engagement SWG Pre-CU (Special Forces / On-Leave / Civilian)
## adaptées à la trinité des factions de Prime (Synthetika, Arcanes, Coalition).

signal faction_action_executed(action_id: String, payload: Dictionary)

const FactionScript = preload("res://scripts/swg_faction_system.gd")

var _panel: Panel = null
var _info_label: RichTextLabel = null
var _status_label: Label = null
var _faction_system_ref: Node = null


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(620, 460)
	size = Vector2(620, 460)
	position = Vector2(330, 160)
	_build_ui()


func set_faction_system(fs: Node) -> void:
	_faction_system_ref = fs
	if fs:
		fs.connect("faction_status_changed", func(_f, _s): update_display())
		fs.connect("faction_points_changed", func(_f, _p): update_display())


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(620, 460)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.08, 0.12, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.0, 0.85, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ BUREAU DE LIAISON DU MULTIVERS — LOST HEAVEN ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(1.0, 0.75, 0.3))
	_panel.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(580, 8)
	close_btn.size = Vector2(28, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	_status_label = Label.new()
	_status_label.position = Vector2(16, 38)
	_status_label.size = Vector2(588, 22)
	_status_label.add_theme_font_size_override("font_size", 11)
	_panel.add_child(_status_label)

	_info_label = RichTextLabel.new()
	_info_label.position = Vector2(16, 68)
	_info_label.size = Vector2(588, 220)
	_info_label.bbcode_enabled = true
	_panel.add_child(_info_label)

	# Boutons d'actions et enrôlement
	var vbox_btn := VBoxContainer.new()
	vbox_btn.position = Vector2(16, 295)
	vbox_btn.size = Vector2(588, 150)
	_panel.add_child(vbox_btn)

	# Ligne 1 : Les 3 Factions du Multivers
	var h1 := HBoxContainer.new()
	vbox_btn.add_child(h1)

	var btn_enlist_synth := _create_action_btn("⚡ Convergence Synthetika (Tech)", Color(0.0, 0.9, 1.0))
	btn_enlist_synth.pressed.connect(func(): _on_enlist_pressed(1))
	h1.add_child(btn_enlist_synth)

	var btn_enlist_arc := _create_action_btn("✧ Cercle des Arcanes (Alchimie)", Color(1.0, 0.8, 0.2))
	btn_enlist_arc.pressed.connect(func(): _on_enlist_pressed(2))
	h1.add_child(btn_enlist_arc)

	var btn_enlist_coal := _create_action_btn("⚓ Coalition des Mondes (Corsaires)", Color(0.95, 0.45, 0.2))
	btn_enlist_coal.pressed.connect(func(): _on_enlist_pressed(3))
	h1.add_child(btn_enlist_coal)

	# Ligne 2 : Règles d'engagement PvP
	var h2 := HBoxContainer.new()
	vbox_btn.add_child(h2)

	var btn_sf := _create_action_btn("⚔ Déclarer SPECIAL FORCES (PvP Mondial)", Color(1.0, 0.25, 0.25))
	btn_sf.pressed.connect(_on_declare_sf)
	h2.add_child(btn_sf)

	var btn_leave := _create_action_btn("🛡 Prendre Permission (On-Leave / Sûr)", Color(0.3, 0.8, 0.5))
	btn_leave.pressed.connect(_on_go_leave)
	h2.add_child(btn_leave)

	# Ligne 3 : Démobilisation & Ravitaillement
	var h3 := HBoxContainer.new()
	vbox_btn.add_child(h3)

	var btn_resign := _create_action_btn("Démobilisation : Retour Statut Neutre", Color(0.65, 0.65, 0.65))
	btn_resign.pressed.connect(_on_resign)
	h3.add_child(btn_resign)

	var btn_supplies := _create_action_btn("📦 Ravitaillement (Stimpacks, Filtres & Cuivre)", Color(0.85, 0.75, 0.2))
	btn_supplies.pressed.connect(_on_buy_supplies)
	h3.add_child(btn_supplies)

	update_display()


func _create_action_btn(text: String, col: Color) -> Button:
	var btn := Button.new()
	btn.text = text
	btn.custom_minimum_size = Vector2(185, 32)
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.14, 0.20, 0.9)
	sb.set_border_width_all(1)
	sb.border_color = col
	sb.set_corner_radius_all(4)
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_color_override("font_color", col)
	return btn


func open_panel() -> void:
	visible = true
	update_display()


func close_panel() -> void:
	visible = false


func toggle() -> void:
	if visible: close_panel()
	else: open_panel()


func update_display() -> void:
	if _faction_system_ref == null or not is_instance_valid(_status_label):
		return

	var f_name: String = str(_faction_system_ref.call("get_faction_name"))
	var prime_name: String = str(_faction_system_ref.call("get_faction_prime_name"))
	var s_name: String = str(_faction_system_ref.call("get_status_name"))
	var is_sf: bool = bool(_faction_system_ref.call("is_special_forces"))
	var prime_rank: String = str(_faction_system_ref.get("prime_rank"))

	var col_tag := "[color=#ff4444]" if is_sf else ("[color=#44ff88]" if f_name != "Neutre" else "[color=#88ccff]")
	_status_label.text = "Allégeance : %s  |  Rang : %s  |  Statut : %s" % [prime_name, prime_rank, s_name]
	if is_sf:
		_status_label.add_theme_color_override("font_color", Color(1.0, 0.3, 0.2))
	else:
		_status_label.add_theme_color_override("font_color", Color(0.4, 0.9, 1.0))

	var info := """%s[b]REGISTRE DU MULTIVERS — GUERRE D'INFLUENCE DE SCRAPALTAI[/b][/color]

• [color=#00e5ff]Convergence Synthetika[/color] (Gunnm / Cyberpunk / Mechari) : %d FP
  Devise : [i]« Le silicium sublime la chair. »[/i] — Grade : [b]%s[/b]

• [color=#ffd700]Cercle des Arcanes Primordiaux[/color] (Avatar / FMA / DBZ) : %d FP
  Devise : [i]« De la terre au cosmos, l'énergie transmute. »[/i] — Grade : [b]%s[/b]

• [color=#ff7043]Coalition des Mondes Brisés[/color] (Firefly / Albator / Discworld) : %d FP
  Devise : [i]« Rouille, liberté et cap sur l'inconnu. »[/i]

[color=#aaaaaa]Règles d'Engagement (Héritées de SWG Pre-CU) :[/color]
- [b]Civilian[/b] : Neutre, libre circulation dans le hub de Lost Heaven sans combat.
- [b]On-Leave[/b] : Enrôlé mais armes rengainées, immunisé aux attaques des joueurs rivaux.
- [b]Special Forces[/b] : [color=#ff5555]PvP ACTIF[/color] ! Attaquable à vue par les agents des autres factions.""" % [
		col_tag,
		_faction_system_ref.get("synthetika_points"),
		_faction_system_ref.get("imperial_rank"),
		_faction_system_ref.get("arcanes_points"),
		_faction_system_ref.get("rebel_rank"),
		_faction_system_ref.get("coalition_points")
	]

	_info_label.text = info


func _on_enlist_pressed(f_type: int) -> void:
	if _faction_system_ref:
		_faction_system_ref.call("enlist", f_type)
	faction_action_executed.emit("enlist", {"faction": f_type})


func _on_declare_sf() -> void:
	if _faction_system_ref:
		_faction_system_ref.declare_special_forces()
	faction_action_executed.emit("declare_sf", {})


func _on_go_leave() -> void:
	if _faction_system_ref:
		_faction_system_ref.go_on_leave()
	faction_action_executed.emit("go_leave", {})


func _on_resign() -> void:
	if _faction_system_ref:
		_faction_system_ref.resign_to_civilian()
	faction_action_executed.emit("resign", {})


func _on_buy_supplies() -> void:
	faction_action_executed.emit("buy_supplies", {})
