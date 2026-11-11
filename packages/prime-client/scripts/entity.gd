# entity.gd — Entité 2D : sprite IA (top-down) ou cercle fallback + label
extends Node2D
class_name Entity

const _SpriteRegistry = preload("res://scripts/sprite_registry.gd")
const _NpcAnchorResolver = preload("res://scripts/npc_anchor_resolver.gd")
const _Projection3D2D = preload("res://scripts/projection.gd")
const _MapTextureLoader = preload("res://scripts/map_texture_loader.gd")
const _HubFocus = preload("res://scripts/hub_focus.gd")

var object_id:     int     = 0
var entity_key:    String  = ""
var core3_pos:     Vector3 = Vector3.ZERO
var color:         Color   = Color.RED
var radius:        float   = 5.0
var label_text:    String  = ""
var _label_raw:     String  = ""
var height_offset: float   = 0.0
var kind:          String  = "object"

var _use_sprite: bool = false
var _pending_texture: Texture2D = null
var _display_jitter: Vector2 = Vector2.ZERO
var _idle_phase: float = 0.0
var _anchor: Dictionary = {}
var _visual_home: Vector3 = Vector3.ZERO
var _use_visual_override: bool = false
## Orientation affichée (tip du triangle) : 0 = nord écran (+Core3 Z).
var facing_angle: float = 0.0
var _selected: bool = false
var _last_patrol_offset: Vector3 = Vector3.ZERO
## Lissage zone_state ~10 Hz → écran (évite saccades bots/PNJ distants).
var _smooth_enabled: bool = false
var _smooth_target: Vector3 = Vector3.ZERO
var _smooth_vel: Vector3 = Vector3.ZERO
var _smooth_target_ms: int = 0
var _last_draw_pos: Vector2 = Vector2.INF
const SMOOTH_SNAP_M := 28.0
## Suivi souple + légère extrapolation vitesse (cible réseau 10 Hz).
const SMOOTH_RATE := 11.0
const SMOOTH_EXTRAP_S := 0.08

## Joueur = joueur (humain ou IA) — même couleur, pas de tag « bot ».
const COLOR_PLAYER_OFFICIAL := Color(0.2, 0.4, 1.0, 1.0)
const COLOR_PLAYER_BOT      := COLOR_PLAYER_OFFICIAL
const COLOR_NPC             := Color(1.0, 0.5, 0.1, 1.0)
const COLOR_OBJECT          := Color(0.7, 0.7, 0.7, 0.8)

static var show_nameplates: bool = false
## C3 — nameplate forcé même si play mode masque les labels globaux.
var force_nameplate: bool = false
## P5b — windup boss (telegraph) / aggro : teinte + anneau.
var combat_goal: String = ""
var is_boss_beast: bool = false
var faction: String = "neutral"
var species_id: String = "human"
var is_mounted: bool = false
var is_lightsaber_active: bool = false
var lightsaber_color: Color = Color(0.2, 0.7, 1.0)
var current_hp: int = 1000
var max_hp: int = 1000

# Lanterne dynamique de caravane
var _caravan_lantern_light: PointLight2D = null
static var _shared_caravan_light_tex: Texture2D = null

func set_force_nameplate(enabled: bool) -> void:
	force_nameplate = enabled
	queue_redraw()


func set_beast_combat(goal: String, boss: bool = false) -> void:
	var g := goal.strip_edges().to_lower()
	if g == combat_goal and boss == is_boss_beast:
		return
	combat_goal = g
	is_boss_beast = boss
	if kind == "beast" and g == "telegraph":
		set_process(true)
	queue_redraw()

func set_entity_key(key: String) -> void:
	entity_key = key
	_rebind_anchor()
	_refresh_appearance()

func set_core3_position(pos: Vector3) -> void:
	## Snap immédiat (spawn, téléport, joueur local).
	_smooth_enabled = false
	_smooth_vel = Vector3.ZERO
	_smooth_target = pos
	_smooth_target_ms = Time.get_ticks_msec()
	var prev := core3_pos
	core3_pos     = pos
	height_offset = _Projection3D2D.height_offset(pos.y)
	if not _use_visual_override:
		_visual_home = Vector3(pos.x, pos.y, pos.z)
	update_facing_from_move(prev, pos)
	_refresh_screen_pos()
	_update_sprite_offset()
	queue_redraw()


