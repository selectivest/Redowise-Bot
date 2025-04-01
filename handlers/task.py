from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import User, Team, TeamMember, Task, UserRole
from database.connection import async_session
from sqlalchemy import select
from datetime import datetime, timedelta, time
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from notifications import NotificationSystem
import re
import asyncio
import calendar as cal
from typing import Tuple, Optional
from aiogram.filters.callback_data import CallbackData
from languages.manager import language_manager

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
                text=self.months[month],
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

        # Get current date for highlighting today
        today = now.date()
        
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
                    # Create date object for comparison
                    current_date = datetime(year, month, day).date()
                    
                    if current_date < datetime.now().date():
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
                    elif current_date == today:
                        # Today's date
                        row.append(InlineKeyboardButton(
                            text=f"🔵{day}",
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
                await query.answer("❌ Cannot select a past date!", show_alert=True)
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
        team_id = int(callback.data.split('_')[1])
        await state.update_data(team_id=team_id)
        
        # Get team members
        async with async_session() as session:
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
                language_manager.get_text("select_member", callback.from_user.language_code),
                reply_markup=keyboard
            )
            await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.callback_query(TaskStates.waiting_for_member_selection)
async def process_member_selection(callback: CallbackQuery, state: FSMContext):
    try:
        member_id = int(callback.data.split('_')[1])
        await state.update_data(assignee_id=member_id)
        
        await state.set_state(TaskStates.waiting_for_task_description)
        await callback.message.answer(
            language_manager.get_text("enter_task_description", callback.from_user.language_code)
        )
        await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.message(TaskStates.waiting_for_task_description)
async def process_task_description(message: Message, state: FSMContext, user: User):
    try:
        # Clear any existing description
        await state.update_data(description=message.text)
        
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
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.callback_query(TaskStates.waiting_for_task_due_date)
async def process_deadline_selection(callback: CallbackQuery, state: FSMContext):
    try:
        deadline_type = callback.data.split('_')[1]
        data = await state.get_data()
        
        if deadline_type == 'custom':
            # Show calendar for custom date selection
            calendar = CustomCalendar()
            keyboard = await calendar.start_calendar()
            
            await state.set_state(TaskStates.waiting_for_calendar_selection)
            await callback.message.answer(
                language_manager.get_text("calendar_instructions", callback.from_user.language_code),
                reply_markup=keyboard
            )
        else:
            # Handle predefined deadlines
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if deadline_type == 'tomorrow':
                due_date = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
            elif deadline_type == 'two_days':
                due_date = (now + timedelta(days=2)).replace(hour=23, minute=59, second=59)
            elif deadline_type == 'three_days':
                due_date = (now + timedelta(days=3)).replace(hour=23, minute=59, second=59)
            elif deadline_type == 'five_days':
                due_date = (now + timedelta(days=5)).replace(hour=23, minute=59, second=59)
            elif deadline_type == 'one_week':
                due_date = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59)
            else:
                raise ValueError(f"Invalid deadline type: {deadline_type}")
            
            await state.update_data(due_date=due_date)
            
            try:
                # Create task first
                async with async_session() as session:
                    # Create the task
                    task = Task(
                        team_id=data['team_id'],
                        assignee_id=data['assignee_id'],
                        description=data['description'],
                        due_date=due_date,
                        status="Pending",
                        creator_id=callback.from_user.id
                    )
                    session.add(task)
                    await session.commit()
                    
                    # Get assignee info for notification
                    assignee_query = select(User).where(User.id == data['assignee_id'])
                    assignee_result = await session.execute(assignee_query)
                    assignee = assignee_result.scalar_one_or_none()
                    
                    if assignee:
                        try:
                            await callback.message.bot.send_message(
                                chat_id=assignee.telegram_id,
                                text=language_manager.get_text(
                                    "new_task_assigned",
                                    assignee.language_code,
                                    description=data['description']
                                )
                            )
                        except Exception as e:
                            print(f"Error sending notification to assignee: {e}")
                    
                    # Send success message
                    await callback.message.answer(
                        language_manager.get_text("task_created", callback.from_user.language_code)
                    )
                    
            except Exception as e:
                print(f"Error creating task in database: {e}")
                await callback.message.answer(
                    language_manager.get_text("error_occurred", callback.from_user.language_code) +
                    "\nDatabase error. Please try again."
                )
            finally:
                await state.clear()
        
        await callback.answer()
    except Exception as e:
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code)
        )
        await state.clear()
        await callback.answer()

