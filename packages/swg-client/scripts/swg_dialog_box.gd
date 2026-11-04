extends Control
## Fenêtre de Dialogue Interactive SWG Pre-CU (Holo-Teal)
## Permet de converser avec les PNJ (Lia, Barman, Maire, Médecin, Gardes, Droïdes)
## avec choix de réponses, soins HAM, commandes et quêtes locales.

signal option_selected(action_id: String, npc_name: String)

var _panel: Panel = null
var _title_lbl: Label = null
var _speaker_lbl: Label = null
var _text_lbl: Label = null
var _options_container: VBoxContainer = null
var _close_btn: Button = null

var current_npc_name: String = ""
var current_npc_kind: String = ""


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(560, 320)
	size = Vector2(560, 320)
	_build_ui()


func _build_ui() -> void:
	# Centrage à l'écran
	position = Vector2(360, 240)

	_panel = Panel.new()
	_panel.size = Vector2(560, 320)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.12, 0.16, 0.94)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.25, 0.85, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	# Barre de titre
	_title_lbl = Label.new()
	_title_lbl.text = "◈ TRANSMISSION COMMUNICATEUR SWG ◈"
	_title_lbl.position = Vector2(16, 12)
	_title_lbl.add_theme_font_size_override("font_size", 12)
	_title_lbl.add_theme_color_override("font_color", Color(0.35, 0.9, 1.0))
	_panel.add_child(_title_lbl)

	# Nom de l'interlocuteur
	_speaker_lbl = Label.new()
	_speaker_lbl.text = "Interlocuteur"
	_speaker_lbl.position = Vector2(16, 36)
	_speaker_lbl.add_theme_font_size_override("font_size", 16)
	_speaker_lbl.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(_speaker_lbl)

	# Texte du dialogue
	_text_lbl = Label.new()
	_text_lbl.text = "Message..."
	_text_lbl.position = Vector2(16, 68)
	_text_lbl.size = Vector2(528, 90)
	_text_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text_lbl.add_theme_font_size_override("font_size", 13)
	_text_lbl.add_theme_color_override("font_color", Color(0.9, 0.95, 1.0))
	_panel.add_child(_text_lbl)

	# Ligne séparatrice
	var sep := ColorRect.new()
	sep.color = Color(0.2, 0.7, 0.85, 0.5)
	sep.position = Vector2(16, 168)
	sep.size = Vector2(528, 1)
	_panel.add_child(sep)

	# Conteneur des options de réponse
	_options_container = VBoxContainer.new()
	_options_container.position = Vector2(16, 178)
	_options_container.size = Vector2(528, 125)
	_panel.add_child(_options_container)

	# Bouton Fermer [X]
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
		return
	option_selected.emit(opt_id, current_npc_name)
	close_dialog()


func close_dialog() -> void:
	visible = false


func _get_dialog_preset(n_name: String, n_kind: String) -> Dictionary:
	var lower_name := n_name.to_lower()
	if "lia" in lower_name or "artiste" in lower_name:
		return {
			"text": "« Bienvenue à la Cantina La Perle, voyageur ! Prends une chaise et repose-toi. Nos chants et nos mélodies dissipent la fatigue des sables et apaisent l'esprit des explorateurs. »",
			"options": [
				{"id": "watch_dance", "label": "Regarder la danse (Dissiper 50 Fatigue & Régen HAM)"},
				{"id": "listen_music", "label": "Écouter l'orchestre Bith (Buff de Mental +200)"},
				{"id": "ask_rumors", "label": "Quelles sont les nouvelles des caravanes ?"},
				{"id": "close", "label": "Merci Lia, je dois y aller."}
			]
		}
	elif "jax" in lower_name or "barman" in lower_name:
		return {
			"text": "« Qu'est-ce que je vous sers ? On a de la bière de racine corellienne fraîche, du lait bleu de bantha et des rations énergétiques pour vos expéditions dans les dunes. »",
			"options": [
				{"id": "buy_drink", "label": "Commander un verre de Lait Bleu (Restaurer 300 Action)"},
				{"id": "buy_rations", "label": "Acheter un paquet de rations de survie (50 crédits)"},
				{"id": "open_bazaar", "label": "Consulter les offres de troc de la cantina"},
				{"id": "close", "label": "Rien pour l'instant, Jax."}
			]
		}
	elif "odo" in lower_name or "maire" in lower_name:
		return {
			"text": "« Salutations, citoyen ! En tant que maire de Lost Heaven, je veille à la prospérité de notre colonie. Vous pouvez enregistrer un terrain, voter pour les décrets municipaux ou consulter les taxes foncières. »",
			"options": [
				{"id": "open_housing", "label": "Gérer mes propriétés & structures [H]"},
				{"id": "open_skills", "label": "Consulter l'arbre des 33 Professions [K]"},
				{"id": "city_status", "label": "Rapport sur l'état de la ville (Cité de Rang 3)"},
				{"id": "close", "label": "Bonne journée, Monsieur le Maire."}
			]
		}
	elif "vane" in lower_name or "médecin" in lower_name or "doctor" in lower_name:
		return {
			"text": "« Vous êtes au Centre Médical de Lost Heaven. Je traite les traumatismes HAM, les poisons de scorpions titan et nous disposons de deux cuves de Bacta prêtes à l'emploi. »",
			"options": [
				{"id": "heal_ham", "label": "Soigner toutes les blessures HAM (Santé, Action, Mental)"},
				{"id": "bacta_bath", "label": "Entrer dans une cuve de Bacta (Régénération totale)"},
				{"id": "buy_medkit", "label": "Acheter des stimulants de terrain (75 crédits)"},
				{"id": "close", "label": "Je suis en pleine forme, Docteur."}
			]
		}
	elif "garde" in lower_name or "milice" in lower_name:
		return {
			"text": "« Halte citoyen ! Zone sous surveillance de la Milice de Lost Heaven. Si vous sortez des remparts, gare aux meutes de chacals dorés et aux pillards des sables. Gardez votre arme à portée. »",
			"options": [
				{"id": "bounty_info", "label": "Y a-t-il des primes sur les bêtes des dunes ?"},
				{"id": "open_missions", "label": "Consulter les avis de recherche [Terminaux]"},
				{"id": "close", "label": "Compris, je reste vigilant."}
			]
		}
	elif "droïde" in lower_name or "r2" in lower_name:
		return {
			"text": "« Bip-bip-sifflement ! Le droïde astromécano R2-T8 fait tourner son dôme, projette un faisceau bleu d'analyse de terrain et affiche des coordonnées hyperspatiales fiables. »",
			"options": [
				{"id": "droid_scan", "label": "Demander une analyse géologique du secteur"},
				{"id": "droid_whistle", "label": "Lui tapoter le dôme amicalement"},
				{"id": "close", "label": "Reprends ta patrouille, R2."}
			]
		}
	else:
		return {
			"text": "« Salutations voyageur des sables ! Que la brise de Lost Heaven vous soit favorable. »",
			"options": [
				{"id": "examine", "label": "Examiner"},
				{"id": "close", "label": "Au revoir."}
			]
		}

