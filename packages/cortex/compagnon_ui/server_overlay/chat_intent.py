"""Heuristiques chat Compagnon — identité / causerie vs ops Team.

Pure (pas d'I/O) : utilisé pour reflection + tests.
"""

from __future__ import annotations

import re


# Greeting / social chaud — doit rester en causerie (pas bible ops Agir)
_GREETING_CHAT_RE = re.compile(
    r"(?i)^\s*("
    r"(?:bonjour|salut|hello|hey|coucou|bonsoir)\b|"
    r"comment\s+(?:(?:ça|ca)\s+)?va\b|"
    r"(?:ça|ca)\s+va\b|"
    r"(?:bien\s+)?merci\b.{0,40}\bet\s+toi\b|"
    r"et\s+toi\s*\??\s*$|"
    r"comment\s+vas[- ]?tu\b"
    r")"
)

# Demande de livrable plan / démarrage travail (pas du social vide)
_PLAN_DELIVERY_RE = re.compile(
    r"(?i)\b("
    r"plan\s+d['\u2019 ]?action|"
    r"pr[ée]pare(?:r)?\s+(?:le\s+|un\s+)?plan|"
    r"r[ée]dige(?:r)?\s+(?:le\s+|un\s+)?plan|"
    r"structure(?:r)?\s+(?:le\s+|un\s+)?plan|"
    r"formalise(?:r)?\s+(?:le\s+|un\s+)?plan|"
    r"soumet(?:s|tre)?(?:[- ]?(?:le|la|l|ce|cette))?.{0,40}(?:au\s+)?studio|"
    r"livr(?:e|er)\s+(?:un\s+|le\s+)?plan|"
    r"commence(?:r)?\s+[àa]\s+travaill|"
    r"commence(?:r)?\s+dessus|"
    r"travaill(?:e|er)\s+dessus|"
    r"fais[- ]?moi\s+(?:un\s+)?plan|"
    r"propose(?:r)?\s+(?:un\s+)?plan"
    r")\b"
)

_GO_AHEAD_RE = re.compile(
    r"(?i)^\s*("
    r"allons[\s-]?y|allez(?:[\s-]?y)?|"
    r"on\s+y\s+va|on\s+y\s+est|"
    r"go\s*!+|c['\u2019]?est\s+parti|"
    r"ok\s+(?:go|vas[- ]?y)|vas[- ]?y"
    r")[\s!.?,…]*$"
)

_PENDING_WORK_RE = re.compile(
    r"(?i)\b("
    r"plan\s+d['\u2019 ]?action|pr[ée]pare(?:r)?|r[ée]dige(?:r)?|"
    r"soumet(?:tre)?|livr(?:e|able)|commence(?:r)?|travaill(?:e|er)\s+dessus|"
    r"prototyp|formalise|structure(?:r)?\s+(?:le\s+|un\s+)?plan|"
    r"fais[- ]?moi\s+(?:un\s+)?plan|propose(?:r)?\s+(?:un\s+)?plan"
    r")\b"
)

# Causerie / identité — ne doit JAMAIS partir en team_route / agent.fallback
_IDENTITY_CHAT_RE = re.compile(
    r"(?i)("
    r"\bqui\s+es[- ]?tu\b|"
    r"\bqui\s+êtes[- ]?vous\b|"
    r"\btu\s+es\s+qui\b|"
    r"\bc['\u2019]?est\s+quoi\s+ton\s+nom\b|"
    r"\bpr[ée]sente[- ]?toi\b|"
    r"\bparle[- ]?moi\s+de\s+toi\b|"
    r"\braconte[- ]?moi\b|"
    r"\bdis[- ]?moi\b|"
    r"\bsur\s+toi\b|"
    r"\bquelque\s+chose\s+d['\u2019 ]?int[ée]ressant\b|"
    r"\btu\s+peux\s+me\s+dire\b|"
    r"\bpeux[- ]?tu\s+me\s+dire\b|"
    r"\bquoi\s+sur\s+toi\b|"
    r"\bton\s+(r[ôo]le|job|m[ée]tier|persona|caract[èe]re)\b|"
    r"\btes\s+(capacit[ée]s|pouvoirs|talents)\b"
    r")"
)