@router.callback_query(TaskStates.waiting_for_calendar_selection)
async def process_calendar_selection(callback: CallbackQuery, state: FSMContext):
    try:
        calendar = CustomCalendar()
        callback_data = CustomCalendarCallback.unpack(callback.data)
        
        if callback_data.action == "ignore":
            await callback.answer()
            return
            
        if callback_data.action == "day":
            selected_date = datetime(callback_data.year, callback_data.month, callback_data.day)
            if selected_date.date() < datetime.now().date():
                await callback.answer(
                    language_manager.get_text("past_date_error", callback.from_user.language_code),
                    show_alert=True
                )
                return
                
            # Set time to end of day
            due_date = selected_date.replace(hour=23, minute=59, second=59)
            
            # Get current state data and verify it
            current_data = await state.get_data()
            print(f"Current state data before task creation: {current_data}")  # Debug log
            
            if not all(key in current_data for key in ['team_id', 'assignee_id', 'description']):
                print("Missing required data in state")  # Debug log
                await callback.message.answer(
                    language_manager.get_text("error_occurred", callback.from_user.language_code) + 
                    "\nMissing required data. Please start task creation again with /add_task"
                )
                await state.clear()
                return
            
            # Update state with due_date
            await state.update_data(due_date=due_date)
            
            # Get final state data
            final_data = await state.get_data()
            print(f"Final state data for task creation: {final_data}")  # Debug log
            
            try:
                # Create task first
                async with async_session() as session:
                    # Verify team exists
                    team_query = select(Team).where(Team.id == final_data['team_id'])
                    team_result = await session.execute(team_query)
                    team = team_result.scalar_one_or_none()
                    
                    if not team:
                        await callback.message.answer(
                            language_manager.get_text("team_not_found", callback.from_user.language_code)
                        )
                        await state.clear()
                        return
                    
                    # Verify assignee exists and is in team
                    member_query = select(TeamMember).where(
                        TeamMember.team_id == final_data['team_id'],
                        TeamMember.user_id == final_data['assignee_id']
                    )
                    member_result = await session.execute(member_query)
                    member = member_result.scalar_one_or_none()
                    
                    if not member:
                        await callback.message.answer(
                            language_manager.get_text("member_not_found", callback.from_user.language_code)
                        )
                        await state.clear()
                        return
                    
                    # Create the task
                    task = Task(
                        team_id=final_data['team_id'],
                        assignee_id=final_data['assignee_id'],
                        description=final_data['description'],
                        due_date=final_data['due_date'],
                        status="Pending",
                        creator_id=callback.from_user.id  # Add creator_id
                    )
                    session.add(task)
                    await session.commit()
                    
                    # Get assignee info for notification
                    assignee_query = select(User).where(User.id == final_data['assignee_id'])
                    assignee_result = await session.execute(assignee_query)
                    assignee = assignee_result.scalar_one_or_none()
                    
                    if assignee:
                        try:
                            await callback.message.bot.send_message(
                                chat_id=assignee.telegram_id,
                                text=language_manager.get_text(
                                    "new_task_assigned",
                                    assignee.language_code,
                                    description=final_data['description']
                                )
                            )
                        except Exception as e:
                            print(f"Error sending notification to assignee: {e}")
                    
                    # Send success message
                    await callback.message.answer(
                        language_manager.get_text("task_created", callback.from_user.language_code)
                    )
                    
                    # Remove the calendar keyboard only after successful task creation
                    await callback.message.delete_reply_markup()
                    
            except Exception as e:
                print(f"Error creating task in database: {e}")
                await callback.message.answer(
                    language_manager.get_text("error_occurred", callback.from_user.language_code) +
                    "\nDatabase error. Please try again."
                )
            finally:
                await state.clear()
            return
            
        # Handle navigation
        new_year = callback_data.year
        new_month = callback_data.month
        
        if callback_data.action == "prev-year":
            new_year -= 1
        elif callback_data.action == "next-year":
            new_year += 1
        elif callback_data.action == "prev-month":
            if new_month == 1:
                new_month = 12
                new_year -= 1
            else:
                new_month -= 1
        elif callback_data.action == "next-month":
            if new_month == 12:
                new_month = 1
                new_year += 1
            else:
                new_month += 1
                
        # Update calendar view
        keyboard = await calendar.start_calendar(new_year, new_month)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        print(f"Error in calendar selection: {e}")  # Debug logging
        # Get the current state data for debugging
        try:
            state_data = await state.get_data()
            print(f"State data at error: {state_data}")
        except:
            print("Could not get state data")
        
        await callback.message.answer(
            language_manager.get_text("error_occurred", callback.from_user.language_code) +
            "\nPlease try again with /add_task"
        )
        await state.clear()
        await callback.answer()

