extends PanelContainer
## Interface SWG Pre-CU (2D Top-Down) — Terminal de Bazar Public & Boutiques Joueurs :
## 1. Arborescence SWG des catégories (Minéraux, Chimiques, Organiques, Composants, Armes, Mobilier...).
## 2. Tableau central des lots (Nom, Vendeur, Localisation, Type Immédiat/Enchère, Prix en crédits).
## 3. Détails d'inspection du lot (Qualité des ressources, stats d'usinage) et Achat / Enchère.
## 4. Onglet de Mise en Vente (Cap 20 000 cr sur le Bazar Public de Lost Heaven, ou Vendeur Privé).

signal item_purchased(item_id: String, price: int)
signal panel_closed()

const _HubRuntimeCfg := preload("res://scripts/hub_runtime_cfg.gd")

var sidecar_base_url: String = "http://192.168.0.246:8787"
var player_name: String = "Voyageur"
var player_credits: int = 15000
var panel_visible: bool = false

var _current_tab: int = 0 # 0=Browse, 1=My Sales, 2=Sell
var _selected_category: String = "all"
var _filter_text: String = ""

# Catalogue local de fallback fidèle à SWG Pre-CU
var _market_items: Array = [
	{
		"id": "lot_scrap_01",
		"name": "Ferraille Recyclée Haute Densité",
		"category": "minerals",
		"qty": 250,
		"price": 750,
		"type": "instant",
		"vendor": "Scrap-Master Nix",
		"location": "Bazar Public Lost Heaven",
		"desc": "Qualité minerai: 88%. Idéal pour la fabrication de kits mécatroniques et de châssis légers."
	},
	{
		"id": "lot_meat_02",
		"name": "Viande Maigre de Chacal des Sables",
		"category": "organics",
		"qty": 40,
		"price": 320,
		"type": "instant",
		"vendor": "Chasseur Vane",
		"location": "Dépôt des Dunes Est",
		"desc": "Dépecée fraîchement. Protéines pures pour alimentation de familiers ou stimpacks."
	},
	{
		"id": "lot_leather_03",
		"name": "Cuir Renforcé de Dune Crawler",
		"category": "organics",
		"qty": 80,
		"price": 1200,
		"type": "instant",
		"vendor": "Tanneur Bram",
		"location": "Boutique Le Mirage",
		"desc": "Résistance à la chaleur: 75%. Composant pour tentes nomades et vestes composites."
	},
	{
		"id": "lot_comp_actuator",
		"name": "Micro-Actuateur Mécanique MK-2",
		"category": "components",
		"qty": 5,
		"price": 2500,
		"type": "instant",
		"vendor": "Atelier Lia",
		"location": "Bazar Public Lost Heaven",
		"desc": "Pièce d'horlogerie et servomoteurs. Requis pour usines d'assemblage d'armes."
	},
	{
		"id": "lot_camp_kit",
		"name": "Kit de Campement Nomade Déployable",
		"category": "furniture",
		"qty": 1,
		"price": 1800,
		"type": "instant",
		"vendor": "Scout Valen",
		"location": "Bazar Public Lost Heaven",
		"desc": "Permet de déployer un camp scout dans les dunes avec accélération de regen HAM de 150%."
	},
	{
		"id": "lot_weapon_carbine",
		"name": "Carabine à Répétition Mod-7",
		"category": "weapons",
		"qty": 1,
		"price": 8500,
		"type": "auction",
		"auction_bid": 6200,
		"vendor": "Armurerie d'Odo",
		"location": "Boutique d'Armures Odo",
		"desc": "Dégâts cinétiques 120-190. Vitesse 2.8s. Expérimentation réussie 4/4 points."
	}
]

var _my_sales: Array = [
	{
		"id": "my_lot_01",
		"name": "Composant Électronique Simple",
		"qty": 10,
		"price": 400,
		"status": "En Vente (Bazar)"
	}
]

# Références UI
var _categories_list: ItemList = null
var _items_list: ItemList = null
var _search_input: LineEdit = null
var _detail_title: Label = null
var _detail_desc: Label = null
var _detail_price_lbl: Label = null
var _btn_buy: Button = null
var _credits_lbl: Label = null

