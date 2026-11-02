extends RefCounted
class_name HubSimDefs
## Constantes de topologie, POIs et catalogues de repli pour la sim hub — Ticket 2.2.

const HUMAN_OID := 100001
const ZONE := "scrapaltai"
const SPAWN_HUMAN := Vector3(4749.0, 0.15, -650.0)
const PLAZA := Vector3(4749.0, 0.15, -737.0)
const MARKET := Vector3(4749.0, 0.15, -980.0)
const STARPORT := Vector3(4260.0, 0.15, -737.0)
const CANTINA := Vector3(5080.0, 0.15, -737.0)
const MISSION := Vector3(5020.0, 0.15, -950.0)
const CLINIC := Vector3(4480.0, 0.15, -530.0)
const TRAINING := Vector3(5020.0, 0.15, -530.0)
const INN := Vector3(4749.0, 0.15, -520.0)
const TOWN_HALL := Vector3(4480.0, 0.15, -950.0)
const ARTISAN := Vector3(5320.0, 0.15, -737.0)
const LODGE_W := Vector3(4060.0, 0.15, -737.0)
const LODGE_N := Vector3(4749.0, 0.15, -370.0)
const LODGE_E := Vector3(5460.0, 0.15, -540.0)
const LODGE_S := Vector3(4749.0, 0.15, -1160.0)
const OUTPOST_ZALEM := Vector3(-1200.0, 0.15, -550.0)
const KSAR_NOMADE := Vector3(4950.0, 0.15, -3800.0)
const BOT_SPEED := 12.0

const POIS: Dictionary = {
	"plaza": PLAZA,
	"market": MARKET,
	"apron": STARPORT,
	"board": MISSION,
	"cantina": CANTINA,
	"inn": INN,
	"clinic": CLINIC,
	"train": TRAINING,
	"hall": TOWN_HALL,
	"craft": ARTISAN,
	"lodge_w": LODGE_W,
	"lodge_n": LODGE_N,
	"lodge_e": LODGE_E,
	"lodge_s": LODGE_S,
	"zalem_outpost": OUTPOST_ZALEM,
	"ksar_nomade": KSAR_NOMADE,
}

const BOT_DEFS_FALLBACK: Array = [
	{
		"eid": "player:Nix", "oid": 900002, "name": "Nix",
		"spawn": Vector3(4757.0, 0.15, -720.0), "speed": 12.0,
		"prefer": ["plaza", "market", "apron", "board"],
		"greet": "Salut {who} — bienvenue au hub Lost Heaven.",
		"ambient": "{who}, je tourne sur le hub — board, marché, plaza.",
	},
	{
		"eid": "player:Lia", "oid": 900003, "name": "Lia",
		"spawn": Vector3(4780.0, 0.15, -690.0), "speed": 11.5,
		"prefer": ["inn", "cantina", "plaza", "craft"],
		"greet": "Hey {who}. Lia — auberge, cantina, atelier.",
		"ambient": "{who}, besoin d'un coup de main au hub ?",
	},
	{
		"eid": "player:Mira", "oid": 900004, "name": "Mira",
		"spawn": Vector3(4700.0, 0.15, -900.0), "speed": 11.0,
		"prefer": ["board", "market", "hall", "plaza"],
		"greet": "{who} — Mira. Board et marché, je joue les contrats.",
		"ambient": "Des contrats au board, {who}. Daan Oth t'attend.",
	},
	{
		"eid": "player:Kael", "oid": 900005, "name": "Kael",
		"spawn": Vector3(4809.0, 0.15, -700.0), "speed": 11.0,
		"prefer": ["train", "inn", "plaza", "clinic"],
		"greet": "{who}. Kael — trainers et auberge, côté nord.",
		"ambient": "Hall d'entraînement si tu veux te mesurer, {who}.",
	},
]

