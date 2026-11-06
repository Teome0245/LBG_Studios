class_name SwgChatBox
extends Control
## Boîte de Chat Spatial & Commandes Galactiques SWG Pre-CU
## 1. Onglets Spatial (Parler local) et Combat/Système (Logs, Dégâts, XP, Quêtes).
## 2. Ligne de saisie avec interprétation des commandes Slash (/dance, /kneel, /camp...).
## 3. Historique défilant avec couleurs thématiques SWG Holo-Teal.

signal command_executed(cmd: String, args: String)
signal chat_message_sent(channel: String, text: String)

var _panel: Panel = null
var _tab_spatial_btn: Button = null
var _tab_combat_btn: Button = null
var _log_display: RichTextLabel = null
var _input_line: LineEdit = null

var _current_tab: String = "spatial"
var _history_spatial: Array = []
var _history_combat: Array = []


func _ready() -> void:
	custom_minimum_size = Vector2(400, 190)
	size = Vector2(400, 190)
	position = Vector2(16, 480)
	_build_ui()
	_print_welcome()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(400, 190)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.01, 0.08, 0.12, 0.88)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.2, 0.75, 0.88, 0.7)
	sb.set_corner_radius_all(4)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	# 1. Barre d'onglets supérieurs
	var tab_bar := HBoxContainer.new()
	tab_bar.position = Vector2(6, 4)
	tab_bar.size = Vector2(388, 24)
	_panel.add_child(tab_bar)

	_tab_spatial_btn = Button.new()
	_tab_spatial_btn.text = "◈ Spatial"
	_tab_spatial_btn.custom_minimum_size = Vector2(85, 22)
	_tab_spatial_btn.add_theme_font_size_override("font_size", 10)
	_tab_spatial_btn.pressed.connect(func() -> void: _switch_tab("spatial"))
	tab_bar.add_child(_tab_spatial_btn)

	_tab_combat_btn = Button.new()
	_tab_combat_btn.text = "⚔ Combat/Système"
	_tab_combat_btn.custom_minimum_size = Vector2(120, 22)
	_tab_combat_btn.add_theme_font_size_override("font_size", 10)
	_tab_combat_btn.pressed.connect(func() -> void: _switch_tab("combat"))
	tab_bar.add_child(_tab_combat_btn)

	# 2. Zone d'affichage de texte riche défilante
	_log_display = RichTextLabel.new()
	_log_display.position = Vector2(8, 30)
	_log_display.size = Vector2(384, 126)
	_log_display.bbcode_enabled = true
	_log_display.scroll_following = true
	_log_display.add_theme_font_size_override("normal_font_size", 11)
	_panel.add_child(_log_display)

	# 3. Champ de saisie inférieur
	_input_line = LineEdit.new()
	_input_line.position = Vector2(6, 160)
	_input_line.size = Vector2(388, 24)
	_input_line.placeholder_text = "Taper un message ou /help (Entrée)..."
	_input_line.add_theme_font_size_override("font_size", 10)
	_input_line.text_submitted.connect(_on_text_submitted)
	_panel.add_child(_input_line)

	_update_tab_styles()


func _print_welcome() -> void:
	add_log("[color=#38e1ff]◈ Canaux Galactiques de Lost Heaven initialisés. Tapez [b]/help[/b] pour la liste des commandes.[/color]", "spatial")
	add_log("[color=#ffd859]⚔ Journal de Combat & Registre HAM en ligne.[/color]", "combat")


func _switch_tab(tab_name: String) -> void:
	_current_tab = tab_name
	_update_tab_styles()
	_refresh_display()


