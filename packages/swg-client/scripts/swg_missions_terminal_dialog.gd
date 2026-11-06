extends Control
## Interface de Terminal de Missions SWG Pre-CU (Holo-Teal)
## Affiche les missions de destruction (Destroy) et de reconnaissance/livraison (Delivery)

signal mission_accepted(mission_id: String, reward_cr: int)

var _panel: Panel = null
var _mission_list: VBoxContainer = null


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(620, 380)
	size = Vector2(620, 380)
	position = Vector2(330, 200)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(620, 380)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.12, 0.18, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.25, 0.85, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ TERMINAL DE MISSIONS GALACTIQUE DE LOST HEAVEN ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 13)
	title.add_theme_color_override("font_color", Color(0.3, 0.9, 1.0))
	_panel.add_child(title)

	var desc := Label.new()
	desc.text = "Sélectionnez un contrat de prime de guilde ou de transport de fret dans les dunes."
	desc.position = Vector2(16, 36)
	desc.add_theme_font_size_override("font_size", 11)
	desc.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.8))
	_panel.add_child(desc)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(580, 8)
	close_btn.size = Vector2(30, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(16, 68)
	scroll.size = Vector2(588, 290)
	_panel.add_child(scroll)

	_mission_list = VBoxContainer.new()
	_mission_list.custom_minimum_size = Vector2(570, 280)
	scroll.add_child(_mission_list)

	_populate_missions()


func _populate_missions() -> void:
	var missions: Array = [
		{
			"id": "mis_lair_chacals",
			"type": "💥 LAIR DESTROY",
			"title": "Destruction de Nid : Tumulus des Chacals des Dunes",
			"target": "Dunes Ouest Lair (-130m, -65m)",
			"reward": "1 250 Crédits • 350 XP Chasseur",
			"desc": "Éradiquez le nid des prédateurs des sables. Attention aux vagues de gardiens furieux."
		},
		{
			"id": "mis_lair_scarabees",
			"type": "💥 LAIR DESTROY",
			"title": "Extermination : Nid de Scarabées Obsidiens",
			"target": "Canyon Est Lair (140m, 95m)",
			"reward": "1 600 Crédits • Chitine Pure de Nid",
			"desc": "Détruisez le nid souterrain de scarabées avant qu'ils ne submergent la station minière."
		},
		{
			"id": "mis_chacals_ouest",
			"type": "⚔ DESTRUCTION",
			"title": "Chasse aux Prédateurs : Meute de Chacals Dorés",
			"target": "Dunes Ouest (-92m, -38m)",
			"reward": "250 Crédits • 120 XP Combat Tactique",
			"desc": "Une meute de chacals dorés menace les caravanes à proximité du camp nomade."
		},
		{
			"id": "mis_recon_ksar",
			"type": "🧭 RECONNAISSANCE",
			"title": "Patrouille de Sécurité : Porte Ouest & Ksar",
			"target": "Porte Ouest (-65m, 0m)",
			"reward": "180 Crédits • 80 XP Prospection",
			"desc": "Rendez-vous au poste avancé de la Porte Ouest pour vérifier l'état des défenses."
		},
		{
			"id": "mis_livraison_eau",
			"type": "📦 TRANSPORT",
			"title": "Ravitaillement en Eau Pure vers le Campement Scout",
			"target": "Campement Nomade (-95m, -45m)",
			"reward": "150 Crédits • Baume de Terrain",
			"desc": "Livrez une bombonne d'eau condensée des vaporisateurs aux chasseurs nomades."
		},
		{
			"id": "mis_scarabee_obsidien",
			"type": "⚔ DESTRUCTION ÉLITE",
			"title": "Élimination : Scarabée Obsidien Géant",
			"target": "Canyon Nord-Est (88m, 78m)",
			"reward": "450 Crédits • Carapace d'armure",
			"desc": "Un scarabée obsidien géant bloque l'accès au gisement de l'extracteur minier."
		}
	]

	for m in missions:
		var card := PanelContainer.new()
		var card_sb := StyleBoxFlat.new()
		card_sb.bg_color = Color(0.04, 0.18, 0.24, 0.85)
		card_sb.set_border_width_all(1)
		card_sb.border_color = Color(0.2, 0.75, 0.85, 0.7)
		card_sb.set_corner_radius_all(4)
		card_sb.content_margin_left = 10
		card_sb.content_margin_right = 10
		card_sb.content_margin_top = 8
		card_sb.content_margin_bottom = 8
		card.add_theme_stylebox_override("panel", card_sb)

		var vb := VBoxContainer.new()

		var h_box := HBoxContainer.new()
		var type_lbl := Label.new()
		type_lbl.text = "[%s]" % m["type"]
		type_lbl.add_theme_font_size_override("font_size", 10)
		type_lbl.add_theme_color_override("font_color", Color(0.95, 0.85, 0.2))
		h_box.add_child(type_lbl)

		var m_title := Label.new()
		m_title.text = " " + m["title"]
		m_title.add_theme_font_size_override("font_size", 12)
		m_title.add_theme_color_override("font_color", Color(1.0, 1.0, 1.0))
		h_box.add_child(m_title)
		vb.add_child(h_box)

		var m_desc := Label.new()
		m_desc.text = m["desc"]
		m_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		m_desc.add_theme_font_size_override("font_size", 11)
		m_desc.add_theme_color_override("font_color", Color(0.85, 0.95, 1.0, 0.9))
		vb.add_child(m_desc)

		var bottom_box := HBoxContainer.new()
		var rew_lbl := Label.new()
		rew_lbl.text = "Récompense : " + m["reward"]
		rew_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rew_lbl.add_theme_font_size_override("font_size", 11)
		rew_lbl.add_theme_color_override("font_color", Color(0.2, 1.0, 0.4))
		bottom_box.add_child(rew_lbl)

		var btn_accept := Button.new()
		btn_accept.text = "Accepter Contrat"
		btn_accept.add_theme_font_size_override("font_size", 11)
		var captured_id: String = m["id"]
		btn_accept.pressed.connect(func() -> void:
			mission_accepted.emit(captured_id, 250)
			btn_accept.text = "✓ ACCEPTÉE"
			btn_accept.disabled = true
		)
		bottom_box.add_child(btn_accept)

		vb.add_child(bottom_box)
		card.add_child(vb)
		_mission_list.add_child(card)


func open_panel() -> void:
	visible = true


func close_panel() -> void:
	visible = false

