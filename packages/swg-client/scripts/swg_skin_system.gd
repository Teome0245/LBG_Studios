class_name SwgSkinSystem
extends RefCounted
## Système de Diversification des Skins & Teintures d'Avatars (SWG Pre-CU)
## Permet de personnaliser l'apparence des PNJ selon leur rôle galactique
## et offre au joueur un sélecteur de skins en temps réel.

# Profils de skins pré-définis pour les rôles PNJ
const NPC_SKIN_PALETTES := {
	"npc_mayor": {
		"name": "Toque & Manteau Municipal",
		"primary": Color(0.48, 0.12, 0.20),   # Pourpre royal
		"secondary": Color(0.92, 0.78, 0.25), # Ornementation dorée
		"hair": Color(0.85, 0.85, 0.90),      # Cheveux argentés de sage
		"metallic": 0.5,
		"roughness": 0.4
	},
	"npc_doctor": {
		"name": "Tunique Chirurgicale Stérile",
		"primary": Color(0.92, 0.95, 0.98),   # Blanc stérile
		"secondary": Color(0.10, 0.75, 0.85), # Cyan médical caducée
		"hair": Color(0.25, 0.20, 0.18),      # Brun classique
		"metallic": 0.2,
		"roughness": 0.5
	},
	"npc_guard": {
		"name": "Armure Lourde de la Milice Urbaine",
		"primary": Color(0.55, 0.15, 0.15),   # Rouge carmin militaire
		"secondary": Color(0.20, 0.20, 0.22), # Acier composite sombre
		"hair": Color(0.15, 0.15, 0.15),
		"metallic": 0.85,
		"roughness": 0.25
	},
	"npc_entertainer": {
		"name": "Parure de Scène Cantina",
		"primary": Color(0.88, 0.22, 0.60),   # Magenta soyeux scintillant
		"secondary": Color(0.98, 0.85, 0.35), # Paillettes d'or
		"hair": Color(0.15, 0.80, 0.95),      # Cheveux turquoise cyber
		"metallic": 0.4,
		"roughness": 0.3
	},
	"npc_scout": {
		"name": "Treillis Camouflage Terres Sauvages",
		"primary": Color(0.32, 0.42, 0.25),   # Vert mousse
		"secondary": Color(0.55, 0.38, 0.22), # Cuir tanné
		"hair": Color(0.40, 0.30, 0.20),
		"metallic": 0.1,
		"roughness": 0.9
	},
	"npc_miner": {
		"name": "Combinaison Industrielle d'Extraction",
		"primary": Color(0.88, 0.62, 0.12),   # Jaune sécurité minier
		"secondary": Color(0.22, 0.22, 0.25), # Carbone poussiéreux
		"hair": Color(0.30, 0.25, 0.20),
		"metallic": 0.3,
		"roughness": 0.8
	},
	"npc_bartender": {
		"name": "Tenue de Cantinier de Lost Heaven",
		"primary": Color(0.45, 0.32, 0.22),   # Tablier de cuir brun
		"secondary": Color(0.85, 0.80, 0.70), # Chemise de lin
		"hair": Color(0.70, 0.65, 0.60),
		"metallic": 0.15,
		"roughness": 0.75
	},
	"npc_pilot": {
		"name": "Combinaison Pressurisée de Vol",
		"primary": Color(0.92, 0.38, 0.05),   # Orange éclatant pilote
		"secondary": Color(0.90, 0.90, 0.92), # Harnais blanc
		"hair": Color(0.18, 0.18, 0.20),
		"metallic": 0.2,
		"roughness": 0.6
	},
	"npc_armorer": {
		"name": "Plastron de Forge & Cuir Réfractaire",
		"primary": Color(0.28, 0.28, 0.32),   # Acier bleuté forgé
		"secondary": Color(0.65, 0.35, 0.15), # Lanières de cuir
		"hair": Color(0.20, 0.20, 0.20),
		"metallic": 0.9,
		"roughness": 0.2
	}
}

