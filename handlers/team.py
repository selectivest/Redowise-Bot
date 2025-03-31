from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import User, Team, TeamMember
from database.connection import async_session
from sqlalchemy import select
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
    await state.set_state(TeamStates.waiting_for_team_name)
    await message.answer("Please enter the name for your new team:")

@router.message(TeamStates.waiting_for_team_name)
async def process_team_name(message: Message, state: FSMContext, user: User):
    async with async_session() as session:
        team = Team(name=message.text)
        session.add(team)
        await session.commit()
        
        # Add creator as team member with Manager role
        team_member = TeamMember(
            team_id=team.id,
            user_id=user.id,
            role="Manager"
        )
        session.add(team_member)
        await session.commit()
    
    await state.clear()
    await message.answer(f"Team '{message.text}' has been created successfully! You are now the manager of this team.")

@router.message(Command("add_member"))
async def cmd_add_member(message: Message, state: FSMContext, user: User):
    # Get user's teams where they are a manager
    async with async_session() as session:
        query = select(Team).join(TeamMember).where(
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        teams = result.scalars().all()
        
        if not teams:
            await message.answer("You need to be a manager of a team to add members. Create a team first using /create_team")
            return
    
    await state.set_state(TeamStates.waiting_for_member_username)
    await message.answer("Please enter the Telegram username of the new member:")

@router.message(TeamStates.waiting_for_member_username)
async def process_member_username(message: Message, state: FSMContext, user: User):
    username = message.text.strip('@')
    
    async with async_session() as session:
        # Check if user exists
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        new_member = result.scalar_one_or_none()
        
        if not new_member:
            await message.answer("User not found. Please make sure they have registered with the bot first.")
            await state.clear()
            return
        
        # Get user's teams where they are a manager
        query = select(Team).join(TeamMember).where(
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        teams = result.scalars().all()
        
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
        await message.answer("Select the team to add the member to:", reply_markup=keyboard)

@router.callback_query(TeamStates.waiting_for_member_role)
async def process_team_selection(callback: CallbackQuery, state: FSMContext):
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
            await callback.message.answer("Error: Team or member not found.")
            await state.clear()
            return
        
        # Check if member has started the bot
        if not member.telegram_id:
            await callback.message.answer(
                f"Error: @{member.username} hasn't started the bot yet. "
                "Please ask them to start the bot using /start command first."
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
            'manager_id': callback.from_user.id,  # Store the manager's user ID
            'manager_username': callback.from_user.username
        }
        
        # Create invitation message with accept/reject buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Accept", callback_data=f"accept_invite_{invitation_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_invite_{invitation_id}")
            ]
        ])
        
        try:
            # Send invitation to the member
            await callback.bot.send_message(
                chat_id=member.telegram_id,
                text=f"👋 You have been invited to join team '{team.name}'!\n\n"
                     f"Manager: @{callback.from_user.username}\n\n"
                     f"Would you like to accept the invitation?",
                reply_markup=keyboard
            )
            
            # Notify the manager
            await callback.message.answer(f"Invitation sent to @{member.username}")
        except Exception as e:
            await callback.message.answer(
                f"Error: Could not send invitation to @{member.username}. "
                "Please make sure they have started the bot and try again."
            )
            # Remove the invitation since we couldn't send it
            del pending_invitations[invitation_id]
        
        await state.clear()
        await callback.answer()

@router.callback_query(F.data.startswith("accept_invite_"))
async def process_invitation_accept(callback: CallbackQuery):
    invitation_id = callback.data.split('_')[2]
    
    if invitation_id not in pending_invitations:
        await callback.message.answer("Invalid or expired invitation.")
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
            f"✅ You have joined team '{invitation['team_name']}'!\n\n"
            f"Manager: @{invitation['manager_username']}"
        )
        
        try:
            # Notify manager
            await callback.bot.send_message(
                chat_id=invitation['manager_id'],
                text=f"✅ @{invitation['member_username']} has accepted your invitation to join team '{invitation['team_name']}'!"
            )
        except Exception as e:
            print(f"Error sending notification to manager: {e}")
    
    # Remove the invitation
    del pending_invitations[invitation_id]
    await callback.answer()

@router.callback_query(F.data.startswith("reject_invite_"))
async def process_invitation_reject(callback: CallbackQuery):
    invitation_id = callback.data.split('_')[2]
    
    if invitation_id not in pending_invitations:
        await callback.message.answer("Invalid or expired invitation.")
        return
    
    invitation = pending_invitations[invitation_id]
    
    # Notify member
    await callback.message.edit_text(
        f"❌ You have declined the invitation to join team '{invitation['team_name']}'."
    )
    
    try:
        # Notify manager
        await callback.bot.send_message(
            chat_id=invitation['manager_id'],
            text=f"❌ @{invitation['member_username']} has declined your invitation to join team '{invitation['team_name']}'."
        )
    except Exception as e:
        print(f"Error sending notification to manager: {e}")
    
    # Remove the invitation
    del pending_invitations[invitation_id]
    await callback.answer() 