extends RefCounted
class_name HubWiki
const _HubPaths = preload("res://scripts/hub_paths.gd")

## C6 — wiki / guide joueur data-driven (PNJ + M10 + POI). Pas de lore inventé.
## Ticket 2.2 — Rumeurs inter-villages colportées par les Joueurs IA itinérants.

static var _shared_rumors: Array = []
const MAX_RUMORS: int = 25


static func add_rumor(rumor: Dictionary) -> void:
	if rumor.is_empty():
		return
	var entry := rumor.duplicate(true)
	if not entry.has("timestamp"):
		entry["timestamp"] = Time.get_unix_time_from_system()
	if not entry.has("id"):
		entry["id"] = "rumor_%d" % int(entry["timestamp"] * 1000.0)
	_shared_rumors.insert(0, entry)
	while _shared_rumors.size() > MAX_RUMORS:
		_shared_rumors.pop_back()


static func get_rumors(max_count: int = 10) -> Array:
	if _shared_rumors.is_empty():
		return []
	var count := mini(max_count, _shared_rumors.size())
	return _shared_rumors.slice(0, count)


static func get_latest_rumor(origin_filter: String = "") -> Dictionary:
	for r in _shared_rumors:
		if typeof(r) != TYPE_DICTIONARY:
			continue
		if origin_filter.is_empty() or str(r.get("origin", "")) == origin_filter:
			return (r as Dictionary).duplicate(true)
	return {}


static func clear_rumors() -> void:
	_shared_rumors.clear()


func snapshot() -> Dictionary:
	var npcs := _hub_npcs()
	var pois := _hub_pois()
	var professions := _professions()
	var recipes := _recipes()
	var guides := _guide_index()
	var rumors := get_rumors()
	var md := _render_markdown(npcs, pois, professions, recipes, guides, rumors)
	var drift := {
		"npc_count": npcs.size(),
		"poi_count": pois.size(),
		"profession_count": professions.size(),
		"recipe_count": recipes.size(),
		"rumor_count": rumors.size(),
		"ok": npcs.size() >= 12 and professions.size() >= 4 and pois.size() >= 6,
		"rule": "npc>=12 · profession>=4 · poi>=6 (hub Lost Heaven)",
	}
	return {
		"ok": true,
		"ticket": "C6",
		"hub": "lost_heaven",
		"planet": "Scrapaltai",
		"title": "Wiki hub — Lost Heaven",
		"npcs": npcs,
		"pois": pois,
		"professions": professions,
		"recipes": recipes,
		"guides": guides,
		"rumors": rumors,
		"markdown": md,
		"drift": drift,
		"source": "prime_hub",
	}


func markdown() -> Dictionary:
	var snap := snapshot()
	return {
		"ok": bool(snap.get("ok")),
		"content_type": "text/markdown; charset=utf-8",
		"markdown": str(snap.get("markdown", "")),
		"drift": snap.get("drift", {}),
		"source": "prime_hub",
		"ticket": "C6",
	}


func _hub_npcs() -> Array:
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("npc_registry.json"))
	var out: Array = []
	if typeof(raw) != TYPE_DICTIONARY:
		return out
	var arr = raw.get("npcs", [])
	if typeof(arr) != TYPE_ARRAY:
		return out
	for n in arr:
		if typeof(n) != TYPE_DICTIONARY:
			continue
		var zone := str(n.get("zone", "")).to_lower()
		var nid := str(n.get("id", ""))
		var hubish := (
			"lost heaven" in zone or "lost_heaven" in zone or "scrapaltai" in zone
			or nid.begins_with("npc:core3_") or nid in [
				"npc:scribe", "npc:sergent_rue", "npc:rumeuriste", "npc:videur",
				"npc:habitue_cantina", "npc:guide_quartier", "npc:artiste_scene",
				"npc:maitre_salle", "npc:guard", "npc:agent_circulation",
			]
		)
		if not hubish:
			continue
		out.append({
			"id": nid,
			"name": str(n.get("name", nid)),
			"role": str(n.get("role", "")),
			"zone": str(n.get("zone", "")),
			"summary": str(n.get("summary", "")).substr(0, 120),
		})
		if out.size() >= 40:
			break
	return out


func _hub_pois() -> Array:
	var path := OS.get_environment("LBG_HUB_BUILDINGS_JSON").strip_edges()
	if path.is_empty():
		path = _HubPaths.data_file("lost_heaven_buildings.json")
	var raw: Variant = _HubPaths.read_json(path)
	var out: Array = []
	if typeof(raw) != TYPE_DICTIONARY:
		return out
	var buildings = raw.get("buildings", [])
	if typeof(buildings) != TYPE_ARRAY:
		return out
	for b in buildings:
		if typeof(b) != TYPE_DICTIONARY:
			continue
		var bid := str(b.get("id", ""))
		if bid.is_empty():
			continue
		out.append({
			"id": bid,
			"label": str(b.get("label", bid)),
			"kind": str(b.get("kind", "")),
			"x": float(b.get("x", 0.0)),
			"z": float(b.get("z", 0.0)),
			"role": str(b.get("role", "")),
		})
	return out


