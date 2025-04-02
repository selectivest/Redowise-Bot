from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from taskmanager.database.connection import async_session
from taskmanager.database.models import User
from sqlalchemy import select

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get user from database
        async with async_session() as session:
            query = select(User).where(User.telegram_id == event.from_user.id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            # Add user to data dict
            data["user"] = user
            
            # Call next handler
            return await handler(event, data) 