# hub_runtime_cfg.gd — lit config/hub_runtime.json (spike ADR 0026)
extends RefCounted
class_name HubRuntimeCfg

const PATH := "res://config/hub_runtime.json"

## Nom personnage session (login) — prioritaire sur le JSON figé « Voyageur ».
static var _session_player_name: String = ""


static func load_cfg() -> Dictionary:
	if not FileAccess.file_exists(PATH):
		return {}
	var f := FileAccess.open(PATH, FileAccess.READ)
	if f == null:
		return {}
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	return raw if raw is Dictionary else {}


static func enabled() -> bool:
	return bool(load_cfg().get("enabled", false))


static func http_url(fallback: String = "http://192.168.0.246:8787") -> String:
	var c := load_cfg()
	var u := str(c.get("http_url", "")).strip_edges()
	return u if u != "" else fallback


static func set_player_name(name: String) -> void:
	_session_player_name = name.strip_edges()


static func player_name(fallback: String = "Voyageur") -> String:
	if not _session_player_name.is_empty():
		return _session_player_name
	var c := load_cfg()
	var n := str(c.get("player_name", "")).strip_edges()
	if n != "":
		return n
	return fallback
