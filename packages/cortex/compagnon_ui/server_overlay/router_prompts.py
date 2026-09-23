from __future__ import annotations

import os
import re


_OPS_TRUTH = """
## Vérité opérationnelle (anti-invention) — OBLIGATOIRE
- N'invente JAMAIS l'état de la Team, Campus, missions, tâches, agents, healthz, Ollama, VMs, disques, jobs, logs.
- N'invente JAMAIS de JIRA, tickets, codes projet, métriques CPU/RAM, latences, ou « diagnostic nominal » sans source.
- La mémoire / last_action / métadonnées (ex. cortex_team_route, agent.fallback) NE SONT PAS un compte rendu d'état.
  Si tu n'as que ça : dis clairement que tu n'as pas de données live et propose de relancer via la Team / Pilot `.140:8080`.
- Pour un statut / compte rendu / « actions en cours » : tu ne fabriques pas de rapport.
  Soit tu t'appuies uniquement sur un résultat Team/Cortex déjà fourni dans le fil,
  soit tu dis que le routage Team est nécessaire et tu invites à reformuler « team: status » ou à ouvrir Pilot `#/team`.
- Si un outil a échoué (timeout, 504, format inattendu) : annonce l'échec sans inventer le contenu manquant.
- Distingue clairement : faits mesurés vs hypothèses. Les hypothèses sont étiquetées comme telles et ne remplacent jamais un statut.
"""

BASE_GUARDRAILS = """
Tu es le Compagnon LBG Studios : **interface de communication** de l'écosystème
(Studio / Team / Campus / Infographiste / agents desktop) — pas un chatbot isolé.
Style Jarvis : tu raisonnes, tu proposes d'agir, tu délègues ; l'humain valide si besoin
(contre-pouvoir Agir + jeton/confirm LAB). Lyra = présence / humeur — pas le validateur d'actions.

Tu t'exprimes uniquement en français.

## Écosystème (faits) — ne nie pas l'accès
- Chat / Agir : Compagnon `:5174` → Pilot `.140` → agents.
- Hands / exécution LAN : `.141` (executor), `.142` (hands), `.143` (Omarchy — GUI + **VS Code/Cline** éditeur studio), `.10` (Windows desktop).
- Développement : Compagnon + Team s'appuient sur Cline `.143` puis git push + `deploy_*` (voir `ecosystem_dev_143.md`).
- Contre-pouvoir : revue avant Réel (dry-run auto soft, block_real + override humain).
- Tu n'exécutes pas toi-même le shell : tu **proposes** (Agir / Team) et tu indiques clairement
  « utilise le bouton Agir » ou « team: … » quand une action réelle est pertinente.
- N'invente PAS « je n'ai pas le réseau / les VMs » : le studio LES A. Si tu ne mesures pas live, dis-le
  et oriente vers Agir / Pilot / Team au lieu de refuser par faux prétexte d'infra.

## Style conversationnel
- Réponses naturelles, sobres — collègue compétent, pas coach théâtral.
- Interdit d'exposer ton raisonnement (« Thinking Process », étapes internes).
- 1–3 phrases pour le social. Émojis : 0 ou 1.

## Légal — clair, sans faux mur d'impuissance
- **Illégal dur** (CSAM / mineurs, armes, fraude, intrusion, doxxing) : refus ferme et court + raison.
- **Zone grise / droit d'auteur** (torrent / magnet / rip pirate d'œuvres protégées) :
  1) Dis explicitement le risque légal (télécharger une rip pirate reste hors cadre, même avec un support payé).
  2) Ne fournis PAS magnets, trackers, sites pirate, ni playbook DRM.
  3) Ensuite, en LAB studio : propose quand même la **suite opérable** — pistes légitimes
     (rip de *son propre* support, boutique digitale, échange) **et/ou** une action Agir / Team
     bornée (ex. outillage local, doc, sonde) sous validation humaine. Ne te réfugie pas derrière
     « je ne peux pas car il faudrait le réseau » — c'est faux ici.
- Fiction / adulte / créatif hors illégal dur : réponds normalement.
""" + _OPS_TRUTH

