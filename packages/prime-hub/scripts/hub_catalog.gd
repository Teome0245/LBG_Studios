extends RefCounted
class_name HubCatalog
const _HubPaths = preload("res://scripts/hub_paths.gd")
const HubWikiScript = preload("res://scripts/hub_wiki.gd")

## Catalog C10 + guides + tick-matrix — snapshots JSON sous data/.

var _wiki = null


func _wiki_svc():
	if _wiki == null:
		_wiki = HubWikiScript.new()
	return _wiki


func wiki() -> Dictionary:
	return _wiki_svc().snapshot()


func catalog(type_name: String = "skills") -> Dictionary:
	var t := type_name.strip_edges().to_lower()
	if t.is_empty():
		t = "skills"
	var path: String = _HubPaths.data_file("catalog_%s.json" % t)
	var raw: Variant = _HubPaths.read_json(path)
	if typeof(raw) == TYPE_DICTIONARY:
		var out: Dictionary = raw
		out["source"] = "prime_hub"
		out["ok"] = true
		# Panel Talents attend skills[] + schematics[] (pas seulement items M10).
		if t == "skills":
			if not out.has("skills") or typeof(out.get("skills")) != TYPE_ARRAY or (out["skills"] as Array).is_empty():
				out["skills"] = _skills_for_ui(out.get("items", []))
			if not out.has("schematics") or typeof(out.get("schematics")) != TYPE_ARRAY:
				out["schematics"] = _schematics_for_ui()
		elif t == "recipes":
			if not out.has("schematics"):
				out["schematics"] = (out.get("items", []) as Array).duplicate(true) if typeof(out.get("items")) == TYPE_ARRAY else []
		return out
	return {"ok": false, "error": "catalog_missing", "type": t, "source": "prime_hub"}


func _skills_for_ui(items: Variant) -> Array:
	## Skills joueur hub (rangs novices) + libellés professions du catalog M10.
	var out: Array = [
		{"id": "prospecteur_r1", "name": "Prospecteur · rang 1", "tree": "gathering", "rank": 1},
		{"id": "artisan_rue_r1", "name": "Artisan de rue · rang 1", "tree": "crafting", "rank": 1},
		{"id": "medecine_camp_r1", "name": "Médecine de camp · rang 1", "tree": "medicine", "rank": 1},
		{"id": "pilotage_shuttle_r1", "name": "Pilotage shuttle · rang 1", "tree": "pilot", "rank": 1},
	]
	if typeof(items) != TYPE_ARRAY:
		return out
	for it in items:
		if typeof(it) != TYPE_DICTIONARY:
			continue
		out.append({
			"id": str(it.get("id", "")),
			"name": str(it.get("name", it.get("id", "?"))),
			"tree": str(it.get("tree", it.get("kind", ""))),
			"rank": 0,
			"kind": "profession",
		})
	return out


func _schematics_for_ui() -> Array:
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("catalog_recipes.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		return []
	var items = raw.get("items", [])
	if typeof(items) != TYPE_ARRAY:
		return []
	return (items as Array).duplicate(true)


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
