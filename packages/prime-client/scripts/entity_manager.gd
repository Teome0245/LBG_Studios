# entity_manager.gd — Gestionnaire d'entites monde SWG
extends Node2D
class_name EntityManager

const _EntityScript = preload("res://scripts/entity.gd")
const _SpriteRegistry = preload("res://scripts/sprite_registry.gd")
const _HubFocus = preload("res://scripts/hub_focus.gd")
const COLOR_NPC := Color(1.0, 0.5, 0.1, 1.0)
const COLOR_OBJECT := Color(0.7, 0.7, 0.7, 0.8)

const ENTITY_SCENE := "res://scenes/entity.tscn"

var _entities: Dictionary = {}
var _entity_packed: PackedScene = null

func _ready() -> void:
	# load() retourne Variant — cast explicite PackedScene
	_entity_packed = load(ENTITY_SCENE) as PackedScene
	if _entity_packed == null:
		push_error("EntityManager: impossible de charger " + ENTITY_SCENE)

func spawn(object_id: int, core3_pos: Vector3,
		color: Color = COLOR_NPC,
		label: String = "",
		kind: String = "object",
		entity_key: String = "") -> Node:
	if _entities.has(object_id):
		return _entities[object_id]
	if _HubFocus.is_clutter(kind, label, entity_key):
		return null
	if _entity_packed == null:
		return null
	var entity: Node = _entity_packed.instantiate()
	entity.object_id = object_id
	entity.set_kind(kind)
	if entity_key != "":
		entity.set_entity_key(entity_key)
	add_child(entity)
	# Jitter uniquement objets anonymes — jamais joueurs (casse la locomotion via from_screen).
	if kind != "npc" and kind != "player":
		entity.set_display_jitter(_jitter_for_oid(object_id))
	entity.set_core3_position(core3_pos)
	entity.set_color(color)
	if label != "":
		entity.set_label(label)
	var tex: Texture2D = _SpriteRegistry.resolve_texture(kind, label, entity_key)
	var tint: Color = _SpriteRegistry.resolve_tint(kind, label)
	if tex:
		entity.set_sprite_texture(tex, tint)
	_entities[object_id] = entity
	return entity

static func _jitter_for_oid(oid: int) -> Vector2:
	# Écarte légèrement les entités au même point (hub LH)
	var angle := float(oid % 360) * (PI / 180.0)
	var ring := float(oid % 4)
	var radius := 14.0 + ring * 8.0
	return Vector2(cos(angle), sin(angle)) * radius

func move(object_id: int, core3_pos: Vector3) -> void:
	if not _entities.has(object_id):
		# Ne pas auto-créer un point gris (mv UDP avant sp).
		return
	_entities[object_id].set_core3_position(core3_pos)

func despawn(object_id: int) -> void:
	if _entities.has(object_id):
		_entities[object_id].queue_free()
		_entities.erase(object_id)

func clear() -> void:
	for entity in _entities.values():
		entity.queue_free()
	_entities.clear()

func get_entity(object_id: int) -> Node:
	return _entities.get(object_id, null)

func count() -> int:
	return _entities.size()

func get_all_entities() -> Array:
	return _entities.values()

func pick_interactable_at_screen(mouse_pos: Vector2) -> Node:
	return _pick_at_screen(mouse_pos, true)


func pick_entity_at_screen(mouse_pos: Vector2) -> Node:
	return _pick_at_screen(mouse_pos, false)


func _pick_at_screen(mouse_pos: Vector2, npc_only: bool) -> Node:
	var best: Node = null
	var best_dist := 1.0e12
	for entity_v in _entities.values():
		var entity: Node = entity_v as Node
		if entity == null:
			continue
		if npc_only and not entity.is_interactable():
			continue
		if not npc_only and entity.kind != "npc" and entity.kind != "player":
			continue
		var d: float = entity.screen_anchor().distance_squared_to(mouse_pos)
		if not entity.hit_test_screen(mouse_pos):
			continue
		if d < best_dist:
			best_dist = d
			best = entity
	return best
