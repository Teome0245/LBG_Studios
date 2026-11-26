extends SceneTree
## generative_memory_selftest.gd — Validation headless de l'architecture Stanford Generative Agents (Smallville).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/generative_memory_selftest.gd

const HubDbScript := preload("res://scripts/hub_db.gd")
const HubGenerativeMemoryScript := preload("res://scripts/hub_generative_memory.gd")
const HubDialogueScript := preload("res://scripts/hub_dialogue.gd")


func _init() -> void:
	print("[*] Lancement du test Stanford Generative Agents (Mémoire, Retrieval & Réflexion)...")

	# Initialisation SQLite
	var db = HubDbScript.get_shared()
	assert(db != null and db.available, "La base SQLite doit être disponible")
	print("[+] PASS: Couche SQLite initialisée")

	# Nettoyage de la table pour les tests
	db.exec_sync("DELETE FROM npc_memories WHERE npc_id LIKE 'npc:test_%' OR npc_id = 'npc:core3_barman_jax';")

	# 1. Initialisation du service de mémoire générative
	var gen_svc = HubGenerativeMemoryScript.new()
	assert(gen_svc.setup(), "Le service de mémoire générative doit se charger avec succès")
	print("[+] PASS: Service HubGenerativeMemory initialisé")

	# 2. Vérification des cohortes (Phase 1 : 10 PNJ)
	assert(gen_svc.is_npc_eligible("npc:core3_barman_jax"), "Jax doit être éligible en Phase 1")
	assert(gen_svc.is_npc_eligible("npc:core3_daan_oth"), "Daan Oth doit être éligible en Phase 1")
	assert(gen_svc.is_npc_eligible("npc:capitaine_vael"), "Vael doit être éligible en Phase 1")
	assert(gen_svc.is_npc_eligible("npc:mecanicien_soren"), "Soren doit être éligible en Phase 1")
	assert(gen_svc.is_npc_eligible("npc:ancien_nadir"), "Nadir doit être éligible en Phase 1")
	assert(not gen_svc.is_npc_eligible("npc:fermier_valen"), "Valen Lars (Phase 2) ne doit pas être actif en Phase 1")
	print("[+] PASS: Cohorte Phase 1 (10 PNJ emblématiques) validée")

	# 3. Test Ingestion dans le Memory Stream (Jax le barman)
	var jax_id := "npc:core3_barman_jax"
	assert(gen_svc.record_event(jax_id, "Nix a demandé un verre d'eau filtrée et a parlé de la tempête.", 4, "observation", "eau,nix,tempete"), "Doit enregistrer le souvenir 1")
	assert(gen_svc.record_event(jax_id, "Une livraison d'eau de la caravane est arrivée avec du retard.", 7, "observation", "eau,caravane,retard"), "Doit enregistrer le souvenir 2")
	assert(gen_svc.record_event(jax_id, "Un voyageur a payé une tournée générale au comptoir.", 6, "observation", "comptoir,credit"), "Doit enregistrer le souvenir 3")

	# Forcer le flush SQLite
	db.wait_idle(2000)

	var count_rows: Array = db.query_rows("SELECT count(*) as total FROM npc_memories WHERE npc_id = '%s';" % jax_id)
	assert(not count_rows.is_empty() and int(count_rows[0].get("total", 0)) == 3, "Il doit y avoir 3 mémoires enregistrées pour Jax")
	print("[+] PASS: Enregistrement dans le Memory Stream validé (3 observations)")

	# 4. Test Retrieval pondéré de Stanford (Récence + Importance + Pertinence)
	var retrieved_water := gen_svc.retrieve_memories(jax_id, "Tu as de l'eau en stock pour les voyageurs ?", 2)
	assert(retrieved_water.size() == 2, "Doit récupérer 2 mémoires")
	var top_mem: Dictionary = retrieved_water[0]
	assert("eau" in str(top_mem.get("content", "")).to_lower(), "Le souvenir le plus pertinent doit mentionner l'eau")
	assert(float(top_mem.get("score", 0.0)) > 1.0, "Le score de Stanford doit être calculé et supérieur à 1.0")
	print("  - Top mémoire extraite : [%s] (Score: %.2f, Pertinence: %.2f)" % [top_mem.get("content"), top_mem.get("score"), top_mem.get("relevance")])
	print("[+] PASS: Retrieval pondéré de Stanford validé")

	# 5. Test Cycle de Réflexion (Pensée d'ordre supérieur)
	# Injecter assez de souvenirs pour dépasser le seuil de 35 points d'importance
	gen_svc.record_event(jax_id, "Les filtres du distillateur numéro 2 sont encrassés.", 8, "observation", "filtre,panne")
	gen_svc.record_event(jax_id, "Le capitaine Vael a averti qu'un convoi a été attaqué.", 8, "observation", "vael,attaque")
	gen_svc.record_event(jax_id, "Le Ksar Nomade demande une aide d'urgence en pièces de rechange.", 8, "observation", "ksar,rechange")
	db.wait_idle(2000)

	var reflection_res := gen_svc.check_and_trigger_reflection(jax_id)
	assert(bool(reflection_res.get("reflected", false)), "La réflexion doit se déclencher car le seuil est atteint")
	print("  - Synthèse de réflexion générée : %s" % reflection_res.get("reflection"))
	db.wait_idle(2000)

	# Vérifier qu'une mémoire de type 'reflection' d'importance 9 a été insérée
	var refl_rows: Array = db.query_rows("SELECT * FROM npc_memories WHERE npc_id = '%s' AND event_type = 'reflection';" % jax_id)
	assert(not refl_rows.is_empty(), "Une mémoire de type reflection doit exister dans SQLite")
	assert(int(refl_rows[0].get("importance", 0)) == 9, "L'importance de la réflexion doit être de 9")
	print("[+] PASS: Cycle de Réflexion Stanford validé (Pensée d'ordre supérieur créée)")

	# 6. Test d'intégration avec HubDialogue
	var dialogue = HubDialogueScript.new()
	dialogue.setup()
	var dial_res := dialogue.invoke({
		"world_npc_id": "npc:core3_barman_jax",
		"npc_name": "Jax Moro",
		"text": "Jax, as-tu des nouvelles de la dernière caravane d'eau ?",
		"player": "Teome"
	})
	assert(dial_res.get("ok") == true, "Le dialogue doit répondre avec succès")
	var dial_meta: Dictionary = dial_res.get("meta", {})
	assert(dial_meta.get("generative_memory_active") == true, "La mémoire générative doit être active pour Jax")
	var gen_mems: Array = dial_meta.get("generative_memories", [])
	assert(not gen_mems.is_empty(), "Des souvenirs génératifs doivent être injectés dans la métadonnée de dialogue")
	print("  - Réplique générée : %s" % dial_res.get("reply"))
	print("[+] PASS: Intégration de bout en bout HubDialogue <-> HubGenerativeMemory validée")

	print("\n>>> TOUS LES TESTS STANFORD GENERATIVE AGENTS SONT AU VERT (PASS) <<<")
	db.shutdown()
	quit(0)
