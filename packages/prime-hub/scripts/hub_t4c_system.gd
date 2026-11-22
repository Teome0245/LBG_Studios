extends RefCounted
class_name HubT4cSystem
## hub_t4c_system.gd — Cœur Hybride T4C (La 4ème Prophétie) & Star Wars Galaxies
## Gère les caractéristiques libres (FOR/END/DEX/INT/SAG), l'influence sur les jauges HAM,
## les prérequis stricts d'équipement (armes/armures) et le Grimoire de Sorts (magie arcanique & foi divine).

var economy = null
var skills = null
var ham_medical = null
var combat = null

# Catalogue canonique des sorts T4C (La 4ème Prophétie) adaptés à Lost Heaven
const SPELLS_CATALOG := {
	"etincelle": {
		"id": "etincelle",
		"name": "Étincelle Arcanique",
		"school": "feu_air",
		"req_intelligence": 20,
		"req_wisdom": 0,
		"mind_cost": 30,
		"power": 65,
		"description": "Projette une gerbe d'étincelles énergétiques sur la cible."
	},
	"guerison_mineure": {
		"id": "guerison_mineure",
		"name": "Guérison Mineure",
		"school": "lumiere",
		"req_intelligence": 0,
		"req_wisdom": 25,
		"mind_cost": 35,
		"heal_amount": 120,
		"description": "Canalise la foi bienveillante pour refermer les plaies légères."
	},
	"bouclier_de_terre": {
		"id": "bouclier_de_terre",
		"name": "Bouclier de Silice",
		"school": "terre",
		"req_intelligence": 25,
		"req_endurance": 30,
		"mind_cost": 50,
		"buff_armor": 20,
		"duration_s": 60,
		"description": "Durcit les poussières de Scrapaltai autour du corps pour absorber les impacts."
	},
	"eclair_de_plasma": {
		"id": "eclair_de_plasma",
		"name": "Éclair de Plasma",
		"school": "feu_air",
		"req_intelligence": 45,
		"req_wisdom": 15,
		"mind_cost": 75,
		"power": 240,
		"description": "Foudroie la cible avec un arc électrique ionisé à haute température."
	},
	"priere_seraphin": {
		"id": "priere_seraphin",
		"name": "Prière du Séraphin",
		"school": "divin",
		"req_wisdom": 50,
		"req_intelligence": 20,
		"min_karma": 200,
		"mind_cost": 110,
		"heal_amount": 380,
		"wound_cure": 30,
		"description": "Réservé aux Protecteurs et Séraphins de l'Ordre : soigne intensément et guérit les blessures HAM."
	},
	"souffle_de_l_abyme": {
		"id": "souffle_de_l_abyme",
		"name": "Souffle de l'Abyme",
		"school": "necro",
		"req_intelligence": 50,
		"req_wisdom": 10,
		"max_karma": -200,
		"mind_cost": 120,
		"power": 360,
		"description": "Réservé aux Hors-la-loi et Terreurs des Sables : draine la vitalité vitale en ignorant 50% d'armure."
	}
}

# Catalogue canonique d'objets avec prérequis stricts T4C
const EQUIPMENT_REQUIREMENTS := {
	"epee_batarde_acier": {"req_strength": 40, "req_endurance": 25, "slot": "weapon_primary"},
	"hache_de_guerre_lourde": {"req_strength": 65, "req_endurance": 45, "slot": "weapon_primary"},
	"arc_composite_des_sables": {"req_dexterity": 45, "req_strength": 25, "slot": "weapon_primary"},
	"dague_assassin_krayt": {"req_dexterity": 55, "slot": "weapon_primary"},
	"cuirasse_plaques_zalem": {"req_strength": 50, "req_endurance": 55, "slot": "chest"},
	"robe_de_soie_astrale": {"req_wisdom": 40, "req_intelligence": 45, "slot": "chest"},
	"tunique_cuir_renforce": {"req_endurance": 30, "req_dexterity": 30, "slot": "chest"},
	"grimoire_arcanique_ancien": {"req_intelligence": 50, "slot": "weapon_secondary"},
	"relique_des_anciens": {"req_wisdom": 50, "slot": "weapon_secondary"}
}


func setup(economy_svc = null, skills_svc = null, ham_svc = null, combat_svc = null) -> void:
	economy = economy_svc
	skills = skills_svc
	ham_medical = ham_svc
	combat = combat_svc


