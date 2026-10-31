extends RefCounted
class_name HubCombat
## Système de bêtes et combat open-world (Boss, Meute, Telegraph, Aggro, Leash, Respawn, Loot) — Ticket 2.2.

const _HubPaths = preload("res://scripts/hub_paths.gd")

var sim = null
var _rng := RandomNumberGenerator.new()


func setup(parent_sim) -> void:
	sim = parent_sim
	_rng.randomize()


func _walkable_xz(x: float, z: float) -> Vector2:
	if sim == null:
		return Vector2(x, z)
	return sim._walkable_xz(x, z)


func _stream(kind: String, text: String, actor: String = "", zone: String = "", detail: Dictionary = {}) -> void:
	if sim != null:
		sim._stream(kind, text, actor, zone, detail)


func _enqueue_say(from_name: String, oid: int, text: String, source: String = "ia") -> void:
	if sim != null:
		sim.enqueue_say(from_name, oid, text, source)


func density_beast_count(density: String) -> int:
	match density.strip_edges().to_lower():
		"pack":
			return 3
		"patrol":
			return 2
		"low", "sparse":
			return 1
		_:
			return 1


func beast_respawn_delay_s(beast_id: String, zone_id: String) -> float:
	## Meute rapide ; boss sparse plus long.
	if "serpent" in beast_id or "titan" in beast_id or "hollow" in zone_id:
		return 90.0
	if "hunt" in zone_id:
		return 28.0
	return 45.0


func revive_density_beasts() -> void:
	if sim == null:
		return
	var now := Time.get_unix_time_from_system()
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "beast":
			continue
		if bool(e.get("active", true)):
			continue
		var at := float(e.get("respawn_at", 0.0))
		if at <= 0.0 or now < at:
			continue
		var hx := float(e.get("home_x", 0.0))
		var hz := float(e.get("home_z", 0.0))
		var wz := _walkable_xz(hx, hz)
		e["pos"] = Vector3(wz.x, 0.15, wz.y)
		e["target"] = Vector3.ZERO
		e["goal"] = "wander"
		e["active"] = true
		e["stuck_ticks"] = 0
		e.erase("aggro_eid")
		e.erase("respawn_at")


func ensure_density_beasts() -> void:
	## Spawn open-world depuis combat_density_lh.json (kind=beast, oid 920xxx).
	if sim == null:
		return
	var raw: Variant = _HubPaths.read_json(_HubPaths.data_file("combat_density_lh.json"))
	if typeof(raw) != TYPE_DICTIONARY:
		return
	var zones = raw.get("zones", [])
	if typeof(zones) != TYPE_ARRAY:
		return
	var oid_base := 920001
	var seq := 0
	for z in zones:
		if typeof(z) != TYPE_DICTIONARY:
			continue
		var engage := str(z.get("engage_surface", "none"))
		var dens := str(z.get("density", "sparse"))
		if engage != "hunt_yard" and dens in ["", "none"]:
			continue
		var beasts = z.get("beasts", [])
		if typeof(beasts) != TYPE_ARRAY or beasts.is_empty():
			continue
		var beast_id := str(beasts[0])
		var n := density_beast_count(dens if engage != "hunt_yard" else "pack")
		if engage != "hunt_yard":
			n = mini(n, 1)
		var p = z.get("pos", {})
		if typeof(p) != TYPE_DICTIONARY:
			continue
		var cx := float(p.get("x", 0))
		var cz := float(p.get("z", 0))
		var zone_id := str(z.get("id", "zone"))
		var label := str(z.get("label", beast_id))
		for i in range(n):
			var eid := "beast:%s:%d" % [zone_id.replace(":", "_"), i]
			if sim.entities.has(eid):
				continue
			var ox := cx + _rng.randf_range(-18.0, 18.0)
			var oz := cz + _rng.randf_range(-18.0, 18.0)
			var wz := _walkable_xz(ox, oz)
			var pos := Vector3(wz.x, 0.15, wz.y)
			var oid := oid_base + seq
			seq += 1
			var is_pack := engage == "hunt_yard" or dens == "pack"
			var is_boss := dens == "sparse" and ("titan" in beast_id or "serpent" in beast_id)
			sim.entities[eid] = {
				"eid": eid,
				"oid": oid,
				"kind": "beast",
				"name": "%s %d" % [label if engage == "hunt_yard" else beast_id.replace("beast:", "").replace("_", " "), i + 1],
				"beast_id": beast_id,
				"zone_id": zone_id,
				"pos": pos,
				"target": Vector3.ZERO,
				"speed": 2.4 if is_boss else (4.2 if is_pack else 3.2),
				"is_bot": false,
				"goal": "wander",
				"play_mode": "ring",
				"quest_id": str(z.get("quest_id", "")),
				"linger_until": 0.0,
				"stuck_ticks": 0,
				"home_x": pos.x,
				"home_z": pos.z,
				"wander_r": 28.0 if engage == "hunt_yard" else 22.0,
				"aggro_r": 38.0 if is_pack else (22.0 if is_boss else 28.0),
				"leash_r": 55.0 if is_pack else 40.0,
				"telegraph_s": 1.4 if is_boss else 0.0,
				"is_boss": is_boss,
				"ambient": "",
				"active": true,
			}


