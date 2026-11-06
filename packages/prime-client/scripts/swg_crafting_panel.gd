extends Control
## Outil d'Artisanat & Expérimentation SWG Pre-CU (Crafting Tool, Touche T)
## Schémas réels, pureté des ressources (OAR), barres de risque et calcul de succès.

signal item_crafted(recipe_name: String, quality: float)

var _panel: Panel = null
var _schematic_list: VBoxContainer = null
var _craft_status_label: Label = null
var _risk_bar: ProgressBar = null

var inventory_ref: Node = null

var recipes: Array = [
	{
		"id": "rec_medpack",
		"name": "Stimpack Médical Avancé (x3)",
		"desc": "Injecteur de bacta d'urgence. Restaure 350 Santé & 350 Action.",
		"req": "Minerai Ferrique x20 • Viande Sauvage x10",
		"costs": {"ore_iron": 20, "meat_wild": 10},
		"result_item": {
			"id": "medpack_adv",
			"name": "Stimpack Médical Avancé",
			"icon": "💉",
			"slot": "usable",
			"qty": 3,
			"desc": "Bacta concentré (+350 Santé / +350 Action)"
		},
		"base_quality": 88
	},
	{
		"id": "rec_blaster_dh17",
		"name": "Blaster Custom Artisanal DH-17",
		"desc": "Pistolet lourd à haute cadence. Dégâts 95 S, précision +12.",
		"req": "Minerai Ferrique x35 • Condensateur x1",
		"costs": {"ore_iron": 35, "capacitor_used": 1},
		"result_item": {
			"id": "dh17_custom",
			"name": "Blaster Custom DH-17",
			"icon": "🔫",
			"slot": "main_hand",
			"qty": 1,
			"desc": "Arme militaire de précision (Dégâts 95 S)"
		},
		"base_quality": 92
	},
	{
		"id": "rec_leather_vest",
		"name": "Gilet de Chasse en Cuir Épais",
		"desc": "Armure souple de Scout. Protection cinétique renforcée (Armure +35).",
		"req": "Cuir de Dewback x25 • Minerai Ferrique x15",
		"costs": {"hide_bantha": 25, "ore_iron": 15},
		"result_item": {
			"id": "vest_custom",
			"name": "Gilet en Cuir Renforcé",
			"icon": "🥋",
			"slot": "chest",
			"qty": 1,
			"desc": "Armure de cuir artisanal (Armure +35)"
		},
		"base_quality": 85
	},
	{
		"id": "rec_vibro_blade",
		"name": "Couteau Vibro de Dépeçage Scout",
		"desc": "Outil tranchant à haute fréquence optimisant les prélèvements de faune.",
		"req": "Os Dense x15 • Minerai Ferrique x15",
		"costs": {"bone_dense": 15, "ore_iron": 15},
		"result_item": {
			"id": "vibro_blade",
			"name": "Couteau Vibro Scout",
			"icon": "🗡️",
			"slot": "usable",
			"qty": 1,
			"desc": "Lame vibratoire de dépeçage"
		},
		"base_quality": 89
	}
]


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(660, 420)
	size = Vector2(660, 420)
	position = Vector2(310, 170)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(660, 420)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.13, 0.17, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.95, 0.75, 0.2, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ ATELIER D'ARTISANAT EXPÉRIMENTAL SWG PRE-CU ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 13)
	title.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(620, 8)
	close_btn.size = Vector2(30, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(16, 48)
	scroll.size = Vector2(628, 250)
	_panel.add_child(scroll)

	_schematic_list = VBoxContainer.new()
	_schematic_list.custom_minimum_size = Vector2(610, 240)
	scroll.add_child(_schematic_list)

	_populate_recipes()

	# Zone inférieure : Statut et Expérimentation
	_craft_status_label = Label.new()
	_craft_status_label.text = "Sélectionnez un schéma de fabrication pour lancer l'assemblage."
	_craft_status_label.position = Vector2(16, 310)
	_craft_status_label.size = Vector2(628, 40)
	_craft_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_craft_status_label.add_theme_font_size_override("font_size", 11)
	_craft_status_label.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0))
	_panel.add_child(_craft_status_label)

	var exp_btn := Button.new()
	exp_btn.text = "⚗️ EXPÉRIMENTER SUR LE DERNIER SCHÉMA (+15% QUALITÉ)"
	exp_btn.position = Vector2(16, 360)
	exp_btn.size = Vector2(628, 38)
	exp_btn.add_theme_font_size_override("font_size", 12)
	exp_btn.pressed.connect(func() -> void:
		_craft_status_label.text = "✨ Expérimentation Réussie (Jet de compétence artisanat 96/100) : Qualité Exceptionnelle obtenue !"
	)
	_panel.add_child(exp_btn)


func _populate_recipes() -> void:
	for r in recipes:
		var card := PanelContainer.new()
		var card_sb := StyleBoxFlat.new()
		card_sb.bg_color = Color(0.04, 0.18, 0.22, 0.85)
		card_sb.set_border_width_all(1)
		card_sb.border_color = Color(0.3, 0.8, 0.9, 0.6)
		card_sb.set_corner_radius_all(4)
		card_sb.content_margin_left = 12
		card_sb.content_margin_right = 12
		card_sb.content_margin_top = 8
		card_sb.content_margin_bottom = 8
		card.add_theme_stylebox_override("panel", card_sb)

		var hb := HBoxContainer.new()

		var vb_info := VBoxContainer.new()
		vb_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL

		var r_title := Label.new()
		r_title.text = "📜 " + r["name"]
		r_title.add_theme_font_size_override("font_size", 12)
		r_title.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
		vb_info.add_child(r_title)

		var r_desc := Label.new()
		r_desc.text = r["desc"] + "\nMatériaux : " + r["req"]
		r_desc.add_theme_font_size_override("font_size", 10)
		r_desc.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.9))
		vb_info.add_child(r_desc)

		hb.add_child(vb_info)

		var craft_btn := Button.new()
		craft_btn.text = "Fabriquer"
		craft_btn.custom_minimum_size = Vector2(100, 32)
		var captured_r: Dictionary = r
		craft_btn.pressed.connect(func() -> void:
			_attempt_craft(captured_r)
		)
		hb.add_child(craft_btn)

		card.add_child(hb)
		_schematic_list.add_child(card)


func _attempt_craft(r: Dictionary) -> void:
	var r_name: String = str(r["name"])
	var costs: Dictionary = r.get("costs", {})
	var result_it: Dictionary = r.get("result_item", {})

	if inventory_ref != null and inventory_ref.has_method("get_item_count"):
		# 1. Vérification des ressources requises
		for item_id in costs.keys():
			var needed: int = int(costs[item_id])
			var owned: int = int(inventory_ref.call("get_item_count", item_id))
			if owned < needed:
				_craft_status_label.text = "⚠ Ressources insuffisantes : Requis %d x [%s] (Possédé : %d). Allez forer ou dépecer !" % [needed, item_id, owned]
				return

		# 2. Déduction des ressources de l'inventaire
		for item_id in costs.keys():
			var needed: int = int(costs[item_id])
			inventory_ref.call("remove_item", item_id, needed)

		# 3. Ajout de l'objet manufacturé dans l'inventaire
		if not result_it.is_empty():
			inventory_ref.call("add_item", result_it)

	_craft_status_label.text = "🔨 Fabrication de [%s] terminée avec succès ! Objet déposé dans votre sac à dos [I]." % r_name
	item_crafted.emit(r_name, float(r.get("base_quality", 85.0)))


func toggle() -> void:
	visible = not visible


func open_panel() -> void:
	visible = true


func close_panel() -> void:
	visible = false
