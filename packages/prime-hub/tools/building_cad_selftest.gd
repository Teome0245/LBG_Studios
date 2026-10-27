extends SceneTree
## building_cad_selftest.gd — Validation headless de la décomposition des blueprints CAO.
##
## Usage:
##   packages/prime-hub/tools/Godot_v4.6.3-stable_linux.x86_64 --headless \
##     --path packages/prime-hub -s res://tools/building_cad_selftest.gd

const HubBlueprintBuilderScript := preload("res://scripts/hub_blueprint_builder.gd")


func _init() -> void:
	print("[*] Lancement du test HubBlueprintBuilder...")

	# Blueprint synthétique de test : 1 pièce de 10x10 avec 1 porte au Sud (largeur 2m)
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
	# Mur Sud : p1=(-5, 5), p2=(5, 5). norm=(1, 0).
	# Porte : offset=4.0 -> x relatif de -1.0 à +1.0 (soit x monde de 99.0 à 101.0).
	# Un point en x=100.0, z=205.0 ne doit être dans AUCUN bloc !
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

	print("[+] HubBlueprintBuilder : Tous les tests passent avec succès !")
	quit(0)