func set_core3_position_smooth(pos: Vector3) -> void:
	## Cible réseau — interpolée dans _process (remote bots / PNJ hub).
	if entity_key == "player:human":
		set_core3_position(pos)
		return
	var dx := pos.x - core3_pos.x
	var dz := pos.z - core3_pos.z
	if dx * dx + dz * dz > SMOOTH_SNAP_M * SMOOTH_SNAP_M:
		set_core3_position(pos)
		return
	var now := Time.get_ticks_msec()
	var dt := float(now - _smooth_target_ms) * 0.001
	if _smooth_target_ms > 0 and dt > 0.02 and dt < 0.75:
		_smooth_vel = Vector3(
			(pos.x - _smooth_target.x) / dt,
			0.0,
			(pos.z - _smooth_target.z) / dt
		)
		# Plafond ~vitesse bot hub (évite pics sur teleports partiels).
		var spd := _smooth_vel.length()
		if spd > 20.0:
			_smooth_vel *= 20.0 / spd
	_smooth_target = pos
	_smooth_target_ms = now
	_smooth_enabled = true
	set_process(true)

func set_display_jitter(offset: Vector2) -> void:
	_display_jitter = offset
	_refresh_screen_pos()

func set_kind(k: String) -> void:
	kind = k
	set_process(_wants_ambient())

func set_color(c: Color) -> void:
	color = c
	queue_redraw()


func set_selected(selected: bool) -> void:
	_selected = selected
	queue_redraw()


func update_facing_from_move(from: Vector3, to: Vector3) -> void:
	var dx := to.x - from.x
	var dz := to.z - from.z
	if dx * dx + dz * dz < 0.0025:
		return
	# Core3 X est → écran X ; Core3 Z nord → écran -Y
	var screen_dir := Vector2(dx, -dz).normalized()
	facing_angle = screen_dir.angle() + PI * 0.5
	queue_redraw()


func set_facing_from_direction(dir: Vector3) -> void:
	if dir.length_squared() < 0.0001:
		return
	var screen_dir := Vector2(dir.x, -dir.z).normalized()
	facing_angle = screen_dir.angle() + PI * 0.5
	queue_redraw()

func set_label(text: String) -> void:
	_label_raw = text
	label_text = _short_label(text)
	_rebind_anchor()
	_refresh_appearance()
	queue_redraw()


## Nom complet pour UI dialogue / portraits (sans troncature nameplate 18 car.).
func get_display_name() -> String:
	var s: String = _label_raw.strip_edges() if _label_raw != "" else label_text.strip_edges()
	if s.is_empty():
		return "PNJ" if kind == "npc" else "Voyageur"
	# C1 — nom seul pour dialogue (pas d’activité · ni tag espèce).
	for sep in [" · ", " (PNJ", " (Bot", " (bot", " (IA", " (ia", " — ", " - "]:
		var i := s.find(sep)
		if i > 0:
			s = s.substr(0, i).strip_edges()
			break
	if s.length() > 48:
		s = s.substr(0, 45) + "…"
	return s


func _refresh_appearance() -> void:
	if kind != "player" and kind != "npc":
		return
	var raw := _label_raw if _label_raw != "" else label_text
	var tex: Texture2D = _SpriteRegistry.resolve_texture(kind, raw, entity_key)
	if tex:
		set_sprite_texture(tex, _SpriteRegistry.resolve_tint(kind, raw))

static func _short_label(raw: String) -> String:
	var s: String = raw.strip_edges()
	# "Jax Moro · Fel'Rani (PNJ IA)" → "Jax Moro" ; "Nix · escorte" garde l'activité.
	var activity := ""
	var dot := s.find(" · ")
	if dot > 0:
		activity = s.substr(dot)  # inclut « · … »
		s = s.substr(0, dot).strip_edges()
	for sep in [" (PNJ", " (Bot", " (bot", " (IA", " (ia", " — ", " - "]:
		var i := s.find(sep)
		if i > 0:
			s = s.substr(0, i).strip_edges()
			break
	s = s + activity
	if s.length() > 22:
		s = s.substr(0, 20) + "…"
	return s

static func toggle_nameplates() -> void:
	show_nameplates = not show_nameplates

func set_sprite_texture(tex: Texture2D, tint: Color = Color.WHITE) -> void:
	if not is_inside_tree():
		_pending_texture = tex
		return
	_apply_sprite_texture(tex, tint)

func _ready() -> void:
	_idle_phase = float(object_id % 997) * 0.017
	_rebind_anchor()
	set_process(_wants_ambient())
	if _pending_texture:
		_apply_sprite_texture(_pending_texture, Color.WHITE)
		_pending_texture = null