var _box_browse: VBoxContainer = null
var _box_my_sales: VBoxContainer = null
var _box_sell: VBoxContainer = null

var _my_sales_list: ItemList = null
var _input_sell_name: LineEdit = null
var _input_sell_qty: SpinBox = null
var _input_sell_price: SpinBox = null

var _http: HTTPRequest = null


func _ready() -> void:
	visible = panel_visible
	custom_minimum_size = Vector2(620, 480)
	_apply_runtime_cfg()
	_apply_style()
	_ensure_ui()
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_http_completed)
	refresh_catalog()


func _ensure_ui() -> void:
	_build_ui()


func _apply_runtime_cfg() -> void:
	if _HubRuntimeCfg.enabled():
		sidecar_base_url = _HubRuntimeCfg.http_url(sidecar_base_url)
		player_name = _HubRuntimeCfg.player_name("Voyageur")


func _apply_style() -> void:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.015, 0.08, 0.12, 0.96)
	sb.set_border_width_all(2)
	sb.border_color = Color(0.24, 0.85, 0.95, 0.95)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 8
	sb.content_margin_bottom = 12
	add_theme_stylebox_override("panel", sb)


func _make_swg_btn(txt: String, active: bool = false) -> Button:
	var btn := Button.new()
	btn.text = txt
	btn.add_theme_font_size_override("font_size", 10)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.32, 0.40, 0.95) if active else Color(0.02, 0.15, 0.19, 0.90)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.95, 0.84, 0.32, 1.0) if active else Color(0.22, 0.78, 0.88, 0.85)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	btn.add_theme_stylebox_override("normal", sb)
	return btn


func _build_ui() -> void:
	for c in get_children():
		if c != _http:
			c.queue_free()

	var root_vbox := VBoxContainer.new()
	root_vbox.add_theme_constant_override("separation", 8)
	add_child(root_vbox)

	# --- En-tête ---
	var header := HBoxContainer.new()
	var title_lbl := Label.new()
	title_lbl.text = "◈ BAZAR PUBLIC & BOUTIQUES DU SECTEUR ◈"
	title_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_lbl.add_theme_font_size_override("font_size", 13)
	title_lbl.add_theme_color_override("font_color", Color(0.96, 0.86, 0.38, 1.0))
	header.add_child(title_lbl)

	_credits_lbl = Label.new()
	_credits_lbl.text = "Crédits : %d cr" % player_credits
	_credits_lbl.add_theme_font_size_override("font_size", 11)
	_credits_lbl.add_theme_color_override("font_color", Color(0.4, 0.95, 0.6, 1.0))
	header.add_child(_credits_lbl)

	var close_btn := Button.new()
	close_btn.text = " ✕ "
	close_btn.add_theme_font_size_override("font_size", 11)
	close_btn.pressed.connect(close_panel)
	header.add_child(close_btn)
	root_vbox.add_child(header)

	var hsep1 := HSeparator.new()
	root_vbox.add_child(hsep1)

	# --- Barre d'onglets SWG ---
	var tab_row := HBoxContainer.new()
	tab_row.add_theme_constant_override("separation", 8)

	var btn_browse := _make_swg_btn(" 🛒 Acheter / Parcourir ", _current_tab == 0)
	btn_browse.pressed.connect(func() -> void: _switch_tab(0))
	tab_row.add_child(btn_browse)

	var btn_sales := _make_swg_btn(" 📦 Mes Ventes en Cours ", _current_tab == 1)
	btn_sales.pressed.connect(func() -> void: _switch_tab(1))
	tab_row.add_child(btn_sales)

	var btn_sell := _make_swg_btn(" ➕ Mettre en Vente un Lot ", _current_tab == 2)
	btn_sell.pressed.connect(func() -> void: _switch_tab(2))
	tab_row.add_child(btn_sell)

	root_vbox.add_child(tab_row)

	# --- Conteneurs par onglet ---
	# 1. Onglet Parcourir
	_box_browse = VBoxContainer.new()
	_box_browse.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_browse.add_theme_constant_override("separation", 6)
	_build_browse_tab(_box_browse)
	root_vbox.add_child(_box_browse)

	# 2. Onglet Mes Ventes
	_box_my_sales = VBoxContainer.new()
	_box_my_sales.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_my_sales.add_theme_constant_override("separation", 6)
	_build_my_sales_tab(_box_my_sales)
	root_vbox.add_child(_box_my_sales)

	# 3. Onglet Déposer une Vente
	_box_sell = VBoxContainer.new()
	_box_sell.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_box_sell.add_theme_constant_override("separation", 8)
	_build_sell_tab(_box_sell)
	root_vbox.add_child(_box_sell)

	_switch_tab(_current_tab)