async def create_task(message: Message, state: FSMContext, language_code: str):
    try:
        data = await state.get_data()
        print(f"Task creation data: {data}")  # Debug log
        
        # Verify we have all required data
        required_fields = ['team_id', 'assignee_id', 'description', 'due_date']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"Missing fields: {missing_fields}")  # Debug log
            await message.answer(
                language_manager.get_text(
                    "missing_fields",
                    language_code,
                    fields=", ".join(missing_fields)
                )
            )
            await state.clear()
            return
        
        async with async_session() as session:
            try:
                # Create the task
                task = Task(
                    team_id=data['team_id'],
                    assignee_id=data['assignee_id'],
                    description=data['description'],
                    due_date=data['due_date'],
                    status="Pending",
                    creator_id=message.from_user.id
                )
                session.add(task)
                await session.commit()
                
                # Get assignee info for notification
                query = select(User).where(User.id == data['assignee_id'])
                result = await session.execute(query)
                assignee = result.scalar_one_or_none()
                
                if assignee:
                    # Send notification to assignee
                    try:
                        await message.bot.send_message(
                            chat_id=assignee.telegram_id,
                            text=language_manager.get_text(
                                "new_task_assigned",
                                assignee.language_code,
                                description=data['description']
                            )
                        )
                    except Exception as e:
                        print(f"Error sending notification to assignee: {e}")
                
                # Send success message
                await message.answer(
                    language_manager.get_text("task_created", language_code)
                )
                
            except Exception as e:
                print(f"Database error in create_task: {e}")
                await session.rollback()
                raise
                
    except Exception as e:
        print(f"Error in create_task: {e}")
        await message.answer(
            language_manager.get_text("error_occurred", language_code)
        )
    finally:
        await state.clear()

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
            # For regular members, show only their tasks
            await show_tasks(callback.message, team_id, user.id, user.role)
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
            await callback.message.answer("You can only view your own tasks.")
            return
    
    # Pass is_manager=True to show_tasks for managers
    await show_tasks(callback.message, team_id, member_id, user.role, is_manager=is_manager)
    await callback.answer()

@router.callback_query(F.data.startswith("view_all_tasks_"))
async def view_all_tasks(callback: CallbackQuery, user: User):
    # Fix the callback data parsing
    data_parts = callback.data.split('_')
    team_id = int(data_parts[3])  # Changed from 2 to 3
    
    async with async_session() as session:
        # Check if user is a manager of this team
        query = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        is_manager = result.scalar_one_or_none() is not None
        
        # Get all tasks for the team
        query = select(Task).where(Task.team_id == team_id)
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        if not tasks:
            await callback.message.answer("No tasks found.")
            return
        
        tasks_text = "📋 Tasks:\n\n"
        for task in tasks:
            remaining_days = get_remaining_days(task.due_date) if task.due_date else None
            due_date_str = f"{task.due_date.strftime('%d.%m.%Y')}({remaining_days} days)" if task.due_date else "No due date"
            status_emoji = {
                "Pending": "📝",
                "In Progress": "🔄",
                "Done": "✅"
            }.get(task.status, "📊")
            
            # Get assignee info
            assignee_query = select(User).where(User.id == task.assignee_id)
            assignee_result = await session.execute(assignee_query)
            assignee = assignee_result.scalar_one_or_none()
            assignee_name = f"{assignee.first_name} {assignee.last_name} (@{assignee.username})" if assignee else "Unknown"
            
            tasks_text += f"🔹 Task ID: {task.id}\n"
            tasks_text += f"👤 Assignee: {assignee_name}\n"
            tasks_text += f"📄 Description: {task.description}\n"
            tasks_text += f"📅 Due Date: {due_date_str}\n"
            tasks_text += f"STATUS: {status_emoji} {task.status}\n"
            tasks_text += "➖➖➖➖➖➖➖➖\n"
            
            # Create status update buttons for each task
            buttons = []
            
            # Show status update button if:
            # 1. User is a manager (can change any status)
            # 2. User is the assignee and task is not Done
            if is_manager or (user.id == task.assignee_id and task.status != "Done"):
                buttons.append(
                    InlineKeyboardButton(
                        text="🔄 In Progress" if task.status == "Pending" else "✅ Done" if task.status == "In Progress" else "📝 To Do",
                        callback_data=f"update_status_{task.id}_{'In Progress' if task.status == 'Pending' else 'Done' if task.status == 'In Progress' else 'Pending'}"
                    )
                )
            
            # Add delete button for managers (always show for managers)
            if is_manager:
                buttons.append(
                    InlineKeyboardButton(
                        text="🗑️ Delete",
                        callback_data=f"delete_task_{task.id}"
                    )
                )
            
            status_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await callback.message.answer(tasks_text, reply_markup=status_keyboard)
            tasks_text = ""  # Clear for next task
        
        await callback.answer()

