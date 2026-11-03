extends RefCounted
class_name HubHamMedical
## Ticket 4.4 (O2 Phase 4 SWG Pre-CU) — Boucle d'Interdépendance Sociale & Médicale :
## Pools HAM (Health / Action / Mind), Blessures (Wounds), Fatigue de Combat (Battle Fatigue),
## Soin d'Esprit & Fatigue à la Cantina La Perle, et Traitement des Blessures au Medcenter.

const BASE_POOL_MAX := 1000
const MAX_WOUNDS := 850
const MAX_BATTLE_FATIGUE := 1000

var economy = null
var skills = null
var show = null


func setup(economy_svc = null, skills_svc = null, show_svc = null) -> void:
	economy = economy_svc
	skills = skills_svc
	show = show_svc


func _ensure_ham(player: String) -> Dictionary:
	if economy == null:
		return {}
	var p: Dictionary = economy._player(player)
	if typeof(p.get("ham")) != TYPE_DICTIONARY:
		p["ham"] = {
			"health": {"base_max": BASE_POOL_MAX, "wounds": 0, "buff": 0, "current": BASE_POOL_MAX},
			"action": {"base_max": BASE_POOL_MAX, "wounds": 0, "buff": 0, "current": BASE_POOL_MAX},
			"mind": {"base_max": BASE_POOL_MAX, "wounds": 0, "buff": 0, "current": BASE_POOL_MAX},
			"battle_fatigue": 0,
		}
	var ham: Dictionary = p["ham"]
	for bar_name in ["health", "action", "mind"]:
		if typeof(ham.get(bar_name)) != TYPE_DICTIONARY:
			ham[bar_name] = {"base_max": BASE_POOL_MAX, "wounds": 0, "buff": 0, "current": BASE_POOL_MAX}
		var bar: Dictionary = ham[bar_name]
		var b_max := int(bar.get("base_max", BASE_POOL_MAX))
		var w := clampi(int(bar.get("wounds", 0)), 0, MAX_WOUNDS)
		var bf := maxi(0, int(bar.get("buff", 0)))
		var eff_max := maxi(100, b_max + bf - w)
		bar["wounds"] = w
		bar["effective_max"] = eff_max
		bar["current"] = clampi(int(bar.get("current", eff_max)), 0, eff_max)
	ham["battle_fatigue"] = clampi(int(ham.get("battle_fatigue", 0)), 0, MAX_BATTLE_FATIGUE)
	return ham


func status(player: String) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var ham := _ensure_ham(p_name)
	if ham.is_empty():
		return {"ok": false, "error": "economy_unavailable"}
	var bf := int(ham.get("battle_fatigue", 0))
	var med_eff := snappedf(clampf(1.0 - (float(bf) / 1200.0), 0.25, 1.0), 0.01)
	return {
		"ok": true,
		"player": p_name,
		"ham": ham.duplicate(true),
		"medical_efficiency_ratio": med_eff,
	}


func apply_combat_trauma(
	player: String,
	damage_health: int = 120,
	wounds_health: int = 45,
	wounds_action: int = 25,
	fatigue_added: int = 60
) -> Dictionary:
	var p_name := player.strip_edges()
	if p_name.is_empty():
		p_name = "Voyageur"
	var ham := _ensure_ham(p_name)
	if ham.is_empty():
		return {"ok": false, "error": "economy_unavailable"}

	var h_bar: Dictionary = ham["health"]
	var a_bar: Dictionary = ham["action"]
	var m_bar: Dictionary = ham["mind"]

	h_bar["wounds"] = clampi(int(h_bar.get("wounds", 0)) + maxi(0, wounds_health), 0, MAX_WOUNDS)
	a_bar["wounds"] = clampi(int(a_bar.get("wounds", 0)) + maxi(0, wounds_action), 0, MAX_WOUNDS)
	m_bar["wounds"] = clampi(int(m_bar.get("wounds", 0)) + maxi(0, int(fatigue_added / 4)), 0, MAX_WOUNDS)
	ham["battle_fatigue"] = clampi(int(ham.get("battle_fatigue", 0)) + maxi(0, fatigue_added), 0, MAX_BATTLE_FATIGUE)

	# Recalcule les plafonds effectifs et applique les dégâts de santé
	_ensure_ham(p_name)
	h_bar["current"] = maxi(1, int(h_bar.get("current", BASE_POOL_MAX)) - maxi(0, damage_health))

	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(p_name, "xp_combat", 40)

	economy._save_players()
	return status(p_name)