func nearest_player_xz(x: float, z: float, radius_m: float) -> Dictionary:
	## Joueur humain le plus proche (pas bot IA flotte).
	if sim == null:
		return {}
	var best: Dictionary = {}
	var best_d := INF
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "player":
			continue
		if bool(e.get("is_bot", false)):
			continue
		var p: Vector3 = e["pos"]
		var d := Vector2(p.x - x, p.z - z).length()
		if d <= radius_m and d < best_d:
			best_d = d
			best = e
	if best.is_empty():
		return {}
	return {"player": best, "dist": best_d}


func step_beast(beast: Dictionary, dt: float) -> void:
	## Wander + aggro joueur (leash home) — meute plus agressive, sparse/boss + telegraph.
	if not bool(beast.get("active", true)):
		return
	var speed: float = float(beast.get("speed", 0.0))
	if speed <= 0.0:
		return
	var pos: Vector3 = beast["pos"]
	var home_x := float(beast.get("home_x", pos.x))
	var home_z := float(beast.get("home_z", pos.z))
	var aggro_r := float(beast.get("aggro_r", 28.0))
	if sim != null and "world_clock" in sim and sim.world_clock != null and sim.world_clock.has_method("get_beast_aggro_mult"):
		aggro_r *= float(sim.world_clock.get_beast_aggro_mult())
	var leash_r := float(beast.get("leash_r", 45.0))
	var telegraph_s := float(beast.get("telegraph_s", 0.0))
	var from_home := Vector2(pos.x - home_x, pos.z - home_z).length()
	var goal := str(beast.get("goal", "wander"))
	if from_home > leash_r:
		beast["goal"] = "leash"
		beast["target"] = Vector3(home_x, 0.15, home_z)
		beast.erase("aggro_eid")
		beast.erase("telegraph_until")
		beast["ambient"] = ""
		goal = "leash"
	elif goal == "telegraph":
		var until := float(beast.get("telegraph_until", 0.0))
		if Time.get_unix_time_from_system() >= until:
			beast["goal"] = "aggro"
			beast["ambient"] = ""
			goal = "aggro"
		else:
			# Windup : immobile, face joueur
			var hit_t := nearest_player_xz(pos.x, pos.z, aggro_r * 1.2)
			if not hit_t.is_empty():
				var pp_t: Vector3 = hit_t["player"]["pos"]
				beast["target"] = Vector3(pp_t.x, 0.15, pp_t.z)
				beast["aggro_eid"] = str(hit_t["player"].get("eid", ""))
			return
	else:
		var hit := nearest_player_xz(pos.x, pos.z, aggro_r)
		if not hit.is_empty():
			var pl: Dictionary = hit["player"]
			var pp: Vector3 = pl["pos"]
			beast["aggro_eid"] = str(pl.get("eid", ""))
			beast["target"] = Vector3(pp.x, 0.15, pp.z)
			if telegraph_s > 0.0 and goal != "aggro" and goal != "telegraph":
				beast["goal"] = "telegraph"
				beast["telegraph_until"] = Time.get_unix_time_from_system() + telegraph_s
				var tline := "Le sable frémit — %s se dresse…" % str(beast.get("name", "la bête"))
				beast["ambient"] = tline
				_enqueue_say(str(beast.get("name", "Bête")), int(beast.get("oid", 0)), tline, "ia")
				return
			beast["goal"] = "aggro"
			speed = speed * (1.05 if bool(beast.get("is_boss", false)) else 1.15)
			goal = "aggro"
		elif goal in ["aggro", "leash", "telegraph"]:
			beast["goal"] = "wander"
			beast.erase("aggro_eid")
			beast.erase("telegraph_until")
			beast["ambient"] = ""
			if sim != null:
				beast["target"] = sim._pick_wander_target(beast)
			goal = "wander"
	goal = str(beast.get("goal", "wander"))
	if goal == "wander" or goal == "":
		if sim != null:
			sim._step_npc(beast, dt)
		return
	var target: Vector3 = beast.get("target", Vector3.ZERO)
	if target == Vector3.ZERO:
		if sim != null:
			beast["target"] = sim._pick_wander_target(beast)
			sim._step_npc(beast, dt)
		return
	var dx := target.x - pos.x
	var dz := target.z - pos.z
	var dist := sqrt(dx * dx + dz * dz)
	if goal == "leash" and dist < 2.0:
		beast["goal"] = "wander"
		if sim != null:
			beast["target"] = sim._pick_wander_target(beast)
		beast["stuck_ticks"] = 0
		return
	if goal == "aggro" and dist < 1.8:
		beast["stuck_ticks"] = 0
		return
	var step_len := minf(dist, speed * dt)
	var nx := pos.x + (dx / dist) * step_len
	var nz := pos.z + (dz / dist) * step_len
	if sim != null and sim.collision != null:
		var c: Vector2 = sim.collision.clamp_move(pos.x, pos.z, nx, nz) as Vector2
		nx = c.x
		nz = c.y
	var moved := Vector2(nx - pos.x, nz - pos.z).length()
	if moved < step_len * 0.15:
		beast["stuck_ticks"] = int(beast.get("stuck_ticks", 0)) + 1
		if int(beast["stuck_ticks"]) >= 5:
			var home := _walkable_xz(home_x, home_z)
			beast["pos"] = Vector3(home.x, pos.y, home.y)
			beast["goal"] = "wander"
			if sim != null:
				beast["target"] = sim._pick_wander_target(beast)
			beast.erase("aggro_eid")
			beast.erase("telegraph_until")
			beast["ambient"] = ""
			beast["stuck_ticks"] = 0
			return
	else:
		beast["stuck_ticks"] = 0
	beast["pos"] = Vector3(nx, pos.y, nz)


