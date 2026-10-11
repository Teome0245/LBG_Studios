extends SceneTree
## Ticket 2.3 — self-test headless navmesh (aucun réseau requis).
##
## Usage:
##   packages/prime-hub/tools/godot --headless --path packages/prime-hub \
##     -s res://tools/nav_selftest.gd
##
## Vérifie : bake > 0 polys, map synchronisée, > 30 (ici 40) entités pouvant
## recalculer leur trajectoire au même tick sans budget, et le fallback hors bornes.

const HubCollisionScript := preload("res://scripts/hub_collision.gd")
const HubNavScript := preload("res://scripts/hub_nav.gd")

const POIS: Array = [
	Vector2(4749.0, -737.0),   # plaza
	Vector2(4809.0, -932.0),   # market
	Vector2(4740.0, -820.0),   # starport
	Vector2(4939.0, -802.0),   # cantina
	Vector2(4939.0, -932.0),   # board
	Vector2(4679.0, -672.0),   # clinic
	Vector2(4939.0, -672.0),   # train
	Vector2(4809.0, -672.0),   # inn
	Vector2(4679.0, -932.0),   # hall
	Vector2(5069.0, -802.0),   # craft
	Vector2(4305.0, -780.0),   # lodge_w
	Vector2(4749.0, -430.0),   # lodge_n
	Vector2(5245.0, -630.0),   # lodge_e
	Vector2(4860.0, -1185.0),  # lodge_s
]


func _init() -> void:
	var collision = HubCollisionScript.new()
	collision.reload()
	assert(collision.blocks.size() > 0, "collision blocks vides")

	var nav = HubNavScript.new()
	var ok: bool = nav.build(collision)
	assert(ok, "navmesh build a échoué")
	var st: Dictionary = nav.stats()
	assert(st["polygons"] > 0, "navmesh sans polygone")
	assert(int(st["regions"]) >= 1, "aucune région enregistrée")
	print("nav stats: ", st)

	# 40 entités recalculent leur trajectoire au même tick (pas de budget).
	var entities := 40
	var t0 := Time.get_ticks_usec()
	var success := 0
	var total_wp := 0
	for i in range(entities):
		var a: Vector2 = POIS[i % POIS.size()]
		var b: Vector2 = POIS[(i * 5 + 3) % POIS.size()]
		if a == b:
			b = POIS[(i + 1) % POIS.size()]
		var route: Array = nav.find_path(a.x, a.y, b.x, b.y)
		if not route.is_empty():
			success += 1
			total_wp += route.size()
	var elapsed_us := Time.get_ticks_usec() - t0
	print("%d entités / tick — succès=%d total_wp=%d temps=%d us (%.1f us/entité)" % [
		entities, success, total_wp, elapsed_us, float(elapsed_us) / float(entities),
	])
	assert(success >= 31, "moins de 31 trajectoires calculées (%d)" % success)

	# Fallback : hors bornes → vide (l'appelant retombe sur l'A* grille).
	var off: Array = nav.find_path(4758.0, -545.0, 9000.0, 9000.0)
	assert(off.is_empty(), "hors bornes devrait renvoyer vide")

	# Cohérence : deux points proches sur sol libre → chemin non vide.
	var direct: Array = nav.find_path(4749.0, -700.0, 4809.0, -730.0)
	assert(not direct.is_empty(), "chemin court vide")

	nav.free_nav()
	print("NAV_SELFTEST_OK")
	quit()
