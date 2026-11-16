# canvas_of_kings_atmosphere.gd — Moteur d'Ambiance Visuelle 2D Style "Canvas of Kings"
# Apporte l'éclairage 2D dynamique, le cycle jour/nuit avec CanvasModulate,
# les ombres portées solaires, les halos de lanternes 2D et les poussières atmosphériques.
extends Node2D
class_name CanvasOfKingsAtmosphere

const Projection3D2D = preload("res://scripts/projection.gd")

var _modulate: CanvasModulate = null
var _light_texture: Texture2D = null
var _sun_angle: float = 0.0
var _sun_shadow_offset: Vector2 = Vector2(-6.0, 8.0)
var _sun_shadow_alpha: float = 0.28
var _game_hour: float = 12.0
var _is_night: bool = false
var _lanterns_active: bool = false
var _particles: CPUParticles2D = null

# Liste des positions mondes 2D des lanternes de Lost Heaven
var _lantern_screen_positions: Array[Vector2] = []
var _lights_nodes: Array[PointLight2D] = []

func _init() -> void:
	name = "CanvasOfKingsAtmosphere"
	z_index = 50 # Au-dessus des sols et bâtiments mais sous le HUD
	_ensure_setup()

func _ready() -> void:
	_ensure_setup()
	set_process(true)

func _ensure_setup() -> void:
	if _lights_nodes.size() > 0:
		return
	_light_texture = _generate_soft_light_texture(128)
	_setup_canvas_modulate()
	_setup_atmospheric_particles()
	_setup_hub_lights()

func _process(delta: float) -> void:
	# Progression continue du cycle Jour/Nuit Est <-> Ouest (Solar Terminator)
	var vp := get_viewport()
	var cam := vp.get_camera_2d() if vp else null
	var world_x: float = (cam.global_position.x / Projection3D2D.SCALE) if cam else 0.0
	# Décalage de longitude : 64 000 m = 24 heures (1 heure = ~2667 m)
	var local_hour: float = fposmod(_game_hour + (world_x / 64000.0) * 24.0, 24.0)
	_apply_lighting_for_hour(local_hour)

	# Scintillement subtil et organique des lanternes la nuit
	if _lanterns_active:
		var time_ms := Time.get_ticks_msec() * 0.003
		for i in range(_lights_nodes.size()):
			var l: PointLight2D = _lights_nodes[i]
			if l and l.visible:
				var flicker := 0.88 + 0.12 * sin(time_ms * 1.7 + float(i * 1.3)) * cos(time_ms * 2.3 + float(i))
				l.energy = flicker

	# Déplacement fluide des particules atmosphériques centré sur la caméra
	if _particles:
		if cam:
			_particles.global_position = cam.global_position

func _generate_soft_light_texture(radius_px: int = 128) -> ImageTexture:
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
				var alpha := t * t * (3.0 - 2.0 * t) # Lissage cubique doux hermite
				img.set_pixel(x, y, Color(1, 1, 1, alpha))
	return ImageTexture.create_from_image(img)

func _setup_canvas_modulate() -> void:
	_modulate = CanvasModulate.new()
	_modulate.name = "AtmosphereModulate"
	_modulate.color = Color(1.0, 0.98, 0.94) # Plein jour par défaut
	add_child(_modulate)

func _setup_atmospheric_particles() -> void:
	# Particules de poussières désertiques / brume dorée flottante style Canvas of Kings
	_particles = CPUParticles2D.new()
	_particles.name = "AtmosphericMotes"
	_particles.amount = 45
	_particles.lifetime = 6.0
	_particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_particles.emission_rect_extents = Vector2(800, 500)
	_particles.gravity = Vector2(8.0, -3.0) # Dérive légère par le vent
	_particles.initial_velocity_min = 5.0
	_particles.initial_velocity_max = 15.0
	_particles.scale_amount_min = 1.5
	_particles.scale_amount_max = 3.5
	_particles.color = Color(1.0, 0.90, 0.65, 0.35)
	add_child(_particles)

