extends RefCounted
class_name HubDefeatSystem
## Système de Défaite & Capture Alternative (Defeat System / 18+ Mature Mechanics)
## Inspiré des boucles de défaite RPG/Survie (Wicked Island) adaptées à l'architecture Prime.
## Au lieu du respawn/clonage immédiat, les ennemis éligibles (bandits, prédateurs)
## capturent le joueur mis hors de combat, déclenchant des options de lutte, soumission ou rançon.

const _HubPaths := preload("res://scripts/hub_paths.gd")

# Constantes d'états
const STATE_NONE := "none"
const STATE_DOWNED := "downed"
const STATE_CAPTIVE := "captive"
const STATE_STRUGGLING := "struggling"
const STATE_SUBMITTED := "submitted"
const STATE_ESCAPED := "escaped"

# Camps de geôles / captivité selon faction ou région
const CAPTIVE_CAMPS := {
	"bandit_camp": {
		"id": "bandit_camp",
		"name": "Campement des Pillards des Sables",
		"pos": [-60.0, 0.2, 40.0],
		"ransom_credits": 150
	},
	"slaver_dungeon": {
		"id": "slaver_dungeon",
		"name": "Geôles Clandestines de Lost Heaven",
		"pos": [15.0, -2.0, -85.0],
		"ransom_credits": 300
	},
	"beast_den": {
		"id": "beast_den",
		"name": "Tanière de Prédateurs",
		"pos": [-120.0, 0.1, -110.0],
		"ransom_credits": 0 # Pas de rançon monétaire pour les bêtes
	}
}

var sim = null
var economy = null
var swg_combat = null
var ham_medical = null

var defeat_enabled: bool = true
var mature_content_enabled: bool = true

# player_id -> Dictionary
var captive_sessions: Dictionary = {}


func setup(parent_sim, economy_svc = null, combat_svc = null, ham_svc = null) -> void:
	sim = parent_sim
	economy = economy_svc
	swg_combat = combat_svc
	ham_medical = ham_svc


## Vérifie si un attaquant est éligible pour déclencher la capture
func is_captor_eligible(attacker_id: String) -> bool:
	if not defeat_enabled:
		return false
	if sim == null or not sim.entities.has(attacker_id):
		# Par défaut, on autorise les bots/PNJ désignés comme bandits ou ravisseurs
		var low := attacker_id.to_lower()
		return low.contains("bandit") or low.contains("slaver") or low.contains("pirate") or low.contains("predator")
	
	var ent: Dictionary = sim.entities[attacker_id]
	var tags: Array = ent.get("tags", [])
	if tags.has("captor") or tags.has("predator") or tags.has("bandit"):
		return true
	var kind: String = str(ent.get("kind", ""))
	if kind == "bandit" or kind == "slaver" or kind == "raider":
		return true
	return false


## Déclenché lorsqu'un joueur subit un coup fatal ou une incapacitation
func on_player_incapacitated(player_id: String, attacker_id: String) -> Dictionary:
	if not defeat_enabled:
		return {"triggered": false, "reason": "system_disabled"}

	var p := player_id.strip_edges()
	var att := attacker_id.strip_edges()

	# Vérifier éligibilité de l'agresseur
	var eligible := is_captor_eligible(att)
	if not eligible:
		return {"triggered": false, "reason": "attacker_not_captor"}

	var camp_key := "bandit_camp"
	var att_low := att.to_lower()
	if att_low.contains("slaver") or att_low.contains("dungeon"):
		camp_key = "slaver_dungeon"
	elif att_low.contains("predator") or att_low.contains("beast") or att_low.contains("chacal"):
		camp_key = "beast_den"

	var camp: Dictionary = CAPTIVE_CAMPS.get(camp_key, CAPTIVE_CAMPS["bandit_camp"])

	var session := {
		"player_id": p,
		"captor_id": att,
		"camp_id": camp_key,
		"camp_name": camp.get("name", "Camp ennemi"),
		"state": STATE_DOWNED,
		"struggle_progress": 0.0,    # 0 à 100%
		"struggle_difficulty": 50.0,  # Résistance
		"time_left": 30.0,           # 30 secondes pour agir
		"ransom_cost": int(camp.get("ransom_credits", 100)),
		"mature_enabled": mature_content_enabled,
		"created_at": Time.get_unix_time_from_system()
	}
	captive_sessions[p] = session

	# Immobiliser le joueur dans la sim si présent
	if sim != null and sim.entities.has(p):
		sim.entities[p]["state"] = "incapacitated"
		sim.entities[p]["active"] = false

	if sim != null and sim.events != null and sim.events.has_method("emit_hub_event"):
		sim.events.emit_hub_event(
			"player.captured",
			"%s a été maîtrisé et capturé par %s !" % [p, att],
			{"player": p, "captor": att, "camp": camp_key}
		)

	return {
		"triggered": true,
		"session": session.duplicate(true)
	}


## Récupère la session de capture active d'un joueur
func get_defeat_state(player_id: String) -> Dictionary:
	var p := player_id.strip_edges()
	if not captive_sessions.has(p):
		return {"active": false, "state": STATE_NONE}
	var sess: Dictionary = captive_sessions[p]
	return {
		"active": true,
		"session": sess.duplicate(true)
	}


