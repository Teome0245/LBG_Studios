extends RefCounted
class_name HubSwgCombat
## Système SWG Pre-CU : Combat Tactique, Ciblage HAM, Postures, Combos d'États
## (Dizzy + Knockdown, Stun, Blind, Intimidate) & Encombrement d'Armure (Ticket 1).

const _HubPaths := preload("res://scripts/hub_paths.gd")

# Postures valides
const POSTURE_UPRIGHT := "upright"
const POSTURE_KNEELING := "kneeling"
const POSTURE_PRONE := "prone"

var sim = null
var economy = null
var skills = null
var ham_medical = null

var postures_by_eid: Dictionary = {}
var states_by_eid: Dictionary = {}
var armor_by_player: Dictionary = {}
var beast_ham_by_eid: Dictionary = {}

var _rng := RandomNumberGenerator.new()


func setup(parent_sim, economy_svc = null, skills_svc = null, ham_svc = null) -> void:
	sim = parent_sim
	economy = economy_svc
	skills = skills_svc
	ham_medical = ham_svc
	_rng.randomize()


# ==============================================================================
# SECTION 1 : GESTION DES POSTURES (UPRIGHT, KNEELING, PRONE)
# ==============================================================================

func get_posture(eid: String) -> String:
	return str(postures_by_eid.get(eid, POSTURE_UPRIGHT))


func change_posture(eid: String, new_posture: String) -> Dictionary:
	var post := new_posture.strip_edges().to_lower()
	if not post in [POSTURE_UPRIGHT, POSTURE_KNEELING, POSTURE_PRONE]:
		return {"ok": false, "error": "invalid_posture", "hint": "upright, kneeling, prone"}

	var cur_post := get_posture(eid)
	if cur_post == post:
		return {"ok": true, "eid": eid, "posture": post, "changed": false}

	# Règle SWG Combo Dizzy : tenter de se relever de Prone en étant Dizzy fait trébucher violemment !
	if cur_post == POSTURE_PRONE and (post == POSTURE_UPRIGHT or post == POSTURE_KNEELING):
		if has_state(eid, "dizzy"):
			# Échec cuisant : reste au sol et subit un étourdissement prolongé
			var states := _ensure_states(eid)
			states["knockdown"] = Time.get_unix_time_from_system() + 3.0
			return {
				"ok": false,
				"outcome": "dizzy_fall",
				"error": "too_dizzy_to_stand",
				"message": "Pris de vertige violent (Dizzy), la cible trébuche et retombe au sol !",
				"posture": POSTURE_PRONE
			}

	postures_by_eid[eid] = post
	return {
		"ok": true,
		"eid": eid,
		"old_posture": cur_post,
		"new_posture": post,
		"changed": true
	}


# ==============================================================================
# SECTION 2 : ÉTATS ALTÉRÉS SWG (DIZZY, KNOCKDOWN, STUN, BLIND, INTIMIDATE)
# ==============================================================================

func _ensure_states(eid: String) -> Dictionary:
	if not states_by_eid.has(eid):
		states_by_eid[eid] = {}
	return states_by_eid[eid]


func apply_state(eid: String, state_name: String, duration_s: float) -> Dictionary:
	var sname := state_name.strip_edges().to_lower()
	var states := _ensure_states(eid)
	var expires := Time.get_unix_time_from_system() + duration_s
	states[sname] = expires

	# Effets directs immédiats
	if sname == "knockdown":
		# Knockdown force la posture Prone (au sol)
		postures_by_eid[eid] = POSTURE_PRONE

	return {
		"ok": true,
		"eid": eid,
		"state": sname,
		"duration_s": duration_s,
		"expires_at": expires
	}


func has_state(eid: String, state_name: String) -> bool:
	if not states_by_eid.has(eid):
		return false
	var states: Dictionary = states_by_eid[eid]
	var sname := state_name.strip_edges().to_lower()
	if states.has(sname):
		var exp_t := float(states[sname])
		if exp_t > Time.get_unix_time_from_system():
			return true
		states.erase(sname)
	return false


func clear_state(eid: String, state_name: String) -> void:
	if states_by_eid.has(eid):
		states_by_eid[eid].erase(state_name.strip_edges().to_lower())


func list_active_states(eid: String) -> Array:
	var out: Array = []
	if not states_by_eid.has(eid):
		return out
	var now := Time.get_unix_time_from_system()
	var states: Dictionary = states_by_eid[eid]
	for s in states.keys():
		var exp_t := float(states[s])
		if exp_t > now:
			out.append({"state": s, "remaining_s": snappedf(exp_t - now, 0.1)})
	return out