func _setup_hub_lights() -> void:
	# 1. Centre-ville de Lost Heaven (Plaza, commerces et bâtiments officiels)
	var hub_center := Projection3D2D.to_screen(Vector3(4749.0, 0.0, -737.0))
	_lantern_screen_positions = [
		hub_center,                          # Rosace Plaza centrale
		hub_center + Vector2(125.0, 0.0),    # Cantina La Perle
		hub_center + Vector2(263.0, 0.0),    # Atelier Mécatronique
		hub_center + Vector2(-117.0, 0.0),   # Banque
		hub_center + Vector2(-215.0, 0.0),   # Starport Terminal
		hub_center + Vector2(0.0, -81.0),    # Auberge
		hub_center + Vector2(0.0, 84.0),     # Grand Marché
		hub_center + Vector2(-134.5, -77.0), # Clinique
		hub_center + Vector2(135.5, -76.0),  # Dojo / Entraînement
		hub_center + Vector2(-134.5, 79.0),  # Mairie
		hub_center + Vector2(135.5, 83.0),   # Missions
	]

	# 2. Entrées de Lost Heaven (Lumières de chaque côté des arches et portails)
	# Porte Ouest — vers Zalem (x = 3688.9, z = -675.9)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(3688.9, 0.0, -662.0))) # Pilier Nord
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(3688.9, 0.0, -690.0))) # Pilier Sud
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(3665.0, 0.0, -676.0))) # Poste avancée route

	# Porte Est — vers le Désert et l'Anneau (x = 5813.6, z = -982.5)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5813.6, 0.0, -968.0))) # Pilier Nord
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5813.6, 0.0, -998.0))) # Pilier Sud
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5838.0, 0.0, -982.0))) # Balise départ convoi

	# Porte Sud — vers la Piste des Caravanes et le Shuttleport (x = 4749.0, z = -450.0)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4726.0, 0.0, -450.0))) # Côté Ouest
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4772.0, 0.0, -450.0))) # Côté Est

	# Porte Nord — sortie palissade Lost Heaven (x = 4749.0, z = -408.0)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4726.0, 0.0, -408.0))) # Côté Ouest
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4772.0, 0.0, -408.0))) # Côté Est

	# 3. Camp Avancé de Zalem (Poste frontière et garnison Ouest)
	# Checkpoint & barrières d'accès Ouest de Zalem (de chaque côté)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1460.0, 0.0, -535.0))) # Pilier Nord
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1460.0, 0.0, -565.0))) # Pilier Sud
	# Bâtiments de l'avant-poste
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1200.0, 0.0, -520.0))) # Commandement Capitaine Vael
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1060.0, 0.0, -440.0))) # Atelier Soren Kray
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1340.0, 0.0, -440.0))) # Caserne Milice
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1200.0, 0.0, -320.0))) # Relais des convois & Inn
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-980.0, 0.0, -680.0)))  # Dépôt de ravitaillement
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(-1200.0, 0.0, -450.0))) # Place centrale Zalem

	# 4. Ksar Nomade (Village fortifié de l'Oasis et refuge caravanier)
	# Grande Arche Nord d'entrée du Ksar (de chaque côté)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4938.0, 0.0, -3470.0))) # Pilier Ouest
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4962.0, 0.0, -3470.0))) # Pilier Est
	# Arche Orientale d'entrée (de chaque côté)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5120.0, 0.0, -3588.0))) # Pilier Nord
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5120.0, 0.0, -3612.0))) # Pilier Sud
	# Oasis du Ksar (Lanternes de berge douces)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4995.0, 0.0, -3670.0))) # Berge Ouest
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5045.0, 0.0, -3670.0))) # Berge Est
	# Campement et tentes bédouines du Ksar
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4920.0, 0.0, -3760.0))) # Tente Ancien Nadir
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4820.0, 0.0, -3650.0))) # Tente Soins Miran Sael
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5120.0, 0.0, -3710.0))) # Tente Troc bédouine
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(4950.0, 0.0, -3800.0))) # Caravansérail nomade

	# 5. Halte et relais de la piste des Caravanes (Oasis d'Al-Khali à mi-chemin)
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5480.0, 0.0, -2450.0))) # Relais d'Al-Khali 1
	_lantern_screen_positions.append(Projection3D2D.to_screen(Vector3(5495.0, 0.0, -2465.0))) # Relais d'Al-Khali 2

	for l_pos in _lantern_screen_positions:
		var pl := PointLight2D.new()
		pl.texture = _light_texture
		pl.texture_scale = 1.8
		pl.color = Color(1.0, 0.78, 0.40) # Lueur ambrée chaleureuse
		pl.energy = 0.95
		pl.position = l_pos
		pl.visible = _lanterns_active
		add_child(pl)
		_lights_nodes.append(pl)

