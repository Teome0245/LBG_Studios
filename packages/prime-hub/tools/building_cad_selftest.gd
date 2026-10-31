extends SceneTree
## building_cad_selftest.gd — Validation headless de la décomposition des blueprints CAO et du mobilier intérieur.
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/building_cad_selftest.gd

const HubBlueprintBuilderScript := preload("res://scripts/hub_blueprint_builder.gd")
const HubCollisionScript := preload("res://scripts/hub_collision.gd")


func _init() -> void:
	print("[*] Lancement du test HubBlueprintBuilder...")

	# Blueprint synthétique de test : 1 pièce de 10x10 avec 1 porte au Sud (largeur 2m) + mobilier
	var synthetic_bp := {
		"id": "poi:test_lab",
		"floors": [
			{
				"floor_index": 0,
				"walls": [
					# Mur Sud de x=-5 à x=5 à z=5, avec porte de 2m au milieu (offset=4.0)
					{
						"id": "wall_south",
						"start": [-5.0, 5.0],
						"end": [5.0, 5.0],
						"thickness_m": 0.4,
						"doors": [
							{"offset_m": 4.0, "width_m": 2.0}
						]
					},
					# Mur Nord plein de x=-5 à x=5 à z=-5
					{
						"id": "wall_north",
						"start": [-5.0, -5.0],
						"end": [5.0, -5.0],
						"thickness_m": 0.4,
						"doors": []
					}
				],
				"furniture": [
					{
						"id": "synthetic_bench_1",
						"kind": "craft_bench",
						"label": "Établi de test",
						"pos": [2.0, -1.0],
						"width_m": 3.0,
						"depth_m": 1.2,
						"interaction_type": "craft",
						"capacity": 2
					}
				]
			}
		]
	}

	var blocks: Array = HubBlueprintBuilderScript.blueprint_to_collision_blocks(synthetic_bp, 100.0, 200.0)
	print("  - Blocs de collision générés: %d" % blocks.size())

	# Le mur Nord plein doit faire 1 bloc
	# Le mur Sud avec porte doit être découpé en 2 sous-blocs (avant la porte et après la porte)
	# Total = 3 blocs
	assert(blocks.size() == 3, "Attendu 3 blocs de collision (1 Nord + 2 Sud découpés), reçu %d" % blocks.size())

	# Vérifier que le passage de la porte (au centre du mur Sud, x=100.0, z=205.0) est libre !
	var test_doorway := Vector2(100.0, 205.0)
	var blocked_in_doorway := false
	for b in blocks:
		if test_doorway.x >= b["min_x"] and test_doorway.x <= b["max_x"] and test_doorway.y >= b["min_z"] and test_doorway.y <= b["max_z"]:
			blocked_in_doorway = true
			break

	assert(not blocked_in_doorway, "Le point au milieu de la porte est bloqué par collision !")
	print("[+] PASS: Ouverture de porte franchissable validée (passage libre)")

	# Vérifier qu'un point sur le mur Nord (x=100.0, z=195.0) EST bloqué !
	var test_north_wall := Vector2(100.0, 195.0)
	var blocked_in_wall := false
	for b in blocks:
		if test_north_wall.x >= b["min_x"] and test_north_wall.x <= b["max_x"] and test_north_wall.y >= b["min_z"] and test_north_wall.y <= b["max_z"]:
			blocked_in_wall = true
			break

	assert(blocked_in_wall, "Le mur plein ne bloque pas !")
	print("[+] PASS: Collision de mur plein validée")

	# Test 2 : Extraction du mobilier et ancrages d'interaction
	var anchors: Array = HubBlueprintBuilderScript.blueprint_to_furniture_anchors(synthetic_bp, 100.0, 200.0)
	assert(anchors.size() == 1, "Attendu 1 ancrage de mobilier synthétique, reçu %d" % anchors.size())
	var a0: Dictionary = anchors[0]
	assert(a0.get("furn_id") == "synthetic_bench_1", "furn_id incorrect pour ancrage")
	assert(a0.get("id") == "poi:test_lab:synthetic_bench_1", "id qualifié incorrect pour ancrage")
	assert(a0.get("interaction_type") == "craft", "Type d'interaction incorrect")
	var a_pos: Vector3 = a0.get("pos", Vector3.ZERO)
	assert(is_equal_approx(a_pos.x, 102.0) and is_equal_approx(a_pos.z, 199.0), "Position monde de mobilier incorrecte")
	print("[+] PASS: Extraction d'ancrage de mobilier synthétique validée")

	# Test 3 : Intégration HubCollision avec les blueprints réels de Lost Heaven
	var collision = HubCollisionScript.new()
	var root := ProjectSettings.globalize_path("res://").rstrip("/")
	var buildings_path := root.path_join("../prime-client/assets/maps/lost_heaven_buildings.json")
	collision.reload(buildings_path)

	var total_anchors: Array = collision.get_furniture_anchors()
	print("  - Total ancrages mobilier chargés dans HubCollision: %d" % total_anchors.size())
	assert(total_anchors.size() >= 10, "Attendu au moins 10 pièces de mobilier chargées (cantina), reçu %d" % total_anchors.size())

	# Vérifier les filtres par interaction_type de la Cantina
	var drink_anchors: Array = collision.get_furniture_anchors("drink")
	var rest_anchors: Array = collision.get_furniture_anchors("rest")
	var sit_anchors: Array = collision.get_furniture_anchors("sit")
	var inspect_anchors: Array = collision.get_furniture_anchors("inspect")
	var loot_anchors: Array = collision.get_furniture_anchors("loot")

	assert(drink_anchors.size() >= 1, "Attendu au moins 1 ancrage drink (comptoir Jax)")
	assert(rest_anchors.size() >= 1, "Attendu au moins 1 ancrage rest (couchette)")
	assert(sit_anchors.size() >= 2, "Attendu au moins 2 ancrages sit (tabourets/tables)")
	assert(inspect_anchors.size() >= 1, "Attendu au moins 1 ancrage inspect (bureau)")
	assert(loot_anchors.size() >= 1, "Attendu au moins 1 ancrage loot (caisse contrebande)")
	print("[+] PASS: Filtres par interaction_type cantina validés (drink, rest, sit, inspect, loot)")

	# Vérifier find_anchor_near
	# Cantina est en (5028.3, -784.1)
	var cantina_center := Vector3(5028.3, 0.0, -784.1)
	var near_drink := collision.find_anchor_near(cantina_center, 35.0, "drink")
	assert(not near_drink.is_empty(), "Aucun ancrage drink trouvé près de la cantina")
	assert(near_drink.get("furn_id") == "cantina_bar_counter", "L'ancrage drink le plus proche devrait être le comptoir")
	print("[+] PASS: find_anchor_near pour cantina validé (%s)" % near_drink.get("label", ""))

	# Test 4 : Blueprint entrepôt dock (craft bench, storage rack, foreman desk)
	var warehouse_path := root.path_join("../prime-client/assets/maps/blueprints/poi_lost_heaven_warehouse_dock.json")
	var warehouse_bp := HubBlueprintBuilderScript.load_blueprint(warehouse_path)
	var wh_anchors := HubBlueprintBuilderScript.blueprint_to_furniture_anchors(warehouse_bp, 4850.0, -920.0)
	assert(wh_anchors.size() >= 4, "Attendu au moins 4 pièces de mobilier dans l'entrepôt, reçu %d" % wh_anchors.size())
	var wh_craft: Array = []
	for a in wh_anchors:
		if a.get("interaction_type") == "craft":
			wh_craft.append(a)
	assert(wh_craft.size() >= 1, "Attendu au moins 1 ancrage craft dans l'entrepôt")
	assert(wh_craft[0].get("furn_id") == "warehouse_craft_bench", "L'ancrage craft devrait être warehouse_craft_bench")
	print("[+] PASS: Blueprint entrepôt et atelier de craft validés (%s)" % wh_craft[0].get("label", ""))

	print("[+] HubBlueprintBuilder & HubCollision : Tous les tests passent avec succès !")
	quit(0)

