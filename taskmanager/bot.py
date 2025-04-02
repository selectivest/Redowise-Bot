import os
import sys
import asyncio
import logging

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from taskmanager.config import Config
from taskmanager.database.models import Base, User
from taskmanager.database.connection import engine, async_session
from taskmanager.handlers import user, team, task
from taskmanager.middlewares.auth import AuthMiddleware
from taskmanager.middlewares.user import UserMiddleware
from taskmanager.languages.manager import language_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()

# Initialize notification system
task.init_notification_system(bot)

# Register middlewares
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())
dp.message.middleware(UserMiddleware())
dp.callback_query.middleware(UserMiddleware())

# Register routers
dp.include_router(team.router)
dp.include_router(task.router)
dp.include_router(user.router)

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