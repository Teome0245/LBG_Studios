extends Control
## Système d'Inventaire & Équipement Papier-Doll SWG Pre-CU (Holo-Teal)
## 1. Papier-Doll central (Silhouette humanoïde avec 6 slots d'équipement : Tête, Torse, Jambes, Pieds, Main D., Accessoire).
## 2. Grille de sac à dos (40 emplacements d'inventaire avec icônes, quantités, types d'objets et infobulles).
## 3. Équipement direct en un clic / double-clic avec statistiques répercutées.

signal item_equipped(slot_name: String, item_data: Dictionary)
signal item_used(item_id: String)

var _panel: Panel = null
var _paperdoll_container: Control = null
var _grid_container: GridContainer = null
var _info_label: Label = null

var equipped_items: Dictionary = {
	"head": {"name": "Casque de Reconnaissance", "icon": "🪖", "armor": 25},
	"chest": {"name": "Gilet en Cuir de Bantha", "icon": "🥋", "armor": 45},
	"legs": {"name": "Pantalon Renforcé en Krayt", "icon": "👖", "armor": 30},
	"feet": {"name": "Bottes de Marcheur des Dunes", "icon": "🥾", "armor": 15},
	"main_hand": {"name": "Pistolet Blaster DH-17", "icon": "🔫", "damage": 85},
	"accessory": {"name": "Jumelles Électro-Optiques", "icon": "🔭", "bonus": "+10 Visée"}
}

var inventory_items: Array = [
	{"id": "dh17", "name": "Pistolet Blaster DH-17", "icon": "🔫", "slot": "main_hand", "qty": 1, "desc": "Arme de poing militaire standard (Dégâts 85 S)"},
	{"id": "medpack_a", "name": "Stimpack Médical A", "icon": "💉", "slot": "usable", "qty": 5, "desc": "Restaure 250 Santé et 250 Action instantanément"},
	{"id": "ration_lh", "name": "Ration Énergétique des Dunes", "icon": "🍖", "slot": "usable", "qty": 8, "desc": "Nourriture de survie condensée"},
	{"id": "ore_iron", "name": "Minerai Ferrique Pur (94%)", "icon": "⛏️", "slot": "crafting", "qty": 120, "desc": "Ressource minérale pour forge et artisanat"},
	{"id": "hide_bantha", "name": "Cuir Épais de Dewback", "icon": "🥋", "slot": "crafting", "qty": 45, "desc": "Matériau pour armures et sellerie"},
	{"id": "capacitor_used", "name": "Condensateur Recyclé", "icon": "🔋", "slot": "crafting", "qty": 3, "desc": "Composant électronique pour réparation de speeder"}
]


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(720, 440)
	size = Vector2(720, 440)
	position = Vector2(280, 160)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(720, 440)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.12, 0.16, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.86, 0.96, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ INVENTAIRE & ÉQUIPEMENT PAPIER-DOLL SWG PRE-CU ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 13)
	title.add_theme_color_override("font_color", Color(0.3, 0.9, 1.0))
	_panel.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(680, 8)
	close_btn.size = Vector2(30, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	# ==========================================================================
	# SECTION GAUCHE : PAPIER-DOLL ÉQUIPEMENT
	# ==========================================================================
	var pd_label := Label.new()
	pd_label.text = "ÉQUIPEMENT ACTIF"
	pd_label.position = Vector2(16, 42)
	pd_label.add_theme_font_size_override("font_size", 11)
	pd_label.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(pd_label)

	_paperdoll_container = Control.new()
	_paperdoll_container.position = Vector2(16, 68)
	_paperdoll_container.size = Vector2(260, 320)
	_panel.add_child(_paperdoll_container)

	_render_paperdoll_slots()

	# Ligne séparatrice verticale
	var sep_v := ColorRect.new()
	sep_v.color = Color(0.2, 0.75, 0.85, 0.4)
	sep_v.position = Vector2(290, 48)
	sep_v.size = Vector2(1, 370)
	_panel.add_child(sep_v)

	# ==========================================================================
	# SECTION DROITE : SAC À DOS GRILLE 40 SLOTS
	# ==========================================================================
	var inv_label := Label.new()
	inv_label.text = "SAC À DOS (CONTENANCE : 40 SLOTS)"
	inv_label.position = Vector2(305, 42)
	inv_label.add_theme_font_size_override("font_size", 11)
	inv_label.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(inv_label)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(305, 68)
	scroll.size = Vector2(400, 280)
	_panel.add_child(scroll)

	_grid_container = GridContainer.new()
	_grid_container.columns = 5
	_grid_container.custom_minimum_size = Vector2(380, 260)
	scroll.add_child(_grid_container)

	_render_inventory_grid()

	# Zone d'infobulle inférieure
	_info_label = Label.new()
	_info_label.text = "Survolez ou cliquez sur un objet pour l'équiper ou le consommer."
	_info_label.position = Vector2(305, 360)
	_info_label.size = Vector2(400, 60)
	_info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_info_label.add_theme_font_size_override("font_size", 11)
	_info_label.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.85))
	_panel.add_child(_info_label)


