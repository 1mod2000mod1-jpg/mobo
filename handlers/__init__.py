#!/usr/bin/env python3
"""
معالجات البوت - تفريغ الوظائف من الملف الرئيسي
"""

import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger("موبي_المعالجات")

def create_admin_keyboards():
    """إنشاء جميع أزرار لوحة المشرفين"""
    
    def admin_panel():
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            ("📊 الإحصائيات", "admin_stats"),
            ("👥 المستخدمين", "admin_users"),
            ("🛡️ المشرفين", "admin_manage"),
            ("💬 المحادثات", "admin_conversations"),
            ("🌟 إدارة VIP", "admin_vip"),
            ("📢 البث", "admin_broadcast"),
            ("🚫 الحظر", "admin_ban"),
            ("🎯 النقاط", "admin_points"),
            ("⚙️ الإعدادات", "admin_settings")
        ]
        
        # إضافة الأزرار في صفوف
        for i in range(0, len(buttons), 2):
            row_buttons = []
            for j in range(2):
                if i + j < len(buttons):
                    text, callback = buttons[i + j]
                    row_buttons.append(InlineKeyboardButton(text, callback_data=callback))
            keyboard.add(*row_buttons)
        
        return keyboard
    
    def broadcast_menu():
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            ("📝 نص", "broadcast_text"),
            ("🖼️ صورة", "broadcast_photo"),
            ("🎥 فيديو", "broadcast_video"),
            ("🎵 صوت", "broadcast_audio"),
            ("📄 ملف", "broadcast_document"),
            ("🔙 رجوع", "admin_back")
        ]
        
        for i in range(0, len(buttons), 2):
            row_buttons = []
            for j in range(2):
                if i + j < len(buttons):
                    text, callback = buttons[i + j]
                    row_buttons.append(InlineKeyboardButton(text, callback_data=callback))
            keyboard.add(*row_buttons)
        
        return keyboard
    
    def settings_menu():
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            ("📢 إدارة القناة", "settings_channel"),
            ("🔐 الاشتراك الإجباري", "settings_subscription"),
            ("💬 عدد الرسائل", "settings_messages"),
            ("🎉 الترحيب", "settings_welcome"),
            ("🔙 رجوع", "admin_back")
        ]
        
        for i in range(0, len(buttons), 2):
            row_buttons = []
            for j in range(2):
                if i + j < len(buttons):
                    text, callback = buttons[i + j]
                    row_buttons.append(InlineKeyboardButton(text, callback_data=callback))
            keyboard.add(*row_buttons)
        
        return keyboard
    
    def welcome_menu():
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            ("📝 نص ترحيبي", "welcome_text"),
            ("🖼️ صورة ترحيبية", "welcome_photo"),
            ("🎥 فيديو ترحيبي", "welcome_video"),
            ("🎵 صوت ترحيبي", "welcome_audio"),
            ("🗑️ مسح الترحيب", "welcome_clear"),
            ("🔙 رجوع", "admin_settings")
        ]
        
        for i in range(0, len(buttons), 2):
            row_buttons = []
            for j in range(2):
                if i + j < len(buttons):
                    text, callback = buttons[i + j]
                    row_buttons.append(InlineKeyboardButton(text, callback_data=callback))
            keyboard.add(*row_buttons)
        
        return keyboard
    
    def points_menu():
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        buttons = [
            ("➕ إضافة نقاط", "add_points"),
            ("➖ نزع نقاط", "remove_points"),
            ("📤 إرسال لمستخدم", "send_to_user"),
            ("🔙 رجوع", "admin_back")
        ]
        
        for i in range(0, len(buttons), 2):
            row_buttons = []
            for j in range(2):
                if i + j < len(buttons):
                    text, callback = buttons[i + j]
                    row_buttons.append(InlineKeyboardButton(text, callback_data=callback))
            keyboard.add(*row_buttons)
        
        return keyboard
    
    return {
        'admin_panel': admin_panel,
        'broadcast_menu': broadcast_menu,
        'settings_menu': settings_menu,
        'welcome_menu': welcome_menu,
        'points_menu': points_menu
    }
