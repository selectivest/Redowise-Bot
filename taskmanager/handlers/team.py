from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from taskmanager.database.models import User, Team, TeamMember, UserRole, TeamMemberRole
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
                
                # Add creator as team member with Owner role
                team_member = TeamMember(
                    team_id=team.id,
                    user_id=user.id,
                    role=TeamMemberRole.OWNER
                )
                session.add(team_member)
                await session.commit()
                print(f"DEBUG: Created team member: user_id={team_member.user_id}, team_id={team_member.team_id}, role={team_member.role}")
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
    
    # Get user's teams where they are an Owner
    async with async_session() as session:
        query = select(Team).join(TeamMember).where(
            TeamMember.user_id == user.id,
            TeamMember.role == TeamMemberRole.OWNER
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
            
            # Get user's teams where they are an Owner
            query = select(Team).join(TeamMember).where(
                TeamMember.user_id == user.id,
                TeamMember.role == TeamMemberRole.OWNER
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
        print(f"Error processing member username: {e}")  # Debug log
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.callback_query(TeamStates.waiting_for_member_role)
async def process_team_selection(callback: CallbackQuery, state: FSMContext):
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
                
            team_id = int(callback.data.split('_')[1])
            data = await state.get_data()
            
            # Get team info
            team_query = select(Team).where(Team.id == team_id)
            team_result = await session.execute(team_query)
            team = team_result.scalar_one_or_none()
            
            if not team:
                await callback.message.answer(
                    language_manager.get_text("team_not_found", user.language_code)
                )
                return
            
            # Get member info using the stored new_member_id
            member_query = select(User).where(User.id == data['new_member_id'])
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            
            if not member:
                await callback.message.answer(
                    language_manager.get_text("user_not_found", user.language_code)
                )
                return

            # Check if user is already in the selected team
            membership_query = select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == member.id
            )
            membership_result = await session.execute(membership_query)
            existing_membership = membership_result.scalar_one_or_none()
            
            if existing_membership:
                await callback.message.answer(
                    language_manager.get_text(
                        "user_already_in_team",
                        user.language_code,
                        username=member.username,
                        team_name=team.name
                    )
                )
                await state.clear()
                await callback.answer()
                return
            
            # Create invitation
            invitation_id = str(uuid.uuid4())
            pending_invitations[invitation_id] = {
                'team_id': team_id,
                'team_name': team.name,
                'member_id': member.id,
                'member_username': member.username,
                'manager_id': user.id
            }
            
            try:
                # Create inline keyboard for invitation response
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=language_manager.get_text("accept", user.language_code),
                            callback_data=f"accept_{invitation_id}"
                        ),
                        InlineKeyboardButton(
                            text=language_manager.get_text("reject", user.language_code),
                            callback_data=f"decline_{invitation_id}"
                        )
                    ]
                ])
                
                # Send invitation to the member
                await callback.bot.send_message(
                    chat_id=member.telegram_id,
                    text=language_manager.get_text(
                        "team_invitation",
                        user.language_code,
                        team_name=team.name,
                        manager_username=user.username
                    ),
                    reply_markup=keyboard
                )
                
                # Notify the manager
                await callback.message.answer(
                    language_manager.get_text(
                        "invitation_sent",
                        user.language_code,
                        username=member.username
                    )
                )
            except Exception as e:
                print(f"Error sending invitation: {e}")  # For debugging
                await callback.message.answer(
                    language_manager.get_text(
                        "invitation_send_error",
                        user.language_code,
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
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.callback_query(F.data.startswith("accept_"))
async def process_invitation_accept(callback: CallbackQuery):
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
                
            invitation_id = callback.data.split('_')[1]
            
            if invitation_id not in pending_invitations:
                await callback.message.answer(
                    language_manager.get_text("invalid_invitation", user.language_code)
                )
                return
            
            invitation = pending_invitations[invitation_id]
            
            # Get manager info for notification
            manager_query = select(User).where(User.id == invitation['manager_id'])
            manager_result = await session.execute(manager_query)
            manager = manager_result.scalar_one_or_none()
            
            if not manager:
                await callback.message.answer(
                    language_manager.get_text("error_occurred", user.language_code)
                )
                return
            
            # Add member to team
            team_member = TeamMember(
                team_id=invitation['team_id'],
                user_id=invitation['member_id'],
                role=TeamMemberRole.MEMBER
            )
            session.add(team_member)
            await session.commit()
            
            # Notify member
            await callback.message.edit_text(
                language_manager.get_text(
                    "team_joined",
                    user.language_code,
                    team_name=invitation['team_name'],
                    manager_username=manager.username
                )
            )
            
            try:
                # Notify manager
                await callback.bot.send_message(
                    chat_id=manager.telegram_id,
                    text=language_manager.get_text(
                        "member_accepted",
                        manager.language_code,  # Use manager's language preference
                        username=user.username,
                        team_name=invitation['team_name']
                    )
                )
            except Exception as e:
                print(f"Error sending notification to manager: {e}")
        
        # Remove the invitation
        del pending_invitations[invitation_id]
        await callback.answer()
    except Exception as e:
        print(f"Error processing invitation acceptance: {e}")  # Debug log
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await callback.answer()

@router.callback_query(F.data.startswith("decline_"))
async def process_invitation_reject(callback: CallbackQuery):
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
                
            invitation_id = callback.data.split('_')[1]
            
            if invitation_id not in pending_invitations:
                await callback.message.answer(
                    language_manager.get_text("invalid_invitation", user.language_code)
                )
                return
            
            invitation = pending_invitations[invitation_id]
            
            # Notify member
            await callback.message.edit_text(
                language_manager.get_text(
                    "invitation_declined",
                    user.language_code,
                    team_name=invitation['team_name']
                )
            )
            
            try:
                # Get manager info for notification
                manager_query = select(User).where(User.id == invitation['manager_id'])
                manager_result = await session.execute(manager_query)
                manager = manager_result.scalar_one_or_none()
                
                if manager:
                    # Notify manager
                    await callback.bot.send_message(
                        chat_id=manager.telegram_id,
                        text=language_manager.get_text(
                            "member_declined",
                            manager.language_code,  # Use manager's language preference
                            username=invitation['member_username'],
                            team_name=invitation['team_name']
                        )
                    )
            except Exception as e:
                print(f"Error sending notification to manager: {e}")
                # Log the error but continue with the process
                pass
        
        # Remove the invitation
        del pending_invitations[invitation_id]
        await callback.answer()
    except Exception as e:
        print(f"Error processing invitation rejection: {e}")  # Debug log
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await callback.answer() 