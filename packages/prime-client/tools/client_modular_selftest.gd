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

	print("CLIENT_MODULAR_SELFTEST_OK: 4 modules initialisés avec succès sur main")
	quit(0)
