extends RefCounted
class_name HubCatalog
const _HubPaths = preload("res://scripts/hub_paths.gd")

## Catalog C10 + guides + tick-matrix — snapshots JSON sous data/.


func catalog(type_name: String = "skills") -> Dictionary:
	var t := type_name.strip_edges().to_lower()
	if t.is_empty():
		t = "skills"
	var path: String = _HubPaths.data_file("catalog_%s.json" % t)
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) == TYPE_DICTIONARY:
		var out: Dictionary = raw
		out["source"] = "prime_hub"
		return out
	return {"ok": false, "error": "catalog_missing", "type": t, "source": "prime_hub"}


func guide(playstyle: String = "prospecteur") -> Dictionary:
	var ps := playstyle.strip_edges().to_lower()
	if ps.is_empty():
		ps = "prospecteur"
	var path: String = _HubPaths.data_file("guide_%s.json" % ps)
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) == TYPE_DICTIONARY:
		var out: Dictionary = raw
		out["source"] = "prime_hub"
		return out
	return {
		"ok": true,
		"playstyle": ps,
		"summary": "Guide hub Lost Heaven — snapshot absent, fallback court.",
		"source": "prime_hub",
	}


func tick_matrix() -> Dictionary:
	var path: String = _HubPaths.data_file("tick_matrix.json")
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) == TYPE_DICTIONARY:
		var out: Dictionary = raw
		out["source"] = "prime_hub"
		return out
	return {"ok": true, "count": 0, "actions": [], "source": "prime_hub"}