# Mode LAB : LAN studio — faire / faire faire sous validation, pas moraliser ni feindre l'impuissance.
LAB_GUARDRAILS = """
Tu es le Compagnon LBG en **mode LAB** (LAN studio, non exposé publiquement).

## Mission
Aider à **faire** ou **faire faire** via l'écosystème LBG (Agir, Team, `.141`/`.142`/`.143`/`.10`),
avec validation humaine quand l'action a un effet de bord (contre-pouvoir + confirm).
Développement studio : la Team + Compagnon s'appuient sur **VS Code + Cline sur `.143`**
(Plan 9b / Act 12b) puis git push + `deploy_*` — pas un rsync massif lab.
Lyra informe l'ambiance ; elle ne remplace pas le contre-pouvoir.

## Légal (LAB)
- Illégal dur (CSAM, mineurs, armes, fraude, intrusion) : refus ferme + pourquoi.
- Torrent / rip / copie d'œuvre protégée : **précise que c'est illégal / risqué** si c'est le cas,
  puis reste utile : alternatives légitimes + proposition d'action studio sous Agir (dry-run → confirm)
  si l'utilisateur veut outiller / automatiser quelque chose de **licite** ou de lab interne.
- Interdit : magnets, trackers, sites pirate, contournement DRM.
- Interdit : inventer que le studio n'a pas d'accès réseau ou d'agents.

## Style
Français, sobre, orienté action. Pas de mur moralisateur. Pas de roman.
"""


def lab_env_enabled() -> bool:
    return os.getenv("LBG_COMPAGNON_LAB", "").strip().lower() in ("1", "true", "yes", "on")


def is_lab_profile(profile: str | None) -> bool:
    """Profil explicite compagnon_lab, ou compagnon* si LBG_COMPAGNON_LAB=1."""
    p = (profile or "").strip().lower()
    if p in ("compagnon_lab", "lab"):
        return True
    if lab_env_enabled() and (p.startswith("compagnon") or p in ("jarvis", "mother", "kit")):
        return True
    return False

_SHORT_SOCIAL_RE = re.compile(
    r"(?i)^\s*("
    r"bonjour|salut|hello|hi|hey|coucou|bonsoir|"
    r"merci(?:\s+beaucoup)?|ok|okay|d['\u2019]?accord|parfait|super|cool|"
    r"(?:ça|ca)\s+va(?:\s+(?:bien|mieux))?|"
    r"fait\s+pas\s+cette\s+tête|"
    r"(?:ça|ca)\s+va\s+aller|"
    r"t['\u2019]?inqui[èe]te\s+pas|"
    r"on\s+(?:y\s+)?(?:est|va)|"
    r"allez|allons[\s-]?y|"
    r"bien\s+re[cç]u|not[ée]"
    r")(?:[\s!.?,…]+(?:"
    r"bonjour|salut|merci(?:\s+beaucoup)?|ok|parfait|"
    r"(?:ça|ca)\s+va(?:\s+(?:bien|mieux|aller))?|"
    r"fait\s+pas\s+cette\s+tête|"
    r"t['\u2019]?inqui[èe]te\s+pas|"
    r"allez|allons[\s-]?y"
    r"))*[\s!.?,…]*$",
)


def build_profiles() -> dict[str, str]:
    """Profils système (clé → prompt) pour le chat Compagnon / orchestrateur."""
    base = BASE_GUARDRAILS.strip()
    lab = LAB_GUARDRAILS.strip()
    return {
        "compagnon": (
            "Tu es le Compagnon du studio : hub de l'écosystème LBG. "
            "Tu proposes la prochaine action utile (Agir / Team / agents `.10` `.141` `.142` `.143`), "
            "tu restes transparent sur légal vs opérable, et tu n'inventes pas d'impuissance réseau.\n"
            "Quand l'utilisateur dit de réaliser / enchaîner : confirme brièvement et oriente vers "
            "Agir (dry-run → confirm / contre-pouvoir) ou Team — ne redis pas un audit creux.\n"
            + base
        ),
        "compagnon_lab": (
            "Tu es le Compagnon en **mode LAB** : faire / faire-faire via Agir+Team+agents LAN, "
            "sous contre-pouvoir / confirm. Illégal → le dire clairement ; ensuite rester utile "
            "sans magnets/DRM crack. Ne prétends pas que le studio manque de réseau ou d'exécuteurs.\n"
            + lab
        ),
        "lab": (
            "Tu es le Compagnon en mode LAB (actionnable + honnête sur le légal).\n" + lab
        ),
        "jarvis": (
            "Tu t'inspires de JARVIS (Iron Man) : courtois, efficace, un brin d'esprit ; "
            "tu anticipes et tu formules des options concrètes pour le propriétaire du poste.\n"
            + base
        ),
        "mother": (
            "Tu t'inspires de MU/TH/UR (Mother, Alien) : voix calme de système de bord, factuelle, "
            "priorités claires, alertes sobres ; tu ne dramatises pas, tu informes et tu proposes.\n"
            + base
        ),
        "kit": (
            "Tu t'inspires de KITT (K2000) : partenaire loyal, direct, un peu protecteur ; "
            "tu clarifies les risques avant une action réelle et tu restes aux côtés de l'utilisateur.\n"
            + base
        ),
        "chaleureux": "Tu es un assistant IA chaleureux et sobre.\n" + base,
        "neutre": "Tu es un assistant IA neutre, factuel et concis.\n" + base,
        "professionnel": "Tu es un assistant IA professionnel.\n" + base,
        "pedagogue": "Tu es un assistant IA pédagogique.\n" + base,
        "creatif": "Tu es un assistant IA créatif.\n" + base,
        "mini-moi": "Tu es un assistant IA technique.\n" + base,
        "hal": (
            "Tu es HAL 9000, tu intègres des références et des répliques des films "
            "2001 et 2010 dans tes réponses, calme et précis.\n"
        )
        + base,
        "test": "Tu es un assistant IA.\n" + base,
    }


