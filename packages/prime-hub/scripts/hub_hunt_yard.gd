extends RefCounted
class_name HubHuntYard
const _HubPaths = preload("res://scripts/hub_paths.gd")

## Cour de chasse — moteur Python déterministe (tools/hunt_yard.py).
## Contrat : GET /v1/hunt-yard · POST reset|tick|run · claim via economy.

const QUEST_ID := "lh_hunt_chacal"
const STEP_ID := "meute"


func _script_path() -> String:
	var override := OS.get_environment("LBG_HUNT_YARD_PY").strip_edges()
	if not override.is_empty() and FileAccess.file_exists(override):
		return override
	var candidate := ProjectSettings.globalize_path("res://tools/hunt_yard.py")
	if FileAccess.file_exists(candidate):
		return candidate
	return "tools/hunt_yard.py"


func _state_path() -> String:
	var override := OS.get_environment("LBG_HUNT_YARD_STATE").strip_edges()
	if not override.is_empty():
		return override
	return _HubPaths.data_file("hunt_yard_session.pkl")


func _python() -> String:
	var override := OS.get_environment("LBG_HUNT_YARD_PYTHON").strip_edges()
	if not override.is_empty():
		return override
	return "python3"


func _run_cmd(args: PackedStringArray) -> Dictionary:
	OS.set_environment("LBG_HUNT_YARD_STATE", _state_path())
	var argv := PackedStringArray([_script_path()])
	for a in args:
		argv.append(str(a))
	var output: Array = []
	var code := OS.execute(_python(), argv, output, true, false)
	var text := ""
	for line in output:
		text += str(line)
		if not str(line).ends_with("\n"):
			text += "\n"
	text = text.strip_edges()
	if text.is_empty():
		return {"ok": false, "error": "hunt_yard_empty", "exit_code": code}
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		var lines := text.split("\n")
		for i in range(lines.size() - 1, -1, -1):
			var cand := str(lines[i]).strip_edges()
			if cand.begins_with("{"):
				parsed = JSON.parse_string(cand)
				if typeof(parsed) == TYPE_DICTIONARY:
					break
	if typeof(parsed) != TYPE_DICTIONARY:
		return {
			"ok": false,
			"error": "hunt_yard_parse",
			"exit_code": code,
			"raw": text.substr(0, 240),
		}
	var out: Dictionary = parsed
	if not out.has("ok"):
		out["ok"] = true
	out["source"] = "prime_hub"
	return out


func snapshot() -> Dictionary:
	return _run_cmd(PackedStringArray(["--json-cmd", "snapshot"]))


func reset(seed: int = 1) -> Dictionary:
	return _run_cmd(PackedStringArray(["--json-cmd", "reset", "--seed", str(seed)]))


func tick(n: int = 1) -> Dictionary:
	return _run_cmd(PackedStringArray(["--json-cmd", "tick", "--ticks", str(maxi(1, n))]))


func run(max_ticks: int = 120) -> Dictionary:
	return _run_cmd(PackedStringArray(["--json-cmd", "run", "--max-ticks", str(maxi(1, max_ticks))]))


func victory() -> bool:
	var snap := snapshot()
	return str(snap.get("status", "")) == "victory"
