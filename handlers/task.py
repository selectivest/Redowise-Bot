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

@router.message(Command("add_task"))
async def cmd_add_task(message: Message, state: FSMContext, user: User):
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

@router.callback_query(TaskStates.waiting_for_team_selection)
async def process_team_selection(callback: CallbackQuery, state: FSMContext):
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
        await callback.message.answer("Select the team member to assign the task to:", reply_markup=keyboard)
        await callback.answer()

@router.callback_query(TaskStates.waiting_for_member_selection)
async def process_member_selection(callback: CallbackQuery, state: FSMContext):
    member_id = int(callback.data.split('_')[1])
    await state.update_data(assignee_id=member_id)
    
    await state.set_state(TaskStates.waiting_for_task_description)
    await callback.message.answer("Please enter the description of the task:")
    await callback.answer()

@router.message(TaskStates.waiting_for_task_description)
async def process_task_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    # Create keyboard with predefined options
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tomorrow", callback_data="deadline_tomorrow")],
        [InlineKeyboardButton(text="2 days later", callback_data="deadline_2days")],
        [InlineKeyboardButton(text="3 days later", callback_data="deadline_3days")],
        [InlineKeyboardButton(text="5 days later", callback_data="deadline_5days")],
        [InlineKeyboardButton(text="A week later", callback_data="deadline_week")],
        [InlineKeyboardButton(text="📅 Choose a date", callback_data="deadline_calendar")]
    ])
    
    await state.set_state(TaskStates.waiting_for_task_due_date)
    await message.answer("Select the due date for the task:", reply_markup=keyboard)

@router.callback_query(TaskStates.waiting_for_task_due_date)
async def process_deadline_selection(callback: CallbackQuery, state: FSMContext, user: User):
    deadline_type = callback.data.split('_')[1]
    
    if deadline_type == 'calendar':
        # Show calendar with basic settings
        calendar = SimpleCalendar(show_alerts=True)
        calendar.set_dates_range(datetime.now(), datetime.now() + timedelta(days=365))
        await state.set_state(TaskStates.waiting_for_calendar_selection)
        await callback.message.answer("Please select a date:", reply_markup=await calendar.start_calendar())
        await callback.answer()
        return
    
    # Calculate the due date based on the selection
    today = datetime.now()
    if deadline_type == 'tomorrow':
        due_date = today + timedelta(days=1)
    elif deadline_type == '2days':
        due_date = today + timedelta(days=2)
    elif deadline_type == '3days':
        due_date = today + timedelta(days=3)
    elif deadline_type == '5days':
        due_date = today + timedelta(days=5)
    elif deadline_type == 'week':
        due_date = today + timedelta(days=7)
    else:
        await callback.message.answer("Invalid selection. Please try again.")
        await callback.answer()
        return
    
    await state.update_data(due_date=due_date)
    await create_task(callback.message, state, user)
    await callback.answer()

@router.callback_query(SimpleCalendarCallback.filter(), TaskStates.waiting_for_calendar_selection)
async def process_calendar_selection(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext, user: User):
    # Show calendar with basic settings
    calendar = SimpleCalendar(show_alerts=True)
    calendar.set_dates_range(datetime.now(), datetime.now() + timedelta(days=365))
    
    selected, date = await calendar.process_selection(callback, callback_data)
    
    if selected:
        await state.update_data(due_date=date)
        await create_task(callback.message, state, user)
        await callback.answer()
    else:
        try:
            await callback.message.edit_reply_markup(reply_markup=await calendar.start_calendar())
            await callback.answer()
        except Exception as e:
            # If the message is not modified, just ignore the error
            if "message is not modified" not in str(e):
                raise e
            await callback.answer()

