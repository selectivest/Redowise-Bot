from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaVideo, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from taskmanager.database.models import User, Team, TeamMember, Task, UserRole
from taskmanager.database.connection import async_session
from taskmanager.notifications import NotificationSystem
from taskmanager.languages.manager import language_manager
from taskmanager.handlers.states import TaskStates
from datetime import datetime, timedelta, time
import re
import asyncio
import calendar as cal
from typing import Tuple, Optional
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.orm import joinedload

router = Router()
notification_system = None

def init_notification_system(bot):
    global notification_system
    notification_system = NotificationSystem(bot)

class TaskStates(StatesGroup):
    waiting_for_team_selection = State()
    waiting_for_member_selection = State()
    waiting_for_task_description = State()
    waiting_for_task_due_date = State()
    waiting_for_calendar_selection = State()

class CustomCalendarCallback(CallbackData, prefix="calendar"):
    action: str
    year: int
    month: int
    day: int

class CustomCalendar:
    def __init__(self):
        self.months = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.today = datetime.now().date()
    
    async def start_calendar(self, year: int = None, month: int = None) -> InlineKeyboardMarkup:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        
        keyboard = []
        
        # First row - Year navigation
        header = [
            InlineKeyboardButton(
                text="<<",
                callback_data=CustomCalendarCallback(
                    action="prev-year",
                    year=year,
                    month=month,
                    day=1
                ).pack()
            ),
            InlineKeyboardButton(
                text=str(year),
                callback_data=CustomCalendarCallback(
                    action="ignore",
                    year=year,
                    month=month,
                    day=1
                ).pack()
            ),
            InlineKeyboardButton(
                text=">>",
                callback_data=CustomCalendarCallback(
                    action="next-year",
                    year=year,
                    month=month,
                    day=1
                ).pack()
            ),
        ]
        keyboard.append(header)
        
        # Second row - Month navigation and display
        month_nav = [
            InlineKeyboardButton(
                text="<",
                callback_data=CustomCalendarCallback(
                    action="prev-month",
                    year=year,
                    month=month,
                    day=1
                ).pack()
            ),
            InlineKeyboardButton(
                text=f"{self.months[month]} {year}",
                callback_data=CustomCalendarCallback(
                    action="ignore",
                    year=year,
                    month=month,
                    day=1
                ).pack()
            ),
            InlineKeyboardButton(
                text=">",
                callback_data=CustomCalendarCallback(
                    action="next-month",
                    year=year,
                    month=month,
                    day=1
                ).pack()
            ),
        ]
        keyboard.append(month_nav)
        
        # Third row - Days of week
        keyboard.append(
            [InlineKeyboardButton(text=day, callback_data=CustomCalendarCallback(
                action="ignore",
                year=year,
                month=month,
                day=1
            ).pack()) for day in self.days]
        )

        month_calendar = cal.monthcalendar(year, month)
        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(
                        text=" ",
                        callback_data=CustomCalendarCallback(
                            action="ignore",
                            year=year,
                            month=month,
                            day=1
                        ).pack()
                    ))
                else:
                    current_date = datetime(year, month, day).date()
                    
                    if current_date < self.today:
                        # Past dates
                        row.append(InlineKeyboardButton(
                            text="❌",
                            callback_data=CustomCalendarCallback(
                                action="ignore",
                                year=year,
                                month=month,
                                day=day
                            ).pack()
                        ))
                    elif current_date == self.today:
                        # Today's date
                        row.append(InlineKeyboardButton(
                            text="🔵",
                            callback_data=CustomCalendarCallback(
                                action="day",
                                year=year,
                                month=month,
                                day=day
                            ).pack()
                        ))
                    else:
                        # Future dates
                        row.append(InlineKeyboardButton(
                            text=str(day),
                            callback_data=CustomCalendarCallback(
                                action="day",
                                year=year,
                                month=month,
                                day=day
                            ).pack()
                        ))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    async def process_selection(self, query: CallbackQuery, data: CustomCalendarCallback) -> tuple[bool, datetime]:
        action = data.action
        year = data.year
        month = data.month
        day = data.day
        
        if action == "ignore":
            await query.answer(cache_time=60)
            return False, None
        
        if action == "day":
            selected_date = datetime(year, month, day)
            if selected_date.date() < datetime.now().date():
                await query.answer(
                    language_manager.get_text("past_date_error", query.from_user.language_code),
                    show_alert=True
                )
                return False, None
            await query.message.delete_reply_markup()
            return True, selected_date
        
        if action == "prev-year":
            prev_date = datetime(year - 1, month, 1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(prev_date.year, prev_date.month)
            )
            return False, None
        
        if action == "next-year":
            next_date = datetime(year + 1, month, 1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(next_date.year, next_date.month)
            )
            return False, None
        
        if action == "prev-month":
            if month == 1:
                prev_date = datetime(year - 1, 12, 1)
            else:
                prev_date = datetime(year, month - 1, 1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(prev_date.year, prev_date.month)
            )
            return False, None
        
        if action == "next-month":
            if month == 12:
                next_date = datetime(year + 1, 1, 1)
            else:
                next_date = datetime(year, month + 1, 1)
            await query.message.edit_reply_markup(
                reply_markup=await self.start_calendar(next_date.year, next_date.month)
            )
            return False, None
        
        return False, None

