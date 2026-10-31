extends SceneTree
## rumor_propagation_selftest.gd — Validation headless de la propagation des rumeurs inter-villages (Ticket 2.2).
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/rumor_propagation_selftest.gd

const HubWikiScript := preload("res://scripts/hub_wiki.gd")
const HubBotAutonomyScript := preload("res://scripts/hub_bot_autonomy.gd")
const HubDialogueScript := preload("res://scripts/hub_dialogue.gd")


func _init() -> void:
	print("[*] Lancement du test Propagation des Rumeurs Inter-Villages (Ticket 2.2)...")

	# Test 1 : État initial et purge des rumeurs
	HubWikiScript.clear_rumors()
	assert(HubWikiScript.get_rumors().is_empty(), "Le pool de rumeurs doit être vide après clear")
	print("[+] PASS: Registre de rumeurs initialisé et propre")

	# Initialisation autonomie et points d'intérêt
	var autonomy = HubBotAutonomyScript.new()
	var test_pois := {
		"cantina": Vector3(5075.0, 0.15, -835.0),
		"plaza": Vector3(4939.0, 0.15, -932.0),
		"inn": Vector3(5120.0, 0.15, -780.0),
	}
	autonomy.setup(null, null, test_pois, null)

	# Test 2 : Acquisition de mémoire de voyage lors d'un déplacement à Zalem
	var bot_nix := {
		"name": "Nix",
		"pos": Vector3(-1200.0, 0.15, -550.0), # Centre avant-poste Zalem
		"goal": "outpost_zalem",
		"goal_id": "outpost_zalem",
		"play_mode": "explore",
		"travel_memory": [],
	}

	autonomy.on_arrival(bot_nix)
	var nix_mem: Array = bot_nix.get("travel_memory", [])
	assert(nix_mem.size() == 1, "Nix doit avoir enregistré 1 souvenir de voyage à Zalem")
	var nix_obs: Dictionary = nix_mem[0]
	assert(nix_obs.get("origin") == "outpost_zalem", "L'origine doit être outpost_zalem")
	assert(nix_obs.get("source_bot") == "Nix", "La source doit être Nix")
	assert(not str(nix_obs.get("text", "")).is_empty(), "L'observation ne doit pas être vide")
	print("  - Souvenir enregistré par Nix: [%s] %s" % [nix_obs.get("origin_label"), nix_obs.get("text")])
	print("[+] PASS: Acquisition de faits marquants à l'Avant-poste Zalem validée")

	# Test 3 : Acquisition de mémoire de voyage pour un second bot au Ksar Nomade
	var bot_lia := {
		"name": "Lia",
		"pos": Vector3(4950.0, 0.15, -3800.0), # Centre Ksar Nomade
		"goal": "outpost_ksar",
		"goal_id": "outpost_ksar",
		"play_mode": "explore",
		"travel_memory": [],
	}

	autonomy.on_arrival(bot_lia)
	var lia_mem: Array = bot_lia.get("travel_memory", [])
	assert(lia_mem.size() == 1, "Lia doit avoir enregistré 1 souvenir au Ksar Nomade")
	var lia_obs: Dictionary = lia_mem[0]
	assert(lia_obs.get("origin") == "outpost_ksar", "L'origine doit être outpost_ksar")
	assert(lia_obs.get("source_bot") == "Lia", "La source doit être Lia")
	print("  - Souvenir enregistré par Lia: [%s] %s" % [lia_obs.get("origin_label"), lia_obs.get("text")])
	print("[+] PASS: Acquisition de faits marquants au Ksar Nomade validée")

	# Test 4 : Arrivée de Nix au Cantina La Perle -> transfert de la rumeur dans HubWiki
	bot_nix["pos"] = test_pois["cantina"]
	bot_nix["goal"] = "cantina"
	bot_nix["goal_id"] = "cantina"
	autonomy.on_arrival(bot_nix)

	assert(bot_nix.get("travel_memory", []).is_empty(), "La mémoire de Nix doit avoir été déchargée au hub")
	var active_rumors: Array = HubWikiScript.get_rumors()
	assert(active_rumors.size() == 1, "HubWiki doit désormais contenir 1 rumeur active")
	assert(active_rumors[0].get("source_bot") == "Nix", "La rumeur doit mentionner Nix")
	print("[+] PASS: Transfert et injection de rumeur au Cantina validés")

	# Transfert de Lia à la Plaza
	bot_lia["pos"] = test_pois["plaza"]
	bot_lia["goal"] = "plaza"
	bot_lia["goal_id"] = "plaza"
	autonomy.on_arrival(bot_lia)
	assert(HubWikiScript.get_rumors().size() == 2, "HubWiki doit contenir 2 rumeurs après l'arrivée de Lia")
	print("[+] PASS: Transfert multi-bots validé (2 rumeurs actives en circulation)")

	# Test 5 : Rendu Wiki Snapshot & Markdown
	var wiki = HubWikiScript.new()
	var snap: Dictionary = wiki.snapshot()
	assert(snap.has("rumors"), "Le snapshot wiki doit contenir la clé rumors")
	var snap_rumors: Array = snap.get("rumors", [])
	assert(snap_rumors.size() == 2, "Le snapshot wiki doit retourner les 2 rumeurs")

	var md: String = snap.get("markdown", "")
	assert("Rumeurs & Échos des Caravanes" in md, "Le markdown du wiki doit inclure la section des rumeurs")
	assert("Avant-poste Zalem" in md, "Le markdown doit mentionner l'Avant-poste Zalem")
	assert("Ksar Nomade" in md, "Le markdown doit mentionner le Ksar Nomade")
	assert("Nix" in md and "Lia" in md, "Les noms des bots voyageurs doivent figurer dans le guide")
	print("[+] PASS: Snapshot wiki et rendu Markdown avec échos de caravanes validés")

	# Test 6 : Intégration du Dialogue PNJ (Jax et Rumeuriste)
	var dialogue = HubDialogueScript.new()
	dialogue.setup()

	# Interrogation de Jax au sujet des rumeurs
	var res_jax: Dictionary = dialogue.invoke({
		"speaker": "player:1001",
		"text": "Tu as entendu des rumeurs récentes ?",
		"context": {
			"world_npc_id": "npc:core3_barman_jax",
			"world_npc_name": "Jax",
		}
	})
	var reply_jax: String = res_jax.get("reply", "")
	print("  - Réplique Jax (rumeur): %s" % reply_jax)
	assert("Jax :" in reply_jax, "Jax doit s'identifier")
	assert("Lia" in reply_jax or "Nix" in reply_jax, "Jax doit relayer une rumeur d'un bot voyageur")

	# Interrogation spécifique sur Zalem auprès du Rumeuriste
	var res_zalem: Dictionary = dialogue.invoke({
		"speaker": "player:1001",
		"text": "Quelles sont les nouvelles de Zalem ?",
		"context": {
			"world_npc_id": "npc:rumeuriste",
			"world_npc_name": "Rumeuriste",
		}
	})
	var reply_zalem: String = res_zalem.get("reply", "")
	print("  - Réplique Rumeuriste (Zalem): %s" % reply_zalem)
	assert("Zalem" in reply_zalem and "Nix" in reply_zalem, "Le Rumeuriste doit citer les échos de Zalem rapportés par Nix")

	print("[+] PASS: Intégration dynamique des rumeurs dans les dialogues PNJ validée")
	print("[+] Émergence Sociale & Rumeurs Inter-Villages (Ticket 2.2) : Tous les tests passent avec succès !")
	quit(0)
