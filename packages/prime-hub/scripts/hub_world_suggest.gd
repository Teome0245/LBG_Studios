extends RefCounted
class_name HubWorldSuggest
## File suggestions monde « off » → Studio (pas de mutation auto).

const _HubPaths = preload("res://scripts/hub_paths.gd")

var path: String = ""
var _recent: Array = []  # last N in memory
const MAX_RECENT := 80


func setup() -> void:
	path = _HubPaths.data_file("world_suggestions.jsonl")
	_recent.clear()


func submit(from_name: String, kind: String, text: String, context: Dictionary = {}) -> Dictionary:
	var t := text.strip_edges()
	if t.is_empty():
		return {"ok": false, "error": "empty"}
	var k := kind.strip_edges().to_lower()
	if k.is_empty():
		k = "poi"
	var row := {
		"ts": int(Time.get_unix_time_from_system()),
		"from": from_name.strip_edges(),
		"kind": k,
		"text": t.substr(0, 400),
		"context": context,
		"status": "pending",
	}
	_append_jsonl(row)
	_recent.push_front(row)
	while _recent.size() > MAX_RECENT:
		_recent.pop_back()
	return {"ok": true, "suggestion": row}


func list_recent(limit: int = 40) -> Dictionary:
	var n := mini(maxi(1, limit), MAX_RECENT)
	var out: Array = []
	for i in range(mini(n, _recent.size())):
		out.append(_recent[i])
	# Si mémoire vide, lire queue du fichier
	if out.is_empty() and FileAccess.file_exists(path):
		out = _tail_jsonl(n)
	return {"ok": true, "count": out.size(), "suggestions": out, "source": "prime_hub"}


func _append_jsonl(row: Dictionary) -> void:
	if path.is_empty():
		return
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var f := FileAccess.open(path, FileAccess.READ_WRITE)
	if f == null:
		f = FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_warning("[prime-hub] cannot write world_suggestions")
		return
	f.seek_end()
	f.store_line(JSON.stringify(row))
	f.close()


func _tail_jsonl(limit: int) -> Array:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return []
	var lines: Array = []
	while not f.eof_reached():
		var line := f.get_line().strip_edges()
		if line.is_empty():
			continue
		lines.append(line)
	f.close()
	var out: Array = []
	var start := maxi(0, lines.size() - limit)
	for i in range(lines.size() - 1, start - 1, -1):
		var parsed: Variant = JSON.parse_string(str(lines[i]))
		if typeof(parsed) == TYPE_DICTIONARY:
			out.append(parsed)
	return out
