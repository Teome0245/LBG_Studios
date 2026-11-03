extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Atelier d'Assemblage Pondéré & d'Expérimentation
## Style SWG Crafting Tool : barres d'expérimentation segmentées en 10 boîtes [■][■][□] + bandeau Amazing/Great Success.

signal experimentation_completed(result: Dictionary)

const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_id: String = "Voyageur"
var panel_visible: bool = false

var _session: Dictionary = {
	"session_id": "exp_local_1001",
	"schematic_id": "mechatronic_repair_kit",
	"serial": "LH-1001",
	"remaining_points": 5,
	"max_points": 5,
	"attributes": {
		"quality_pct": 66.0,
		"power": 90,
		"durability": 410,
	},
}
var _last_outcome: String = "ASSEMBLAGE TERMINÉ — PRÊT POUR L'EXPÉRIMENTATION"

var _http: HTTPRequest = null
var _header_lbl: Label = null
var _banner_lbl: Label = null
var _points_lbl: Label = null
var _bar_quality: ProgressBar = null
var _bar_power: ProgressBar = null
var _bar_durability: ProgressBar = null
var _seg_quality: _SwgExpSegments = null
var _seg_power: _SwgExpSegments = null
var _seg_durability: _SwgExpSegments = null
var _val_quality: Label = null
var _val_power: Label = null
var _val_durability: Label = null


class _SwgExpSegments extends Control:
	var ratio: float = 0.66
	var fill_color: Color = Color(0.24, 0.90, 0.68, 0.95)

	func _init() -> void:
		custom_minimum_size = Vector2(180, 22)
		size_flags_horizontal = Control.SIZE_EXPAND_FILL

	func set_ratio(r: float) -> void:
		ratio = clampf(r, 0.0, 1.0)
		queue_redraw()

	func _draw() -> void:
		var boxes := 10
		var gap := 3.0
		var total_w := size.x
		var bw := maxf(8.0, (total_w - gap * float(boxes - 1)) / float(boxes))
		var bh := size.y - 4.0
		var filled_cnt := int(round(ratio * float(boxes)))
		for i in range(boxes):
			var bx := float(i) * (bw + gap)
			var rect := Rect2(bx, 2.0, bw, bh)
			draw_rect(rect, Color(0.01, 0.06, 0.08, 0.95), true)
			if i < filled_cnt:
				var inner := rect.grow(-2.0)
				draw_rect(inner, fill_color, true)
				draw_rect(Rect2(inner.position.x, inner.position.y, inner.size.x, 3.0), Color(1, 1, 1, 0.28), true)
			draw_rect(rect, Color(0.28, 0.78, 0.88, 0.85), false, 1.0)


func _ready() -> void:
	visible = panel_visible
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_paint_session()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_done)


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_id = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.11, 0.14, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.95, 0.76, 0.26, 0.94)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 14
	sb.content_margin_top = 10
	sb.content_margin_right = 14
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func _style_exp_btn(btn: Button) -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.25, 0.30, 0.95)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.95, 0.78, 0.28, 0.90)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 8
	sb.content_margin_top = 3
	sb.content_margin_right = 8
	sb.content_margin_bottom = 3
	var sb_hov := sb.duplicate() as StyleBoxFlat
	sb_hov.bg_color = Color(0.10, 0.38, 0.44, 0.98)
	btn.add_theme_stylebox_override("normal", sb)
	btn.add_theme_stylebox_override("hover", sb_hov)
	btn.add_theme_stylebox_override("pressed", sb_hov)
	btn.add_theme_color_override("font_color", Color(0.98, 0.92, 0.65, 1.0))
	btn.add_theme_font_size_override("font_size", 10)


func toggle() -> void:
	panel_visible = not panel_visible
	visible = panel_visible
	mouse_filter = Control.MOUSE_FILTER_STOP if panel_visible else Control.MOUSE_FILTER_IGNORE
	if panel_visible:
		_paint_session()


func open_with_session(sess: Dictionary) -> void:
	_ensure_ui()
	if not sess.is_empty():
		_session = sess.duplicate(true)
		_last_outcome = "ASSEMBLY COMPLETE (%s) — ALLOCATE EXPERIMENTATION POINTS" % str(_session.get("serial", "LH-1001"))
	panel_visible = true
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	_paint_session()


