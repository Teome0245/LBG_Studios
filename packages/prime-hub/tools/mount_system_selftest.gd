extends SceneTree

## Selftest Automatisé du Système de Domptage & Montures (Mount System)
## Valide l'apprivoisement d'un Drake/Marcheur, l'invocation, la monte et la descente.

const HubSimScript = preload("res://scripts/hub_sim.gd")
const HubCreaturesScript = preload("res://scripts/hub_creatures.gd")
const HubSkillsScript = preload("res://scripts/hub_skills.gd")
const HubEconomyScript = preload("res://scripts/hub_economy.gd")

func _init() -> void:
	print("[*] Lancement du selftest Taming & Mount System (Creature Handler)...")

	var sim = HubSimScript.new()
	var eco = HubEconomyScript.new()
	var skills = HubSkillsScript.new()
	var creatures = HubCreaturesScript.new()

	skills.setup(eco)
	creatures.setup(sim, eco, skills, null, null)
	sim.creatures = creatures

	var player := "Dresseur_Test"
	eco._player(player)

	# 1. Vérification du bestiaire (Drake et Marcheur avec tag is_mountable)
	var drake_def: Dictionary = creatures.bestiary_by_id.get("beast:drake_des_sables", {})
	assert(not drake_def.is_empty(), "Le Drake des Sables doit exister dans le bestiaire")
	assert(bool(drake_def.get("is_mountable", false)) == true, "Le Drake doit être montable")
	assert(float(drake_def.get("mount_speed_mult", 1.0)) > 1.5, "Le Drake doit offrir un bonus de vitesse > 50%")
	print("[+] PASS: Définition du Drake des Sables montable validée (vitesse x%.2f)." % float(drake_def.get("mount_speed_mult", 1.0)))

	# 2. Spawn d'une bête sauvage et apprivoisement forcé
	var wild_eid := "wild_drake_99"
	sim.entities[wild_eid] = {
		"eid": wild_eid,
		"kind": "beast",
		"beast_id": "beast:drake_des_sables",
		"name": "Drake Sauvage",
		"pos": Vector3(10.0, 0.0, 10.0),
		"active": true
	}

	var tame_res: Dictionary = creatures.tame_creature(player, wild_eid, true)
	assert(bool(tame_res.get("ok", false)) == true, "Le domptage doit réussir")
	var pet_info: Dictionary = tame_res.get("pet", {})
	var pet_id: String = str(pet_info.get("pet_id", ""))
	assert(not pet_id.is_empty(), "Un pet_id valide doit être attribué")
	print("[+] PASS: Domptage du Drake réussi -> familier %s enregistré." % pet_id)

	# 3. Invocation du familier (Call Pet)
	var call_res: Dictionary = creatures.call_pet(player, pet_id, 12.0, 12.0)
	assert(bool(call_res.get("ok", false)) == true, "L'invocation du pet doit réussir")
	var active_eid: String = str(call_res.get("eid", ""))
	assert(sim.entities.has(active_eid), "L'entité pet doit être active dans la sim")
	print("[+] PASS: Invocation du pet validée sur le terrain.")

	# 4. Monter sur le Drake (Mount Pet)
	sim.entities[player] = {
		"eid": player,
		"kind": "player",
		"pos": Vector3(12.0, 0.0, 12.0),
		"active": true
	}
	var mount_res: Dictionary = creatures.mount_pet(player, pet_id)
	assert(bool(mount_res.get("ok", false)) == true, "L'action de monter doit réussir")
	assert(mount_res.get("outcome") == "mounted", "L'issue doit être 'mounted'")
	assert(float(mount_res.get("speed_mult", 1.0)) == float(drake_def.get("mount_speed_mult", 1.75)), "Le bonus de vitesse doit être appliqué")
	assert(str(sim.entities[player].get("mounted_pet_id", "")) == pet_id, "Le joueur doit être marqué comme chevauchant le pet")
	print("[+] PASS: Monture activée avec succès (+75% vitesse, état joueur synchronisé).")

	# 5. Descendre de la monture (Dismount Pet)
	var dismount_res: Dictionary = creatures.dismount_pet(player, pet_id)
	assert(bool(dismount_res.get("ok", false)) == true, "La descente doit réussir")
	assert(dismount_res.get("outcome") == "dismounted", "L'issue doit être 'dismounted'")
	assert(float(sim.entities[player].get("speed_mult", 1.0)) == 1.0, "La vitesse joueur doit revenir à la normale")
	assert(str(sim.entities[player].get("mounted_pet_id", "")).is_empty(), "Le joueur ne doit plus avoir de monture active")
	print("[+] PASS: Descente de monture validée, vitesse réinitialisée.")

	print("[+] TOUS LES TESTS DU SYSTÈME DE MONTURES SONT VERTS (100% SUCCÈS) !")
	quit(0)