func _update_tab_styles() -> void:
	var sb_active := StyleBoxFlat.new()
	sb_active.bg_color = Color(0.08, 0.28, 0.36, 0.95)
	sb_active.set_border_width_all(1)
	sb_active.border_color = Color(0.3, 0.9, 1.0)
	sb_active.set_corner_radius_all(3)

	var sb_inactive := StyleBoxFlat.new()
	sb_inactive.bg_color = Color(0.02, 0.1, 0.14, 0.6)
	sb_inactive.set_border_width_all(1)
	sb_inactive.border_color = Color(0.15, 0.45, 0.55, 0.4)
	sb_inactive.set_corner_radius_all(3)

	if _tab_spatial_btn:
		_tab_spatial_btn.add_theme_stylebox_override("normal", sb_active if _current_tab == "spatial" else sb_inactive)
	if _tab_combat_btn:
		_tab_combat_btn.add_theme_stylebox_override("normal", sb_active if _current_tab == "combat" else sb_inactive)


func add_log(bb_text: String, channel: String = "spatial") -> void:
	if channel == "combat" or channel == "system":
		_history_combat.append(bb_text)
		if _history_combat.size() > 80:
			_history_combat.pop_front()
	else:
		_history_spatial.append(bb_text)
		if _history_spatial.size() > 80:
			_history_spatial.pop_front()

	if _current_tab == channel or (_current_tab == "combat" and channel == "system"):
		_append_to_display(bb_text)
	elif _current_tab == "spatial" and channel == "spatial":
		_append_to_display(bb_text)


func _append_to_display(bb_text: String) -> void:
	if _log_display:
		_log_display.append_text(bb_text + "\n")


func _refresh_display() -> void:
	if _log_display == null:
		return
	_log_display.clear()
	var list: Array = _history_combat if _current_tab == "combat" else _history_spatial
	for msg in list:
		_log_display.append_text(str(msg) + "\n")


func _on_text_submitted(input_text: String) -> void:
	var text := input_text.strip_edges()
	_input_line.text = ""
	_input_line.release_focus()

	if text.is_empty():
		return

	# Commandes Slash SWG
	if text.begins_with("/"):
		var parts := text.substr(1).split(" ", true, 1)
		var cmd := parts[0].to_lower()
		var args := parts[1] if parts.size() > 1 else ""
		_handle_slash_command(cmd, args)
	else:
		# Message spatial ordinaire
		var out := "[color=#9be5ff][Spatial] Vous :[/color] %s" % text
		add_log(out, "spatial")
		chat_message_sent.emit("spatial", text)


func _handle_slash_command(cmd: String, args: String) -> void:
	match cmd:
		"help", "aide":
			var help_msg := "[color=#ffdf5d]◈ COMMANDES SWG PRE-CU DISPONIBLES :[/color]\n"
			help_msg += "  [b]/dance[/b] : Déclenche la danse de cantina\n"
			help_msg += "  [b]/kneel[/b], [b]/prone[/b], [b]/stand[/b] : Changement de posture HAM\n"
			help_msg += "  [b]/camp[/b] : Déploie le Bivouac de Scout\n"
			help_msg += "  [b]/harvester[/b] : Déploie l'Extracteur Minier\n"
			help_msg += "  [b]/speeder[/b] : Sort / range le Landspeeder\n"
			help_msg += "  [b]/dewback[/b] : Monte le Dewback\n"
			help_msg += "  [b]/shout <msg>[/b] : Crier dans toute la zone\n"
			help_msg += "  [b]/clone[/b] : Téléporte au centre de clonage\n"
			help_msg += "  [b]/skin[/b] : Change l'apparence de tenue"
			add_log(help_msg, "spatial")

		"shout", "crier":
			if not args.is_empty():
				add_log("[color=#ff4d4d][CRI SPATIAL] Vous : %s ![/color]" % args.to_upper(), "spatial")
				chat_message_sent.emit("shout", args)
			else:
				add_log("[color=#ffaaaa]Usage : /shout <message>[/color]", "spatial")

		_:
			command_executed.emit(cmd, args)


func grab_chat_focus() -> void:
	if _input_line:
		_input_line.grab_focus()


func is_chat_focused() -> bool:
	return _input_line != null and _input_line.has_focus()

