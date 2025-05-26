from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
from taskmanager.services.transcription import transcription_service

router = Router()
notification_system = None

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
                language_manager.get_text("continue_adding", user.language_code)
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
        # Get current state data
        current_data = await state.get_data()
        current_description = current_data.get('description', '')
        current_media_type = current_data.get('media_type')
        current_media_file_id = current_data.get('media_file_id')
        current_media_caption = current_data.get('media_caption', '')

        # Handle different types of messages
        if message.voice:
            try:
                # For voice messages, we'll store the file_id and transcribe it
                voice_file = await message.bot.get_file(message.voice.file_id)
                voice_bytes = await message.bot.download_file(voice_file.file_path)
                
                # Show processing message
                processing_msg = await message.answer(
                    language_manager.get_text("processing_voice", user.language_code)
                )
                
                # Transcribe the voice message
                if transcription_service:
                    transcribed_text = await transcription_service.transcribe_voice(voice_bytes)
                    if transcribed_text:
                        # Update description with transcribed text
                        if current_description:
                            current_description += "\n\n" + transcribed_text
                        else:
                            current_description = transcribed_text
                        
                        # Update processing message
                        await processing_msg.edit_text(
                            language_manager.get_text("voice_transcribed", user.language_code)
                        )
                    else:
                        await processing_msg.edit_text(
                            language_manager.get_text("transcription_failed", user.language_code)
                        )
                else:
                    await processing_msg.edit_text(
                        language_manager.get_text("transcription_not_available", user.language_code)
                    )
                
                # Store voice message info
                await state.update_data(
                    media_type="voice",
                    media_file_id=message.voice.file_id,
                    description=current_description,
                    media_caption=message.caption or current_media_caption
                )
                
                # Show media added confirmation
                await message.answer(
                    language_manager.get_text("media_added", user.language_code)
                )
            except Exception as e:
                print(f"Error processing voice message: {e}")
                await message.answer(
                    language_manager.get_text("error_occurred", user.language_code)
                )
                return
            
        elif message.photo:
            try:
                # For photos, store the largest photo file_id
                photo = message.photo[-1]  # Get the largest photo
                if current_description:
                    current_description += "\n\n" + (message.caption or "")
                else:
                    current_description = message.caption or ""
                
                await state.update_data(
                    media_type="photo",
                    media_file_id=photo.file_id,
                    description=current_description,
                    media_caption=message.caption or current_media_caption
                )
                
                # Show media added confirmation
                await message.answer(
                    language_manager.get_text("media_added", user.language_code)
                )
            except Exception as e:
                print(f"Error processing photo: {e}")
                await message.answer(
                    language_manager.get_text("error_occurred", user.language_code)
                )
                return
            
        elif message.video:
            try:
                # For videos, store the video file_id
                if current_description:
                    current_description += "\n\n" + (message.caption or "")
                else:
                    current_description = message.caption or ""
                
                await state.update_data(
                    media_type="video",
                    media_file_id=message.video.file_id,
                    description=current_description,
                    media_caption=message.caption or current_media_caption
                )
                
                # Show media added confirmation
                await message.answer(
                    language_manager.get_text("media_added", user.language_code)
                )
            except Exception as e:
                print(f"Error processing video: {e}")
                await message.answer(
                    language_manager.get_text("error_occurred", user.language_code)
                )
                return
            
        elif message.text:
            try:
                # For text messages, append to existing description
                if current_description:
                    current_description += "\n\n" + message.text
                else:
                    current_description = message.text
                
                await state.update_data(
                    media_type=current_media_type,  # Keep existing media type
                    media_file_id=current_media_file_id,  # Keep existing media file
                    description=current_description,
                    media_caption=current_media_caption  # Keep existing caption
                )
                
                # Show description updated confirmation
                await message.answer(
                    language_manager.get_text("description_updated", user.language_code)
                )
            except Exception as e:
                print(f"Error processing text message: {e}")
                await message.answer(
                    language_manager.get_text("error_occurred", user.language_code)
                )
                return
        else:
            # Unsupported message type
            await message.answer(
                language_manager.get_text("unsupported_message_type", user.language_code)
            )
            return

        try:
            # Create inline keyboard for description management
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=language_manager.get_text("finish_description", user.language_code),
                        callback_data="finish_description"
                    )
                ]
            ])
            
            # Show current description preview
            preview_text = language_manager.get_text(
                "description_preview",
                user.language_code,
                description=current_description[:500] + "..." if len(current_description) > 500 else current_description
            )
            await message.answer(preview_text, reply_markup=keyboard)
        except Exception as e:
            print(f"Error showing description preview: {e}")
            await message.answer(
                language_manager.get_text("error_occurred", user.language_code)
            )
            await state.clear()
            
    except Exception as e:
        print(f"Error in process_task_description: {e}")
        await message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()

