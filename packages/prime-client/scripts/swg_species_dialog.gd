class_name SwgSpeciesDialog
extends Control
## Interface de l'Image Designer & Sélection d'Espèces SWG Pre-CU (Lost Heaven)
## Permet de choisir l'espèce de son personnage, d'adapter son gabarit et ses bonus HAM.

signal species_selected(species_data: Dictionary)

const SpeciesSystemScript = preload("res://scripts/swg_species_system.gd")

var _panel: Panel = null
var _species_list: ItemList = null
var _info_label: RichTextLabel = null
var _current_selection: int = 0


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(560, 400)
	size = Vector2(560, 400)
	position = Vector2(360, 190)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(560, 400)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.10, 0.16, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.3, 0.85, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ SALON D'IMAGE DESIGNER : ESPÈCES & MORPHOLOGIE SWG ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(0.3, 0.9, 1.0))
	_panel.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(520, 8)
	close_btn.size = Vector2(28, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	var hbox := HBoxContainer.new()
	hbox.position = Vector2(16, 45)
	hbox.size = Vector2(528, 290)
	_panel.add_child(hbox)

	_species_list = ItemList.new()
	_species_list.custom_minimum_size = Vector2(220, 280)
	_species_list.item_selected.connect(_on_species_selected)
	hbox.add_child(_species_list)

	for i in range(SpeciesSystemScript.get_species_count()):
		var sp: Dictionary = SpeciesSystemScript.get_species(i)
		_species_list.add_item("%d. %s" % [i + 1, str(sp["name"])])

	_info_label = RichTextLabel.new()
	_info_label.custom_minimum_size = Vector2(295, 280)
	_info_label.bbcode_enabled = true
	hbox.add_child(_info_label)

	var apply_btn := Button.new()
	apply_btn.text = "◈ CONFIRMER LA MORPHOLOGIE & ADAPTER LE PERSONNAGE ◈"
	apply_btn.position = Vector2(16, 348)
	apply_btn.size = Vector2(528, 36)
	apply_btn.pressed.connect(_on_apply_pressed)
	var b_sb := StyleBoxFlat.new()
	b_sb.bg_color = Color(0.08, 0.28, 0.38, 0.95)
	b_sb.border_color = Color(0.4, 0.95, 1.0)
	b_sb.set_border_width_all(1)
	b_sb.set_corner_radius_all(4)
	apply_btn.add_theme_stylebox_override("normal", b_sb)
	apply_btn.add_theme_color_override("font_color", Color(0.9, 0.98, 1.0))
	_panel.add_child(apply_btn)

	_species_list.select(0)
	_update_details(0)


func open_panel() -> void:
	visible = true


func close_panel() -> void:
	visible = false


func toggle() -> void:
	if visible: close_panel()
	else: open_panel()


func _on_species_selected(idx: int) -> void:
	_current_selection = idx
	_update_details(idx)


func _update_details(idx: int) -> void:
	var sp: Dictionary = SpeciesSystemScript.get_species(idx)
	var ham: Dictionary = sp.get("ham_bonus", {})

	var text := """[color=#33ddff][b]%s[/b][/color]
[color=#ffff77]%s[/color]

[color=#aaaaaa]Description :[/color]
%s

[color=#aaaaaa]Modèle Avatar :[/color] [b]%s[/b]
[color=#aaaaaa]Gabarit corporel :[/color] %.2fx

[color=#ff5544]♥ Bonus Santé Max : +%d[/color]
[color=#44ff77]⚡ Bonus Action Max : +%d[/color]
[color=#33aaff]🧠 Bonus Mental Max : +%d[/color]
""" % [
		str(sp.get("name")),
		str(sp.get("title")),
		str(sp.get("description")),
		str(sp.get("vrm_model")),
		float(sp.get("scale_vec", Vector3.ONE).x),
		int(ham.get("health", 0)),
		int(ham.get("action", 0)),
		int(ham.get("mind", 0))
	]

	_info_label.text = text


func _on_apply_pressed() -> void:
	var sp: Dictionary = SpeciesSystemScript.get_species(_current_selection)
	species_selected.emit(sp)
	close_panel()