func watch_entertainer(
	listener_player: String,
	performer_player: String = "Lia",
	ticks: int = 3,
	in_cantina: bool = true
) -> Dictionary:
	var listener := listener_player.strip_edges()
	if listener.is_empty():
		listener = "Voyageur"
	var performer := performer_player.strip_edges()
	if performer.is_empty():
		performer = "Lia"
	if not in_cantina:
		return {
			"ok": false,
			"error": "not_in_cantina",
			"hint": "Rends-toi à la Cantina La Perle pour écouter/regarder un artiste et dissiper la Battle Fatigue.",
		}

	var ham := _ensure_ham(listener)
	if ham.is_empty():
		return {"ok": false, "error": "economy_unavailable"}

	var perf_mods := {"fatigue_heal_power": 18}
	if skills != null and skills.has_method("compute_skill_mods"):
		perf_mods = skills.compute_skill_mods(performer)
	var heal_per_tick := maxi(15, int(perf_mods.get("fatigue_heal_power", 18)) * 2)
	var n_ticks := maxi(1, ticks)

	var old_bf := int(ham.get("battle_fatigue", 0))
	var bf_cured := mini(old_bf, heal_per_tick * n_ticks)
	ham["battle_fatigue"] = maxi(0, old_bf - bf_cured)

	var m_bar: Dictionary = ham["mind"]
	var old_mw := int(m_bar.get("wounds", 0))
	var mw_cured := mini(old_mw, int(round(float(heal_per_tick * n_ticks) * 0.6)))
	m_bar["wounds"] = maxi(0, old_mw - mw_cured)
	m_bar["buff"] = clampi(int(m_bar.get("buff", 0)) + 50 * n_ticks, 0, 450)

	_ensure_ham(listener)
	m_bar["current"] = int(m_bar["effective_max"])

	var xp_scene_gain := 30 * n_ticks + int(bf_cured * 0.5)
	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(performer, "xp_scene", xp_scene_gain)

	economy.log_session_event(
		listener,
		"cantina_recovery",
		"Spectacle de %s à La Perle : -%d Fatigue, +%d buff Esprit" % [performer, bf_cured, int(m_bar["buff"])],
		{"performer": performer, "fatigue_cured": bf_cured, "mind_wounds_cured": mw_cured}
	)
	economy._save_players()

	return {
		"ok": true,
		"listener": listener,
		"performer": performer,
		"fatigue_cured": bf_cured,
		"mind_wounds_cured": mw_cured,
		"mind_buff": int(m_bar["buff"]),
		"performer_xp_gained": xp_scene_gain,
		"status": status(listener),
	}


func treat_wounds(
	medic_player: String,
	patient_player: String,
	pool_name: String = "health",
	medpack_item_id: String = "",
	in_medcenter: bool = true
) -> Dictionary:
	var medic := medic_player.strip_edges()
	if medic.is_empty():
		medic = "Voyageur"
	var patient := patient_player.strip_edges()
	if patient.is_empty():
		patient = medic
	if economy == null:
		return {"ok": false, "error": "economy_unavailable"}

	var p_medic: Dictionary = economy._player(medic)
	var m_skills: Array = p_medic.get("skills", [])
	if "medecin_novice" not in m_skills and "medecine_camp_r1" not in m_skills:
		return {
			"ok": false,
			"error": "missing_medic_skill",
			"requires_skill": "medecin_novice",
		}
	var is_field_kit := medpack_item_id.strip_edges() in ["baume_urgence_terrain", "bandage_antivenin"]
	if not in_medcenter and not is_field_kit:
		return {
			"ok": false,
			"error": "not_in_medcenter",
			"hint": "Le traitement des blessures en milieu hostile requiert un baume d'urgence ou le Poste Médical (Odo Merr).",
		}

	var target_bar := pool_name.strip_edges().to_lower()
	if target_bar not in ["health", "action"]:
		target_bar = "health"

	var ham := _ensure_ham(patient)
	var mods := {"wound_heal_efficiency": 25}
	if skills != null and skills.has_method("compute_skill_mods"):
		mods = skills.compute_skill_mods(medic)

	var base_power := int(mods.get("wound_heal_efficiency", 25)) * 3
	# Bonus si le médecin utilise un consommable artisanal (bandage_antivenin / scrap_repair_kit / water_filter_condenser)
	var crafted_bonus := 0
	if not medpack_item_id.strip_edges().is_empty():
		var inv: Array = p_medic.get("inventory", [])
		for it in inv:
			if typeof(it) == TYPE_DICTIONARY and str(it.get("id", "")) == medpack_item_id.strip_edges() and int(it.get("qty", 0)) > 0:
				if typeof(it.get("item_stats")) == TYPE_DICTIONARY:
					crafted_bonus = int((it["item_stats"] as Dictionary).get("power", 30))
				else:
					crafted_bonus = 30
				it["qty"] = int(it.get("qty", 1)) - 1
				break

	var bf := int(ham.get("battle_fatigue", 0))
	var fatigue_mult := clampf(1.0 - (float(bf) / 1200.0), 0.25, 1.0)
	var raw_cure := int(round(float(base_power + crafted_bonus) * fatigue_mult))

	var bar: Dictionary = ham[target_bar]
	var old_wounds := int(bar.get("wounds", 0))
	var cured := mini(old_wounds, maxi(10, raw_cure))
	bar["wounds"] = maxi(0, old_wounds - cured)
	if is_field_kit:
		ham["battle_fatigue"] = maxi(0, int(ham.get("battle_fatigue", 0)) - 25)

	_ensure_ham(patient)
	bar["current"] = int(bar["effective_max"])

	var xp_med_gain := 35 + int(cured * 0.8)
	if skills != null and skills.has_method("grant_xp"):
		skills.grant_xp(medic, "xp_medecine", xp_med_gain)

	economy.log_session_event(
		medic,
		"medic_treat_wounds",
		"Soin médical sur %s (%s) : -%d Wounds (eff. fatigue %d%%)" % [patient, target_bar, cured, int(round(fatigue_mult * 100.0))],
		{"patient": patient, "pool": target_bar, "wounds_cured": cured}
	)
	economy._save_players()

	return {
		"ok": true,
		"medic": medic,
		"patient": patient,
		"pool": target_bar,
		"wounds_cured": cured,
		"remaining_wounds": int(bar["wounds"]),
		"fatigue_multiplier": snappedf(fatigue_mult, 0.01),
		"crafted_medpack_bonus": crafted_bonus,
		"medic_xp_gained": xp_med_gain,
		"status": status(patient),
	}

