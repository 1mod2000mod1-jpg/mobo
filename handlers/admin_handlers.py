#!/usr/bin/env python3
"""
معالجات لوحة المشرفين
"""

import logging
from datetime import datetime

logger = logging.getLogger("موبي_المشرفين")

def show_admin_stats(bot, call, memory):
    """عرض إحصائيات البوت"""
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        total_messages = sum(stats.get('message_count', 0) for stats in memory.user_stats.values())
        
        stats_text = f"""
📊 **إحصائيات البوت**

👥 **المستخدمين:**
• الإجمالي: {total_users}
• النشطين اليوم: {active_today}

💬 **الرسائل:**
• الإجمالي: {total_messages}

⚡ **النظام:**
• المشرفين: {len(memory.admins)}
• VIP: {len(memory.vip_users)}
• المحظورين: {len(memory.banned_users)}

🕒 **آخر تحديث:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        from handlers import create_admin_keyboards
        keyboards = create_admin_keyboards()
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards['admin_panel'](),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الإحصائيات: {e}")
        bot.answer_callback_query(call.id, "❌ خطأ في تحميل الإحصائيات")

def show_users_list(bot, call, memory):
    """عرض قائمة المستخدمين"""
    try:
        users_text = "👥 **قائمة المستخدمين**\n\n"
        
        for i, (user_id, stats) in enumerate(list(memory.user_stats.items())[:50], 1):
            username = stats.get('username', 'بدون معرف')
            first_name = stats.get('first_name', 'بدون اسم')
            message_count = stats.get('message_count', 0)
            
            users_text += f"{i}. {first_name} (@{username})\n"
            users_text += f"   🆔: {user_id} | 📝: {message_count}\n"
            users_text += f"   💎: {'VIP' if memory.is_vip(user_id) else 'عادي'} | 🛡️: {'مشرف' if memory.is_admin(user_id) else 'مستخدم'}\n\n"
        
        if len(memory.user_stats) > 50:
            users_text += f"📋 ... وعرض {len(memory.user_stats) - 50} مستخدم آخر"
        
        from handlers import create_admin_keyboards
        keyboards = create_admin_keyboards()
        
        bot.edit_message_text(
            users_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboards['admin_panel'](),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المستخدمين: {e}")
        bot.answer_callback_query(call.id, "❌ خطأ في تحميل المستخدمين")