func beast_count() -> int:
	if sim == null:
		return 0
	var n := 0
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) == "beast" and bool(e.get("active", true)):
			n += 1
	return n


func beasts_snapshot() -> Dictionary:
	if sim == null:
		return {"ok": true, "count": 0, "beasts": [], "source": "prime_hub", "ticket": "P5b"}
	var rows: Array = []
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "beast":
			continue
		if not bool(e.get("active", true)):
			continue
		var p: Vector3 = e["pos"]
		rows.append({
			"entity_key": str(e.get("eid", eid)),
			"beast_id": str(e.get("beast_id", "")),
			"name": str(e.get("name", "")),
			"zone_id": str(e.get("zone_id", "")),
			"pos": [snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01)],
			"goal": str(e.get("goal", "wander")),
			"is_boss": bool(e.get("is_boss", false)),
			"telegraph_s": float(e.get("telegraph_s", 0.0)),
			"telegraph_until": float(e.get("telegraph_until", 0.0)),
			"ambient": str(e.get("ambient", "")),
			"aggro_r": float(e.get("aggro_r", 0.0)),
		})
	return {
		"ok": true,
		"count": rows.size(),
		"beasts": rows,
		"source": "prime_hub",
		"ticket": "P5b",
	}


func force_beast_telegraph(x: float, z: float, radius_m: float = 120.0, bosses_only: bool = true) -> Dictionary:
	if sim == null:
		return {"ok": false, "error": "sim_unavailable"}
	var best_eid := ""
	var best_d := INF
	var best: Dictionary = {}
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "beast" or not bool(e.get("active", true)):
			continue
		if bosses_only and not bool(e.get("is_boss", false)):
			continue
		var p: Vector3 = e["pos"]
		var d := Vector2(p.x - x, p.z - z).length()
		if d <= radius_m and d < best_d:
			best_d = d
			best_eid = eid
			best = e
	if best_eid.is_empty():
		return {
			"ok": false,
			"error": "no_boss_in_range" if bosses_only else "no_beast_in_range",
			"radius_m": radius_m,
			"source": "prime_hub",
		}
	var ts := float(best.get("telegraph_s", 1.4))
	if ts <= 0.0:
		ts = 1.4
	best["telegraph_s"] = ts
	best["goal"] = "telegraph"
	best["telegraph_until"] = Time.get_unix_time_from_system() + ts
	var tline := "Le sable frémit — %s se dresse…" % str(best.get("name", "la bête"))
	best["ambient"] = tline
	_enqueue_say(str(best.get("name", "Bête")), int(best.get("oid", 0)), tline, "ia")
	return {
		"ok": true,
		"entity_key": str(best.get("eid", best_eid)),
		"beast_id": str(best.get("beast_id", "")),
		"beast_name": str(best.get("name", "")),
		"goal": "telegraph",
		"telegraph_s": ts,
		"telegraph_until": float(best["telegraph_until"]),
		"ambient": tline,
		"distance_m": snappedf(best_d, 0.1),
		"is_boss": bool(best.get("is_boss", false)),
		"source": "prime_hub",
		"ticket": "P5b",
	}


