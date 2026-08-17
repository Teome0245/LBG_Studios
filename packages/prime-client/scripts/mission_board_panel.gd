# mission_board_panel.gd — Board missions Lost Heaven (sidecar :8791)
extends PanelContainer
class_name MissionBoardPanel

signal quest_accepted(result: Dictionary)
signal quest_completed(result: Dictionary)

const SIDECAR_DEFAULT := "http://192.168.0.246:8791"
const PLAYER_DEFAULT := "local"
const GIVER_DEFAULT := "npc:core3_daan_oth"

@export var sidecar_base_url: String = SIDECAR_DEFAULT
@export var player_id: String = PLAYER_DEFAULT
@export var giver_id: String = GIVER_DEFAULT
@export var panel_visible: bool = false

var _quests: Array = []
var _active: Array = []
var _credits: int = 0
var _status: String = "idle"
var _http: HTTPRequest
var _http_act: HTTPRequest
var _pending: String = ""

var _title: Label
var _status_label: Label
var _detail: Label
var _list: ItemList
var _refresh_btn: Button
var _accept_btn: Button
var _complete_btn: Button
var _tip_btn: Button
var _objective_hud: Label
var _poi_cache: Dictionary = {}  # id -> Vector2(x,z)
var _progress_cooldown: float = 0.0
var _reported_steps: Dictionary = {}  # "quest|step" -> true

func _ready() -> void:
	visible = panel_visible
	_apply_mouse_filter()
	_apply_modal_style()
	_ensure_ui()
	_ensure_objective_hud()
	_load_poi_cache()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_done)
	_http_act = HTTPRequest.new()
	add_child(_http_act)
	_http_act.request_completed.connect(_on_act_done)
	call_deferred("refresh_board")
	call_deferred("_paint_objective_hud")

func _process(delta: float) -> void:
	if not panel_visible and _active.is_empty():
		return
	_progress_cooldown = maxf(0.0, _progress_cooldown - delta)
	if _progress_cooldown > 0.0:
		return
	_progress_cooldown = 0.6
	_try_auto_progress()

func _load_poi_cache() -> void:
	_poi_cache.clear()
	const path := "res://assets/maps/lost_heaven_buildings.json"
	if not FileAccess.file_exists(path):
		return
	var f := FileAccess.open(path, FileAccess.READ)
	var raw: Variant = JSON.parse_string(f.get_as_text())
	f.close()
	if not raw is Dictionary:
		return
	for item: Variant in (raw as Dictionary).get("buildings", []):
		if item is Dictionary:
			var b: Dictionary = item
			_poi_cache[str(b.get("id", ""))] = Vector2(float(b.get("x", 0.0)), float(b.get("z", 0.0)))

func _player_core3_xz() -> Vector2:
	var main := get_tree().get_first_node_in_group("prime_main")
	if main == null:
		return Vector2.INF
	var pc: Node = main.get_node_or_null("PlayerController")
	if pc == null or not pc.has_method("get_player_id"):
		return Vector2.INF
	var pid: int = int(pc.get_player_id())
	if pid == 0:
		return Vector2.INF
	var em: Node = main.get_node_or_null("EntityManager")
	if em == null or not em.has_method("get_entity"):
		return Vector2.INF
	var e: Node = em.get_entity(pid)
	if e == null:
		return Vector2.INF
	var p: Vector3 = e.get("core3_pos")
	return Vector2(p.x, p.z)

func _try_auto_progress() -> void:
	if _active.is_empty():
		return
	var pos := _player_core3_xz()
	if pos == Vector2.INF:
		return
	for a in _active:
		if typeof(a) != TYPE_DICTIONARY:
			continue
		var qid := str(a.get("id", ""))
		var steps = a.get("progress_steps", [])
		if typeof(steps) != TYPE_ARRAY:
			continue
		for s in steps:
			if typeof(s) != TYPE_DICTIONARY:
				continue
			if bool(s.get("done", false)):
				continue
			var poi := str(s.get("poi", ""))
			if poi == "" or not _poi_cache.has(poi):
				continue
			var target: Vector2 = _poi_cache[poi]
			var radius := float(s.get("radius_m", 50.0))
			if pos.distance_to(target) > radius:
				continue
			var key := "%s|%s" % [qid, str(s.get("id", ""))]
			if _reported_steps.has(key):
				continue
			_reported_steps[key] = true
			_post_act("/v1/quests/progress", {
				"player": player_id,
				"quest_id": qid,
				"step_id": str(s.get("id", "")),
				"poi_id": poi,
				"x": pos.x,
				"z": pos.y,
			}, "progress")
			return  # one step per tick