func _rebind_anchor() -> void:
	_anchor.clear()
	_use_visual_override = false
	if kind != "npc":
		return
	if entity_key == "" and label_text == "":
		return
	_anchor = _NpcAnchorResolver.resolve(entity_key, _label_raw if _label_raw != "" else label_text)
	if _anchor.is_empty():
		return
	_use_visual_override = bool(_anchor.get("apply_visual_override", false))
	_visual_home = Vector3(
		float(_anchor.get("_home_x", core3_pos.x)),
		core3_pos.y,
		float(_anchor.get("_home_z", core3_pos.z))
	)
	var seed_i: int = int(_anchor.get("_seed", object_id))
	_idle_phase = float(seed_i % 997) * 0.017
	set_process(true)

func _wants_ambient() -> bool:
	return kind == "npc" or kind == "player" or not _anchor.is_empty()

func _process(delta: float) -> void:
	if kind == "beast" and combat_goal == "telegraph":
		queue_redraw()
		# Pas de patrol ambient — juste le pulse telegraph.
	var moved := false
	if _smooth_enabled:
		var prev := core3_pos
		var aim := _smooth_target + _smooth_vel * SMOOTH_EXTRAP_S
		var t := 1.0 - exp(-SMOOTH_RATE * maxf(delta, 1e-5))
		core3_pos = core3_pos.lerp(aim, clampf(t, 0.0, 1.0))
		height_offset = _Projection3D2D.height_offset(core3_pos.y)
		if not _use_visual_override:
			_visual_home = Vector3(core3_pos.x, core3_pos.y, core3_pos.z)
		update_facing_from_move(prev, core3_pos)
		if core3_pos.distance_squared_to(_smooth_target) < 0.04:
			core3_pos = _smooth_target
			_smooth_vel = Vector3.ZERO
			_smooth_enabled = false
		moved = true
	if _wants_ambient():
		var prev_patrol := _patrol_offset_m()
		_idle_phase += delta
		_refresh_screen_pos()
		var cur_patrol := _patrol_offset_m()
		if kind == "npc":
			var vel := cur_patrol - prev_patrol
			if vel.length_squared() > 1.0e-8:
				set_facing_from_direction(Vector3(vel.x, 0.0, vel.z))
				moved = true
		_last_patrol_offset = cur_patrol
		moved = true
	else:
		_refresh_screen_pos()
		if not _smooth_enabled and not (kind == "beast" and combat_goal == "telegraph"):
			set_process(false)
	_update_sprite_offset()
	_update_caravan_lantern_tick()
	# Évite redraw 60 Hz × N entités si rien n'a bougé à l'écran.
	if moved or _last_draw_pos == Vector2.INF or position.distance_squared_to(_last_draw_pos) > 0.25:
		_last_draw_pos = position
		queue_redraw()

func _refresh_screen_pos() -> void:
	var base := _visual_home if _use_visual_override else core3_pos
	var world := base + _patrol_offset_m()
	var bob_y := _bob_offset_px()
	position = _Projection3D2D.to_screen(world) + _display_jitter + Vector2(0.0, bob_y)

func _bob_offset_px() -> float:
	if kind == "player":
		if _smooth_vel.length_squared() > 0.05:
			return sin(_idle_phase * 12.0) * 1.5
		return 0.0
	if not _anchor.has("_bob") or not (_anchor["_bob"] is Dictionary):
		return 0.0
	var bob: Dictionary = _anchor["_bob"]
	if bob.get("enabled", false) != true:
		return 0.0
	var amp := float(bob.get("amplitude_px", 0.8))
	var period := maxf(float(bob.get("period_s", 2.4)), 0.2)
	return sin(_idle_phase * (TAU / period)) * amp

func _patrol_offset_m() -> Vector3:
	# Joueur humain contrôlé : pas de patrol
	if kind == "player" and entity_key == "player:human":
		return Vector3.ZERO
	var pat: Dictionary = {}
	if _anchor.has("_patrol") and (_anchor["_patrol"] is Dictionary):
		pat = _anchor["_patrol"]
	else:
		return Vector3.ZERO
	if pat.get("enabled", true) == false:
		return Vector3.ZERO
	var mode := str(pat.get("mode", "orbit"))
	var seed_i: int = int(_anchor.get("_seed", object_id)) if not _anchor.is_empty() else object_id
	var theta0 := float(seed_i % 360) * (PI / 180.0)
	if mode == "waypoints":
		var wps: Variant = pat.get("waypoints_relative", [])
		if not wps is Array or (wps as Array).is_empty():
			return Vector3.ZERO
		var arr: Array = wps
		var speed := float(pat.get("speed_m_s", 0.4))
		var pause := float(pat.get("pause_at_waypoint_s", 1.2))
		var seg_t := 3.0 / maxf(speed, 0.05) + pause
		var total := seg_t * float(arr.size())
		var t := fposmod(_idle_phase, total)
		var idx := int(t / seg_t) % arr.size()
		var local_t := t - float(idx) * seg_t
		var a: Dictionary = arr[idx] if arr[idx] is Dictionary else {}
		var b: Dictionary = arr[(idx + 1) % arr.size()] if arr[(idx + 1) % arr.size()] is Dictionary else a
		var blend := clampf(local_t / maxf(seg_t - pause, 0.01), 0.0, 1.0)
		var ax := float(a.get("x", 0.0))
		var az := float(a.get("z", 0.0))
		var bx := float(b.get("x", 0.0))
		var bz := float(b.get("z", 0.0))
		return Vector3(lerpf(ax, bx, blend), 0.0, lerpf(az, bz, blend))
	# orbit
	var radius_m := minf(float(pat.get("radius_m", 4.0)), 15.0)
	var speed := float(pat.get("speed_m_s", 0.55))
	var omega := speed / maxf(radius_m, 0.5)
	var theta := theta0 + _idle_phase * omega
	return Vector3(cos(theta) * radius_m, 0.0, sin(theta) * radius_m)

