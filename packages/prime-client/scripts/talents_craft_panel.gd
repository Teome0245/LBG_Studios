# talents_craft_panel.gd — M10 UI talents + craft (Control, hub :8787)
extends PanelContainer
class_name TalentsCraftPanel

signal craft_completed(result: Dictionary)

const SIDECAR_DEFAULT := "http://192.168.0.246:8787"
const PLAYER_DEFAULT := "local"

@export var sidecar_base_url: String = SIDECAR_DEFAULT
@export var player_id: String = PLAYER_DEFAULT
@export var panel_visible: bool = false

var _skills: Array = []
var _schematics: Array = []
var _status: String = "idle"
var _http: HTTPRequest
var _http_craft: HTTPRequest
var _pending: String = ""  # catalog | craft

var _title: Label
var _status_label: Label
var _recipe_label: Label
var _skills_list: ItemList
var _schematics_list: ItemList
var _refresh_btn: Button
var _craft_btn: Button

func _ready() -> void:
	visible = panel_visible
	_apply_hub_runtime_sidecar()
	_apply_mouse_filter()
	_apply_modal_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_done)
	_http_craft = HTTPRequest.new()
	add_child(_http_craft)
	_http_craft.request_completed.connect(_on_craft_http_done)
	call_deferred("_refresh_sidecar")


func _apply_hub_runtime_sidecar() -> void:
	if not HubRuntimeCfg.enabled():
		return
	sidecar_base_url = HubRuntimeCfg.http_url(sidecar_base_url)
	player_id = HubRuntimeCfg.player_name("Voyageur")


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
		_title.text = "Talents & Craft (M10)"
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
	if not _refresh_btn.pressed.is_connected(_refresh_sidecar):
		_refresh_btn.pressed.connect(_refresh_sidecar)
	_craft_btn = header.get_node_or_null("Craft") as Button
	if _craft_btn == null:
		_craft_btn = Button.new()
		_craft_btn.name = "Craft"
		_craft_btn.text = "Craft"
		header.add_child(_craft_btn)
	if not _craft_btn.pressed.is_connected(_craft_selected):
		_craft_btn.pressed.connect(_craft_selected)
	var skills_lbl := root.get_node_or_null("SkillsLabel") as Label
	if skills_lbl == null:
		skills_lbl = Label.new()
		skills_lbl.name = "SkillsLabel"
		skills_lbl.text = "Skills"
		root.add_child(skills_lbl)
	_skills_list = root.get_node_or_null("SkillsList") as ItemList
	if _skills_list == null:
		_skills_list = ItemList.new()
		_skills_list.name = "SkillsList"
		_skills_list.custom_minimum_size = Vector2(0, 100)
		_skills_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
		root.add_child(_skills_list)
	var schem_lbl := root.get_node_or_null("SchematicsLabel") as Label
	if schem_lbl == null:
		schem_lbl = Label.new()
		schem_lbl.name = "SchematicsLabel"
		schem_lbl.text = "Schematics"
		root.add_child(schem_lbl)
	_schematics_list = root.get_node_or_null("SchematicsList") as ItemList
	if _schematics_list == null:
		_schematics_list = ItemList.new()
		_schematics_list.name = "SchematicsList"
		_schematics_list.custom_minimum_size = Vector2(0, 100)
		_schematics_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
		root.add_child(_schematics_list)
	if not _schematics_list.item_selected.is_connected(_on_schematic_selected):
		_schematics_list.item_selected.connect(_on_schematic_selected)
	_recipe_label = root.get_node_or_null("Recipe") as Label
	if _recipe_label == null:
		_recipe_label = Label.new()
		_recipe_label.name = "Recipe"
		_recipe_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_recipe_label.add_theme_font_size_override("font_size", 11)
		_recipe_label.add_theme_color_override("font_color", Color(0.82, 0.78, 0.68, 0.95))
		_recipe_label.text = "Sélectionne un schematic · T craft · I inventaire"
		root.add_child(_recipe_label)
	_paint_lists()


func _apply_modal_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.055, 0.05, 0.94)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.78, 0.52, 0.28, 0.95)
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
		_apply_hub_runtime_sidecar()
		_refresh_sidecar()

func _refresh_sidecar() -> void:
	_apply_hub_runtime_sidecar()
	_status = "fetch…"
	_pending = "catalog"
	_paint_status()
	var url := sidecar_base_url.rstrip("/") + "/v1/catalog/skills"
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http.cancel_request()
	var err := _http.request(url, [], HTTPClient.METHOD_GET)
	if err != OK:
		_apply_local_mock("req_%d" % err)

