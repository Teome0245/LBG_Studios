extends Control
## Interface SWG Pre-CU (2D Top-Down, Français) — HUD Complet :
## 1. Haut-Gauche : Cadre HAM Joueur (Santé / Action / Esprit + Blessures + Fatigue) + Cadres Groupe (Nix, Lia).
## 2. Haut-Droite : Cadre HAM de la Cible sélectionnée (Cible : Nom + Distance + Barres S/A/E).
## 3. Bas-Droite  : Barrette Système verticale Holo-Teal (Compétences, Prospection, Expérim., Inventaire, Artisanat, Missions, Carte).

signal quick_panel_requested(panel_key: String)

const _HubRuntimeCfg = preload("res://scripts/hub_runtime_cfg.gd")
const _SwgPortrait3D = preload("res://scripts/swg_portrait_3d.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_id: String = "Voyageur"
var poll_interval_sec: float = 3.5

var _ham: Dictionary = {
	"health": {"base_max": 1000, "wounds": 0, "buff": 0, "effective_max": 1000, "current": 1000},
	"action": {"base_max": 1000, "wounds": 0, "buff": 0, "effective_max": 1000, "current": 1000},
	"mind": {"base_max": 1000, "wounds": 0, "buff": 0, "effective_max": 1000, "current": 1000},
	"battle_fatigue": 0,
}
var _medical_efficiency: float = 1.0
var _target_name: String = ""
var _target_kind: String = ""
var _target_dist_m: float = -1.0
var _posture_label: String = "Debout"
var _combat_posture: String = "upright"
var _combat_statuses: Dictionary = {}

var _http: HTTPRequest = null
var _poll_timer: float = 0.0

# Proxies de compatibilité pour client_modular_selftest.gd
var _bar_health: _SwgPoolState = null
var _bar_action: _SwgPoolState = null
var _bar_mind: _SwgPoolState = null
var _target_box: Control = null
var _canvas_draw: _SwgHamCanvas = null
var _sys_dock: PanelContainer = null
var _portrait_3d: SubViewportContainer = null


class _SwgPoolState extends RefCounted:
	var pool_name: String = "S"
	var fill_color: Color = Color(0.88, 0.18, 0.22, 1.0)
	var base_max: int = 1000
	var wounds: int = 0
	var buff: int = 0
	var current: int = 1000

	func _init(p_name: String, p_col: Color) -> void:
		pool_name = p_name
		fill_color = p_col

	func set_pool_data(d: Dictionary) -> void:
		base_max = maxi(100, int(d.get("base_max", 1000)))
		wounds = clampi(int(d.get("wounds", 0)), 0, base_max - 50)
		buff = maxi(0, int(d.get("buff", 0)))
		var eff_max := maxi(50, base_max + buff - wounds)
		current = clampi(int(d.get("current", eff_max)), 0, eff_max)


class _SwgHamCanvas extends Control:
	var owner_hud: Control = null

	func _draw_chamfer_box(r: Rect2, bg: Color, border: Color, cut: float = 7.0) -> void:
		var x0 := r.position.x
		var y0 := r.position.y
		var x1 := x0 + r.size.x
		var y1 := y0 + r.size.y
		var pts := PackedVector2Array([
			Vector2(x0 + cut, y0),
			Vector2(x1 - cut, y0),
			Vector2(x1, y0 + cut),
			Vector2(x1, y1 - cut),
			Vector2(x1 - cut, y1),
			Vector2(x0 + cut, y1),
			Vector2(x0, y1 - cut),
			Vector2(x0, y0 + cut),
		])
		draw_colored_polygon(pts, bg)
		var line_pts := pts.duplicate()
		line_pts.append(pts[0])
		draw_polyline(line_pts, border, 1.6, true)

	func _draw_swg_bar(rect: Rect2, cur: int, base: int, wounds: int, buff: int, col: Color, label_char: String, compact: bool = false) -> void:
		var w := rect.size.x
		var h := rect.size.y
		var x := rect.position.x
		var y := rect.position.y
		var total_cap := float(maxi(100, base + buff))
		var eff_max := maxi(50, base + buff - wounds)

		draw_rect(Rect2(x, y, w, h), Color(0.015, 0.05, 0.07, 0.96), true)

		var cur_ratio := clampf(float(cur) / total_cap, 0.0, 1.0)
		var fill_w := (w - 2.0) * cur_ratio
		if fill_w > 0.0:
			draw_rect(Rect2(x + 1, y + 1, fill_w, h - 2), col, true)
			draw_rect(Rect2(x + 1, y + 1, fill_w, (h - 2) * 0.38), Color(1.0, 1.0, 1.0, 0.24), true)

		var wound_ratio := clampf(float(wounds) / total_cap, 0.0, 0.90)
		if wound_ratio > 0.0:
			var ww := (w - 2.0) * wound_ratio
			var wx := x + w - 1.0 - ww
			draw_rect(Rect2(wx, y + 1, ww, h - 2), Color(0.04, 0.01, 0.01, 0.98), true)
			draw_line(Vector2(wx, y + 1), Vector2(wx, y + h - 1), Color(0.95, 0.28, 0.22, 0.95), 1.5)

		for g in [0.25, 0.50, 0.75]:
			var gx: float = x + w * float(g)
			draw_line(Vector2(gx, y + 1), Vector2(gx, y + h - 1), Color(0.0, 0.0, 0.0, 0.35), 1.0)

		var b_col := Color(0.96, 0.82, 0.32, 0.95) if buff > 0 else Color(0.22, 0.76, 0.86, 0.88)
		draw_rect(Rect2(x, y, w, h), b_col, false, 1.0)

		var font := ThemeDB.fallback_font
		if font and not compact:
			draw_string(font, Vector2(x - 12, y + h - 2), label_char, HORIZONTAL_ALIGNMENT_LEFT, 12, 9, Color(0.68, 0.94, 0.98, 1.0))
			var txt := "%d / %d" % [cur, eff_max]
			if wounds > 0:
				txt += " [-%d]" % wounds
			draw_string(font, Vector2(x + 4, y + h - 2), txt, HORIZONTAL_ALIGNMENT_CENTER, w - 8, 9, Color(0.98, 0.99, 1.0, 1.0))

	func _draw_group_member(y_top: float, m_name: String, dist_txt: String, h_pct: float, a_pct: float, m_pct: float) -> void:
		var font := ThemeDB.fallback_font
		var r := Rect2(0, y_top, 196, 36)
		_draw_chamfer_box(r, Color(0.015, 0.10, 0.13, 0.84), Color(0.18, 0.68, 0.78, 0.82), 5.0)
		# Icône silhouette groupe à gauche
		draw_rect(Rect2(6, y_top + 6, 22, 24), Color(0.04, 0.20, 0.25, 0.92), true)
		draw_rect(Rect2(6, y_top + 6, 22, 24), Color(0.25, 0.78, 0.88, 0.80), false, 1.0)
		draw_circle(Vector2(17, y_top + 14), 4.0, Color(0.55, 0.94, 1.0, 0.95))
		if font:
			draw_string(font, Vector2(34, y_top + 12), "%s (%s)" % [m_name, dist_txt], HORIZONTAL_ALIGNMENT_LEFT, 154, 9, Color(0.84, 0.96, 1.0, 1.0))
		_draw_swg_bar(Rect2(34, y_top + 15, 152, 5), int(h_pct * 1000.0), 1000, 0, 0, Color(0.86, 0.16, 0.20, 1.0), "", true)
		_draw_swg_bar(Rect2(34, y_top + 21, 152, 5), int(a_pct * 1000.0), 1000, 0, 0, Color(0.18, 0.78, 0.30, 1.0), "", true)
		_draw_swg_bar(Rect2(34, y_top + 27, 152, 5), int(m_pct * 1000.0), 1000, 0, 0, Color(0.18, 0.48, 0.92, 1.0), "", true)

	func _draw() -> void:
		if owner_hud == null:
			return
		var font := ThemeDB.fallback_font
		# 1. Cadre principal HAM Joueur (Haut-Gauche)
		var main_rect := Rect2(0, 0, 276, 72)
		_draw_chamfer_box(main_rect, Color(0.02, 0.12, 0.15, 0.90), Color(0.22, 0.82, 0.92, 0.94), 7.0)

		draw_rect(Rect2(8, 4, 260, 13), Color(0.05, 0.28, 0.35, 0.92), true)
		if font:
			draw_string(font, Vector2(14, 14), owner_hud.player_id, HORIZONTAL_ALIGNMENT_LEFT, 150, 10, Color(0.86, 0.98, 1.0, 1.0))
			var bf := int(owner_hud._ham.get("battle_fatigue", 0))
			var bf_txt := "Fatigue : %d" % bf
			var bf_col := Color(0.98, 0.58, 0.25, 1.0) if bf > 0 else Color(0.52, 0.88, 0.82, 0.90)
			draw_string(font, Vector2(160, 14), bf_txt, HORIZONTAL_ALIGNMENT_RIGHT, 102, 9, bf_col)

		# Médaillon 3D Joueur (Viewport à Vector2(8, 20))
		var med_rect := Rect2(8, 20, 48, 48)
		draw_rect(med_rect, Color(0.01, 0.07, 0.09, 0.95), true)
		draw_rect(med_rect, Color(0.24, 0.82, 0.94, 0.90), false, 1.2)
		if owner_hud._portrait_3d == null:
			draw_circle(Vector2(32, 38), 6.5, Color(0.38, 0.92, 0.98, 0.95))
			if font:
				draw_string(font, Vector2(9, 61), owner_hud._posture_label, HORIZONTAL_ALIGNMENT_CENTER, 46, 8, Color(0.75, 0.95, 1.0, 0.95))

		# 3 Barres S / A / E (Santé, Action, Esprit)
		var bh: _SwgPoolState = owner_hud._bar_health
		var ba: _SwgPoolState = owner_hud._bar_action
		var bm: _SwgPoolState = owner_hud._bar_mind
		_draw_swg_bar(Rect2(62, 21, 206, 13), bh.current, bh.base_max, bh.wounds, bh.buff, bh.fill_color, "S")
		_draw_swg_bar(Rect2(62, 37, 206, 13), ba.current, ba.base_max, ba.wounds, ba.buff, ba.fill_color, "A")
		_draw_swg_bar(Rect2(62, 53, 206, 13), bm.current, bm.base_max, bm.wounds, bm.buff, bm.fill_color, "E")

		# Posture et Statuts Tactiques SWG (sous le cadre HAM)
		var post_str: String = owner_hud._posture_label.to_upper()
		var post_col := Color(0.24, 0.88, 0.98, 0.95)
		if owner_hud._combat_posture == "kneeling":
			post_col = Color(0.98, 0.85, 0.25, 0.95)
		elif owner_hud._combat_posture == "prone":
			post_col = Color(0.95, 0.35, 0.25, 0.95)

		var bx := 282.0
		var by := 6.0
		# Badge Posture
		draw_rect(Rect2(bx, by, 72, 18), Color(0.02, 0.12, 0.16, 0.92), true)
		draw_rect(Rect2(bx, by, 72, 18), post_col, false, 1.2)
		if font:
			draw_string(font, Vector2(bx + 4, by + 13), post_str, HORIZONTAL_ALIGNMENT_CENTER, 64, 8, post_col)

		# Badges Statuts Combat Actifs (Dizzy, Knockdown, Stun, Blind, Intimidate)
		var stat_keys := ["knockdown", "stun", "dizzy", "blind", "intimidate"]
		var stat_colors := {
			"knockdown": Color(0.98, 0.32, 0.18, 1.0),
			"stun": Color(0.92, 0.15, 0.15, 1.0),
			"dizzy": Color(0.95, 0.84, 0.22, 1.0),
			"blind": Color(0.65, 0.65, 0.75, 1.0),
			"intimidate": Color(0.72, 0.35, 0.95, 1.0),
		}
		var sx := bx
		var sy := by + 22.0
		for sk in stat_keys:
			if owner_hud._combat_statuses.has(sk) and float(owner_hud._combat_statuses[sk]) > 0.0:
				var col: Color = stat_colors.get(sk, Color.WHITE)
				draw_rect(Rect2(sx, sy, 72, 16), Color(0.08, 0.02, 0.02, 0.94), true)
				draw_rect(Rect2(sx, sy, 72, 16), col, false, 1.0)
				if font:
					var sk_lbl: String = str(sk).to_upper().substr(0, 8)
					draw_string(font, Vector2(sx + 2, sy + 11), sk_lbl, HORIZONTAL_ALIGNMENT_CENTER, 68, 8, col)
				sy += 18.0

		# 2. Mini-cadres Groupe sous le joueur (comme sur le screenshot 1 SWG)
		_draw_group_member(78.0, "Nix · Escorte", "6m", 0.96, 0.88, 0.94)
		_draw_group_member(118.0, "Lia · La Perle", "14m", 1.0, 0.92, 1.0)

		# 3. Cadre Cible (Target HAM) dans le coin Haut-Droite de l'écran (comme sur le screenshot 2 SWG)
		if owner_hud._target_box and owner_hud._target_box.visible:
			var vp_w := get_viewport_rect().size.x
			if vp_w < 400.0:
				vp_w = 1280.0
			var tx := vp_w - 284.0
			var trect := Rect2(tx, 0, 260, 62)
			_draw_chamfer_box(trect, Color(0.02, 0.11, 0.14, 0.90), Color(0.95, 0.46, 0.24, 0.94), 7.0)
			draw_rect(Rect2(tx + 8, 4, 244, 13), Color(0.32, 0.11, 0.08, 0.92), true)
			if font:
				var d_str := " (%.0fm)" % owner_hud._target_dist_m if owner_hud._target_dist_m >= 0.0 else ""
				var t_hdr := "Cible : %s%s" % [owner_hud._target_name, d_str]
				draw_string(font, Vector2(tx + 12, 14), t_hdr, HORIZONTAL_ALIGNMENT_LEFT, 236, 9, Color(1.0, 0.88, 0.68, 1.0))
			_draw_swg_bar(Rect2(tx + 14, 21, 232, 10), 1000, 1000, 0, 0, Color(0.88, 0.18, 0.22, 1.0), "", true)
			_draw_swg_bar(Rect2(tx + 14, 34, 232, 10), 1000, 1000, 0, 0, Color(0.18, 0.78, 0.30, 1.0), "", true)
			_draw_swg_bar(Rect2(tx + 14, 47, 232, 10), 1000, 1000, 0, 0, Color(0.18, 0.48, 0.92, 1.0), "", true)


func _init() -> void:
	_bar_health = _SwgPoolState.new("S", Color(0.86, 0.14, 0.18, 1.0))
	_bar_action = _SwgPoolState.new("A", Color(0.16, 0.76, 0.28, 1.0))
	_bar_mind = _SwgPoolState.new("E", Color(0.16, 0.46, 0.92, 1.0))
	_target_box = Control.new()
	_target_box.name = "SwgTargetFrame"
	_target_box.visible = false
	add_child(_target_box)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(1280, 720)
	_apply_runtime_cfg()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)
	refresh_from_hub()


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_id = _HubRuntimeCfg.player_name("Voyageur")