@router.message(Command("add_task"))
async def cmd_add_task(message: Message, state: FSMContext, user: User):
    # Clear any existing state data first
    await state.clear()
    
    try:
        # Get user's teams
        async with async_session() as session:
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
            [InlineKeyboardButton(text=team.name, callback_data=f"team_{team.id}")]
            for team in teams
        ])
        
        await state.set_state(TaskStates.waiting_for_team_selection)
        await message.answer(
            language_manager.get_text("select_team", user.language_code),
            reply_markup=keyboard
        )
    except Exception as e:
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.callback_query(TaskStates.waiting_for_team_selection)
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
            await state.update_data(team_id=team_id)
            
            # Get team members
            query = select(User).join(TeamMember).where(TeamMember.team_id == team_id)
            result = await session.execute(query)
            members = result.scalars().all()
            
            # Create inline keyboard for member selection
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{member.first_name} {member.last_name} (@{member.username})",
                    callback_data=f"member_{member.id}"
                )]
                for member in members
            ])
            
            await state.set_state(TaskStates.waiting_for_member_selection)
            await callback.message.answer(
                language_manager.get_text("select_member", user.language_code),
                reply_markup=keyboard
            )
            await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.callback_query(TaskStates.waiting_for_member_selection)
async def process_member_selection(callback: CallbackQuery, state: FSMContext):
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
                
            member_id = int(callback.data.split('_')[1])
            await state.update_data(assignee_id=member_id)
            
            await state.set_state(TaskStates.waiting_for_task_description)
            await callback.message.answer(
                language_manager.get_text("enter_task_description", user.language_code)
            )
            await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.message(TaskStates.waiting_for_task_description)