func _on_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code < 200 or code >= 300:
		_apply_local_mock(code)
	else:
		var parsed = JSON.parse_string(body.get_string_from_utf8())
		if typeof(parsed) == TYPE_DICTIONARY:
			_skills = parsed.get("skills", [])
			_schematics = parsed.get("schematics", [])
			# Fallback forme catalog M10 (items) si le hub n'a pas encore enrichi.
			if (typeof(_skills) != TYPE_ARRAY or _skills.is_empty()) and typeof(parsed.get("items")) == TYPE_ARRAY:
				_skills = parsed.get("items", [])
			if typeof(_schematics) != TYPE_ARRAY:
				_schematics = []
			var fb := bool(parsed.get("fallback", false))
			var src := str(parsed.get("source", ""))
			_status = "live%s — %d skills, %d schematics%s" % [
				" (fallback catalog)" if fb else "",
				_skills.size() if typeof(_skills) == TYPE_ARRAY else 0,
				_schematics.size() if typeof(_schematics) == TYPE_ARRAY else 0,
				(" · " + src) if src != "" else "",
			]
		else:
			_status = "parse error"
			_apply_local_mock("parse")
			return
	_paint_lists()

func _craft_selected() -> void:
	if _schematics_list == null:
		return
	var idxs := _schematics_list.get_selected_items()
	if idxs.is_empty():
		_status = "sélectionne un schematic"
		_paint_status()
		return
	var i: int = idxs[0]
	if i < 0 or i >= _schematics.size():
		return
	var sc = _schematics[i]
	if typeof(sc) != TYPE_DICTIONARY:
		_status = "schematic invalide"
		_paint_status()
		return
	var sid := str(sc.get("id", ""))
	if sid == "":
		_status = "schematic sans id (mock hors ligne)"
		_paint_status()
		return
	_status = "craft %s…" % sid
	_paint_status()
	var url := sidecar_base_url.rstrip("/") + "/v1/craft/combine"
	var payload := JSON.stringify({"player": player_id, "schematic_id": sid})
	var headers := PackedStringArray(["Content-Type: application/json"])
	if _http_craft.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		_http_craft.cancel_request()
	var err := _http_craft.request(url, headers, HTTPClient.METHOD_POST, payload)
	if err != OK:
		_status = "craft req_%d" % err
		_paint_status()

func _on_craft_http_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var parsed = JSON.parse_string(body.get_string_from_utf8()) if body.size() > 0 else null
	if result != HTTPRequest.RESULT_SUCCESS:
		_status = "craft réseau KO"
		_paint_status()
		return
	if code == 404:
		_status = "craft indisponible (sidecar 404)"
		if _craft_btn:
			_craft_btn.disabled = true
		_paint_status()
		return
	if typeof(parsed) != TYPE_DICTIONARY:
		_status = "craft parse error (%d)" % code
		_paint_status()
		return
	if not bool(parsed.get("ok", false)):
		_status = _craft_error_text(parsed, code)
		_paint_status()
		return
	var crafted = parsed.get("crafted", {})
	var cname := str(crafted.get("name", crafted.get("id", "?"))) if typeof(crafted) == TYPE_DICTIONARY else "?"
	var cqty := int(crafted.get("qty", 1)) if typeof(crafted) == TYPE_DICTIONARY else 1
	_status = "craft OK — %s ×%d" % [cname, cqty]
	var cost_line := _cost_status_suffix(parsed)
	if cost_line != "":
		_status = "%s · %s" % [_status, cost_line]
	_paint_status()
	craft_completed.emit(parsed)

func _cost_status_suffix(parsed: Dictionary) -> String:
	## D1 — pastille coût hub.
	var cost = parsed.get("cost", {})
	if typeof(cost) != TYPE_DICTIONARY:
		return ""
	var summary := str(cost.get("summary", "")).strip_edges()
	if summary.is_empty():
		return ""
	return "coût %s" % summary

func _craft_error_text(parsed: Dictionary, code: int) -> String:
	var err := str(parsed.get("error", code))
	var base := ""
	match err:
		"missing_inputs":
			base = "manque %s (%s/%s)" % [
				str(parsed.get("item_id", "?")),
				str(parsed.get("have", 0)),
				str(parsed.get("need", "?")),
			]
		"missing_skill":
			base = "skill requis: %s" % str(parsed.get("requires_skill", "?"))
		"unknown_schematic":
			base = "schematic inconnu"
		"schematic_draft":
			base = "schematic draft (non craftable)"
		_:
			base = "craft échec: %s" % err
	var cost_line := _cost_status_suffix(parsed)
	if cost_line != "":
		return "%s · %s" % [base, cost_line]
	return base

func _on_schematic_selected(index: int) -> void:
	_update_recipe_label(index)

