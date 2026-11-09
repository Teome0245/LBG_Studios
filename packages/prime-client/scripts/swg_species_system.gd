class_name SwgSpeciesSystem
extends RefCounted
## Système des Espèces & Races SWG Pre-CU / Prime (Lost Heaven)
## Gère la morphologie, les bonus raciaux HAM et les modèles VRM/3D interchangeables.

const SPECIES_CATALOG := [
	{
		"id": "human",
		"prime_id": "race:human",
		"aliases": ["human", "humain"],
		"name": "Humain (Corellien)",
		"prime_name": "Humain de Terre1",
		"title": "« Citoyen Polyvalent »",
		"vrm_model": "Anna.vrm",
		"scale_vec": Vector3(0.95, 0.95, 0.95),
		"skin_tint": Color(0.92, 0.85, 0.78),
		"ham_bonus": {"health": 100, "action": 100, "mind": 100},
		"description": "Équilibré dans toutes les jauges HAM. Polyvalence universelle originaire de Terre1."
	},
	{
		"id": "twilek",
		"prime_id": "race:fel_rani",
		"aliases": ["twilek", "fel_rani", "fae_lume"],
		"name": "Twi'lek des Oasis",
		"prime_name": "Fel'Rani d'Arvandor",
		"title": "« Grâce Féline & Lekku »",
		"vrm_model": "LadyKoi.vrm",
		"scale_vec": Vector3(0.92, 1.0, 0.92),
		"skin_tint": Color(0.95, 0.65, 0.35),
		"ham_bonus": {"health": 50, "action": 150, "mind": 200},
		"description": "Grâce féline d'Arvandor, oreilles pointues, lekku crâniens et agilité d'artiste."
	},
	{
		"id": "cyborg",
		"prime_id": "race:mechari",
		"aliases": ["cyborg", "mechari"],
		"name": "Androïde / Cyborg Compagnon",
		"prime_name": "Mechari de Mecha-Prime",
		"title": "« Châssis Mécatronique »",
		"vrm_model": "Compagnon.vrm",
		"scale_vec": Vector3(1.0, 1.0, 1.0),
		"skin_tint": Color(0.92, 0.94, 0.98),
		"ham_bonus": {"health": 200, "action": 100, "mind": 50},
		"description": "Châssis mécatronique renforcé de Mecha-Prime, capteur optique et réacteur dorsal."
	},
	{
		"id": "zabrak",
		"prime_id": "race:kmiri",
		"aliases": ["zabrak", "kmiri"],
		"name": "Zabrak d'Iridonia",
		"prime_name": "K'Miri de Khar'Zuun",
		"title": "« Volonté d'Airain »",
		"vrm_model": "Aurora.vrm",
		"scale_vec": Vector3(0.96, 0.96, 0.96),
		"skin_tint": Color(0.85, 0.55, 0.40),
		"ham_bonus": {"health": 150, "action": 150, "mind": 120},
		"description": "Couronne de 6 cornes crâniennes pointues, volonté d'airain et résistance physique."
	},
	{
		"id": "wookiee",
		"prime_id": "race:varkoon",
		"aliases": ["wookiee", "varkoon"],
		"name": "Wookiee de Kashyyyk",
		"prime_name": "Varkoon d'Arvandor",
		"title": "« Colosse des Forêts & Poing »",
		"vrm_model": "Compagnon.vrm",
		"scale_vec": Vector3(1.25, 1.15, 1.25),
		"skin_tint": Color(0.42, 0.28, 0.18),
		"ham_bonus": {"health": 350, "action": 50, "mind": 50},
		"description": "Force herculéenne (+350 Santé). Buste massif, cartouchière de guerre et grande robustesse."
	},
	{
		"id": "rodian",
		"prime_id": "race:pykrel",
		"aliases": ["rodian", "pykrel"],
		"name": "Rodien Chasseur",
		"prime_name": "Pykrel d'Arvandor",
		"title": "« Tireur d'Élite & Traqueur »",
		"vrm_model": "LadyKoi.vrm",
		"scale_vec": Vector3(0.90, 0.90, 0.90),
		"skin_tint": Color(0.35, 0.72, 0.42),
		"ham_bonus": {"health": 80, "action": 200, "mind": 80},
		"description": "Museau tubulaire, yeux composés facettés. Vision nocturne et sens de la traque au blaster."
	},
	{
		"id": "tinkling",
		"prime_id": "race:tinkling",
		"aliases": ["tinkling", "sullustan"],
		"name": "Tinkling (Artisan de Mecha-Prime)",
		"prime_name": "Tinkling de Mecha-Prime",
		"title": "« Le Petit Forgeur »",
		"vrm_model": "Aurora.vrm",
		"scale_vec": Vector3(0.48, 0.48, 0.48),
		"skin_tint": Color(0.88, 0.75, 0.58),
		"ham_bonus": {"health": 60, "action": 180, "mind": 160},
		"description": "Petite stature (~45 cm), grandes lunettes steampunk luminescentes et sacoche d'outils."
	},
	{
		"id": "mogrul",
		"prime_id": "race:mogrul",
		"aliases": ["mogrul", "ithorian"],
		"name": "Mogrul (Soigneur d'Aetherion)",
		"prime_name": "Mogrul d'Aetherion",
		"title": "« Apothicaire & Soigneur »",
		"vrm_model": "Aurora.vrm",
		"scale_vec": Vector3(0.85, 0.72, 0.90),
		"skin_tint": Color(0.60, 0.52, 0.42),
		"ham_bonus": {"health": 180, "action": 60, "mind": 220},
		"description": "Morphologie trapue, masque respirateur à double cartouche et grande maîtrise spirituelle."
	}
]


static func get_species_count() -> int:
	return SPECIES_CATALOG.size()


static func get_species(idx: int) -> Dictionary:
	return SPECIES_CATALOG[idx % SPECIES_CATALOG.size()]


static func find_species_by_id(s_id: String) -> Dictionary:
	var query := s_id.to_lower().strip_edges()
	for sp in SPECIES_CATALOG:
		if str(sp.get("id", "")).to_lower() == query:
			return sp
		if str(sp.get("prime_id", "")).to_lower() == query:
			return sp
		for alias in sp.get("aliases", []):
			if str(alias).to_lower() == query:
				return sp
	return SPECIES_CATALOG[0]