func _sprite_node() -> Sprite2D:
	return get_node_or_null("Sprite2D") as Sprite2D

func _apply_sprite_texture(tex: Texture2D, tint: Color = Color.WHITE) -> void:
	var sprite := _sprite_node()
	if sprite == null:
		_pending_texture = tex
		return
	if tex == null:
		_use_sprite = false
		sprite.texture = null
		sprite.visible = false
		queue_redraw()
		return
	if _MapTextureLoader.debug_triangle_markers_enabled() and (kind == "player" or kind == "npc"):
		_use_sprite = false
		sprite.texture = null
		sprite.visible = false
		queue_redraw()
		return
	_use_sprite = true
	sprite.texture = tex
	sprite.modulate = tint
	sprite.visible = true
	var target: float = float(_SpriteRegistry.display_px())
	var mul: float = float(_SpriteRegistry.resolve_scale_multiplier(_SpriteRegistry.last_sprite_key()))
	var w := float(tex.get_width())
	var h := float(tex.get_height())
	var dim := maxf(w, h)
	if dim > 0.0:
		var s := (target / dim) * mul
		sprite.scale = Vector2(s, s)
	_update_sprite_offset()
	queue_redraw()

func _update_sprite_offset() -> void:
	var sprite := _sprite_node()
	if sprite:
		sprite.position.y = height_offset
		if _smooth_vel.x < -0.1:
			sprite.flip_h = true
		elif _smooth_vel.x > 0.1:
			sprite.flip_h = false
		elif absf(facing_angle) > 0.01:
			var sin_a := sin(facing_angle)
			if sin_a < -0.2:
				sprite.flip_h = true
			elif sin_a > 0.2:
				sprite.flip_h = false

func is_caravan_member() -> bool:
	if entity_key.begins_with("npc:caravan_"):
		return true
	var ek := entity_key.to_lower()
	if "caravan" in ek:
		return true
	var lbl := label_text.to_lower()
	return "caravane" in lbl or "caravanier" in lbl or "nomade" in lbl

static func _get_or_create_caravan_light_texture() -> Texture2D:
	if _shared_caravan_light_tex != null:
		return _shared_caravan_light_tex
	var radius_px := 96
	var img := Image.create(radius_px * 2, radius_px * 2, false, Image.FORMAT_RGBA8)
	var center := Vector2(radius_px, radius_px)
	var max_r := float(radius_px)
	for y in range(radius_px * 2):
		for x in range(radius_px * 2):
			var dist := center.distance_to(Vector2(x, y))
			if dist >= max_r:
				img.set_pixel(x, y, Color(1, 1, 1, 0))
			else:
				var t := 1.0 - (dist / max_r)
				var alpha := t * t * (3.0 - 2.0 * t)
				img.set_pixel(x, y, Color(1, 1, 1, alpha))
	_shared_caravan_light_tex = ImageTexture.create_from_image(img)
	return _shared_caravan_light_tex

func _update_caravan_lantern_tick() -> void:
	if not is_caravan_member():
		if _caravan_lantern_light != null and _caravan_lantern_light.visible:
			_caravan_lantern_light.visible = false
		return
	if _caravan_lantern_light == null:
		_caravan_lantern_light = PointLight2D.new()
		_caravan_lantern_light.name = "CaravanLanternLight"
		_caravan_lantern_light.texture = _get_or_create_caravan_light_texture()
		_caravan_lantern_light.texture_scale = 2.0
		_caravan_lantern_light.color = Color(1.0, 0.76, 0.38) # Ambre nomade chaleureux
		_caravan_lantern_light.energy = 0.95
		add_child(_caravan_lantern_light)
	if _caravan_lantern_light:
		_caravan_lantern_light.visible = true
		var t := Time.get_ticks_msec() * 0.0035 + float(object_id * 2.2)
		_caravan_lantern_light.energy = 0.86 + 0.14 * sin(t * 1.8) * cos(t * 2.4)

