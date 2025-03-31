import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from database.models import Base
from database.connection import engine
from handlers import user, team, task
from middlewares.auth import AuthMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()

# Initialize notification system
task.init_notification_system(bot)

# Register middlewares
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

# Register routers
dp.include_router(user.router)
dp.include_router(team.router)
dp.include_router(task.router)

async def main():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start notification system
    if task.notification_system:
        await task.notification_system.start()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 