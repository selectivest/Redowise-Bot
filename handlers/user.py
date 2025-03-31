from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, BotCommandScopeDefault, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.models import User, UserRole, Team, TeamMember
from database.connection import async_session
from sqlalchemy import select
from handlers.team import TeamStates
from handlers.task import TaskStates

router = Router()

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Start the bot and register"),
        BotCommand(command="help", description="Show detailed help information"),
        BotCommand(command="menu", description="Show main menu"),
        BotCommand(command="show_keyboard", description="Show keyboard menu"),
        BotCommand(command="hide_keyboard", description="Hide keyboard menu")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

def get_keyboard_menu(user: User = None) -> ReplyKeyboardMarkup:
    """Create keyboard menu based on user role"""
    buttons = [
        [KeyboardButton(text="📝 Add Task"), KeyboardButton(text="👥 Add Member")],
        [KeyboardButton(text="➕ Create Team"), KeyboardButton(text="📋 Tasks")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Select an option"
    )

@router.message(Command("start"))
async def cmd_start(message: Message, bot):
    async with async_session() as session:
        # Check if user already exists
        query = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                role=UserRole.MEMBER
            )
            session.add(user)
            await session.commit()
            
            # Set up commands menu
            await set_commands(bot)
            
            await message.answer(
                "👋 Welcome to Task Manager Bot!\n\n"
                "I'm here to help you manage your tasks and teams efficiently.\n\n"
                "Here's what you can do:\n"
                "1️⃣ Create and manage teams\n"
                "2️⃣ Assign and track tasks\n"
                "3️⃣ Collaborate with team members\n\n"
                "Use /menu to see the main menu or /help for detailed instructions.\n"
                "Use /show_keyboard to show the keyboard menu.",
                reply_markup=get_keyboard_menu(user)
            )
        else:
            await message.answer(
                "👋 Welcome back!\n\n"
                "Use /menu to see the main menu or /help for detailed instructions.\n"
                "Use /show_keyboard to show the keyboard menu.",
                reply_markup=get_keyboard_menu(user)
            )

@router.message(Command("show_keyboard"))
async def cmd_show_keyboard(message: Message, user: User):
    await message.answer(
        "Keyboard menu is now visible. Use /hide_keyboard to hide it.",
        reply_markup=get_keyboard_menu(user)
    )

@router.message(Command("hide_keyboard"))
async def cmd_hide_keyboard(message: Message):
    await message.answer(
        "Keyboard menu is now hidden. Use /show_keyboard to show it again.",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Teams", callback_data="menu_teams"),
            InlineKeyboardButton(text="📝 Tasks", callback_data="menu_tasks")
        ],
        [
            InlineKeyboardButton(text="❓ Help", callback_data="menu_help"),
            InlineKeyboardButton(text="ℹ️ About", callback_data="menu_about")
        ]
    ])
    
    await message.answer(
        "🎯 Main Menu\n\n"
        "Select an option below:",
        reply_markup=keyboard
    )

@router.message(Command("help"))
async def cmd_help(message: Message, user: User):
    help_text = """
🤖 *Task Manager Bot Help*

*Basic Commands:*
/start - Start the bot and register
/menu - Show main menu
/help - Show this help message
/show_keyboard - Show keyboard menu
/hide_keyboard - Hide keyboard menu

*User Roles:*
👨‍💼 *Manager*
• Can create and manage teams
• Can add members to teams
• Can assign tasks to any team member
• Can view all tasks in their teams

👥 *Member*
• Can create tasks for themselves
• Can view their assigned tasks
• Can be added to teams by managers

*How to Use:*
1. Start with /start to register
2. Use the keyboard menu to:
   • Create a team
   • Add team members
   • Create tasks
   • View tasks

Need more help? Use /menu to access the main menu.
"""
    await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text == "📝 Add Task")
async def handle_add_task_button(message: Message, state: FSMContext, user: User):
    # Get user's teams
    async with async_session() as session:
        query = select(Team).join(TeamMember).where(TeamMember.user_id == user.id)
        result = await session.execute(query)
        teams = result.scalars().all()
        
        if not teams:
            await message.answer("You need to be a member of a team to add tasks. Create or join a team first.")
            return
    
    # Create inline keyboard for team selection
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=team.name, callback_data=f"team_{team.id}")]
        for team in teams
    ])
    
    await state.set_state(TaskStates.waiting_for_team_selection)
    await message.answer("Select the team to add the task to:", reply_markup=keyboard)

@router.message(F.text == "👥 Add Member")
async def handle_add_member_button(message: Message, state: FSMContext, user: User):
    # Get user's teams where they are a manager
    async with async_session() as session:
        query = select(Team).join(TeamMember).where(
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        teams = result.scalars().all()
        
        if not teams:
            await message.answer("You need to be a manager of a team to add members. Create a team first.")
            return
    
    await state.set_state(TeamStates.waiting_for_member_username)
    await message.answer("Please enter the Telegram username of the new member:")

@router.message(F.text == "➕ Create Team")
async def handle_create_team_button(message: Message, state: FSMContext, user: User):
    await state.set_state(TeamStates.waiting_for_team_name)
    await message.answer("Please enter the name for your new team:")

@router.message(F.text == "📋 Tasks")
async def handle_tasks_button(message: Message, user: User):
    async with async_session() as session:
        # Get user's teams
        query = select(Team).join(TeamMember).where(TeamMember.user_id == user.id)
        result = await session.execute(query)
        teams = result.scalars().all()
        
        if not teams:
            await message.answer("You need to be a member of a team first.")
            return
        
        # Create inline keyboard for team selection
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=team.name, callback_data=f"view_tasks_{team.id}")]
            for team in teams
        ])
        
        await message.answer("Select a team to view tasks:", reply_markup=keyboard)

@router.message(F.text == "❓ Help")
async def handle_help_button(message: Message, user: User):
    await cmd_help(message, user)

@router.message(F.text == "ℹ️ About")
async def handle_about_button(message: Message):
    await message.answer(
        "ℹ️ *About Task Manager Bot*\n\n"
        "A powerful tool for managing tasks and teams in Telegram.\n\n"
        "Features:\n"
        "• Team management\n"
        "• Task assignment\n"
        "• Progress tracking\n"
        "• Role-based access\n\n"
        "Use /help for detailed instructions.",
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("menu_"))
async def process_menu_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    
    if action == "teams":
        await callback.message.answer(
            "👥 *Teams Management*\n\n"
            "• /create_team - Create a new team\n"
            "• /add_member - Add member to team\n\n"
            "Note: Team management features are available for managers only.",
            parse_mode="Markdown"
        )
    elif action == "tasks":
        await callback.message.answer(
            "📝 *Tasks Management*\n\n"
            "• /add_task - Create a new task\n"
            "• /tasks - View your tasks\n\n"
            "Tasks can be assigned to team members and tracked.",
            parse_mode="Markdown"
        )
    elif action == "help":
        # Get user from database
        async with async_session() as session:
            query = select(User).where(User.telegram_id == callback.from_user.id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if user:
                await cmd_help(callback.message, user)
    elif action == "about":
        await callback.message.answer(
            "ℹ️ *About Task Manager Bot*\n\n"
            "A powerful tool for managing tasks and teams in Telegram.\n\n"
            "Features:\n"
            "• Team management\n"
            "• Task assignment\n"
            "• Progress tracking\n"
            "• Role-based access\n\n"
            "Use /help for detailed instructions.",
            parse_mode="Markdown"
        )
    
    await callback.answer() 