func get_combat_state(eid: String) -> Dictionary:
	return {
		"eid": eid,
		"posture": get_posture(eid),
		"active_statuses": states_by_eid.get(eid, {}),
		"active_states": list_active_states(eid),
		"armor_protection": get_armor_protection(eid)
	}


# ==============================================================================
# SECTION 3 : ENCOMBREMENT D'ARMURE (ARMOR ENCUMBRANCE)
# ==============================================================================

func equip_armor_piece(player: String, slot: String, armor_data: Dictionary) -> Dictionary:
	if not armor_by_player.has(player):
		armor_by_player[player] = {}
	var slots: Dictionary = armor_by_player[player]
	slots[slot] = armor_data.duplicate(true)

	var enc := calculate_encumbrance(player)
	return {
		"ok": true,
		"player": player,
		"slot": slot,
		"equipped": armor_data.get("name", slot),
		"total_encumbrance": enc
	}


func unequip_armor_piece(player: String, slot: String) -> Dictionary:
	if armor_by_player.has(player):
		armor_by_player[player].erase(slot)
	return {"ok": true, "player": player, "slot": slot, "total_encumbrance": calculate_encumbrance(player)}


func calculate_encumbrance(player: String) -> Dictionary:
	var enc := {"health": 0, "action": 0, "mind": 0}
	if not armor_by_player.has(player):
		return enc

	var slots: Dictionary = armor_by_player[player]
	for s in slots.keys():
		var piece: Dictionary = slots[s]
		enc["health"] += int(piece.get("encumbrance_health", 0))
		enc["action"] += int(piece.get("encumbrance_action", 0))
		enc["mind"] += int(piece.get("encumbrance_mind", 0))
	return enc


func get_armor_protection(eid: String) -> int:
	var prot := 0
	if armor_by_player.has(eid):
		var slots: Dictionary = armor_by_player[eid]
		for s in slots.keys():
			prot += int(slots[s].get("armor_rating", 0))

	# Si Stun : réduction d'armure de 50%
	if has_state(eid, "stun"):
		prot = int(prot * 0.5)

	return prot


# ==============================================================================
# SECTION 4 : CIBLAGE HAM & ATTAQUES TACTIQUES (TACTICAL STRIKES)
# ==============================================================================

func _ensure_beast_ham(beast_eid: String, max_hp: int = 500) -> Dictionary:
	if not beast_ham_by_eid.has(beast_eid):
		beast_ham_by_eid[beast_eid] = {
			"health": max_hp,
			"action": max_hp,
			"mind": max_hp,
			"max_health": max_hp,
			"max_action": max_hp,
			"max_mind": max_hp
		}
	return beast_ham_by_eid[beast_eid]


