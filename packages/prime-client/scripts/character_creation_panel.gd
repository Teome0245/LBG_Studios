extends Control
## CharacterCreationPanel — flow Hammat en 3 phases (Émergence → Cristallisation → Éveil)

signal creation_completed(result: Dictionary)
signal creation_cancelled
signal creation_completed_in_game(result: Dictionary)

const CONFIG_PATH := "res://config/character_creation.json"

enum Phase { EMERGENCE, CRYSTALLIZATION, AWAKENING }

@onready var _phase_emergence: Control = %PhaseEmergence
@onready var _phase_crystal: Control = %PhaseCrystallization
@onready var _phase_awakening: Control = %PhaseAwakening
@onready var _mode_list: ItemList = %ModeList
@onready var _choice_list: ItemList = %ChoiceList
@onready var _race_label: Label = %RaceLabel
@onready var _race_list: ItemList = %RaceList
@onready var _hint: Label = %HintLabel
@onready var _name_edit: LineEdit = %CharacterName
@onready var _color_preset: OptionButton = %ColorPreset
@onready var _summary: RichTextLabel = %SummaryLabel
@onready var _status: Label = %StatusLabel
@onready var _btn_back: Button = %BackButton
@onready var _btn_next: Button = %NextButton
@onready var _btn_cancel: Button = %CancelButton
@onready var _hammat_glow: ColorRect = %HammatGlow

var _cfg: Dictionary = {}
var _phase: Phase = Phase.EMERGENCE
var _mode: String = "archetype"
var _choice_id: String = ""
var _race_id: String = ""
var _client: Node = null
var _pending_result: Dictionary = {}
var _pulse: float = 0.0
var _in_game: bool = false


func _ready() -> void:
	_load_config()
	_wire_client()
	_populate_modes()
	_show_phase(Phase.EMERGENCE)
	_mode_list.item_selected.connect(_on_mode_selected)
	_choice_list.item_selected.connect(_on_choice_selected)
	_race_list.item_selected.connect(_on_race_selected)
	_color_preset.item_selected.connect(_on_color_changed)
	_btn_back.pressed.connect(_on_back_pressed)
	_btn_next.pressed.connect(_on_next_pressed)
	_btn_cancel.pressed.connect(_on_cancel_pressed)
	_name_edit.text_changed.connect(_on_name_changed)
	if _mode_list.item_count > 0:
		_mode_list.select(0)
		_on_mode_selected(0)


func _process(delta: float) -> void:
	if not visible:
		return
	_pulse += delta * 2.4
	if _hammat_glow:
		var alpha: float = 0.18 + abs(sin(_pulse)) * 0.22
		_hammat_glow.color = Color(0.2, 0.75, 0.95, alpha)


func open_panel(in_game: bool = false) -> void:
	_in_game = in_game
	_pending_result = {}
	_name_edit.text = ""
	_race_id = ""
	_populate_color_presets()
	_show_phase(Phase.EMERGENCE)
	_status.text = ""
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = true


func _load_config() -> void:
	_cfg = {}
	if FileAccess.file_exists(CONFIG_PATH):
		var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
		if raw is Dictionary:
			_cfg = raw


func _wire_client() -> void:
	_client = get_node_or_null("LbgCharacterClient")
	if _client == null:
		_client = preload("res://scripts/LbgCharacterClient.gd").new()
		_client.name = "LbgCharacterClient"
		add_child(_client)
	if not _client.create_ok.is_connected(_on_create_ok):
		_client.create_ok.connect(_on_create_ok)
	if not _client.create_failed.is_connected(_on_create_failed):
		_client.create_failed.connect(_on_create_failed)


func _populate_modes() -> void:
	_mode_list.clear()
	for m in _cfg.get("modes", []):
		if m is Dictionary:
			_mode_list.add_item(str(m.get("label", m.get("id", "?"))))


func _on_mode_selected(index: int) -> void:
	var modes: Array = _cfg.get("modes", [])
	if index < 0 or index >= modes.size():
		return
	var m: Dictionary = modes[index]
	_mode = str(m.get("id", "archetype"))
	_hint.text = str(m.get("hint", ""))
	_populate_choices()
	_refresh_emergence_next()


