extends RefCounted
class_name HubCaravan
## Caravane marchande itinérante du désert de Scrapaltai (Circuit Est & Inter-Villages).
## Fait la navette continue : Porte Est Lost Heaven -> Poste Guet -> Oasis Al-Khali -> Canyon -> Ksar de l'Oasis -> Zalem -> Lost Heaven.

const LEADER_EID := "npc:caravan_leader"
const LEADER_OID := 930001
const LEADER_NAME := "Meneur de convoi"

const MERCHANT_EID := "npc:caravan_merchant"
const MERCHANT_OID := 930002
const MERCHANT_NAME := "Marchand caravanier"

const BEAST_EID := "npc:caravan_beast"
const BEAST_OID := 930003
const BEAST_NAME := "Bête de somme"

const GUARD_EID := "npc:caravan_guard"
const GUARD_OID := 930004
const GUARD_NAME := "Garde de caravane"

const CARAVAN_SPEED := 8.0 # Vitesse de marche régulière

## Circuit des waypoints planétaires avec temps de halte optionnel (halte_s)
const WAYPOINTS: Array = [
	{"pos": Vector3(5813.6, 0.15, -982.5),  "label": "Porte Est Lost Heaven", "halte_s": 25.0},
	{"pos": Vector3(6050.0, 0.15, -1060.0), "label": "Piste des Dunes Est"},
	{"pos": Vector3(6350.0, 0.15, -1180.0), "label": "Contournement Barkhanes"},
	{"pos": Vector3(6650.0, 0.15, -1380.0), "label": "Poste de Guet des Dunes", "halte_s": 20.0},
	{"pos": Vector3(6820.0, 0.15, -1680.0), "label": "Passe du Massif Oriental"},
	{"pos": Vector3(6800.0, 0.15, -2050.0), "label": "Descente vers l'Oasis"},
	{"pos": Vector3(6550.0, 0.15, -2480.0), "label": "Oasis d'Al-Khali — Étape", "halte_s": 35.0},
	{"pos": Vector3(6250.0, 0.15, -2820.0), "label": "Piste sablonneuse Sud"},
	{"pos": Vector3(5650.0, 0.15, -3250.0), "label": "Canyon des Épaves", "halte_s": 20.0},
	{"pos": Vector3(5100.0, 0.15, -3580.0), "label": "Approche du Ksar"},
	{"pos": Vector3(4950.0, 0.15, -3700.0), "label": "Place du Ksar de l'Oasis", "halte_s": 40.0},
	{"pos": Vector3(3900.0, 0.15, -3400.0), "label": "Traversière Ouest"},
	{"pos": Vector3(2300.0, 0.15, -2650.0), "label": "Bassin Occidental"},
	{"pos": Vector3(500.0,  0.15, -1650.0), "label": "Route rouge sud"},
	{"pos": Vector3(-1200.0, 0.15, -550.0),  "label": "Avant-poste Zalem", "halte_s": 35.0},
	{"pos": Vector3(350.0,  0.15, -600.0),  "label": "Route Impériale Ouest"},
	{"pos": Vector3(2100.0, 0.15, -700.0),  "label": "Passe de Lost Heaven"},
	{"pos": Vector3(3688.9, 0.15, -675.9),  "label": "Porte Ouest Lost Heaven"},
	{"pos": Vector3(4859.3, 0.15, -1008.3), "label": "Marché de Lost Heaven", "halte_s": 30.0},
]

var cur_wp_idx: int = 0
var halte_until: float = 0.0
var _last_stream_step: int = -1

func clear() -> void:
	cur_wp_idx = 0
	halte_until = 0.0
	_last_stream_step = -1

func setup(sim) -> void:
	if sim == null:
		return
	_ensure_caravan_entities(sim)