# Exploration / sparring — chatter avant d'agir (pas d'ops)
_EXPLORATORY_CHAT_RE = re.compile(
    r"(?i)("
    r"\bchatter\b|"
    r"\b[ée]changer\b|"
    r"\bconfondre\b|"
    r"\bdiscut(?:er|ons|e|ion)\b|"
    r"\bpapoter\b|"
    r"\bbavarder\b|"
    r"\bsparring\b|"
    r"\bbrainstorm\b|"
    r"\bcoll[eè]gues?\b|"
    r"\bamis?\b|"
    r"\bcomme\s+si\s+(?:on|nous)\b|"
    r"\bfrustr(?:e|é|ée|ation)\b|"
    r"\bfluidit[ée]\b|"
    r"\binventes?\b|"
    r"\binvestigat|"
    r"\bpistes?\s+d['\u2019 ]?am[ée]lior|"
    r"\bton\s+avis\b|"
    r"\bque\s+penses?[- ]?tu\b|"
    r"\bqu['\u2019]?en\s+penses[- ]?tu\b|"
    r"\br[ôo]le\s+(?:du\s+)?compagnon\b|"
    r"\br[ôo]le\s+de\s+lyra\b|"
    r"\blyra\b|"
    r"\bpr[êe]t\s+(?:pour|à|a)\b|"
    r"\baider\s+[àa]\s+faire\s+[ée]volu|"
    r"\bfaire\s+[ée]volu(?:er|tion)\b|"
    r"\bjusqu['\u2019]?o[uù]\b|"
    r"\bmaturité\b|"
    r"\bmaturit[ée]\b|"
    r"\bécosyst[èe]me\b|"
    r"\becosysteme\b|"
    r"\bmmorpg\b|"
    r"\bprendre\s+des\s+d[ée]cisions\b|"
    r"\bvalider\s+l[12]\b|"
    r"\bpartie\s+(?:team|studio)\b|"
    r"\bprojet\s+lbg\b|"
    r"\bsur\s+le\s+projet\b|"
    r"\bcampus\b|"
    r"\bc['\u2019]?est\s+quoi\b|"
    r"\bqu['\u2019]?est[- ]ce\s+que\b"
    r")"
)

_OPS_OVERRIDE_RE = re.compile(
    r"(?i)\b("
    r"team|mission|smoke|deploy|d[ée]ploy|proxmox|healthz|selfcheck|"
    r"sondes?|disk|disque|ram|cpu|status|statut|compte\s+rendu|@hephaistos|"
    r"@argus|@themis|pilot|orchestrateur|"
    r"campus\s+(?:status|statut|mission|spawn|jobs?)|"
    r"(?:status|statut|mission|spawn)\s+campus|"
    r"auto[\s-]?audit|\baudit\b|diagnostic|bilan"
    r")\b"
)

_STUDIO_SCOPE_RE = re.compile(
    r"(?i)\b("
    r"team|studio|campus|atlas|plateforme|pilot|cortex|"
    r"[ée]cosyst[èe]me|ecosysteme|maturité|maturite|"
    r"base|bases|état\s+actuel|etat\s+actuel|[ée]volution"
    r")\b"
)

_OLLAMA_SCOPE_RE = re.compile(
    r"(?i)\b("
    r"ollama|\.110|\.111|providers?\s+llm|mod[èe]les?\s+(?:llm|ollama|locaux)|"
    r"llm\s+local|topo\s+llm"
    r")\b"
)

_AUDIT_CUE_RE = re.compile(
    r"(?i)\b("
    r"auto[\s-]?audit|\baudit\b|bilan|"
    r"[ée]tat\s+(?:actuel|complet)|etat\s+(?:actuel|complet)|"
    r"bonne(?:s)?\s+bases?|partir\s+sur\s+de\s+bonnes?\s+bases?"
    r")\b"
)

_BROAD_AUDIT_RE = re.compile(
    r"(?i)("
    r"\bauto[\s-]?audit\b|"
    r"\b(faire|lancer|run|demande|veux|voudrais|pourrais)\b.{0,40}\baudit\b|"
    r"\baudit\b.{0,40}\b(base|bases|[ée]tat|etat|[ée]volution|complet)\b"
    r")"
)


def _ctx_text(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("content") or item.get("prompt") or item.get("text") or "")
    return str(item or "")


def is_greeting_chat(prompt: str) -> bool:
    """True si ouverture sociale / greeting (doit sentir compagnon, pas hub ops)."""
    text = (prompt or "").strip()
    if not text or len(text) > 120:
        return False
    if _OPS_OVERRIDE_RE.search(text):
        return False
    return bool(_GREETING_CHAT_RE.search(text))


def wants_plan_delivery(prompt: str) -> bool:
    """True si l'humain demande un plan / livrable utilisable (pas de méta vide)."""
    text = (prompt or "").strip()
    if not text or len(text) > 500:
        return False
    return bool(_PLAN_DELIVERY_RE.search(text))


def is_go_ahead(prompt: str) -> bool:
    """True si go-ahead court (« allons-y ») — peut signifier « livre / enchaîne »."""
    text = (prompt or "").strip()
    if not text or len(text) > 40:
        return False
    return bool(_GO_AHEAD_RE.match(text))


