from typing import Dict

translations: Dict[str, str] = {
    # General
    "welcome": "👋 مرحباً بك في ربات إدارة المهام!\n\nأنا هنا لمساعدتك في إدارة المهام والفرق بكفاءة.\n\nما يمكنك القيام به:\n1️⃣ إنشاء وإدارة الفرق\n2️⃣ تعيين وتتبع المهام\n3️⃣ التعاون مع أعضاء الفريق\n\nاستخدم /menu لرؤية القائمة الرئيسية أو /help للحصول على تعليمات مفصلة.\nاستخدم /show_keyboard لإظهار قائمة لوحة المفاتيح.",
    "select_language": "الرجاء اختيار اللغة المفضلة لديك:",
    "language_changed": "تم تغيير اللغة إلى العربية",
    "main_menu": "🎯 القائمة الرئيسية\n\nاختر خياراً:",
    "help": "🤖 *دليل ربات إدارة المهام*\n\n*الميزات الرئيسية* 🎯\n• إنشاء وإدارة الفرق\n• تعيين المهام لأعضاء الفريق\n• تتبع حالة المهام\n• تلقي الإشعارات للتحديثات\n• دعم لغات متعددة\n\n*الأوامر المتاحة* 📝\n• /add_task - إنشاء مهمة جديدة\n• /add_member - إضافة عضو إلى فريقك\n• /create_team - إنشاء فريق جديد\n• /view_tasks - عرض جميع المهام\n• /help - عرض هذا الدليل\n• /menu - عرض القائمة الرئيسية\n• /language - تغيير اللغة\n\n*تسلسل حالة المهمة* 🔄\n1. 📝 قيد الانتظار\n2. 🔄 قيد التنفيذ\n3. ✅ مكتملة\n\n*الصلاحيات حسب الدور* 👥\n*المدراء:*\n• إنشاء وحذف المهام\n• إضافة/إزالة أعضاء الفريق\n• تغيير حالة المهمة\n• عرض جميع مهام الفريق\n\n*الأعضاء:*\n• عرض المهام المسندة إليهم\n• تحديث حالة المهمة (حتى مكتملة)\n• تلقي الإشعارات\n\n*الإشعارات* 🔔\n• تعيين مهام جديدة\n• تغييرات الحالة\n• حذف المهام\n• تذكيرات الموعد النهائي\n\n*تحتاج إلى مزيد من المساعدة؟* 💡\nتواصل مع مدير فريقك أو استخدم /menu للوصول إلى المزيد من الخيارات.",
    
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
    "user_not_started_bot": "خطأ: @{username} لم يبدأ استخدام البوت بعد. يرجى طلب منه بدء البوت باستخدام /start أولاً.",
    "user_already_in_team": "خطأ: @{username} عضو بالفعل في فريق '{team_name}'.",
    "team_invitation": "👋 تمت دعوتك للانضمام إلى فريق '{team_name}'!\n\nالمدير: @{manager_username}\n\nهل ترغب في قبول الدعوة؟",
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
    "new_task": "📝 تم تعيين مهمة جديدة!\n\n👥 الفريق: {team_name}\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\n🔄 الحالة: قيد الانتظار",
    "status_change_manager": "🔄 تم تحديث حالة المهمة!\n\n👥 الفريق: {team_name}\n🔹 معرف المهمة: {task_id}\n👤 المسؤول: {assignee_name}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\n🔄 الحالة الجديدة: {new_status}",
    "status_change_assignee": "🔄 تم تحديث حالة مهمتك بواسطة المدير\n\n👥 الفريق: {team_name}\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\n🔄 الحالة الجديدة: {new_status}",
    "task_deleted": "🗑️ تم حذف المهمة\n\n👥 الفريق: {team_name}\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\n🔄 الحالة: {status}\nتم الحذف بواسطة: {deleted_by}",
    "due_date_reminder": "⚠️ موعد استحقاق المهمة غداً!\n\n🔹 معرف المهمة: {task_id}\n📄 الوصف: {description}\n📅 تاريخ الاستحقاق: {due_date}\nالحالة: {status}",
    "daily_tasks": "📋 مهامك اليوم:\n\n{tasks}",
    "task_item": "👥 الفريق: {team_name}\n\n🔹 معرف المهمة: {task_id}\n\n👤 المسؤول: {assignee}\n\n📄 الوصف:\n{description}\n\n📅 تاريخ الاستحقاق: {due_date}\n\n📝 الحالة: {status}\n\n➖➖➖➖➖➖➖➖\n",
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
    "member_management": "👥 إدارة الأعضاء",
    "select_option": "اختر الخيار المطلوب",
    
    # Member Management
    "select_team_manage": "اختر فريقًا لإدارة الأعضاء:",
    "select_member_manage": "اختر عضوًا للإدارة:",
    "member_management_options": "ماذا تريد أن تفعل مع {full_name}؟",
    "remove_member": "🗑️ إزالة العضو",
    "make_manager": "👑 تعيين كمدير",
    "make_member": "👤 تعيين كعضو",
    "member_removed": "✅ تمت إزالة {full_name} من فريق '{team_name}'",
    "member_role_changed": "✅ تم تغيير دور {full_name} إلى {role} في فريق '{team_name}'",
    "member_removed_notification": "❌ تمت إزالتك من فريق '{team_name}' بواسطة {manager_name}",
    "member_role_changed_notification": "👥 تم تغيير دورك إلى {role} في فريق '{team_name}' بواسطة {manager_name}",
    "cannot_remove_last_manager": "❌ لا يمكن إزالة آخر مدير في الفريق. يرجى تعيين مدير آخر أولاً.",
    "cannot_change_own_role": "❌ لا يمكنك تغيير دورك الخاص.",
    "confirm_remove_member": "⚠️ هل أنت متأكد أنك تريد إزالة {full_name} من فريق '{team_name}'؟\nسيؤدي هذا أيضًا إلى حذف جميع مهامهم.",
    "confirm_role_change": "⚠️ هل أنت متأكد أنك تريد تغيير دور {full_name} إلى {role} في فريق '{team_name}'؟",
    "yes": "✅ نعم",
    "no": "❌ لا",
    "already_manager": "ℹ️ {full_name} هو بالفعل مدير في هذا الفريق.",
    "already_member": "ℹ️ {full_name} هو بالفعل عضو في هذا الفريق.",
    "role_changed_to_manager": "✅ {full_name} أصبح الآن مديرًا في فريق '{team_name}'",
    "role_changed_to_member": "✅ {full_name} أصبح الآن عضوًا في فريق '{team_name}'",
    "member_deleted": "✅ تمت إزالة {full_name} وجميع مهامهم من فريق '{team_name}'",
    "member_deleted_notification": "❌ تمت إزالتك وجميع مهامك من فريق '{team_name}' بواسطة {manager_name}",
    "back": "⬅️ رجوع",
    "no_managed_teams": "ليس لديك أي فرق للإدارة.",
    "team_not_found": "لم يتم العثور على الفريق.",
    "member_not_found": "لم يتم العثور على العضو.",
    "user_not_found": "لم يتم العثور على المستخدم.",
    "error_occurred": "حدث خطأ. يرجى المحاولة مرة أخرى.",
    "manager": "مدير",
    "member": "عضو",
    "owner": "مالك",
    
    # Management Messages
    "teams_management": "👥 *إدارة الفرق*\n\n• /create_team - إنشاء فريق جديد\n• /add_member - إضافة عضو إلى الفريق\n\nملاحظة: ميزات إدارة الفريق متاحة فقط للمدراء.",
    "tasks_management": "📝 *إدارة المهام*\n\n• /add_task - إنشاء مهمة جديدة\n• /tasks - عرض مهامك\n\nيمكن تعيين المهام لأعضاء الفريق وتتبعها.",
    "about_bot": "ℹ️ *حول ربات إدارة المهام*\n\nأداة قوية لإدارة المهام والفرق في تيليجرام.\n\n{features}",
    "bot_features": "الميزات:\n• إدارة الفريق\n• تعيين المهام\n• تتبع التقدم\n• الوصول القائم على الأدوار\n\nاستخدم /help للحصول على تعليمات مفصلة.",
} 