func _build_browse_tab(parent: VBoxContainer) -> void:
	# Barre de recherche & filtres
	var search_row := HBoxContainer.new()
	search_row.add_theme_constant_override("separation", 6)

	var lbl_s := Label.new()
	lbl_s.text = "Filtre :"
	lbl_s.add_theme_font_size_override("font_size", 10)
	search_row.add_child(lbl_s)

	_search_input = LineEdit.new()
	_search_input.placeholder_text = "Nom d'objet, ressource, vendeur..."
	_search_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_search_input.add_theme_font_size_override("font_size", 10)
	_search_input.text_changed.connect(func(new_text: String) -> void:
		_filter_text = new_text.to_lower()
		_populate_items_list()
	)
	search_row.add_child(_search_input)

	var btn_refresh := Button.new()
	btn_refresh.text = " ↻ Actualiser "
	btn_refresh.add_theme_font_size_override("font_size", 10)
	btn_refresh.pressed.connect(refresh_catalog)
	search_row.add_child(btn_refresh)

	parent.add_child(search_row)

	# Corps 2 Colonnes (Gauche: Catégories SWG, Droite: Tableau des Lots)
	var split_box := HBoxContainer.new()
	split_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	split_box.add_theme_constant_override("separation", 10)

	# Colonne Catégories SWG
	var cat_box := VBoxContainer.new()
	cat_box.custom_minimum_size = Vector2(160, 0)
	var cat_hdr := Label.new()
	cat_hdr.text = "CATÉGORIES DU BAZAR"
	cat_hdr.add_theme_font_size_override("font_size", 9)
	cat_hdr.add_theme_color_override("font_color", Color(0.4, 0.85, 0.95, 0.9))
	cat_box.add_child(cat_hdr)

	_categories_list = ItemList.new()
	_categories_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_categories_list.add_theme_font_size_override("font_size", 10)

	var cats := [
		{"k": "all", "t": "◈ Toutes Catégories"},
		{"k": "minerals", "t": "⛏ Minéraux & Métaux"},
		{"k": "organics", "t": "🥩 Organiques & Cuir"},
		{"k": "chemicals", "t": "🧪 Chimiques & Gaz"},
		{"k": "components", "t": "⚙ Composants d'Usine"},
		{"k": "weapons", "t": "⚔ Armes & Munitions"},
		{"k": "furniture", "t": "⛺ Mobilier & Tentes"}
	]
	for c_item in cats:
		var d: Dictionary = c_item
		var idx: int = _categories_list.add_item(str(d["t"]))
		_categories_list.set_item_metadata(idx, str(d["k"]))

	_categories_list.item_selected.connect(_on_category_selected)
	_categories_list.select(0)
	cat_box.add_child(_categories_list)
	split_box.add_child(cat_box)

	# Colonne Liste des Lots
	var items_box := VBoxContainer.new()
	items_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var items_hdr := Label.new()
	items_hdr.text = "LOTS EN VENTE (PRIX IMMÉDIATS & ENCHÈRES) :"
	items_hdr.add_theme_font_size_override("font_size", 9)
	items_hdr.add_theme_color_override("font_color", Color(0.4, 0.85, 0.95, 0.9))
	items_box.add_child(items_hdr)

	_items_list = ItemList.new()
	_items_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_items_list.add_theme_font_size_override("font_size", 10)
	_items_list.item_selected.connect(_on_item_selected)
	items_box.add_child(_items_list)
	split_box.add_child(items_box)

	parent.add_child(split_box)

	# Cadre d'inspection et achat
	var inspect_panel := PanelContainer.new()
	var sb_insp := StyleBoxFlat.new()
	sb_insp.bg_color = Color(0.02, 0.12, 0.16, 0.85)
	sb_insp.set_border_width_all(1)
	sb_insp.border_color = Color(0.24, 0.72, 0.82, 0.7)
	sb_insp.set_corner_radius_all(4)
	sb_insp.content_margin_left = 8
	sb_insp.content_margin_right = 8
	sb_insp.content_margin_top = 6
	sb_insp.content_margin_bottom = 6
	inspect_panel.add_theme_stylebox_override("panel", sb_insp)

	var insp_hbox := HBoxContainer.new()
	insp_hbox.add_theme_constant_override("separation", 10)

	var insp_vbox := VBoxContainer.new()
	insp_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	_detail_title = Label.new()
	_detail_title.text = "Sélectionnez un lot dans la liste pour examiner ses attributs."
	_detail_title.add_theme_font_size_override("font_size", 11)
	_detail_title.add_theme_color_override("font_color", Color(0.96, 0.88, 0.42, 1.0))
	insp_vbox.add_child(_detail_title)

	_detail_desc = Label.new()
	_detail_desc.text = ""
	_detail_desc.add_theme_font_size_override("font_size", 9)
	_detail_desc.add_theme_color_override("font_color", Color(0.75, 0.88, 0.95, 0.9))
	insp_vbox.add_child(_detail_desc)
	insp_hbox.add_child(insp_vbox)

	var buy_vbox := VBoxContainer.new()
	_detail_price_lbl = Label.new()
	_detail_price_lbl.text = "Prix : ---"
	_detail_price_lbl.add_theme_font_size_override("font_size", 12)
	_detail_price_lbl.add_theme_color_override("font_color", Color(0.4, 0.95, 0.6, 1.0))
	buy_vbox.add_child(_detail_price_lbl)

	_btn_buy = Button.new()
	_btn_buy.text = " Acheter le Lot "
	_btn_buy.disabled = true
	_btn_buy.add_theme_font_size_override("font_size", 11)
	_btn_buy.pressed.connect(_on_buy_pressed)
	buy_vbox.add_child(_btn_buy)
	insp_hbox.add_child(buy_vbox)

	inspect_panel.add_child(insp_hbox)
	parent.add_child(inspect_panel)