func _render_paperdoll_slots() -> void:
	for c in _paperdoll_container.get_children():
		c.queue_free()

	var slot_positions := {
		"head": Vector2(100, 10),
		"chest": Vector2(100, 65),
		"legs": Vector2(100, 120),
		"feet": Vector2(100, 175),
		"main_hand": Vector2(20, 65),
		"accessory": Vector2(180, 65)
	}

	for s_name in slot_positions.keys():
		var pos: Vector2 = slot_positions[s_name]
		var item: Dictionary = equipped_items.get(s_name, {})

		var btn := Button.new()
		btn.position = pos
		btn.size = Vector2(60, 48)
		btn.text = "%s\n%s" % [item.get("icon", "⬜"), s_name.substr(0, 4).to_upper()]
		btn.add_theme_font_size_override("font_size", 9)

		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.04, 0.18, 0.24, 0.9)
		sb.set_border_width_all(1)
		sb.border_color = Color(0.2, 0.85, 0.95, 0.8)
		sb.set_corner_radius_all(4)
		btn.add_theme_stylebox_override("normal", sb)

		var captured_item := item
		btn.mouse_entered.connect(func() -> void:
			if not captured_item.is_empty():
				_info_label.text = "ÉQUIPÉ : %s (%s)" % [captured_item.get("name", ""), str(captured_item)]
		)
		_paperdoll_container.add_child(btn)


func _render_inventory_grid() -> void:
	for c in _grid_container.get_children():
		c.queue_free()

	for i in range(40):
		var btn := Button.new()
		btn.custom_minimum_size = Vector2(72, 60)
		btn.add_theme_font_size_override("font_size", 9)

		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.03, 0.14, 0.18, 0.85)
		sb.set_border_width_all(1)
		sb.border_color = Color(0.2, 0.7, 0.8, 0.5)
		sb.set_corner_radius_all(4)
		btn.add_theme_stylebox_override("normal", sb)

		if i < inventory_items.size():
			var it: Dictionary = inventory_items[i]
			btn.text = "%s x%d\n%s" % [it.get("icon", "📦"), it.get("qty", 1), it.get("name", "").substr(0, 8)]
			var captured_it := it
			btn.mouse_entered.connect(func() -> void:
				_info_label.text = "◈ %s [x%d] ◈\n%s" % [captured_it.get("name", ""), captured_it.get("qty", 1), captured_it.get("desc", "")]
			)
			btn.pressed.connect(func() -> void:
				_use_or_equip_item(captured_it)
			)
		else:
			btn.text = "—"
			btn.modulate = Color(1, 1, 1, 0.2)

		_grid_container.add_child(btn)


func _use_or_equip_item(it: Dictionary) -> void:
	var slot: String = str(it.get("slot", ""))
	if slot in equipped_items:
		equipped_items[slot] = it.duplicate(true)
		_render_paperdoll_slots()
		_info_label.text = "✓ %s équipé dans le slot [%s] !" % [it.get("name", ""), slot.to_upper()]
		item_equipped.emit(slot, it)
	elif slot == "usable":
		it["qty"] = it.get("qty", 1) - 1
		if it["qty"] <= 0:
			inventory_items.erase(it)
		_render_inventory_grid()
		_info_label.text = "✓ Objet %s consommé !" % it.get("name", "")
		item_used.emit(str(it.get("id", "")))
	else:
		_info_label.text = "%s est une ressource d'artisanat. Utilisez la touche [T] pour fabriquer des objets." % it.get("name", "")


func toggle() -> void:
	visible = not visible


func open_panel() -> void:
	visible = true


func close_panel() -> void:
	visible = false


## Ajoute un objet dans l'inventaire avec empilement automatique (Stacking SWG)
func add_item(item_data: Dictionary) -> bool:
	var item_id: String = str(item_data.get("id", ""))
	var add_qty: int = int(item_data.get("qty", 1))

	# 1. Empilement sur un objet existant si stackable
	for it in inventory_items:
		if str(it.get("id", "")) == item_id and str(it.get("slot", "")) != "main_hand" and str(it.get("slot", "")) != "chest" and str(it.get("slot", "")) != "legs":
			it["qty"] = int(it.get("qty", 1)) + add_qty
			_render_inventory_grid()
			_info_label.text = "✓ Reçu : +%d %s (Total : %d)" % [add_qty, it.get("name", ""), it["qty"]]
			return true

	# 2. Nouvel emplacement dans la limite des 40 slots
	if inventory_items.size() < 40:
		var new_it: Dictionary = item_data.duplicate(true)
		if not new_it.has("qty"):
			new_it["qty"] = add_qty
		inventory_items.append(new_it)
		_render_inventory_grid()
		_info_label.text = "✓ Nouvel objet ajouté : %s (x%d)" % [new_it.get("name", ""), new_it["qty"]]
		return true

	_info_label.text = "⚠ Sac à dos plein ! Impossible de stocker %s." % item_data.get("name", "")
	return false


## Vérifie si un objet est présent dans l'inventaire
func has_item(item_id: String) -> bool:
	for it in inventory_items:
		if str(it.get("id", "")) == item_id:
			return true
	return false


## Retourne la quantité totale possédée d'un objet
func get_item_count(item_id: String) -> int:
	for it in inventory_items:
		if str(it.get("id", "")) == item_id:
			return int(it.get("qty", 0))
	return 0


## Retire une quantité d'un objet
func remove_item(item_id: String, qty: int = 1) -> bool:
	for it in inventory_items:
		if str(it.get("id", "")) == item_id:
			var current: int = int(it.get("qty", 1))
			if current <= qty:
				inventory_items.erase(it)
			else:
				it["qty"] = current - qty
			_render_inventory_grid()
			return true
	return false

