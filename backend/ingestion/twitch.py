"""Read-only Twitch Helix metadata for a selected live channel.

This adapter resolves Twitch's declared stream category. It does not access the
stream media, infer the game from audio, or treat category metadata as an
independent quality claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import time
from typing import Literal
import asyncio

import httpx

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_STREAMS_URL = "https://api.twitch.tv/helix/streams"
TWITCH_LOGIN = re.compile(r"^[a-z0-9_]{1,25}$", re.IGNORECASE)


@dataclass(frozen=True)
class TwitchLiveStreamResult:
    """Nullable, timestamped lookup result for one requested channel."""

    status: Literal["live", "offline", "unavailable"]
    channel_login: str
    game_id: str | None
    game_name: str | None
    observed_at: datetime
    reason: str | None
    source: Literal["twitch_helix"] = "twitch_helix"

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "channel_login": self.channel_login,
            "game_id": self.game_id,
            "game_name": self.game_name,
            "observed_at": self.observed_at.isoformat().replace("+00:00", "Z"),
            "reason": self.reason,
            "source": self.source,
        }


class TwitchHelixClient:
    """Resolve live channel category through Twitch's app-token Helix API.

    The supplied `httpx.AsyncClient` is owned and closed by the caller. An app
    access token is cached only in this adapter's memory until shortly before
    expiry. Client credentials and tokens never appear in returned values.
    """

    def __init__(self, client: httpx.AsyncClient, *, client_id: str | None,
                 client_secret: str | None):
        self.client = client
        self.client_id = client_id.strip() if client_id else None
        self.client_secret = client_secret.strip() if client_secret else None
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    @staticmethod
    def _result(status: Literal["live", "offline", "unavailable"],
                channel_login: str, *, game_id: str | None = None,
                game_name: str | None = None, reason: str | None = None) -> TwitchLiveStreamResult:
        return TwitchLiveStreamResult(
            status=status, channel_login=channel_login, game_id=game_id,
            game_name=game_name, observed_at=datetime.now(timezone.utc),
            reason=reason,
        )

    async def _app_token(self) -> tuple[str | None, str | None]:
        if not self.client_id or not self.client_secret:
            return None, "Twitch Helix metadata is unavailable: configure TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET."
        async with self._token_lock:
            if self._access_token and time.monotonic() < self._token_expires_at:
                return self._access_token, None
            self._access_token = None
            self._token_expires_at = 0.0
            try:
                response = await self.client.post(
                    TWITCH_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "client_credentials",
                    },
                )
            except httpx.HTTPError:
                return None, "Twitch app-token request failed; channel metadata is unavailable."
            if response.status_code != 200:
                return None, f"Twitch app-token request returned HTTP {response.status_code}; channel metadata is unavailable."
            try:
                body = response.json()
                token = body.get("access_token")
                expires_in = body.get("expires_in")
                if not isinstance(token, str) or not token or not isinstance(expires_in, (int, float)):
                    raise ValueError("invalid token response")
            except (ValueError, TypeError, AttributeError):
                return None, "Twitch app-token response was invalid; channel metadata is unavailable."
            self._access_token = token
            self._token_expires_at = time.monotonic() + max(0.0, float(expires_in) - 60.0)
            return token, None

    async def get_live_stream(self, channel_login: str) -> TwitchLiveStreamResult:
        """Return live/offline/unavailable and nullable declared game metadata."""
        normalized = channel_login.strip().lstrip("@").lower() if isinstance(channel_login, str) else ""
        if not TWITCH_LOGIN.fullmatch(normalized):
            return self._result("unavailable", normalized,
                                reason="Twitch channel login must be 1–25 letters, numbers, or underscores.")

        token, reason = await self._app_token()
        if token is None:
            return self._result("unavailable", normalized, reason=reason)

        for attempt in range(2):
            try:
                response = await self.client.get(
                    TWITCH_STREAMS_URL,
                    params={"user_login": normalized, "first": 1},
                    headers={"Client-Id": self.client_id or "", "Authorization": f"Bearer {token}"},
                )
            except httpx.HTTPError:
                return self._result("unavailable", normalized,
                                    reason="Twitch stream lookup failed; game metadata is unavailable.")
            if response.status_code == 401 and attempt == 0:
                # Refresh one expired/invalid app token. No response body or
                # credential is included in the returned status.
                self._access_token = None
                self._token_expires_at = 0.0
                token, reason = await self._app_token()
                if token is None:
                    return self._result("unavailable", normalized, reason=reason)
                continue
            if response.status_code != 200:
                return self._result(
                    "unavailable", normalized,
                    reason=f"Twitch stream lookup returned HTTP {response.status_code}; game metadata is unavailable.",
                )
            try:
                body = response.json()
                streams = body.get("data")
                if not isinstance(streams, list):
                    raise ValueError("missing stream list")
            except (ValueError, TypeError, AttributeError):
                return self._result("unavailable", normalized,
                                    reason="Twitch stream response was invalid; game metadata is unavailable.")

            if not streams:
                return self._result("offline", normalized,
                                    reason="Twitch did not report this channel as live.")
            stream = streams[0]
            if not isinstance(stream, dict) or str(stream.get("user_login", "")).casefold() != normalized:
                return self._result("unavailable", normalized,
                                    reason="Twitch returned an unexpected channel; game metadata is unavailable.")
            raw_game_id, raw_game_name = stream.get("game_id"), stream.get("game_name")
            game_id = raw_game_id.strip() if isinstance(raw_game_id, str) and raw_game_id.strip() else None
            game_name = raw_game_name.strip() if isinstance(raw_game_name, str) and raw_game_name.strip() else None
            if game_id is None or game_name is None:
                return self._result("live", normalized, game_id=game_id, game_name=game_name,
                                    reason="Channel is live, but Twitch has no complete game category for this stream.")
            return self._result("live", normalized, game_id=game_id, game_name=game_name)

        return self._result("unavailable", normalized,
                            reason="Twitch stream lookup could not refresh its app token.")