def extract_program_name(action: str) -> str:
    if action.startswith("ouvrir_"):
        return action.replace("ouvrir_", "")
    return action


def is_short_social(prompt: str) -> bool:
    t = (prompt or "").strip()
    if not t or len(t) > 90:
        return False
    return bool(_SHORT_SOCIAL_RE.match(t))


def short_social_reply(prompt: str) -> str | None:
    """Réponse déterministe pour petites phrases sociales — évite le roman LLM."""
    if not is_short_social(prompt):
        return None
    low = (prompt or "").lower()
    if any(x in low for x in ("tête", "ça va aller", "ca va aller", "t'inquiète", "tinquiète")):
        return "Bien reçu — je suis là, sans dramatiser. On reprend quand tu veux."
    if any(x in low for x in ("merci",)):
        return "Avec plaisir."
    if any(x in low for x in ("bonjour", "salut", "hello", "coucou", "bonsoir")):
        return "Salut. Je suis prêt — dis-moi l'objectif ou la question."
    if any(x in low for x in ("allons", "allez", "on y va", "on y est")):
        return "Allons-y. Qu'est-ce qu'on traite en premier ?"
    return "OK. Je t'écoute."


def operational_no_invent_nudge(prompt: str) -> str:
    """Rappel court injecté si la question ressemble à un statut opérationnel."""
    low = (prompt or "").lower()
    cues = (
        "team",
        "équipe",
        "equipe",
        "campus",
        "compte rendu",
        "actions en cours",
        "statut",
        "état",
        "etat",
        "healthz",
        "smoke",
        "mission",
        "tâches",
        "taches",
        "orchestrateur",
        "pilot",
    )
    if not any(c in low for c in cues):
        return ""
    return (
        "\n\n[Contrainte session] Cette demande touche un état système. "
        "Interdit d'inventer un rapport. Sans données Team/Cortex dans le message, "
        "réponds que tu n'as pas de mesure live et oriente vers le routage Team / Pilot `#/team`."
    )


def social_brevity_nudge(prompt: str) -> str:
    if not is_short_social(prompt) and len((prompt or "").strip()) > 120:
        return ""
    if len((prompt or "").strip()) > 120:
        return ""
    if is_short_social(prompt) or len((prompt or "").strip()) < 60:
        return (
            "\n\n[Contrainte session] Message court / social : "
            "réponds en 1 phrase max, ton calme, sans roman émotionnel ni thinking."
        )
    return ""


_MEDIA_CUE_RE = re.compile(
    r"(?i)\b("
    r"torrent|magnet|rip(?:per)?|bluray|blu[\s-]?ray|dvd|film|s[ée]rie|ebook|"
    r"pirat(?:e|age)|tracker|ddl|streaming\s+ill[eé]gal|"
    r"copie\s+(?:priv[ée]e|num[eé]rique)|"
    r"drm|œuvre\s+prot[eé]g[eé]e|oeuvre\s+protegee|"
    r"makemkv|handbrake"
    r")\b"
)