func _update_recipe_label(index: int = -1) -> void:
	if _recipe_label == null:
		return
	if index < 0:
		if _schematics_list:
			var sel := _schematics_list.get_selected_items()
			index = sel[0] if not sel.is_empty() else -1
	if index < 0 or index >= _schematics.size():
		_recipe_label.text = "Sélectionne un schematic · Craft consomme l'inventaire M10"
		return
	var sc = _schematics[index]
	if typeof(sc) != TYPE_DICTIONARY:
		_recipe_label.text = str(sc)
		return
	var parts: PackedStringArray = PackedStringArray()
	var inputs = sc.get("inputs", [])
	if typeof(inputs) == TYPE_ARRAY:
		for inp in inputs:
			if typeof(inp) == TYPE_DICTIONARY:
				parts.append("%s×%s" % [str(inp.get("id", "?")), str(inp.get("qty", 1))])
	var out = sc.get("output", {})
	var out_s := "?"
	if typeof(out) == TYPE_DICTIONARY:
		out_s = "%s×%s" % [str(out.get("id", sc.get("id", "?"))), str(out.get("qty", 1))]
	var req := str(sc.get("requires_skill", ""))
	var line := "Recette: %s → %s" % [", ".join(parts) if parts.size() > 0 else "(sans inputs)", out_s]
	if req != "":
		line += " · skill %s" % req
	_recipe_label.text = line

func _apply_local_mock(code: Variant) -> void:
	_status = "hors ligne (%s) · mock local" % str(code)
	# Miroir packages/cortex/content/m10/m10_skills_catalog.json (schema 3, vitrine)
	_skills = [
		{"id": "prospecteur_r1", "name": "Prospecteur · rang 1", "tree": "gathering", "rank": 1},
		{"id": "artisan_rue_r1", "name": "Artisan de rue · rang 1", "tree": "crafting", "rank": 1},
		{"id": "medecine_camp_r1", "name": "Médecine de camp · rang 1", "tree": "medicine", "rank": 1},
		{"id": "pilotage_shuttle_r1", "name": "Pilotage shuttle · rang 1", "tree": "pilot", "rank": 1},
	]
	_schematics = [
		{
			"id": "kit_reparation",
			"name": "Kit de réparation",
			"category": "tool",
			"requires_skill": "artisan_rue_r1",
			"inputs": [{"id": "scrap_metal", "qty": 2}, {"id": "binding_tape", "qty": 1}],
			"output": {"id": "kit_reparation", "qty": 1},
		},
		{
			"id": "ration_compacte",
			"name": "Ration compacte",
			"category": "consumable",
			"requires_skill": "artisan_rue_r1",
			"inputs": [{"id": "dried_grain", "qty": 2}, {"id": "water_capsule", "qty": 1}],
			"output": {"id": "ration_compacte", "qty": 1},
		},
	]

func _paint_status() -> void:
	if _status_label:
		_status_label.text = _status
		if _status.begins_with("hors ligne"):
			_status_label.add_theme_color_override("font_color", Color(0.95, 0.7, 0.35, 1))
		elif _status.begins_with("live") or _status.begins_with("craft OK"):
			_status_label.add_theme_color_override("font_color", Color(0.55, 0.9, 0.65, 1))
		elif _status.begins_with("craft échec") or _status.begins_with("craft réseau") or _status.begins_with("craft indisponible") or _status.begins_with("manque") or _status.begins_with("skill requis"):
			_status_label.add_theme_color_override("font_color", Color(0.95, 0.45, 0.4, 1))
		else:
			_status_label.add_theme_color_override("font_color", Color(0.75, 0.82, 0.9, 1))

func _paint_lists() -> void:
	_paint_status()
	if _skills_list == null or _schematics_list == null:
		return
	_skills_list.clear()
	if _skills.is_empty():
		_skills_list.add_item("(aucun skill)")
	else:
		for s in _skills:
			var label := str(s.get("name", s)) if typeof(s) == TYPE_DICTIONARY else str(s)
			if typeof(s) == TYPE_DICTIONARY and str(s.get("tree", "")) != "":
				label = "%s  [%s]" % [label, str(s.get("tree"))]
			_skills_list.add_item(label)
	_schematics_list.clear()
	if _schematics.is_empty():
		_schematics_list.add_item("(aucun schematic)")
	else:
		for sc in _schematics:
			var slabel := str(sc.get("name", sc)) if typeof(sc) == TYPE_DICTIONARY else str(sc)
			if typeof(sc) == TYPE_DICTIONARY and str(sc.get("requires_skill", "")) != "":
				slabel = "%s  ← %s" % [slabel, str(sc.get("requires_skill"))]
			_schematics_list.add_item(slabel)
	_update_recipe_label()
