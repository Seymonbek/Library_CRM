"""
Auth Middleware — har bir xabarda foydalanuvchini tekshiradi.

Yangi flow (parolsiz):
1. FSM storage'dan token olinadi
2. Agar token bor → API'ga /users/me/ so'rov (valid-mi?)
3. Agar token eskirgan → refresh token bilan yangilanadi
4. Agar hech narsa yo'q → telegram_id orqali login urinadi
5. Agar user topilmasa → api_client=None (handler registratsiya boshlaydi)
"""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.api_client import APIClient


class AuthMiddleware(BaseMiddleware):
    """
    Har bir update uchun:
    - Tokenni tekshiradi va APIClient yaratadi
    - Token eskirgan bo'lsa refresh qiladi
    - Hech narsa bo'lmasa telegram_id orqali auto-login urinadi
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext | None = data.get("state")
        api_client = None

        # Telegram user ID olish
        tg_user = None
        if isinstance(event, Message) and event.from_user:
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_user = event.from_user

        if state:
            state_data = await state.get_data()
            access_token = state_data.get("access_token")
            refresh_token = state_data.get("refresh_token")

            if access_token:
                api_client = APIClient(token=access_token)

                # Token ishlashini tekshirish
                _, status_code = await api_client.get_me()

                if status_code == 401 and refresh_token:
                    # Access token eskirgan — refresh
                    new_tokens, refresh_status = await APIClient().refresh_token(refresh_token)

                    if refresh_status == 200:
                        access_token = new_tokens["access"]
                        await state.update_data(
                            access_token=access_token,
                            refresh_token=new_tokens.get("refresh", refresh_token),
                        )
                        api_client = APIClient(token=access_token)
                    else:
                        # Refresh ham eskirgan — qayta login
                        api_client = None
                        await state.update_data(access_token=None, refresh_token=None)

                elif status_code == 401:
                    api_client = None
                    await state.update_data(access_token=None, refresh_token=None)

            # Agar token yo'q — telegram_id orqali auto-login
            if api_client is None and tg_user:
                client = APIClient()
                response, login_status = await client.telegram_login(telegram_id=tg_user.id)

                if login_status == 200:
                    access_token = response.get("access")
                    refresh_token = response.get("refresh")
                    await state.update_data(
                        access_token=access_token,
                        refresh_token=refresh_token,
                    )
                    api_client = APIClient(token=access_token)

        data["api_client"] = api_client
        return await handler(event, data)
