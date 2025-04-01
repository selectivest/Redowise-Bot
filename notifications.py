from aiogram import Bot
from datetime import datetime, time, timedelta
import asyncio
from database.models import User, Task
from database.connection import async_session
from sqlalchemy import select
from collections import defaultdict
import random
from languages.manager import language_manager

class NotificationSystem:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.notification_tasks = []
        self.queued_notifications = defaultdict(list)  # Store notifications by user_id
        self.quiet_start = time(1, 0)   # 1:00 AM
        self.quiet_end = time(7, 0)     # 7:00 AM
        self.is_quiet_hours = False

    def is_quiet_time(self, current_time: datetime) -> bool:
        """Check if current time is within quiet hours"""
        current = current_time.time()
        # Handle the case when quiet hours span across midnight (1 AM to 7 AM)
        if self.quiet_start > self.quiet_end:
            return current >= self.quiet_start or current < self.quiet_end
        return self.quiet_start <= current < self.quiet_end

    async def start(self):
        """Start all notification tasks"""
        # Start daily morning notification
        self.notification_tasks.append(
            asyncio.create_task(self.daily_morning_notification())
        )
        # Start notification delivery task
        self.notification_tasks.append(
            asyncio.create_task(self.deliver_queued_notifications())
        )

    async def stop(self):
        """Stop all notification tasks"""
        for task in self.notification_tasks:
            task.cancel()
        self.notification_tasks.clear()

    async def send_notification(self, user_id: int, message: str, lang_code: str = 'en'):
        """Send notification or queue it if in quiet hours"""
        try:
            now = datetime.now()
            if self.is_quiet_time(now):
                # Queue the notification
                self.queued_notifications[user_id].append(message)
            else:
                # Send immediately
                await self.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Error sending notification: {e}")
            # If sending fails, queue the notification
            self.queued_notifications[user_id].append(message)

    async def notify_new_task(self, task: Task, assignee: User):
        """Send notification when a new task is assigned"""
        message = language_manager.get_text(
            "new_task",
            assignee.language_code,
            task_id=task.id,
            description=task.description,
            due_date=task.due_date.strftime('%d.%m.%Y')
        )
        await self.send_notification(assignee.telegram_id, message, assignee.language_code)

    async def notify_status_change(self, task: Task, assignee: User, manager: User, new_status: str):
        """Send notification when task status changes"""
        # Notify manager when assignee changes status
        manager_message = language_manager.get_text(
            "status_change_manager",
            manager.language_code,
            task_id=task.id,
            assignee_name=f"{assignee.first_name} {assignee.last_name}",
            description=task.description,
            due_date=task.due_date.strftime('%d.%m.%Y'),
            new_status=new_status
        )
        await self.send_notification(manager.telegram_id, manager_message, manager.language_code)

        # Notify assignee when manager changes status
        assignee_message = language_manager.get_text(
            "status_change_assignee",
            assignee.language_code,
            task_id=task.id,
            description=task.description,
            due_date=task.due_date.strftime('%d.%m.%Y'),
            new_status=new_status
        )
        await self.send_notification(assignee.telegram_id, assignee_message, assignee.language_code)

    async def notify_task_deleted(self, task: Task, assignee: User, deleted_by: User):
        """Send notification when a task is deleted"""
        message = language_manager.get_text(
            "task_deleted",
            assignee.language_code,
            task_id=task.id,
            description=task.description,
            due_date=task.due_date.strftime('%d.%m.%Y'),
            status=task.status,
            deleted_by=f"{deleted_by.first_name} {deleted_by.last_name}"
        )
        await self.send_notification(assignee.telegram_id, message, assignee.language_code)

    async def notify_due_date_reminder(self, task: Task, assignee: User):
        """Send notification one day before due date"""
        message = language_manager.get_text(
            "due_date_reminder",
            assignee.language_code,
            task_id=task.id,
            description=task.description,
            due_date=task.due_date.strftime('%d.%m.%Y'),
            status=task.status
        )
        await self.send_notification(assignee.telegram_id, message, assignee.language_code)

    async def deliver_queued_notifications(self):
        """Deliver queued notifications when quiet hours end"""
        while True:
            try:
                now = datetime.now()
                if self.is_quiet_time(now):
                    # Wait until quiet hours end
                    if now.time() >= self.quiet_start:
                        # If we're past quiet start, wait until quiet end
                        wait_seconds = (
                            datetime.combine(now.date(), self.quiet_end) + 
                            timedelta(days=1) - now
                        ).total_seconds()
                    else:
                        # If we're before quiet start, wait until quiet end
                        wait_seconds = (
                            datetime.combine(now.date(), self.quiet_end) - now
                        ).total_seconds()
                    
                    await asyncio.sleep(wait_seconds)
                
                # Deliver all queued notifications
                for user_id, messages in self.queued_notifications.items():
                    if messages:
                        # Get user's language preference
                        async with async_session() as session:
                            user = await session.get(User, user_id)
                            if user:
                                lang_code = user.language_code
                            else:
                                lang_code = 'en'
                        
                        # Combine all messages for this user
                        combined_message = language_manager.get_text(
                            "queued_notifications",
                            lang_code,
                            notifications="\n\n".join(messages)
                        )
                        await self.bot.send_message(user_id, combined_message)
                        # Clear the queue for this user
                        self.queued_notifications[user_id] = []
                
                # Wait a minute before checking again
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error delivering queued notifications: {e}")
                await asyncio.sleep(60)

    async def daily_morning_notification(self):
        """Send daily morning notification with open tasks"""
        while True:
            try:
                # Get current time
                now = datetime.now()
                target_time = time(8, 0)  # 8:00 AM
                
                # Calculate time until next notification
                if now.time() < target_time:
                    # If it's before 8 AM, wait until 8 AM
                    wait_seconds = (
                        datetime.combine(now.date(), target_time) - now
                    ).total_seconds()
                else:
                    # If it's after 8 AM, wait until 8 AM tomorrow
                    wait_seconds = (
                        datetime.combine(now.date(), target_time) + 
                        timedelta(days=1) - now
                    ).total_seconds()
                
                # Wait until next notification time
                await asyncio.sleep(wait_seconds)
                
                # Get all users with open tasks
                async with async_session() as session:
                    # Get all tasks that are not Done
                    query = select(Task).where(Task.status != "Done")
                    result = await session.execute(query)
                    tasks = result.scalars().all()
                    
                    # Group tasks by assignee
                    tasks_by_assignee = {}
                    for task in tasks:
                        if task.assignee_id not in tasks_by_assignee:
                            tasks_by_assignee[task.assignee_id] = []
                        tasks_by_assignee[task.assignee_id].append(task)
                    
                    # Send notifications to each user
                    for assignee_id, user_tasks in tasks_by_assignee.items():
                        # Get user info
                        user_query = select(User).where(User.id == assignee_id)
                        user_result = await session.execute(user_query)
                        user = user_result.scalar_one_or_none()
                        
                        if user:
                            # Format tasks list
                            tasks_text = ""
                            for task in user_tasks:
                                remaining_days = (
                                    task.due_date.date() - datetime.now().date()
                                ).days
                                tasks_text += language_manager.get_text(
                                    "task_item",
                                    user.language_code,
                                    task_id=task.id,
                                    description=task.description,
                                    due_date=task.due_date.strftime('%d.%m.%Y'),
                                    remaining_days=remaining_days,
                                    status=task.status
                                )
                            
                            # Send daily tasks notification
                            message = language_manager.get_text(
                                "daily_tasks",
                                user.language_code,
                                tasks=tasks_text
                            )
                            await self.send_notification(user.telegram_id, message, user.language_code)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in daily notification: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def schedule_due_date_reminder(self, task: Task, assignee: User, delay: float):
        """Schedule due date reminder with random time between 9 AM and 10 AM"""
        try:
            # Wait until the specified delay
            await asyncio.sleep(delay)
            
            # Generate random time between 9 AM and 10 AM
            random_minutes = random.randint(0, 60)
            reminder_time = time(9, random_minutes)
            
            # Wait until the random time
            now = datetime.now()
            if now.time() < reminder_time:
                wait_seconds = (
                    datetime.combine(now.date(), reminder_time) - now
                ).total_seconds()
                await asyncio.sleep(wait_seconds)
            
            # Send the reminder
            await self.notify_due_date_reminder(task, assignee)
            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in due date reminder: {e}") 