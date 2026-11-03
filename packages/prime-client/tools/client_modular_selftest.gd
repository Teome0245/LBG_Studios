extends SceneTree
## Ticket 2.2 — Self-test headless du client Prime modulaire.
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/prime-client \
##     -s res://tools/client_modular_selftest.gd

const GameplayOpsScript := preload("res://scripts/client_gameplay_ops.gd")
const QuestOpsScript := preload("res://scripts/client_quest_ops.gd")
const NetWorldScript := preload("res://scripts/client_net_world.gd")
const UiDialogueScript := preload("res://scripts/client_ui_dialogue.gd")
const MainScript := preload("res://scripts/main.gd")

func _init() -> void:
	print("[client_selftest] début vérification des modules")

	var gops = GameplayOpsScript.new()
	assert(gops != null, "Échec instanciation GameplayOps")
	assert(gops.SALVAGE_RADIUS_M > 0.0, "Constante salvage invalide")

	var qops = QuestOpsScript.new()
	assert(qops != null, "Échec instanciation QuestOps")

	var nw = NetWorldScript.new()
	assert(nw != null, "Échec instanciation NetWorld")
	assert(nw.LOST_HEAVEN_HUB.x > 0.0, "Constante hub invalide")

	var uid = UiDialogueScript.new()
	assert(uid != null, "Échec instanciation UiDialogue")
	assert(uid.HUB_CHAT_MAX_LINES > 0, "Constante chat max lines invalide")

	var main_node = MainScript.new()
	assert(main_node != null, "Échec instanciation Main")
	main_node._init_modules()

	assert(main_node.gameplay_ops != null, "Sous-module gameplay_ops non initialisé")
	assert(main_node.quest_ops != null, "Sous-module quest_ops non initialisé")
	assert(main_node.net_world != null, "Sous-module net_world non initialisé")
	assert(main_node.ui_dialogue != null, "Sous-module ui_dialogue non initialisé")

	# Test InventoryPanel Drag & Drop
	var InventoryPanelScript := preload("res://scripts/inventory_panel.gd")
	var inv = InventoryPanelScript.new()
	assert(inv != null, "Échec instanciation InventoryPanel")
	inv._ensure_ui()
	var test_items: Array[Dictionary] = [
		{"id": "ferraille", "name": "Ferraille", "icon": "copper", "qty": 5},
		{"id": "vis", "name": "Vis", "icon": "screw", "qty": 3},
		{"id": "ferraille", "name": "Ferraille", "icon": "copper", "qty": 2},
	]
	inv._fill_from_items(test_items)
	assert(inv._items.size() >= 3, "Échec chargement items")

	# Test déplacement vers slot vide (0 -> 8)
	inv.swap_or_move_slots(0, 8)
	assert(inv._items[0].is_empty(), "Slot 0 devrait être vide après déplacement")
	assert(inv._items[8].get("id") == "ferraille" and inv._items[8].get("qty") == 5, "Slot 8 devrait contenir ferraille x5")

	# Test empilement (slot 8 ferraille x5 vers slot 2 ferraille x2 -> slot 2 ferraille x7)
	inv.swap_or_move_slots(8, 2)
	assert(inv._items[8].is_empty(), "Slot 8 devrait être vide après empilement")
	assert(inv._items[2].get("id") == "ferraille" and inv._items[2].get("qty") == 7, "Slot 2 devrait avoir qty 7 après empilement")

	# Test permutation (slot 1 vis x3 et slot 2 ferraille x7)
	inv.swap_or_move_slots(1, 2)
	assert(inv._items[1].get("id") == "ferraille", "Slot 1 devrait contenir ferraille après swap")
	assert(inv._items[2].get("id") == "vis", "Slot 2 devrait contenir vis après swap")

	# Test drag & drop virtuals
	var slot_btn = inv._grid.get_child(1)
	assert(slot_btn != null and slot_btn is Button, "Slot button manquant")
	var drag_data = slot_btn._get_drag_data(Vector2.ZERO)
	assert(typeof(drag_data) == TYPE_DICTIONARY, "Drag data invalide")
	assert(drag_data.get("type") == "inventory_slot", "Type de drag incorrect")
	assert(drag_data.get("from_index") == 1, "from_index incorrect")

	var target_btn = inv._grid.get_child(2)
	assert(target_btn._can_drop_data(Vector2.ZERO, drag_data) == true, "can_drop_data devrait être true sur un slot différent")
	assert(slot_btn._can_drop_data(Vector2.ZERO, drag_data) == false, "can_drop_data devrait être false sur le même slot")

	# Test Hotbar Drag & Drop assignment
	var HotbarScript := preload("res://scripts/hotbar.gd")
	var hotbar = HotbarScript.new()
	assert(hotbar != null, "Échec instanciation Hotbar")
	hotbar._build_slots()
	var tracker := {"received": false}
	hotbar.item_assigned.connect(func(idx: int, it: Dictionary) -> void:
		if idx == 2 and it.get("id") == "ferraille":
			tracker["received"] = true
	)
	hotbar.assign_item_to_slot(2, {"id": "ferraille", "name": "Ferraille", "icon": "copper", "qty": 7})
	assert(tracker["received"], "Signal item_assigned non reçu sur Hotbar")

	# Test Interface Joueur SWG Pre-CU (2D Top-Down) : 5 composants
	var SwgHamHudScript := preload("res://scripts/swg_ham_hud.gd")
	var ham_hud = SwgHamHudScript.new()
	ham_hud.apply_ham_payload({
		"ham": {
			"health": {"base_max": 1000, "wounds": 150, "buff": 200, "effective_max": 1050, "current": 980},
			"action": {"base_max": 1000, "wounds": 50, "buff": 0, "effective_max": 950, "current": 900},
			"mind": {"base_max": 1000, "wounds": 0, "buff": 300, "effective_max": 1300, "current": 1300},
			"battle_fatigue": 220,
		},
		"medical_efficiency_ratio": 0.82,
	})
	assert(ham_hud._bar_health.wounds == 150 and ham_hud._bar_mind.buff == 300, "Barres HAM SWG Wounds/Buffs incorrectes")
	assert(ham_hud._portrait_3d != null, "SwgPortrait3D doit être instancié dans SwgHamHud")
	assert(ham_hud._portrait_3d._viewport != null, "SubViewport 3D doit être présent")
	ham_hud.set_posture("Accroupi")
	assert(ham_hud._posture_label == "Accroupi" and ham_hud._combat_posture == "kneeling", "Posture joueur doit être mise à jour")
	ham_hud.apply_combat_status({
		"posture": "prone",
		"statuses": {"knockdown": 3.0, "dizzy": 5.0}
	})
	assert(ham_hud._combat_posture == "prone" and ham_hud._combat_statuses.has("knockdown"), "Statuts de combat SWG doivent être enregistrés")
	assert(ham_hud._sys_dock != null, "Dock Système Datapad doit être présent")
	ham_hud.set_target_entity("Odo Merr", "npc", 6.4)
	assert(ham_hud._target_box.visible == true, "Target Frame SWG doit être visible")

	var SwgRadialMenuScript := preload("res://scripts/swg_radial_menu.gd")
	var radial = SwgRadialMenuScript.new()
	var radial_tracker := {"action": ""}
	radial.radial_action_selected.connect(func(act: String, _ctx: Dictionary) -> void:
		radial_tracker["action"] = act
	)
	radial.open_at(Vector2(200, 200), {"kind": "npc", "name": "Lia (Cantina La Perle)"})
	assert(radial._current_options.size() >= 3, "Le menu radial SWG sur Lia doit proposer Examiner/Converse/Watch")
	radial.trigger_option(2)
	assert(radial_tracker["action"] == "watch_entertainer", "L'action radiale 3 sur Lia doit être watch_entertainer")

	# Test Radial Menu : Cadavres de bêtes (Harvesting Scout)
	var corpse_opts := radial.build_options_for_context({"kind": "corpse", "name": "Cadavre de Dune Crawler"})
	var corpse_actions := []
	for o in corpse_opts:
		corpse_actions.append(o.get("id"))
	assert("harvest_meat" in corpse_actions and "harvest_hide" in corpse_actions and "harvest_bone" in corpse_actions, "Menu radial cadavre doit proposer Dépecer Viande/Cuir/Os")

	# Test Radial Menu : Vendeur joueur & Structures
	var vendor_opts := radial.build_options_for_context({"kind": "vendor", "name": "Boutique d'Armures"})
	var vendor_actions := []
	for o in vendor_opts:
		vendor_actions.append(o.get("id"))
	assert("vendor_browse" in vendor_actions and "vendor_manage" in vendor_actions, "Menu radial vendeur doit proposer Boutique et Gestion")

	var house_opts := radial.build_options_for_context({"kind": "structure", "name": "Maison en pisé"})
	var house_actions := []
	for o in house_opts:
		house_actions.append(o.get("id"))
	assert("house_enter" in house_actions and "house_maintenance" in house_actions, "Menu radial maison doit proposer Entrer et Maintenance")

	# Test Radial Menu : Terrain (Camp scout et Postures)
	var ground_opts := radial.build_options_for_context({"kind": "ground", "name": "Dunes"})
	var ground_actions := []
	for o in ground_opts:
		ground_actions.append(o.get("id"))
	assert("deploy_camp" in ground_actions and "posture_kneel" in ground_actions and "posture_prone" in ground_actions, "Menu radial sol doit proposer Camp et Postures")

	var SwgSkillsPanelScript := preload("res://scripts/swg_skills_panel.gd")
	var skills_ui = SwgSkillsPanelScript.new()
	skills_ui._ensure_ui()
	skills_ui._apply_local_fallback()
	assert(skills_ui._grid_4x4.get_child_count() == 16, "La grille SWG Pre-CU doit afficher 4x4 = 16 boxes")

	var SwgSurveyPanelScript := preload("res://scripts/swg_survey_panel.gd")
	var survey_ui = SwgSurveyPanelScript.new()
	survey_ui._ensure_ui()
	survey_ui._apply_local_fallback()
	assert(survey_ui._spawns_list.item_count >= 2, "Le Survey Tool SWG doit lister les gisements actifs")

	var SwgExperimentPanelScript := preload("res://scripts/swg_experiment_panel.gd")
	var exp_ui = SwgExperimentPanelScript.new()
	exp_ui.open_with_session({
		"session_id": "exp_local_test",
		"schematic_id": "mechatronic_repair_kit",
		"serial": "LH-2001",
		"remaining_points": 4,
		"max_points": 4,
		"attributes": {"quality_pct": 66.0, "power": 90, "durability": 410},
	})
	var exp_out: Dictionary = exp_ui.spend_points("power", 2)
	assert(bool(exp_out.get("ok", false)) == true and int(exp_out.get("remaining_points", -1)) == 2, "L'atelier d'expérimentation SWG doit dépenser 2 points et augmenter power")

	print("CLIENT_MODULAR_SELFTEST_OK: 4 modules + Inventory DnD + Hotbar + 5 Composants UI SWG Pre-CU 2D vérifiés avec succès")
	quit(0)