async def show_tasks(message, team_id: int, member_id: int | None, user_role: UserRole, is_manager: bool = False):
    async with async_session() as session:
        # Build query based on user role and member_id
        query = select(Task).where(Task.team_id == team_id)
        
        # If viewing specific member's tasks
        if member_id is not None:
            query = query.where(Task.assignee_id == member_id)
        # If viewing all tasks (member_id is None) and user is not a manager
        elif user_role != UserRole.MANAGER:
            query = query.where(Task.assignee_id == message.from_user.id)
        
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        if not tasks:
            await message.answer(
                language_manager.get_text("no_tasks", message.from_user.language_code)
            )
            return
        
        # Format tasks
        tasks_text = language_manager.get_text("tasks_header", message.from_user.language_code) + "\n\n"
        for task in tasks:
            remaining_days = get_remaining_days(task.due_date) if task.due_date else None
            due_date_str = f"{task.due_date.strftime('%d.%m.%Y')}({remaining_days} {language_manager.get_text('days', message.from_user.language_code)})" if task.due_date else language_manager.get_text("no_due_date", message.from_user.language_code)
            status_emoji = {
                "Pending": "📝",
                "In Progress": "🔄",
                "Done": "✅"
            }.get(task.status, "📊")
            
            # Get assignee info
            assignee_query = select(User).where(User.id == task.assignee_id)
            assignee_result = await session.execute(assignee_query)
            assignee = assignee_result.scalar_one_or_none()
            assignee_name = f"{assignee.first_name} {assignee.last_name} (@{assignee.username})" if assignee else language_manager.get_text("unknown", message.from_user.language_code)
            
            tasks_text += language_manager.get_text(
                "task_item",
                message.from_user.language_code,
                task_id=task.id,
                assignee=assignee_name,
                description=task.description,
                due_date=due_date_str,
                status=f"{status_emoji} {task.status}"
            )
            
            # Create status update buttons for each task
            buttons = []
            
            # Show status update button if:
            # 1. User is a manager (can change any status)
            # 2. User is the assignee and task is not Done
            if is_manager or (task.assignee_id == member_id and task.status != "Done"):
                next_status = "In Progress" if task.status == "Pending" else "Done" if task.status == "In Progress" else "Pending"
                button_text = language_manager.get_text(
                    f"status_{next_status.lower().replace(' ', '_')}",
                    message.from_user.language_code
                )
                buttons.append(
                    InlineKeyboardButton(
                        text=f"{status_emoji} {button_text}",
                        callback_data=f"update_status_{task.id}_{next_status}"
                    )
                )
            
            # Add delete button for managers (always show for managers)
            if is_manager:
                buttons.append(
                    InlineKeyboardButton(
                        text=language_manager.get_text("delete_task", message.from_user.language_code),
                        callback_data=f"delete_task_{task.id}"
                    )
                )
            
            status_keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await message.answer(tasks_text, reply_markup=status_keyboard)
            tasks_text = ""  # Clear for next task

