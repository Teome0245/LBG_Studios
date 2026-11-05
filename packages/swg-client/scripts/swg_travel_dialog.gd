class_name SwgTravelDialog
extends Control
## Interface de Terminal de Transport Galactique SWG Pre-CU (Holo-Teal)
## Permet d'acheter un ticket de navette et d'embarquer vers d'autres villes et planètes.

signal travel_ticket_purchased(dest_id: String, dest_name: String, cost_cr: int, world_pos: Vector3)

var _panel: Panel = null
var _dest_container: VBoxContainer = null
var _balance_lbl: Label = null

var destinations: Array = [
	{
		"id": "dest_mos_eisley",
		"name": "Mos Eisley (Tatooine)",
		"planet": "TATOOINE",
		"cost": 100,
		"pos": Vector3(140.0, 0.0, -160.0),
		"desc": "Cité portuaire légendaire. Bazar marchand, Cantina de Chalmun et marché des contrebandiers."
	},
	{
		"id": "dest_anchorhead",
		"name": "Anchorhead (Tatooine)",
		"planet": "TATOOINE",
		"cost": 75,
		"pos": Vector3(-130.0, 0.0, 110.0),
		"desc": "Communauté pionnière agricole à la lisière des canyons et des sables profonds."
	},
	{
		"id": "dest_ksar_nomade",
		"name": "Ksar & Campement Nomade (Dunes Ouest)",
		"planet": "TATOOINE",
		"cost": 50,
		"pos": Vector3(-95.0, 0.0, -45.0),
		"desc": "Avant-poste de chasseurs et dresseurs nomades près du puits des dunes."
	},
	{
		"id": "dest_mine_est",
		"name": "Extracteur Minier Lourd (Plaines Est)",
		"planet": "TATOOINE",
		"cost": 50,
		"pos": Vector3(90.0, 0.0, -55.0),
		"desc": "Site de forage industriel et de raffinage de silicium et de fer brut."
	},
	{
		"id": "dest_theed",
		"name": "Theed (Naboo - Transit Hyperspatial)",
		"planet": "NABOO",
		"cost": 250,
		"pos": Vector3(0.0, 0.0, -42.0),
		"desc": "Capitale royale de Naboo. Dômes de cuivre, fleuve Solleu et jardins d'agrément."
	}
]


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(620, 420)
	size = Vector2(620, 420)
	position = Vector2(330, 160)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(620, 420)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.10, 0.16, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.86, 0.96, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ TERMINAL DE TRANSPORT GALACTIQUE • SPATIOPORT DE LOST HEAVEN ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(0.3, 0.95, 1.0))
	_panel.add_child(title)

	var sub := Label.new()
	sub.text = "Sélectionnez votre destination planétaire. Une navette Lambda est en phase d'embarquement."
	sub.position = Vector2(16, 34)
	sub.add_theme_font_size_override("font_size", 11)
	sub.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.8))
	_panel.add_child(sub)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(580, 8)
	close_btn.size = Vector2(30, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(16, 62)
	scroll.size = Vector2(588, 310)
	_panel.add_child(scroll)

	_dest_container = VBoxContainer.new()
	_dest_container.custom_minimum_size = Vector2(570, 300)
	scroll.add_child(_dest_container)

	_balance_lbl = Label.new()
	_balance_lbl.text = "Crédits disponibles : Compte Galactique en règle"
	_balance_lbl.position = Vector2(16, 385)
	_balance_lbl.add_theme_font_size_override("font_size", 11)
	_balance_lbl.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(_balance_lbl)

	_populate_destinations()


func _populate_destinations() -> void:
	for d in destinations:
		var card := PanelContainer.new()
		var card_sb := StyleBoxFlat.new()
		card_sb.bg_color = Color(0.04, 0.16, 0.22, 0.85)
		card_sb.set_border_width_all(1)
		card_sb.border_color = Color(0.2, 0.75, 0.85, 0.6)
		card_sb.set_corner_radius_all(4)
		card_sb.content_margin_left = 10
		card_sb.content_margin_right = 10
		card_sb.content_margin_top = 8
		card_sb.content_margin_bottom = 8
		card.add_theme_stylebox_override("panel", card_sb)

		var vb := VBoxContainer.new()

		var hb_title := HBoxContainer.new()
		var planet_tag := Label.new()
		planet_tag.text = "[%s]" % d["planet"]
		planet_tag.add_theme_font_size_override("font_size", 10)
		planet_tag.add_theme_color_override("font_color", Color(0.95, 0.85, 0.2))
		hb_title.add_child(planet_tag)

		var name_lbl := Label.new()
		name_lbl.text = " " + d["name"]
		name_lbl.add_theme_font_size_override("font_size", 12)
		name_lbl.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
		hb_title.add_child(name_lbl)
		vb.add_child(hb_title)

		var desc_lbl := Label.new()
		desc_lbl.text = d["desc"]
		desc_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		desc_lbl.add_theme_font_size_override("font_size", 11)
		desc_lbl.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.85))
		vb.add_child(desc_lbl)

		var hb_act := HBoxContainer.new()
		var cost_lbl := Label.new()
		cost_lbl.text = "Tarif du vol : %d Crédits" % int(d["cost"])
		cost_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		cost_lbl.add_theme_font_size_override("font_size", 11)
		cost_lbl.add_theme_color_override("font_color", Color(0.2, 1.0, 0.4))
		hb_act.add_child(cost_lbl)

		var btn_book := Button.new()
		btn_book.text = "Embarquer dans la Navette ➔"
		btn_book.add_theme_font_size_override("font_size", 11)
		var dest_id: String = d["id"]
		var dest_name: String = d["name"]
		var dest_cost: int = int(d["cost"])
		var dest_pos: Vector3 = d["pos"]
		btn_book.pressed.connect(func() -> void:
			travel_ticket_purchased.emit(dest_id, dest_name, dest_cost, dest_pos)
			close_panel()
		)
		hb_act.add_child(btn_book)

		vb.add_child(hb_act)
		card.add_child(vb)
		_dest_container.add_child(card)


func open_panel() -> void:
	visible = true


func close_panel() -> void:
	visible = false

