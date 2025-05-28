from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, BotCommandScopeDefault, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from taskmanager.database.models import User, Team, TeamMember, Task, UserRole
from taskmanager.database.connection import async_session
from taskmanager.languages.manager import language_manager
from taskmanager.handlers.team import TeamStates
from taskmanager.handlers.task import process_task_description, TaskStates
from taskmanager.handlers.member_management import MemberManagementStates, start_member_management

router = Router()

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Start the bot and register"),
        BotCommand(command="help", description="Show detailed help information"),
        BotCommand(command="menu", description="Show main menu"),
        BotCommand(command="show_keyboard", description="Show keyboard menu"),
        BotCommand(command="hide_keyboard", description="Hide keyboard menu"),
        BotCommand(command="language", description="Change language")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

def get_keyboard_menu(user: User = None) -> ReplyKeyboardMarkup:
    """Create keyboard menu based on user role"""
    if not user:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Loading...")]],
            resize_keyboard=True
        )
    
    buttons = [
        [KeyboardButton(text=language_manager.get_text("add_task", user.language_code))],
        [KeyboardButton(text=language_manager.get_text("add_member", user.language_code))],
        [KeyboardButton(text=language_manager.get_text("member_management", user.language_code))],
        [KeyboardButton(text=language_manager.get_text("create_team", user.language_code))],
        [KeyboardButton(text=language_manager.get_text("view_tasks", user.language_code))],
        [KeyboardButton(text=language_manager.get_text("help", user.language_code))]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder=language_manager.get_text("select_option", user.language_code)
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Check if user exists
    async with async_session() as session:
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
                role=UserRole.MEMBER,
                language_code='en'  # Default language
            )
            session.add(user)
            await session.commit()
    
    # Show language selection menu
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=name,
                callback_data=f"set_language:{code}"
            )
        ]
        for code, name in language_manager.get_available_languages().items()
    ])
    
    await message.answer(
        language_manager.get_text("select_language", user.language_code),
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("set_language:"))
async def process_language_selection(callback: CallbackQuery):
    """Handle language selection callback."""
    lang_code = callback.data.split(":")[1]
    
    if not language_manager.is_valid_language(lang_code):
        await callback.answer("Invalid language selection")
        return
    
    # Update user's language preference
    async with async_session() as session:
        query = select(User).where(User.telegram_id == callback.from_user.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.language_code = lang_code
            await session.commit()
            
            # Set up commands menu
            await set_commands(callback.bot)
            
            # Show welcome message in selected language
            await callback.message.edit_text(
                language_manager.get_text("welcome", lang_code)
            )
            
            # Show keyboard menu with translated buttons
            keyboard = get_keyboard_menu(user)
            keyboard.keyboard = [
                [KeyboardButton(text=language_manager.get_text("add_task", lang_code))],
                [KeyboardButton(text=language_manager.get_text("add_member", lang_code))],
                [KeyboardButton(text=language_manager.get_text("member_management", lang_code))],
                [KeyboardButton(text=language_manager.get_text("create_team", lang_code))],
                [KeyboardButton(text=language_manager.get_text("view_tasks", lang_code))],
                [KeyboardButton(text=language_manager.get_text("help", lang_code))]
            ]
            
            await callback.message.answer(
                language_manager.get_text("main_menu", lang_code),
                reply_markup=keyboard
            )
        else:
            await callback.answer("Error: User not found")
    
    await callback.answer()

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
async def cmd_menu(message: Message, user: User):
    # Create keyboard with menu options
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=language_manager.get_text("create_team", user.language_code), callback_data="menu_teams")],
        [InlineKeyboardButton(text=language_manager.get_text("my_tasks", user.language_code), callback_data="menu_tasks")],
        [InlineKeyboardButton(text=language_manager.get_text("settings", user.language_code), callback_data="menu_settings")]
    ])
    
    await message.answer(
        language_manager.get_text("main_menu", user.language_code),
        reply_markup=keyboard
    )

@router.message(Command("help"))
async def cmd_help(message: Message, user: User):
    help_text = language_manager.get_text("help", user.language_code)
    await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text)
