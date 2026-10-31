extends RefCounted
class_name AgentEnvironmentAdapter
## Contrat d'Environnement Universel pour Joueurs IA (Ticket 2.1 — O3).
##
## Découple la prise de décision de l'agent de l'implémentation de la simulation.
## L'agent interagit uniquement par observations standardisées et intentions d'action.

const ACTION_TYPE_MOVE := "MOVE"
const ACTION_TYPE_SAY := "SAY"
const ACTION_TYPE_EMOTE := "EMOTE"
const ACTION_TYPE_INTERACT := "INTERACT_POI"
const ACTION_TYPE_TRADE := "TRADE"
const ACTION_TYPE_CRAFT := "CRAFT"
const ACTION_TYPE_IDLE := "IDLE"
const ACTION_TYPE_FORMATION_FOLLOW := "FORMATION_FOLLOW"
const ACTION_TYPE_COVER_TARGET := "COVER_TARGET"
const ACTION_TYPE_TACTICAL_RETREAT := "TACTICAL_RETREAT"

## Émetteur d'événements observables par les agents
signal observation_updated(bot_id: String, observation: Dictionary)
signal action_completed(bot_id: String, action_type: String, result: Dictionary)


## Récupère le vecteur d'observation complet pour un agent donné
func get_observation(bot_id: String) -> Dictionary:
	return make_observation(
		bot_id,
		Vector3.ZERO,
		"default_zone",
		100,
		0,
		[],
		[],
		[],
		{},
		[]
	)


## Exécute une action demandée par l'agent et retourne le résultat de validation
func perform_action(bot_id: String, action: Dictionary) -> Dictionary:
	var act_type := str(action.get("type", ACTION_TYPE_IDLE))
	return {
		"ok": false,
		"action": act_type,
		"agent_id": bot_id,
		"error": "not_implemented_in_base_adapter",
		"timestamp": Time.get_unix_time_from_system()
	}


## Factory pour construire une observation standardisée et typée
static func make_observation(
	bot_id: String,
	pos: Vector3,
	zone: String = "scrapaltai",
	health: int = 100,
	credits: int = 0,
	nearby_entities: Array = [],
	nearby_pois: Array = [],
	active_events: Array = [],
	dials: Dictionary = {},
	inventory: Array = [],
	team_context: Dictionary = {}
) -> Dictionary:
	return {
		"agent_id": bot_id,
		"position": [pos.x, pos.y, pos.z],
		"position_v3": pos,
		"zone_id": zone,
		"health": health,
		"credits": credits,
		"nearby_entities": nearby_entities,
		"nearby_pois": nearby_pois,
		"active_events": active_events,
		"presence_dials": dials,
		"inventory": inventory,
		"team_context": team_context,
		"timestamp": Time.get_unix_time_from_system()
	}


## Factory pour construire une intention d'action standardisée
static func make_action(type: String, params: Dictionary = {}) -> Dictionary:
	var act := params.duplicate()
	act["type"] = type
	return act