async def process_task_description(message: Message, state: FSMContext, user: User):
    try:
        # Get text content from message or caption
        description = message.caption if message.caption else message.text
        
        # Handle forwarded messages
        if message.forward_from or message.forward_from_chat:
            # If it's a forwarded message, use the original text/caption
            description = message.caption or message.text or ""
        
        # Handle media content
        media_file_id = None
        if message.photo:
            # Get the largest photo size
            photo = message.photo[-1]
            media_file_id = photo.file_id
        elif message.video:
            media_file_id = message.video.file_id
        elif message.forward_from or message.forward_from_chat:
            # Check for video in forwarded message
            if hasattr(message, 'video') and message.video:
                media_file_id = message.video.file_id
            elif hasattr(message, 'document') and message.document and message.document.mime_type.startswith('video/'):
                media_file_id = message.document.file_id
        
        # Store both description and media_file_id in state
        await state.update_data(
            description=description,
            media_file_id=media_file_id
        )
        
        # Create inline keyboard for deadline selection
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=language_manager.get_text("tomorrow", user.language_code),
                    callback_data="deadline_tomorrow"
                ),
                InlineKeyboardButton(
                    text=language_manager.get_text("two_days", user.language_code),
                    callback_data="deadline_two_days"
                )
            ],
            [
                InlineKeyboardButton(
                    text=language_manager.get_text("three_days", user.language_code),
                    callback_data="deadline_three_days"
                ),
                InlineKeyboardButton(
                    text=language_manager.get_text("five_days", user.language_code),
                    callback_data="deadline_five_days"
                )
            ],
            [
                InlineKeyboardButton(
                    text=language_manager.get_text("one_week", user.language_code),
                    callback_data="deadline_one_week"
                ),
                InlineKeyboardButton(
                    text=language_manager.get_text("custom_date", user.language_code),
                    callback_data="deadline_custom"
                )
            ]
        ])
        
        await state.set_state(TaskStates.waiting_for_task_due_date)
        await message.answer(
            language_manager.get_text("select_due_date", user.language_code),
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Error in process_task_description: {e}")
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.callback_query(TaskStates.waiting_for_task_due_date)
async def process_deadline_selection(callback: CallbackQuery, state: FSMContext):
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
                
            deadline_type = callback.data.replace('deadline_', '')  # Remove 'deadline_' prefix
            print(f"Selected deadline type: {deadline_type}")  # Debug log
            data = await state.get_data()
            print(f"Current state data: {data}")  # Debug log
            
            if deadline_type == 'custom':
                # Show calendar for custom date selection
                calendar = CustomCalendar()
                keyboard = await calendar.start_calendar()
                
                await state.set_state(TaskStates.waiting_for_calendar_selection)
                await callback.message.answer(
                    language_manager.get_text("calendar_instructions", user.language_code),
                    reply_markup=keyboard
                )
                return
            
            # Handle predefined deadlines
            from datetime import datetime, timedelta
            now = datetime.now()
            print(f"Current time: {now}")  # Debug log
            
            # Map deadline types to days
            deadline_map = {
                'tomorrow': 1,
                'two_days': 2,
                'three_days': 3,
                'five_days': 5,
                'one_week': 7
            }
            
            if deadline_type not in deadline_map:
                print(f"Invalid deadline type received: {deadline_type}")  # Debug log
                raise ValueError(f"Invalid deadline type: {deadline_type}")
            
            # Calculate due date based on the deadline type
            days_to_add = deadline_map[deadline_type]
            due_date = (now + timedelta(days=days_to_add)).replace(hour=23, minute=59, second=59)
            
            print(f"Calculated due date: {due_date}")  # Debug log
            
            await state.update_data(due_date=due_date)
            
            try:
                # Create task first
                async with async_session() as session:
                    task = Task(
                        team_id=data['team_id'],
                        assignee_id=data['assignee_id'],
                        description=data['description'],
                        due_date=due_date,
                        status="pending",  # Use lowercase status
                        creator_id=callback.from_user.id,
                        media_file_id=data.get('media_file_id')  # Add media_file_id if exists
                    )
                    session.add(task)
                    await session.commit()
                    
                    # Refresh task to load team relationship
                    await session.refresh(task, ['team'])
                    
                    # Get assignee info for notification
                    assignee_query = select(User).where(User.id == data['assignee_id'])
                    assignee_result = await session.execute(assignee_query)
                    assignee = assignee_result.scalar_one_or_none()
                    
                    if assignee and notification_system:
                        await notification_system.notify_new_task(task, assignee)
                    
                    # Send success message in user's language
                    print(f"Debug: Task created with language code: {user.language_code}")  # Debug log
                    await callback.message.answer(
                        language_manager.get_text("task_created", user.language_code)
                    )
                    
                    # Remove the keyboard after successful task creation
                    await callback.message.delete_reply_markup()
                    
            except Exception as e:
                print(f"Error creating task in database: {e}")
                await callback.message.answer(
                    language_manager.get_text("error_occurred", user.language_code) +
                    "\n" + language_manager.get_text("database_error", user.language_code)
                )
            finally:
                await state.clear()
            
    except Exception as e:
        print(f"Error in deadline selection: {e}")
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()
    finally:
        await callback.answer()

@router.callback_query(TaskStates.waiting_for_calendar_selection)
async def process_calendar_selection(callback: CallbackQuery, state: FSMContext):
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
                
            calendar = CustomCalendar()
            callback_data = CustomCalendarCallback.unpack(callback.data)
            
            # Process the calendar selection
            is_selected, selected_date = await calendar.process_selection(callback, callback_data)
            
            if is_selected:
                if selected_date.date() < datetime.now().date():
                    await callback.answer(
                        language_manager.get_text("past_date_error", user.language_code),
                        show_alert=True
                    )
                    return
                
                # Get the current state data
                data = await state.get_data()
                
                if not all(key in data for key in ['team_id', 'assignee_id', 'description']):
                    print("Missing required data in state")  # Debug log
                    await callback.message.answer(
                        language_manager.get_text("error_occurred", user.language_code) + 
                        "\nMissing required data. Please start task creation again with /add_task"
                    )
                    await state.clear()
                    return
                
                # Create the task
                try:
                    async with async_session() as session:
                        # Get team and member info
                        team_query = select(Team).where(Team.id == data['team_id'])
                        team_result = await session.execute(team_query)
                        team = team_result.scalar_one_or_none()
                        
                        if not team:
                            await callback.message.answer(
                                language_manager.get_text("team_not_found", user.language_code)
                            )
                            await state.clear()
                            return
                        
                        member_query = select(User).where(User.id == data['assignee_id'])
                        member_result = await session.execute(member_query)
                        member = member_result.scalar_one_or_none()
                        
                        if not member:
                            await callback.message.answer(
                                language_manager.get_text("member_not_found", user.language_code)
                            )
                            await state.clear()
                            return
                        
                        # Create task
                        task = Task(
                            team_id=data['team_id'],
                            assignee_id=data['assignee_id'],
                            description=data['description'],
                            due_date=selected_date,
                            status="pending",
                            creator_id=user.id,
                            media_file_id=data.get('media_file_id')  # Add media_file_id if exists
                        )
                        session.add(task)
                        await session.commit()
                        
                        # Refresh task to load team relationship
                        await session.refresh(task, ['team'])
                        
                        # Notify assignee
                        if notification_system:
                            await notification_system.notify_new_task(task, member)
                        
                        # Send success message in user's language
                        print(f"Debug: Task created with language code: {user.language_code}")  # Debug log
                        await callback.message.answer(
                            language_manager.get_text("task_created", user.language_code)
                        )
                        
                except Exception as e:
                    print(f"Error creating task in database: {e}")
                    await callback.message.answer(
                        language_manager.get_text("error_occurred", user.language_code) +
                        "\n" + language_manager.get_text("database_error", user.language_code)
                    )
                finally:
                    await state.clear()
            
    except Exception as e:
        print(f"Error in calendar selection: {e}")  # Debug logging
        # Get the current state data for debugging
        try:
            state_data = await state.get_data()
            print(f"State data at error: {state_data}")
        except:
            print("Could not get state data")
        
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code) +
            "\nPlease try again with /add_task"
        )
        await state.clear()
        await callback.answer()

