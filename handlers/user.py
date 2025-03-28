from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, BotCommandScopeDefault, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from database.models import User, UserRole
from database.connection import async_session
from sqlalchemy import select

router = Router()

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Start the bot and register"),
        BotCommand(command="help", description="Show detailed help information"),
        BotCommand(command="menu", description="Show main menu"),
        BotCommand(command="show_keyboard", description="Show keyboard menu"),
        BotCommand(command="hide_keyboard", description="Hide keyboard menu"),
        BotCommand(command="create_team", description="Create a new team (Manager only)"),
        BotCommand(command="createteam", description="Create a new team (Manager only)"),
        BotCommand(command="add_member", description="Add member to team (Manager only)"),
        BotCommand(command="add_task", description="Create a new task"),
        BotCommand(command="tasks", description="View your tasks")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

def get_keyboard_menu(user: User = None) -> ReplyKeyboardMarkup:
    """Create keyboard menu based on user role"""
    buttons = [
        [KeyboardButton(text="📝 Tasks"), KeyboardButton(text="👥 Teams")],
        [KeyboardButton(text="❓ Help"), KeyboardButton(text="ℹ️ About")]
    ]
    
    # Add manager-specific buttons
    if user and user.role == UserRole.MANAGER:
        buttons.insert(0, [KeyboardButton(text="➕ Create Team"), KeyboardButton(text="👤 Add Member")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Select an option or type a command"
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

*Team Management:*
/create_team - Create a new team (Manager only)
/createteam - Create a new team (Manager only)
/add_member - Add a member to your team (Manager only)

*Task Management:*
/add_task - Create a new task
/tasks - View your tasks

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
2. Create a team using /create_team (Manager only)
3. Add team members using /add_member (Manager only)
4. Create tasks using /add_task
5. View tasks using /tasks

Need more help? Use /menu to access the main menu.
"""
    await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text == "📝 Tasks")
async def handle_tasks_button(message: Message, user: User):
    await message.answer(
        "📝 *Tasks Management*\n\n"
        "• /add_task - Create a new task\n"
        "• /tasks - View your tasks\n\n"
        "Tasks can be assigned to team members and tracked.",
        parse_mode="Markdown"
    )

@router.message(F.text == "👥 Teams")
async def handle_teams_button(message: Message, user: User):
    if user.role == UserRole.MANAGER:
        await message.answer(
            "👥 *Teams Management*\n\n"
            "• /create_team - Create a new team\n"
            "• /createteam - Create a new team\n"
            "• /add_member - Add member to team\n\n"
            "Use these commands to manage your teams.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👥 *Teams*\n\n"
            "You are a team member. Contact your team manager for team-related actions.",
            parse_mode="Markdown"
        )

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

@router.message(F.text == "➕ Create Team")
async def handle_create_team_button(message: Message, user: User):
    if user.role == UserRole.MANAGER:
        await message.answer(
            "To create a new team, use the /create_team command.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "Only managers can create teams.",
            parse_mode="Markdown"
        )

@router.message(F.text == "👤 Add Member")
async def handle_add_member_button(message: Message, user: User):
    if user.role == UserRole.MANAGER:
        await message.answer(
            "To add a member to your team, use the /add_member command.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "Only managers can add team members.",
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("menu_"))
async def process_menu_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    
    if action == "teams":
        await callback.message.answer(
            "👥 *Teams Management*\n\n"
            "• /create_team - Create a new team\n"
            "• /createteam - Create a new team\n"
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