async def handle_menu_button(message: Message, state: FSMContext, user: User):
    try:
        print(f"Handling menu button for user {user.id} with language {user.language_code}")
        
        # Get current state
        current_state = await state.get_state()
        print(f"Current state: {current_state}")
        
        # Get user-specific text for menu options
        create_team_text = language_manager.get_text("create_team", user.language_code)
        add_member_text = language_manager.get_text("add_member", user.language_code)
        member_management_text = language_manager.get_text("member_management", user.language_code)
        add_task_text = language_manager.get_text("add_task", user.language_code)
        view_tasks_text = language_manager.get_text("view_tasks", user.language_code)
        
        print(f"Received text: {message.text}")
        print(f"Expected create team text: {create_team_text}")
        
        # If we're in a state, only allow task description input
        if current_state == "TaskStates:waiting_for_task_description":
            await process_task_description(message, state, user)
            return
        elif current_state:
            print(f"User is in state {current_state}, skipping menu button handling")
            return
        
        # Handle menu button clicks
        if message.text == create_team_text:
            await state.set_state(TeamStates.waiting_for_team_name)
            await message.answer(
                language_manager.get_text("team_name_prompt", user.language_code)
            )
        elif message.text == add_member_text:
            await state.set_state(TeamStates.waiting_for_member_username)
            await message.answer(
                language_manager.get_text("enter_username", user.language_code)
            )
        elif message.text == member_management_text:
            # Start member management process
            await start_member_management(message, state)
        elif message.text == add_task_text:
            async with async_session() as session:
                # Get user's teams (any role)
                query = select(Team).join(TeamMember).where(
                    TeamMember.user_id == user.id
                )
                result = await session.execute(query)
                teams = result.scalars().all()
                
                if not teams:
                    await message.answer(
                        language_manager.get_text("not_in_team", user.language_code)
                    )
                    return
                
                # Create inline keyboard for team selection
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=team.name, callback_data=f"team_{team.id}")]
                    for team in teams
                ])
                
                await state.set_state(TaskStates.waiting_for_team_selection)
                await message.answer(
                    language_manager.get_text("select_team", user.language_code),
                    reply_markup=keyboard
                )
        
        elif message.text == view_tasks_text:
            async with async_session() as session:
                # Get user's teams
                query = select(Team).join(TeamMember).where(TeamMember.user_id == user.id)
                result = await session.execute(query)
                teams = result.scalars().all()
                
                if not teams:
                    await message.answer(
                        language_manager.get_text("not_in_team", user.language_code)
                    )
                    return
                
                # Create inline keyboard for team selection
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=team.name, callback_data=f"view_tasks_{team.id}")]
                    for team in teams
                ])
                
                await message.answer(
                    language_manager.get_text("select_team_view", user.language_code),
                    reply_markup=keyboard
                )
    except Exception as e:
        print(f"Error handling menu button: {e}")  # For debugging
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Debug log
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
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

@router.callback_query(F.data.startswith("menu_"))
async def process_menu_callback(callback: CallbackQuery):
    try:
        # Get user from database to ensure we have the correct language code
        async with async_session() as session:
            query = select(User).where(User.telegram_id == callback.from_user.id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                await callback.message.answer(
                    language_manager.get_text("error_occurred", 'en')
                )
                return
                
            menu_type = callback.data.split('_')[1]
            
            if menu_type == "tasks":
                # Show tasks menu
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("view_tasks", user.language_code),
                            callback_data="view_tasks"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("add_task", user.language_code),
                            callback_data="add_task"
                        )
                    ]
                ])
                
                await callback.message.edit_text(
                    language_manager.get_text("tasks_menu", user.language_code),
                    reply_markup=keyboard
                )
            elif menu_type == "teams":
                # Show teams menu
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("view_teams", user.language_code),
                            callback_data="view_teams"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("create_team", user.language_code),
                            callback_data="create_team"
                        )
                    ]
                ])
                
                await callback.message.edit_text(
                    language_manager.get_text("teams_menu", user.language_code),
                    reply_markup=keyboard
                )
            elif menu_type == "settings":
                # Show settings menu
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("change_language", user.language_code),
                            callback_data="change_language"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("notification_settings", user.language_code),
                            callback_data="notification_settings"
                        )
                    ]
                ])
                
                await callback.message.edit_text(
                    language_manager.get_text("settings_menu", user.language_code),
                    reply_markup=keyboard
                )
            elif menu_type == "about":
                # Show about menu
                await callback.message.edit_text(
                    language_manager.get_text(
                        "about_bot",
                        user.language_code,
                        features=language_manager.get_text("bot_features", user.language_code)
                    ),
                    parse_mode="Markdown"
                )
            
            await callback.answer()
    except Exception as e:
        print(f"Error processing menu callback: {e}")  # For debugging
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await callback.answer() 