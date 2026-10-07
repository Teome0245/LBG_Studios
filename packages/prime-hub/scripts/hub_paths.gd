extends RefCounted
class_name HubPaths
## Répertoire d'état / assets data pour prime-hub.


static func state_dir() -> String:
	var env := OS.get_environment("LBG_PRIME_HUB_STATE_DIR").strip_edges()
	if env.is_empty():
		env = OS.get_environment("LBG_HUB_STATE_DIR").strip_edges()
	if env.is_empty():
		var root := ProjectSettings.globalize_path("res://").rstrip("/")
		env = root.path_join("data")
	DirAccess.make_dir_recursive_absolute(env)
	return env


static func data_file(name: String) -> String:
	return state_dir().path_join(name)


static func read_json(path: String) -> Variant:
	if path.is_empty() or not FileAccess.file_exists(path):
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	return raw


static func write_json(path: String, payload: Dictionary) -> bool:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(payload))
	f.close()
	DirAccess.remove_absolute(path)
	return DirAccess.rename_absolute(tmp, path) == OK
