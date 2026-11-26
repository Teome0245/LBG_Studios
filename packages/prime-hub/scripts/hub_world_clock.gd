extends RefCounted
class_name HubWorldClock
## Horloge circadienne et cycle jour/nuit pour Lost Heaven — Ticket 2.1 O2 Phase 3.
## Synchronise les phases d'éclairage, l'activation des lanternes et l'agressivité des bêtes.

const _HubPaths = preload("res://scripts/hub_paths.gd")

## Configuration temporelle : 90 minutes réelles = 24 heures en jeu (time_dilation = 16.0).
## 1 heure en jeu = 225 secondes réelles (3 min 45 s).
## Jour plein (10h jeu) = 37.5 min | Nuit (8h jeu) = 30 min | Aube/Crépuscule (6h jeu) = 22.5 min.
var time_dilation: float = 16.0
var _game_hour: float = 10.0 # 10:00 (Matin / Plein jour) par défaut
var total_game_hours: float = 10.0
var game_day: int = 1

var day_phase: String = "day" # "dawn", "day", "dusk", "night"
var is_night: bool = false
var night_lanterns_active: bool = false
var beast_aggro_mult: float = 1.0
var light_ambient: float = 1.0
var light_color: String = "#fff6d6"

var world_stream = null
var _on_announce: Callable = Callable()


func attach_world_stream(stream_svc) -> void:
	world_stream = stream_svc


func _stream(kind: String, text: String, actor: String = "", zone: String = "", detail: Dictionary = {}) -> void:
	if world_stream != null and world_stream.has_method("emit"):
		world_stream.emit(kind, text, actor, zone, detail)


func setup(start_hour: float = 10.0, dilation: float = 60.0, announce_cb: Callable = Callable()) -> void:
	time_dilation = maxf(1.0, dilation)
	_on_announce = announce_cb
	set_time(start_hour)


func set_time(hour: float) -> void:
	var old_phase := day_phase
	_game_hour = fposmod(hour, 24.0)
	_update_phase_state()
	if old_phase != day_phase and old_phase != "":
		_notify_phase_change(old_phase, day_phase)


func tick(dt: float) -> void:
	if dt <= 0.0:
		return
	var old_phase := day_phase
	var old_day := game_day
	var delta_hours := dt * time_dilation / 3600.0
	total_game_hours += delta_hours
	_game_hour = fposmod(_game_hour + delta_hours, 24.0)
	game_day = int(total_game_hours / 24.0) + 1
	_update_phase_state()
	if old_phase != day_phase:
		_notify_phase_change(old_phase, day_phase)
	if game_day > old_day:
		_stream("world.day_dawn", "Un nouveau jour se lève sur Scrapaltaï — Jour %d." % game_day, "Horloge Planétaire", "scrapaltai", {"game_day": game_day})


func _update_phase_state() -> void:
	if _game_hour >= 5.0 and _game_hour < 8.0:
		day_phase = "dawn"
		is_night = false
		# Lanternes actives au tout début de l'aube (jusqu'à 06h30)
		night_lanterns_active = (_game_hour < 6.5)
		beast_aggro_mult = 1.25
		light_ambient = lerpf(0.35, 0.90, (_game_hour - 5.0) / 3.0)
		light_color = "#ffaa5e"
	elif _game_hour >= 8.0 and _game_hour < 18.0:
		day_phase = "day"
		is_night = false
		night_lanterns_active = false
		beast_aggro_mult = 1.0
		light_ambient = 1.0
		light_color = "#fff6d6"
	elif _game_hour >= 18.0 and _game_hour < 21.0:
		day_phase = "dusk"
		is_night = (_game_hour >= 20.0)
		# Les lanternes s'allument dès 18h30 pour la pénombre
		night_lanterns_active = (_game_hour >= 18.5)
		beast_aggro_mult = 1.35
		light_ambient = lerpf(0.90, 0.35, (_game_hour - 18.0) / 3.0)
		light_color = "#e07a5f"
	else:
		day_phase = "night"
		is_night = true
		night_lanterns_active = true
		# Nuit profonde : les bêtes chassent avec férocité et portée accrue
		beast_aggro_mult = 1.60
		light_ambient = 0.25
		light_color = "#1d2d44"


func _notify_phase_change(old_phase: String, new_phase: String) -> void:
	var state := get_time_state()
	var label := get_phase_label()
	var msg := "Transition circadienne : %s (%s). Lanternes %s." % [
		label,
		get_time_string(),
		"allumées" if night_lanterns_active else "éteintes"
	]
	_stream("world.clock.phase", msg, "Horloge", "scrapaltai", state)

	if _on_announce.is_valid():
		match new_phase:
			"dusk":
				_on_announce.call(
					"Guet de Scrapaltai",
					910002,
					"Le soleil décline sur les dunes. Les lanternes du Cantina et du Dépôt s'allument.",
					"ia"
				)
			"night":
				_on_announce.call(
					"Guet de Scrapaltai",
					910002,
					"Nuit profonde sur Lost Heaven. Les hyènes du désert rôdent : restez sous les lanternes !",
					"ia"
				)
			"dawn":
				_on_announce.call(
					"Guet de Scrapaltai",
					910002,
					"L'aube se lève sur Scrapaltai. Les caravanes préparent leurs attelages.",
					"ia"
				)


func get_game_hour() -> float:
	return _game_hour


func get_day_phase() -> String:
	return day_phase


func get_time_string() -> String:
	var h := int(_game_hour)
	var m := int((_game_hour - float(h)) * 60.0)
	return "%02d:%02d" % [h, m]


func get_phase_label() -> String:
	match day_phase:
		"dawn":
			return "Aube"
		"day":
			return "Plein jour"
		"dusk":
			return "Crépuscule"
		"night":
			return "Nuit profonde"
		_:
			return "Plein jour"


func is_night_time() -> bool:
	return is_night


func are_lanterns_active() -> bool:
	return night_lanterns_active


func get_beast_aggro_mult() -> float:
	return beast_aggro_mult


func get_light_ambient() -> float:
	return light_ambient


func get_light_color() -> String:
	return light_color


func get_time_state() -> Dictionary:
	return {
		"game_day": game_day,
		"total_game_hours": snappedf(total_game_hours, 0.01),
		"game_hour": snappedf(_game_hour, 0.01),
		"time_string": get_time_string(),
		"day_phase": day_phase,
		"day_phase_label": get_phase_label(),
		"is_night": is_night,
		"night_lanterns_active": night_lanterns_active,
		"beast_aggro_mult": snappedf(beast_aggro_mult, 0.01),
		"light_ambient": snappedf(light_ambient, 0.01),
		"light_color": light_color,
		"time_dilation": time_dilation,
	}