func _build_my_sales_tab(parent: VBoxContainer) -> void:
	var hdr := Label.new()
	hdr.text = "VOS LOTS EN VENTE DANS LES BAZARS ET BOUTIQUES PERSONNELLES :"
	hdr.add_theme_font_size_override("font_size", 10)
	hdr.add_theme_color_override("font_color", Color(0.4, 0.85, 0.95, 0.9))
	parent.add_child(hdr)

	_my_sales_list = ItemList.new()
	_my_sales_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_my_sales_list.add_theme_font_size_override("font_size", 10)
	parent.add_child(_my_sales_list)

	var bot_row := HBoxContainer.new()
	var btn_cancel := Button.new()
	btn_cancel.text = " Retirer de la Vente "
	btn_cancel.add_theme_font_size_override("font_size", 10)
	btn_cancel.pressed.connect(_on_cancel_sale_pressed)
	bot_row.add_child(btn_cancel)
	parent.add_child(bot_row)


func _build_sell_tab(parent: VBoxContainer) -> void:
	var hdr := Label.new()
	hdr.text = "DÉPOSER UN LOT SUR LE BAZAR PUBLIC DE LOST HEAVEN (PLAFOND: 20 000 CR) :"
	hdr.add_theme_font_size_override("font_size", 10)
	hdr.add_theme_color_override("font_color", Color(0.96, 0.88, 0.42, 1.0))
	parent.add_child(hdr)

	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 8)

	var l1 := Label.new()
	l1.text = "Désignation du Lot :"
	l1.add_theme_font_size_override("font_size", 10)
	grid.add_child(l1)

	_input_sell_name = LineEdit.new()
	_input_sell_name.placeholder_text = "ex: Ferraille Recyclée, Stimpack..."
	_input_sell_name.custom_minimum_size = Vector2(280, 0)
	_input_sell_name.add_theme_font_size_override("font_size", 10)
	grid.add_child(_input_sell_name)

	var l2 := Label.new()
	l2.text = "Quantité :"
	l2.add_theme_font_size_override("font_size", 10)
	grid.add_child(l2)

	_input_sell_qty = SpinBox.new()
	_input_sell_qty.min_value = 1
	_input_sell_qty.max_value = 1000
	_input_sell_qty.value = 10
	grid.add_child(_input_sell_qty)

	var l3 := Label.new()
	l3.text = "Prix Demandé (Crédits) :"
	l3.add_theme_font_size_override("font_size", 10)
	grid.add_child(l3)

	_input_sell_price = SpinBox.new()
	_input_sell_price.min_value = 1
	_input_sell_price.max_value = 20000
	_input_sell_price.value = 500
	grid.add_child(_input_sell_price)

	parent.add_child(grid)

	var info_lbl := Label.new()
	info_lbl.text = "ℹ Les ventes au Bazar sont taxées à 5% par la municipalité.\nPour vendre des objets à plus de 20 000 cr, déployez un Vendeur Privé dans votre maison."
	info_lbl.add_theme_font_size_override("font_size", 9)
	info_lbl.add_theme_color_override("font_color", Color(0.65, 0.85, 0.95, 0.8))
	parent.add_child(info_lbl)

	var btn_confirm := Button.new()
	btn_confirm.text = " ✦ Confirmer la Mise en Vente au Bazar ✦ "
	btn_confirm.add_theme_font_size_override("font_size", 11)
	btn_confirm.pressed.connect(_on_confirm_sell_pressed)
	parent.add_child(btn_confirm)


