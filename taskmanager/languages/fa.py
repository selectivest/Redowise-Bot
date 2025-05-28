from typing import Dict

translations: Dict[str, str] = {
    # General
    "welcome": "👋 به ربات مدیریت وظایف خوش آمدید!\n\nمن اینجا هستم تا به شما در مدیریت وظایف و تیم‌ها کمک کنم.\n\nآنچه می‌توانید انجام دهید:\n1️⃣ ایجاد و مدیریت تیم‌ها\n2️⃣ تعیین و پیگیری وظایف\n3️⃣ همکاری با اعضای تیم\n\nاز /menu برای مشاهده منوی اصلی یا /help برای دستورالعمل‌های دقیق استفاده کنید.\nاز /show_keyboard برای نمایش منوی صفحه کلید استفاده کنید.",
    "select_language": "لطفاً زبان مورد نظر خود را انتخاب کنید:",
    "language_changed": "زبان به فارسی تغییر کرد",
    "main_menu": "🎯 منوی اصلی\n\nگزینه‌ای را انتخاب کنید:",
    "help": "🤖 *راهنمای ربات مدیریت وظایف*\n\n*ویژگی‌های اصلی* 🎯\n• ایجاد و مدیریت تیم‌ها\n• تعیین وظایف برای اعضای تیم\n• پیگیری وضعیت وظایف\n• دریافت اعلان‌ها برای به‌روزرسانی‌ها\n• پشتیبانی از چندین زبان\n\n*دستورات موجود* 📝\n• /add_task - ایجاد وظیفه جدید\n• /add_member - افزودن عضو به تیم شما\n• /create_team - ایجاد تیم جدید\n• /view_tasks - مشاهده تمام وظایف\n• /help - نمایش این راهنما\n• /menu - نمایش منوی اصلی\n• /language - تغییر زبان\n\n*جریان وضعیت وظیفه* 🔄\n1. 📝 انجام نشده (در انتظار)\n2. 🔄 در حال انجام\n3. ✅ انجام شده\n\n*دسترسی‌های مبتنی بر نقش* 👥\n*مدیران:*\n• ایجاد و حذف وظایف\n• افزودن/حذف اعضای تیم\n• تغییر وضعیت وظیفه\n• مشاهده تمام وظایف تیم\n\n*اعضا:*\n• مشاهده وظایف محول شده\n• به‌روزرسانی وضعیت وظیفه (تا انجام شده)\n• دریافت اعلان‌ها\n\n*اعلان‌ها* 🔔\n• محول کردن وظایف جدید\n• تغییرات وضعیت\n• حذف وظایف\n• یادآوری تاریخ موعد\n\n*نیاز به راهنمایی بیشتر؟* 💡\nبا مدیر تیم خود تماس بگیرید یا از /menu برای دسترسی به گزینه‌های بیشتر استفاده کنید.",
    
    # Menu
    "create_team": "ایجاد تیم",
    "join_team": "پیوستن به تیم",
    "my_tasks": "وظایف من",
    "settings": "تنظیمات",
    
    # Team
    "team_created": "تیم با موفقیت ایجاد شد! شما اکنون مدیر این تیم هستید.",
    "team_name_prompt": "لطفاً نام تیم جدید را وارد کنید:",
    "invalid_team_name": "نام تیم نمی‌تواند خالی باشد. لطفاً نام معتبری وارد کنید.",
    "team_name_exists": "تیمی با این نام قبلاً وجود دارد. لطفاً نام دیگری انتخاب کنید.",
    "team_join_code": "کد پیوستن به تیم: {code}",
    "team_joined": "✅ شما به تیم '{team_name}' پیوستید!\n\nمدیر: @{manager_username}",
    "member_username_prompt": "لطفاً نام کاربری تلگرام عضو جدید را وارد کنید:",
    "select_team": "تیمی را که می‌خواهید تسک به آن اضافه کنید انتخاب کنید:",
    "user_not_found": "کاربر پیدا نشد. لطفاً مطمئن شوید که ابتدا در ربات ثبت‌نام کرده باشد.",
    "user_not_started_bot": "خطا: @{username} هنوز ربات را شروع نکرده است. لطفاً از او بخواهید ابتدا با دستور /start ربات را شروع کند.",
    "user_already_in_team": "خطا: @{username} قبلاً عضو تیم '{team_name}' است.",
    "team_invitation": "👋 شما برای پیوستن به تیم '{team_name}' دعوت شده‌اید!\n\nمدیر: @{manager_username}\n\nآیا می‌خواهید دعوت را بپذیرید؟",
    "invitation_sent": "دعوت‌نامه برای @{username} ارسال شد",
    "invitation_send_error": "خطا: امکان ارسال دعوت‌نامه به @{username} وجود ندارد. لطفاً مطمئن شوید که ربات را شروع کرده باشد و دوباره تلاش کنید.",
    "invalid_invitation": "دعوت‌نامه نامعتبر یا منقضی شده است.",
    "member_accepted": "✅ @{username} دعوت پیوستن به تیم '{team_name}' را پذیرفت!",
    "member_declined": "❌ @{username} دعوت پیوستن به تیم '{team_name}' را رد کرد.",
    "invitation_declined": "❌ شما دعوت پیوستن به تیم '{team_name}' را رد کردید.",
    "accept": "✅ پذیرفتن",
    "reject": "❌ رد کردن",
    
    # Tasks
    "task_created": "وظیفه با موفقیت ایجاد شد!",
    "task_assigned": "وظیفه به {user} اختصاص داده شد",
    "new_task_assigned": "📝 وظیفه جدید به شما اختصاص داده شد!\n\n🔹 شناسه وظیفه: {task_id}\n📄 توضیحات: {description}\n📅 تاریخ موعد: {due_date}\nوضعیت: در انتظار",
    "task_completed": "وظیفه به عنوان تکمیل شده علامت‌گذاری شد",
    "task_status": "وضعیت وظیفه: {status}",
    "not_in_team": "شما باید ابتدا عضو یک تیم باشید.",
    "select_team_view": "تیمی را برای مشاهده وظایف انتخاب کنید:",
    "select_member": "عضو تیم را برای اختصاص وظیفه انتخاب کنید:",
    "enter_task_description": "لطفاً توضیحات وظیفه را وارد کنید:",
    "select_due_date": "تاریخ موعد وظیفه را انتخاب کنید:",
    "tomorrow": "فردا",
    "two_days": "۲ روز دیگر",
    "three_days": "۳ روز دیگر",
    "five_days": "۵ روز دیگر",
    "one_week": "یک هفته دیگر",
    "custom_date": "انتخاب تاریخ",
    "missing_fields": "خطا: اطلاعات مورد نیاز ناقص است: {fields}",
    "no_tasks": "هیچ وظیفه‌ای یافت نشد.",
    "no_members": "هیچ عضوی در این تیم یافت نشد.",
    "select_member_view": "عضو تیم را برای مشاهده وظایف انتخاب کنید:",
    "all_members": "👥 همه اعضا",
    "own_tasks_only": "شما فقط می‌توانید وظایف خود را مشاهده کنید.",
    "update_own_tasks": "شما فقط می‌توانید وظایف خود را به‌روزرسانی کنید.",
    "completed_tasks_locked": "فقط مدیران می‌توانند وضعیت وظایف تکمیل شده را تغییر دهند.",
    "status_limit": "شما فقط می‌توانید وضعیت وظیفه را به 'در حال انجام' یا 'تکمیل شده' تغییر دهید.",
    "task_not_found": "وظیفه یافت نشد.",
    "error_occurred": "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
    
    # Status
    "status_pending": "در انتظار",
    "status_in_progress": "در حال انجام",
    "status_completed": "تکمیل شده",
    
    # Notifications
    "new_task": "📝 وظیفه جدید تعیین شد!\n\n👥 تیم: {team_name}\n🔹 شناسه وظیفه: {task_id}\n📄 توضیحات: {description}\n📅 تاریخ موعد: {due_date}\n🔄 وضعیت: در انتظار",
    "status_change_manager": "🔄 وضعیت وظیفه به‌روزرسانی شد!\n\n👥 تیم: {team_name}\n🔹 شناسه وظیفه: {task_id}\n👤 مسئول: {assignee_name}\n📄 توضیحات: {description}\n📅 تاریخ موعد: {due_date}\n🔄 وضعیت جدید: {new_status}",
    "status_change_assignee": "🔄 وضعیت وظیفه شما توسط مدیر به‌روزرسانی شد!\n\n👥 تیم: {team_name}\n🔹 شناسه وظیفه: {task_id}\n📄 توضیحات: {description}\n📅 تاریخ موعد: {due_date}\n🔄 وضعیت جدید: {new_status}",
    "task_deleted": "🗑️ وظیفه حذف شد\n\n👥 تیم: {team_name}\n🔹 شناسه وظیفه: {task_id}\n📄 توضیحات: {description}\n📅 تاریخ موعد: {due_date}\n🔄 وضعیت: {status}\nحذف شده توسط: {deleted_by}",
    "due_date_reminder": "⚠️ موعد استحقاق وظیفه فردا است!\n\n🔹 شناسه وظیفه: {task_id}\n📄 توضیحات: {description}\n📅 تاریخ موعد: {due_date}\nوضعیت: {status}",
    "daily_tasks": "📋 وظایف امروز شما:\n\n{tasks}",
    "task_item": "👥 تیم: {team_name}\n\n🔹 شناسه وظیفه: {task_id}\n\n👤 مسئول: {assignee}\n\n📄 توضیحات:\n{description}\n\n📅 تاریخ سررسید: {due_date}\n\n📝 وضعیت: {status}\n\n➖➖➖➖➖➖➖➖\n",
    "queued_notifications": "📋 اعلان‌های جدید شما:\n\n{notifications}",
    
    # Errors
    "error_occurred": "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
    "invalid_input": "ورودی نامعتبر است. لطفاً دوباره تلاش کنید.",
    "not_authorized": "برای افزودن عضو جدید باید مدیر تیم باشید. ابتدا با استفاده از دستور /create_team یک تیم ایجاد کنید.",
    "database_error": "خطای پایگاه داده. لطفاً دوباره تلاش کنید.",
    
    # Calendar
    "calendar_instructions": "لطفاً تاریخ مورد نظر را از تقویم انتخاب کنید:",
    
    # Tasks List
    "tasks_header": "📋 وظایف:",
    "no_due_date": "بدون تاریخ سررسید",
    "days": "روز",
    "unknown": "ناشناس",
    
    # Task Status Buttons
    "status_pending": "در انتظار",
    "status_in_progress": "در حال انجام",
    "status_done": "تکمیل شده",
    "delete_task": "🗑️ حذف",
    
    # Task Management Messages
    "managers_only_delete": "فقط مدیران تیم می‌توانند وظایف را حذف کنند.",
    "task_deleted_success": "وظیفه با موفقیت حذف شد!",
    "update_own_tasks": "شما فقط می‌توانید وظایف خود را به‌روزرسانی کنید.",
    "completed_tasks_locked": "فقط مدیران می‌توانند وضعیت وظایف تکمیل شده را تغییر دهند.",
    "status_limit": "شما فقط می‌توانید وضعیت وظیفه را به 'در حال انجام' یا 'تکمیل شده' تغییر دهید.",
    
    # Menu Items
    "add_task": "📝 افزودن وظیفه",
    "view_tasks": "📋 مشاهده وظایف",
    "add_member": "اعضو افزودن",
    "member_management": "👥 مدیریت اعضا",
    "select_option": "گزینه مورد نظر را انتخاب کنید",
    
    # Member Management
    "select_team_manage": "یک تیم برای مدیریت اعضا انتخاب کنید:",
    "select_member_manage": "یک عضو برای مدیریت انتخاب کنید:",
    "member_management_options": "چه کاری می‌خواهید با {full_name} انجام دهید؟",
    "remove_member": "🗑️ حذف عضو",
    "make_manager": "👑 تبدیل به مدیر",
    "make_member": "👤 تبدیل به عضو",
    "member_removed": "✅ {full_name} از تیم '{team_name}' حذف شد",
    "member_role_changed": "✅ نقش {full_name} در تیم '{team_name}' به {role} تغییر کرد",
    "member_removed_notification": "❌ شما توسط {manager_name} از تیم '{team_name}' حذف شدید",
    "member_role_changed_notification": "👥 نقش شما در تیم '{team_name}' توسط {manager_name} به {role} تغییر کرد",
    "cannot_remove_last_manager": "❌ نمی‌توان آخرین مدیر تیم را حذف کرد. لطفاً ابتدا یک مدیر دیگر تعیین کنید.",
    "cannot_change_own_role": "❌ شما نمی‌توانید نقش خود را تغییر دهید.",
    "confirm_remove_member": "⚠️ آیا مطمئن هستید که می‌خواهید {full_name} را از تیم '{team_name}' حذف کنید؟\nاین کار تمام وظایف آنها را نیز حذف خواهد کرد.",
    "confirm_role_change": "⚠️ آیا مطمئن هستید که می‌خواهید نقش {full_name} را در تیم '{team_name}' به {role} تغییر دهید؟",
    "yes": "✅ بله",
    "no": "❌ خیر",
    "already_manager": "ℹ️ {full_name} در حال حاضر مدیر این تیم است.",
    "already_member": "ℹ️ {full_name} در حال حاضر عضو این تیم است.",
    "role_changed_to_manager": "✅ {full_name} اکنون مدیر تیم '{team_name}' است",
    "role_changed_to_member": "✅ {full_name} اکنون عضو تیم '{team_name}' است",
    "member_deleted": "✅ {full_name} و تمام وظایف آنها از تیم '{team_name}' حذف شدند",
    "member_deleted_notification": "❌ شما و تمام وظایف شما توسط {manager_name} از تیم '{team_name}' حذف شدند",
    "back": "⬅️ بازگشت",
    "no_managed_teams": "شما هیچ تیمی برای مدیریت ندارید.",
    "team_not_found": "تیم یافت نشد.",
    "member_not_found": "عضو یافت نشد.",
    "user_not_found": "کاربر یافت نشد.",
    "error_occurred": "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
    "manager": "مدیر",
    "member": "عضو",
    "owner": "مالک",
    
    # Management Messages
    "teams_management": "👥 *مدیریت تیم‌ها*\n\n• /create_team - ایجاد تیم جدید\n• /add_member - افزودن عضو به تیم\n\nنکته: ویژگی‌های مدیریت تیم فقط برای مدیران در دسترس است.",
    "tasks_management": "📝 *مدیریت وظایف*\n\n• /add_task - ایجاد وظیفه جدید\n• /tasks - مشاهده وظایف شما\n\nوظایف می‌توانند به اعضای تیم اختصاص داده شوند و پیگیری شوند.",
    "about_bot": "ℹ️ *درباره ربات مدیریت وظایف*\n\nابزاری قدرتمند برای مدیریت وظایف و تیم‌ها در تلگرام.\n\n{features}",
    "bot_features": "ویژگی‌ها:\n• مدیریت تیم\n• اختصاص وظایف\n• پیگیری پیشرفت\n• دسترسی مبتنی بر نقش\n\nاز /help برای دستورالعمل‌های دقیق استفاده کنید.",
    "enter_username": "لطفاً نام کاربری تلگرام عضو جدید را وارد کنید:",
    "no_managed_teams": "شما هیچ تیمی برای مدیریت اعضا ندارید.",
    "back": "🔙 بازگشت",
} 