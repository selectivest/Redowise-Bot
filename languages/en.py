from typing import Dict

translations: Dict[str, str] = {
    # General
    "welcome": "👋 Welcome to the Task Management Bot!\n\nI'm here to help you manage tasks and teams efficiently.\n\nWhat you can do:\n1️⃣ Create and manage teams\n2️⃣ Assign and track tasks\n3️⃣ Collaborate with team members\n\nUse /menu to see the main menu or /help for detailed instructions.\nUse /show_keyboard to show the keyboard menu.",
    "select_language": "Please select your preferred language:",
    "language_changed": "Language has been changed to English",
    "main_menu": "🎯 Main Menu\n\nSelect an option:",
    
    # Menu
    "create_team": "Create Team",
    "join_team": "Join Team",
    "my_tasks": "My Tasks",
    "settings": "Settings",
    
    # Team
    "team_created": "Team has been created successfully! You are now the manager of this team.",
    "team_name_prompt": "Please enter the name for your new team:",
    "team_join_code": "Team join code: {code}",
    "team_joined": "✅ You have joined team '{team_name}'!\n\nManager: @{manager_username}",
    "member_username_prompt": "Please enter the Telegram username of the new member:",
    "select_team": "Select the team to add the member to:",
    "user_not_found": "User not found. Please make sure they have registered with the bot first.",
    "user_not_started_bot": "Error: @{username} hasn't started the bot yet. Please ask them to start the bot with /start first.",
    "team_invitation": "👋 You have been invited to join team '{team_name}'!\n\nManager: @{manager_username}\n\nWould you like to accept the invitation?",
    "invitation_sent": "Invitation has been sent to @{username}",
    "invitation_send_error": "Error: Cannot send invitation to @{username}. Please make sure they have started the bot and try again.",
    "invalid_invitation": "Invalid or expired invitation.",
    "member_accepted": "✅ @{username} has accepted the invitation to join team '{team_name}'!",
    "member_declined": "❌ @{username} has declined the invitation to join team '{team_name}'.",
    "invitation_declined": "❌ You have declined the invitation to join team '{team_name}'.",
    "accept": "✅ Accept",
    "reject": "❌ Reject",
    
    # Tasks
    "task_created": "Task has been created successfully!",
    "task_assigned": "Task has been assigned to {user}",
    "task_completed": "Task has been marked as completed",
    "task_status": "Task status: {status}",
    "not_in_team": "You need to be a member of a team first.",
    "select_team_view": "Select a team to view tasks:",
    "select_member": "Select the team member to assign the task to:",
    "enter_task_description": "Please enter the description of the task:",
    "select_due_date": "Select the due date for the task:",
    "tomorrow": "Tomorrow",
    "two_days": "2 days later",
    "three_days": "3 days later",
    "five_days": "5 days later",
    "one_week": "A week later",
    "choose_date": "📅 Choose a date",
    "missing_fields": "Error: Missing required data: {fields}",
    "no_tasks": "No tasks found.",
    "no_members": "No members found in this team.",
    "select_member_view": "Select a team member to view their tasks:",
    "all_members": "👥 All Members",
    "own_tasks_only": "You can only view your own tasks.",
    "update_own_tasks": "You can only update your own tasks.",
    "completed_tasks_locked": "Only managers can change the status of completed tasks.",
    "status_limit": "You can only change task status to 'In Progress' or 'Done'.",
    "task_not_found": "Task not found.",
    "error_occurred": "An error occurred. Please try again.",
    
    # Status
    "status_pending": "To Do",
    "status_in_progress": "In Progress",
    "status_completed": "Done",
    
    # Notifications
    "new_task": "📝 New task assigned!\n\n🔹 Task ID: {task_id}\n📄 Description: {description}\n📅 Due Date: {due_date}\nStatus: To Do",
    "status_change_manager": "🔄 Task status updated!\n\n🔹 Task ID: {task_id}\n👤 Assignee: {assignee_name}\n📄 Description: {description}\n📅 Due Date: {due_date}\nNew Status: {new_status}",
    "status_change_assignee": "🔄 Your task status has been updated!\n\n🔹 Task ID: {task_id}\n📄 Description: {description}\n📅 Due Date: {due_date}\nNew Status: {new_status}",
    "task_deleted": "🗑️ Task deleted\n\n🔹 Task ID: {task_id}\n📄 Description: {description}\n📅 Due Date: {due_date}\nStatus: {status}\nDeleted by: {deleted_by}",
    "due_date_reminder": "⚠️ Task due tomorrow!\n\n🔹 Task ID: {task_id}\n📄 Description: {description}\n📅 Due Date: {due_date}\nStatus: {status}",
    "daily_tasks": "📋 Your tasks for today:\n\n{tasks}",
    "task_item": "🔹 Task ID: {task_id}\n\n👤 Assignee: {assignee}\n\n📄 Description: {description}\n\n📅 Due Date: {due_date}\n\nSTATUS: {status}\n\n➖➖➖➖➖➖➖➖\n",
    "queued_notifications": "📋 Your new notifications:\n\n{notifications}",
    
    # Errors
    "error_occurred": "An error occurred. Please try again.",
    "invalid_input": "Invalid input. Please try again.",
    "not_authorized": "You need to be a team manager to add new members. Create a team first using /create_team.",
    
    # Calendar
    "calendar_instructions": "Please select a date:\n🔵 Today\n❌ Disabled dates (past or beyond 1 year)\n📅 Available dates",
    
    # Tasks List
    "tasks_header": "📋 Tasks:",
    "no_due_date": "No due date",
    "days": "days",
    "unknown": "Unknown",
    
    # Task Status Buttons
    "status_to_do": "To Do",
    "status_in_progress": "In Progress",
    "status_done": "Done",
    "delete_task": "🗑️ Delete",
    
    # Task Management Messages
    "managers_only_delete": "Only team managers can delete tasks.",
    "task_deleted_success": "Task deleted successfully!",
    "task_not_found": "Task not found.",
    "update_own_tasks": "You can only update your own tasks.",
    "completed_tasks_locked": "Only managers can change the status of completed tasks.",
    "status_limit": "You can only change task status to 'In Progress' or 'Done'.",
    
    # Menu Items
    "add_task": "📝 Add Task",
    "view_tasks": "📋 View Tasks",
    "add_member": "👥 Add Member",
    "select_option": "Select an option",
    
    # Management Messages
    "teams_management": "👥 *Teams Management*\n\n• /create_team - Create a new team\n• /add_member - Add member to team\n\nNote: Team management features are available for managers only.",
    "tasks_management": "📝 *Tasks Management*\n\n• /add_task - Create a new task\n• /tasks - View your tasks\n\nTasks can be assigned to team members and tracked.",
    "about_bot": "ℹ️ *About Task Manager Bot*\n\nA powerful tool for managing tasks and teams in Telegram.\n\n{features}",
    "bot_features": "Features:\n• Team management\n• Task assignment\n• Progress tracking\n• Role-based access\n\nUse /help for detailed instructions.",
} 