## Calcule les bonus dérivés T4C sur les 3 jauges HAM de SWG (Health / Action / Mind)
func calculate_ham_derived_pools(player: String) -> Dictionary:
	var base_health := 1000
	var base_action := 1000
	var base_mind := 1000

	if skills == null:
		return {"max_health": base_health, "max_action": base_action, "max_mind": base_mind}

	var atts: Dictionary = skills.get_t4c_attributes(player)
	var str_val := int(atts.get("strength", 20))
	var end_val := int(atts.get("endurance", 20))
	var dex_val := int(atts.get("dexterity", 20))
	var int_val := int(atts.get("intelligence", 20))
	var wis_val := int(atts.get("wisdom", 20))

	# Formule dérivée hybride T4C / SWG :
	# Santé dépend principalement de la Force et de l'Endurance
	var max_health := base_health + (str_val * 10) + (end_val * 18)
	# Action dépend de la Dextérité et de la Force
	var max_action := base_action + (dex_val * 15) + (str_val * 8)
	# Mind (Mana/Esprit) dépend de l'Intelligence et de la Sagesse
	var max_mind := base_mind + (int_val * 16) + (wis_val * 16)

	return {
		"strength": str_val,
		"endurance": end_val,
		"dexterity": dex_val,
		"intelligence": int_val,
		"wisdom": wis_val,
		"max_health": max_health,
		"max_action": max_action,
		"max_mind": max_mind,
		"physical_power_bonus": int(str_val * 1.5),
		"crit_chance_pct": snappedf(float(dex_val) * 0.15, 0.1),
		"spell_power_bonus": int((int_val + wis_val) * 1.2)
	}


## Vérifie si le joueur remplit les prérequis stricts T4C pour équiper un objet
func can_equip_item(player: String, item_id: String) -> Dictionary:
	var item_clean := item_id.strip_edges().to_lower()
	if not EQUIPMENT_REQUIREMENTS.has(item_clean):
		# Pas de prérequis spécifique répertorié : équipable librement
		return {"ok": true, "can_equip": true, "item": item_clean, "missing": {}}

	if skills == null:
		return {"ok": false, "error": "skills_unavailable"}

	var atts: Dictionary = skills.get_t4c_attributes(player)
	var reqs: Dictionary = EQUIPMENT_REQUIREMENTS[item_clean]
	var missing: Dictionary = {}
	var can_equip := true

	for req_key_variant in ["req_strength", "req_endurance", "req_dexterity", "req_intelligence", "req_wisdom"]:
		var req_key: String = str(req_key_variant)
		if reqs.has(req_key):
			var stat_name: String = req_key.replace("req_", "")
			var required_val := int(reqs[req_key])
			var current_val := int(atts.get(stat_name, 0))
			if current_val < required_val:
				can_equip = false
				missing[stat_name] = {
					"required": required_val,
					"current": current_val,
					"lacking": required_val - current_val
				}

	return {
		"ok": true,
		"player": player,
		"item": item_clean,
		"can_equip": can_equip,
		"requirements": reqs,
		"current_attributes": atts,
		"missing": missing
	}


## Récupère le grimoire des sorts éligibles ou connus par le joueur
func get_spellbook(player: String) -> Dictionary:
	if skills == null:
		return {"ok": false, "error": "skills_unavailable"}

	var atts: Dictionary = skills.get_t4c_attributes(player)
	var karma := int(atts.get("karma", 0))
	var int_val := int(atts.get("intelligence", 20))
	var wis_val := int(atts.get("wisdom", 20))

	var available_spells: Array = []
	for spell_id in SPELLS_CATALOG.keys():
		var sp: Dictionary = (SPELLS_CATALOG[spell_id] as Dictionary).duplicate(true)
		var can_cast := true
		var reasons: Array = []

		if int_val < int(sp.get("req_intelligence", 0)):
			can_cast = false
			reasons.append("req_intelligence_%d" % int(sp["req_intelligence"]))
		if wis_val < int(sp.get("req_wisdom", 0)):
			can_cast = false
			reasons.append("req_wisdom_%d" % int(sp["req_wisdom"]))
		if sp.has("min_karma") and karma < int(sp["min_karma"]):
			can_cast = false
			reasons.append("min_karma_%d" % int(sp["min_karma"]))
		if sp.has("max_karma") and karma > int(sp["max_karma"]):
			can_cast = false
			reasons.append("max_karma_%d" % int(sp["max_karma"]))

		sp["can_cast"] = can_cast
		sp["unmet_conditions"] = reasons
		available_spells.append(sp)

	return {
		"ok": true,
		"player": player,
		"attributes": atts,
		"spells_count": available_spells.size(),
		"spells": available_spells
	}


