extends Node
## Entrée headless — WS :8787 + HTTP :8789 (proxy peel) + A* bots.

const HubSimScript = preload("res://scripts/hub_sim.gd")
const HubWsScript = preload("res://scripts/hub_ws_server.gd")
const HubHttpScript = preload("res://scripts/hub_http.gd")

const TICK_HZ := 20.0
const DEFAULT_WS_PORT := 8787
const DEFAULT_HTTP_PORT := 8789

var sim: Node
var ws: Node
var http: Node
var _accum: float = 0.0


func _ready() -> void:
	OS.low_processor_usage_mode = false

	var ws_port := int(OS.get_environment("LBG_PRIME_HUB_WS_PORT"))
	if ws_port <= 0:
		ws_port = DEFAULT_WS_PORT
	var http_port := int(OS.get_environment("LBG_PRIME_HUB_HTTP_PORT"))
	if http_port <= 0:
		http_port = DEFAULT_HTTP_PORT

	sim = HubSimScript.new()
	sim.name = "HubSim"
	add_child(sim)
	sim.reset()

	ws = HubWsScript.new()
	ws.name = "HubWs"
	add_child(ws)
	if ws.start(sim, ws_port) != OK:
		push_error("[prime-hub] abort: WS bind failed")
		get_tree().quit(1)
		return

	http = HubHttpScript.new()
	http.name = "HubHttp"
	add_child(http)
	if http.start(sim, http_port, ws_port) != OK:
		push_error("[prime-hub] abort: HTTP bind failed")
		get_tree().quit(1)
		return

	var nblocks: int = 0
	if sim.collision != null:
		nblocks = int(sim.collision.blocks.size())
	print("[prime-hub] ready — bots=%d npcs=%d collision=%d A*" % [sim.bot_count(), sim.npc_count(), nblocks])
	print("[prime-hub] WS :%d · HTTP :%d (peel → Python lab)" % [ws_port, http_port])


func _process(delta: float) -> void:
	_accum += delta
	var interval := 1.0 / TICK_HZ
	while _accum >= interval:
		_accum -= interval
		sim.step(interval)
		ws.flush_chat()
		ws.broadcast_zone_state()
