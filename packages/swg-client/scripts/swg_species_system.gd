class_name SwgSpeciesSystem
extends RefCounted
## Système des Espèces & Races SWG Pre-CU (Lost Heaven)
## Gère la morphologie, les bonus raciaux HAM et les modèles VRM/3D interchangeables.

const SPECIES_CATALOG := [
	{
		"id": "human",
		"name": "Humain (Corellien)",
		"title": "« Citoyen Polyvalent »",
		"vrm_model": "Anna.vrm",
		"scale_vec": Vector3(0.94, 0.94, 0.94),
		"skin_tint": Color(0.92, 0.85, 0.78),
		"ham_bonus": {"health": 100, "action": 100, "mind": 100},
		"description": "Équilibré dans toutes les jauges HAM. Polyvalence universelle."
	},
	{
		"id": "twilek",
		"name": "Twi'lek des Oasis",
		"title": "« Danseur aux Lekku »",
		"vrm_model": "LadyKoi.vrm",
		"scale_vec": Vector3(0.95, 0.95, 0.95),
		"skin_tint": Color(0.95, 0.55, 0.25), # Teinte orangée/rougeâtre avec lekku
		"ham_bonus": {"health": 50, "action": 150, "mind": 200},
		"description": "Lekku crâniens, grâce naturelle et résistance aux poisons. Bonus d'artiste."
	},
	{
		"id": "cyborg",
		"name": "Androïde / Cyborg Compagnon",
		"title": "« Compagnon de Bord »",
		"vrm_model": "Compagnon.vrm",
		"scale_vec": Vector3(0.95, 0.95, 0.95),
		"skin_tint": Color(0.95, 0.95, 0.98), # Coque blanche et néon cyan
		"ham_bonus": {"health": 200, "action": 100, "mind": 50},
		"description": "Châssis mécatronique renforcé, haute résistance physique et blindage."
	},
	{
		"id": "zabrak",
		"name": "Zabrak d'Iridonia",
		"title": "« Volonté d'Airain »",
		"vrm_model": "Aurora.vrm",
		"scale_vec": Vector3(0.96, 0.96, 0.96),
		"skin_tint": Color(0.85, 0.65, 0.45), # Carnation mate avec tatouages faciaux
		"ham_bonus": {"health": 150, "action": 150, "mind": 120},
		"description": "Résistance exceptionnelle aux étourdissements et régénération rapide."
	},
	{
		"id": "wookiee",
		"name": "Wookiee de Kashyyyk",
		"title": "« Colosse des Forêts »",
		"vrm_model": "Compagnon.vrm", # Re-stylisé en colosse géant
		"scale_vec": Vector3(1.18, 1.18, 1.18),
		"skin_tint": Color(0.42, 0.28, 0.18), # Pelage brun sombre
		"ham_bonus": {"health": 350, "action": 50, "mind": 50},
		"description": "Force herculéenne (+350 Santé). Taille imposante et robustesse légendaire."
	},
	{
		"id": "rodian",
		"name": "Rodien Chasseur",
		"title": "« Tireur d'Élite »",
		"vrm_model": "LadyKoi.vrm",
		"scale_vec": Vector3(0.92, 0.92, 0.92),
		"skin_tint": Color(0.35, 0.75, 0.45), # Peau verte reptilienne
		"ham_bonus": {"health": 80, "action": 200, "mind": 80},
		"description": "Vision nocturne et sens de la traque. Bonus de précision au blaster."
	}
]


static func get_species_count() -> int:
	return SPECIES_CATALOG.size()


static func get_species(idx: int) -> Dictionary:
	return SPECIES_CATALOG[idx % SPECIES_CATALOG.size()]


static func find_species_by_id(s_id: String) -> Dictionary:
	for sp in SPECIES_CATALOG:
		if sp["id"] == s_id:
			return sp
	return SPECIES_CATALOG[0]

