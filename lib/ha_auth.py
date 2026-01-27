"""
Shared Home Assistant authentication utilities.
Centralizes token management and request header setup.
"""
import os
import urllib.request
from typing import Optional


def get_ha_token(config: dict) -> Optional[str]:
    """
    Get HA token with supervisor token preferred, fallback to manual token.

    Args:
        config: Full config dict containing 'homeassistant' section

    Returns:
        Token string or None if not configured
    """
    ha_cfg = config.get('homeassistant') or {}
    use_supervisor = bool(ha_cfg.get('use_supervisor_token', True))

    if use_supervisor:
        sup = os.environ.get('SUPERVISOR_TOKEN')
        if sup:
            return sup

    token = ha_cfg.get('token')
    return token if isinstance(token, str) and token.strip() else None


def add_ha_auth_header(request: urllib.request.Request, config: dict) -> None:
    """
    Add Authorization header to urllib request using Bearer token.

    Args:
        request: urllib.request.Request object to modify
        config: Full config dict containing 'homeassistant' section

    Raises:
        ValueError: If no token is configured
    """
    token = get_ha_token(config)
    if not token:
        raise ValueError("Home Assistant token not configured")
    request.add_header('Authorization', f'Bearer {token}')
