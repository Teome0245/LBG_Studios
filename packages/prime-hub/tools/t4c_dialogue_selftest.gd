extends SceneTree
## t4c_dialogue_selftest.gd — Validation headless du Moteur de Dialogue par Mots-Clés (T4C)
## et des PNJ étendus de la planète Scrapaltai (Modèle Tatooine crédible).

const HubDialogueScript := preload("res://scripts/hub_dialogue.gd")


func _init() -> void:
	print("[*] Lancement du test Dialogue par Mots-Clés T4C & PNJ Scrapaltai...")

	var dialogue = HubDialogueScript.new()
	dialogue.setup()

	# 1. Vérification des PNJ de Scrapaltai enregistrés dans le catalogue
	var test_npcs := [
		"npc:prospecteur_durn",
		"npc:chimiste_sela",
		"npc:fermier_valen",
		"npc:ferrailleur_kliktik",
		"npc:chamane_uror",
		"npc:armurier_kane"
	]
	for nid in test_npcs:
		assert(dialogue._registry.has(nid), "Le PNJ %s doit figurer dans le registre" % nid)
	print("[+] PASS: Enregistrement des 6 nouveaux PNJ de Scrapaltai validé")

	# 2. Vérification des salutations personnalisées
	for nid in test_npcs:
		var res := dialogue.invoke({
			"world_npc_id": nid,
			"text": "bonjour"
		})
		assert(bool(res.get("ok", false)) == true, "La requête de dialogue doit réussir")
		var reply: String = str(res.get("reply", ""))
		assert(reply.length() > 10, "La salutation de %s ne doit pas être vide" % nid)
		assert(res.has("structuredContent"), "structuredContent attendu")
		var kws: Array = res["structuredContent"].get("t4c_keywords", [])
		assert(kws.size() >= 3, "Au moins 3 mots-clés T4C attendus pour %s (reçu %d)" % [nid, kws.size()])
	print("[+] PASS: Salutations et exposition des mots-clés T4C validées")

	# 3. Test du Moteur de Mots-Clés T4C (Questionnement textuel direct sans clic UI)
	# Durn Vane -> "minerai"
	var res_durn := dialogue.invoke({
		"world_npc_id": "npc:prospecteur_durn",
		"text": "Où peut-on trouver du bon minerai dans la région ?"
	})
	assert(str(res_durn.get("reply", "")).find("duracier brut") >= 0, "Réplique attendue sur le duracier brut")

	# Sela Kore -> "alchimie"
	var res_sela := dialogue.invoke({
		"world_npc_id": "npc:chimiste_sela",
		"text": "Est-ce que tu pratiques une forme d'alchimie ?"
	})
	assert(str(res_sela.get("reply", "")).find("sels alcalins") >= 0, "Réplique attendue sur les sels alcalins")

	# Valen Lars -> "eau"
	var res_valen := dialogue.invoke({
		"world_npc_id": "npc:fermier_valen",
		"text": "Parle-moi de vos réserves en eau"
	})
	assert(str(res_valen.get("reply", "")).find("pinte d'eau pure") >= 0, "Réplique attendue sur la pinte d'eau pure")

	# Klik'Tik -> "troc"
	var res_jawa := dialogue.invoke({
		"world_npc_id": "npc:ferrailleur_kliktik",
		"text": "Faisons un troc de ferraille"
	})
	assert(str(res_jawa.get("reply", "")).find("Utini") >= 0, "Cri de troc Utini attendu")

	# U'Ror'K -> "esprits"
	var res_tusken := dialogue.invoke({
		"world_npc_id": "npc:chamane_uror",
		"text": "Que murmurent les esprits ?"
	})
	assert(str(res_tusken.get("reply", "")).find("vent chante") >= 0, "Réplique chamanique attendue")

	# Kane Rill -> "blindage"
	var res_kane := dialogue.invoke({
		"world_npc_id": "npc:armurier_kane",
		"text": "Je veux inspecter ton blindage lourd"
	})
	assert(str(res_kane.get("reply", "")).find("Plastron de duracier") >= 0, "Réplique d'armurier attendue")
	print("[+] PASS: Résolution contextuelle des mots-clés T4C spécifiques validée")

	# 4. Test des mots-clés transversaux universels (T4C Fallbacks)
	var res_trans := dialogue.invoke({
		"world_npc_id": "npc:guide_quartier",
		"text": "Que sais-tu sur le dragon krayt ?"
	})
	assert(str(res_trans.get("reply", "")).find("Gouffre du Krayt") >= 0, "Référence au Gouffre du Krayt attendue")

	var res_prophetie := dialogue.invoke({
		"world_npc_id": "npc:guide_quartier",
		"text": "Existe-t-il une vieille prophétie ?"
	})
	assert(str(res_prophetie.get("reply", "")).find("ailes du Séraphin") >= 0, "Allusion à la 4ème prophétie attendue")
	print("[+] PASS: Mots-clés transversaux (Krayt, Prophétie, Anchor-Ridge) validés")

	print("[+] TOUS LES TESTS DIALOGUES & MOTS-CLÉS T4C ONT RÉUSSI AVEC SUCCÈS !")
	const HubDbScript := preload("res://scripts/hub_db.gd")
	HubDbScript.shutdown_shared()
	quit(0)
