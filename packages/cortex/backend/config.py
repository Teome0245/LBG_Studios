"""Configuration centralisée du backend (variables d'environnement LBG_*)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    lbg_cors_origins: str = Field(default="", validation_alias="LBG_CORS_ORIGINS")
    lbg_orchestrator_url: str = Field(default="http://127.0.0.1:8010", validation_alias="LBG_ORCHESTRATOR_URL")
    ollama_base_url: str = Field(default="http://192.168.0.110:11434", validation_alias="OLLAMA_BASE_URL")

    lbg_agent_dialogue_url: str = Field(default="", validation_alias="LBG_AGENT_DIALOGUE_URL")
    lbg_agent_quests_url: str = Field(default="", validation_alias="LBG_AGENT_QUESTS_URL")
    lbg_agent_combat_url: str = Field(default="", validation_alias="LBG_AGENT_COMBAT_URL")
    lbg_agent_pm_url: str = Field(default="", validation_alias="LBG_AGENT_PM_URL")
    lbg_agent_desktop_url: str = Field(default="", validation_alias="LBG_AGENT_DESKTOP_URL")
    lbg_mmo_server_url: str = Field(default="", validation_alias="LBG_MMO_SERVER_URL")
    lbg_mmo_internal_token: str = Field(default="", validation_alias="LBG_MMO_INTERNAL_TOKEN")

    lbg_pilot_internal_token: str = Field(default="", validation_alias="LBG_PILOT_INTERNAL_TOKEN")
    lbg_pilot_internal_rl_rps: float = Field(default=0.0, validation_alias="LBG_PILOT_INTERNAL_RL_RPS")
    lbg_pilot_internal_rl_burst: int = Field(default=0, validation_alias="LBG_PILOT_INTERNAL_RL_BURST")
    lbg_pilot_agent_dialogue_invoke_timeout: str = Field(
        default="300", validation_alias="LBG_PILOT_AGENT_DIALOGUE_INVOKE_TIMEOUT"
    )
    lbg_pilot_lbgia_backend_url: str = Field(default="", validation_alias="LBG_PILOT_LBGIA_BACKEND_URL")
    lbg_ia_backend_url: str = Field(default="", validation_alias="LBG_IA_BACKEND_URL")
    lbg_pilot_lbgia_http_timeout: str = Field(default="3", validation_alias="LBG_PILOT_LBGIA_HTTP_TIMEOUT")

    lbg_lan_host_precu: str = Field(default="192.168.0.245", validation_alias="LBG_LAN_HOST_PRECU")
    lbg_lan_host_mmo: str = Field(default="192.168.0.246", validation_alias="LBG_LAN_HOST_MMO")
    lbg_lan_host_front: str = Field(default="192.168.0.110", validation_alias="LBG_LAN_HOST_FRONT")
    lbg_pilot_static: str = Field(default="auto", validation_alias="LBG_PILOT_STATIC")

    def cors_origins_list(self) -> list[str]:
        raw = self.lbg_cors_origins.strip()
        if not raw:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]

    def orchestrator_base(self) -> str:
        return self.lbg_orchestrator_url.rstrip("/")

    def lbg_ia_backend_base_url(self) -> str | None:
        raw = (self.lbg_pilot_lbgia_backend_url.strip() or self.lbg_ia_backend_url.strip()).rstrip("/")
        return raw or None

    def pilot_agent_dialogue_invoke_timeout_s(self) -> float:
        raw = self.lbg_pilot_agent_dialogue_invoke_timeout.strip()
        try:
            return max(45.0, float(raw))
        except ValueError:
            return 300.0

    def pilot_lbg_ia_http_timeout_s(self) -> float:
        raw = self.lbg_pilot_lbgia_http_timeout.strip()
        try:
            return max(0.8, min(15.0, float(raw)))
        except ValueError:
            return 3.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