func _draw() -> void:
	if kind != "player" and _is_clutter_visual():
		return
	var draw_pos := Vector2(0.0, height_offset)
	var token_px: float = float(_SpriteRegistry.display_px())
	var token_r: float = token_px * 0.38
	var tri_style: bool = _MapTextureLoader.debug_triangle_markers_enabled()

	if _use_sprite and not tri_style:
		draw_colored_polygon(
			_ellipse_points(draw_pos + Vector2(0, token_r * 0.55), token_r * 1.05, token_r * 0.32, 16),
			Color(0, 0, 0, 0.22)
		)
		if kind == "player":
			draw_arc(draw_pos, token_r * 1.05, 0.0, TAU, 32, color.lightened(0.2), 1.8, true)
	elif tri_style and (kind == "player" or kind == "npc"):
		_draw_marker_triangle(draw_pos, color, kind == "player")
		if _selected:
			draw_arc(draw_pos, 13.0, 0.0, TAU, 32, Color(0.24, 0.90, 0.98, 0.98), 2.0, true)
			draw_arc(draw_pos, 16.5, 0.0, TAU, 32, Color(0.98, 0.84, 0.32, 0.85), 1.2, true)
	elif kind == "player":
		draw_circle(draw_pos + Vector2(1, 1), radius, Color(0, 0, 0, 0.3))
		draw_circle(draw_pos, radius, color)
		draw_arc(draw_pos, radius, 0.0, TAU, 20, color.lightened(0.35), 1.2, true)
	elif kind == "npc":
		draw_circle(draw_pos + Vector2(0.5, 0.5), 3.5, Color(0, 0, 0, 0.25))
		draw_circle(draw_pos, 3.0, color.darkened(0.15))
	elif kind == "creature_lair":
		var lair_col := Color(0.55, 0.42, 0.28) # Terre ocre
		if "beetle" in entity_key or "scarab" in entity_key:
			lair_col = Color(0.25, 0.22, 0.28) # Obsidienne sombre
		draw_circle(draw_pos + Vector2(2, 2), 14.0, Color(0, 0, 0, 0.35))
		draw_circle(draw_pos, 13.0, lair_col)
		draw_arc(draw_pos, 13.0, 0.0, TAU, 24, lair_col.lightened(0.25), 2.0, true)
		# Cratère central
		draw_circle(draw_pos, 5.0, Color(0.12, 0.08, 0.05))
		# Jauge de vie du nid
		if max_hp > 0:
			var ratio: float = clampf(float(current_hp) / float(max_hp), 0.0, 1.0)
			var bar_w := 24.0
			draw_rect(Rect2(draw_pos.x - bar_w * 0.5, draw_pos.y - 18.0, bar_w, 3.0), Color(0.1, 0.1, 0.1, 0.8))
			draw_rect(Rect2(draw_pos.x - bar_w * 0.5, draw_pos.y - 18.0, bar_w * ratio, 3.0), Color(0.2, 0.85, 0.3, 0.9))
	elif kind == "beast":
		var beast_col := color
		if combat_goal == "telegraph":
			beast_col = Color(1.0, 0.82, 0.2, 1.0)
		elif combat_goal == "aggro":
			beast_col = Color(0.95, 0.25, 0.18, 1.0)
		draw_circle(draw_pos + Vector2(1, 1), radius * 1.15, Color(0, 0, 0, 0.28))
		draw_circle(draw_pos, radius * (1.25 if is_boss_beast else 1.0), beast_col)
		if combat_goal == "telegraph":
			var pulse := 0.55 + 0.35 * sin(Time.get_ticks_msec() * 0.012)
			draw_arc(draw_pos, radius * 2.2, 0.0, TAU, 28, Color(1.0, 0.85, 0.25, pulse), 2.0, true)
		elif combat_goal == "aggro":
			draw_arc(draw_pos, radius * 1.8, 0.0, TAU, 24, Color(0.95, 0.3, 0.2, 0.75), 1.6, true)

	# Affichage de Monture / Véhicule au sol sous le joueur
	if is_mounted and kind == "player":
		draw_arc(draw_pos, token_r * 1.4, 0.0, TAU, 24, Color(0.3, 0.85, 0.95, 0.8), 2.2, true)

	# Insigne de Faction GCW SWG Pre-CU
	if faction == "imperial":
		draw_circle(draw_pos + Vector2(token_r * 0.7, -token_r * 0.7), 3.5, Color(0.85, 0.15, 0.15, 0.95)) # Badge Impérial rouge
	elif faction == "rebel":
		draw_circle(draw_pos + Vector2(token_r * 0.7, -token_r * 0.7), 3.5, Color(0.95, 0.6, 0.15, 0.95)) # Badge Rebelle orange

	# Lame de Sabre Laser Jedi 2D (Plasma émissif & Halo de lumière)
	if is_lightsaber_active and kind == "player":
		var blade_dir := Vector2(sin(facing_angle), cos(facing_angle))
		var blade_start := draw_pos + blade_dir * (token_r * 0.6)
		var blade_end := draw_pos + blade_dir * (token_r * 2.4)
		# Halo lumineux au sol
		draw_circle(draw_pos, token_r * 1.8, Color(lightsaber_color.r, lightsaber_color.g, lightsaber_color.b, 0.12))
		# Halo externe émissif
		draw_line(blade_start, blade_end, lightsaber_color.lightened(0.3), 4.5, true)
		# Cœur de plasma blanc intense
		draw_line(blade_start, blade_end, Color.WHITE, 2.0, true)
		draw_circle(blade_start, 2.5, lightsaber_color)

	# Droïde Astromécano R2 / MSE compagnon 2D
	if kind == "droid" or "r2" in entity_key.to_lower():
		draw_colored_polygon(_ellipse_points(draw_pos + Vector2(2, 4), 8.0, 3.5, 12), Color(0, 0, 0, 0.28))
		draw_circle(draw_pos, 7.0, Color(0.9, 0.92, 0.95)) # Corps blanc
		draw_arc(draw_pos, 7.0, -PI, 0.0, 16, Color(0.1, 0.35, 0.85), 3.0, true) # Dôme bleu
		draw_circle(draw_pos + Vector2(0, -3), 1.5, Color(1.0, 0.1, 0.1)) # Œil rouge

	# Sonde Impériale Arakyd MK-IV 2D
	if "arakyd" in entity_key.to_lower() or "probe" in entity_key.to_lower():
		draw_colored_polygon(_ellipse_points(draw_pos + Vector2(2, 8), 9.0, 4.0, 12), Color(0, 0, 0, 0.22))
		draw_circle(draw_pos, 8.0, Color(0.15, 0.15, 0.18))
		draw_circle(draw_pos, 3.0, Color(1.0, 0.1, 0.1)) # Capteur rouge
		var p_wave := 0.4 + 0.3 * sin(Time.get_ticks_msec() * 0.008)
		draw_arc(draw_pos, 16.0, 0.0, TAU, 20, Color(1.0, 0.2, 0.2, p_wave), 1.5, true)

	# Terminaux Interactifs SWG Pre-CU (Bounty, Clonage, Mairie, Bio, Galaxie)
	if kind == "terminal" or entity_key.begins_with("terminal:"):
		var term_color := Color(0.2, 0.85, 1.0) # Cyan par défaut
		if "bounty" in entity_key: term_color = Color(1.0, 0.25, 0.2) # Rouge chasseur
		elif "insurance" in entity_key: term_color = Color(0.2, 0.9, 0.5) # Vert clonage
		elif "cityhall" in entity_key: term_color = Color(1.0, 0.85, 0.3) # Or municipal
		elif "bio" in entity_key: term_color = Color(0.3, 1.0, 0.4) # Vert biochimique
		elif "planets" in entity_key: term_color = Color(0.7, 0.5, 1.0) # Violet galactique

		# Halo de lumière ambiante au sol style Canvas of Kings
		var t_glow := 0.6 + 0.4 * sin(Time.get_ticks_msec() * 0.005)
		draw_circle(draw_pos, 22.0, Color(term_color.r, term_color.g, term_color.b, 0.08 * t_glow))
		# Ombre de socle
		draw_colored_polygon(_ellipse_points(draw_pos + Vector2(3, 3), 8.5, 4.5, 12), Color(0, 0, 0, 0.35))
		# Piédestal hexagonal et écran holo
		draw_circle(draw_pos, 6.5, Color(0.2, 0.22, 0.25))
		draw_circle(draw_pos, 4.5, term_color)
		draw_arc(draw_pos, 9.5, 0.0, TAU, 16, Color(term_color.r, term_color.g, term_color.b, t_glow), 1.5, true)

	# Caravanes Nomades de Scrapaltai (Lanterne de convoi & Bâtis de transport)
	if is_caravan_member():
		var l_offset := Vector2(token_r * 0.72, token_r * 0.15 + _bob_offset_px() * 0.5)
		var l_pos := draw_pos + l_offset
		# Lueur d'ambiance projetée au sol style Canvas of Kings
		var c_flicker := 0.75 + 0.25 * sin(Time.get_ticks_msec() * 0.007)
		draw_circle(l_pos, 20.0, Color(1.0, 0.76, 0.35, 0.12 * c_flicker))
		# Ombre de la lanterne
		draw_colored_polygon(_ellipse_points(l_pos + Vector2(1, 4), 3.5, 2.0, 8), Color(0, 0, 0, 0.25))
		# Corps en cuivre / laiton
		draw_rect(Rect2(l_pos.x - 2.5, l_pos.y - 4.0, 5.0, 6.0), Color(0.38, 0.26, 0.16))
		# Flamme / verre incandescent
		draw_rect(Rect2(l_pos.x - 1.5, l_pos.y - 3.0, 3.0, 4.0), Color(1.0, 0.88, 0.42, 0.95))
		# Anse supérieure de suspension
		draw_arc(l_pos + Vector2(0, -4.0), 2.2, -PI, 0.0, 8, Color(0.22, 0.16, 0.10), 1.2, true)
		# Bête de bât de convoi : sacoches et coffres de caravane des deux côtés
		if "beast" in entity_key.to_lower():
			draw_rect(Rect2(draw_pos.x - token_r * 0.85, draw_pos.y - 4.0, 4.5, 8.0), Color(0.42, 0.32, 0.20)) # Bât gauche
			draw_rect(Rect2(draw_pos.x + token_r * 0.55, draw_pos.y - 4.0, 4.5, 8.0), Color(0.42, 0.32, 0.20)) # Bât droit

	# Chasseur Incom T-65B X-Wing au sol (Starport)
	if "ship:" in entity_key or "xwing" in entity_key:
		# Ombre portée des 4 ailes sur le tarmac
		var sh_off := Vector2(-5, 6)
		draw_line(draw_pos + sh_off + Vector2(-16, -8), draw_pos + sh_off + Vector2(16, 8), Color(0, 0, 0, 0.25), 3.5)
		draw_line(draw_pos + sh_off + Vector2(-16, 8), draw_pos + sh_off + Vector2(16, -8), Color(0, 0, 0, 0.25), 3.5)
		# Fuselage
		draw_rect(Rect2(draw_pos.x - 3, draw_pos.y - 14, 6, 28), Color(0.85, 0.85, 0.88))
		# Cockpit
		draw_rect(Rect2(draw_pos.x - 2, draw_pos.y - 4, 4, 8), Color(0.2, 0.7, 1.0))
		# 4 Ailes en X déployées
		draw_line(draw_pos + Vector2(-16, -8), draw_pos + Vector2(16, 8), Color(0.8, 0.82, 0.85), 2.5)
		draw_line(draw_pos + Vector2(-16, 8), draw_pos + Vector2(16, -8), Color(0.8, 0.82, 0.85), 2.5)
		# Canons lasers rouges aux bouts
		draw_circle(draw_pos + Vector2(-16, -8), 2.0, Color(1.0, 0.2, 0.2))
		draw_circle(draw_pos + Vector2(16, -8), 2.0, Color(1.0, 0.2, 0.2))

	# Sas Pressurisé de la Corvette Corellienne (Donjon)
	if "dungeon:" in entity_key or "corvette" in entity_key:
		draw_rect(Rect2(draw_pos.x - 10, draw_pos.y - 6, 20, 12), Color(0.65, 0.15, 0.15))
		draw_rect(Rect2(draw_pos.x - 7, draw_pos.y - 4, 14, 8), Color(0.15, 0.18, 0.22))
		var a_pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() * 0.01)
		draw_circle(draw_pos + Vector2(0, -7), 3.0, Color(1.0, 0.1, 0.1, a_pulse)) # Gyrophare d'alerte
	if abs(height_offset) > 1.0 and abs(height_offset) <= 48.0:
		draw_line(
			Vector2(0.0, 0.0),
			draw_pos,
			Color(color.r, color.g, color.b, 0.45),
			1.0
		)
	var should_draw_nameplate := false
	if label_text != "":
		var is_companion := ("nix" in label_text.to_lower() or "lia" in label_text.to_lower())
		var is_in_combat := (kind == "beast" and combat_goal != "idle" and combat_goal != "")
		var vp := get_viewport()
		var cam := vp.get_camera_2d() if vp else null
		var z_val: float = cam.zoom.x if cam else 1.0
		
		if _selected or kind == "player" or is_companion or is_in_combat:
			should_draw_nameplate = true
		elif (show_nameplates or force_nameplate) and z_val >= 1.25:
			should_draw_nameplate = true

	if should_draw_nameplate:
		var label_y: float = -token_px * 0.52 if _use_sprite else -radius - 6.0
		var shown := label_text
		var col := Color(0.68, 0.96, 1.0, 0.98) if kind == "player" else Color(0.96, 0.92, 0.78, 0.95)
		if kind == "beast" and combat_goal == "telegraph":
			shown = "%s !" % label_text
			col = Color(1.0, 0.9, 0.35, 0.98)
		elif kind == "beast" and combat_goal == "aggro":
			col = Color(1.0, 0.45, 0.35, 0.98)
		# Barre rouge au-dessus de la tête STRICTEMENT réservée aux bêtes agressives en combat (le joueur et les cibles ont le HUD HAM SWG en haut d'écran)
		if kind == "beast" and (combat_goal == "aggro" or combat_goal == "attack" or combat_goal == "telegraph"):
			var bw := 24.0
			var bh := 3.0
			var bx := draw_pos.x - bw * 0.5
			var by := draw_pos.y + label_y - 8.0
			draw_rect(Rect2(bx - 1, by - 1, bw + 2, bh + 2), Color(0.01, 0.06, 0.08, 0.92), true)
			draw_rect(Rect2(bx, by, bw, bh), Color(0.88, 0.16, 0.20, 0.96), true)
		var font := ThemeDB.fallback_font
		if font:
			var fsize := 9
			var str_w := font.get_string_size(shown, HORIZONTAL_ALIGNMENT_CENTER, -1, fsize).x
			var t_pos := draw_pos + Vector2(-str_w * 0.5, label_y)
			# Cartouche de lisibilité SWG discret sous le nom
			var pad_x := 4.0
			var pad_y := 1.0
			var bg_rect := Rect2(t_pos.x - pad_x, t_pos.y - fsize + pad_y, str_w + pad_x * 2.0, fsize + pad_y * 2.0)
			draw_rect(bg_rect, Color(0.05, 0.04, 0.03, 0.75), true)
			draw_string(font, t_pos + Vector2(1, 1), shown, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, Color(0.02, 0.02, 0.02, 0.95))
			draw_string(font, t_pos, shown, HORIZONTAL_ALIGNMENT_LEFT, -1, fsize, col)

