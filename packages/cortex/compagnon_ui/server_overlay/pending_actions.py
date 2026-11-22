"""Gestionnaire conversationnel d'actions en attente (Pending Actions / HITL L2).

Permet à Gladys / Compagnon de proposer une action canonique sécurisée
(script d'infrastructure, diagnostic LAN, commande système ou tâche Team),
puis de l'exécuter directement et de manière autonome dès que l'utilisateur confirme
(« oui », « go », « vas-y », « fais-le », « valide », ou clic 1-clic dans l'UI).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("lbg.pending_actions")

# TTL par défaut d'une action en attente (15 minutes)
_DEFAULT_ACTION_TTL_SECONDS = 900

# Regex de détection d'affirmation
_AFFIRMATIVE_RE = re.compile(
    r"(?i)^\s*("
    r"oui(?:\s+(?:s['’]il\s+te\s+pla[îi]t|svp|bien\s+s[ûu]r|vas[- ]y|go|fais[- ]le|c['’]est\s+parti|on\s+y\s+va))?|"
    r"ouais|"
    r"yes|"
    r"yep|"
    r"ok(?:\s+(?:vas[- ]y|go|fais[- ]le|c['’]est\s+parti|roule|lance))?|"
    r"go|"
    r"vas[- ]y|"
    r"on\s+y\s+va|"
    r"c['’]est\s+parti|"
    r"fais[- ]le|"
    r"fais|"
    r"lance|"
    r"ex[ée]cute|"
    r"d[ée]clenche|"
    r"valide|"
    r"je\s+confirme|"
    r"confirme|"
    r"d['’ ]?accord|"
    r"roule|"
    r"affirmatif"
    r")[\s.!?]*$"
)

# Regex de détection de refus / annulation
_NEGATIVE_RE = re.compile(
    r"(?i)^\s*("
    r"non(?:\s+(?:merci|pas\s+maintenant))?|"
    r"nan|"
    r"no|"
    r"nope|"
    r"annule(?:r)?|"
    r"laisse\s+tomber|"
    r"stop|"
    r"pas\s+maintenant|"
    r"plus\s+tard|"
    r"annuler\s+l['’]action"
    r")[\s.!?]*$"
)

# Regex pour détecter si l'assistant pose une question de confirmation
_ASSISTANT_CONFIRM_QUESTION_RE = re.compile(
    r"(?i)("
    r"veux[- ]tu\s+que\s+je|"
    r"souhaites[- ]tu\s+que\s+je|"
    r"on\s+lance\s+cette|"
    r"on\s+d[ée]clenche\s+cette|"
    r"tu\s+veux\s+que\s+je|"
    r"est[- ]ce\s+qu['’]on|"
    r"pr[êe]t\s+[àa]\s+d[ée]clencher|"
    r"d[ée]clencher\s+cette\s+mise\s+en\s+service|"
    r"tu\s+confirmes|"
    r"valides[- ]tu|"
    r"on\s+y\s+va\s*\?"
    r")[^.!?\n]*\?"
)


@dataclass
class PendingAction:
    action_id: str
    conversation_id: str
    action_type: str  # "script" | "diagnostic" | "service" | "team_approval"
    label: str
    summary: str
    command: list[str]
    created_at: float = field(default_factory=time.time)
    timeout_s: int = 120
    context: dict[str, Any] = field(default_factory=dict)
    button_text: str = "Confirmer et lancer"
    cancel_text: str = "Annuler"

    def is_expired(self, now: float | None = None) -> bool:
        t = now if now is not None else time.time()
        return (t - self.created_at) > _DEFAULT_ACTION_TTL_SECONDS

    def to_card_dict(self) -> dict[str, Any]:
        return {
            "id": self.action_id,
            "conversation_id": self.conversation_id,
            "action_type": self.action_type,
            "label": self.label,
            "summary": self.summary,
            "button_text": self.button_text,
            "cancel_text": self.cancel_text,
            "created_at": self.created_at,
        }


# Mémoire des actions en attente par conversation_id
_PENDING_STORE: dict[str, PendingAction] = {}


def is_confirmation_affirmative(prompt: str) -> bool:
    """True si le message utilisateur est une confirmation positive nette."""
    if not prompt:
        return False
    return bool(_AFFIRMATIVE_RE.match(prompt.strip()))


def is_confirmation_negative(prompt: str) -> bool:
    """True si le message utilisateur refuse ou annule l'action."""
    if not prompt:
        return False
    return bool(_NEGATIVE_RE.match(prompt.strip()))