func execute_tactical_strike(
	attacker_id: String,
	target_eid: String,
	strike_type: String,
	force_hit: bool = false
) -> Dictionary:
	var stype := strike_type.strip_edges().to_lower()

	# Coûts et paramètres par compétence
	var target_pool := "health"
	var cost_pool := "action"
	var cost_amount := 20
	var base_dmg := 60
	var status_inflicted := ""
	var status_duration := 15.0

	match stype:
		"head_shot":
			# Tir/frappe à la tête : cible le MIND, inflige DIZZY
			target_pool = "mind"
			cost_pool = "mind"
			cost_amount = 35
			base_dmg = 75
			status_inflicted = "dizzy"
			status_duration = 16.0
		"leg_sweep":
			# Balayage des jambes : cible l'ACTION, inflige KNOCKDOWN
			target_pool = "action"
			cost_pool = "action"
			cost_amount = 30
			base_dmg = 65
			status_inflicted = "knockdown"
			status_duration = 4.0
		"body_hit":
			# Frappe corporelle : cible la SANTÉ, inflige STUN
			target_pool = "health"
			cost_pool = "action"
			cost_amount = 25
			base_dmg = 85
			status_inflicted = "stun"
			status_duration = 12.0
		"dirt_throw":
			# Projection de poussière : cible l'ACTION, inflige BLIND
			target_pool = "action"
			cost_pool = "action"
			cost_amount = 15
			base_dmg = 20
			status_inflicted = "blind"
			status_duration = 18.0
		"intimidate":
			# Intimidation psychologique : cible le MIND, inflige INTIMIDATE
			target_pool = "mind"
			cost_pool = "mind"
			cost_amount = 30
			base_dmg = 25
			status_inflicted = "intimidate"
			status_duration = 20.0
		_:
			stype = "body_hit"

	# 1. Vérification et déduction du coût HAM pour l'attaquant
	if ham_medical != null:
		var att_ham: Dictionary = ham_medical._ensure_ham(attacker_id)
		if not att_ham.is_empty():
			var c_bar: Dictionary = att_ham.get(cost_pool, {})
			var cur_cost_val := int(c_bar.get("current", 100))
			if cur_cost_val < cost_amount:
				return {
					"ok": false,
					"error": "insufficient_ham_pool",
					"pool": cost_pool,
					"required": cost_amount,
					"available": cur_cost_val
				}
			c_bar["current"] = cur_cost_val - cost_amount

	# 2. Précision et jet de touche
	var hit_chance := 80
	var att_post := get_posture(attacker_id)
	var tgt_post := get_posture(target_eid)

	if att_post == POSTURE_KNEELING: hit_chance += 15
	elif att_post == POSTURE_PRONE: hit_chance += 25

	if tgt_post == POSTURE_PRONE: hit_chance -= 20 # Cible au sol plus dure à toucher à distance

	# Malus si l'attaquant est Aveuglé (Blind)
	if has_state(attacker_id, "blind"):
		hit_chance -= 45

	var roll := _rng.randi_range(1, 100)
	if not force_hit and roll > hit_chance:
		return {
			"ok": true,
			"outcome": "miss",
			"message": "Le tir a manqué la cible !",
			"strike_type": stype,
			"target_pool": target_pool,
			"roll": roll,
			"hit_chance": hit_chance
		}

	# 3. Calcul des dégâts et mitigation
	var dmg := base_dmg
	# Si l'attaquant est Intimidé : dégâts divisés par 2
	if has_state(attacker_id, "intimidate"):
		dmg = int(dmg * 0.5)

	# Si la cible est au sol (Prone) et subit un body_hit ou leg_sweep au corps à corps : +35% dégâts
	if tgt_post == POSTURE_PRONE and (stype == "body_hit" or stype == "leg_sweep"):
		dmg = int(dmg * 1.35)

	# Mitigation par l'armure de la cible
	var armor_prot := get_armor_protection(target_eid)
	var final_dmg := maxi(10, dmg - armor_prot)

	# 4. Application des dégâts au pool HAM ciblé
	var is_incapacitated := false
	var remaining_target_pool := 100
	var defeat_res: Dictionary = {}

	# Cas 1 : Cible est un joueur avec système HAM
	if ham_medical != null and economy != null and economy._player(target_eid).has("ham"):
		var tgt_ham: Dictionary = ham_medical._ensure_ham(target_eid)
		var p_bar: Dictionary = tgt_ham[target_pool]
		var cur_val := int(p_bar.get("current", 500))
		var new_val := maxi(0, cur_val - final_dmg)
		p_bar["current"] = new_val
		remaining_target_pool = new_val
		if new_val <= 0:
			is_incapacitated = true
			apply_state(target_eid, "knockdown", 10.0)
			if sim != null and sim.defeat_system != null:
				defeat_res = sim.defeat_system.on_player_incapacitated(target_eid, attacker_id)

	# Cas 2 : Cible est une créature ou PNJ
	else:
		var b_ham := _ensure_beast_ham(target_eid)
		var cur_val := int(b_ham.get(target_pool, 500))
		var new_val := maxi(0, cur_val - final_dmg)
		b_ham[target_pool] = new_val
		remaining_target_pool = new_val
		if new_val <= 0:
			is_incapacitated = true
			apply_state(target_eid, "knockdown", 10.0)
			if sim != null and sim.entities.has(target_eid):
				sim.entities[target_eid]["active"] = false
				sim.entities[target_eid]["goal"] = "incapacitated"

	# 5. Application de l'état altéré
	var state_applied := false
	if not status_inflicted.is_empty():
		apply_state(target_eid, status_inflicted, status_duration)
		state_applied = true

	# 6. Combo fatal SWG : Dizzy + Knockdown vérifié
	var is_deadly_combo := has_state(target_eid, "dizzy") and has_state(target_eid, "knockdown")

	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(attacker_id, "xp_combat", 50)

	return {
		"ok": true,
		"outcome": "hit",
		"strike_type": stype,
		"target_pool": target_pool,
		"damage": final_dmg,
		"armor_mitigation": armor_prot,
		"remaining_pool": remaining_target_pool,
		"status_applied": status_inflicted if state_applied else "none",
		"is_incapacitated": is_incapacitated,
		"is_deadly_combo": is_deadly_combo,
		"defeat_triggered": bool(defeat_res.get("triggered", false)),
		"defeat_session": defeat_res.get("session", {}),
		"target_posture": get_posture(target_eid)
	}


# ==============================================================================
# SECTION 5 : TICKS & EXPIRATION DES ÉTATS
# ==============================================================================

func tick_combat(_dt: float) -> void:
	var now := Time.get_unix_time_from_system()
	for eid in states_by_eid.keys():
		var states: Dictionary = states_by_eid[eid]
		for s in states.keys():
			if float(states[s]) < now:
				states.erase(s)
		if states.is_empty():
			states_by_eid.erase(eid)