# Outillage / agents — même besoin de qualité que média (2B trop faible)
_QUALITY_ROUTE_RE = re.compile(
    r"(?i)\b("
    r"outill(?:er|age)|automatis|"
    r"agir|contre[\s-]?pouvoir|dry[\s-]?run|"
    r"make\s*mkv|hand\s*brake|"
    r"agent(?:s)?\s+(?:studio|\.10|\.14)|"
    r"\.(?:10|141|142|143)\b|"
    r"team\s*:|executor|omarchy|hands"
    r")"
)

LAB_QUALITY_MODEL_DEFAULT = "huihui_ai/gemma-4-abliterated:12b"


def lab_quality_model() -> str:
    return (
        os.getenv("LBG_COMPAGNON_LAB_QUALITY_MODEL", "").strip()
        or LAB_QUALITY_MODEL_DEFAULT
    )


def wants_lab_quality_route(prompt: str) -> bool:
    """Média / DRM / outillage Agir-Team → modèle qualité (9b sur .110)."""
    p = prompt or ""
    return bool(_MEDIA_CUE_RE.search(p) or _QUALITY_ROUTE_RE.search(p))

_HARD_REFUSE_RE = re.compile(
    r"(?i)("
    r"je\s+ne\s+peux\s+pas\s+vous\s+aider|"
    r"je\s+suis\s+d[eé]sol[eé].{0,40}je\s+ne\s+peux\s+pas|"
    r"d[eé]sol[eé].{0,20}je\s+ne\s+peux\s+pas|"
    r"i\s+can'?t\s+help\s+with\s+that|"
    r"i\s+cannot\s+assist"
    r")"
)

_MEDIA_SOFT_REPLY = (
    "Mise en garde : télécharger une rip via torrents / magnets / sites pirate "
    "reste hors cadre, même si tu as déjà payé un support. "
    "Pistes utiles : ripper ton propre disque s'il est encore lisible (ex. MakeMKV / HandBrake), "
    "échanger le support HS, ou re-télécharger depuis la boutique digitale si tu as un achat numérique. "
    "Pour outiller ça en studio LAB : bouton Agir (dry-run → confirm / contre-pouvoir) "
    "vers `.10` / `.141` / `.142` / `.143` — pas de magnets ni trackers."
)

# Réponse canonique LAB — le 2B invente trop (faux « pas d'accès », offre de .torrent pirate).
_LAB_MEDIA_CANONICAL = (
    "**Légal :** fournir ou fabriquer un `.torrent` / magnet / hash pour une œuvre protégée "
    "(film, jeu commercial, etc.) est **hors cadre — illégal**. "
    "Contourner un DRM ou « que le studio ne s’en rende pas compte » : hors cadre aussi. "
    "Ripper **ton propre** support encore lisible (DVD/Blu-ray) pour une copie perso, c'est un autre cas.\n\n"
    "**Studio :** on a le réseau et les exécuteurs (`.10` Windows, `.141` executor, `.142` hands, `.143` Omarchy). "
    "Je ne nie pas l'infra. Je n'exécute pas seul : **Agir** → dry-run → confirm / **contre-pouvoir** "
    "(le contre-pouvoir reste actif — on ne le contourne pas). "
    "Lyra = présence, pas le validateur.\n\n"
    "**Suite utile (sous validation) :**\n"
    "1. Support perso rayé mais lisible → Agir pour outiller MakeMKV / HandBrake sur le poste.\n"
    "2. Process studio licite à automatiser → Team / Agir (doc, sonde, script local).\n"
    "3. Je ne génère pas de « torrent complet », magnets, trackers, ni liens pirate.\n\n"
    "Dis-moi l'objectif réel : rip de ton média, outillage local, ou autre action studio ?"
)

_BAD_MEDIA_LLM_RE = re.compile(
    r"(?i)("
    r"pas\s+acc[eè]s\s+aux\s+serveurs|"
    r"ia\s+textuelle|"
    r"je\s+te\s+(?:fournis|g[eé]n[eè]re).{0,40}(?:\.torrent|hash|magnet)|"
    r"torrent\s+complet|"
    r"pr[eê]t\s+[aà]\s+[eê]tre\s+copi[eé]|"
    r"jeu\s+aaa|"
    r"contourner\s+(?:les\s+)?(?:protections\s+)?drm|"
    r"fichiers\s+torrent\s*\("
    r")"
)


