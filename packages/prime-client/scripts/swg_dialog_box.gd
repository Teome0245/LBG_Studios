# swg_dialog_box.gd — Fenêtre de dialogue et interactions SWG Pre-CU (Prime Client 2D)
# Gère les échanges textuels immersifs avec les PNJ, terminaux de ville, incubateurs, droïdes, spatioports et donjons.
extends Control
class_name SwgDialogBox

signal option_selected(option_id: String, npc_name: String)
signal dialog_closed()

var current_npc_name: String = ""
var current_npc_kind: String = ""

var _panel: Panel = null
var _speaker_lbl: Label = null
var _text_lbl: Label = null
var _options_container: VBoxContainer = null
var _close_btn: Button = null

func _init() -> void:
	name = "SwgDialogBox"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	_build_ui()

func _build_ui() -> void:
	_panel = Panel.new()
	_panel.name = "DialogPanel"
	_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_panel.position = Vector2(-280, -320)
	_panel.size = Vector2(560, 310)

	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.14, 0.20, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.18, 0.65, 0.85, 0.9)
	sb.set_corner_radius_all(8)
	sb.shadow_color = Color(0, 0, 0, 0.6)
	sb.shadow_size = 8
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	# Titre / Nom du locuteur
	_speaker_lbl = Label.new()
	_speaker_lbl.name = "SpeakerLabel"
	_speaker_lbl.position = Vector2(16, 12)
	_speaker_lbl.size = Vector2(500, 26)
	_speaker_lbl.add_theme_font_size_override("font_size", 16)
	_speaker_lbl.add_theme_color_override("font_color", Color(1.0, 0.88, 0.35))
	_panel.add_child(_speaker_lbl)

	# Texte narratif
	_text_lbl = Label.new()
	_text_lbl.name = "DialogText"
	_text_lbl.position = Vector2(16, 44)
	_text_lbl.size = Vector2(528, 120)
	_text_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text_lbl.add_theme_font_size_override("font_size", 13)
	_text_lbl.add_theme_color_override("font_color", Color(0.85, 0.92, 0.98))
	_panel.add_child(_text_lbl)

	# Séparateur
	var sep := ColorRect.new()
	sep.color = Color(0.2, 0.5, 0.7, 0.4)
	sep.position = Vector2(16, 168)
	sep.size = Vector2(528, 1)
	_panel.add_child(sep)

	# Options
	_options_container = VBoxContainer.new()
	_options_container.position = Vector2(16, 178)
	_options_container.size = Vector2(528, 125)
	_panel.add_child(_options_container)

	# Bouton Fermer
	_close_btn = Button.new()
	_close_btn.text = "✕"
	_close_btn.position = Vector2(520, 8)
	_close_btn.size = Vector2(30, 24)
	_close_btn.pressed.connect(close_dialog)
	_panel.add_child(_close_btn)

func open_dialog(npc_name: String, npc_kind: String, custom_text: String = "", custom_options: Array = []) -> void:
	current_npc_name = npc_name
	current_npc_kind = npc_kind
	_speaker_lbl.text = npc_name

	for c in _options_container.get_children():
		c.queue_free()

	var text_body: String = custom_text
	var opts: Array = custom_options

	if text_body.is_empty():
		var preset := _get_dialog_preset(npc_name, npc_kind)
		text_body = preset["text"]
		opts = preset["options"]

	_text_lbl.text = text_body

	for i in range(opts.size()):
		var opt_data: Dictionary = opts[i]
		var btn := Button.new()
		btn.text = " %d. %s" % [i + 1, opt_data.get("label", "Répondre")]
		btn.custom_minimum_size = Vector2(528, 26)
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.add_theme_font_size_override("font_size", 12)
		btn.add_theme_color_override("font_color", Color(0.95, 0.98, 1.0))

		var sb_opt := StyleBoxFlat.new()
		sb_opt.bg_color = Color(0.04, 0.22, 0.28, 0.9)
		sb_opt.set_border_width_all(1)
		sb_opt.border_color = Color(0.2, 0.8, 0.9, 0.8)
		sb_opt.set_corner_radius_all(4)
		btn.add_theme_stylebox_override("normal", sb_opt)

		var sb_h := sb_opt.duplicate() as StyleBoxFlat
		sb_h.bg_color = Color(0.1, 0.45, 0.55, 0.95)
		sb_h.border_color = Color(0.98, 0.85, 0.3)
		btn.add_theme_stylebox_override("hover", sb_h)

		var opt_id: String = opt_data.get("id", "close")
		btn.pressed.connect(func() -> void: _on_option_clicked(opt_id))
		_options_container.add_child(btn)

	visible = true