func _draw_marker_triangle(center: Vector2, col: Color, is_player: bool) -> void:
	var tip := Vector2(0.0, -5.5)
	var p1 := Vector2(-4.0, 3.2)
	var p2 := Vector2(4.0, 3.2)
	tip = tip.rotated(facing_angle) + center
	p1 = p1.rotated(facing_angle) + center
	p2 = p2.rotated(facing_angle) + center
	var fill := col if is_player else Color(1.0, 1.0, 1.0, 0.92)
	draw_colored_polygon(PackedVector2Array([tip, p1, p2]), fill)
	draw_polyline(PackedVector2Array([tip, p1, p2, tip]), col.darkened(0.2), 1.2, true)

func _ellipse_points(center: Vector2, rx: float, ry: float, segments: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in range(segments):
		var a := (float(i) / float(segments)) * TAU
		pts.append(center + Vector2(cos(a) * rx, sin(a) * ry))
	return pts

func _is_clutter_visual() -> bool:
	var raw := _label_raw if _label_raw != "" else label_text
	return _HubFocus.is_clutter(kind, raw, entity_key)


func is_interactable() -> bool:
	return kind == "npc" or kind == "terminal" or kind == "droid" or entity_key.begins_with("terminal:") or entity_key.begins_with("ship:") or entity_key.begins_with("dungeon:") or entity_key.begins_with("droid:")


func is_local_player(local_id: int) -> bool:
	return kind == "player" and object_id == local_id and object_id != 0

func screen_anchor() -> Vector2:
	# Centre visuel du marqueur (triangle / sprite), repère monde 2D + caméra.
	return to_global(Vector2(0.0, height_offset))


func hit_test_screen(mouse_pos: Vector2) -> bool:
	if not visible:
		return false
	if kind != "npc" and kind != "player" and kind != "beast" and kind != "terminal" and kind != "droid" and not entity_key.begins_with("terminal:") and not entity_key.begins_with("ship:") and not entity_key.begins_with("dungeon:"):
		return false
	var token_px: float = float(_SpriteRegistry.display_px())
	# Hitbox précise ajustée sur la figurine (évite d'intercepter les clics au sol pour marcher)
	var radius_px := clampf(token_px * 0.35, 8.0, 16.0)
	return screen_anchor().distance_squared_to(mouse_pos) <= radius_px * radius_px