# 5 Skins de joueur interchangeables en jeu
const PLAYER_SKIN_PRESETS := [
	{
		"id": "pioneer",
		"name": "1. Pionnier des Sables (Standard)",
		"primary": Color(0.15, 0.55, 0.75),
		"secondary": Color(0.90, 0.92, 0.95),
		"hair": Color(0.10, 0.65, 0.90),
		"metallic": 0.4,
		"roughness": 0.35
	},
	{
		"id": "mandalorian",
		"name": "2. Chasseur de Primes (Acier Beskar)",
		"primary": Color(0.35, 0.38, 0.42),
		"secondary": Color(0.68, 0.12, 0.15),
		"hair": Color(0.12, 0.12, 0.12),
		"metallic": 0.95,
		"roughness": 0.15
	},
	{
		"id": "rebel_pilot",
		"name": "3. Pilote Spécialisé (Orange d'Assaut)",
		"primary": Color(0.95, 0.38, 0.05),
		"secondary": Color(0.92, 0.92, 0.92),
		"hair": Color(0.45, 0.25, 0.15),
		"metallic": 0.25,
		"roughness": 0.55
	},
	{
		"id": "nomad_scout",
		"name": "4. Éclaireur Nomade (Camouflage Dunes)",
		"primary": Color(0.62, 0.52, 0.38),
		"secondary": Color(0.28, 0.38, 0.22),
		"hair": Color(0.75, 0.60, 0.40),
		"metallic": 0.15,
		"roughness": 0.85
	},
	{
		"id": "cyber_infiltrator",
		"name": "5. Infiltrateur Furtif (Noir & Néon)",
		"primary": Color(0.08, 0.08, 0.10),
		"secondary": Color(0.98, 0.15, 0.25),
		"hair": Color(0.95, 0.15, 0.35),
		"metallic": 0.7,
		"roughness": 0.2
	}
]


## Applique une palette personnalisée à un modèle 3D d'avatar
static func apply_skin(model_root: Node3D, palette: Dictionary) -> void:
	if model_root == null or palette.is_empty():
		return

	var prim_col: Color = palette.get("primary", Color.WHITE)
	var sec_col: Color = palette.get("secondary", Color.GRAY)
	var hair_col: Color = palette.get("hair", Color(0.2, 0.2, 0.2))
	var metallic: float = float(palette.get("metallic", 0.4))
	var roughness: float = float(palette.get("roughness", 0.5))

	var meshes: Array[MeshInstance3D] = _collect_all_meshes(model_root)
	for m: MeshInstance3D in meshes:
		var m_name: String = m.name.to_lower()
		var parent_name: String = m.get_parent().name.to_lower() if m.get_parent() != null else ""

		# 1. Cheveux (Hair)
		if "hair" in m_name or "hair" in parent_name:
			var mat_h := StandardMaterial3D.new()
			mat_h.albedo_color = hair_col
			mat_h.roughness = 0.65
			m.material_override = mat_h
			continue

		# 2. Corps / Vêtements / Armure (Body)
		if "body" in m_name or "avatar" in m_name or "capsule" in m_name or "mesh" in m_name:
			var mat_b := StandardMaterial3D.new()
			mat_b.albedo_color = prim_col
			mat_b.metallic = metallic
			mat_b.roughness = roughness
			m.material_override = mat_b
			continue

		# 3. Épaulières / Visière / Accessoires
		if "visor" in m_name or "eye" in m_name:
			var mat_v := StandardMaterial3D.new()
			mat_v.albedo_color = sec_col
			mat_v.emission_enabled = true
			mat_v.emission = sec_col
			mat_v.emission_energy_multiplier = 2.0
			m.material_override = mat_v


## Applique automatiquement le skin associé au rôle du PNJ
static func apply_npc_role_skin(model_root: Node3D, role_id: String) -> void:
	if NPC_SKIN_PALETTES.has(role_id):
		apply_skin(model_root, NPC_SKIN_PALETTES[role_id])


static func _collect_all_meshes(n: Node) -> Array[MeshInstance3D]:
	var result: Array[MeshInstance3D] = []
	var stack: Array[Node] = [n]
	while not stack.is_empty():
		var curr: Node = stack.pop_back()
		if curr is MeshInstance3D:
			result.append(curr as MeshInstance3D)
		for child in curr.get_children():
			stack.append(child)
	return result