async def create_task(
    team_id: int,
    description: str,
    due_date: datetime,
    creator_id: int,
    assignee_id: int,
    language_code: str
) -> Optional[Task]:
    try:
        async with async_session() as session:
            # Get user from database to ensure we have the correct language code
            query = select(User).where(User.telegram_id == creator_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return None
                
            # Use the language code from the user object
            language_code = user.language_code
            
            # Rest of the function using language_code
            # ... existing code ...
            
            # Send success message in user's language
            print(f"Debug: Task created with language code: {language_code}")  # Debug log
            await callback.message.answer(
                language_manager.get_text("task_created", language_code)
            )
            
            # ... existing code ...
            
            return task
    except Exception as e:
        print(f"Error in create_task: {e}")
        await callback.message.answer(
            language_manager.get_text("error_occurred", language_code)
        )
        return None

@router.message(Command("tasks"))
async def cmd_tasks(message: Message, user: User):
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

@router.callback_query(F.data.startswith("view_tasks_"))
async def view_team_tasks(callback: CallbackQuery, user: User):
    team_id = int(callback.data.split('_')[2])
    
    async with async_session() as session:
        # Check if user is a manager of this team
        query = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        is_manager = result.scalar_one_or_none() is not None
        
        if is_manager:
            # Get all members of the team
            query = select(User).join(TeamMember).where(TeamMember.team_id == team_id)
            result = await session.execute(query)
            members = result.scalars().all()
            
            if not members:
                await callback.message.answer(
                    language_manager.get_text("no_members", user.language_code)
                )
                return
            
            # Create inline keyboard for member selection
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{member.first_name} {member.last_name} (@{member.username})",
                    callback_data=f"view_member_tasks_{team_id}_{member.id}"
                )]
                for member in members
            ])
            
            # Add "All members" button
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=language_manager.get_text("all_members", user.language_code),
                    callback_data=f"view_all_tasks_{team_id}"
                )
            ])
            
            await callback.message.answer(
                language_manager.get_text("select_member_view", user.language_code),
                reply_markup=keyboard
            )
            await callback.answer()
        else:
            # For regular members, show only their tasks with their language preference
            # Get tasks for the user in this team
            query = select(Task).options(joinedload(Task.team)).where(
                Task.team_id == team_id,
                Task.assignee_id == user.id
            )
            result = await session.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                await callback.message.answer(
                    language_manager.get_text("no_tasks", user.language_code)
                )
                return
            
            # Send header first
            await callback.message.answer(
                language_manager.get_text("tasks_header", user.language_code)
            )
            
            # Send each task
            for task in tasks:
                try:
                    # Format due date
                    due_date_str = task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text("no_due_date", user.language_code)
                    
                    # Calculate remaining days
                    remaining_days = (
                        task.due_date.date() - datetime.now().date()
                    ).days if task.due_date else None
                    
                    if remaining_days is not None:
                        due_date_str += f" ({remaining_days} {language_manager.get_text('days', user.language_code)})"
                    
                    # Get translated status with emoji
                    status_emoji = {
                        "pending": "📝",
                        "in_progress": "🔄",
                        "done": "✅"
                    }
                    current_status_emoji = status_emoji.get(task.status.lower(), "\ud83d\udcca")
                    status_key = {
                        'pending': 'status_pending',
                        'in_progress': 'status_in_progress',
                        'done': 'status_done'
                    }[task.status.lower()]
                    translated_status = f"{current_status_emoji} {language_manager.get_text(status_key, user.language_code)}"
                    
                    # Log the values being passed
                    print(f"Member task view values - task_id: {task.id}, team_name: {task.team.name if task.team else 'None'}, description: {task.description}, due_date: {due_date_str}, status: {translated_status}")
                    
                    # Format task text
                    task_text = language_manager.get_text(
                        "task_item",
                        user.language_code,
                        team_name=task.team.name if task.team else language_manager.get_text("unknown", user.language_code),
                        task_id=str(task.id),
                        assignee=f"{user.first_name} {user.last_name} (@{user.username})",
                        description=task.description,
                        due_date=due_date_str,
                        status=translated_status
                    )
                    
                    # Create status update buttons for each task
                    buttons = []
                    
                    # Show status update button if task is not done
                    if task.status.lower() != "done":
                        # Map current status to next status
                        status_flow = {
                            "pending": "in_progress",
                            "in_progress": "done"
                        }
                        next_status = status_flow[task.status.lower()]
                        next_status_emoji = status_emoji[next_status]
                        button_text = language_manager.get_text(
                            {
                                'pending': 'status_pending',
                                'in_progress': 'status_in_progress',
                                'done': 'status_done'
                            }[next_status],
                            user.language_code
                        )
                        buttons.append(
                            InlineKeyboardButton(
                                text=f"{next_status_emoji} {button_text}",
                                callback_data=f"update_status_{task.id}_{next_status}"
                            )
                        )
                    
                    status_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                    await callback.message.answer(task_text, reply_markup=status_keyboard)
                except Exception as e:
                    print(f"Error formatting task in view_team_tasks: {e}")
                    continue
            
            await callback.answer()

@router.callback_query(F.data.startswith("view_member_tasks_"))
async def view_member_tasks(callback: CallbackQuery, user: User):
    # Fix the callback data parsing
    data_parts = callback.data.split('_')
    team_id = int(data_parts[3])  # Changed from 2 to 3
    member_id = int(data_parts[4])  # Changed from 3 to 4
    
    async with async_session() as session:
        # Check if user is a manager of this team
        query = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        is_manager = result.scalar_one_or_none() is not None
        
        # Allow members to view their own tasks
        if not is_manager and user.id != member_id:
            await callback.message.answer(
                language_manager.get_text("own_tasks_only", user.language_code)
            )
            return
    
    # Pass is_manager=True to show_tasks for managers
    await show_tasks(callback.message, team_id, member_id, user.language_code, is_manager=is_manager)
    await callback.answer()