@router.callback_query(F.data.startswith("update_status_"))
async def update_task_status(callback: CallbackQuery, user: User):
    _, _, task_id, new_status = callback.data.split('_')
    task_id = int(task_id)
    
    async with async_session() as session:
        # Get the task
        query = select(Task).where(Task.id == task_id)
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
        
        # For members (non-managers):
        # 1. Can only update their own tasks
        # 2. Can only change status up to "Done"
        # 3. Cannot change status of tasks that are already "Done"
        if not is_manager:
            if task.assignee_id != user.id:
                await callback.message.answer(
                    language_manager.get_text("update_own_tasks", user.language_code)
                )
                return
            if task.status == "Done":
                await callback.message.answer(
                    language_manager.get_text("completed_tasks_locked", user.language_code)
                )
                return
            if new_status not in ["In Progress", "Done"]:
                await callback.message.answer(
                    language_manager.get_text("status_limit", user.language_code)
                )
                return
        
        # Get assignee info for notification
        assignee_query = select(User).where(User.id == task.assignee_id)
        assignee_result = await session.execute(assignee_query)
        assignee = assignee_result.scalar_one_or_none()
        
        # Get manager info for notification
        manager_query = select(User).join(TeamMember).where(
            TeamMember.team_id == task.team_id,
            TeamMember.role == "Manager"
        )
        manager_result = await session.execute(manager_query)
        manager = manager_result.scalar_one_or_none()
        
        # Update task status
        task.status = new_status
        await session.commit()
        
        # Send notifications based on who made the change
        if notification_system:
            if is_manager and assignee:
                # If manager changed status, notify assignee
                await notification_system.notify_status_change(task, assignee, user, new_status)
            elif not is_manager and manager:
                # If assignee changed status, notify manager
                await notification_system.notify_status_change(task, user, manager, new_status)
        
        # Update the message
        status_emoji = {
            "Pending": "📝",
            "In Progress": "🔄",
            "Done": "✅"
        }.get(new_status, "📊")
        
        remaining_days = get_remaining_days(task.due_date) if task.due_date else None
        due_date_str = f"{task.due_date.strftime('%d.%m.%Y')}({remaining_days} {language_manager.get_text('days', user.language_code)})" if task.due_date else language_manager.get_text("no_due_date", user.language_code)
        
        tasks_text = language_manager.get_text(
            "task_item",
            user.language_code,
            task_id=task.id,
            assignee=f"{assignee.first_name} {assignee.last_name} (@{assignee.username})",
            description=task.description,
            due_date=due_date_str,
            status=f"{status_emoji} {language_manager.get_text(f'status_{new_status.lower().replace(' ', '_')}', user.language_code)}"
        )
        
        # Create new keyboard
        buttons = []
        # Show status update button if:
        # 1. User is a manager (can change any status)
        # 2. User is the assignee and task is not Done
        if is_manager or (user.id == task.assignee_id and new_status != "Done"):
            next_status = "In Progress" if new_status == "Pending" else "Done" if new_status == "In Progress" else "Pending"
            button_text = language_manager.get_text(
                f"status_{next_status.lower().replace(' ', '_')}",
                user.language_code
            )
            buttons.append(
                InlineKeyboardButton(
                    text=f"{status_emoji} {button_text}",
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
        await callback.message.edit_text(tasks_text, reply_markup=keyboard)
        await callback.answer()

@router.callback_query(F.data.startswith("delete_task_"))
async def delete_task(callback: CallbackQuery, user: User):
    task_id = int(callback.data.split('_')[2])
    
    async with async_session() as session:
        # Get the task
        query = select(Task).where(Task.id == task_id)
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
        
        # Delete the task
        await session.delete(task)
        await session.commit()
        
        # Send notification to assignee
        if assignee and notification_system:
            await notification_system.notify_task_deleted(task, assignee, user)
        
        # Delete the message
        await callback.message.delete()
        await callback.answer(
            language_manager.get_text("task_deleted_success", user.language_code)
        )

def get_remaining_days(deadline: datetime) -> int:
    today = datetime.now()
    # Set both dates to midnight to compare only days
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
    remaining = deadline - today
    return max(0, remaining.days) 