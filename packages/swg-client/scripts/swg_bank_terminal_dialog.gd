extends Control
## Interface de Terminal Bancaire SWG Pre-CU (Holo-Teal)
## Permet de consulter son solde, déposer et retirer des crédits galactiques

signal balance_updated(new_balance: int)

var _panel: Panel = null
var _balance_lbl: Label = null
var _msg_lbl: Label = null
var current_balance: int = 2450


func _ready() -> void:
	visible = false
	custom_minimum_size = Vector2(460, 260)
	size = Vector2(460, 260)
	position = Vector2(410, 260)
	_build_ui()


func _build_ui() -> void:
	_panel = Panel.new()
	_panel.size = Vector2(460, 260)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.14, 0.18, 0.95)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.2, 0.9, 0.4, 0.95)
	sb.set_corner_radius_all(6)
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)

	var title := Label.new()
	title.text = "◈ BORNE BANCAIRE GALACTIQUE DE LOST HEAVEN ◈"
	title.position = Vector2(16, 12)
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(0.2, 1.0, 0.5))
	_panel.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.position = Vector2(420, 8)
	close_btn.size = Vector2(30, 24)
	close_btn.pressed.connect(close_panel)
	_panel.add_child(close_btn)

	_balance_lbl = Label.new()
	_balance_lbl.text = "Solde Actuel : %d Crédits Galactiques" % current_balance
	_balance_lbl.position = Vector2(16, 50)
	_balance_lbl.add_theme_font_size_override("font_size", 15)
	_balance_lbl.add_theme_color_override("font_color", Color(0.96, 0.86, 0.35))
	_panel.add_child(_balance_lbl)

	var hb := HBoxContainer.new()
	hb.position = Vector2(16, 100)
	hb.size = Vector2(428, 40)

	var btn_dep := Button.new()
	btn_dep.text = "Déposer 100 cr"
	btn_dep.custom_minimum_size = Vector2(130, 36)
	btn_dep.pressed.connect(func() -> void:
		current_balance += 100
		_update_display("Dépôt de 100 crédits effectué avec succès.")
	)
	hb.add_child(btn_dep)

	var btn_ret := Button.new()
	btn_ret.text = "Retirer 100 cr"
	btn_ret.custom_minimum_size = Vector2(130, 36)
	btn_ret.pressed.connect(func() -> void:
		if current_balance >= 100:
			current_balance -= 100
			_update_display("Retrait de 100 crédits effectué.")
		else:
			_update_display("Solde insuffisant pour ce retrait.")
	)
	hb.add_child(btn_ret)

	var btn_dep_all := Button.new()
	btn_dep_all.text = "Sécuriser Coffre"
	btn_dep_all.custom_minimum_size = Vector2(140, 36)
	btn_dep_all.pressed.connect(func() -> void:
		_update_display("Coffre personnel de Lost Heaven synchronisé (Sécurité maximale).")
	)
	hb.add_child(btn_dep_all)

	_panel.add_child(hb)

	_msg_lbl = Label.new()
	_msg_lbl.text = "Prêt pour les transactions sécurisées par la Guilde Bancaire."
	_msg_lbl.position = Vector2(16, 160)
	_msg_lbl.size = Vector2(428, 40)
	_msg_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_msg_lbl.add_theme_font_size_override("font_size", 11)
	_msg_lbl.add_theme_color_override("font_color", Color(0.8, 0.95, 1.0, 0.9))
	_panel.add_child(_msg_lbl)


func _update_display(msg: String) -> void:
	_balance_lbl.text = "Solde Actuel : %d Crédits Galactiques" % current_balance
	_msg_lbl.text = msg
	balance_updated.emit(current_balance)


func open_panel() -> void:
	visible = true
	_update_display("Connecté au réseau bancaire galactique de Lost Heaven.")


func close_panel() -> void:
	visible = false