func _apply_modal_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.055, 0.05, 0.94)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.55, 0.72, 0.85, 0.95)
	sb.set_corner_radius_all(5)
	sb.content_margin_left = 12
	sb.content_margin_top = 10
	sb.content_margin_right = 12
	sb.content_margin_bottom = 12
	sb.shadow_color = Color(0, 0, 0, 0.45)
	sb.shadow_size = 8
	add_theme_stylebox_override("panel", sb)

func _apply_mouse_filter() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE

func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	_apply_mouse_filter()
	if panel_visible:
		refresh_board()

func _ensure_ui() -> void:
	var root := get_node_or_null("VBox") as VBoxContainer
	if root == null:
		root = VBoxContainer.new()
		root.name = "VBox"
		root.add_theme_constant_override("separation", 6)
		add_child(root)
	_title = root.get_node_or_null("Title") as Label
	if _title == null:
		_title = Label.new()
		_title.name = "Title"
		_title.text = "Bureau des missions — Lost Heaven"
		root.add_child(_title)
	_status_label = root.get_node_or_null("Status") as Label
	if _status_label == null:
		_status_label = Label.new()
		_status_label.name = "Status"
		_status_label.add_theme_font_size_override("font_size", 11)
		root.add_child(_status_label)
	var header := root.get_node_or_null("HeaderRow") as HBoxContainer
	if header == null:
		header = HBoxContainer.new()
		header.name = "HeaderRow"
		root.add_child(header)
	_refresh_btn = header.get_node_or_null("Refresh") as Button
	if _refresh_btn == null:
		_refresh_btn = Button.new()
		_refresh_btn.name = "Refresh"
		_refresh_btn.text = "Rafraîchir"
		header.add_child(_refresh_btn)
	if not _refresh_btn.pressed.is_connected(refresh_board):
		_refresh_btn.pressed.connect(refresh_board)
	_accept_btn = header.get_node_or_null("Accept") as Button
	if _accept_btn == null:
		_accept_btn = Button.new()
		_accept_btn.name = "Accept"
		_accept_btn.text = "Accepter"
		header.add_child(_accept_btn)
	if not _accept_btn.pressed.is_connected(_accept_selected):
		_accept_btn.pressed.connect(_accept_selected)
	_complete_btn = header.get_node_or_null("Complete") as Button
	if _complete_btn == null:
		_complete_btn = Button.new()
		_complete_btn.name = "Complete"
		_complete_btn.text = "Terminer"
		header.add_child(_complete_btn)
	if not _complete_btn.pressed.is_connected(_complete_selected):
		_complete_btn.pressed.connect(_complete_selected)
	_tip_btn = header.get_node_or_null("Tip") as Button
	if _tip_btn == null:
		_tip_btn = Button.new()
		_tip_btn.name = "Tip"
		_tip_btn.text = "Tip Scène"
		header.add_child(_tip_btn)
	if not _tip_btn.pressed.is_connected(_tip_scene):
		_tip_btn.pressed.connect(_tip_scene)
	var list_lbl := root.get_node_or_null("ListLabel") as Label
	if list_lbl == null:
		list_lbl = Label.new()
		list_lbl.name = "ListLabel"
		list_lbl.text = "Offres (Daan Oth)"
		root.add_child(list_lbl)
	_list = root.get_node_or_null("QuestList") as ItemList
	if _list == null:
		_list = ItemList.new()
		_list.name = "QuestList"
		_list.custom_minimum_size = Vector2(0, 160)
		_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
		root.add_child(_list)
	if not _list.item_selected.is_connected(_on_quest_selected):
		_list.item_selected.connect(_on_quest_selected)
	_detail = root.get_node_or_null("Detail") as Label
	if _detail == null:
		_detail = Label.new()
		_detail.name = "Detail"
		_detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_detail.add_theme_font_size_override("font_size", 11)
		_detail.add_theme_color_override("font_color", Color(0.82, 0.78, 0.68, 0.95))
		_detail.text = "J ouvrir · sélectionne une mission · Accepter / Terminer (MVP stub)"
		root.add_child(_detail)
	_paint()