def has_pending_work(short_ctx: list | None = None) -> bool:
    """True si le fil récent porte une demande de plan / travail (sticky livraison)."""
    if not short_ctx:
        return False
    for item in list(short_ctx)[-8:]:
        role = ""
        if isinstance(item, dict):
            role = str(item.get("role") or "").lower()
        chunk = _ctx_text(item).strip()
        if not chunk:
            continue
        if role in ("assistant", "ai", "compagnon"):
            continue
        if wants_plan_delivery(chunk) or _PENDING_WORK_RE.search(chunk):
            return True
    return False


def wants_deliverable_turn(prompt: str, short_ctx: list | None = None) -> bool:
    """True → ce tour doit produire un artefact (plan) plutôt qu'un short_social / méta."""
    if wants_plan_delivery(prompt):
        return True
    if is_go_ahead(prompt) and has_pending_work(short_ctx):
        return True
    return False


def is_companion_chat(prompt: str) -> bool:
    """True si message = causerie / identité / exploration Compagnon (pas d'ops)."""
    text = (prompt or "").strip()
    if not text or len(text) > 400:
        return False
    if _OPS_OVERRIDE_RE.search(text):
        return False
    if is_greeting_chat(text):
        return True
    if wants_plan_delivery(text):
        return True
    return bool(_IDENTITY_CHAT_RE.search(text) or _EXPLORATORY_CHAT_RE.search(text))


def wants_exploratory_chat(prompt: str) -> bool:
    """Causerie exploratoire (sparring / maturité / écosystème) — même hors ops override partiel."""
    text = (prompt or "").strip()
    if not text:
        return False
    if _AUDIT_CUE_RE.search(text) and _STUDIO_SCOPE_RE.search(text):
        return False
    if is_greeting_chat(text) or wants_plan_delivery(text):
        return True
    return bool(_EXPLORATORY_CHAT_RE.search(text) or _IDENTITY_CHAT_RE.search(text))


def wants_sticky_causerie(
    prompt: str,
    *,
    short_ctx: list | None = None,
) -> bool:
    """True si le tour courant OU le fil récent est une causerie (sans override ops dur)."""
    text = (prompt or "").strip()
    if not text:
        return False
    conceptual = bool(
        re.search(
            r"(?i)\b("
            r"c['\u2019]?est\s+quoi|qu['\u2019]?est[- ]ce\s+que|défini[rst]?|explique|"
            r"pour\s+toi|ton\s+avis|pense[- ]?tu|discut|coll[eè]gue"
            r")\b",
            text,
        )
    )
    # Override ops explicite → sortir de la sticky (sauf question conceptuelle)
    if _OPS_OVERRIDE_RE.search(text) and not conceptual:
        return False
    if wants_exploratory_chat(text) or is_companion_chat(text):
        return True
    if not short_ctx:
        return False
    # Sticky : un message user récent a ouvert une causerie
    for item in list(short_ctx)[-8:]:
        role = ""
        if isinstance(item, dict):
            role = str(item.get("role") or "").lower()
        chunk = _ctx_text(item).strip()
        if not chunk:
            continue
        if role in ("assistant", "ai", "compagnon"):
            continue
        if wants_exploratory_chat(chunk) or is_companion_chat(chunk):
            return True
    return False


def wants_studio_team_audit(prompt: str) -> bool:
    """Audit Team / studio / plateforme — PAS inventaire Ollama seul."""
    text = (prompt or "").strip()
    if not text or not _AUDIT_CUE_RE.search(text):
        return False
    if _OLLAMA_SCOPE_RE.search(text) and not _STUDIO_SCOPE_RE.search(text):
        return False
    return bool(_STUDIO_SCOPE_RE.search(text))


def wants_broad_audit(prompt: str) -> bool:
    """Auto-audit / bilan large → tool_loop (Team d'abord)."""
    text = (prompt or "").strip()
    if not text:
        return False
    if wants_studio_team_audit(text):
        return True
    if _OLLAMA_SCOPE_RE.search(text) and not _STUDIO_SCOPE_RE.search(text):
        return False
    return bool(_BROAD_AUDIT_RE.search(text))


def wants_ollama_only_audit(prompt: str) -> bool:
    """Audit strictement LLM/Ollama .110/.111."""
    text = (prompt or "").strip()
    if not text:
        return False
    if not (_AUDIT_CUE_RE.search(text) or _OLLAMA_SCOPE_RE.search(text)):
        return False
    if _STUDIO_SCOPE_RE.search(text) and not _OLLAMA_SCOPE_RE.search(text):
        return False
    return bool(_OLLAMA_SCOPE_RE.search(text))