async def create_task(message: Message, state: FSMContext, user: User):
    data = await state.get_data()
    
    async with async_session() as session:
        task = Task(
            description=data['description'],
            due_date=data['due_date'],
            team_id=data['team_id'],
            creator_id=user.id,
            assignee_id=data['assignee_id'],
            status="To Do"
        )
        session.add(task)
        await session.commit()
        
        # Get assignee info for notification
        assignee_query = select(User).where(User.id == data['assignee_id'])
        assignee_result = await session.execute(assignee_query)
        assignee = assignee_result.scalar_one_or_none()
        
        # Get manager info for notification
        manager_query = select(User).join(TeamMember).where(
            TeamMember.team_id == data['team_id'],
            TeamMember.role == "Manager"
        )
        manager_result = await session.execute(manager_query)
        manager = manager_result.scalar_one_or_none()
        
        # Send notification to assignee
        if assignee and notification_system:
            await notification_system.notify_new_task(task, assignee)
            
            # Schedule due date reminder
            due_date = data['due_date']
            if due_date:
                # Calculate reminder date (day before due date)
                reminder_date = due_date - timedelta(days=1)
                if reminder_date > datetime.now():
                    # Calculate delay until 9 AM on the reminder date
                    reminder_time = datetime.combine(reminder_date.date(), time(9, 0))
                    if reminder_time > datetime.now():
                        delay = (reminder_time - datetime.now()).total_seconds()
                        asyncio.create_task(
                            notification_system.schedule_due_date_reminder(task, assignee, delay)
                        )
        
        # Send notifications based on who made the change
        if notification_system:
            if manager and assignee:
                # If manager changed status, notify assignee
                await notification_system.notify_status_change(task, assignee, user, data['status'])
            elif not manager and assignee:
                # If assignee changed status, notify manager
                await notification_system.notify_status_change(task, user, manager, data['status'])
    
    await state.clear()
    await message.answer(f"Task has been created successfully!")

@router.message(Command("tasks"))
async def cmd_tasks(message: Message, user: User):
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
                await callback.message.answer("No members found in this team.")
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
                    text="👥 All Members",
                    callback_data=f"view_all_tasks_{team_id}"
                )
            ])
            
            await callback.message.answer("Select a team member to view their tasks:", reply_markup=keyboard)
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
        
        if not is_manager:
            await callback.message.answer("Only managers can view other members' tasks.")
            return
    
    await show_tasks(callback.message, team_id, member_id, user.role)
    await callback.answer()