func _make_swg_btn_style(hover: bool = false) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.28, 0.34, 0.95) if hover else Color(0.02, 0.14, 0.18, 0.92)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.55, 0.96, 1.0, 0.98) if hover else Color(0.22, 0.78, 0.88, 0.90)
	sb.set_corner_radius_all(3)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 3
	sb.content_margin_bottom = 3
	return sb


func _ensure_ui() -> void:
	if _canvas_draw != null:
		return
	_canvas_draw = _SwgHamCanvas.new()
	_canvas_draw.name = "SwgHamCanvas"
	_canvas_draw.owner_hud = self
	_canvas_draw.custom_minimum_size = Vector2(1280, 220)
	_canvas_draw.size = Vector2(1280, 220)
	_canvas_draw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_canvas_draw)

	if _portrait_3d == null:
		_portrait_3d = _SwgPortrait3D.new()
		_portrait_3d.position = Vector2(8, 20)
		_portrait_3d.size = Vector2(48, 48)
		_portrait_3d.custom_minimum_size = Vector2(48, 48)
		add_child(_portrait_3d)

	# Barrette Système Verticale en Bas-Droite (comme sur les captures SWG)
	_sys_dock = PanelContainer.new()
	_sys_dock.name = "SwgSystemDock"
	var sb_dock := StyleBoxFlat.new()
	sb_dock.bg_color = Color(0.015, 0.10, 0.13, 0.92)
	sb_dock.set_border_width_all(1)
	sb_dock.border_color = Color(0.24, 0.82, 0.92, 0.92)
	sb_dock.set_corner_radius_all(5)
	sb_dock.content_margin_left = 5
	sb_dock.content_margin_right = 5
	sb_dock.content_margin_top = 5
	sb_dock.content_margin_bottom = 5
	_sys_dock.add_theme_stylebox_override("panel", sb_dock)
	add_child(_sys_dock)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 3)
	_sys_dock.add_child(vbox)

	var hdr := Label.new()
	hdr.text = "◈ DATAPAD SYSTÈME"
	hdr.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hdr.add_theme_font_size_override("font_size", 9)
	hdr.add_theme_color_override("font_color", Color(0.58, 0.95, 1.0, 1.0))
	vbox.add_child(hdr)

	var buttons := [
		{"k": "character", "lbl": "👤 Fiche Perso HAM [C]"},
		{"k": "datapad", "lbl": "📟 Datapad & PCD [P]"},
		{"k": "skills", "lbl": "◈ Compétences [K]"},
		{"k": "survey", "lbl": "◎ Prospection [U]"},
		{"k": "experiment", "lbl": "⚙ Expérimenter [X]"},
		{"k": "inventory", "lbl": "🎒 Inventaire [I]"},
		{"k": "talents", "lbl": "🛠 Artisanat [T]"},
		{"k": "vendors", "lbl": "🏪 Bazar & Boutiques [B]"},
		{"k": "housing", "lbl": "🏠 Propriétés & Villes [H]"},
		{"k": "missions", "lbl": "📜 Missions [J]"},
		{"k": "map", "lbl": "🗺 Carte [M]"},
	]
	for b_info in buttons:
		var d: Dictionary = b_info
		var btn := Button.new()
		btn.text = str(d["lbl"])
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.custom_minimum_size = Vector2(138, 22)
		btn.add_theme_font_size_override("font_size", 10)
		btn.add_theme_color_override("font_color", Color(0.84, 0.98, 1.0, 1.0))
		btn.add_theme_stylebox_override("normal", _make_swg_btn_style(false))
		btn.add_theme_stylebox_override("hover", _make_swg_btn_style(true))
		btn.add_theme_stylebox_override("pressed", _make_swg_btn_style(true))
		var key_str := str(d["k"])
		btn.pressed.connect(func() -> void: quick_panel_requested.emit(key_str))
		vbox.add_child(btn)

	_reposition_dock()


