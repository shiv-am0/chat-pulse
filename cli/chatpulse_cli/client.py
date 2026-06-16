import httpx
from .config import get_api_url
from .token_storage import load_tokens, save_tokens, clear_tokens


class ChatPulseError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class ChatPulseClient:
    def __init__(self):
        self.base_url = get_api_url().rstrip("/")
        self._client = httpx.Client(timeout=15)
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._current_user: dict | None = None
        self._load_from_storage()

    def _load_from_storage(self):
        tokens = load_tokens()
        if tokens:
            self._access_token = tokens["access"]
            self._refresh_token = tokens["refresh"]

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._access_token:
            h["Authorization"] = f"Bearer {self._access_token}"
        return h

    def _try_refresh(self) -> bool:
        if not self._refresh_token:
            return False
        try:
            r = self._client.post(
                f"{self.base_url}/auth/token/refresh/",
                json={"refresh": self._refresh_token},
            )
            if r.is_success:
                data = r.json()
                self._access_token = data["access"]
                save_tokens(self._access_token, self._refresh_token)
                return True
        except httpx.RequestError:
            pass
        clear_tokens()
        self._access_token = None
        self._refresh_token = None
        return False

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"
        for attempt in range(2):
            try:
                r = self._client.request(method, url, headers=self._headers(), **kwargs)
            except httpx.TransportError as e:
                raise ChatPulseError(str(e)) from e
            if r.status_code != 401 or not self._refresh_token:
                return r
            if attempt == 0 and self._try_refresh():
                continue
            break
        return r

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    # ── Auth ──────────────────────────────────────────────

    def register(self, username: str, email: str, password: str) -> dict:
        r = self._client.post(
            f"{self.base_url}/auth/register/",
            json={
                "username": username,
                "email": email,
                "password": password,
                "password2": password,
            },
        )
        return self._handle(r, 201)

    def login(self, username: str, password: str) -> dict:
        r = self._client.post(
            f"{self.base_url}/auth/login/",
            json={"username": username, "password": password},
        )
        data = self._handle(r, 200)
        self._access_token = data["access"]
        self._refresh_token = data["refresh"]
        self._current_user = data["user"]
        save_tokens(self._access_token, self._refresh_token)
        return data

    def logout(self, refresh_token: str | None = None) -> dict:
        token = refresh_token or self._refresh_token
        if token:
            r = self.post("/auth/logout/", json={"refresh": token})
        else:
            r = self.post("/auth/logout/", json={"refresh": ""})
        clear_tokens()
        self._access_token = None
        self._refresh_token = None
        self._current_user = None
        return self._handle(r, 200)

    def me(self) -> dict:
        r = self.get("/auth/me/")
        data = self._handle(r, 200)
        self._current_user = data
        return data

    def get_current_user(self) -> dict | None:
        return self._current_user

    # ── Rooms ─────────────────────────────────────────────

    def list_rooms(self) -> list:
        r = self.get("/rooms/")
        return self._handle(r, 200)

    def create_room(self, name: str) -> dict:
        r = self.post("/rooms/", json={"name": name})
        return self._handle(r, 201)

    def room_detail(self, room_id: int) -> dict:
        r = self.get(f"/rooms/{room_id}/")
        return self._handle(r, 200)

    def join_room(self, room_id: int) -> dict:
        r = self.post(f"/rooms/{room_id}/join/")
        return self._handle(r, 200)

    def leave_room(self, room_id: int) -> dict:
        r = self.post(f"/rooms/{room_id}/leave/")
        return self._handle(r, 200)

    # ── Messages ──────────────────────────────────────────

    def send_message(self, room_id: int, content: str) -> dict:
        r = self.post(
            "/messages/send/",
            json={"room_id": room_id, "content": content},
        )
        return self._handle(r, 202)

    def get_messages(
        self, room_id: int, limit: int = 50, before_id: int | None = None
    ) -> dict:
        params = {"room_id": str(room_id), "limit": str(limit)}
        if before_id is not None:
            params["before_id"] = str(before_id)
        r = self.get("/messages/", params=params)
        return self._handle(r, 200)

    # ── Helpers ───────────────────────────────────────────

    @staticmethod
    def _handle(r: httpx.Response, expected: int) -> dict | list:
        try:
            data = r.json()
        except Exception:
            data = {"error": "Invalid response from server"}
        if r.status_code == expected:
            return data
        msg = data.get("detail") or data.get("error") or data
        if isinstance(msg, dict):
            parts = []
            for k, v in msg.items():
                if isinstance(v, list):
                    parts.append(f"{k}: {'; '.join(str(x) for x in v)}")
                else:
                    parts.append(f"{k}: {v}")
            msg = " | ".join(parts)
        raise ChatPulseError(msg, status_code=r.status_code)


_client: ChatPulseClient | None = None


def get_client() -> ChatPulseClient:
    global _client
    if _client is None:
        _client = ChatPulseClient()
    return _client


def reset_client():
    global _client
    _client = None
