# hub_focus.gd — Masque visuel hub LH (entités + overlays deprecated ME)
extends RefCounted
class_name HubFocus

const DEFAULT_DEPRECATED: Array = [
	{"id": "mos_eisley", "x": 3520.0, "z": -4800.0, "radius_m": 680.0},
	{"id": "anchorhead", "x": -100.0, "z": -5400.0, "radius_m": 520.0},
	{"id": "bestine", "x": -4000.0, "z": -6000.0, "radius_m": 520.0},
]

static func cfg() -> Dictionary:
	var wr := MapTextureLoader.world_render_cfg()
	var hf: Variant = wr.get("hub_focus", null)
	return hf if hf is Dictionary else {}

static func enabled() -> bool:
	if cfg().is_empty():
		return true
	return bool(cfg().get("enabled", true))

static func anchor() -> Vector2:
	var c := cfg()
	return Vector2(float(c.get("anchor_x", 4749.0)), float(c.get("anchor_z", -737.0)))

static func hub_radius_m() -> float:
	return float(cfg().get("radius_m", 980.0))

static func deprecated_cities() -> Array:
	var raw: Variant = cfg().get("deprecated_cities", DEFAULT_DEPRECATED)
	return raw if raw is Array else DEFAULT_DEPRECATED

static func in_deprecated_city(x: float, z: float) -> bool:
	for item: Variant in deprecated_cities():
		if not item is Dictionary:
			continue
		var d: Dictionary = item
		var cx := float(d.get("x", 0.0))
		var cz := float(d.get("z", 0.0))
		var r := float(d.get("radius_m", 600.0))
		var dx := x - cx
		var dz := z - cz
		if dx * dx + dz * dz <= r * r:
			return true
	return false

static func in_hub_radius(x: float, z: float) -> bool:
	var a := anchor()
	var r := hub_radius_m()
	var dx := x - a.x
	var dz := z - a.y
	return dx * dx + dz * dz <= r * r

static func should_show_entity(core3: Vector3, kind: String, name: String = "", entity_key: String = "") -> bool:
	if kind == "player":
		return true
	if is_clutter(kind, name, entity_key):
		return false
	if not enabled():
		return true
	if in_deprecated_city(core3.x, core3.z):
		return false
	return in_hub_radius(core3.x, core3.z)


## Navettes / tangibles Core3 (points gris « shuttle fly to tatooine »).
static func is_clutter(kind: String, name: String = "", entity_key: String = "") -> bool:
	var k := kind.strip_edges().to_lower()
	if k in ["object", "tangible", "vehicle", "building", "static", "waypoint", "cell"]:
		return true
	var blob := ("%s %s" % [name, entity_key]).to_lower()
	if blob.strip_edges() == "":
		return k != "npc" and k != "player"
	for frag in [
		"shuttle", "tatooine", "ticket collector", "ticket_collector",
		"starport", "player_shuttle", "transport_shuttle", "fly to",
		"mos eisley", "mos espa", "anchorhead", "bestine",
		"waypoint", "shared_shuttle", "shuttleport",
	]:
		if blob.contains(frag):
			return true
	return false

static func should_draw_world_overlay(x: float, z: float) -> bool:
	if not enabled():
		return true
	return not in_deprecated_city(x, z)
