extends RefCounted
class_name HubGenerativeMemory
## Architecture Cognitive Stanford Generative Agents (Smallville) pour les PNJ de Lost Heaven.
## Gère le Memory Stream, le score de Retrieval pondéré (Récence + Importance + Pertinence)
## et le cycle de Réflexion périodique (pensées d'ordre supérieur).

const _HubPaths = preload("res://scripts/hub_paths.gd")
const HubDbScript = preload("res://scripts/hub_db.gd")

const DEFAULT_CONFIG_PATH := "life/generative_cohorts.json"

static var _instance = null

var config: Dictionary = {}
var active_npcs: Dictionary = {} # npc_id -> true
var all_enabled: bool = false
var recency_half_life_seconds: float = 7200.0
var weight_recency: float = 1.0
var weight_importance: float = 1.5
var weight_relevance: float = 2.0
var max_retrieved_memories: int = 4
var reflection_threshold: int = 35


static func get_shared():
	if _instance == null:
		_instance = load("res://scripts/hub_generative_memory.gd").new()
		_instance.setup()
	return _instance


func setup(custom_config_path: String = "") -> bool:
	var path := custom_config_path if not custom_config_path.is_empty() else _HubPaths.data_file(DEFAULT_CONFIG_PATH)
	var loaded: Variant = _HubPaths.read_json(path)
	if typeof(loaded) == TYPE_DICTIONARY:
		config = loaded
	else:
		config = _get_default_config()

	_apply_config()
	return true


func _get_default_config() -> Dictionary:
	return {
		"active_phase": 1,
		"phases": {
			"1": {
				"name": "Phase 1 : Pilote 10 PNJ Emblématiques",
				"duration_weeks": 2,
				"enabled": true,
				"npcs": [
					"npc:core3_barman_jax",
					"npc:core3_daan_oth",
					"npc:core3_artisan_trainer_c",
					"npc:core3_brawler_trainer_c",
					"npc:core3_medic_trainer_c",
					"npc:core3_scout_trainer_c",
					"npc:capitaine_vael",
					"npc:mecanicien_soren",
					"npc:ancien_nadir",
					"npc:rumeuriste"
				]
			}
		},
		"settings": {
			"recency_half_life_seconds": 7200,
			"weights": {"recency": 1.0, "importance": 1.5, "relevance": 2.0},
			"max_retrieved_memories": 4,
			"reflection_importance_threshold": 35
		}
	}


func _apply_config() -> void:
	active_npcs.clear()
	all_enabled = false
	var phases: Dictionary = config.get("phases", {})
	var current_phase_key := str(config.get("active_phase", 1))

	# Activer toutes les phases actives jusqu'à la phase actuelle
	for phase_num in range(1, int(current_phase_key) + 1):
		var p_data: Dictionary = phases.get(str(phase_num), {})
		if p_data.get("enabled", false) or str(phase_num) == current_phase_key:
			var npcs: Array = p_data.get("npcs", [])
			for npc in npcs:
				var nid := str(npc).strip_edges()
				if nid == "*":
					all_enabled = true
				else:
					active_npcs[nid] = true

	var settings: Dictionary = config.get("settings", {})
	recency_half_life_seconds = float(settings.get("recency_half_life_seconds", 7200.0))
	var w: Dictionary = settings.get("weights", {})
	weight_recency = float(w.get("recency", 1.0))
	weight_importance = float(w.get("importance", 1.5))
	weight_relevance = float(w.get("relevance", 2.0))
	max_retrieved_memories = int(settings.get("max_retrieved_memories", 4))
	reflection_threshold = int(settings.get("reflection_importance_threshold", 35))


func is_npc_eligible(npc_id: String) -> bool:
	if all_enabled:
		return true
	return active_npcs.has(npc_id.strip_edges())


func record_event(npc_id: String, content: String, importance: int = 5, event_type: String = "observation", tags: String = "") -> bool:
	## Enregistre une observation ou interaction dans le Memory Stream SQLite.
	if not is_npc_eligible(npc_id):
		return false
	var clean_content := content.strip_edges()
	if clean_content.is_empty():
		return false

	var db = HubDbScript.get_shared()
	if db == null or not db.available:
		return false

	var now := int(Time.get_unix_time_from_system())
	var safe_nid := HubDbScript.escape_sql(npc_id)
	var safe_content := HubDbScript.escape_sql(clean_content)
	var safe_type := HubDbScript.escape_sql(event_type)
	var safe_tags := HubDbScript.escape_sql(tags)
	var clamped_importance := clampi(importance, 1, 10)

	var sql := "INSERT INTO npc_memories(npc_id, timestamp, event_type, content, importance, reflected, tags) VALUES ('%s', %d, '%s', '%s', %d, 0, '%s');" % [
		safe_nid, now, safe_type, safe_content, clamped_importance, safe_tags
	]
	db.enqueue([sql])
	return true


