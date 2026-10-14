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

	print("CLIENT_MODULAR_SELFTEST_OK: 4 modules + Inventory DnD (move/swap/stack) + Hotbar assign vérifiés avec succès")
	quit(0)