func _ensure_objective_hud() -> void:
	# Hors panneau J et hors hotbar : bandeau haut (HudLayer), visible panel fermé.
	var hud_layer: Node = null
	var ui := get_parent()
	if ui != null:
		ui = ui.get_parent()  # ModalLayer -> UI
	if ui != null:
		hud_layer = ui.get_node_or_null("HudLayer")
	if hud_layer == null:
		return
	_objective_hud = hud_layer.get_node_or_null("QuestObjectiveHud") as Label
	if _objective_hud == null:
		_objective_hud = Label.new()
		_objective_hud.name = "QuestObjectiveHud"
		hud_layer.add_child(_objective_hud)
	# Toujours réaligner (évite un ancien placement bas si le label existait déjà).
	_objective_hud.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_objective_hud.anchor_left = 0.15
	_objective_hud.anchor_right = 0.85
	_objective_hud.offset_left = 0.0
	_objective_hud.offset_right = 0.0
	_objective_hud.offset_top = 10.0
	_objective_hud.offset_bottom = 34.0
	_objective_hud.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_objective_hud.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_objective_hud.add_theme_font_size_override("font_size", 13)
	_objective_hud.add_theme_color_override("font_color", Color(0.92, 0.86, 0.62, 0.96))
	_objective_hud.add_theme_color_override("font_outline_color", Color(0.05, 0.04, 0.03, 0.85))
	_objective_hud.add_theme_constant_override("outline_size", 4)
	_objective_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not _objective_hud.visible and _objective_hud.text.is_empty():
		_objective_hud.visible = false

func _next_objective_text() -> String:
	for a in _active:
		if typeof(a) != TYPE_DICTIONARY:
			continue
		var title := str(a.get("title", a.get("id", "Mission")))
		var steps = a.get("progress_steps", [])
		if typeof(steps) != TYPE_ARRAY or steps.is_empty():
			return "Mission : %s — J pour terminer" % title
		for s in steps:
			if typeof(s) != TYPE_DICTIONARY:
				continue
			if bool(s.get("done", false)):
				continue
			var label := str(s.get("label", s.get("id", "objectif")))
			return "Objectif : %s — %s" % [title, label]
		return "Mission : %s — prête à Terminer (J)" % title
	return ""

func _paint_objective_hud() -> void:
	if _objective_hud == null:
		_ensure_objective_hud()
	if _objective_hud == null:
		return
	var text := _next_objective_text()
	if text == "":
		_objective_hud.visible = false
		_objective_hud.text = ""
		return
	_objective_hud.text = text
	_objective_hud.visible = true

func refresh_board() -> void:
	_status = "fetch board…"
	_pending = "board"
	_paint_status()
	var url := "%s/v1/quests/board?giver=%s&player=%s" % [
		sidecar_base_url.rstrip("/"),
		giver_id.uri_encode(),
		player_id.uri_encode(),
	]
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http.cancel_request()
	var err := _http.request(url, [], HTTPClient.METHOD_GET)
	if err != OK:
		_apply_local_mock("req_%d" % err)

func _refresh_status_after_board() -> void:
	_pending = "status"
	var url := "%s/v1/quests/status?player=%s" % [sidecar_base_url.rstrip("/"), player_id.uri_encode()]
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http.cancel_request()
	_http.request(url, [], HTTPClient.METHOD_GET)

