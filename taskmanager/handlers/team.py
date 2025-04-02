from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from taskmanager.database.models import User, Team, TeamMember, UserRole
from taskmanager.database.connection import async_session
from taskmanager.languages.manager import language_manager
import uuid

router = Router()

class TeamStates(StatesGroup):
    waiting_for_team_name = State()
    waiting_for_member_username = State()
    waiting_for_member_role = State()

# Store pending invitations
pending_invitations = {}

@router.message(Command("create_team"))
async def cmd_create_team(message: Message, state: FSMContext, user: User):
    try:
        await state.clear()  # Clear any existing state
        await state.set_state(TeamStates.waiting_for_team_name)
        await message.answer(
            language_manager.get_text("team_name_prompt", user.language_code)
        )
    except Exception as e:
        print(f"Error in create_team command: {e}")  # For debugging
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.message(TeamStates.waiting_for_team_name)
async def process_team_name(message: Message, state: FSMContext, user: User):
    try:
        print(f"Processing team name for user {user.id} with language {user.language_code}")  # Debug log
        team_name = message.text.strip()
        print(f"Received team name: {team_name}")  # Debug log
        
        if not team_name:
            print("Empty team name received")  # Debug log
            await message.answer(
                language_manager.get_text("invalid_team_name", user.language_code)
            )
            return

        async with async_session() as session:
            print("Starting database transaction")  # Debug log
            try:
                print("Checking for existing team")  # Debug log
                # Check if team name already exists
                query = select(Team).where(Team.name == team_name)
                result = await session.execute(query)
                existing_team = result.scalar_one_or_none()
                
                if existing_team:
                    print(f"Team with name {team_name} already exists")  # Debug log
                    await message.answer(
                        language_manager.get_text("team_name_exists", user.language_code)
                    )
                    return

                print("Creating new team")  # Debug log
                # Create new team
                team = Team(name=team_name)
                session.add(team)
                await session.flush()  # Flush to get the team ID
                print(f"Team created with ID: {team.id}")  # Debug log
                
                # Add creator as team member with Manager role
                team_member = TeamMember(
                    team_id=team.id,
                    user_id=user.id,
                    role="Manager"
                )
                session.add(team_member)
                await session.commit()
                print("Team member added and transaction committed")  # Debug log
            except Exception as db_error:
                print(f"Database error: {db_error}")  # Debug log
                await session.rollback()
                raise
        
        print("Clearing state")  # Debug log
        await state.clear()
        print("Sending success message")
        await message.answer(
            language_manager.get_text("team_created", user.language_code)
        )
        
        # Show keyboard menu after team creation
        print("Showing keyboard menu")  # Debug log
        from handlers.user import get_keyboard_menu
        await message.answer(
            language_manager.get_text("main_menu", user.language_code),
            reply_markup=get_keyboard_menu(user)
        )
    except Exception as e:
        print(f"Error creating team: {e}")  # For debugging
        print(f"Error type: {type(e)}")  # Debug log
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Debug log
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.message(Command("add_member"))
async def cmd_add_member(message: Message, state: FSMContext, user: User):
    await state.clear()  # Clear any existing state
    
    # Get user's teams where they are a manager
    async with async_session() as session:
        query = select(Team).join(TeamMember).where(
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        teams = result.scalars().all()
        
        if not teams:
            await message.answer(
                language_manager.get_text("not_authorized", user.language_code)
            )
            return
    
    await state.set_state(TeamStates.waiting_for_member_username)
    await message.answer(
        language_manager.get_text("member_username_prompt", user.language_code)
    )

@router.message(TeamStates.waiting_for_member_username)
async def process_member_username(message: Message, state: FSMContext, user: User):
    try:
        username = message.text.strip('@')
        if not username:
            await message.answer(
                language_manager.get_text("invalid_username", user.language_code)
            )
            return
        
        async with async_session() as session:
            # Check if user exists
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            new_member = result.scalar_one_or_none()
            
            if not new_member:
                await message.answer(
                    language_manager.get_text("user_not_found", user.language_code)
                )
                await state.clear()
                return
            
            # Get user's teams where they are a manager
            query = select(Team).join(TeamMember).where(
                TeamMember.user_id == user.id,
                TeamMember.role == "Manager"
            )
            result = await session.execute(query)
            teams = result.scalars().all()
            
            if not teams:
                await message.answer(
                    language_manager.get_text("not_authorized", user.language_code)
                )
                await state.clear()
                return
            
            # Store data for next step
            await state.update_data(
                new_member_id=new_member.id,
                teams=teams
            )
            
            # Create inline keyboard for team selection
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=team.name, callback_data=f"team_{team.id}")]
                for team in teams
            ])
            
            await state.set_state(TeamStates.waiting_for_member_role)
            await message.answer(
                language_manager.get_text("select_team", user.language_code),
                reply_markup=keyboard
            )
    except Exception as e:
        print(f"Error processing member username: {e}")  # For debugging
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.callback_query(TeamStates.waiting_for_member_role)
async def process_team_selection(callback: CallbackQuery, state: FSMContext):
    try:
        team_id = int(callback.data.split('_')[1])
        data = await state.get_data()
        
        async with async_session() as session:
            # Get team and member info
            team_query = select(Team).where(Team.id == team_id)
            team_result = await session.execute(team_query)
            team = team_result.scalar_one_or_none()
            
            member_query = select(User).where(User.id == data['new_member_id'])
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not team or not member:
                await callback.message.answer(
                    language_manager.get_text("error_occurred", callback.from_user.language_code)
                )
                await state.clear()
                return
            
            # Check if member has started the bot
            if not member.telegram_id:
                await callback.message.answer(
                    language_manager.get_text(
                        "user_not_started_bot",
                        callback.from_user.language_code,
                        username=member.username
                    )
                )
                await state.clear()
                return
            
            # Generate unique invitation ID
            invitation_id = str(uuid.uuid4())
            
            # Store invitation data
            pending_invitations[invitation_id] = {
                'team_id': team_id,
                'team_name': team.name,
                'member_id': member.id,
                'member_username': member.username,
                'member_telegram_id': member.telegram_id,
                'manager_id': callback.from_user.id,
                'manager_username': callback.from_user.username
            }
            
            # Create invitation message with accept/reject buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=language_manager.get_text("accept", member.language_code),
                        callback_data=f"accept_invite_{invitation_id}"
                    ),
                    InlineKeyboardButton(
                        text=language_manager.get_text("reject", member.language_code),
                        callback_data=f"reject_invite_{invitation_id}"
                    )
                ]
            ])
            
            try:
                # Send invitation to the member
                await callback.bot.send_message(
                    chat_id=member.telegram_id,
                    text=language_manager.get_text(
                        "team_invitation",
                        member.language_code,
                        team_name=team.name,
                        manager_username=callback.from_user.username
                    ),
                    reply_markup=keyboard
                )
                
                # Notify the manager
                await callback.message.answer(
                    language_manager.get_text(
                        "invitation_sent",
                        callback.from_user.language_code,
                        username=member.username
                    )
                )
            except Exception as e:
                print(f"Error sending invitation: {e}")  # For debugging
                await callback.message.answer(
                    language_manager.get_text(
                        "invitation_send_error",
                        callback.from_user.language_code,
                        username=member.username
                    )
                )
                # Remove the invitation since we couldn't send it
                del pending_invitations[invitation_id]
            
            await state.clear()
            await callback.answer()
    except Exception as e:
        print(f"Error processing team selection: {e}")  # For debugging
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.callback_query(F.data.startswith("accept_invite_"))
async def process_invitation_accept(callback: CallbackQuery):
    try:
        invitation_id = callback.data.split('_')[2]
        
        if invitation_id not in pending_invitations:
            await callback.message.answer(
                language_manager.get_text("invalid_invitation", callback.from_user.language_code)
            )
            return
        
        invitation = pending_invitations[invitation_id]
        
        async with async_session() as session:
            # Add member to team
            team_member = TeamMember(
                team_id=invitation['team_id'],
                user_id=invitation['member_id'],
                role="Member"
            )
            session.add(team_member)
            await session.commit()
            
            # Notify member
            await callback.message.edit_text(
                language_manager.get_text(
                    "team_joined",
                    callback.from_user.language_code,
                    team_name=invitation['team_name'],
                    manager_username=invitation['manager_username']
                )
            )
            
            try:
                # Notify manager
                await callback.bot.send_message(
                    chat_id=invitation['manager_id'],
                    text=language_manager.get_text(
                        "member_accepted",
                        callback.from_user.language_code,
                        username=invitation['member_username'],
                        team_name=invitation['team_name']
                    )
                )
            except Exception as e:
                print(f"Error sending notification to manager: {e}")
        
        # Remove the invitation
        del pending_invitations[invitation_id]
        await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code)
        )
        await callback.answer()

@router.callback_query(F.data.startswith("reject_invite_"))
async def process_invitation_reject(callback: CallbackQuery):
    try:
        invitation_id = callback.data.split('_')[2]
        
        if invitation_id not in pending_invitations:
            await callback.message.answer(
                language_manager.get_text("invalid_invitation", callback.from_user.language_code)
            )
            return
        
        invitation = pending_invitations[invitation_id]
        
        # Notify member
        await callback.message.edit_text(
            language_manager.get_text(
                "invitation_declined",
                callback.from_user.language_code,
                team_name=invitation['team_name']
            )
        )
        
        try:
            # Notify manager
            await callback.bot.send_message(
                chat_id=invitation['manager_id'],
                text=language_manager.get_text(
                    "member_declined",
                    callback.from_user.language_code,
                    username=invitation['member_username'],
                    team_name=invitation['team_name']
                )
            )
        except Exception as e:
            print(f"Error sending notification to manager: {e}")
        
        # Remove the invitation
        del pending_invitations[invitation_id]
        await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code)
        )
        await callback.answer() 