func _switch_tab(tab_idx: int) -> void:
	_current_tab = tab_idx
	if _box_browse:
		_box_browse.visible = (_current_tab == 0)
	if _box_my_sales:
		_box_my_sales.visible = (_current_tab == 1)
	if _box_sell:
		_box_sell.visible = (_current_tab == 2)

	if _current_tab == 0:
		_populate_items_list()
	elif _current_tab == 1:
		_populate_my_sales()


func _on_category_selected(idx: int) -> void:
	if _categories_list == null:
		return
	_selected_category = str(_categories_list.get_item_metadata(idx))
	_populate_items_list()


func _populate_items_list() -> void:
	if _items_list == null:
		return
	_items_list.clear()

	for item in _market_items:
		var d: Dictionary = item
		var cat := str(d.get("category", ""))
		var item_name := str(d.get("name", ""))

		if _selected_category != "all" and cat != _selected_category:
			continue
		if not _filter_text.is_empty():
			var search_space := (item_name + " " + str(d.get("vendor", "")) + " " + str(d.get("desc", ""))).to_lower()
			if not search_space.contains(_filter_text):
				continue

		var price: int = int(d.get("price", 0))
		var qty: int = int(d.get("qty", 1))
		var v_name := str(d.get("vendor", "Inconnu"))
		var row_txt := "%s (×%d) — %d cr — [%s]" % [item_name, qty, price, v_name]
		var new_idx: int = _items_list.add_item(row_txt)
		_items_list.set_item_metadata(new_idx, d)


func _on_item_selected(idx: int) -> void:
	if _items_list == null:
		return
	var d: Dictionary = _items_list.get_item_metadata(idx)
	if d.is_empty():
		return

	if _detail_title:
		_detail_title.text = "%s (Quantité : %d)" % [str(d.get("name", "")), int(d.get("qty", 1))]
	if _detail_desc:
		_detail_desc.text = "%s\nVendeur : %s | Localisation : %s" % [str(d.get("desc", "")), str(d.get("vendor", "")), str(d.get("location", ""))]
	if _detail_price_lbl:
		_detail_price_lbl.text = "Prix : %d cr" % int(d.get("price", 0))
	if _btn_buy:
		_btn_buy.disabled = false