func _refresh_emergence_next() -> void:
	if _phase != Phase.EMERGENCE:
		return
	var ready := false
	match _mode:
		"chaos", "empreinte":
			ready = not _choice_id.is_empty()
		"archetype":
			ready = not _choice_id.is_empty() and not _race_id.is_empty()
		_:
			ready = not _choice_id.is_empty()
	_btn_next.disabled = not ready


func _populate_choices() -> void:
	_choice_list.clear()
	_choice_id = ""
	match _mode:
		"archetype":
			for a in _cfg.get("archetypes", []):
				if a is Dictionary:
					var label := "%s — %s" % [a.get("label", "?"), a.get("identity", "")]
					_choice_list.add_item(label)
					_choice_list.set_item_metadata(_choice_list.item_count - 1, str(a.get("id", "")))
		"empreinte":
			for e in _cfg.get("empreintes", []):
				if e is Dictionary:
					var label := "%s (%s)" % [e.get("label", "?"), e.get("race", "")]
					_choice_list.add_item(label)
					_choice_list.set_item_metadata(_choice_list.item_count - 1, str(e.get("pnj_id", "")))
		"chaos":
			_choice_list.add_item("Laisser l'Amas se cristalliser seul")
			_choice_list.set_item_metadata(0, "chaos")
	if _choice_list.item_count > 0:
		_choice_list.select(0)
		_on_choice_selected(0)


func _on_choice_selected(index: int) -> void:
	_choice_id = str(_choice_list.get_item_metadata(index))
	_populate_races()


func _archetype_cfg(arch_id: String) -> Dictionary:
	for a in _cfg.get("archetypes", []):
		if a is Dictionary and str(a.get("id", "")) == arch_id:
			return a
	return {}


func _race_label_for(race_id: String) -> String:
	for r in _cfg.get("races", []):
		if r is Dictionary and str(r.get("id", "")) == race_id:
			return str(r.get("label", race_id))
	return race_id


func _populate_races() -> void:
	_race_list.clear()
	_race_id = ""
	var show_races := _mode == "archetype" and not _choice_id.is_empty()
	if _race_label:
		_race_label.visible = show_races
	_race_list.visible = show_races
	if not show_races:
		_refresh_emergence_next()
		return
	var arch := _archetype_cfg(_choice_id)
	for rid in arch.get("suggested_races", []):
		var race_id := str(rid)
		_race_list.add_item(_race_label_for(race_id))
		_race_list.set_item_metadata(_race_list.item_count - 1, race_id)
	if _race_list.item_count > 0:
		_race_list.select(0)
		_on_race_selected(0)


func _on_race_selected(index: int) -> void:
	if index < 0:
		return
	_race_id = str(_race_list.get_item_metadata(index))
	_refresh_emergence_next()


func _on_name_changed(new_text: String) -> void:
	if _phase == Phase.CRYSTALLIZATION:
		_btn_next.disabled = new_text.strip_edges().length() < 2


func _populate_color_presets() -> void:
	_color_preset.clear()
	for p in _cfg.get("color_presets", []):
		if p is Dictionary:
			_color_preset.add_item(str(p.get("id", "palette")).replace("_", " ").capitalize())
			_color_preset.set_item_metadata(_color_preset.item_count - 1, p)
	if _color_preset.item_count > 0:
		_color_preset.select(0)


func _on_color_changed(_index: int) -> void:
	pass


func _show_phase(p: Phase) -> void:
	_phase = p
	_phase_emergence.visible = p == Phase.EMERGENCE
	_phase_crystal.visible = p == Phase.CRYSTALLIZATION
	_phase_awakening.visible = p == Phase.AWAKENING
	_btn_back.visible = p != Phase.EMERGENCE and p != Phase.AWAKENING
	match p:
		Phase.EMERGENCE:
			_btn_next.text = "Nommer →"
			_refresh_emergence_next()
		Phase.CRYSTALLIZATION:
			_btn_next.text = "Éveil →"
			_btn_next.disabled = _name_edit.text.strip_edges().length() < 2
		Phase.AWAKENING:
			_btn_next.text = "Confirmer l'éclat" if _in_game else "Entrer dans le monde"
			_btn_next.disabled = _pending_result.is_empty()
			_render_summary()