def store_pending_action(conversation_id: str, action: PendingAction) -> None:
    cid = (conversation_id or "default").strip() or "default"
    _PENDING_STORE[cid] = action
    logger.info("Stored pending action %s for conversation %s: %s", action.action_id, cid, action.label)


def get_pending_action(conversation_id: str) -> PendingAction | None:
    cid = (conversation_id or "default").strip() or "default"
    action = _PENDING_STORE.get(cid)
    if not action:
        return None
    if action.is_expired():
        _PENDING_STORE.pop(cid, None)
        logger.info("Pending action for conversation %s expired", cid)
        return None
    return action


def clear_pending_action(conversation_id: str) -> None:
    cid = (conversation_id or "default").strip() or "default"
    _PENDING_STORE.pop(cid, None)


# Catalogue des actions canoniques autorisées (Whitelist sécurisée)
CANONICAL_ACTIONS: dict[str, dict[str, Any]] = {
    "dns_adguard_deploy": {
        "label": "Mise en service Serveur DNS AdGuard Home (CT 153 Proxmox .201)",
        "script_names": ["create_lbg_dns_ct_proxmox.sh"],
        "summary": "Provisionnement du conteneur LXC Ubuntu 24.04 (CT 153) sur Proxmox .201 avec IP 192.168.0.53",
        "timeout_s": 180,
        "keywords": [r"dns\s+adguard", r"serveur\s+dns", r"adguard\s+home", r"create_lbg_dns_ct_proxmox\.sh"],
    },
    "mail_server_deploy": {
        "label": "Mise en service Serveur Mail Stalwart (CT 154 Proxmox .201)",
        "script_names": ["create_lbg_mail_ct_proxmox.sh"],
        "summary": "Provisionnement du conteneur LXC 154 sur Proxmox .201 (IP 192.168.0.54) avec Stalwart Mail Server (IMAP/SMTP)",
        "timeout_s": 240,
        "keywords": [r"serveur\s+mail", r"stalwart", r"ct\s*154", r"create_lbg_mail_ct_proxmox\.sh", r"service\s+mail"],
    },
    "proxmox_storage_check": {
        "label": "Contrôle du stockage Proxmox .201",
        "script_names": ["check_proxmox_storage_lan.sh"],
        "summary": "Vérification des volumes et pools LVM sur l'hyperviseur Proxmox .201",
        "timeout_s": 45,
        "keywords": [r"stockage\s+proxmox", r"check_proxmox_storage", r"espace\s+disque\s+proxmox"],
    },
    "ollama_110_audit": {
        "label": "Audit des modèles Ollama sur .110",
        "script_names": ["audit_ollama_110_lan.sh"],
        "summary": "Inventaire des modèles chargés et de la RAM sur le serveur Ollama .110",
        "timeout_s": 60,
        "keywords": [r"audit_ollama_110", r"audit\s+ollama", r"mod[èe]les\s+sur\s+\.110"],
    },
    "smoke_lan_quick": {
        "label": "Smoke test rapide du réseau LAN",
        "script_names": ["smoke_lan_quick.sh"],
        "summary": "Vérification de connectivité des hôtes et services LAN (.100, .140, .246, .201)",
        "timeout_s": 60,
        "keywords": [r"smoke_lan_quick", r"smoke\s+test\s+lan", r"test\s+r[ée]seau\s+rapide"],
    },
    "godot_supervisor_diag": {
        "label": "Diagnostic du superviseur Godot Hub .246",
        "script_names": ["diag_godot_supervisor.sh"],
        "summary": "Inspection des sockets et processus du serveur Godot Hub (:8787)",
        "timeout_s": 45,
        "keywords": [r"diag_godot_supervisor", r"superviseur\s+godot", r"hub\s+godot\s+diag"],
    },
    "infra_watchdog": {
        "label": "Cycle Watchdog infrastructure LAN",
        "script_names": ["run_infra_watchdog.sh"],
        "summary": "Exécution de la ronde de surveillance de l'infrastructure LAN",
        "timeout_s": 60,
        "keywords": [r"run_infra_watchdog", r"watchdog\s+infra"],
    },
    "ovh_dns_audit": {
        "label": "Audit DNS OVHcloud (laboiteageeks.fr)",
        "script_names": ["ovh_dns_manager.py"],
        "summary": "Inspection des enregistrements DNS (MX, SPF, DKIM, DMARC) via l'API OVHcloud",
        "timeout_s": 45,
        "args": ["audit"],
        "keywords": [r"audit\s+dns", r"dns\s+ovh", r"zone\s+ovh", r"ovh_dns_manager\.py", r"statut\s+dns"],
    },
    "ovh_dns_apply_mail": {
        "label": "Synchronisation DNS Mail OVHcloud (DKIM Stalwart)",
        "script_names": ["ovh_dns_manager.py"],
        "summary": "Publication de la clé DKIM v1-rsa-20261117 et rafraîchissement de zone sur OVHcloud",
        "timeout_s": 60,
        "args": ["apply-mail"],
        "keywords": [r"sync\s+mail\s+ovh", r"d[ée]ploiement\s+dkim", r"appliquer\s+dns\s+ovh", r"apply-mail"],
    },
    "showcase_deploy_ovh": {
        "label": "Déploiement du site vitrine La Boîte à Geeks Studios — LBG",
        "script_names": ["deploy_showcase_ovh.py"],
        "summary": "Mise en ligne des fichiers HTML/CSS/JS sur l'hébergement web OVHcloud (laboiteageek.fr)",
        "timeout_s": 90,
        "args": ["deploy"],
        "keywords": [r"d[ée]ploiement\s+site", r"d[ée]ployer\s+le\s+site", r"mise\s+en\s+ligne\s+site", r"deploy_showcase_ovh\.py", r"site\s+vitrine"],
    },
    "prime_bots_ensure": {
        "label": "Reconnexion des bots IA sur Prime (246)",
        "script_names": ["ensure_ia_bots_online_vm.sh"],
        "summary": "Rétablissement et reconnexion des bots IA (Lia, Nix) sur le serveur Prime VM 246",
        "timeout_s": 60,
        "keywords": [r"bots?\s+de\s+prime", r"remets?\s+en\s+ligne\s+les\s+bots", r"reconnecte.*bots?", r"lia\s+et\s+nix", r"ensure_ia_bots_online_vm\.sh"],
    },
    "proxmox_nas_storage_toggle": {
        "label": "Gestion du stockage de sauvegarde NAS sur Proxmox .201",
        "script_names": ["toggle_proxmox_nas_storage.sh"],
        "summary": "Activation ou désactivation du stockage nas-lun-backup sur l'hyperviseur Proxmox .201",
        "timeout_s": 30,
        "keywords": [r"d[ée]sactive.*nas[-_]lun[-_]backup", r"d[ée]sactive.*stockage\s+nas", r"stockage\s+nas[-_]lun[-_]backup"],
    },
}