## Lance un sort T4C : consomme du Mind (HAM) et applique soins ou dégâts magiques
func cast_spell(player: String, spell_id: String, target_id: String = "") -> Dictionary:
	var sp_id := spell_id.strip_edges().to_lower()
	if not SPELLS_CATALOG.has(sp_id):
		return {"ok": false, "error": "spell_not_found", "spell_id": sp_id}

	var spell: Dictionary = SPELLS_CATALOG[sp_id]
	var book := get_spellbook(player)
	var matching_sp: Dictionary = {}
	for s in book.get("spells", []):
		if s.get("id") == sp_id:
			matching_sp = s
			break

	if not bool(matching_sp.get("can_cast", false)):
		return {
			"ok": false,
			"error": "conditions_not_met",
			"unmet_conditions": matching_sp.get("unmet_conditions", []),
			"spell": spell
		}

	# Vérification et déduction du coût en Mind dans le système HAM
	var mind_cost := int(spell.get("mind_cost", 20))
	var h_status: Dictionary = {}
	if ham_medical != null and ham_medical.has_method("status"):
		h_status = ham_medical.status(player)
		var ham_dict: Dictionary = h_status.get("ham", {})
		var m_bar: Dictionary = ham_dict.get("mind", {})
		var current_mind := int(m_bar.get("current", 0))
		if current_mind < mind_cost:
			return {
				"ok": false,
				"error": "insufficient_mind",
				"required_mind": mind_cost,
				"current_mind": current_mind
			}
		# Déduit le Mind
		m_bar["current"] = maxi(0, current_mind - mind_cost)

	# Application de l'effet magique
	var effect_type := ""
	var effect_value := 0

	if spell.has("heal_amount"):
		effect_type = "heal"
		effect_value = int(spell["heal_amount"])
		if not h_status.is_empty():
			var ham_dict: Dictionary = h_status.get("ham", {})
			var h_bar: Dictionary = ham_dict.get("health", {})
			var eff_max := int(h_bar.get("effective_max", 1000))
			h_bar["current"] = mini(eff_max, int(h_bar.get("current", 0)) + effect_value)
			if spell.has("wound_cure"):
				h_bar["wounds"] = maxi(0, int(h_bar.get("wounds", 0)) - int(spell["wound_cure"]))
				var b_max := int(h_bar.get("base_max", 1000))
				var bf := maxi(0, int(h_bar.get("buff", 0)))
				h_bar["effective_max"] = maxi(100, b_max + bf - int(h_bar["wounds"]))

	elif spell.has("power"):
		effect_type = "damage"
		effect_value = int(spell["power"])
		if target_id != "" and combat != null:
			combat.inflict_pvp_damage(player, target_id, effect_value, "magical")

	elif spell.has("buff_armor"):
		effect_type = "buff"
		effect_value = int(spell["buff_armor"])

	return {
		"ok": true,
		"player": player,
		"spell_id": sp_id,
		"spell_name": spell.get("name"),
		"mind_consumed": mind_cost,
		"effect_type": effect_type,
		"effect_value": effect_value,
		"target": target_id if target_id != "" else player
	}


## Cérémonie de Renaissance T4C (Séraphin / Démon) :
## Accessible après avoir fait ses preuves (ex: 200+ Skill Points et Karma tranché)
func renaissance_seraph(player: String) -> Dictionary:
	if skills == null or economy == null:
		return {"ok": false, "error": "services_unavailable"}

	var atts: Dictionary = skills.get_t4c_attributes(player)
	var karma := int(atts.get("karma", 0))
	var wing_type := "céleste" if karma >= 0 else "infernale"

	# Bonus de renaissance : +25 points non alloués et titre
	var current_unalloc := int(atts.get("unallocated_points", 0))
	var p: Dictionary = economy._player(player)
	p["t4c_attributes"]["unallocated_points"] = current_unalloc + 25
	p["t4c_attributes"]["seraph_rank"] = int(atts.get("seraph_rank", 0)) + 1
	p["t4c_attributes"]["wing_type"] = wing_type

	economy.log_session_event(
		player,
		"renaissance_seraph",
		"Renaissance Séraphin accomplie (Ailes %s) : +25 stats points !" % wing_type,
		{"karma": karma, "wings": wing_type}
	)
	economy._save_players()

	return {
		"ok": true,
		"player": player,
		"renaissance": true,
		"wing_type": wing_type,
		"bonus_points": 25,
		"new_unallocated_points": current_unalloc + 25,
		"seraph_rank": p["t4c_attributes"]["seraph_rank"]
	}