func _render_summary() -> void:
	if _pending_result.is_empty():
		_summary.text = ""
		return
	var stats: Dictionary = _pending_result.get("stats", {})
	var lines: PackedStringArray = []
	lines.append("[center][b]%s[/b][/center]" % _pending_result.get("name", "?"))
	lines.append("")
	lines.append(str(_pending_result.get("race_display", _pending_result.get("race", "?"))))
	lines.append("Archétype : %s" % _pending_result.get("archetype_starter", "?"))
	lines.append("")
	lines.append(str(_pending_result.get("lore_brief", "")))
	lines.append("")
	lines.append("Force %d · Agi %d · Int %d · End %d · Esprit %d" % [
		int(stats.get("force", 0)),
		int(stats.get("agilite", 0)),
		int(stats.get("intelligence", 0)),
		int(stats.get("endurance", 0)),
		int(stats.get("esprit", 0)),
	])
	_summary.text = "\n".join(lines)


func _on_back_pressed() -> void:
	match _phase:
		Phase.CRYSTALLIZATION:
			_show_phase(Phase.EMERGENCE)
		Phase.AWAKENING:
			_show_phase(Phase.CRYSTALLIZATION)


func _on_next_pressed() -> void:
	match _phase:
		Phase.EMERGENCE:
			if _mode != "chaos" and _choice_id.is_empty():
				_status.text = "Choisis une direction"
				return
			_show_phase(Phase.CRYSTALLIZATION)
		Phase.CRYSTALLIZATION:
			var name := _name_edit.text.strip_edges()
			if name.length() < 2:
				_status.text = "Nom trop court (2 caractères min.)"
				return
			_submit_creation(name)
		Phase.AWAKENING:
			if not _pending_result.is_empty():
				if _in_game:
					creation_completed_in_game.emit(_pending_result)
				else:
					creation_completed.emit(_pending_result)
				_hide_panel()


func _submit_creation(name: String) -> void:
	_btn_next.disabled = true
	_status.text = "L'Amas pulse…"
	var colors: Dictionary = {}
	var idx := _color_preset.selected
	if idx >= 0:
		var meta: Variant = _color_preset.get_item_metadata(idx)
		if meta is Dictionary:
			colors = {
				"skin": str(meta.get("skin", "")),
				"eyes": str(meta.get("eyes", "")),
				"accent": str(meta.get("accent", "")),
			}
	var payload := {
		"mode": _mode,
		"customization": {"name": name, "colors": colors},
		"skip_awakening": false,
		"is_ai": false,
	}
	if _mode == "archetype":
		payload["archetype"] = _choice_id
		if not _race_id.is_empty():
			payload["race_id"] = _race_id
	elif _mode == "empreinte":
		payload["empreinte_pnj_id"] = _choice_id
	_client.create_character(payload)


func _on_create_ok(result: Dictionary) -> void:
	_pending_result = result
	_status.text = "Cristallisation réussie"
	_btn_next.disabled = false
	_show_phase(Phase.AWAKENING)


func _on_create_failed(code: String, message: String) -> void:
	# Filet : jamais coincé sur « réseau (2) » — cristallise localement.
	var name := _name_edit.text.strip_edges()
	if name.length() >= 2:
		_pending_result = {
			"character_id": "chr_local",
			"name": name,
			"race": "race:human",
			"race_display": "Humain",
			"archetype_starter": _choice_id if _choice_id else "traqueur",
			"stats": {"force": 55, "agilite": 60, "intelligence": 50, "hp": 100, "endurance": 55, "esprit": 45},
			"lore_brief": "Cristallisation locale — Cortex injoignable.",
			"noyau_id": "noyau_local",
			"particule_seed": "local0001",
			"_mock_numeric_id": 9001,
		}
		_status.text = "Cristallisation locale (Cortex injoignable)"
		_btn_next.disabled = false
		_show_phase(Phase.AWAKENING)
		return
	_btn_next.disabled = false
	_status.text = "%s: %s" % [code, message]


func _hide_panel() -> void:
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vp := get_viewport()
	if vp:
		vp.gui_release_focus()


func _on_cancel_pressed() -> void:
	_hide_panel()
	creation_cancelled.emit()
