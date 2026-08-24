extends Node
## InitiationQuestController — quête « L'Éclat qui se divise » (1er perso, local V1)

signal step_changed(step_id: String, step_index: int)
signal quest_completed(quest_id: String)
signal request_create_character
signal request_open_echo_panel
signal show_particule(noyau_id: String, particule_seed: String)

const CONFIG_PATH := "res://config/initiation_quest_particule.json"
const SAVE_PATH := "user://initiation_quest.json"

var quest_id: String = "lh_init_particule_echo"
var active: bool = false
var step_index: int = 0
var _cfg: Dictionary = {}
var _steps: Array = []


func _ready() -> void:
	_load_config()


func _load_config() -> void:
	_cfg = {}
	if FileAccess.file_exists(CONFIG_PATH):
		var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
		if raw is Dictionary:
			_cfg = raw
	quest_id = str(_cfg.get("quest_id", quest_id))
	_steps = _cfg.get("steps", [])


func is_done() -> bool:
	return bool(_load_save().get("done", false))


func should_auto_start(hammat_roster_size: int) -> bool:
	if is_done():
		return false
	var save := _load_save()
	if bool(save.get("in_progress", false)):
		return true
	return hammat_roster_size <= int(_cfg.get("requires_roster_max", 1))


func start_quest() -> void:
	if is_done():
		return
	active = true
	var save := _load_save()
	step_index = int(save.get("step_index", 0))
	step_index = clampi(step_index, 0, maxi(0, _steps.size() - 1))
	save["in_progress"] = true
	_save(save)
	_emit_step()


func get_current_step() -> Dictionary:
	if step_index < 0 or step_index >= _steps.size():
		return {}
	return _steps[step_index]


func advance_step() -> void:
	if not active:
		return
	step_index += 1
	var save := _load_save()
	save["step_index"] = step_index
	if step_index >= _steps.size():
		_complete_quest(save)
		return
	_save(save)
	_emit_step()


func mark_echo_practiced() -> void:
	var step := get_current_step()
	if str(step.get("id", "")) == "invocation":
		advance_step()


func on_second_character_created() -> void:
	var step := get_current_step()
	if str(step.get("id", "")) == "second_eclat":
		advance_step()


func get_action_for_step() -> String:
	return str(get_current_step().get("action", "continue"))


func get_button_label() -> String:
	var step := get_current_step()
	return str(step.get("button_label", "Continuer"))


func _complete_quest(save: Dictionary) -> void:
	active = false
	save["done"] = true
	save["in_progress"] = false
	save["completed_at"] = Time.get_datetime_string_from_system(true)
	_save(save)
	quest_completed.emit(quest_id)


func _emit_step() -> void:
	var step := get_current_step()
	if step.is_empty():
		return
	step_changed.emit(str(step.get("id", "")), step_index)


func _load_save() -> Dictionary:
	if not FileAccess.file_exists(SAVE_PATH):
		return {}
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(SAVE_PATH))
	return raw if raw is Dictionary else {}


func _save(data: Dictionary) -> void:
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify(data))
	f.close()


static func reset_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(SAVE_PATH)
