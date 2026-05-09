import aiohttp
from bot.config import API_BASE_URL


class APIClient:
    """Django API bilan ishlash uchun helper"""

    def __init__(self, token: str = None):
        self.base_url = API_BASE_URL
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def get(self, endpoint: str, params: dict = None):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(f"{self.base_url}{endpoint}", params=params) as resp:
                return await resp.json(), resp.status

    async def post(self, endpoint: str, data: dict):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.base_url}{endpoint}", json=data) as resp:
                return await resp.json(), resp.status
