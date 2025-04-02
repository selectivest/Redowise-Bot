from typing import Dict

translations: Dict[str, str] = {
    # General
    "welcome": "👋 مرحباً بك في ربات إدارة المهام!\n\nأنا هنا لمساعدتك في إدارة المهام والفرق بكفاءة.\n\nما يمكنك القيام به:\n1️⃣ إنشاء وإدارة الفرق\n2️⃣ تعيين وتتبع المهام\n3️⃣ التعاون مع أعضاء الفريق\n\nاستخدم /menu لعرض القائمة الرئيسية أو /help للحصول على تعليمات مفصلة.\nاستخدم /show_keyboard لعرض قائمة لوحة المفاتيح.",
    "select_language": "الرجاء اختيار اللغة المفضلة لديك:",
    "language_changed": "تم تغيير اللغة إلى العربية",
    "main_menu": "🎯 القائمة الرئيسية\n\nالرجاء اختيار خيار:",
    
    # Menu
    "create_team": "إنشاء فريق",
    "join_team": "الانضمام إلى فريق",
    "my_tasks": "مهامي",
    "settings": "الإعدادات",
    
    # Team
    "team_created": "تم إنشاء الفريق بنجاح! أنت الآن مدير هذا الفريق.",
    "team_name_prompt": "الرجاء إدخال اسم الفريق الجديد:",
    "invalid_team_name": "لا يمكن أن يكون اسم الفريق فارغاً. الرجاء إدخال اسم صالح.",
    "team_name_exists": "يوجد فريق بهذا الاسم بالفعل. الرجاء اختيار اسم آخر.",
    "team_join_code": "رمز الانضمام إلى الفريق: {code}",
    "team_joined": "✅ انضممت إلى الفريق '{team_name}'!\n\nالمدير: @{manager_username}",
    "member_username_prompt": "الرجاء إدخال اسم المستخدم في تيليجرام للعضو الجديد:",
    "select_team": "اختر الفريق الذي تريد إضافة العضو إليه:",
    "user_not_found": "لم يتم العثور على المستخدم. الرجاء التأكد من أنه قام بالتسجيل في البوت أولاً.",
    "user_not_started_bot": "خطأ: @{username} لم يبدأ البوت بعد. الرجاء طلب منه بدء البوت باستخدام الأمر /start أولاً.",
    "team_invitation": "👋 تمت دعوتك للانضمام إلى الفريق '{team_name}'!\n\nالمدير: @{manager_username}\n\nهل تريد قبول الدعوة؟",
    "invitation_sent": "تم إرسال دعوة إلى @{username}",
    "invitation_send_error": "خطأ: لا يمكن إرسال دعوة إلى @{username}. الرجاء التأكد من أنه بدأ البوت والمحاولة مرة أخرى.",
    "invalid_invitation": "دعوة غير صالحة أو منتهية الصلاحية.",
    "member_accepted": "✅ قبل @{username} دعوة الانضمام إلى الفريق '{team_name}'!",
    "member_declined": "❌ رفض @{username} دعوة الانضمام إلى الفريق '{team_name}'.",
    "invitation_declined": "❌ رفضت دعوة الانضمام إلى الفريق '{team_name}'.",
    "accept": "✅ قبول",
    "reject": "❌ رفض",
    
    # Tasks
    "task_created": "تم إنشاء المهمة بنجاح!",
    "task_assigned": "تم تعيين المهمة إلى {user}",
    "new_task_assigned": "📝 تم تعيين مهمة جديدة لك!\n\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة: قيد الانتظار",
    "task_completed": "تم تحديد المهمة كمكتملة",
    "task_status": "حالة المهمة: {status}",
    "not_in_team": "يجب أن تكون عضواً في فريق أولاً.",
    "select_team_view": "اختر الفريق لعرض المهام:",
    "select_member": "اختر عضو الفريق لتعيين المهمة إليه:",
    "enter_task_description": "الرجاء إدخال وصف المهمة:",
    "select_due_date": "اختر تاريخ استحقاق المهمة:",
    "tomorrow": "غداً",
    "two_days": "بعد يومين",
    "three_days": "بعد ثلاثة أيام",
    "five_days": "بعد خمسة أيام",
    "one_week": "بعد أسبوع",
    "custom_date": "📅 اختيار التاريخ",
    "missing_fields": "خطأ: الحقول المطلوبة مفقودة: {fields}",
    "no_tasks": "لم يتم العثور على مهام.",
    "no_members": "لم يتم العثور على أعضاء في هذا الفريق.",
    "select_member_view": "اختر عضو الفريق لعرض مهامه:",
    "all_members": "👥 جميع الأعضاء",
    "own_tasks_only": "يمكنك فقط عرض مهامك الخاصة.",
    "update_own_tasks": "يمكنك فقط تحديث مهامك الخاصة.",
    "completed_tasks_locked": "يمكن للمدراء فقط تغيير حالة المهام المكتملة.",
    "status_limit": "يمكنك فقط تغيير حالة المهمة إلى 'قيد التنفيذ' أو 'مكتملة'.",
    "task_not_found": "لم يتم العثور على المهمة.",
    "error_occurred": "حدث خطأ. الرجاء المحاولة مرة أخرى.",
    
    # Status
    "status_pending": "قيد الانتظار",
    "status_in_progress": "قيد التنفيذ",
    "status_completed": "مكتملة",
    
    # Notifications
    "new_task": "📝 تم تعيين مهمة جديدة!\n\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة: قيد الانتظار",
    "status_change_manager": "🔄 تم تحديث حالة المهمة!\n\n🔹 معرف المهمة: {task_id}\n👤 المسؤول: {assignee_name}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة الجديدة: {new_status}",
    "status_change_assignee": "🔄 تم تحديث حالة مهمتك!\n\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة الجديدة: {new_status}",
    "task_deleted": "🗑️ تم حذف المهمة\n\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة: {status}\nتم الحذف بواسطة: {deleted_by}",
    "due_date_reminder": "⚠️ موعد استحقاق المهمة غداً!\n\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة: {status}",
    "daily_tasks": "📋 مهامك اليوم:\n\n{tasks}",
    "task_item": "🔹 معرف المهمة: {task_id}\n\n👤 المسؤول: {assignee}\n\n📄 الوصف: {description}\n\n📅 تاريخ الاستحقاق: {due_date}\n\nالحالة: {status}\n\n➖➖➖➖➖➖➖➖\n",
    "queued_notifications": "📋 إشعاراتك الجديدة:\n\n{notifications}",
    
    # Errors
    "error_occurred": "حدث خطأ. الرجاء المحاولة مرة أخرى.",
    "invalid_input": "إدخال غير صالح. الرجاء المحاولة مرة أخرى.",
    "not_authorized": "يجب أن تكون مدير فريق لإضافة عضو جديد. قم بإنشاء فريق أولاً باستخدام الأمر /create_team.",
    "database_error": "خطأ في قاعدة البيانات. الرجاء المحاولة مرة أخرى.",
    
    # Calendar
    "calendar_instructions": "الرجاء اختيار التاريخ من التقويم:",
    
    # Tasks List
    "tasks_header": "📋 المهام:",
    "no_due_date": "بدون تاريخ استحقاق",
    "days": "يوم",
    "unknown": "غير معروف",
    
    # Task Status Buttons
    "status_to_do": "قيد الانتظار",
    "status_in_progress": "قيد التنفيذ",
    "status_done": "مكتملة",
    "delete_task": "🗑️ حذف",
    
    # Task Management Messages
    "managers_only_delete": "يمكن لمدراء الفريق فقط حذف المهام.",
    "task_deleted_success": "تم حذف المهمة بنجاح!",
    "update_own_tasks": "يمكنك فقط تحديث مهامك الخاصة.",
    "completed_tasks_locked": "يمكن للمدراء فقط تغيير حالة المهام المكتملة.",
    "status_limit": "يمكنك فقط تغيير حالة المهمة إلى 'قيد التنفيذ' أو 'مكتملة'.",
    
    # Menu Items
    "add_task": "📝 إضافة مهمة",
    "view_tasks": "📋 عرض المهام",
    "add_member": "👥 إضافة عضو",
    "select_option": "اختر خياراً",
    
    # Management Messages
    "teams_management": "👥 *إدارة الفرق*\n\n• /create_team - إنشاء فريق جديد\n• /add_member - إضافة عضو إلى الفريق\n\nملاحظة: ميزات إدارة الفريق متاحة فقط للمدراء.",
    "tasks_management": "📝 *إدارة المهام*\n\n• /add_task - إنشاء مهمة جديدة\n• /tasks - عرض مهامك\n\nيمكن تعيين المهام لأعضاء الفريق وتتبعها.",
    "about_bot": "ℹ️ *حول ربات إدارة المهام*\n\nأداة قوية لإدارة المهام والفرق في تيليجرام.\n\n{features}",
    "bot_features": "الميزات:\n• إدارة الفريق\n• تعيين المهام\n• تتبع التقدم\n• الوصول القائم على الأدوار\n\nاستخدم /help للحصول على تعليمات مفصلة.",
} 