func retrieve_memories(npc_id: String, query_text: String = "", limit: int = -1) -> Array:
	## Récupère les mémoires les plus pertinentes selon l'algorithme de Stanford.
	if not is_npc_eligible(npc_id):
		return []

	var db = HubDbScript.get_shared()
	if db == null or not db.available:
		return []

	var target_limit := limit if limit > 0 else max_retrieved_memories
	var safe_nid := HubDbScript.escape_sql(npc_id)
	# Extraire les 30 derniers souvenirs pour calculer le score
	var query_sql := "SELECT id, timestamp, event_type, content, importance, tags FROM npc_memories WHERE npc_id = '%s' ORDER BY timestamp DESC LIMIT 30;" % safe_nid
	var rows: Array = db.query_rows(query_sql)
	if rows.is_empty():
		return []

	var now := float(Time.get_unix_time_from_system())
	var query_tokens := _tokenize(query_text)
	var scored_memories: Array = []

	for row in rows:
		if typeof(row) != TYPE_DICTIONARY:
			continue
		var ts := float(row.get("timestamp", now))
		var delta_t := maxf(0.0, now - ts)
		# Récence : fonction exponentielle basée sur la demi-vie configurée
		var recency := pow(0.5, delta_t / maxf(1.0, recency_half_life_seconds))

		# Importance : normalisée 1-10 -> 0.1-1.0
		var imp := float(row.get("importance", 5)) / 10.0

		# Pertinence sémantique lexicale (overlap de tokens normalisés)
		var relevance := 0.0
		if not query_tokens.is_empty():
			var content_tokens := _tokenize(str(row.get("content", "")) + " " + str(row.get("tags", "")))
			relevance = _compute_overlap_score(query_tokens, content_tokens)

		var total_score := (weight_recency * recency) + (weight_importance * imp) + (weight_relevance * relevance)
		
		var mem_copy: Dictionary = row.duplicate()
		mem_copy["score"] = total_score
		mem_copy["recency"] = recency
		mem_copy["relevance"] = relevance
		scored_memories.append(mem_copy)

	# Trier par score décroissant
	scored_memories.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a.get("score", 0.0)) > float(b.get("score", 0.0))
	)

	if scored_memories.size() > target_limit:
		return scored_memories.slice(0, target_limit)
	return scored_memories


func check_and_trigger_reflection(npc_id: String) -> Dictionary:
	## Vérifie si le seuil d'importance des mémoires non réfléchies est dépassé.
	## Si oui, agrège les mémoires et produit une réflexion d'ordre supérieur.
	if not is_npc_eligible(npc_id):
		return {"reflected": false, "reason": "not_eligible"}

	var db = HubDbScript.get_shared()
	if db == null or not db.available:
		return {"reflected": false, "reason": "no_db"}

	var safe_nid := HubDbScript.escape_sql(npc_id)
	var sql_unreflected := "SELECT id, content, importance, event_type FROM npc_memories WHERE npc_id = '%s' AND reflected = 0 ORDER BY timestamp ASC;" % safe_nid
	var unreflected_rows: Array = db.query_rows(sql_unreflected)
	if unreflected_rows.is_empty():
		return {"reflected": false, "reason": "empty"}

	var total_imp := 0
	var memory_ids: Array = []
	var descriptions: Array = []

	for row in unreflected_rows:
		if typeof(row) != TYPE_DICTIONARY:
			continue
		total_imp += int(row.get("importance", 5))
		memory_ids.append(int(row.get("id", 0)))
		descriptions.append(str(row.get("content", "")))

	if total_imp < reflection_threshold:
		return {"reflected": false, "reason": "threshold_not_met", "current_sum": total_imp, "threshold": reflection_threshold}

	# Synthèse de réflexion
	var reflection_text := _synthesize_reflection(descriptions)
	
	# Marquer comme réfléchi
	var id_list_str := ""
	for i in range(memory_ids.size()):
		id_list_str += str(memory_ids[i])
		if i < memory_ids.size() - 1:
			id_list_str += ", "

	var update_sql := "UPDATE npc_memories SET reflected = 1 WHERE id IN (%s);" % id_list_str
	var now := int(Time.get_unix_time_from_system())
	var insert_reflection_sql := "INSERT INTO npc_memories(npc_id, timestamp, event_type, content, importance, reflected, tags) VALUES ('%s', %d, 'reflection', '%s', 9, 1, 'reflection,insight');" % [
		safe_nid, now, HubDbScript.escape_sql(reflection_text)
	]

	db.enqueue([update_sql, insert_reflection_sql])

	return {
		"reflected": true,
		"npc_id": npc_id,
		"reflection": reflection_text,
		"memories_count": memory_ids.size(),
		"importance_sum": total_imp
	}


func format_memories_for_prompt(memories: Array) -> String:
	## Formate une liste de mémoires pour l'injection dans le system prompt.
	if memories.is_empty():
		return ""
	var lines := ["\n[Souvenirs récents & réflexions pertinentes du PNJ] :"]
	for m in memories:
		if typeof(m) != TYPE_DICTIONARY:
			continue
		var prefix := "- "
		if str(m.get("event_type", "")) == "reflection":
			prefix = "- [Réflexion profonde] "
		lines.append(prefix + str(m.get("content", "")))
	return "\n".join(lines)


func _tokenize(text: String) -> Array:
	var clean := text.to_lower()
	var tokens: Array = []
	var words := clean.split(" ", false)
	for w in words:
		var clean_w := w.strip_edges().replace(",", "").replace(".", "").replace("!", "").replace("?", "").replace("'", "")
		if clean_w.length() >= 3:
			tokens.append(clean_w)
	return tokens


func _compute_overlap_score(query_tokens: Array, doc_tokens: Array) -> float:
	if query_tokens.is_empty() or doc_tokens.is_empty():
		return 0.0
	var doc_set: Dictionary = {}
	for dt in doc_tokens:
		doc_set[dt] = true

	var matches := 0
	for qt in query_tokens:
		if doc_set.has(qt):
			matches += 1

	return float(matches) / float(query_tokens.size())


func _synthesize_reflection(descriptions: Array) -> String:
	## Synthèse heuristique déterministe (fallback si LLM hors-ligne).
	if descriptions.size() == 1:
		return "Constat clé : " + descriptions[0]
	var summary_points: Array = []
	var sample_size := mini(3, descriptions.size())
	for i in range(sample_size):
		summary_points.append(descriptions[descriptions.size() - 1 - i])
	return "Synthèse des récents événements : " + " ; ".join(summary_points) + "."