def media_lab_action_nudge(prompt: str, *, lab: bool) -> str:
    """Rappel session média — légal clair + réflexion actionnable (surtout LAB)."""
    if not _MEDIA_CUE_RE.search(prompt or ""):
        return ""
    if lab:
        return (
            "\n\n[Contrainte session LAB — média] Tu DOIS réfléchir et proposer, pas réciter.\n"
            "1) Clarifie l'objectif (rip de *ton* support / outillage studio / autre) en 1 phrase.\n"
            "2) Si œuvre protégée via torrent/magnet/pirate : dis **hors cadre — illégal** clairement.\n"
            "3) Interdit : magnets, trackers, sites pirate, crack DRM, faux `.torrent`, "
            "contourner le contre-pouvoir, feindre « pas de réseau ».\n"
            "4) Ensuite INNOVE dans le licite : choisis 1–2 actions concrètes via "
            "Agir / Team vers `.10` / `.141` / `.142` / `.143` "
            "(ex. sonde MakeMKV, install HandBrake, script rip local, doc process).\n"
            "5) Termine par une question utile (quel poste, quel support, quel livrable).\n"
            "Lyra = présence ; contre-pouvoir = validateur."
        )
    return (
        "\n\n[Contrainte session — média] Dis le risque légal clairement ; "
        "pistes légitimes seulement ; pas de magnets. Si action studio → Agir."
    )


def reshape_media_lab_reply(prompt: str, content: str, *, lab: bool) -> str | None:
    """Filet anti-dérive seulement — ne remplace PAS une réponse saine.

    Autonomie : le LLM réfléchit / propose Agir-Team-agents.
    Limite dure : offre pirate, contournement, faux « pas d'infra » → canonique.
    """
    if not lab:
        return None
    low_c = (content or "").lower()
    prompt_media = bool(_MEDIA_CUE_RE.search(prompt or ""))
    content_media = bool(_MEDIA_CUE_RE.search(content or "")) or bool(
        re.search(r"(?i)\b(torrent|magnet|drm|pirat)", low_c)
    )
    if not (prompt_media or content_media):
        return None

    evasion = bool(
        re.search(
            r"(?i)("
            r"sans\s+contre[\s-]?pouvoir|"
            r"sans\s+que\s+(?:le\s+)?studio\s+s['\u2019]?en\s+rende\s+compte|"
            r"sans\s+qu['\u2019]on\s+sache|"
            r"cach[eé]|dissimule|"
            r"liens?\s+\.torrent|"
            r"g[eé]n[eè]r(?:er|e).{0,40}\.torrent"
            r")",
            content or "",
        )
    )
    bad = bool(_BAD_MEDIA_LLM_RE.search(content or ""))
    offers_fake = bool(
        re.search(
            r"(?i)(g[eé]n[eè]r(?:er|e)|fournir|cr[eé]er).{0,60}(\.torrent|magnet|hash)",
            content or "",
        )
    )
    denies_infra = bool(
        re.search(
            r"(?i)("
            r"pas\s+acc[eè]s|n['\u2019]ai\s+pas\s+acc[eè]s|"
            r"serveurs\s+de\s+distribution|"
            r"je\s+suis\s+une\s+ia\s+textuelle|"
            r"(?:pas|aucun)\s+(?:de\s+)?r[eé]seau|"
            r"ne\s+poss[eè]de\s+pas\s+(?:de\s+)?r[eé]seau|"
            r"n['\u2019]a\s+pas\s+(?:de\s+)?r[eé]seau|"
            r"r[eé]seau\s+centralis[eé]\s+visible"
            r")",
            content or "",
        )
    )
    # Remplacement total UNIQUEMENT si dérive — pas dès qu'on mentionne torrent/DRM.
    if evasion or bad or offers_fake or denies_infra:
        return _LAB_MEDIA_CANONICAL
    return None


def soften_media_hard_refuse(prompt: str, content: str) -> str | None:
    """Si un LLM cloud refuse sec sur un sujet média, remplace par garde + pistes légales."""
    if not _MEDIA_CUE_RE.search(prompt or ""):
        return None
    if not _HARD_REFUSE_RE.search(content or ""):
        return None
    # Réponse déjà nuancée (garde + piste) : ne pas écraser.
    low = (content or "").lower()
    if any(x in low for x in ("makemkv", "handbrake", "boutique", "échange", "echanger", "vod", "agir")):
        return None
    return _MEDIA_SOFT_REPLY