func _ensure_ui() -> void:
	if _bar_quality != null:
		return
	custom_minimum_size = Vector2(640, 340)
	position = Vector2(250, 130)
	size = Vector2(640, 340)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 8)
	add_child(root)

	var hdr_panel := PanelContainer.new()
	var sb_hdr := StyleBoxFlat.new()
	sb_hdr.bg_color = Color(0.05, 0.24, 0.30, 0.96)
	sb_hdr.set_border_width_all(1)
	sb_hdr.border_color = Color(0.96, 0.78, 0.28, 0.92)
	sb_hdr.set_corner_radius_all(4)
	sb_hdr.content_margin_left = 10
	sb_hdr.content_margin_top = 4
	sb_hdr.content_margin_right = 8
	sb_hdr.content_margin_bottom = 4
	hdr_panel.add_theme_stylebox_override("panel", sb_hdr)
	root.add_child(hdr_panel)

	var top_row := HBoxContainer.new()
	hdr_panel.add_child(top_row)

	var title := Label.new()
	title.text = "⚙  OUTIL D'ARTISANAT — PHASE D'EXPÉRIMENTATION  (SWG PRE-CU)"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.add_theme_font_size_override("font_size", 12)
	title.add_theme_color_override("font_color", Color(0.98, 0.84, 0.35, 1.0))
	top_row.add_child(title)

	var close_btn := Button.new()
	close_btn.text = "✕"
	close_btn.custom_minimum_size = Vector2(26, 22)
	close_btn.pressed.connect(toggle)
	top_row.add_child(close_btn)

	_header_lbl = Label.new()
	_header_lbl.add_theme_font_size_override("font_size", 10)
	_header_lbl.add_theme_color_override("font_color", Color(0.75, 0.92, 0.96, 1.0))
	root.add_child(_header_lbl)

	var banner_panel := PanelContainer.new()
	var sb_ban := StyleBoxFlat.new()
	sb_ban.bg_color = Color(0.01, 0.06, 0.08, 0.94)
	sb_ban.set_border_width_all(1)
	sb_ban.border_color = Color(0.28, 0.86, 0.68, 0.85)
	sb_ban.set_corner_radius_all(4)
	sb_ban.content_margin_top = 5
	sb_ban.content_margin_bottom = 5
	banner_panel.add_theme_stylebox_override("panel", sb_ban)
	root.add_child(banner_panel)

	_banner_lbl = Label.new()
	_banner_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_lbl.add_theme_font_size_override("font_size", 11)
	_banner_lbl.add_theme_color_override("font_color", Color(0.45, 0.98, 0.68, 1.0))
	banner_panel.add_child(_banner_lbl)

	_points_lbl = Label.new()
	_points_lbl.add_theme_font_size_override("font_size", 11)
	_points_lbl.add_theme_color_override("font_color", Color(0.98, 0.86, 0.42, 1.0))
	root.add_child(_points_lbl)

	# Ligne 1 : Quality %
	var row_q := _build_attr_row("Qualité Expérimentale (OQ/MA)", "quality_pct", 100.0, Color(0.24, 0.92, 0.68, 0.95))
	_bar_quality = row_q["bar"]
	_seg_quality = row_q["seg"]
	_val_quality = row_q["val"]
	root.add_child(row_q["container"])

	# Ligne 2 : Power
	var row_p := _build_attr_row("Efficacité Mécanique (OQ/PE)", "power", 180.0, Color(0.32, 0.82, 0.98, 0.95))
	_bar_power = row_p["bar"]
	_seg_power = row_p["seg"]
	_val_power = row_p["val"]
	root.add_child(row_p["container"])

	# Ligne 3 : Durability
	var row_d := _build_attr_row("Intégrité Structurelle (SR/OQ)", "durability", 700.0, Color(0.96, 0.78, 0.26, 0.95))
	_bar_durability = row_d["bar"]
	_seg_durability = row_d["seg"]
	_val_durability = row_d["val"]
	root.add_child(row_d["container"])


func _build_attr_row(label_txt: String, attr_key: String, max_v: float, col: Color) -> Dictionary:
	var hbox := HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 8)

	var lbl := Label.new()
	lbl.text = label_txt
	lbl.custom_minimum_size = Vector2(195, 0)
	lbl.add_theme_font_size_override("font_size", 10)
	lbl.add_theme_color_override("font_color", Color(0.84, 0.95, 0.98, 1.0))
	hbox.add_child(lbl)

	# Barre 10 segments style SWG
	var seg := _SwgExpSegments.new()
	seg.fill_color = col
	hbox.add_child(seg)

	# ProgressBar cachée conservée pour compatibilité selftest
	var bar := ProgressBar.new()
	bar.max_value = max_v
	bar.visible = false
	hbox.add_child(bar)

	var val_lbl := Label.new()
	val_lbl.custom_minimum_size = Vector2(62, 0)
	val_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	val_lbl.add_theme_font_size_override("font_size", 10)
	val_lbl.add_theme_color_override("font_color", Color(0.98, 0.88, 0.42, 1.0))
	hbox.add_child(val_lbl)

	var btn1 := Button.new()
	btn1.text = "+1 PT"
	_style_exp_btn(btn1)
	btn1.pressed.connect(func() -> void: spend_points(attr_key, 1))
	hbox.add_child(btn1)

	var btn2 := Button.new()
	btn2.text = "+2 PTS"
	_style_exp_btn(btn2)
	btn2.pressed.connect(func() -> void: spend_points(attr_key, 2))
	hbox.add_child(btn2)

	return {"container": hbox, "bar": bar, "seg": seg, "val": val_lbl}