func set_world_clock(wc: Dictionary) -> void:
	_game_hour = float(wc.get("game_hour", 12.0))
	_is_night = bool(wc.get("is_night", false))
	_lanterns_active = bool(wc.get("night_lanterns_active", _is_night))

func _apply_lighting_for_hour(hour: float) -> void:
	# 1. Calcul de la teinte d'ambiance CanvasModulate selon l'heure locale
	var amb_col := _calculate_day_cycle_color(hour)
	if _modulate:
		_modulate.color = amb_col

	# 2. Activation des lanternes en pénombre et nuit locale
	var local_night: bool = (hour < 6.5 or hour > 19.0)
	for l in _lights_nodes:
		if l:
			l.visible = local_night

	# 3. Calcul du décalage d'ombre solaire dynamique (Canvas of Kings)
	var sun_t := (hour - 6.0) / 12.0 # 0.0 à l'aube, 0.5 à midi, 1.0 au crépuscule
	if sun_t >= 0.0 and sun_t <= 1.0:
		_sun_angle = lerpf(-2.4, -0.7, sun_t)
		var shadow_len := lerpf(18.0, 6.0, sin(sun_t * PI))
		_sun_shadow_offset = Vector2(cos(_sun_angle), sin(_sun_angle)) * shadow_len
		_sun_shadow_alpha = lerpf(0.20, 0.35, sin(sun_t * PI))
	else:
		_sun_shadow_offset = Vector2(-4.0, 4.0)
		_sun_shadow_alpha = 0.12

	# 4. Ajustement des particules selon l'ambiance locale
	if _particles:
		if local_night:
			_particles.color = Color(0.6, 0.8, 1.0, 0.25)
		else:
			_particles.color = Color(1.0, 0.88, 0.60, 0.38)

func get_sun_shadow_offset() -> Vector2:
	return _sun_shadow_offset

func get_sun_shadow_alpha() -> float:
	return _sun_shadow_alpha

func _calculate_day_cycle_color(hour: float) -> Color:
	# Cycle de 24h avec transitions harmonieuses de palette de couleurs
	if hour >= 6.0 and hour < 8.0:
		# Aube : Doré rosé doux
		var t := (hour - 6.0) / 2.0
		return Color(0.72, 0.62, 0.68).lerp(Color(1.0, 0.94, 0.86), t)
	elif hour >= 8.0 and hour < 17.0:
		# Plein jour : Éclat solaire chaud désertique
		return Color(1.0, 0.98, 0.95)
	elif hour >= 17.0 and hour < 19.5:
		# Crépuscule : Ambre incandescent & pourpre
		var t := (hour - 17.0) / 2.5
		return Color(1.0, 0.94, 0.86).lerp(Color(0.85, 0.60, 0.45), t)
	elif hour >= 19.5 and hour < 21.5:
		# Tombée de la nuit : Transition vers l'indigo
		var t := (hour - 19.5) / 2.0
		return Color(0.85, 0.60, 0.45).lerp(Color(0.28, 0.32, 0.48), t)
	else:
		# Nuit noire : Bleu nuit profond lisible (pas tout noir opaque)
		return Color(0.24, 0.28, 0.44)