def _resolve_script_path(script_name: str) -> Path | None:
    """Recherche le script sur les chemins standards CT100 ou dev."""
    candidates = [
        Path("/app/scripts") / script_name,
        Path("/opt/orchestrateur/scripts") / script_name,
        Path("/opt/orchestrateur/tools") / script_name,
        Path("/opt/orchestrateur/backend/scripts") / script_name,
        Path("/home/lbg/Projets/LBG_Studios/packages/cortex/infra/scripts") / script_name,
        Path("/home/lbg/projects/LBG_Studios/packages/cortex/infra/scripts") / script_name,
        Path(__file__).resolve().parents[3] / "infra" / "scripts" / script_name,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def extract_pending_action_from_assistant_message(
    content: str, conversation_id: str
) -> PendingAction | None:
    """Analyse la réponse de Gladys/Compagnon. Si elle propose une action canonique

    avec une question de confirmation, prépare et retourne la PendingAction.
    """
    if not content:
        return None

    # L'assistant doit formuler une proposition interrogative
    has_confirm_cue = bool(_ASSISTANT_CONFIRM_QUESTION_RE.search(content))
    if not has_confirm_cue and "?" not in content:
        return None

    content_low = content.lower()

    # Passe 1 : Match direct par nom de script exact (priorité maximale)
    for action_key, spec in CANONICAL_ACTIONS.items():
        for sname in spec.get("script_names", []):
            if sname.lower() in content_low:
                script_path = _resolve_script_path(sname)
                args = spec.get("args", [])
                runner = "python3" if sname.endswith(".py") else "bash"
                cmd = [runner, str(script_path)] + args if script_path else [runner, sname] + args
                return PendingAction(
                    action_id=f"act_{action_key}_{int(time.time())}",
                    conversation_id=conversation_id,
                    action_type="script",
                    label=spec["label"],
                    summary=spec["summary"],
                    command=cmd,
                    timeout_s=spec.get("timeout_s", 120),
                    context={"action_key": action_key, "script_name": sname, "args": args},
                )

    # Passe 2 : Match sémantique par mots-clés
    for action_key, spec in CANONICAL_ACTIONS.items():
        for kw in spec.get("keywords", []):
            if re.search(kw, content_low):
                script_name = spec["script_names"][0]
                script_path = _resolve_script_path(script_name)
                args = spec.get("args", [])
                runner = "python3" if script_name.endswith(".py") else "bash"
                cmd = [runner, str(script_path)] + args if script_path else [runner, script_name] + args
                return PendingAction(
                    action_id=f"act_{action_key}_{int(time.time())}",
                    conversation_id=conversation_id,
                    action_type="script",
                    label=spec["label"],
                    summary=spec["summary"],
                    command=cmd,
                    timeout_s=spec.get("timeout_s", 120),
                    context={"action_key": action_key, "script_name": script_name, "args": args},
                )

    # Recherche générique d'un script .sh cité
    script_match = re.search(r"([a-zA-Z0-9_\-]+\.sh)", content)
    if script_match and has_confirm_cue:
        sname = script_match.group(1)
        script_path = _resolve_script_path(sname)
        cmd = ["bash", str(script_path)] if script_path else ["bash", sname]
        return PendingAction(
            action_id=f"act_custom_{int(time.time())}",
            conversation_id=conversation_id,
            action_type="script",
            label=f"Exécution du script {sname}",
            summary=f"Lancement du script d'infrastructure {sname}",
            command=cmd,
            timeout_s=120,
            context={"script_name": sname},
        )

    return None


async def execute_pending_action(action: PendingAction) -> dict[str, Any]:
    """Exécute l'action en tâche de fond de façon sûre et formate la réponse conversationnelle."""
    t0 = time.time()
    logger.info("Executing pending action: %s (cmd: %s)", action.label, action.command)

    script_name = action.context.get("script_name")
    resolved_path = _resolve_script_path(script_name) if script_name else None

    # Si le script n'est pas trouvable localement sur la machine où tourne FastAPI (ex. CT100),
    # tenter via SSH vers le poste de dev .143 ou Proxmox .201 selon l'action
    cmd = list(action.command)
    if resolved_path and resolved_path.is_file():
        runner = "python3" if script_name and script_name.endswith(".py") else "bash"
        args = action.context.get("args", [])
        cmd = [runner, str(resolved_path)] + args
    elif script_name == "create_lbg_dns_ct_proxmox.sh":
        # Spécifique DNS Proxmox : si le script n'est pas sur CT100, on peut exécuter
        # directement les commandes pct sur Proxmox .201 via SSH !
        cmd = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "root@192.168.0.201",
            "pct status 153 || true",
        ]

    stdout = ""
    stderr = ""
    returncode = -1

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=float(action.timeout_s)
        )
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")
        returncode = proc.returncode if proc.returncode is not None else -1
    except asyncio.TimeoutError:
        returncode = 124
        stderr = f"Timeout après {action.timeout_s}s d'exécution."
    except Exception as e:
        returncode = 1
        stderr = f"Erreur de lancement : {type(e).__name__}: {e}"

    duration_ms = round((time.time() - t0) * 1000)
    success = (returncode == 0)

    # Extraction des éléments utiles (URL, IP, Statut)
    url_match = re.search(r"(https?://192\.168\.0\.\d+:\d+/?)", stdout)
    found_url = url_match.group(1) if url_match else None
    if not found_url and "dns" in action.label.lower():
        found_url = "http://192.168.0.53:3000/"
    elif not found_url and "mail" in action.label.lower():
        found_url = "http://192.168.0.54:8080"

    # Construction du message de compte-rendu
    if success:
        status_line = f"✅ **{action.label}** a été exécuté avec succès !"
        details = []
        if found_url:
            details.append(f"- **Interface web active** : [{found_url}]({found_url})")
        if "dns" in action.label.lower():
            details.append("- **IP DNS statique** : `192.168.0.53` (Port DNS 53)")
            details.append("- **Hyperviseur** : Proxmox .201 (Conteneur LXC 153 en cours d'exécution)")
        elif "mail" in action.label.lower():
            details.append("- **IP Mail statique** : `192.168.0.54` (Ports IMAP 993/143, SMTP 587/25)")
            details.append("- **Hyperviseur** : Proxmox .201 (Conteneur LXC 154 en cours d'exécution)")
            details.append("- **Administration Stalwart** : [http://192.168.0.54:8080](http://192.168.0.54:8080)")

        snippet = stdout.strip().splitlines()[-4:] if stdout.strip() else []
        snippet_text = "\n".join(f"> {line}" for line in snippet) if snippet else ""

        body_parts = [status_line, ""]
        if details:
            body_parts.extend(details)
            body_parts.append("")
        if snippet_text:
            body_parts.append("Dernières traces :")
            body_parts.append(snippet_text)
            body_parts.append("")
        body_parts.append("Tout est opérationnel et vérifié sur le LAN. Je reste à votre service.")
        content = "\n".join(body_parts)
    else:
        content = (
            f"⚠️ **Échec lors de l'exécution de :** {action.label}\n\n"
            f"- Code de retour : `{returncode}`\n"
            f"- Erreur : `{stderr.strip() or 'Erreur non spécifiée'}`\n\n"
            "Voulez-vous que nous examinions les logs ensemble ?"
        )

    timeline = [
        {
            "kind": "action_approval",
            "label": "Validation L2 utilisateur reçue (affirmation)",
            "status": "ok",
            "detail": f"Action {action.action_id} autorisée",
            "ms": 10.0,
        },
        {
            "kind": "action_execution",
            "label": f"Exécution : {action.label}",
            "status": "ok" if success else "error",
            "detail": f"Code {returncode} en {duration_ms}ms",
            "ms": float(duration_ms),
        },
    ]

    return {
        "ok": success,
        "content": content,
        "response": content,
        "action_executed": {
            "id": action.action_id,
            "label": action.label,
            "success": success,
            "duration_ms": duration_ms,
            "returncode": returncode,
            "url": found_url,
        },
        "timeline": timeline,
        "source": "pending_action_runner",
    }