func _ensure_caravan_entities(sim) -> void:
	var wp: Dictionary = WAYPOINTS[cur_wp_idx]
	var p: Vector3 = wp["pos"]

	var defs := [
		{"eid": LEADER_EID, "oid": LEADER_OID, "name": LEADER_NAME, "off": Vector3.ZERO, "ambient": "En route vers la prochaine étape — suivez la piste balisée."},
		{"eid": BEAST_EID, "oid": BEAST_OID, "name": BEAST_NAME, "off": Vector3(3.5, 0, 1.5), "ambient": "La bête de bât porte les ballots de tissu et d'épices du désert."},
		{"eid": MERCHANT_EID, "oid": MERCHANT_OID, "name": MERCHANT_NAME, "off": Vector3(6.5, 0, 2.5), "ambient": "Marchandises de l'Oasis et pièces de récupération. Troc direct au convoi !"},
		{"eid": GUARD_EID, "oid": GUARD_OID, "name": GUARD_NAME, "off": Vector3(9.5, 0, 3.5), "ambient": "La passe est sous surveillance. Les chacals n'approchent pas du convoi."},
	]

	for d in defs:
		var eid: String = d["eid"]
		if not sim.entities.has(eid):
			sim.entities[eid] = {
				"eid": eid,
				"oid": int(d["oid"]),
				"kind": "npc",
				"name": str(d["name"]),
				"pos": p + (d["off"] as Vector3),
				"target": p,
				"speed": CARAVAN_SPEED,
				"is_bot": false,
				"goal": "caravan_patrol",
				"play_mode": "caravan",
				"ambient": str(d["ambient"]),
				"active": true
			}

func tick(sim, dt: float) -> void:
	if sim == null or WAYPOINTS.is_empty():
		return
	_ensure_caravan_entities(sim)

	var now := Time.get_unix_time_from_system()
	if now < halte_until:
		return

	var leader = sim.entities.get(LEADER_EID)
	if leader == null:
		return

	var wp: Dictionary = WAYPOINTS[cur_wp_idx]
	var target_pos: Vector3 = wp["pos"]
	var l_pos: Vector3 = leader["pos"]

	var dx := target_pos.x - l_pos.x
	var dz := target_pos.z - l_pos.z
	var dist := sqrt(dx * dx + dz * dz)

	if dist <= 8.0:
		# Arrivé au waypoint actuel
		var halte_s: float = float(wp.get("halte_s", 0.0))
		if halte_s > 0.0:
			halte_until = now + halte_s
			var lbl: String = str(wp.get("label", "étape"))
			if sim.has_method("_stream") and cur_wp_idx != _last_stream_step:
				_last_stream_step = cur_wp_idx
				sim._stream("caravan.halte", "La Caravane marchande fait étape à : %s." % lbl, LEADER_NAME, "scrapaltai")

		# Passage au waypoint suivant
		cur_wp_idx = (cur_wp_idx + 1) % WAYPOINTS.size()
		wp = WAYPOINTS[cur_wp_idx]
		target_pos = wp["pos"]
		dx = target_pos.x - l_pos.x
		dz = target_pos.z - l_pos.z
		dist = sqrt(dx * dx + dz * dz)

	# Avancement du convoi en file indienne
	var dir := Vector3(dx, 0.0, dz).normalized()
	leader["target"] = target_pos
	leader["pos"] = l_pos + dir * (CARAVAN_SPEED * dt)

	# Les suiveurs suivent le leader en échelon
	var members := [
		{"eid": BEAST_EID, "dist": 4.5},
		{"eid": MERCHANT_EID, "dist": 8.0},
		{"eid": GUARD_EID, "dist": 12.0},
	]

	for m in members:
		var eid: String = m["eid"]
		if sim.entities.has(eid):
			var follower: Dictionary = sim.entities[eid]
			var f_target: Vector3 = leader["pos"] - dir * float(m["dist"])
			var f_pos: Vector3 = follower["pos"]
			var f_diff := f_target - f_pos
			f_diff.y = 0.0
			var f_d := f_diff.length()
			if f_d > 0.5:
				var f_dir := f_diff / f_d
				var f_speed := CARAVAN_SPEED * (1.2 if f_d > float(m["dist"]) + 2.0 else 1.0)
				follower["pos"] = f_pos + f_dir * (f_speed * dt)
				follower["target"] = f_target
