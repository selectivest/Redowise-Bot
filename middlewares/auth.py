from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.models import User
from database.connection import async_session
from sqlalchemy import select

class AuthMiddleware(BaseMiddleware):
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
            
            # If user doesn't exist and it's not a /start command, ignore the message
            if not user and isinstance(event, Message) and not event.text.startswith('/start'):
                return
            
            # Add user to data
            data['user'] = user
        
        return await handler(event, data) 