@router.callback_query(F.data == "finish_description")
async def finish_description(callback: CallbackQuery, state: FSMContext, user: User):
    try:
        # Get current state data
        data = await state.get_data()
        if not data.get('description'):
            await callback.message.answer(
                language_manager.get_text("empty_description", user.language_code)
            )
            await callback.answer()
            return

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
        
        # Move to deadline selection state
        await state.set_state(TaskStates.waiting_for_task_due_date)
        await callback.message.answer(
            language_manager.get_text("select_due_date", user.language_code),
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        print(f"Error in finish_description: {e}")
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
        await state.clear()
        await callback.answer()

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
                # Get state data including media information
                data = await state.get_data()
                
                # Create task with media information
                task = await create_task_with_media(
                        team_id=data['team_id'],
                        assignee_id=data['assignee_id'],
                        description=data['description'],
                        due_date=due_date,
                    creator_id=callback.from_user.id,
                    media_type=data.get('media_type'),
                    media_file_id=data.get('media_file_id'),
                    media_caption=data.get('media_caption'),
                    language_code=user.language_code
                )
                
                if task and notification_system:
                    # Get assignee info for notification
                    assignee_query = select(User).where(User.id == data['assignee_id'])
                    assignee_result = await session.execute(assignee_query)
                    assignee = assignee_result.scalar_one_or_none()
                    
                    if assignee:
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
                await callback.answer()
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
                
                # Get state data including media information
                data = await state.get_data()
                
                if not all(key in data for key in ['team_id', 'assignee_id', 'description']):
                    print("Missing required data in state")  # Debug log
                    await callback.message.answer(
                        language_manager.get_text("error_occurred", user.language_code) + 
                        "\nMissing required data. Please start task creation again with /add_task"
                    )
                    await state.clear()
                    await callback.answer()
                    return
                
                try:
                    # Create task with media information
                    task = await create_task_with_media(
                        team_id=data['team_id'],
                        assignee_id=data['assignee_id'],
                        description=data['description'],
                        due_date=selected_date,
                        creator_id=user.id,
                        media_type=data.get('media_type'),
                        media_file_id=data.get('media_file_id'),
                        media_caption=data.get('media_caption'),
                        language_code=user.language_code
                    )
                    
                    if task and notification_system:
                        # Get assignee info for notification
                        assignee_query = select(User).where(User.id == data['assignee_id'])
                        assignee_result = await session.execute(assignee_query)
                        assignee = assignee_result.scalar_one_or_none()
                        
                        if assignee:
                            await notification_system.notify_new_task(task, assignee)
                            
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
                    await callback.answer()
            
    except Exception as e:
        print(f"Error in calendar selection: {e}")  # Debug logging
        # Get the current state data for debugging
        try:
            state_data = await state.get_data()
            print(f"State data at error: {state_data}")
        except Exception as e:
            print(f"Could not get state data: {e}")
        
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
            
            # Create the task
            task = Task(
                team_id=team_id,
                assignee_id=assignee_id,
                description=description,
                due_date=due_date,
                status="pending",
                creator_id=creator_id
            )
            
            session.add(task)
            await session.commit()
            await session.refresh(task, ['team'])
            
            print(f"Debug: Task created with language code: {language_code}")  # Debug log
            return task
            
    except Exception as e:
        print(f"Error in create_task: {e}")
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
    
    try:
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
                    await callback.answer()
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
                return
            
            # For regular members, show only their tasks
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
                await callback.answer()
                return
            
            # Send header first
            await callback.message.answer(
                language_manager.get_text("tasks_header", user.language_code)
            )
            
            # Send each task
            for task in tasks:
                task_text, keyboard = await format_task_message(task, user, user.language_code)
                await send_task_with_media(callback.message, task, task_text, keyboard)
            
            await callback.answer()
            
    except Exception as e:
        print(f"Error in view_team_tasks: {e}")
        await callback.message.answer(
            language_manager.get_text("error_occurred", user.language_code)
        )
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
            task_text, keyboard = await format_task_message(task, user, user.language_code)
            await send_task_with_media(callback.message, task, task_text, keyboard)
        
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
            task_text, keyboard = await format_task_message(task, user, language_code)
            await send_task_with_media(message, task, task_text, keyboard)

@router.callback_query(F.data.startswith("update_status_"))
async def update_task_status(callback: CallbackQuery, user: User):
    try:
        # Fix callback data parsing to handle status with underscores
        data_parts = callback.data.split('_', 3)  # Split only first 3 underscores
        task_id = int(data_parts[2])
        new_status = data_parts[3]  # This will keep "in_progress" intact
        
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
            
            # For members (non-managers):
            # 1. Can only update their own tasks
            # 2. Can only change status up to "done"
            # 3. Cannot change status of tasks that are already "done"
            if not is_manager:
                if task.assignee_id != user.id:
                    await callback.message.answer(
                        language_manager.get_text("update_own_tasks", user.language_code)
                    )
                    return
                if task.status.lower() == "done":
                    await callback.message.answer(
                        language_manager.get_text("completed_tasks_locked", user.language_code)
                    )
                    return
                if new_status not in ["in_progress", "done"]:
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
            if is_manager and assignee:
                # If manager changed status, notify assignee
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
            current_status_emoji = status_emoji.get(new_status.lower(), "📊")
            status_key = {
                'pending': 'status_pending',
                'in_progress': 'status_in_progress',
                'done': 'status_done'
            }[new_status.lower()]
            translated_status = f"{current_status_emoji} {language_manager.get_text(status_key, user.language_code)}"
            
            # Log the values being passed
            print(f"Update status values - task_id: {task.id}, team_name: {task.team.name if task.team else 'None'}, description: {task.description}, due_date: {due_date_str}, status: {translated_status}")
            
            # Format task text
            task_text, keyboard = await format_task_message(task, user, user.language_code)
            
            # Send task message with media if any
            await send_task_with_media(callback.message, task, task_text, keyboard)
            await callback.answer()
    except Exception as e:
        print(f"Error in update_task_status: {e}")
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

async def create_task_with_media(
    team_id: int,
    description: str,
    due_date: datetime,
    creator_id: int,
    assignee_id: int,
    media_type: str | None,
    media_file_id: str | None,
    media_caption: str | None,
    language_code: str
) -> Optional[Task]:
    try:
        async with async_session() as session:
            task = Task(
                team_id=team_id,
                assignee_id=assignee_id,
                description=description,
                due_date=due_date,
                status="pending",
                creator_id=creator_id,
                media_type=media_type,
                media_file_id=media_file_id,
                media_caption=media_caption
            )
            session.add(task)
            await session.commit()
            await session.refresh(task, ['team'])
            return task
    except Exception as e:
        print(f"Error in create_task_with_media: {e}")
        return None

async def format_task_message(task: Task, user: User, language_code: str) -> tuple[str, InlineKeyboardMarkup]:
    """Helper function to format task message and keyboard"""
    # Format due date
    due_date_str = task.due_date.strftime('%d.%m.%Y') if task.due_date else language_manager.get_text("no_due_date", language_code)
    
    # Get translated status
    status_map = {
        "pending": "status_pending",
        "in_progress": "status_in_progress",
        "done": "status_done"
    }
    translated_status = language_manager.get_text(status_map[task.status.lower()], language_code)
    
    # Format task text
    task_text = language_manager.get_text(
        "task_item",
        language_code,
        team_name=task.team.name if task.team else language_manager.get_text("unknown", language_code),
        task_id=str(task.id),
        assignee=f"{user.first_name} {user.last_name} (@{user.username})",
        description=task.description,
        due_date=due_date_str,
        status=translated_status
    )
    
    # Add media caption if exists
    if task.media_caption:
        task_text += f"\n\n📎 Media caption:\n{task.media_caption}"
    
    # Create status update buttons
    buttons = []
    if task.status.lower() != "done":
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
            language_code
        )
        buttons.append(
            InlineKeyboardButton(
                text=f"{next_status_emoji} {button_text}",
                callback_data=f"update_status_{task.id}_{next_status}"
            )
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
    return task_text, keyboard

async def send_task_with_media(message: Message, task: Task, task_text: str, keyboard: InlineKeyboardMarkup | None = None):
    """Helper function to send task message with media if any"""
    if task.media_type == "photo" and task.media_file_id:
        await message.answer_photo(
            photo=task.media_file_id,
            caption=task_text,
            reply_markup=keyboard
        )
    elif task.media_type == "video" and task.media_file_id:
        await message.answer_video(
            video=task.media_file_id,
            caption=task_text,
            reply_markup=keyboard
        )
    elif task.media_type == "voice" and task.media_file_id:
        await message.answer_voice(
            voice=task.media_file_id,
            caption=task_text,
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=task_text,
            reply_markup=keyboard
        ) 