func _reposition_dock() -> void:
	if _sys_dock == null or not is_inside_tree():
		return
	var vp := get_viewport_rect().size
	if vp.x < 400.0:
		vp = Vector2(1280, 720)
	# Positionné en bas à droite de l'écran (tenant compte des 11 boutons)
	_sys_dock.position = Vector2(vp.x - 166.0 - position.x, vp.y - 308.0 - position.y)
	if _canvas_draw:
		_canvas_draw.size = Vector2(vp.x, 220.0)


func _process(delta: float) -> void:
	_reposition_dock()
	_poll_timer += delta
	if _poll_timer >= poll_interval_sec:
		_poll_timer = 0.0
		refresh_from_hub()


func refresh_from_hub() -> void:
	_apply_runtime_cfg()
	if _http == null or not is_inside_tree():
		return
	var url := "%s/v1/medical/status?player=%s" % [sidecar_base_url.rstrip("/"), player_id.uri_encode()]
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	_http.request(url, [], HTTPClient.METHOD_GET)


func _on_http_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var d := parsed as Dictionary
	if bool(d.get("ok", false)):
		apply_ham_payload(d)


func apply_ham_payload(payload: Dictionary) -> void:
	_ensure_ui()
	var ham_dict: Dictionary = payload.get("ham", payload) if typeof(payload.get("ham", payload)) == TYPE_DICTIONARY else {}
	if ham_dict.has("health") and typeof(ham_dict["health"]) == TYPE_DICTIONARY:
		_ham["health"] = (ham_dict["health"] as Dictionary).duplicate()
		_bar_health.set_pool_data(_ham["health"])
	if ham_dict.has("action") and typeof(ham_dict["action"]) == TYPE_DICTIONARY:
		_ham["action"] = (ham_dict["action"] as Dictionary).duplicate()
		_bar_action.set_pool_data(_ham["action"])
	if ham_dict.has("mind") and typeof(ham_dict["mind"]) == TYPE_DICTIONARY:
		_ham["mind"] = (ham_dict["mind"] as Dictionary).duplicate()
		_bar_mind.set_pool_data(_ham["mind"])
	_ham["battle_fatigue"] = int(ham_dict.get("battle_fatigue", _ham.get("battle_fatigue", 0)))
	_medical_efficiency = float(payload.get("medical_efficiency_ratio", _medical_efficiency))
	if _portrait_3d and _bar_health:
		var total_cap := float(maxi(1, _bar_health.base_max + _bar_health.buff - _bar_health.wounds))
		var h_ratio := float(_bar_health.current) / total_cap
		_portrait_3d.update_ham_state(h_ratio, _ham["battle_fatigue"], _posture_label)
	if _canvas_draw:
		_canvas_draw.queue_redraw()


