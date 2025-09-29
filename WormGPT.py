#!/usr/bin/env python3
"""
موبي - البوت الذكي المتقدم
"""

import os
import json
import logging
import requests
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import watchdog
import psutil
# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("موبي_البوت")

# التوكن
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN غير معروف")
    exit(1)

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# معلومات المطور
DEVELOPER_USERNAME = "@xtt19x"
DEVELOPER_ID = 0000000000

# إعدادات البوت
BOT_SETTINGS = {
    "required_channel": "",
    "free_messages": 50,
    "welcome_content": {"type": "text", "content": ""},
    "subscription_enabled": False
}

# نظام الذاكرة
class MemorySystem:
    def __init__(self):
        self.workspace = Path("/tmp/mobi_memory")
        self.workspace.mkdir(exist_ok=True)
        self.conversations = {}
        self.user_stats = self.load_user_stats()
        self.admins = self.load_admins()
        self.banned_users = self.load_banned_users()
        self.vip_users = self.load_vip_users()
        self.settings = self.load_settings()
        self.temp_files = {}
    
    def get_user_file(self, user_id):
        return self.workspace / f"user_{user_id}.json"
    
    def get_stats_file(self):
        return self.workspace / "user_stats.json"
    
    def get_admins_file(self):
        return self.workspace / "admins.json"
    
    def get_banned_file(self):
        return self.workspace / "banned_users.json"
    
    def get_vip_file(self):
        return self.workspace / "vip_users.json"
    
    def get_settings_file(self):
        return self.workspace / "bot_settings.json"
    
    def load_user_stats(self):
        stats_file = self.get_stats_file()
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def load_admins(self):
        admins_file = self.get_admins_file()
        if admins_file.exists():
            try:
                with open(admins_file, 'r', encoding='utf-8') as f:
                    admins = json.load(f)
                    if DEVELOPER_ID not in admins:
                        admins.append(DEVELOPER_ID)
                    return admins
            except:
                return [DEVELOPER_ID]
        return [DEVELOPER_ID]
    
    def load_banned_users(self):
        banned_file = self.get_banned_file()
        if banned_file.exists():
            try:
                with open(banned_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def load_vip_users(self):
        vip_file = self.get_vip_file()
        if vip_file.exists():
            try:
                with open(vip_file, 'r', encoding='utf-8') as f:
                    vip_users = json.load(f)
                    if DEVELOPER_ID not in vip_users:
                        vip_users.append(DEVELOPER_ID)
                    return vip_users
            except:
                return [DEVELOPER_ID]
        return [DEVELOPER_ID]
    
    def load_settings(self):
        settings_file = self.get_settings_file()
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    return {**BOT_SETTINGS, **loaded_settings}
            except:
                return BOT_SETTINGS
        return BOT_SETTINGS
    
    def save_user_stats(self):
        stats_file = self.get_stats_file()
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_stats, f, ensure_ascii=False, indent=2)
    
    def save_admins(self):
        admins_file = self.get_admins_file()
        with open(admins_file, 'w', encoding='utf-8') as f:
            json.dump(self.admins, f, ensure_ascii=False, indent=2)
    
    def save_banned_users(self):
        banned_file = self.get_banned_file()
        with open(banned_file, 'w', encoding='utf-8') as f:
            json.dump(self.banned_users, f, ensure_ascii=False, indent=2)
    
    def save_vip_users(self):
        vip_file = self.get_vip_file()
        with open(vip_file, 'w', encoding='utf-8') as f:
            json.dump(self.vip_users, f, ensure_ascii=False, indent=2)
    
    def save_settings(self):
        settings_file = self.get_settings_file()
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    def update_user_stats(self, user_id, username, first_name, message_text=""):
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'username': username,
                'first_name': first_name,
                'message_count': 0,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'last_message': message_text[:100] if message_text else "",
                'is_admin': user_id in self.admins,
                'is_banned': user_id in self.banned_users,
                'is_vip': user_id in self.vip_users,
                'message_limit': self.settings.get('free_messages', 50),
                'used_messages': 0,
                'points': 0
            }
        else:
            self.user_stats[user_id]['message_count'] += 1
            self.user_stats[user_id]['last_seen'] = datetime.now().isoformat()
            if message_text:
                self.user_stats[user_id]['last_message'] = message_text[:100]
            self.user_stats[user_id]['is_admin'] = user_id in self.admins
            self.user_stats[user_id]['is_banned'] = user_id in self.banned_users
            self.user_stats[user_id]['is_vip'] = user_id in self.vip_users
            
            if not self.is_vip(user_id) and not self.is_admin(user_id):
                self.user_stats[user_id]['used_messages'] += 1
        
        self.save_user_stats()
    
    def can_send_message(self, user_id):
        if self.is_vip(user_id) or self.is_admin(user_id):
            return True, "VIP"
        
        if user_id not in self.user_stats:
            return True, "جديد"
        
        used = self.user_stats[user_id].get('used_messages', 0)
        limit = self.user_stats[user_id].get('message_limit', self.settings.get('free_messages', 50))
        
        if used < limit:
            return True, f"مجاني ({limit - used} متبقي)"
        else:
            return False, f"انتهت الرسائل ({used}/{limit})"
    
    def add_vip(self, user_id, username, first_name):
        if user_id not in self.vip_users:
            self.vip_users.append(user_id)
            self.save_vip_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_vip'] = True
            self.update_user_stats(user_id, username, first_name, "تم ترقيته إلى VIP")
            return True
        return False
    
    def remove_vip(self, user_id):
        if user_id in self.vip_users and user_id != DEVELOPER_ID:
            self.vip_users.remove(user_id)
            self.save_vip_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_vip'] = False
            return True
        return False
    
    def is_vip(self, user_id):
        return user_id in self.vip_users
    
    def add_admin(self, user_id, username, first_name):
        if user_id not in self.admins:
            self.admins.append(user_id)
            self.save_admins()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_admin'] = True
            self.update_user_stats(user_id, username, first_name, "تم ترقيته إلى مشرف")
            return True
        return False
    
    def remove_admin(self, user_id):
        if user_id in self.admins and user_id != DEVELOPER_ID:
            self.admins.remove(user_id)
            self.save_admins()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_admin'] = False
            return True
        return False
    
    def ban_user(self, user_id, username, first_name):
        if user_id not in self.banned_users and user_id != DEVELOPER_ID:
            self.banned_users.append(user_id)
            self.save_banned_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_banned'] = True
            return True
        return False
    
    def unban_user(self, user_id):
        if user_id in self.banned_users:
            self.banned_users.remove(user_id)
            self.save_banned_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_banned'] = False
            return True
        return False
    
    def add_points(self, user_id, points):
        if user_id in self.user_stats:
            self.user_stats[user_id]['points'] = self.user_stats[user_id].get('points', 0) + points
            self.save_user_stats()
            return True
        return False
    
    def remove_points(self, user_id, points):
        if user_id in self.user_stats:
            current_points = self.user_stats[user_id].get('points', 0)
            new_points = max(0, current_points - points)
            self.user_stats[user_id]['points'] = new_points
            self.save_user_stats()
            return True
        return False
    
    def is_admin(self, user_id):
        return user_id in self.admins
    
    def is_banned(self, user_id):
        return user_id in self.banned_users
    
    def get_user_conversation(self, user_id):
        return self.load_conversation(user_id)
    
    def get_user_stats(self):
        return self.user_stats
    
    def get_total_users(self):
        return len(self.user_stats)
    
    def get_active_today(self):
        today = datetime.now().date()
        active_count = 0
        for user_id, stats in self.user_stats.items():
            if user_id in self.banned_users:
                continue
            last_seen = datetime.fromisoformat(stats['last_seen']).date()
            if last_seen == today:
                active_count += 1
        return active_count
    
    def get_admins_list(self):
        admins_info = []
        for admin_id in self.admins:
            if admin_id in self.user_stats:
                stats = self.user_stats[admin_id]
                admins_info.append({
                    'id': admin_id,
                    'username': stats.get('username', 'بدون معرف'),
                    'first_name': stats.get('first_name', 'بدون اسم'),
                    'message_count': stats.get('message_count', 0),
                    'points': stats.get('points', 0)
                })
        return admins_info
    
    def get_vip_list(self):
        vip_info = []
        for vip_id in self.vip_users:
            if vip_id in self.user_stats:
                stats = self.user_stats[vip_id]
                vip_info.append({
                    'id': vip_id,
                    'username': stats.get('username', 'بدون معرف'),
                    'first_name': stats.get('first_name', 'بدون اسم'),
                    'message_count': stats.get('message_count', 0),
                    'points': stats.get('points', 0)
                })
        return vip_info
    
    def get_recent_messages(self, user_id, minutes=10):
        conversation = self.get_user_conversation(user_id)
        if not conversation:
            return []
        
        time_threshold = datetime.now() - timedelta(minutes=minutes)
        recent_messages = []
        
        for msg in conversation:
            msg_time = datetime.fromisoformat(msg['timestamp'])
            if msg_time >= time_threshold:
                recent_messages.append(msg)
        
        return recent_messages
    
    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save_settings()
        
        new_limit = self.settings.get('free_messages', 50)
        for user_id in self.user_stats:
            if not self.is_vip(user_id) and not self.is_admin(user_id):
                self.user_stats[user_id]['message_limit'] = new_limit
        self.save_user_stats()
    
    def load_conversation(self, user_id):
        user_file = self.get_user_file(user_id)
        if user_file.exists():
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ خطأ في تحميل محادثة المستخدم {user_id}: {e}")
                return []
        return []
    
    def save_conversation(self, user_id, conversation):
        self.conversations[user_id] = conversation
        user_file = self.get_user_file(user_id)
        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(conversation[-15:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ محادثة المستخدم {user_id}: {e}")
    
    def add_message(self, user_id, role, content):
        conversation = self.load_conversation(user_id)
        conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_conversation(user_id, conversation)
    
    def clear_conversation(self, user_id):
        self.conversations[user_id] = []
        user_file = self.get_user_file(user_id)
        if user_file.exists():
            user_file.unlink()
    
    def cleanup_old_conversations(self):
        """تنظيف المحادثات القديمة"""
        try:
            for user_id in list(self.conversations.keys()):
                conversation = self.get_user_conversation(user_id)
                if conversation:
                    # حذف الرسائل الأقدم من 10 دقائق
                    time_threshold = datetime.now() - timedelta(minutes=10)
                    cleaned_conversation = [
                        msg for msg in conversation 
                        if datetime.fromisoformat(msg['timestamp']) >= time_threshold
                    ]
                    self.save_conversation(user_id, cleaned_conversation)
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف المحادثات: {e}")

# تهيئة النظام
memory = MemorySystem()

# نظام الذكاء الاصطناعي
class AIService:
    API_URL = "https://sii3.top/api/grok4.php?text=hello"
    
    @staticmethod
    def generate_response(user_id, user_message):
        try:
            can_send, status = memory.can_send_message(user_id)
            if not can_send:
                return f"❌ انتهت رسائلك المجانية! ({status})\n\n💎 ترقى إلى VIP للاستخدام غير المحدود!\n/upgrade للترقية"
            
            if memory.is_banned(user_id):
                return "❌ تم حظرك من استخدام موبي."
            
            memory.add_message(user_id, "user", user_message)
            
            try:
                response = AIService.api_call(user_message, user_id)
                if response and len(response.strip()) > 5:
                    return response
            except Exception as api_error:
                logger.warning(f"⚠️ النظام غير متاح: {api_error}")
            
            return AIService.smart_response(user_message, user_id)
            
        except Exception as e:
            logger.error(f"❌ خطأ في النظام: {e}")
            return "⚠️ عذراً، النظام يواجه صعوبات. جرب مرة أخرى!"
    
    @staticmethod
    def api_call(message, user_id):
        try:
            api_url = f"{AIService.API_URL}?text={requests.utils.quote(message)}"
            logger.info(f"🔗 موبي يتصل بالنظام: {api_url}")
            
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 200:
                ai_response = response.text.strip()
                
                # تنظيف الرد من JSON إذا كان موجوداً
                if '{"date"' in ai_response and '"response"' in ai_response:
                    import re
                    match = re.search(r'"response":"([^"]+)"', ai_response)
                    if match:
                        ai_response = match.group(1)
                
                # تنظيف الرد من معلومات إضافية
                lines = ai_response.split('\n')
                clean_lines = []
                for line in lines:
                    if not any(x in line.lower() for x in ['dev:', 'support', 'channel', '@', 'don\'t forget']):
                        clean_lines.append(line)
                ai_response = '\n'.join(clean_lines).strip()
                
                if not ai_response or ai_response.isspace():
                    ai_response = "🔄 موبي يفكر... جرب صياغة سؤالك بطريقة أخرى!"
                
                ai_response = ai_response.replace('\\n', '\n').replace('\\t', '\t')
                if len(ai_response) > 2000:
                    ai_response = ai_response[:2000] + "..."
                
                memory.add_message(user_id, "assistant", ai_response)
                logger.info(f"✅ موبي رد: {ai_response[:100]}...")
                return ai_response
            else:
                raise Exception(f"خطأ في النظام: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في النظام: {e}")
            raise
    
    @staticmethod
    def smart_response(message, user_id):
        message_lower = message.lower()
        
        responses = {
            'مرحبا': 'أهلاً! أنا موبي 🤖! كيف يمكنني مساعدتك؟ 💫',
            'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته! موبي جاهز لخدمتك. 🌟',
            'شكرا': 'العفو! دائماً سعيد بمساعدتك. 😊',
            'اسمك': 'أنا موبي! 🤖 المساعد الذكي!',
            'من صنعك': f'السيد موبي - {DEVELOPER_USERNAME} 👑',
            'من صنعك؟': f'السيد موبي - {DEVELOPER_USERNAME} 👑',
            'صانعك': f'السيد موبي - {DEVELOPER_USERNAME} 👑',
            'مطورك': f'السيد موبي - {DEVELOPER_USERNAME} 👑',
            'مين صنعك': f'السيد موبي - {DEVELOPER_USERNAME} 👑',
            'كيف حالك': 'أنا بخير الحمدلله! جاهز لمساعدتك. ⚡',
            'مساعدة': 'موبي يمكنه مساعدتك في:\n• الإجابة على الأسئلة\n• الشرح والتوضيح\n• الكتابة والإبداع\n• حل المشكلات\nما الذي تحتاج؟ 🎯',
            'مطور': f'السيد موبي - {DEVELOPER_USERNAME} 👑',
            'موبي': 'نعم! أنا موبي هنا! 🤖 كيف يمكنني مساعدتك؟',
            'vip': '🌟 نظام VIP يمنحك صلاحيات متقدمة! تواصل مع المطور.',
            'بريميوم': '💎 اشترك في البريميوم للوصول غير المحدود!',
            'ترقية': f'💎 للترقية إلى VIP تواصل مع {DEVELOPER_USERNAME}',
        }
        
        for key, response in responses.items():
            if key in message_lower:
                memory.add_message(user_id, "assistant", response)
                return response
        
        import random
        fallback_responses = [
            f"🤔 '{message}' - سؤال مثير! دعني أفكر...",
            f"💭 أحلل سؤالك: '{message}'",
            f"🎯 رائع! '{message}' - سأستخدم ذكائي للإجابة!",
            f"⚡ موبي يعالج: '{message}'",
        ]
        
        response = random.choice(fallback_responses)
        memory.add_message(user_id, "assistant", response)
        return response

def check_subscription(user_id):
    if not memory.settings.get('required_channel') or not memory.settings.get('subscription_enabled', False):
        return True
        
    try:
        chat_member = bot.get_chat_member(memory.settings['required_channel'], user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من الاشتراك: {e}")
        return False

def create_subscription_button():
    if not memory.settings.get('required_channel') or not memory.settings.get('subscription_enabled', False):
        return None
        
    channel_link = f"https://t.me/{memory.settings['required_channel'][1:]}"
    keyboard = InlineKeyboardMarkup()
    channel_btn = InlineKeyboardButton("📢 اشترك في القناة", url=channel_link)
    check_btn = InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")
    keyboard.add(channel_btn, check_btn)
    return keyboard

def create_developer_button():
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton("👑 السيد موبي", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    keyboard.add(developer_btn)
    return keyboard

def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    stats_btn = InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")
    users_btn = InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")
    admins_btn = InlineKeyboardButton("🛡️ المشرفين", callback_data="admin_manage")
    conversations_btn = InlineKeyboardButton("💬 المحادثات", callback_data="admin_conversations")
    vip_btn = InlineKeyboardButton("🌟 إدارة VIP", callback_data="admin_vip")
    broadcast_btn = InlineKeyboardButton("📢 البث", callback_data="admin_broadcast")
    ban_btn = InlineKeyboardButton("🚫 الحظر", callback_data="admin_ban")
    points_btn = InlineKeyboardButton("🎯 النقاط", callback_data="admin_points")
    settings_btn = InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")
    
    keyboard.add(stats_btn, users_btn)
    keyboard.add(admins_btn, conversations_btn)
    keyboard.add(vip_btn, broadcast_btn)
    keyboard.add(ban_btn, points_btn)
    keyboard.add(settings_btn)
    
    return keyboard

def create_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    help_btn = InlineKeyboardButton("🆘 المساعدة", callback_data="user_help")
    status_btn = InlineKeyboardButton("📊 الحالة", callback_data="user_status")
    vip_btn = InlineKeyboardButton("💎 ترقية", callback_data="user_vip")
    developer_btn = InlineKeyboardButton("👑 السيد موبي", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    
    keyboard.add(help_btn, status_btn)
    keyboard.add(vip_btn, developer_btn)
    
    return keyboard

def create_settings_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    channel_btn = InlineKeyboardButton("📢 إدارة القناة", callback_data="settings_channel")
    subscription_btn = InlineKeyboardButton("🔐 الاشتراك الإجباري", callback_data="settings_subscription")
    messages_btn = InlineKeyboardButton("💬 عدد الرسائل", callback_data="settings_messages")
    welcome_btn = InlineKeyboardButton("🎉 الترحيب", callback_data="settings_welcome")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    
    keyboard.add(channel_btn, subscription_btn)
    keyboard.add(messages_btn, welcome_btn)
    keyboard.add(back_btn)
    
    return keyboard

def create_broadcast_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    text_btn = InlineKeyboardButton("📝 نص", callback_data="broadcast_text")
    photo_btn = InlineKeyboardButton("🖼️ صورة", callback_data="broadcast_photo")
    video_btn = InlineKeyboardButton("🎥 فيديو", callback_data="broadcast_video")
    audio_btn = InlineKeyboardButton("🎵 صوت", callback_data="broadcast_audio")
    document_btn = InlineKeyboardButton("📄 ملف", callback_data="broadcast_document")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    
    keyboard.add(text_btn, photo_btn)
    keyboard.add(video_btn, audio_btn)
    keyboard.add(document_btn)
    keyboard.add(back_btn)
    
    return keyboard

def create_points_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    add_points_btn = InlineKeyboardButton("➕ إضافة نقاط", callback_data="add_points")
    remove_points_btn = InlineKeyboardButton("➖ نزع نقاط", callback_data="remove_points")
    send_user_btn = InlineKeyboardButton("📤 إرسال لمستخدم", callback_data="send_to_user")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    
    keyboard.add(add_points_btn, remove_points_btn)
    keyboard.add(send_user_btn)
    keyboard.add(back_btn)
    
    return keyboard

def create_welcome_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    text_btn = InlineKeyboardButton("📝 نص ترحيبي", callback_data="welcome_text")
    photo_btn = InlineKeyboardButton("🖼️ صورة ترحيبية", callback_data="welcome_photo")
    video_btn = InlineKeyboardButton("🎥 فيديو ترحيبي", callback_data="welcome_video")
    audio_btn = InlineKeyboardButton("🎵 صوت ترحيبي", callback_data="welcome_audio")
    clear_btn = InlineKeyboardButton("🗑️ مسح الترحيب", callback_data="welcome_clear")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings")
    
    keyboard.add(text_btn, photo_btn)
    keyboard.add(video_btn, audio_btn)
    keyboard.add(clear_btn)
    keyboard.add(back_btn)
    
    return keyboard

def require_subscription(func):
    def wrapper(message):
        if not memory.settings.get('required_channel') or not memory.settings.get('subscription_enabled', False):
            return func(message)
            
        user_id = message.from_user.id
        
        if memory.is_vip(user_id) or memory.is_admin(user_id):
            return func(message)
        
        if not check_subscription(user_id):
            subscription_msg = f"""
📢 **اشتراك إجباري مطلوب!**

🔐 للوصول إلى موبي، يجب الاشتراك في قناتنا أولاً:

{memory.settings['required_channel']}

✅ بعد الاشتراك، اضغط على زر "تحقق من الاشتراك"
            """
            bot.send_message(
                message.chat.id, 
                subscription_msg, 
                reply_markup=create_subscription_button(),
                parse_mode='Markdown'
            )
            return
        return func(message)
    return wrapper

def send_welcome_message(chat_id, user_id):
    """إرسال رسالة الترحيب المخصصة"""
    welcome_content = memory.settings.get('welcome_content', {})
    welcome_type = welcome_content.get('type', 'text')
    content = welcome_content.get('content', '')
    
    if not content:
        # رسالة ترحيب افتراضية
        handle_start_type(chat_id, user_id, force_text=True)
        return
    
    try:
        if welcome_type == 'text':
            bot.send_message(chat_id, content, parse_mode='Markdown', reply_markup=create_main_menu() if not memory.is_admin(user_id) else create_admin_panel())
        elif welcome_type == 'photo':
            bot.send_photo(chat_id, content, parse_mode='Markdown', reply_markup=create_main_menu() if not memory.is_admin(user_id) else create_admin_panel())
        elif welcome_type == 'video':
            bot.send_video(chat_id, content, parse_mode='Markdown', reply_markup=create_main_menu() if not memory.is_admin(user_id) else create_admin_panel())
        elif welcome_type == 'audio':
            bot.send_audio(chat_id, content, parse_mode='Markdown', reply_markup=create_main_menu() if not memory.is_admin(user_id) else create_admin_panel())
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الترحيب: {e}")
        # Fallback إلى الرسالة النصية
        handle_start_type(chat_id, user_id, force_text=True)

def handle_start_type(chat_id, user_id, force_text=False):
    """معالجة رسالة البداية مع تحديد النوع"""
    user_status = ""
    if memory.is_vip(user_id):
        user_status = "🌟 **أنت مستخدم VIP** - وصول غير محدود!\n"
    elif memory.is_admin(user_id):
        user_status = "🛡️ **أنت مشرف** - صلاحيات كاملة!\n"
    else:
        can_send, status = memory.can_send_message(user_id)
        user_status = f"🔓 **وضع مجاني** - {status}\n"
    
    welcome_text = f"""
🤖 **مرحباً! أنا موبي**

{user_status}
⚡ **المميزات:**
✅ ذكاء اصطناعي متقدم
✅ دعم عربي كامل
✅ ذاكرة محادثات
✅ سرعة فائقة

💡 **الأوامر:**
/start - بدء المحادثة
/help - المساعدة  
/status - حالة حسابك
/upgrade - ترقية إلى VIP
/memory - إدارة الذاكرة
/new - محادثة جديدة
/developer - المطور

👑 **المطور:** {DEVELOPER_USERNAME}
    """
    
    if force_text or not memory.settings.get('welcome_content', {}).get('content'):
        if memory.is_admin(user_id):
            bot.send_message(chat_id, welcome_text, reply_markup=create_admin_panel(), parse_mode='Markdown')
        else:
            bot.send_message(chat_id, welcome_text, reply_markup=create_main_menu(), parse_mode='Markdown')
    else:
        send_welcome_message(chat_id, user_id)

@bot.message_handler(commands=['start'])
@require_subscription
def handle_start(message):
    try:
        memory.update_user_stats(
            message.from_user.id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            "/start"
        )
        
        send_welcome_message(message.chat.id, message.from_user.id)
            
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

# ... (جميع الدوال الأخرى تبقى كما هي مع التعديلات البسيطة)

# حالات المستخدم
broadcast_state = {}
admin_state = {}
ban_state = {}
vip_state = {}
settings_state = {}
points_state = {}
send_user_state = {}
welcome_state = {}

@bot.message_handler(func=lambda message: True)
@require_subscription  
def handle_all_messages(message):
    try:
        user_id = message.from_user.id
        
        # معالجة البث
        if user_id in broadcast_state:
            broadcast_type = broadcast_state[user_id]['type']
            success_count = 0
            total_users = len(memory.user_stats)
            failed_users = []
            
            for chat_id in memory.user_stats.keys():
                if chat_id == user_id:  # تخطي المرسل
                    continue
                try:
                    if broadcast_type == 'text' and message.text:
                        bot.send_message(chat_id, f"📢 إشعار من الإدارة:\n\n{message.text}")
                    elif broadcast_type == 'photo' and message.photo:
                        bot.send_photo(chat_id, message.photo[-1].file_id, caption=message.caption or "📢 إشعار من الإدارة")
                    elif broadcast_type == 'video' and message.video:
                        bot.send_video(chat_id, message.video.file_id, caption=message.caption or "📢 إشعار من الإدارة")
                    elif broadcast_type == 'audio' and message.audio:
                        bot.send_audio(chat_id, message.audio.file_id, caption=message.caption or "📢 إشعار من الإدارة")
                    elif broadcast_type == 'document' and message.document:
                        bot.send_document(chat_id, message.document.file_id, caption=message.caption or "📢 إشعار من الإدارة")
                    success_count += 1
                except Exception as e:
                    failed_users.append(chat_id)
                    continue
            
            result_text = f"✅ تم إرسال البث إلى {success_count}/{total_users} مستخدم"
            if failed_users:
                result_text += f"\n❌ فشل الإرسال لـ {len(failed_users)} مستخدم"
            
            bot.send_message(user_id, result_text)
            broadcast_state.pop(user_id, None)
            return
        
        # معالجة إرسال لمستخدم معين
        if user_id in send_user_state:
            if send_user_state[user_id]['step'] == 'waiting_user':
                try:
                    target_user_id = int(message.text)
                    send_user_state[user_id]['target_user'] = target_user_id
                    send_user_state[user_id]['step'] = 'waiting_content'
                    bot.send_message(user_id, "📤 أرسل المحتوى الذي تريد إرساله:")
                    return
                except:
                    bot.send_message(user_id, "❌ أدخل رقم مستخدم صحيح!")
                    return
            
            elif send_user_state[user_id]['step'] == 'waiting_content':
                target_user_id = send_user_state[user_id]['target_user']
                try:
                    if message.text:
                        bot.send_message(target_user_id, f"📩 رسالة من الإدارة:\n\n{message.text}")
                    elif message.photo:
                        bot.send_photo(target_user_id, message.photo[-1].file_id, caption=message.caption or "📩 رسالة من الإدارة")
                    elif message.video:
                        bot.send_video(target_user_id, message.video.file_id, caption=message.caption or "📩 رسالة من الإدارة")
                    elif message.audio:
                        bot.send_audio(target_user_id, message.audio.file_id, caption=message.caption or "📩 رسالة من الإدارة")
                    elif message.document:
                        bot.send_document(target_user_id, message.document.file_id, caption=message.caption or "📩 رسالة من الإدارة")
                    
                    bot.send_message(user_id, "✅ تم إرسال الرسالة للمستخدم")
                except:
                    bot.send_message(user_id, "❌ فشل في إرسال الرسالة!")
                
                send_user_state.pop(user_id, None)
                return
        
        # معالجة الترحيب المخصص
        if user_id in welcome_state:
            welcome_type = welcome_state[user_id]
            try:
                if welcome_type == 'text' and message.text:
                    memory.update_settings({'welcome_content': {'type': 'text', 'content': message.text}})
                    bot.send_message(user_id, "✅ تم حفظ النص الترحيبي")
                elif welcome_type == 'photo' and message.photo:
                    memory.update_settings({'welcome_content': {'type': 'photo', 'content': message.photo[-1].file_id}})
                    bot.send_message(user_id, "✅ تم حفظ الصورة الترحيبية")
                elif welcome_type == 'video' and message.video:
                    memory.update_settings({'welcome_content': {'type': 'video', 'content': message.video.file_id}})
                    bot.send_message(user_id, "✅ تم حفظ الفيديو الترحيبي")
                elif welcome_type == 'audio' and message.audio:
                    memory.update_settings({'welcome_content': {'type': 'audio', 'content': message.audio.file_id}})
                    bot.send_message(user_id, "✅ تم حفظ الصوت الترحيبي")
                else:
                    bot.send_message(user_id, "❌ أرسل المحتوى المناسب للنوع المحدد")
            except Exception as e:
                bot.send_message(user_id, f"❌ خطأ في حفظ المحتوى: {e}")
            welcome_state.pop(user_id, None)
            return
        
        # ... (بقية معالجات الحالات)
        
        # معالجة الرسائل العادية
        memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, message.text)
        
        if memory.is_banned(user_id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام البوت.")
            return
        
        can_send, status = memory.can_send_message(user_id)
        if not can_send:
            bot.send_message(message.chat.id, f"❌ انتهت رسائلك المجانية! ({status})\n\n💎 ترقى إلى VIP للاستخدام غير المحدود!\n/upgrade للترقية")
            return
        
        bot.send_chat_action(message.chat.id, 'typing')
        
        response = AIService.generate_response(user_id, message.text)
        
        if response:
            bot.send_message(message.chat.id, response)
        
        logger.info(f"💬 معالجة رسالة من {message.from_user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في المعالجة: {e}")

# معالجة الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if call.data == "check_subscription":
        if check_subscription(user_id):
            bot.answer_callback_query(call.id, "✅ مشترك! يمكنك استخدام البوت الآن.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            handle_start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد! اشترك ثم اضغط مرة أخرى.", show_alert=True)
    
    elif call.data == "user_help":
        handle_help(call.message)
        bot.answer_callback_query(call.id, "📚 المساعدة")
    
    elif call.data == "user_status":
        handle_status(call.message)
        bot.answer_callback_query(call.id, "📊 الحالة")
    
    elif call.data == "user_vip":
        handle_upgrade(call.message)
        bot.answer_callback_query(call.id, "💎 الترقية")
    
    elif not memory.is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية!", show_alert=True)
        return
    
    elif call.data == "admin_stats":
        show_admin_stats(call)
    elif call.data == "admin_users":
        show_users_list(call)
    elif call.data == "admin_manage":
        show_admins_management(call)
    elif call.data == "admin_conversations":
        show_conversations_list(call)
    elif call.data == "admin_vip":
        show_vip_management(call)
    elif call.data == "admin_broadcast":
        show_broadcast_menu(call)
    elif call.data == "admin_ban":
        show_ban_management(call)
    elif call.data == "admin_points":
        show_points_menu(call)
    elif call.data == "admin_settings":
        show_settings_menu(call)
    elif call.data == "admin_back":
        show_admin_panel(call)
    
    # أزرار البث
    elif call.data.startswith("broadcast_"):
        broadcast_type = call.data.split("_")[1]
        broadcast_state[user_id] = {'type': broadcast_type}
        bot.send_message(user_id, f"📢 أرسل {'النص' if broadcast_type == 'text' else 'الصورة' if broadcast_type == 'photo' else 'الفيديو' if broadcast_type == 'video' else 'الصوت' if broadcast_type == 'audio' else 'الملف'} الذي تريد بثه:")
        bot.answer_callback_query(call.id, f"📢 بث {broadcast_type}")
    
    # أزرار الترحيب
    elif call.data == "settings_welcome":
        show_welcome_menu(call)
    elif call.data.startswith("welcome_"):
        welcome_type = call.data.split("_")[1]
        if welcome_type == 'clear':
            memory.update_settings({'welcome_content': {'type': 'text', 'content': ''}})
            bot.answer_callback_query(call.id, "✅ تم مسح المحتوى الترحيبي")
            show_welcome_menu(call)
        else:
            welcome_state[user_id] = welcome_type
            bot.send_message(user_id, f"🎉 أرسل {'النص' if welcome_type == 'text' else 'الصورة' if welcome_type == 'photo' else 'الفيديو' if welcome_type == 'video' else 'الصوت'} الترحيبي:")
            bot.answer_callback_query(call.id, f"🎉 ترحيب {welcome_type}")
    
    # ... (بقية معالجات الأزرار)

def show_welcome_menu(call):
    welcome_content = memory.settings.get('welcome_content', {})
    current_type = welcome_content.get('type', 'text')
    has_content = bool(welcome_content.get('content'))
    
    welcome_text = f"""
🎉 **إعدادات الترحيب**

📋 **النوع الحالي:** {current_type}
✅ **الحالة:** {'🟢 معين' if has_content else '🔴 غير معين'}

🛠 **اختر نوع المحتوى الترحيبي:**
    """
    bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id,
                        reply_markup=create_welcome_menu(), parse_mode='Markdown')
    bot.answer_callback_query(call.id, "🎉 الترحيب")

# دوال التنظيف
def cleanup_old_data():
    """تنظيف البيانات القديمة"""
    while True:
        try:
            # تنظيف المحادثات القديمة
            memory.cleanup_old_conversations()
            
            # تنظيف الملفات المؤقتة
            for user_id in list(memory.temp_files.keys()):
                if datetime.now() - memory.temp_files[user_id] > timedelta(minutes=10):
                    del memory.temp_files[user_id]
            
            logger.info("🧹 تم تنظيف البيانات القديمة")
            time.sleep(300)  # انتظر 5 دقائق
        except Exception as e:
            logger.error(f"❌ خطأ في التنظيف: {e}")
            time.sleep(60)

def keep_alive():
    """الحفاظ على البوت حياً"""
    while True:
        try:
            logger.info("🫀 البوت حي ويعمل...")
            time.sleep(300)
        except Exception as e:
            logger.error(f"❌ خطأ في الحفاظ على الحياة: {e}")
            time.sleep(60)

def main():
    logger.info("🚀 بدء تشغيل موبي مع جميع الميزات...")
    
    try:
        # إزالة أي instance سابقة
        bot.remove_webhook()
        time.sleep(2)
        
        # اختبار النظام
        try:
            test_url = f"{AIService.API_URL}?text=test"
            response = requests.get(test_url, timeout=10)
            logger.info(f"✅ النظام يعمل: {response.status_code}")
        except Exception as api_error:
            logger.warning(f"⚠️ النظام غير متاح: {api_error}")
        
        logger.info(f"✅ موبي جاهز - المطور: {DEVELOPER_USERNAME}")
        logger.info("🤖 البوت يعمل الآن ويستمع للرسائل...")
        
        # بدء خيوط الخدمة
        threading.Thread(target=keep_alive, daemon=True).start()
        threading.Thread(target=cleanup_old_data, daemon=True).start()
        
        # تشغيل البوت
        bot.infinity_polling(timeout=60, long_polling_timeout=60, restart_on_change=True)
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
