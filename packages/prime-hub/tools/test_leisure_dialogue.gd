extends SceneTree

const HubDialogueScript := preload("res://scripts/hub_dialogue.gd")
const HubSimScript := preload("res://scripts/hub_sim.gd")
const HubEconomyScript := preload("res://scripts/hub_economy.gd")

func _init() -> void:
	print("[*] Test Dialogue Redirection PNJ en Loisir...")

	var economy = HubEconomyScript.new()
	economy.setup()

	var sim = HubSimScript.new()
	sim.attach_economy(economy)
	sim.reset()

	var dialogue = HubDialogueScript.new()
	dialogue.setup()
	dialogue.attach_sim(sim)

	assert(sim.life != null, "HubLife doit être initialisé dans sim")
	assert(sim.life._sched.size() > 0, "Le planning des triplons doit contenir des entités")

	# Trouver un PNJ en loisir et son collègue au travail
	var leisure_eid := ""
	var worker_eid := ""
	var triplon_id := ""

	for eid in sim.life._sched.keys():
		var entry: Dictionary = sim.life._sched[eid]
		if str(entry.get("phase", "")) == "leisure":
			leisure_eid = eid
			triplon_id = str(entry.get("triplon_id", ""))
			break

	assert(not leisure_eid.is_empty(), "Au moins un PNJ doit être en loisir (allow_leisure_citizens=true)")

	for eid in sim.life._sched.keys():
		var entry: Dictionary = sim.life._sched[eid]
		if str(entry.get("triplon_id", "")) == triplon_id and str(entry.get("phase", "")) == "work":
			worker_eid = eid
			break

	assert(not worker_eid.is_empty(), "Un membre du même triplon doit être en poste (phase=work)")

	var leisure_name: String = str(sim.life._sched[leisure_eid].get("meta", {}).get("name", leisure_eid))
	var worker_name: String = str(sim.life._sched[worker_eid].get("meta", {}).get("name", worker_eid))

	print("[+] PNJ en loisir trouvé: %s (%s)" % [leisure_name, leisure_eid])
	print("[+] PNJ au travail trouvé: %s (%s)" % [worker_name, worker_eid])

	# 1. Dialogue avec le PNJ en loisir
	var res_leisure := dialogue.invoke({
		"world_npc_id": leisure_eid,
		"text": "bonjour"
	})
	assert(bool(res_leisure.get("ok", false)) == true, "Invoke dialogue doit réussir")
	var reply_leisure: String = str(res_leisure.get("reply", ""))
	print("[+] Réponse reçue du PNJ en loisir :")
	print("    « %s »" % reply_leisure)

	assert(reply_leisure.find(worker_name) >= 0, "La réponse doit mentionner le collègue actif (%s)" % worker_name)
	assert(reply_leisure.find("quartier libre") >= 0 or reply_leisure.find("pas de service") >= 0, "Doit mentionner qu'il n'est pas de service")

	var moves: Array = res_leisure.get("suggested_moves", [])
	assert(moves.size() >= 2, "Doit proposer au moins 2 choix d'action (reçu %d)" % moves.size())
	var has_where := false
	var has_break := false
	for m in moves:
		var lbl: String = str(m.get("label", ""))
		if lbl.find("Où trouver") >= 0 and lbl.find(worker_name) >= 0:
			has_where = true
		if lbl.find("Bonne pause") >= 0:
			has_break = true
	assert(has_where, "Option 'Où trouver %s ?' attendue" % worker_name)
	assert(has_break, "Option 'Bonne pause !' attendue")

	# 2. Demande de localisation
	var res_loc := dialogue.invoke({
		"world_npc_id": leisure_eid,
		"text": "Où puis-je trouver %s ?" % worker_name
	})
	var reply_loc: String = str(res_loc.get("reply", ""))
	print("[+] Réponse localisation : « %s »" % reply_loc)
	assert(reply_loc.find(worker_name) >= 0, "Doit confirmer le nom")
	assert(reply_loc.find("assure le service") >= 0 or reply_loc.find("poste") >= 0, "Doit indiquer le lieu de service")

	# 3. Souhaiter bonne pause
	var res_break := dialogue.invoke({
		"world_npc_id": leisure_eid,
		"text": "Bonne pause à toi !"
	})
	var reply_break: String = str(res_break.get("reply", ""))
	print("[+] Réponse bonne pause : « %s »" % reply_break)
	assert(reply_break.find("Merci") >= 0, "Doit remercier chaleureusement")

	# 4. Vérification que le PNJ au travail répond normalement de service (pas de redirection)
	var res_work := dialogue.invoke({
		"world_npc_id": worker_eid,
		"text": "bonjour"
	})
	var reply_work: String = str(res_work.get("reply", ""))
	print("[+] Réponse reçue du PNJ en service : « %s »" % reply_work)
	assert(reply_work.find("quartier libre") == -1, "Le PNJ en service ne doit PAS dire qu'il est en quartier libre")

	print("\n>>> TOUS LES TESTS DE REDIRECTION PNJ EN LOISIR ONT RÉUSSI AVEC SUCCÈS ! <<<")
	quit(0)