func _on_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
		if _pending == "board":
			_apply_local_mock(code)
		else:
			_status = "status hors ligne (%s)" % str(code)
			_paint_status()
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		_status = "parse error"
		_paint_status()
		return
	if _pending == "board":
		_quests = parsed.get("quests", [])
		if bool(parsed.get("rotated", false)):
			_status = "nouvelles offres — %d missions" % _quests.size()
		else:
			_status = "live — %d offres (Daan Oth)" % _quests.size()
		_paint()
		_refresh_status_after_board()
		return
	# status
	_active = parsed.get("active", [])
	_credits = int(parsed.get("credits", _credits))
	_status = "live — %d actives · %d Cr" % [_active.size(), _credits]
	_paint()

func _accept_selected() -> void:
	var qid := _selected_quest_id()
	if qid == "":
		_status = "sélectionne une offre"
		_paint_status()
		return
	_post_act("/v1/quests/accept", {"player": player_id, "quest_id": qid, "giver_id": giver_id}, "accept")

func _complete_selected() -> void:
	var qid := _selected_quest_id()
	if qid == "":
		# fallback: first active
		if _active.size() > 0 and typeof(_active[0]) == TYPE_DICTIONARY:
			qid = str(_active[0].get("id", ""))
	if qid == "":
		_status = "aucune mission active"
		_paint_status()
		return
	_post_act("/v1/quests/complete", {"player": player_id, "quest_id": qid}, "complete")

func _tip_scene() -> void:
	_post_act("/v1/quests/tip", {"player": player_id, "quest_id": "lh_show_perle", "amount": 2}, "tip")

func _post_act(path: String, payload: Dictionary, kind: String) -> void:
	_pending = kind
	_status = "%s…" % kind
	_paint_status()
	var url := sidecar_base_url.rstrip("/") + path
	var body := JSON.stringify(payload)
	var headers := PackedStringArray(["Content-Type: application/json"])
	if _http_act.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http_act.cancel_request()
	var err := _http_act.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		_status = "%s req_%d" % [kind, err]
		_paint_status()

func _on_act_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if result != HTTPRequest.RESULT_SUCCESS:
		_status = "réseau KO"
		_paint_status()
		return
	if typeof(parsed) != TYPE_DICTIONARY:
		_status = "parse error (%d)" % code
		_paint_status()
		return
	if not bool(parsed.get("ok", false)):
		var err := str(parsed.get("error", code))
		var hint := str(parsed.get("hint", ""))
		match err:
			"objectives_incomplete":
				_status = hint if hint != "" else "objectifs incomplets — va sur place"
			"steps_out_of_order":
				_status = hint if hint != "" else "fais les étapes dans l'ordre"
			"no_offers":
				_status = hint if hint != "" else "aucune mission — rafraîchis le board"
				call_deferred("refresh_board")
			_:
				_status = "échec: %s%s" % [err, (" — " + hint) if hint != "" else ""]
		_paint_status()
		return
	if _pending == "accept":
		var accepted_title := str((parsed.get("accepted") or {}).get("title", "?"))
		if parsed.has("redirected_from"):
			_status = "nouvelle mission — %s" % accepted_title
		else:
			_status = "acceptée — %s (va aux POI)" % accepted_title
		_reported_steps.clear()
		quest_accepted.emit(parsed)
	elif _pending == "tip":
		_credits = int(parsed.get("credits", _credits))
		_status = "tip — %s Cr · %s" % [str(parsed.get("tipped", 0)), str(parsed.get("message", "Scène"))]
	elif _pending == "progress":
		var label := str(parsed.get("label", parsed.get("step_id", "étape")))
		_status = "étape OK — %s" % label
		if bool(parsed.get("ready_to_turn_in", false)):
			_status += " · prête à Terminer"
		if parsed.has("active"):
			_active = parsed.get("active", _active)
		_paint()
		return
	else:
		var title := str(parsed.get("title", parsed.get("quest_id", "?")))
		var cr := int((parsed.get("reward_applied") or {}).get("credits_gained", 0))
		var new_offer = parsed.get("new_offer", {})
		if typeof(new_offer) == TYPE_DICTIONARY and str(new_offer.get("title", "")) != "":
			_status = "terminée — %s (+%d Cr) · nouvelle : %s" % [title, cr, str(new_offer.get("title"))]
		else:
			_status = "terminée — %s (+%d Cr)" % [title, cr]
		_credits = int(parsed.get("credits", _credits))
		quest_completed.emit(parsed)
	_active = parsed.get("active", _active)
	_paint()
	# refresh board list state
	call_deferred("refresh_board")

