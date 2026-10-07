extends Node
## Entrée headless G5 — HTTP+WS unifiés :8787, peel natif (plus de Python).

const HubSimScript = preload("res://scripts/hub_sim.gd")
const HubWsScript = preload("res://scripts/hub_ws_server.gd")
const HubHttpScript = preload("res://scripts/hub_http.gd")
const HubAuthScript = preload("res://scripts/hub_auth.gd")
const HubEconomyScript = preload("res://scripts/hub_economy.gd")
const HubCatalogScript = preload("res://scripts/hub_catalog.gd")
const HubDialogueScript = preload("res://scripts/hub_dialogue.gd")

const TICK_HZ := 20.0
const DEFAULT_PORT := 8787

var sim: Node
var ws: Node
var http: Node
var auth
var economy
var catalog
var dialogue
var _accum: float = 0.0


func _ready() -> void:
	OS.low_processor_usage_mode = false

	var port := int(OS.get_environment("LBG_PRIME_HUB_WS_PORT"))
	if port <= 0:
		port = DEFAULT_PORT
	# Unify : HTTP sur le même port sauf override explicite différent
	var http_port := int(OS.get_environment("LBG_PRIME_HUB_HTTP_PORT"))
	if http_port <= 0:
		http_port = port

	auth = HubAuthScript.new()
	auth.setup()
	economy = HubEconomyScript.new()
	economy.setup()
	catalog = HubCatalogScript.new()
	dialogue = HubDialogueScript.new()
	dialogue.setup()

	sim = HubSimScript.new()
	sim.name = "HubSim"
	add_child(sim)
	sim.reset()

	http = HubHttpScript.new()
	http.name = "HubHttp"
	add_child(http)
	http.setup_services(auth, economy, catalog, dialogue)
	# Router only si même port que WS ; sinon écoute dédiée
	var listen_http := 0 if http_port == port else http_port
	if http.start(sim, listen_http, port) != OK:
		push_error("[prime-hub] abort: HTTP bind failed")
		get_tree().quit(1)
		return

	ws = HubWsScript.new()
	ws.name = "HubWs"
	add_child(ws)
	if ws.start(sim, port, http, auth) != OK:
		push_error("[prime-hub] abort: gateway bind failed")
		get_tree().quit(1)
		return

	var nblocks: int = 0
	if sim.collision != null:
		nblocks = int(sim.collision.blocks.size())
	print("[prime-hub] ready G5 — bots=%d npcs=%d collision=%d" % [sim.bot_count(), sim.npc_count(), nblocks])
	if listen_http == 0:
		print("[prime-hub] unified HTTP+WS on :%d (peel native)" % port)
	else:
		print("[prime-hub] WS :%d · HTTP :%d (peel native)" % [port, listen_http])


func _process(delta: float) -> void:
	_accum += delta
	var interval := 1.0 / TICK_HZ
	while _accum >= interval:
		_accum -= interval
		sim.step(interval)
		ws.flush_chat()
		ws.broadcast_zone_state()