func _professions() -> Array:
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("catalog_skills.json"))
	var out: Array = []
	if typeof(raw) != TYPE_DICTIONARY:
		return out
	var items = raw.get("items", [])
	if typeof(items) != TYPE_ARRAY:
		return out
	for it in items:
		if typeof(it) != TYPE_DICTIONARY:
			continue
		out.append({
			"id": str(it.get("id", "")),
			"name": str(it.get("name", it.get("id", "?"))),
			"tree": str(it.get("tree", "")),
			"kind": str(it.get("kind", "profession")),
		})
	return out


func _recipes() -> Array:
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("catalog_recipes.json"))
	var out: Array = []
	if typeof(raw) != TYPE_DICTIONARY:
		return out
	var items = raw.get("items", [])
	if typeof(items) != TYPE_ARRAY:
		return out
	for it in items:
		if typeof(it) != TYPE_DICTIONARY:
			continue
		out.append({
			"id": str(it.get("id", "")),
			"name": str(it.get("name", it.get("id", "?"))),
			"requires_skill": str(it.get("requires_skill", "")),
			"category": str(it.get("category", "")),
		})
	return out


func _guide_index() -> Array:
	var styles := ["prospecteur", "artisan", "medecin", "scene", "scout"]
	var out: Array = []
	for ps in styles:
		var path := _HubPaths.data_file("guide_%s.json" % ps)
		var raw: Variant = _HubPaths.read_json(path)
		if typeof(raw) != TYPE_DICTIONARY:
			continue
		var g = raw.get("guide", raw)
		if typeof(g) != TYPE_DICTIONARY:
			continue
		out.append({
			"playstyle": ps,
			"profession_name": str(g.get("profession_name", ps)),
			"loop": str(g.get("loop", "")),
		})
	return out


func _render_markdown(npcs: Array, pois: Array, professions: Array, recipes: Array, guides: Array, rumors: Array = []) -> String:
	var lines: PackedStringArray = PackedStringArray()
	lines.append("# Wiki hub — Lost Heaven")
	lines.append("")
	lines.append("**Ticket** : C6 · **Source** : prime-hub (registry + M10 catalog + POI buildings)")
	lines.append("")
	lines.append("> Guide joueur data-driven — pas de lore inventé hors inventaire / M10 / POI.")
	if not rumors.is_empty():
		lines.append("")
		lines.append("## Rumeurs & Échos des Caravanes")
		lines.append("")
		lines.append("> Faits marquants rapportés par les Joueurs IA itinérants de retour au hub.")
		lines.append("")
		for r in rumors:
			if typeof(r) != TYPE_DICTIONARY:
				continue
			var orig := str(r.get("origin_label", r.get("origin", "Région inconnue")))
			var bot_name := str(r.get("source_bot", "Un voyageur"))
			var txt := str(r.get("text", ""))
			lines.append("- **[%s]** *(via %s)* : %s" % [orig, bot_name, txt])
	lines.append("")
	lines.append("## PNJ hub")
	lines.append("")
	lines.append("| Nom | Id | Rôle | Zone |")
	lines.append("|-----|----|------|------|")
	for n in npcs:
		if typeof(n) != TYPE_DICTIONARY:
			continue
		lines.append("| %s | `%s` | %s | %s |" % [
			str(n.get("name", "?")),
			str(n.get("id", "")),
			str(n.get("role", "")),
			str(n.get("zone", "")).substr(0, 40),
		])
	lines.append("")
	lines.append("## POI Lost Heaven")
	lines.append("")
	lines.append("| Label | Id | Kind |")
	lines.append("|-------|----|------|")
	for p in pois:
		if typeof(p) != TYPE_DICTIONARY:
			continue
		lines.append("| %s | `%s` | %s |" % [
			str(p.get("label", "?")),
			str(p.get("id", "")),
			str(p.get("kind", "")),
		])
	lines.append("")
	lines.append("## Professions M10")
	lines.append("")
	for pr in professions:
		if typeof(pr) != TYPE_DICTIONARY:
			continue
		lines.append("- **%s** (`%s`) — %s" % [
			str(pr.get("name", "?")),
			str(pr.get("id", "")),
			str(pr.get("tree", "")),
		])
	lines.append("")
	lines.append("## Schematics / craft")
	lines.append("")
	for r in recipes:
		if typeof(r) != TYPE_DICTIONARY:
			continue
		lines.append("- **%s** ← `%s`" % [str(r.get("name", "?")), str(r.get("requires_skill", ""))])
	lines.append("")
	lines.append("## Guides playstyle")
	lines.append("")
	for g in guides:
		if typeof(g) != TYPE_DICTIONARY:
			continue
		lines.append("- **%s** — %s" % [str(g.get("profession_name", g.get("playstyle"))), str(g.get("loop", ""))])
	lines.append("")
	lines.append("## Boucles utiles")
	lines.append("")
	lines.append("- Board Daan · event scrap · salvage `[1]` pile ferraille · craft **T**")
	lines.append("- Jax · négo bornée (trade/offer) · tip scène")
	lines.append("- Scribe · chronique session (C5)")
	lines.append("")
	return "\n".join(lines)