func _populate_my_sales() -> void:
	if _my_sales_list == null:
		return
	_my_sales_list.clear()
	for s in _my_sales:
		var d: Dictionary = s
		var row := "%s (×%d) — %d cr — Statut : %s" % [str(d.get("name", "")), int(d.get("qty", 1)), int(d.get("price", 0)), str(d.get("status", "En vente"))]
		_my_sales_list.add_item(row)


func _on_buy_pressed() -> void:
	var sel: PackedInt32Array = _items_list.get_selected_items() if _items_list else PackedInt32Array()
	if sel.is_empty():
		return
	var d: Dictionary = _items_list.get_item_metadata(sel[0])
	var item_id := str(d.get("id", ""))
	var price := int(d.get("price", 0))

	if player_credits < price:
		if _detail_desc:
			_detail_desc.text = "Solde insuffisant ! Vous disposez de %d cr." % player_credits
		return

	player_credits -= price
	if _credits_lbl:
		_credits_lbl.text = "Crédits : %d cr" % player_credits

	# Suppression locale du lot
	_market_items.erase(d)
	_populate_items_list()
	if _btn_buy:
		_btn_buy.disabled = true
	if _detail_title:
		_detail_title.text = "Lot acheté avec succès ! Transféré dans votre inventaire."

	item_purchased.emit(item_id, price)

	# Requête HTTP vers le hub
	if _http and _http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
		var url := "%s/v1/bazaar/buy" % sidecar_base_url.rstrip("/")
		_http.request(url, PackedStringArray(["Content-Type: application/json"]), HTTPClient.METHOD_POST, JSON.stringify({
			"buyer": player_name,
			"item_id": item_id
		}))


func _on_confirm_sell_pressed() -> void:
	var s_name := _input_sell_name.text.strip_edges() if _input_sell_name else ""
	if s_name.is_empty():
		return
	var qty := int(_input_sell_qty.value) if _input_sell_qty else 1
	var pr := int(_input_sell_price.value) if _input_sell_price else 100

	var new_sale := {
		"id": "sale_%d" % Time.get_ticks_msec(),
		"name": s_name,
		"qty": qty,
		"price": pr,
		"status": "En Vente (Bazar Public)"
	}
	_my_sales.append(new_sale)

	# Ajout immédiat au catalogue browse pour rétroaction
	_market_items.append({
		"id": new_sale["id"],
		"name": s_name,
		"category": "components",
		"qty": qty,
		"price": pr,
		"type": "instant",
		"vendor": player_name,
		"location": "Bazar Public Lost Heaven",
		"desc": "Lot personnel mis en vente par le joueur."
	})

	if _input_sell_name:
		_input_sell_name.text = ""
	_switch_tab(1)


func _on_cancel_sale_pressed() -> void:
	var sel: PackedInt32Array = _my_sales_list.get_selected_items() if _my_sales_list else PackedInt32Array()
	if sel.is_empty() or sel[0] >= _my_sales.size():
		return
	_my_sales.remove_at(sel[0])
	_populate_my_sales()


func toggle() -> void:
	if visible:
		close_panel()
	else:
		open_panel()


func open_panel() -> void:
	visible = true
	panel_visible = true
	refresh_catalog()


func close_panel() -> void:
	visible = false
	panel_visible = false
	panel_closed.emit()


func refresh_catalog() -> void:
	_apply_runtime_cfg()
	if _http == null or not is_inside_tree():
		return
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	var url := "%s/v1/bazaar/browse?category=%s&limit=20" % [sidecar_base_url.rstrip("/"), _selected_category.uri_encode()]
	_http.request(url, [], HTTPClient.METHOD_GET)


func _on_http_completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or body.is_empty():
		return
	var parsed: Variant = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) == TYPE_DICTIONARY and (parsed as Dictionary).has("items"):
		var it_arr: Array = (parsed as Dictionary)["items"]
		if not it_arr.is_empty():
			_market_items = it_arr
			_populate_items_list()