func set_posture(posture_name: String) -> void:
	var raw := posture_name.strip_edges().to_lower()
	if raw in ["kneeling", "accroupi"]:
		_combat_posture = "kneeling"
		_posture_label = "Accroupi"
	elif raw in ["prone", "couche", "couché"]:
		_combat_posture = "prone"
		_posture_label = "Couché"
	else:
		_combat_posture = "upright"
		_posture_label = "Debout"

	if _portrait_3d and _bar_health:
		var total_cap := float(maxi(1, _bar_health.base_max + _bar_health.buff - _bar_health.wounds))
		var h_ratio := float(_bar_health.current) / total_cap
		_portrait_3d.update_ham_state(h_ratio, int(_ham.get("battle_fatigue", 0)), _posture_label)
	if _canvas_draw:
		_canvas_draw.queue_redraw()


func apply_combat_status(payload: Dictionary) -> void:
	_ensure_ui()
	if payload.has("posture"):
		set_posture(str(payload["posture"]))
	if payload.has("statuses") and typeof(payload["statuses"]) == TYPE_DICTIONARY:
		_combat_statuses = (payload["statuses"] as Dictionary).duplicate()
	elif payload.has("active_statuses") and typeof(payload["active_statuses"]) == TYPE_DICTIONARY:
		_combat_statuses = (payload["active_statuses"] as Dictionary).duplicate()
	if _canvas_draw:
		_canvas_draw.queue_redraw()


func set_target_entity(entity_name: String, entity_kind: String = "npc", distance_m: float = -1.0) -> void:
	_ensure_ui()
	_target_name = entity_name.strip_edges()
	_target_kind = entity_kind.strip_edges()
	_target_dist_m = distance_m
	if _target_box:
		_target_box.visible = not _target_name.is_empty()
	if _canvas_draw:
		_canvas_draw.queue_redraw()
