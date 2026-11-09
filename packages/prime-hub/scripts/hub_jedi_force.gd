extends RefCounted
class_name HubJediForce
## Système SWG Pre-CU : Force Sensitive, Voie du Jedi, Arbres d'Aurilia,
## Confection de Sabres Laser, Pouvoirs de Force & Visibilité Impériale.

const _HubPaths := preload("res://scripts/hub_paths.gd")

const FORCE_POOLS := {
	"initiate": {"max_force": 500, "regen_rate": 20.0},
	"padawan": {"max_force": 1000, "regen_rate": 35.0},
	"knight": {"max_force": 1750, "regen_rate": 50.0},
	"master": {"max_force": 2500, "regen_rate": 70.0}
}

const FORCE_POWERS := {
	"force_heal": {
		"label": "Guérison de Force (Force Heal)",
		"force_cost": 150,
		"heal_amount": 350,
		"cooldown_s": 3.0,
		"desc": "Canalise l'énergie vivante pour restaurer instantanément Santé et Action."
	},
	"force_speed": {
		"label": "Vélocité de Force (Force Speed)",
		"force_cost": 200,
		"speed_multiplier": 2.0,
		"duration_s": 15.0,
		"cooldown_s": 20.0,
		"desc": "Altère le flux temporel pour doubler la vitesse de sprint."
	},
	"mind_trick": {
		"label": "Suggestion Mentale (Mind Trick)",
		"force_cost": 220,
		"duration_s": 8.0,
		"cooldown_s": 12.0,
		"desc": "Sature le mental de la cible pour briser son hostilité et l'étourdir."
	},
	"force_lightning": {
		"label": "Éclairs de Force (Force Lightning)",
		"force_cost": 300,
		"damage": 280,
		"cooldown_s": 5.0,
		"desc": "Projette des arcs électriques dévastateurs ignorant une partie de l'armure."
	},
	"saber_block": {
		"label": "Parade au Sabre (Saber Block)",
		"force_cost": 50,
		"reflect_chance": 0.75,
		"duration_s": 10.0,
		"cooldown_s": 15.0,
		"desc": "Adopte la posture Soresu pour dévier et renvoyer les tirs de blaster ennemis."
	}
}

const CRYSTAL_TYPES := {
	"crystal_ilum_blue": {"color": "blue", "damage_bonus": 45, "force_cost_mod": -10, "label": "Cristal d'Ilum Azur"},
	"crystal_corusca_green": {"color": "green", "damage_bonus": 50, "force_cost_mod": -15, "label": "Gemme Corusca Émeraude"},
	"crystal_synth_red": {"color": "red", "damage_bonus": 75, "force_cost_mod": +10, "label": "Cristal Synthétique Sith"},
	"crystal_krayt_pearl": {"color": "purple", "damage_bonus": 120, "force_cost_mod": -25, "label": "Perle de Dragon Krayt Légendaire"}
}

var sim = null
var economy = null
var skills = null
var bounty_svc = null

# État Jedi des joueurs : player_name -> Dictionary
var jedi_state: Dictionary = {}


func setup(sim_svc = null, economy_svc = null, skills_svc = null, bounty_hunter_svc = null) -> void:
	sim = sim_svc
	economy = economy_svc
	skills = skills_svc
	bounty_svc = bounty_hunter_svc


func _ensure_player(player: String) -> Dictionary:
	var p := player.strip_edges()
	if not jedi_state.has(p):
		jedi_state[p] = {
			"player": p,
			"rank": "initiate", # initiate, padawan, knight, master
			"current_force": 500,
			"max_force": 500,
			"regen_rate": 20.0,
			"visibility": 0, # 0..100 (génère des bounties si > 30)
			"unlocked_fs_branches": [],
			"holocrons_consulted": 0,
			"active_buffs": {},
			"lightsaber": {
				"crafted": false,
				"hilt": "standard",
				"crystal": "crystal_ilum_blue",
				"blade_color": "blue",
				"min_damage": 180,
				"max_damage": 320
			},
			"last_update_ts": Time.get_unix_time_from_system()
		}
	return jedi_state[p]


func get_status(player: String) -> Dictionary:
	_update_force_pool(player)
	return _ensure_player(player).duplicate(true)


func _update_force_pool(player: String) -> void:
	var p: Dictionary = _ensure_player(player)
	var now := Time.get_unix_time_from_system()
	var dt: float = float(now - float(p.get("last_update_ts", now)))
	if dt > 0.0:
		var cur_f: float = float(p.get("current_force", 500))
		var max_f: float = float(p.get("max_force", 500))
		var rate: float = float(p.get("regen_rate", 20.0))
		p["current_force"] = minf(max_f, cur_f + rate * dt)
		p["last_update_ts"] = now