@router.callback_query(F.data.startswith("view_all_tasks_"))
async def view_all_tasks(callback: CallbackQuery, user: User):
    # Fix the callback data parsing
    data_parts = callback.data.split('_')
    team_id = int(data_parts[3])
    
    async with async_session() as session:
        # Check if user is a manager of this team
        query = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        is_manager = result.scalar_one_or_none() is not None
        
        # Get all tasks for the team with team relationship loaded
        query = select(Task).options(joinedload(Task.team)).where(Task.team_id == team_id)
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        if not tasks:
            await callback.message.answer(
                language_manager.get_text("no_tasks", user.language_code)
            )
            return
        
        # Send header first
        await callback.message.answer(
            language_manager.get_text("tasks_header", user.language_code)
        )
        
        # Send each task
        for task in tasks:
            try:
                # Get assignee info
                assignee_query = select(User).where(User.id == task.assignee_id)
                assignee_result = await session.execute(assignee_query)
                assignee = assignee_result.scalar_one_or_none()
                
                # Format assignee name
                assignee_name = (
                    f"{assignee.first_name} {assignee.last_name} (@{assignee.username})"
                    if assignee
                    else language_manager.get_text("unknown", user.language_code)
                )
                
                # Format due date
                due_date_str = task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text("no_due_date", user.language_code)
                
                # Calculate remaining days
                remaining_days = (
                    task.due_date.date() - datetime.now().date()
                ).days if task.due_date else None
                
                if remaining_days is not None:
                    due_date_str += f" ({remaining_days} {language_manager.get_text('days', user.language_code)})"
                
                # Get translated status with emoji
                status_emoji = {
                    "pending": "📝",
                    "in_progress": "🔄",
                    "done": "✅"
                }
                current_status_emoji = status_emoji.get(task.status.lower(), "\ud83d\udcca")
                status_key = {
                    'pending': 'status_pending',
                    'in_progress': 'status_in_progress',
                    'done': 'status_done'
                }[task.status.lower()]
                translated_status = f"{current_status_emoji} {language_manager.get_text(status_key, user.language_code)}"
                
                # Log the values being passed
                print(f"All tasks view values - task_id: {task.id}, team_name: {task.team.name if task.team else 'None'}, description: {task.description}, due_date: {due_date_str}, status: {translated_status}")
                
                # Format task text
                task_text = language_manager.get_text(
                    "task_item",
                    user.language_code,
                    team_name=task.team.name if task.team else language_manager.get_text("unknown", user.language_code),
                    task_id=str(task.id),
                    assignee=assignee_name,
                    description=task.description,
                    due_date=due_date_str,
                    status=translated_status
                )
                
                # Create status update buttons for each task
                buttons = []
                
                # Show status update button if:
                # 1. User is a manager (can change any status)
                # 2. User is the assignee and task is not done
                if is_manager or (task.assignee_id == user.id and task.status.lower() != "done"):
                    # Map current status to next status
                    status_flow = {
                        "pending": "in_progress",
                        "in_progress": "done",
                        "done": "pending"
                    }
                    next_status = status_flow[task.status.lower()]
                    button_text = language_manager.get_text(
                        {
                            'pending': 'status_pending',
                            'in_progress': 'status_in_progress',
                            'done': 'status_done'
                        }[next_status],
                        user.language_code
                    )
                    buttons.append(
                        InlineKeyboardButton(
                            text=f"{status_emoji[next_status]} {button_text}",
                            callback_data=f"update_status_{task.id}_{next_status}"
                        )
                    )
                
                # Add delete button for managers (always show for managers)
                if is_manager:
                    buttons.append(
                        InlineKeyboardButton(
                            text=language_manager.get_text("delete_task", user.language_code),
                            callback_data=f"delete_task_{task.id}"
                        )
                    )
                
                status_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                await callback.message.answer(task_text, reply_markup=status_keyboard)
            except Exception as e:
                print(f"Error formatting task in view_all_tasks: {e}")
                continue
        
        await callback.answer()