@router.callback_query(F.data.startswith("view_all_tasks_"))
async def view_all_tasks(callback: CallbackQuery, user: User):
    # Fix the callback data parsing
    data_parts = callback.data.split('_')
    team_id = int(data_parts[3])  # Changed from 2 to 3
    
    print(f"Viewing all tasks for team {team_id}")
    print(f"User ID: {user.id}")
    print(f"User Role: {user.role}")
    
    async with async_session() as session:
        # Check if user is a manager of this team
        query = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        result = await session.execute(query)
        is_manager = result.scalar_one_or_none() is not None
        
        print(f"Is manager: {is_manager}")
        
        if not is_manager:
            await callback.message.answer("Only managers can view all tasks.")
            return
        
        # Get all tasks for the team
        query = select(Task).where(Task.team_id == team_id)
        print(f"Query: {query}")
        result = await session.execute(query)
        tasks = result.scalars().all()
        
        print(f"Found {len(tasks)} tasks")
        
        if not tasks:
            await callback.message.answer("No tasks found.")
            return
        
        # Format tasks
        tasks_text = "📋 Tasks:\n\n"
        for task in tasks:
            print(f"Task ID: {task.id}")
            print(f"Task Status: {task.status}")
            print(f"Task Assignee: {task.assignee_id}")
            
            remaining_days = get_remaining_days(task.due_date) if task.due_date else None
            due_date_str = f"{task.due_date.strftime('%d.%m.%Y')}({remaining_days} days)" if task.due_date else "No due date"
            status_emoji = {
                "To Do": "📝",
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
            
            # Add status update button
            buttons.append(
                InlineKeyboardButton(
                    text="🔄 In Progress" if task.status == "To Do" else "✅ Done" if task.status == "In Progress" else "📝 To Do",
                    callback_data=f"update_status_{task.id}_{'In Progress' if task.status == 'To Do' else 'Done' if task.status == 'In Progress' else 'To Do'}"
                )
            )
            
            # Add delete button for managers
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

async def show_tasks(message, team_id: int, member_id: int | None, user_role: UserRole):
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
            await message.answer("No tasks found.")
            return
        
        # Check if user is a manager of this team
        team_member_query = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == message.from_user.id,
            TeamMember.role == "Manager"
        )
        team_member_result = await session.execute(team_member_query)
        is_manager = team_member_result.scalar_one_or_none() is not None
        
        # Format tasks
        tasks_text = "📋 Tasks:\n\n"
        for task in tasks:
            remaining_days = get_remaining_days(task.due_date) if task.due_date else None
            due_date_str = f"{task.due_date.strftime('%d.%m.%Y')}({remaining_days} days)" if task.due_date else "No due date"
            status_emoji = {
                "To Do": "📝",
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
            # 2. Task is not Done (members can change non-completed tasks)
            # 3. User is the assignee and task is To Do (members can update their own tasks from To Do)
            if is_manager or task.status != "Done" or (message.from_user.id == task.assignee_id and task.status == "To Do"):
                buttons.append(
                    InlineKeyboardButton(
                        text="🔄 In Progress" if task.status == "To Do" else "✅ Done" if task.status == "In Progress" else "📝 To Do",
                        callback_data=f"update_status_{task.id}_{'In Progress' if task.status == 'To Do' else 'Done' if task.status == 'In Progress' else 'To Do'}"
                    )
                )
            
            # Add delete button for managers
            if is_manager:
                buttons.append(
                    InlineKeyboardButton(
                        text="🗑️ Delete",
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
            await callback.message.answer("Task not found.")
            return
        
        # Check if user is a manager of the team
        team_member_query = select(TeamMember).where(
            TeamMember.team_id == task.team_id,
            TeamMember.user_id == user.id,
            TeamMember.role == "Manager"
        )
        team_member_result = await session.execute(team_member_query)
        is_manager = team_member_result.scalar_one_or_none() is not None
        
        # Check if user is the assignee or a manager
        if task.assignee_id != user.id and not is_manager:
            await callback.message.answer("You can only update your own tasks.")
            return
        
        # Prevent non-managers from changing Done status
        if task.status == "Done" and not is_manager:
            await callback.message.answer("Only managers can change the status of completed tasks.")
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
            "To Do": "📝",
            "In Progress": "🔄",
            "Done": "✅"
        }.get(new_status, "📊")
        
        remaining_days = get_remaining_days(task.due_date) if task.due_date else None
        due_date_str = f"{task.due_date.strftime('%d.%m.%Y')}({remaining_days} days)" if task.due_date else "No due date"
        
        tasks_text = f"🔹 Task ID: {task.id}\n"
        tasks_text += f"👤 Assignee: {assignee.first_name} {assignee.last_name} (@{assignee.username})\n"
        tasks_text += f"📄 Description: {task.description}\n"
        tasks_text += f"📅 Due Date: {due_date_str}\n"
        tasks_text += f"STATUS: {status_emoji} {new_status}\n"
        tasks_text += "➖➖➖➖➖➖➖➖\n"
        
        # Create new keyboard
        buttons = []
        # Show status update button if:
        # 1. User is a manager (can change any status)
        # 2. Task is not Done (members can change non-completed tasks)
        # 3. User is the assignee and task is To Do (members can update their own tasks from To Do)
        if is_manager or new_status != "Done" or (user.id == task.assignee_id and new_status == "To Do"):
            buttons.append(
                InlineKeyboardButton(
                    text="🔄 In Progress" if new_status == "To Do" else "✅ Done" if new_status == "In Progress" else "📝 To Do",
                    callback_data=f"update_status_{task.id}_{'In Progress' if new_status == 'To Do' else 'Done' if new_status == 'In Progress' else 'To Do'}"
                )
            )
        
        if is_manager:
            buttons.append(
                InlineKeyboardButton(
                    text="🗑️ Delete",
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
            await callback.message.answer("Task not found.")
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
            await callback.message.answer("Only team managers can delete tasks.")
            return
        
        # Delete the task
        await session.delete(task)
        await session.commit()
        
        # Delete the message
        await callback.message.delete()
        await callback.answer("Task deleted successfully!")

def get_remaining_days(due_date: datetime) -> int:
    today = datetime.now()
    # Set both dates to midnight to compare only days
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    due_date = due_date.replace(hour=0, minute=0, second=0, microsecond=0)
    remaining = due_date - today
    return max(0, remaining.days) 