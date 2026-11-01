"""Configure local Fuelio ZIP backups through the Home Assistant UI."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import CONF_FILE_PATH, DEFAULT_BACKUP_PATH, DOMAIN
from .parser import load_snapshot


class FuelioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One config entry per locally stored Fuelio backup ZIP."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Validate the ZIP and keep import paths inside HA's config folder."""
        errors: dict[str, str] = {}
        config_dir = Path(self.hass.config.config_dir).resolve()
        if user_input is not None:
            try:
                candidate = Path(user_input[CONF_FILE_PATH]).expanduser()
                if not candidate.is_absolute():
                    candidate = config_dir / candidate
                # Resolve symlinks to prevent escaping /config through a link.
                candidate = await self.hass.async_add_executor_job(candidate.resolve)
                if not candidate.is_relative_to(config_dir):
                    errors["base"] = "outside_config"
                else:
                    await self.hass.async_add_executor_job(load_snapshot, str(candidate))
                    await self.async_set_unique_id(str(candidate))
                    self._abort_if_unique_id_configured()
                    # Do not expose a registration/vehicle name in the entry title.
                    # Existing titles are intentionally not silently migrated.
                    return self.async_create_entry(
                        title="Fuelio vehicle",
                        data={CONF_FILE_PATH: str(candidate)},
                    )
            except (OSError, ValueError):
                errors["base"] = "invalid_backup"

        schema = vol.Schema({vol.Required(CONF_FILE_PATH, default=DEFAULT_BACKUP_PATH): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