async def show_tasks(message, team_id: int, member_id: int | None, language_code: str, is_manager: bool = False):
    async with async_session() as session:
        # Build query based on user role and member_id
        query = select(Task).options(joinedload(Task.team)).where(Task.team_id == team_id)
        
        # If viewing specific member's tasks
        if member_id is not None:
            query = query.where(Task.assignee_id == member_id)
        # If viewing all tasks (member_id is None) and user is not a manager
        elif not is_manager:
            query = query.where(Task.assignee_id == message.from_user.id)
        
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        if not tasks:
            await message.answer(
                language_manager.get_text("no_tasks", language_code)
            )
            return
        
        # Send header first
        await message.answer(
            language_manager.get_text("tasks_header", language_code)
        )
        
        # Send each task
        for task in tasks:
            try:
                # Get assignee info
                assignee_query = select(User).where(User.id == task.assignee_id)
                assignee_result = await session.execute(assignee_query)
                assignee = assignee_result.scalar_one_or_none()
                
                # Format assignee name
                assignee_name = (
                    f"{assignee.first_name} {assignee.last_name} (@{assignee.username})"
                    if assignee
                    else language_manager.get_text("unknown", language_code)
                )
                
                # Format due date
                due_date_str = task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text("no_due_date", language_code)
                
                # Calculate remaining days
                remaining_days = (
                    task.due_date.date() - datetime.now().date()
                ).days if task.due_date else None
                
                if remaining_days is not None:
                    due_date_str += f" ({remaining_days} {language_manager.get_text('days', language_code)})"
                
                # Get translated status with emoji
                status_emoji = {
                    "pending": "📝",
                    "in_progress": "🔄",
                    "done": "✅"
                }
                current_status_emoji = status_emoji.get(task.status.lower(), "\ud83d\udcca")
                status_key = {
                    'pending': 'status_pending',
                    'in_progress': 'status_in_progress',
                    'done': 'status_done'
                }[task.status.lower()]
                translated_status = f"{current_status_emoji} {language_manager.get_text(status_key, language_code)}"
                
                # Format task text
                task_text = language_manager.get_text(
                    "task_item",
                    language_code,
                    team_name=task.team.name if task.team else language_manager.get_text("unknown", language_code),
                    task_id=str(task.id),
                    assignee=assignee_name,
                    description=task.description,
                    due_date=due_date_str,
                    status=translated_status
                )
                
                # Create status update buttons for each task
                buttons = []
                
                # Show status update button if:
                # 1. User is a manager (can change any status)
                # 2. User is the assignee and task is not done
                if is_manager or (message.from_user.id == task.assignee_id and task.status.lower() != "done"):
                    # Map current status to next status
                    status_flow = {
                        "pending": "in_progress",
                        "in_progress": "done",
                        "done": "pending"
                    }
                    next_status = status_flow[task.status.lower()]
                    next_status_emoji = status_emoji[next_status]
                    button_text = language_manager.get_text(
                        {
                            'pending': 'status_pending',
                            'in_progress': 'status_in_progress',
                            'done': 'status_done'
                        }[next_status],
                        language_code
                    )
                    buttons.append(
                        InlineKeyboardButton(
                            text=f"{next_status_emoji} {button_text}",
                            callback_data=f"update_status_{task.id}_{next_status}"
                        )
                    )
                
                # Add delete button for managers (always show for managers)
                if is_manager:
                    buttons.append(
                        InlineKeyboardButton(
                            text=language_manager.get_text("delete_task", language_code),
                            callback_data=f"delete_task_{task.id}"
                        )
                    )
                
                status_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

                # If task has media, send it first
                if task.media_file_id:
                    try:
                        # Try to send as video first
                        await message.answer_video(
                            video=task.media_file_id,
                            caption=task_text,
                            reply_markup=status_keyboard
                        )
                    except Exception as video_error:
                        try:
                            # If video fails, try as photo
                            await message.answer_photo(
                                photo=task.media_file_id,
                                caption=task_text,
                                reply_markup=status_keyboard
                            )
                        except Exception as photo_error:
                            # If both fail, just send the text
                            print(f"Error sending media for task {task.id}: {video_error}, {photo_error}")
                            await message.answer(task_text, reply_markup=status_keyboard)
                else:
                    # If no media, just send the text
                    await message.answer(task_text, reply_markup=status_keyboard)

            except Exception as e:
                print(f"Error formatting task in show_tasks: {e}")
                continue

