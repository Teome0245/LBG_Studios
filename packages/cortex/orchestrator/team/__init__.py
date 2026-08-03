"""Équipe virtuelle studio — file de tâches par rôle (phase A + ADR 0019)."""

# Imports paresseux : éviter de tirer roles/dispatch au simple `import team.store`.

__all__ = ["team_store", "team_roles"]


def __getattr__(name: str):  # pragma: no cover
    if name == "team_store":
        from team import store as team_store

        return team_store
    if name == "team_roles":
        from team import roles as team_roles

        return team_roles
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