const HUB_NPCS: Array = [
	{"eid": "npc:core3_daan_oth", "oid": 910001, "name": "Daan Oth", "pos": MISSION, "wander_r": 10.0,
		"ambient": "Des offres au board — pas de touristes, des contrats."},
	{"eid": "npc:core3_barman_jax", "oid": 910002, "name": "Jax Moro", "pos": CANTINA, "wander_r": 6.0,
		"ambient": "La Perle reste ouverte. Un verre, ou juste l'ombre."},
	{"eid": "npc:guide_quartier", "oid": 910003, "name": "Guide de quartier", "pos": STARPORT, "wander_r": 14.0,
		"ambient": "Starport, marché, porte est — tu te perds, tu cries."},
	{"eid": "npc:core3_medic_trainer_c", "oid": 910004, "name": "Odo Merr", "pos": CLINIC, "wander_r": 8.0,
		"ambient": "Clinique. Kits d'abord, discours après."},
	{"eid": "npc:core3_scout_trainer_c", "oid": 910005, "name": "Yara Nis", "pos": TRAINING, "wander_r": 12.0,
		"ambient": "Pistes hors remparts — le désert ne pardonne pas."},
	{"eid": "npc:core3_artisan_trainer_c", "oid": 910006, "name": "Kell Asa", "pos": ARTISAN, "wander_r": 10.0,
		"ambient": "Atelier ouvert. On assemble ce qu'on ramasse."},
	{"eid": "npc:core3_talen_ress", "oid": 910007, "name": "Talen Ress", "pos": INN, "wander_r": 8.0,
		"ambient": "Formation scène à l'auberge — danse, musique, moral."},
	{"eid": "npc:scribe", "oid": 910008, "name": "Scribe", "pos": TOWN_HALL, "wander_r": 6.0,
		"ambient": "Chroniques de session. Pas de légendes inventées."},
	{"eid": "npc:habitue_cantina", "oid": 910009, "name": "Habitué", "pos": CANTINA, "wander_r": 9.0,
		"ambient": "Toujours la même table à La Perle…"},
	{"eid": "npc:videur", "oid": 910010, "name": "Videur", "pos": Vector3(4995.0, 0.15, -737.0), "wander_r": 6.0,
		"ambient": "Pas de bagarre devant La Perle."},
	{"eid": "npc:sergent_rue", "oid": 910011, "name": "Sergent de rue", "pos": Vector3(5180.0, 0.15, -737.0), "wander_r": 14.0,
		"ambient": "Porte est surveillée. Meute ou pas — on tient."},
	{"eid": "npc:rumeuriste", "oid": 910012, "name": "Rumeuriste", "pos": MARKET, "wander_r": 14.0,
		"ambient": "Au marché on entend tout — et on répète la moitié."},
	{"eid": "npc:core3_brawler_trainer_c", "oid": 910013, "name": "Tobin Ress", "pos": TRAINING, "wander_r": 11.0,
		"ambient": "Poing avant paroles. Hall d'entraînement."},
	{"eid": "npc:core3_marksman_trainer_c", "oid": 910014, "name": "Unar Tek", "pos": TRAINING, "wander_r": 11.0,
		"ambient": "Visée. Respire, tire, ne rate pas le désert."},
	{"eid": "npc:core3_pilot_imperial_a", "oid": 910015, "name": "Garr Vek", "pos": STARPORT, "wander_r": 12.0,
		"ambient": "Pilotage shuttle — apron propre, décollages courts."},
	{"eid": "npc:capitaine_vael", "oid": 910016, "name": "Capitaine Vael", "pos": OUTPOST_ZALEM, "wander_r": 12.0,
		"ambient": "Avant-poste Zalem. Route ouest sécurisée — convois en règle."},
	{"eid": "npc:mecanicien_soren", "oid": 910017, "name": "Soren Kray", "pos": Vector3(-1060.0, 0.15, -470.0), "wander_r": 10.0,
		"ambient": "Atelier relais. Si votre landspeeder fume avant la capitale, c'est ici."},
	{"eid": "npc:ancien_nadir", "oid": 910018, "name": "Ancien Nadir", "pos": KSAR_NOMADE, "wander_r": 14.0,
		"ambient": "Bienvenue au Ksar de l'Oasis, voyageur. L'eau fraîche et l'ombre de nos murs de pierre se partagent avec respect."},
	{"eid": "npc:guerisseur_miran", "oid": 910019, "name": "Miran Sael", "pos": Vector3(4800.0, 0.15, -3730.0), "wander_r": 10.0,
		"ambient": "Dispensaire de l'Oasis. Nos baumes et infusions de racines soignent les brûlures du désert."},
	{"eid": "npc:guetteur_dunes", "oid": 910020, "name": "Vigie des Dunes", "pos": Vector3(6650.0, 0.15, -1380.0), "wander_r": 8.0,
		"ambient": "Horizon dégagé. Les convois de ferraille passent sans encombre le long des crêtes."},
	{"eid": "npc:gardien_source", "oid": 910021, "name": "Gardien de la Source", "pos": Vector3(6550.0, 0.15, -2480.0), "wander_r": 10.0,
		"ambient": "Prenez de l'eau fraîche pour vos bêtes à l'Oasis d'Al-Khali avant la traversée vers le Ksar."},
	{"eid": "npc:ferrailleur_canyon", "oid": 910022, "name": "Ferrailleur du Canyon", "pos": Vector3(5650.0, 0.15, -3250.0), "wander_r": 8.0,
		"ambient": "Une carcasse de cargo impérial gît dans la faille — encore des pièces à dessouder."},
]