@router.callback_query(F.data.startswith("update_status_"))
async def update_task_status(callback: CallbackQuery, user: User):
    try:
        print(f"Starting status update process for user {user.id}")  # Debug log
        
        # Fix callback data parsing to handle status with underscores
        data_parts = callback.data.split('_', 3)  # Split only first 3 underscores
        task_id = int(data_parts[2])
        new_status = data_parts[3]  # This will keep "in_progress" intact
        print(f"Parsed callback data - task_id: {task_id}, new_status: {new_status}")  # Debug log
        
        async with async_session() as session:
            # Get the task with team relationship loaded
            query = select(Task).options(joinedload(Task.team)).where(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if not task:
                print(f"Task not found with id {task_id}")  # Debug log
                await callback.message.answer(
                    language_manager.get_text("task_not_found", user.language_code)
                )
                return
            
            print(f"Found task: id={task.id}, current_status={task.status}, new_status={new_status}")  # Debug log
            
            # Check if user is a manager of the team
            team_member_query = select(TeamMember).where(
                TeamMember.team_id == task.team_id,
                TeamMember.user_id == user.id,
                TeamMember.role == "Manager"
            )
            team_member_result = await session.execute(team_member_query)
            is_manager = team_member_result.scalar_one_or_none() is not None
            print(f"User {user.id} is manager: {is_manager}")  # Debug log
            
            # For members (non-managers):
            # 1. Can only update their own tasks
            # 2. Can only change status up to "done"
            # 3. Cannot change status of tasks that are already "done"
            if not is_manager:
                if task.assignee_id != user.id:
                    print(f"User {user.id} tried to update task {task.id} assigned to {task.assignee_id}")  # Debug log
                    await callback.message.answer(
                        language_manager.get_text("update_own_tasks", user.language_code)
                    )
                    return
                if task.status.lower() == "done":
                    print(f"User {user.id} tried to update done task {task.id}")  # Debug log
                    await callback.message.answer(
                        language_manager.get_text("completed_tasks_locked", user.language_code)
                    )
                    return
                if new_status not in ["in_progress", "done"]:
                    print(f"User {user.id} tried to set invalid status {new_status} for task {task.id}")  # Debug log
                    await callback.message.answer(
                        language_manager.get_text("status_limit", user.language_code)
                    )
                    return
            
            try:
                # Get assignee info for notification
                assignee_query = select(User).where(User.id == task.assignee_id)
                assignee_result = await session.execute(assignee_query)
                assignee = assignee_result.scalar_one_or_none()
                print(f"Found assignee: {assignee.id if assignee else 'None'}")  # Debug log
                
                # Get manager info for notification
                manager_query = select(User).join(TeamMember).where(
                    TeamMember.team_id == task.team_id,
                    TeamMember.role == "Manager"
                )
                manager_result = await session.execute(manager_query)
                manager = manager_result.scalar_one_or_none()
                print(f"Found manager: {manager.id if manager else 'None'}")  # Debug log
                
                # Update task status
                old_status = task.status
                task.status = new_status
                await session.commit()
                print(f"Updated task {task.id} status from {old_status} to {new_status}")  # Debug log
                
                try:
                    # Send notifications based on who made the change
                    if is_manager and assignee:
                        # If manager changed status, notify assignee
                        print(f"Sending notification to assignee {assignee.id}")  # Debug log
                        await callback.bot.send_message(
                            chat_id=assignee.telegram_id,
                            text=language_manager.get_text(
                                'status_change_assignee',
                                assignee.language_code,
                                team_name=task.team.name if task.team else language_manager.get_text("unknown", assignee.language_code),
                                task_id=str(task.id),
                                description=task.description,
                                due_date=task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text('no_due_date', assignee.language_code),
                                new_status=language_manager.get_text({
                                    'pending': 'status_pending',
                                    'in_progress': 'status_in_progress',
                                    'done': 'status_done'
                                }[new_status], assignee.language_code)
                            )
                        )
                    elif not is_manager and manager:
                        # If assignee changed status, notify manager
                        print(f"Sending notification to manager {manager.id}")  # Debug log
                        await callback.bot.send_message(
                            chat_id=manager.telegram_id,
                            text=language_manager.get_text(
                                'status_change_manager',
                                manager.language_code,
                                team_name=task.team.name if task.team else language_manager.get_text("unknown", manager.language_code),
                                task_id=str(task.id),
                                assignee_name=f"{user.first_name} {user.last_name} (@{user.username})",
                                description=task.description,
                                due_date=task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text('no_due_date', manager.language_code),
                                new_status=language_manager.get_text({
                                    'pending': 'status_pending',
                                    'in_progress': 'status_in_progress',
                                    'done': 'status_done'
                                }[new_status], manager.language_code)
                            )
                        )
                except Exception as notify_error:
                    print(f"Error sending notification: {notify_error}")  # Debug log
                
                # Format due date
                due_date_str = task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text("no_due_date", user.language_code)
                
                # Calculate remaining days
                remaining_days = (
                    task.due_date.date() - datetime.now().date()
                ).days if task.due_date else None
                
                if remaining_days is not None:
                    due_date_str += f" ({remaining_days} {language_manager.get_text('days', user.language_code)})"
                
                # Get translated status with emoji
                status_emoji = {
                    "pending": "📝",
                    "in_progress": "🔄",
                    "done": "✅"
                }
                current_status_emoji = status_emoji.get(new_status.lower(), "\ud83d\udcca")
                status_key = {
                    'pending': 'status_pending',
                    'in_progress': 'status_in_progress',
                    'done': 'status_done'
                }[new_status.lower()]
                translated_status = f"{current_status_emoji} {language_manager.get_text(status_key, user.language_code)}"
                
                # Format task text
                task_text = language_manager.get_text(
                    "task_item",
                    user.language_code,
                    team_name=task.team.name if task.team else language_manager.get_text("unknown", user.language_code),
                    task_id=str(task.id),
                    assignee=f"{assignee.first_name} {assignee.last_name} (@{assignee.username})" if assignee else language_manager.get_text("unknown", user.language_code),
                    description=task.description,
                    due_date=due_date_str,
                    status=translated_status
                )
                
                # Create new keyboard
                buttons = []
                # Show status update button if:
                # 1. User is a manager (can change any status)
                # 2. User is the assignee and task is not done
                if is_manager or (user.id == task.assignee_id and new_status != "done"):
                    # Map current status to next status
                    status_flow = {
                        "pending": "in_progress",
                        "in_progress": "done",
                        "done": "pending"
                    }
                    next_status = status_flow[new_status.lower()]
                    next_status_emoji = status_emoji[next_status]
                    button_text = language_manager.get_text(
                        {
                            'pending': 'status_pending',
                            'in_progress': 'status_in_progress',
                            'done': 'status_done'
                        }[next_status],
                        user.language_code
                    )
                    buttons.append(
                        InlineKeyboardButton(
                            text=f"{next_status_emoji} {button_text}",
                            callback_data=f"update_status_{task.id}_{next_status}"
                        )
                    )
                
                # Add delete button for managers (always show for managers)
                if is_manager:
                    buttons.append(
                        InlineKeyboardButton(
                            text=language_manager.get_text("delete_task", user.language_code),
                            callback_data=f"delete_task_{task.id}"
                        )
                    )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                
                try:
                    # If task has media, update with media
                    if task.media_file_id:
                        try:
                            # Try to edit as video first
                            await callback.message.edit_media(
                                media=InputMediaVideo(
                                    media=task.media_file_id,
                                    caption=task_text
                                ),
                                reply_markup=keyboard
                            )
                        except Exception as video_error:
                            try:
                                # If video fails, try as photo
                                await callback.message.edit_media(
                                    media=InputMediaPhoto(
                                        media=task.media_file_id,
                                        caption=task_text
                                    ),
                                    reply_markup=keyboard
                                )
                            except Exception as photo_error:
                                print(f"Error updating media message: {video_error}, {photo_error}")  # Debug log
                                # If both fail, just update the text
                                await callback.message.edit_text(task_text, reply_markup=keyboard)
                    else:
                        # If no media, just update the text
                        await callback.message.edit_text(task_text, reply_markup=keyboard)
                except Exception as edit_error:
                    print(f"Error updating message: {edit_error}")  # Debug log
                    # If editing fails, try to send a new message
                    try:
                        if task.media_file_id:
                            try:
                                await callback.message.answer_video(
                                    video=task.media_file_id,
                                    caption=task_text,
                                    reply_markup=keyboard
                                )
                            except Exception as video_error:
                                try:
                                    await callback.message.answer_photo(
                                        photo=task.media_file_id,
                                        caption=task_text,
                                        reply_markup=keyboard
                                    )
                                except Exception as photo_error:
                                    print(f"Error sending new media message: {video_error}, {photo_error}")  # Debug log
                                    await callback.message.answer(task_text, reply_markup=keyboard)
                        else:
                            await callback.message.answer(task_text, reply_markup=keyboard)
                    except Exception as send_error:
                        print(f"Error sending new message: {send_error}")  # Debug log
                        await callback.message.answer(
                            language_manager.get_text("error_occurred", user.language_code)
                        )
                
                await callback.answer()
                
            except Exception as db_error:
                print(f"Database error during status update: {db_error}")  # Debug log
                await session.rollback()
                raise
            
    except Exception as e:
        print(f"Error in update_task_status: {e}")  # Debug log
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await callback.answer()

@router.callback_query(F.data.startswith("delete_task_"))
async def delete_task(callback: CallbackQuery, user: User):
    try:
        task_id = int(callback.data.split('_')[2])
        
        async with async_session() as session:
            # Get the task with team relationship loaded
            query = select(Task).options(joinedload(Task.team)).where(Task.id == task_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if not task:
                await callback.message.answer(
                    language_manager.get_text("task_not_found", user.language_code)
                )
                return
            
            # Check if user is a manager of the team
            team_member_query = select(TeamMember).where(
                TeamMember.team_id == task.team_id,
                TeamMember.user_id == user.id,
                TeamMember.role == "Manager"
            )
            team_member_result = await session.execute(team_member_query)
            is_manager = team_member_result.scalar_one_or_none() is not None
            
            if not is_manager:
                await callback.message.answer(
                    language_manager.get_text("managers_only_delete", user.language_code)
                )
                return
            
            # Get assignee info for notification
            assignee_query = select(User).where(User.id == task.assignee_id)
            assignee_result = await session.execute(assignee_query)
            assignee = assignee_result.scalar_one_or_none()
            
            # Log the values being passed
            print(f"Delete task notification values - task_id: {task.id}, team_name: {task.team.name if task.team else 'None'}, description: {task.description}")
            
            # Delete the task
            await session.delete(task)
            await session.commit()
            
            # Send notification to assignee
            if assignee and notification_system:
                await callback.bot.send_message(
                    chat_id=assignee.telegram_id,
                    text=language_manager.get_text(
                        'task_deleted',
                        assignee.language_code,
                        team_name=task.team.name if task.team else language_manager.get_text("unknown", assignee.language_code),
                        task_id=str(task.id),
                        description=task.description,
                        due_date=task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text('no_due_date', assignee.language_code),
                        status=language_manager.get_text({
                            'pending': 'status_pending',
                            'in_progress': 'status_in_progress',
                            'done': 'status_done'
                        }[task.status.lower()], assignee.language_code),
                        deleted_by=f"{user.first_name} {user.last_name} (@{user.username})"
                    )
                )
            
            # Delete the message
            await callback.message.delete()
            await callback.answer(
                language_manager.get_text("task_deleted_success", user.language_code)
            )
    except Exception as e:
        print(f"Error in delete_task: {e}")
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await callback.answer()

def get_remaining_days(deadline: datetime) -> int:
    today = datetime.now()
    # Set both dates to midnight to compare only days
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
    remaining = deadline - today
    return max(0, remaining.days) 