func engage_nearest_beast(player: String, x: float, z: float, radius_m: float = 42.0) -> Dictionary:
	if sim == null:
		return {"ok": false, "error": "sim_unavailable"}
	var best_eid := ""
	var best_d := INF
	var best: Dictionary = {}
	for eid in sim.entities.keys():
		var e: Dictionary = sim.entities[eid]
		if str(e.get("kind", "")) != "beast" or not bool(e.get("active", true)):
			continue
		var p: Vector3 = e["pos"]
		var d := Vector2(p.x - x, p.z - z).length()
		if d <= radius_m and d < best_d:
			best_d = d
			best_eid = eid
			best = e
	if best_eid.is_empty():
		return {
			"ok": false,
			"error": "no_beast_in_range",
			"hint": "approche une meute (anneau / porte est)",
			"radius_m": radius_m,
			"source": "prime_hub",
		}
	var beast_id := str(best.get("beast_id", "beast:chacal_dore"))
	var zone_id := str(best.get("zone_id", ""))
	var name := str(best.get("name", beast_id))
	var delay := beast_respawn_delay_s(beast_id, zone_id)
	best["active"] = false
	best["goal"] = "dead"
	best["target"] = Vector3.ZERO
	best.erase("aggro_eid")
	best["respawn_at"] = Time.get_unix_time_from_system() + delay
	var hx := float(best.get("home_x", best["pos"].x))
	var hz := float(best.get("home_z", best["pos"].z))
	var home := _walkable_xz(hx, hz)
	best["pos"] = Vector3(home.x, 0.15, home.y)
	var loot: Array = [{"id": "fourrure_doree", "name": "Fourrure dorée", "qty": 1}]
	if "scarab" in beast_id or "obsidien" in beast_id:
		loot = [{"id": "obsidienne", "name": "Obsidienne", "qty": 1}]
	elif "scorpion" in beast_id:
		loot = [{"id": "venin", "name": "Venin", "qty": 1}]
	elif "serpent" in beast_id:
		loot = [{"id": "ecailles_dorees", "name": "Écailles dorées", "qty": 1}]
	var credits := 3
	if sim.economy != null and sim.economy.has_method("grant_world_loot"):
		sim.economy.grant_world_loot(player, loot, credits)
	var who := player if not player.is_empty() else "Voyageur"
	var is_boss := bool(best.get("is_boss", false))
	_stream(
		"beast.defeated",
		"%s a dispersé %s (%s)." % [who, name, beast_id],
		who,
		zone_id,
		{"beast_id": beast_id, "is_boss": is_boss, "beast_count": beast_count()}
	)
	if is_boss:
		_stream("world.boss_defeated", "Un boss a été abattu : %s." % name, who, zone_id, {"beast_id": beast_id})
	return {
		"ok": true,
		"player": who,
		"beast_id": beast_id,
		"beast_name": name,
		"zone_id": zone_id,
		"distance_m": snappedf(best_d, 0.1),
		"loot": loot,
		"credits_gained": credits,
		"respawn_s": delay,
		"beast_count": beast_count(),
		"source": "prime_hub",
	}
