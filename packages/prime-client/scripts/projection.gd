# projection.gd — Projection Core3 -> Godot 2D
# Stockage Core3 : X=Est/Ouest, Y=hauteur (altitude), Z=Nord/Sud (+Z=nord).
# Affichage HUD (format_hud_*) : E/O · N/S · ↑alt — voir altitude_local_m().
class_name Projection3D2D

const SCALE: float = 0.5   # 1 unite Core3 = 0.5 pixel

# ~2 m au sol ; même repère que size_m des bâtiments (mètres Core3).
const ENTITY_HEIGHT_M: float = 2.0
# Jetons lisibles mais plus petits que les emprises bâtiment (mul ~3).
const ENTITY_READABILITY: float = 8.0

static func entity_token_px() -> float:
	return ENTITY_HEIGHT_M * SCALE * ENTITY_READABILITY

# Tatooine outdoor : Y monde ~ -4800 ; intérieurs : Y local (petites valeurs).
const TATOOINE_FLOOR_Y: float = -4800.0
const OUTDOOR_Y_THRESHOLD: float = -1000.0

# Remap feeds où le nord est dans `y` et la hauteur dans `z`
# (snapshots ia_bridge / zone_feed). Core3 correct : X est, Y hauteur, Z nord.
const AXIS_SWAP_Z_MAX: float = 50.0
const AXIS_SWAP_Y_MIN: float = 100.0

static func to_screen(core3_pos: Vector3) -> Vector2:
	return Vector2(core3_pos.x * SCALE, -core3_pos.z * SCALE)

static func needs_yz_swap(pos: Vector3) -> bool:
	return absf(pos.z) < AXIS_SWAP_Z_MAX and absf(pos.y) > AXIS_SWAP_Y_MIN

static func normalize_core3_pos(pos: Vector3) -> Vector3:
	if needs_yz_swap(pos):
		return Vector3(pos.x, pos.z, pos.y)
	return pos

static func height_offset(core3_y: float) -> float:
	var local_y := core3_y
	if core3_y < OUTDOOR_Y_THRESHOLD:
		local_y = core3_y - TATOOINE_FLOOR_Y
	return clampf(-local_y * SCALE, -64.0, 64.0)

static func project(core3_pos: Vector3) -> Dictionary:
	return {
		"position": to_screen(core3_pos),
		"offset_y": height_offset(core3_pos.y),
	}

static func from_screen(screen_pos: Vector2) -> Vector3:
	return Vector3(
		screen_pos.x / SCALE,
		0.0,
		-screen_pos.y / SCALE,
	)

## Altitude locale (m) — extérieur : au-dessus du plan sol Tatooine ; intérieur : Y cellule.
## Future : soustraire ici une DTM relief (canyon, plateaux) ou plan d'étage explicite.
static func altitude_local_m(core3_y: float) -> float:
	if core3_y < OUTDOOR_Y_THRESHOLD:
		return core3_y - TATOOINE_FLOOR_Y
	return core3_y

static func is_outdoor_altitude(core3_y: float) -> bool:
	return core3_y < OUTDOOR_Y_THRESHOLD

## Affichage HUD : X=E/O (Core3 X), Y=N/S (Core3 Z), Z=altitude (Core3 Y).
static func format_hud_coordinates(pos: Vector3, compact: bool = true) -> String:
	var p := normalize_core3_pos(pos)
	var ew := _axis_ew_label(p.x)
	var ns := _axis_ns_label(p.z)
	var alt_m := altitude_local_m(p.y)
	var alt := _format_altitude_label(p.y, alt_m, compact)
	if compact:
		return "%s %s %s" % [ew, ns, alt]
	var ew_full: String
	if p.x >= 0.0:
		ew_full = "Est %.0f" % absf(p.x)
	else:
		ew_full = "Ouest %.0f" % absf(p.x)
	var ns_full: String
	if p.z >= 0.0:
		ns_full = "Nord %.0f" % absf(p.z)
	else:
		ns_full = "Sud %.0f" % absf(p.z)
	var alt_full := "Alt %.0f m" % alt_m
	if not is_outdoor_altitude(p.y):
		alt_full += " (local)"
	return "%s · %s · %s" % [ew_full, ns_full, alt_full]

static func format_hud_plan(pos: Vector3, compact: bool = true) -> String:
	var p := normalize_core3_pos(pos)
	if compact:
		return "%s %s" % [_axis_ew_label(p.x), _axis_ns_label(p.z)]
	var ew_full: String
	if p.x >= 0.0:
		ew_full = "Est %.0f" % absf(p.x)
	else:
		ew_full = "Ouest %.0f" % absf(p.x)
	var ns_full: String
	if p.z >= 0.0:
		ns_full = "Nord %.0f" % absf(p.z)
	else:
		ns_full = "Sud %.0f" % absf(p.z)
	return "%s · %s" % [ew_full, ns_full]

static func _axis_ew_label(x: float) -> String:
	var v := int(roundf(absf(x)))
	if x >= 0.0:
		return "E%d" % v
	return "O%d" % v

static func _axis_ns_label(z: float) -> String:
	var v := int(roundf(absf(z)))
	if z >= 0.0:
		return "N%d" % v
	return "S%d" % v

static func _format_altitude_label(core3_y: float, local_m: float, compact: bool) -> String:
	var v := int(roundf(local_m))
	if compact:
		if is_outdoor_altitude(core3_y):
			return "↑%dm" % v
		return "↑%dm*" % v
	if is_outdoor_altitude(core3_y):
		return "Alt %d m" % v
	return "Alt %d m (local)" % v