func _selected_quest_id() -> String:
	if _list == null:
		return ""
	var idxs := _list.get_selected_items()
	if idxs.is_empty():
		return ""
	var i: int = idxs[0]
	if i < 0 or i >= _quests.size():
		return ""
	var q = _quests[i]
	if typeof(q) != TYPE_DICTIONARY:
		return ""
	return str(q.get("id", ""))

func _on_quest_selected(index: int) -> void:
	if index < 0 or index >= _quests.size():
		return
	var q = _quests[index]
	if typeof(q) != TYPE_DICTIONARY:
		return
	var qid := str(q.get("id", ""))
	var active_entry: Dictionary = {}
	for a in _active:
		if typeof(a) == TYPE_DICTIONARY and str(a.get("id", "")) == qid:
			active_entry = a
			break
	var lines: PackedStringArray = PackedStringArray()
	lines.append(str(q.get("title", "")))
	lines.append(str(q.get("objective", "")))
	var rewards = q.get("rewards", {})
	if typeof(rewards) == TYPE_DICTIONARY:
		lines.append("Récompense: %d Cr" % int(rewards.get("credits", 0)))
	var steps = active_entry.get("progress_steps", q.get("progress", []))
	if typeof(steps) == TYPE_ARRAY and steps.size() > 0:
		lines.append("Objectifs:")
		for s in steps:
			if typeof(s) != TYPE_DICTIONARY:
				continue
			var done := bool(s.get("done", false))
			lines.append("%s %s" % ["[x]" if done else "[ ]", str(s.get("label", s.get("id", "?")))])
	else:
		var ns = q.get("next_steps", [])
		if typeof(ns) == TYPE_ARRAY:
			for s in ns:
				lines.append("· %s" % str(s))
	_detail.text = "\n".join(lines)

func _apply_local_mock(code: Variant) -> void:
	_status = "hors ligne (%s) · mock local" % str(code)
	_quests = [
		{
			"id": "lh_delivery_starport",
			"title": "Colis du port shuttle",
			"objective": "Livrer un colis du port shuttle au marché de Lost Heaven.",
			"next_steps": ["Récupérer le colis au starport.", "Le porter au marché.", "Confirmer."],
			"rewards": {"credits": 15},
		},
		{
			"id": "lh_survey_dunes",
			"title": "Relevé hors palissade",
			"objective": "Relever un gisement hors palissade.",
			"next_steps": ["Sortir par la porte.", "Prospecter.", "Revenir."],
			"rewards": {"credits": 25},
		},
	]
	_paint()

func _paint_status() -> void:
	if _status_label:
		_status_label.text = _status

func _paint() -> void:
	_paint_status()
	_paint_objective_hud()
	if _list == null:
		return
	_list.clear()
	var active_ids: Dictionary = {}
	for a in _active:
		if typeof(a) == TYPE_DICTIONARY:
			active_ids[str(a.get("id", ""))] = true
	if _quests.is_empty():
		_list.add_item("(aucune offre)")
		return
	for q in _quests:
		if typeof(q) != TYPE_DICTIONARY:
			_list.add_item(str(q))
			continue
		var mark := "● " if active_ids.has(str(q.get("id", ""))) else ""
		var label := "%s%s" % [mark, str(q.get("title", q.get("id", "?")))]
		var cr := 0
		var rewards = q.get("rewards", {})
		if typeof(rewards) == TYPE_DICTIONARY:
			cr = int(rewards.get("credits", 0))
		if cr > 0:
			label += "  · %d Cr" % cr
		_list.add_item(label)