## Consultation d'un Holocron Jedi ou Sith
func consult_holocron(player: String, holocron_kind: String = "jedi") -> Dictionary:
	var p: Dictionary = _ensure_player(player)
	var count: int = int(p.get("holocrons_consulted", 0)) + 1
	p["holocrons_consulted"] = count

	var hints := [
		"L'Holocron vibre et révèle : « Maîtrise les arts martiaux du Bagarreur Teräs Käsi. »",
		"L'Holocron diffuse une lueur d'or : « Sonde les profondeurs géologiques comme Artisan. »",
		"Une mélodie résonne : « Dissipe la fatigue des guerriers comme Artiste de Cantina. »",
		"Un murmure froid résonne : « Développe l'art des soins et des stimpacks au Medcenter. »"
	]
	var hint_text: String = hints[(count - 1) % hints.size()]

	if count >= 4 and p["rank"] == "initiate":
		p["rank"] = "padawan"
		p["max_force"] = FORCE_POOLS["padawan"]["max_force"]
		p["regen_rate"] = FORCE_POOLS["padawan"]["regen_rate"]
		p["current_force"] = p["max_force"]
		p["unlocked_fs_branches"] = ["fs_reflexes_01", "fs_senses_01"]

	return {
		"ok": true,
		"player": player,
		"holocron_kind": holocron_kind,
		"consultation_count": count,
		"hint": hint_text,
		"new_rank": p["rank"],
		"max_force": p["max_force"]
	}


## Confection d'un Sabre Laser personnel
func craft_lightsaber(player: String, crystal_id: String = "crystal_ilum_blue", hilt_type: String = "curved") -> Dictionary:
	var p: Dictionary = _ensure_player(player)
	if not CRYSTAL_TYPES.has(crystal_id):
		return {"ok": false, "error": "unknown_crystal_type"}

	var c_data: Dictionary = CRYSTAL_TYPES[crystal_id]
	var base_min := 180 + int(c_data.get("damage_bonus", 0))
	var base_max := 320 + int(c_data.get("damage_bonus", 0)) * 2

	var saber := {
		"crafted": true,
		"hilt": hilt_type,
		"crystal": crystal_id,
		"crystal_label": str(c_data.get("label", "Cristal")),
		"blade_color": str(c_data.get("color", "blue")),
		"min_damage": base_min,
		"max_damage": base_max,
		"force_mod": int(c_data.get("force_cost_mod", 0)),
		"crafted_at": Time.get_unix_time_from_system()
	}
	p["lightsaber"] = saber

	# Émettre événement si sim connecté
	if sim != null and sim.has_method("_stream"):
		sim._stream("jedi.saber_crafted", "« Un bourdonnement d'énergie pure retentit : %s a forgé son sabre laser (%s) ! »" % [player, saber["crystal_label"]], player, "world", saber)

	return {
		"ok": true,
		"player": player,
		"lightsaber": saber.duplicate(true)
	}


## Déclenchement d'un Pouvoir de Force
func execute_force_power(player: String, power_id: String, target_entity: String = "") -> Dictionary:
	_update_force_pool(player)
	var p: Dictionary = _ensure_player(player)

	if not FORCE_POWERS.has(power_id):
		return {"ok": false, "error": "unknown_force_power"}

	var pow: Dictionary = FORCE_POWERS[power_id]
	var cost := int(pow.get("force_cost", 100))
	var cur_f := float(p.get("current_force", 0.0))

	if cur_f < cost:
		return {
			"ok": false,
			"error": "insufficient_force",
			"cost": cost,
			"available": int(cur_f)
		}

	# Déduction de Force
	p["current_force"] = cur_f - cost

	# Augmentation de la visibilité impériale (génération de prime si en public)
	var vis_gain := 15
	p["visibility"] = clampi(int(p.get("visibility", 0)) + vis_gain, 0, 100)

	var result := {
		"ok": true,
		"player": player,
		"power": power_id,
		"label": str(pow.get("label", power_id)),
		"remaining_force": int(p["current_force"]),
		"visibility": p["visibility"]
	}

	match power_id:
		"force_heal":
			var heal := int(pow.get("heal_amount", 350))
			result["heal_applied"] = heal
		"force_speed":
			var dur := float(pow.get("duration_s", 15.0))
			result["buff_speed"] = float(pow.get("speed_multiplier", 2.0))
			result["duration_s"] = dur
		"mind_trick":
			result["target_stunned"] = target_entity
			result["duration_s"] = float(pow.get("duration_s", 8.0))
		"force_lightning":
			var dmg := int(pow.get("damage", 280))
			result["damage_dealt"] = dmg
			result["target"] = target_entity
		"saber_block":
			result["active_block"] = true
			result["reflect_chance"] = float(pow.get("reflect_chance", 0.75))

	# Si la visibilité dépasse 30, générer automatiquement un avis de recherche (Bounty)
	if int(p.get("visibility", 0)) >= 30 and bounty_svc != null and bounty_svc.has_method("post_jedi_bounty"):
		var bounty_reward: int = int(p["visibility"]) * 100
		bounty_svc.post_jedi_bounty(player, bounty_reward, "Utilisation illégale de la Force détectée par les sondes impériales.")
		result["bounty_generated"] = bounty_reward

	return result


## Réinitialisation ou dissipation de la visibilité (Méditation discrète)
func meditate(player: String) -> Dictionary:
	_update_force_pool(player)
	var p: Dictionary = _ensure_player(player)
	p["current_force"] = p["max_force"]
	p["visibility"] = maxi(0, int(p.get("visibility", 0)) - 25)
	return {
		"ok": true,
		"player": player,
		"current_force": int(p["current_force"]),
		"visibility": p["visibility"]
	}
