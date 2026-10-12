extends RefCounted
class_name HubWorldStream
## Plan 3.1 — Live World Stream Hub → Compagnon.
## Buffer léger (ring) d'événements monde, exposé en JSON (`GET /v1/world/stream`).
## Le Compagnon (Cortex) tire le dernier événement marquant pour enrichir sa salutation.

const MAX_EVENTS := 64


var _events: Array = []
var _seq: int = 0


func emit(kind: String, text: String, actor: String = "", zone: String = "", detail: Dictionary = {}) -> Dictionary:
	## Émet un événement léger. `seq` strictement croissant (curseur de lecture).
	var line := text.strip_edges()
	if line.is_empty():
		return {}
	_seq += 1
	var ev := {
		"v": 1,
		"seq": _seq,
		"kind": kind,
		"text": line,
		"actor": actor,
		"zone": zone,
		"detail": detail,
		"ts": Time.get_unix_time_from_system(),
	}
	_events.append(ev)
	if _events.size() > MAX_EVENTS:
		_events = _events.slice(_events.size() - MAX_EVENTS)
	return ev


func recent(since: int = 0, limit: int = 20) -> Dictionary:
	## Événements de `seq > since`, du plus ancien au plus récent (cap `limit`).
	var out: Array = []
	var cap := clampi(limit, 1, MAX_EVENTS)
	for i in range(_events.size() - 1, -1, -1):
		var ev: Dictionary = _events[i]
		if int(ev.get("seq", 0)) <= since:
			break
		out.append(ev)
		if out.size() >= cap:
			break
	out.reverse()
	return {
		"ok": true,
		"seq": _seq,
		"count": out.size(),
		"events": out,
		"source": "prime_hub",
	}


func latest() -> Dictionary:
	if _events.is_empty():
		return {}
	return _events[_events.size() - 1]


func snapshot() -> Dictionary:
	var last := latest()
	return {
		"ok": true,
		"seq": _seq,
		"buffered": _events.size(),
		"last": last,
		"source": "prime_hub",
	}
