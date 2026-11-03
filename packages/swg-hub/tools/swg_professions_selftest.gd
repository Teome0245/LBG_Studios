extends SceneTree
## Self-test des 33 Professions SWG Pre-CU (Arbres 4x4 & 250 Skill Points).
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/swg-hub \
##     -s res://tools/swg_professions_selftest.gd

const ProfessionsScript := preload("res://scripts/swg_professions_service.gd")

func _init() -> void:
	print("[swg_professions_selftest] Début du test des 33 Professions Pre-CU & 250 Skill Points...")

	var svc = ProfessionsScript.new()
	assert(svc != null, "Échec instanciation SwgProfessionsService")
	svc.setup("res://data/swg_precu_professions.json")

	assert(svc.professions_catalog.size() >= 32, "Le catalogue doit indexer au moins 32 professions SWG Pre-CU")
	assert(svc.skills_by_id.size() >= 550, "Le catalogue doit compter plus de 550 boîtes de compétences")

	var player_id := "Pionnier_PreCU_01"
	var profile := svc.get_or_create_profile(player_id)
	assert(profile["points_remaining"] == 250, "Le joueur doit débuter avec 250 Skill Points")

	# 1. Apprentissage Novice Marksman (Métier de Base)
	var res_nov := svc.learn_skill(player_id, "marksman_novice")
	assert(bool(res_nov.get("ok")) == true, "Novice Marksman doit être appris sans prérequis")
	assert(res_nov["points_remaining"] == 235, "Novice Marksman (15 pts) doit laisser 235 points restants")

	# 2. Progression dans la branche Fusils (Rifles I -> II -> III -> IV)
	# Tenter Rifles II sans Rifles I doit échouer
	var fail_check := svc.can_learn_skill(player_id, "marksman_rifle_02")
	assert(bool(fail_check.get("ok")) == false, "Rifles II ne doit pas être accessible sans Rifles I")

	var res_r1 := svc.learn_skill(player_id, "marksman_rifle_01")
	assert(bool(res_r1.get("ok")) == true, "Rifles I doit être appris")
	var res_r2 := svc.learn_skill(player_id, "marksman_rifle_02")
	assert(bool(res_r2.get("ok")) == true, "Rifles II doit être appris")
	var res_r3 := svc.learn_skill(player_id, "marksman_rifle_03")
	assert(bool(res_r3.get("ok")) == true, "Rifles III doit être appris")
	var res_r4 := svc.learn_skill(player_id, "marksman_rifle_04")
	assert(bool(res_r4.get("ok")) == true, "Rifles IV doit être appris")

	# 3. Déblocage du métier d'élite : Rifleman
	var res_elite := svc.learn_skill(player_id, "rifleman_novice")
	assert(bool(res_elite.get("ok")) == true, "Novice Rifleman doit être débloqué grâce à Marksman Rifles IV")

	# 4. Test de sécurité de l'abandon (Surrender Skill)
	# Tenter d'abandonner Rifles IV alors que Rifleman en dépend doit être bloqué
	var fail_surrender := svc.surrender_skill(player_id, "marksman_rifle_04")
	assert(bool(fail_surrender.get("ok")) == false, "Rifles IV ne peut pas être abandonné car Rifleman en dépend !")

	# Abandonner Novice Rifleman puis Rifles IV doit rembourser les points
	var pts_before: int = profile["points_remaining"]
	var ok_surrender_elite := svc.surrender_skill(player_id, "rifleman_novice")
	assert(bool(ok_surrender_elite.get("ok")) == true, "Rifleman Novice doit pouvoir être abandonné")
	assert(profile["points_remaining"] > pts_before, "Les points de compétence doivent être remboursés")

	var ok_surrender_r4 := svc.surrender_skill(player_id, "marksman_rifle_04")
	assert(bool(ok_surrender_r4.get("ok")) == true, "Rifles IV peut désormais être abandonné")

	print("SWG_PROFESSIONS_SELFTEST_OK: 33 Professions Pre-CU, 250 Skill Points, Déblocages d'Élites et Sécurité de Surrender validés !")
	quit(0)

