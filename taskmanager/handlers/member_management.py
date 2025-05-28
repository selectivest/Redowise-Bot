from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
import logging

from ..database.models import Team, TeamMember, User, TeamMemberRole, Task
from ..database.connection import async_session
from ..languages.manager import language_manager
from ..utils.team import get_user_managed_teams, get_team_members

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

class MemberManagementStates(StatesGroup):
    selecting_team = State()
    selecting_member = State()
    selecting_action = State()
    confirming_action = State()

# States
SELECTING_TEAM, SELECTING_MEMBER, SELECTING_ACTION, CONFIRMING_ACTION = range(4)

def get_user_full_name(user: User) -> str:
    """Helper function to get user's full name"""
    return f"{user.first_name} {user.last_name}" if user.last_name else user.first_name

@router.message(Command("member_management"))
async def start_member_management(message: Message, state: FSMContext):
    """Start the member management process"""
    async with async_session() as db:
        # First get user by telegram_id
        query = select(User).where(User.telegram_id == message.from_user.id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(language_manager.get_text("user_not_found", 'fa'))
            return
            
        lang_code = user.language_code
        # Get teams where user is a manager using user.id
        teams = await get_user_managed_teams(db, user.id)
        if not teams:
            await message.answer(language_manager.get_text("no_managed_teams", lang_code))
            return
        # Create keyboard with team options
        builder = InlineKeyboardBuilder()
        for team in teams:
            builder.button(text=team.name, callback_data=f"team_{team.id}")
        builder.adjust(1)
        await message.answer(
            language_manager.get_text("select_team_manage", lang_code),
            reply_markup=builder.as_markup()
        )
        await state.set_state(MemberManagementStates.selecting_team)

@router.callback_query(MemberManagementStates.selecting_team, F.data.startswith("team_"))
async def process_team_selection(callback: CallbackQuery, state: FSMContext):
    """Handle team selection for member management"""
    team_id = int(callback.data.split("_")[1])
    async with async_session() as db:
        user = await db.get(User, callback.from_user.id)
        lang_code = user.language_code if user else 'fa'
        team = await db.get(Team, team_id)
        if not team:
            await callback.answer(language_manager.get_text("team_not_found", lang_code))
            return
        members = await get_team_members(db, team_id)
        if not members:
            await callback.answer(language_manager.get_text("no_members", lang_code))
            return
        builder = InlineKeyboardBuilder()
        for member in members:
            if member.user_id != callback.from_user.id:
                u = await db.get(User, member.user_id)
                if u:
                    role_emoji = "👑" if member.role == TeamMemberRole.OWNER else "⭐" if member.role == TeamMemberRole.MANAGER else "👤"
                    builder.button(
                        text=f"{role_emoji} {get_user_full_name(u)}",
                        callback_data=f"member_{member.id}"
                    )
        builder.adjust(1)
        await callback.message.edit_text(
            language_manager.get_text("select_member_manage", lang_code),
            reply_markup=builder.as_markup()
        )
        await state.update_data(team_id=team_id)
        await state.set_state(MemberManagementStates.selecting_member)

@router.callback_query(MemberManagementStates.selecting_member, F.data.startswith("member_"))
async def process_member_selection(callback: CallbackQuery, state: FSMContext):
    """Handle member selection and show management options"""
    member_id = int(callback.data.split("_")[1])
    async with async_session() as db:
        user = await db.get(User, callback.from_user.id)
        lang_code = user.language_code if user else 'fa'
        member = await db.get(TeamMember, member_id)
        if not member:
            await callback.answer(language_manager.get_text("member_not_found", lang_code))
            return
        
        member_user = await db.get(User, member.user_id)
        if not member_user:
            await callback.answer(language_manager.get_text("user_not_found", lang_code))
            return
        
        # Create keyboard with management options
        builder = InlineKeyboardBuilder()
        builder.button(
            text=language_manager.get_text("remove_member", lang_code),
            callback_data=f"action_remove"
        )
        
        if member.role == TeamMemberRole.MANAGER:
            builder.button(
                text=language_manager.get_text("make_member", lang_code),
                callback_data=f"action_make_member"
            )
        else:
            builder.button(
                text=language_manager.get_text("make_manager", lang_code),
                callback_data=f"action_make_manager"
            )
        
        builder.button(
            text=language_manager.get_text("back", lang_code),
            callback_data="back"
        )
        builder.adjust(1)
        
        await callback.message.edit_text(
            language_manager.get_text("member_management_options", lang_code).format(
                full_name=get_user_full_name(member_user)
            ),
            reply_markup=builder.as_markup()
        )
        await state.update_data(member_id=member_id)
        await state.set_state(MemberManagementStates.selecting_action)

@router.callback_query(MemberManagementStates.selecting_action, F.data.startswith("action_"))
async def process_member_action(callback: CallbackQuery, state: FSMContext):
    """Handle member management action selection"""
    # Get the full action type (e.g., "make_manager" or "make_member")
    action = callback.data.split("_", 1)[1]  # Changed to split only once and take the rest
    logger.info(f"Full action type from button: {action}")
    
    state_data = await state.get_data()
    member_id = state_data.get("member_id")
    
    async with async_session() as db:
        user = await db.get(User, callback.from_user.id)
        lang_code = user.language_code if user else 'fa'
        member = await db.get(TeamMember, member_id)
        if not member:
            await callback.answer(language_manager.get_text("member_not_found", lang_code))
            return
        
        member_user = await db.get(User, member.user_id)
        if not member_user:
            await callback.answer(language_manager.get_text("user_not_found", lang_code))
            return
        
        team = await db.get(Team, member.team_id)
        if not team:
            await callback.answer(language_manager.get_text("team_not_found", lang_code))
            return
        
        # Check if trying to remove last manager
        if action == "remove" and member.role == TeamMemberRole.MANAGER:
            manager_count = await db.scalar(
                select(func.count()).select_from(TeamMember).where(
                    and_(
                        TeamMember.team_id == team.id,
                        TeamMember.role == TeamMemberRole.MANAGER
                    )
                )
            )
            if manager_count <= 1:
                await callback.answer(language_manager.get_text("cannot_remove_last_manager", lang_code))
                return
        
        # Create confirmation keyboard
        builder = InlineKeyboardBuilder()
        builder.button(
            text=language_manager.get_text("yes", lang_code),
            callback_data=f"confirm_{action}"  # Pass the full action type
        )
        builder.button(
            text=language_manager.get_text("no", lang_code),
            callback_data="confirm_no"
        )
        builder.button(
            text=language_manager.get_text("back", lang_code),
            callback_data="back"
        )
        builder.adjust(2)
        
        if action == "remove":
            text = language_manager.get_text("confirm_remove_member", lang_code).format(
                full_name=get_user_full_name(member_user),
                team_name=team.name
            )
        else:
            role = language_manager.get_text("manager", lang_code) if action == "make_manager" else language_manager.get_text("member", lang_code)
            text = language_manager.get_text("confirm_role_change", lang_code).format(
                full_name=get_user_full_name(member_user),
                team_name=team.name,
                role=role
            )
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await state.set_state(MemberManagementStates.confirming_action)

@router.callback_query(MemberManagementStates.confirming_action, F.data.startswith("confirm_"))
async def process_action_confirmation(callback: CallbackQuery, state: FSMContext):
    """Process the confirmed member management action"""
    logger.info(f"Starting process_action_confirmation with callback data: {callback.data}")
    
    if callback.data == "confirm_no":
        logger.info("User declined the action, returning to member selection")
        return await process_member_selection(callback, state)
    
    # Extract the full action type (e.g., "make_manager" or "make_member")
    action = callback.data.split("_", 1)[1]  # Changed to split only once and take the rest
    logger.info(f"Full action type: {action}")
    
    state_data = await state.get_data()
    member_id = state_data.get("member_id")
    logger.info(f"Member ID from state: {member_id}")
    
    async with async_session() as db:
        # First get the manager (current user) by telegram_id
        manager_query = select(User).where(User.telegram_id == callback.from_user.id)
        manager_result = await db.execute(manager_query)
        manager = manager_result.scalar_one_or_none()
        
        if not manager:
            logger.error(f"Manager not found with telegram_id: {callback.from_user.id}")
            await callback.answer(language_manager.get_text("user_not_found", 'fa'))
            return
            
        lang_code = manager.language_code
        logger.info(f"Current user language: {lang_code}")
        logger.info(f"Manager found: {get_user_full_name(manager)}")
        
        member = await db.get(TeamMember, member_id)
        if not member:
            logger.error(f"Member not found with ID: {member_id}")
            await callback.answer(language_manager.get_text("member_not_found", lang_code))
            return
        
        logger.info(f"Current member role: {member.role}")
        
        member_user = await db.get(User, member.user_id)
        if not member_user:
            logger.error(f"Member user not found with ID: {member.user_id}")
            await callback.answer(language_manager.get_text("user_not_found", lang_code))
            return
        
        logger.info(f"Member user found: {get_user_full_name(member_user)}")
        
        team = await db.get(Team, member.team_id)
        if not team:
            logger.error(f"Team not found with ID: {member.team_id}")
            await callback.answer(language_manager.get_text("team_not_found", lang_code))
            return
        
        logger.info(f"Team found: {team.name}")
        
        if action == "remove":
            logger.info("Processing member removal")
            # Delete member's tasks
            logger.info(f"Deleting tasks for member {member.user_id} in team {team.id}")
            delete_query = select(Task).where(
                and_(
                    Task.team_id == team.id,
                    Task.assignee_id == member.user_id
                )
            )
            tasks_to_delete = await db.execute(delete_query)
            tasks = tasks_to_delete.scalars().all()
            
            # Delete each task
            for task in tasks:
                logger.info(f"Deleting task {task.id}")
                await db.delete(task)
            
            # Remove member
            logger.info(f"Removing member {member.id} from team {team.id}")
            await db.delete(member)
            await db.commit()
            logger.info("Member and their tasks removed successfully")
            
            # Notify both users
            await callback.message.edit_text(
                language_manager.get_text("member_deleted", lang_code).format(
                    full_name=get_user_full_name(member_user),
                    team_name=team.name
                )
            )
            
            # Try to notify the removed member
            try:
                await callback.bot.send_message(
                    member_user.telegram_id,
                    language_manager.get_text("member_deleted_notification", lang_code).format(
                        team_name=team.name,
                        manager_name=get_user_full_name(manager)
                    )
                )
                logger.info("Notification sent to removed member")
            except Exception as e:
                logger.error(f"Failed to send notification to removed member: {e}")
                pass  # Ignore if we can't notify the user
        
        else:  # Role change
            logger.info("Processing role change")
            # Determine the new role based on the action
            if action == "make_manager":
                new_role = TeamMemberRole.MANAGER
                logger.info(f"Attempting to make user a manager. Current role: {member.role}, New role: {new_role}")
                # Only show error if already a manager
                if member.role == TeamMemberRole.MANAGER:
                    logger.info(f"User is already a manager, showing error message")
                    await callback.message.edit_text(
                        language_manager.get_text("already_manager", lang_code).format(
                            full_name=get_user_full_name(member_user)
                        )
                    )
                    return
            elif action == "make_member":  # Changed to explicit check
                new_role = TeamMemberRole.MEMBER
                logger.info(f"Attempting to make user a member. Current role: {member.role}, New role: {new_role}")
                # Only show error if already a member
                if member.role == TeamMemberRole.MEMBER:
                    logger.info(f"User is already a member, showing error message")
                    await callback.message.edit_text(
                        language_manager.get_text("already_member", lang_code).format(
                            full_name=get_user_full_name(member_user)
                        )
                    )
                    return
            else:
                logger.error(f"Unknown action type: {action}")
                await callback.answer(language_manager.get_text("invalid_action", lang_code))
                return
            
            logger.info(f"Updating role from {member.role} to {new_role}")
            # Update role
            member.role = new_role
            await db.commit()
            logger.info("Role updated successfully")
            
            role_text = language_manager.get_text("manager", lang_code) if new_role == TeamMemberRole.MANAGER else language_manager.get_text("member", lang_code)
            logger.info(f"Role text for notification: {role_text}")
            
            # Notify both users
            message = language_manager.get_text("role_changed_to_manager", lang_code) if new_role == TeamMemberRole.MANAGER else language_manager.get_text("role_changed_to_member", lang_code)
            logger.info(f"Notification message: {message}")
            
            await callback.message.edit_text(
                message.format(
                    full_name=get_user_full_name(member_user),
                    team_name=team.name
                )
            )
            logger.info("Notification sent to manager")
            
            # Try to notify the member whose role was changed
            try:
                await callback.bot.send_message(
                    member_user.telegram_id,
                    language_manager.get_text("member_role_changed_notification", lang_code).format(
                        team_name=team.name,
                        manager_name=get_user_full_name(manager),
                        role=role_text
                    )
                )
                logger.info("Notification sent to member")
            except Exception as e:
                logger.error(f"Failed to send notification to member: {e}")
                pass  # Ignore if we can't notify the user
        
        # Clear state
        await state.clear()
        logger.info("State cleared, process completed")

@router.callback_query(MemberManagementStates.confirming_action, F.data == "back")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel the current action and go back to member selection"""
    await process_member_selection(callback, state)

@router.callback_query(MemberManagementStates.selecting_action, F.data == "back")
async def back_to_teams(callback: CallbackQuery, state: FSMContext):
    """Go back to team selection"""
    await start_member_management(callback.message, state) 