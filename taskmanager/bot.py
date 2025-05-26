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
from aiogram.fsm.storage.memory import MemoryStorage

from taskmanager.config import Config
from taskmanager.database.models import Base, User
from taskmanager.database.connection import engine, async_session, init_db
from taskmanager.handlers import user, team, task
from taskmanager.middlewares.auth import AuthMiddleware
from taskmanager.middlewares.user import UserMiddleware
from taskmanager.languages.manager import language_manager
from taskmanager.notifications import init_notification_system
from taskmanager.services.transcription import init_transcription_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize notification system
notification_system = init_notification_system(bot)

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
    # Initialize database
    await init_db()
    
    # Start notification system
    await notification_system.start()
    
    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        # Stop notification system
        await notification_system.stop()

if __name__ == '__main__':
    asyncio.run(main()) 