func _on_option_clicked(opt_id: String) -> void:
	if opt_id == "close":
		close_dialog()
	else:
		option_selected.emit(opt_id, current_npc_name)
		close_dialog()

func close_dialog() -> void:
	visible = false
	dialog_closed.emit()

func _get_dialog_preset(n_name: String, n_kind: String) -> Dictionary:
	var lower_name := n_name.to_lower()
	if "cityhall" in lower_name or "ville" in lower_name or "municipal" in lower_name or "city" in n_kind:
		return {
			"text": "« TERMINAL POLITIQUE & HÔTEL DE VILLE CIVIQUE. Enregistrez votre statut de citoyen, votez pour le prochain mandat de Maire et consultez la caisse municipale. »",
			"options": [
				{"id": "vote_mayor", "label": "🗳 Voter pour le Maire sortant aux élections civiques"},
				{"id": "register_citizen", "label": "📜 Devenir citoyen officiel de la ville"},
				{"id": "view_city_taxes", "label": "💰 Consulter les taux d'imposition (Foncier & Commerce)"},
				{"id": "city_specialization", "label": "⚙ Spécialisation active : Centre Industriel (-10% temps craft)"},
				{"id": "close", "label": "Quitter le terminal municipal."}
			]
		}
	elif "bio" in lower_name or "incubateur" in lower_name or "adn" in lower_name or "bio" in n_kind:
		return {
			"text": "« INCUBATEUR GÉNÉTIQUE & LABORATOIRE BIO-INGÉNIEUR. Analysez vos échantillons d'ADN de créatures prélevés sur le terrain et synthétisez des embryons mutants. »",
			"options": [
				{"id": "sample_dna_wild", "label": "🧪 Prélever un échantillon d'ADN sur la faune ciblée"},
				{"id": "fuse_embryo", "label": "🧬 Fusionner 2 matrices d'ADN pour concevoir un familier hybride"},
				{"id": "craft_stimulant", "label": "💉 Synthétiser une enzyme de régénération pour Médecin"},
				{"id": "close", "label": "Fermer la console de l'incubateur."}
			]
		}
	elif "droïde" in lower_name or "droid" in lower_name or "r2" in lower_name or "droid" in n_kind:
		return {
			"text": "« UNITÉ DROÏDE R2 (DROID ENGINEER). Le droïde émet un bip joyeux et déploie ses interfaces d'inventaire ambulant et d'atelier de confection. »",
			"options": [
				{"id": "droid_follow", "label": "🐕 /follow (Suivre mon personnage)"},
				{"id": "droid_stay", "label": "🛑 /stay (Garder la position)"},
				{"id": "droid_inventory", "label": "📦 Ouvrir la soute de stockage (+25 slots)"},
				{"id": "droid_craft", "label": "⚙ Utiliser l'atelier de confection mobile (+10% craft)"},
				{"id": "close", "label": "Fermer les commandes droïde."}
			]
		}
	elif "corvette" in lower_name or "donjon" in lower_name or "raid" in lower_name or "corvette" in n_kind:
		return {
			"text": "« SAS DE LA CORVETTE CORELLIENNE (DONJON RAID). Alerte rouge ! Le vaisseau diplomatique a été pris d'assaut. Vous disposez de 60 minutes pour sécuriser le pont et saboter l'hyperdrive. »",
			"options": [
				{"id": "enter_corvette", "label": "🚨 Franchir le sas pressurisé (Lancer l'instance 60 min)"},
				{"id": "sabotage_engines", "label": "💥 Saboter les générateurs de saut hyperspatial"},
				{"id": "rescue_hostages", "label": "🤝 Évacuer les otages diplomatiques"},
				{"id": "close", "label": "Repli vers la zone d'atterrissage."}
			]
		}
	elif "planete" in lower_name or "galaxie" in lower_name or "galactique" in lower_name or "starmap" in lower_name or "planet" in n_kind:
		return {
			"text": "« CONSOLE DE TRANSIT STELLAIRE & CARTOGRAPHIE GALACTIQUE. Choisissez votre destination planétaire parmi les 5 mondes majeurs de Star Wars Galaxies. »",
			"options": [
				{"id": "travel_tatooine", "label": "🏜 Tatooine (Désert aride, Mer de dunes & Canyons)"},
				{"id": "travel_naboo", "label": "🌿 Naboo (Plaines verdoyantes, Cascades & Cités d'art)"},
				{"id": "travel_endor", "label": "🌲 Endor (Lune forestière aux séquoias géants & Ewoks)"},
				{"id": "travel_dathomir", "label": "🩸 Dathomir (Ciel carmin, Rancors sauvages & Brumes toxiques)"},
				{"id": "travel_corellia", "label": "🏙 Corellia (Berceau naval de Coronet City & Fret galactique)"},
				{"id": "close", "label": "Conserver les coordonnées actuelles."}
			]
		}
	elif "bounty" in lower_name or "primes" in lower_name or "bounty" in n_kind:
		return {
			"text": "« GUILDE DES CHASSEURS DE PRIMES — Terminaux Sécurisés. Des fugitifs, des officiers en fuite et des individus sensibles à la Force sont recherchés vivants ou morts. »",
			"options": [
				{"id": "open_bounty_terminal", "label": "📜 Consulter les Contrats de Primes Actifs"},
				{"id": "deploy_probe_droid", "label": "📡 Déployer une Sonde Arakyd MK-IV pour traquer la cible"},
				{"id": "close", "label": "Quitter le terminal."}
			]
		}
	elif "assurance" in lower_name or "insurance" in lower_name or "insurance" in n_kind:
		return {
			"text": "« TERMINAL D'ASSURANCE & CLONAGE GALACTIQUE. Protégez votre équipement contre la dégradation définitive (Decay) et enregistrez votre matrice génétique. »",
			"options": [
				{"id": "insure_equipment", "label": "🛡 Assurer l'intégralité de mon équipement (200 crédits)"},
				{"id": "bind_clone", "label": "🧬 Lier ma matrice de résurrection à ce Centre de Clonage"},
				{"id": "close", "label": "Fermer le terminal."}
			]
		}
	elif "xwing" in lower_name or "starfighter" in lower_name or "vaisseau" in lower_name or "spatial" in lower_name:
		return {
			"text": "« CHASSEUR STELLAIRE INCOM T-65B X-WING — Prêt pour le vol orbital Jump to Lightspeed (JTL). Systèmes d'armes armés, boucliers déflecteurs en ligne. »",
			"options": [
				{"id": "launch_starfighter", "label": "🚀 Décoller vers l'espace orbital (Combat Dogfight JTL) [F9]"},
				{"id": "close", "label": "Rester au sol."}
			]
		}
	else:
		return {
			"text": "« Salutations voyageur de Lost Heaven ! Que les vents du désert vous soient cléments. »",
			"options": [
				{"id": "examine", "label": "Examiner"},
				{"id": "close", "label": "Au revoir."}
			]
		}