## Action de lutte (QTE / Résistance)
func struggle(player_id: String, effort: float = 15.0) -> Dictionary:
	var p := player_id.strip_edges()
	if not captive_sessions.has(p):
		return {"ok": false, "error": "no_active_capture"}

	var sess: Dictionary = captive_sessions[p]
	if sess["state"] == STATE_SUBMITTED or sess["state"] == STATE_ESCAPED:
		return {"ok": false, "error": "session_already_finished"}

	sess["state"] = STATE_STRUGGLING
	var progress: float = float(sess.get("struggle_progress", 0.0)) + effort
	sess["struggle_progress"] = progress

	# Victoire de la lutte : Libération avec petite réanimation
	if progress >= 100.0:
		sess["state"] = STATE_ESCAPED
		_revive_escaped_player(p)
		return {
			"ok": true,
			"outcome": "escaped",
			"message": "Vous avez réussi à vous dégager et à fuir !"
		}

	return {
		"ok": true,
		"outcome": "struggling",
		"progress": progress,
		"time_left": sess.get("time_left", 0.0)
	}


## Soumission volontaire ou par épuisement du timer
func submit(player_id: String, forced: bool = false) -> Dictionary:
	var p := player_id.strip_edges()
	if not captive_sessions.has(p):
		return {"ok": false, "error": "no_active_capture"}

	var sess: Dictionary = captive_sessions[p]
	sess["state"] = STATE_SUBMITTED

	# Conséquence : Téléportation au camp/cage, confiscation de crédits / malus
	var camp_key: String = str(sess.get("camp_id", "bandit_camp"))
	var camp: Dictionary = CAPTIVE_CAMPS.get(camp_key, CAPTIVE_CAMPS["bandit_camp"])
	var target_pos: Array = camp.get("pos", [0.0, 0.0, 0.0])

	# Pénalité économique (pillage partiel par les bandits)
	var lost_credits := 0
	if economy != null:
		var p_data: Dictionary = economy._player(p)
		var current_cr := int(p_data.get("credits", 0))
		lost_credits = mini(current_cr, 50)
		if lost_credits > 0:
			p_data["credits"] = current_cr - lost_credits

	# Téléportation & Réanimation minimale au camp
	if sim != null and sim.entities.has(p):
		sim.entities[p]["x"] = target_pos[0]
		sim.entities[p]["y"] = target_pos[1]
		sim.entities[p]["z"] = target_pos[2]
		sim.entities[p]["state"] = "subdued"
		sim.entities[p]["active"] = true

	# Réanimation avec débuff "Épuisement / Soumission"
	if ham_medical != null:
		var ham: Dictionary = ham_medical._ensure_ham(p)
		ham["health"]["current"] = 50
		ham["action"]["current"] = 50
		ham["mind"]["current"] = 50

	var outcome_msg := "Vous vous êtes soumis. Vos ravisseurs vous ont enfermé dans le %s." % camp.get("name", "camp")
	if forced:
		outcome_msg = "Épuisé, vous avez perdu connaissance. Vous vous réveillez captif au %s." % camp.get("name", "camp")

	return {
		"ok": true,
		"outcome": "submitted",
		"camp": camp,
		"lost_credits": lost_credits,
		"message": outcome_msg
	}


## Paiement de la rançon (rachat de liberté)
func pay_ransom(player_id: String) -> Dictionary:
	var p := player_id.strip_edges()
	if not captive_sessions.has(p):
		return {"ok": false, "error": "no_active_capture"}

	var sess: Dictionary = captive_sessions[p]
	var cost: int = int(sess.get("ransom_cost", 100))
	if cost <= 0:
		return {"ok": false, "error": "ransom_not_accepted_by_captor"}

	if economy != null:
		var p_data: Dictionary = economy._player(p)
		var current_cr := int(p_data.get("credits", 0))
		if current_cr < cost:
			return {"ok": false, "error": "insufficient_credits", "required": cost, "current": current_cr}
		p_data["credits"] = current_cr - cost

	sess["state"] = STATE_ESCAPED
	_revive_escaped_player(p)

	return {
		"ok": true,
		"outcome": "ransomed",
		"paid_credits": cost,
		"message": "La rançon a été payée ! Vos ravisseurs vous laissent partir."
	}


## Réanimation minimale après évasion
func _revive_escaped_player(p: String) -> void:
	if sim != null and sim.entities.has(p):
		sim.entities[p]["state"] = "idle"
		sim.entities[p]["active"] = true
	if ham_medical != null:
		var ham: Dictionary = ham_medical._ensure_ham(p)
		# Rétablir un petit pool pour pouvoir s'enfuir
		ham["health"]["current"] = maxi(int(ham["health"]["current"]), 150)
		ham["action"]["current"] = maxi(int(ham["action"]["current"]), 150)
		ham["mind"]["current"] = maxi(int(ham["mind"]["current"]), 150)


## Tick périodique (mise à jour du timer de lutte)
func tick(dt: float) -> void:
	var to_submit: Array = []
	for p in captive_sessions.keys():
		var sess: Dictionary = captive_sessions[p]
		if sess["state"] == STATE_DOWNED or sess["state"] == STATE_STRUGGLING:
			var t: float = float(sess.get("time_left", 30.0)) - dt
			sess["time_left"] = t
			if t <= 0.0:
				to_submit.append(p)
	
	for p in to_submit:
		submit(p, true)
