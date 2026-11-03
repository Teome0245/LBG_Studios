extends SceneTree
## ham_cantina_medcenter_selftest.gd — Validation headless de la Boucle HAM, Wounds (Medcenter) & Battle Fatigue (Cantina) (Ticket 4.4).

const HubEconomyScript := preload("res://scripts/hub_economy.gd")
const HubSkillsScript := preload("res://scripts/hub_skills.gd")
const HubHamMedicalScript := preload("res://scripts/hub_ham_medical.gd")


func _init() -> void:
	print("[*] Lancement du test Boucle Sociale & Médicale HAM / Wounds / Battle Fatigue (Ticket 4.4)...")

	var economy := HubEconomyScript.new()
	economy.setup()

	var skills := HubSkillsScript.new()
	skills.setup(economy)

	var ham_med := HubHamMedicalScript.new()
	ham_med.setup(economy, skills)

	var ts := int(Time.get_unix_time_from_system() * 1000.0) + (Time.get_ticks_msec() % 10000)
	var fighter := "Kael_Fighter_%d" % ts
	var dancer := "Lia_Dancer_%d" % ts
	var medic := "Odo_Medic_%d" % ts

	skills.learn_box(dancer, "scene_novice", true)
	skills.learn_box(dancer, "scene_soin_01", true)
	skills.learn_box(medic, "medecin_soin_01", true)

	# 1. Traumatisme de combat : le combattant subit des Wounds et de la Battle Fatigue
	var trauma := ham_med.apply_combat_trauma(fighter, 250, 180, 90, 240)
	var ham_t: Dictionary = trauma.get("ham", {})
	var h_bar_t: Dictionary = ham_t.get("health", {})
	assert(int(h_bar_t.get("wounds", 0)) == 180, "Le combattant doit avoir 180 Wounds sur Health")
	assert(int(h_bar_t.get("effective_max", 1000)) == 820, "Le Health max effectif doit être réduit à 820 par les Wounds")
	assert(int(ham_t.get("battle_fatigue", 0)) == 240, "La Battle Fatigue doit être à 240")
	print("[+] PASS: Blessures de combat (180 Wounds -> Max Health=820) et Battle Fatigue (240) appliquées")

	# 2. Passage à la Cantina La Perle : regarder l'artiste dissipe la Battle Fatigue et buff l'Esprit (Mind)
	var cantina_res := ham_med.watch_entertainer(fighter, dancer, 4, true)
	assert(bool(cantina_res.get("ok", false)) == true, "watch_entertainer à la Cantina doit réussir")
	assert(int(cantina_res.get("fatigue_cured", 0)) > 0, "La Battle Fatigue doit être réduite")
	assert(int(cantina_res.get("mind_buff", 0)) >= 150, "Un buff Mind doit être conféré")
	var st_after_cantina: Dictionary = cantina_res.get("status", {})
	var bf_after := int((st_after_cantina.get("ham", {}) as Dictionary).get("battle_fatigue", 999))
	assert(bf_after < 240, "La Battle Fatigue après Cantina doit avoir diminué")
	print("[+] PASS: Passage Cantina La Perle : Battle Fatigue 240 -> %d, Mind Buff=+%d" % [
		bf_after,
		int(cantina_res.get("mind_buff", 0))
	])

	# 3. Passage au Medcenter : le médecin soigne les Wounds de Health
	var med_res := ham_med.treat_wounds(medic, fighter, "health", "", true)
	assert(bool(med_res.get("ok", false)) == true, "treat_wounds au Medcenter doit réussir")
	assert(int(med_res.get("wounds_cured", 0)) > 0, "Des blessures doivent être soignées")
	assert(int(med_res.get("remaining_wounds", 999)) < 180, "Les Wounds restantes doivent avoir diminué")
	print("[+] PASS: Soin au Medcenter : -%d Wounds (Wounds restantes=%d, XP médecin=+%d)" % [
		int(med_res.get("wounds_cured", 0)),
		int(med_res.get("remaining_wounds", 0)),
		int(med_res.get("medic_xp_gained", 0))
	])

	if economy.db != null and economy.db.has_method("shutdown"):
		economy.db.shutdown()

	print("[+] Ticket 4.4 (Boucle HAM / Cantina / Medcenter) : Tous les tests passent avec succès !")
	quit(0)