func spend_points(attribute_line: String, pts: int = 1) -> Dictionary:
	_ensure_ui()
	var rem := int(_session.get("remaining_points", 0))
	if rem < pts:
		_last_outcome = "⚠ INSUFFICIENT EXPERIMENTATION POINTS (%d REMAINING)" % rem
		_paint_session()
		return {"ok": false, "error": "insufficient_experimentation_points"}

	var sess_id := str(_session.get("session_id", ""))
	if _http != null and is_inside_tree() and not sess_id.begins_with("exp_local"):
		var url := "%s/v1/craft/experiment" % sidecar_base_url.rstrip("/")
		var body := JSON.stringify({
			"player": player_id,
			"session_id": sess_id,
			"attribute": attribute_line,
			"points": pts,
		})
		if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
			_http.cancel_request()
		_http.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, body)
		return {"ok": true, "pending": true}

	_session["remaining_points"] = rem - pts
	var attrs: Dictionary = _session.get("attributes", {})
	if attribute_line == "quality_pct":
		attrs["quality_pct"] = clampf(float(attrs.get("quality_pct", 60.0)) + float(pts) * 5.5, 5.0, 99.9)
	elif attribute_line == "power":
		attrs["power"] = int(attrs.get("power", 80)) + pts * 8
	elif attribute_line == "durability":
		attrs["durability"] = int(attrs.get("durability", 350)) + pts * 22
	_session["attributes"] = attrs
	_last_outcome = "★ GREAT SUCCESS ! (+%d PT ON %s) ★" % [pts, attribute_line.to_upper()]
	_paint_session()
	var res := {
		"ok": true,
		"session_id": sess_id,
		"attribute": attribute_line,
		"points_spent": pts,
		"remaining_points": int(_session["remaining_points"]),
		"outcome": "great_success",
		"item_stats": attrs.duplicate(true),
	}
	experimentation_completed.emit(res)
	return res


func _on_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d := parsed as Dictionary
	if bool(d.get("ok", false)):
		_session["remaining_points"] = int(d.get("remaining_points", 0))
		if typeof(d.get("item_stats")) == TYPE_DICTIONARY:
			_session["attributes"] = (d["item_stats"] as Dictionary).duplicate(true)
		var out_str := str(d.get("outcome", "great_success")).to_upper().replace("_", " ")
		_last_outcome = "★ %s (%s : +%s) ★" % [out_str, str(d.get("attribute", "")), str(d.get("delta", ""))]
		_paint_session()
		experimentation_completed.emit(d)
	else:
		_last_outcome = "⚠ EXPERIMENTATION FAILED : %s" % str(d.get("error", code))
		_paint_session()


func _paint_session() -> void:
	if _header_lbl == null:
		return
	var sc_id := str(_session.get("schematic_id", "mechatronic_repair_kit"))
	var serial := str(_session.get("serial", "LH-1001"))
	var rem := int(_session.get("remaining_points", 0))
	var max_p := int(_session.get("max_points", 5))
	var attrs: Dictionary = _session.get("attributes", {}) if typeof(_session.get("attributes")) == TYPE_DICTIONARY else {}

	_header_lbl.text = "PROTOTYPE : %s   ·   N° SÉRIE : %s   ·   ARTISAN : %s" % [sc_id.to_upper(), serial, player_id]
	_banner_lbl.text = _last_outcome
	_points_lbl.text = "◈  POINTS D'EXPÉRIMENTATION DISPONIBLES :  %d / %d" % [rem, max_p]

	var q := float(attrs.get("quality_pct", 66.0))
	var p := int(attrs.get("power", 90))
	var dur := int(attrs.get("durability", 410))

	_bar_quality.value = q
	if _seg_quality:
		_seg_quality.set_ratio(q / 100.0)
	_val_quality.text = "%.1f%%" % q

	_bar_power.value = float(p)
	if _seg_power:
		_seg_power.set_ratio(float(p) / 180.0)
	_val_power.text = "%d" % p

	_bar_durability.value = float(dur)
	if _seg_durability:
		_seg_durability.set_ratio(float(dur) / 700.0)
	_val_durability.text = "%d" % dur
