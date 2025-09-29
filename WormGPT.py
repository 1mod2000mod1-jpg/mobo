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
DEVELOPER_ID = 6521966233

# إعدادات البوت
BOT_SETTINGS = {
    "required_channel": "",
    "free_messages": 50,
    "welcome_image": "",
    "welcome_video": "",
    "welcome_audio": "",
    "welcome_document": "",
    "welcome_text": "",
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
        
        # بدء تنظيف المحادثات القديمة
        self.start_cleanup_thread()
    
    def start_cleanup_thread(self):
        """بدء خيط لتنظيف المحادثات القديمة تلقائياً"""
        def cleanup_old_conversations():
            while True:
                try:
                    self.cleanup_old_messages()
                    time.sleep(600)  # تنظيف كل 10 دقائق
                except Exception as e:
                    logger.error(f"❌ خطأ في تنظيف المحادثات: {e}")
                    time.sleep(300)
        
        thread = threading.Thread(target=cleanup_old_conversations, daemon=True)
        thread.start()
        logger.info("✅ بدأ تنظيف المحادثات القديمة تلقائياً")
    
    def cleanup_old_messages(self):
        """حذف المحادثات الأقدم من 10 دقائق"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=10)
            deleted_count = 0
            
            for user_file in self.workspace.glob("user_*.json"):
                try:
                    with open(user_file, 'r', encoding='utf-8') as f:
                        conversation = json.load(f)
                    
                    # تصفية الرسائل الأحدث من 10 دقائق
                    filtered_conversation = []
                    for msg in conversation:
                        msg_time = datetime.fromisoformat(msg['timestamp'])
                        if msg_time > cutoff_time:
                            filtered_conversation.append(msg)
                        else:
                            deleted_count += 1
                    
                    # حفظ المحادثة المصفاة
                    if filtered_conversation:
                        with open(user_file, 'w', encoding='utf-8') as f:
                            json.dump(filtered_conversation, f, ensure_ascii=False, indent=2)
                    else:
                        # حذف الملف إذا كانت المحادثة فارغة
                        user_file.unlink()
                        
                except Exception as e:
                    logger.error(f"❌ خطأ في تنظيف ملف {user_file}: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"🧹 تم تنظيف {deleted_count} رسالة قديمة")
                
        except Exception as e:
            logger.error(f"❌ خطأ عام في التنظيف: {e}")
    
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

# تهيئة النظام
memory = MemorySystem()

# نظام الذكاء الاصطناعي
class AIService:
    API_URL = "http://sii3.top/DARK/api/wormgpt.php"
    
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
                
                # تنظيف الرد من المعلومات غير المرغوب فيها
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
    welcome_btn = InlineKeyboardButton("🎊 الترحيب", callback_data="settings_welcome")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    
    keyboard.add(channel_btn, subscription_btn)
    keyboard.add(messages_btn, welcome_btn)
    keyboard.add(back_btn)
    
    return keyboard

def create_welcome_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    text_btn = InlineKeyboardButton("📝 نص ترحيب", callback_data="welcome_text")
    photo_btn = InlineKeyboardButton("🖼️ صورة ترحيب", callback_data="welcome_photo")
    video_btn = InlineKeyboardButton("🎥 فيديو ترحيب", callback_data="welcome_video")
    audio_btn = InlineKeyboardButton("🎵 صوت ترحيب", callback_data="welcome_audio")
    document_btn = InlineKeyboardButton("📄 ملف ترحيب", callback_data="welcome_document")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings")
    
    keyboard.add(text_btn, photo_btn)
    keyboard.add(video_btn, audio_btn)
    keyboard.add(document_btn)
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
    """إرسال رسالة ترحيبية مع الوسائط المتعددة"""
    try:
        user_status = ""
        if memory.is_vip(user_id):
            user_status = "🌟 **أنت مستخدم VIP** - وصول غير محدود!\n"
        elif memory.is_admin(user_id):
            user_status = "🛡️ **أنت مشرف** - صلاحيات كاملة!\n"
        else:
            can_send, status = memory.can_send_message(user_id)
            user_status = f"🔓 **وضع مجاني** - {status}\n"
        
        welcome_text = memory.settings.get('welcome_text') or f"""
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
        
        # إرسال الوسائط المتعددة حسب الإعدادات
        sent = False
        
        # محاولة إرسال فيديو أولاً
        if memory.settings.get('welcome_video'):
            try:
                bot.send_video(
                    chat_id,
                    memory.settings['welcome_video'],
                    caption=welcome_text,
                    reply_markup=create_admin_panel() if memory.is_admin(user_id) else create_main_menu(),
                    parse_mode='Markdown'
                )
                sent = True
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال الفيديو الترحيبي: {e}")
        
        # إذا لم ينجح الفيديو، حاول إرسال صورة
        if not sent and memory.settings.get('welcome_photo'):
            try:
                bot.send_photo(
                    chat_id,
                    memory.settings['welcome_photo'],
                    caption=welcome_text,
                    reply_markup=create_admin_panel() if memory.is_admin(user_id) else create_main_menu(),
                    parse_mode='Markdown'
                )
                sent = True
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال الصورة الترحيبية: {e}")
        
        # إذا لم تنجح الصورة، حاول إرسال صوت
        if not sent and memory.settings.get('welcome_audio'):
            try:
                bot.send_audio(
                    chat_id,
                    memory.settings['welcome_audio'],
                    caption=welcome_text,
                    reply_markup=create_admin_panel() if memory.is_admin(user_id) else create_main_menu(),
                    parse_mode='Markdown'
                )
                sent = True
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال الصوت الترحيبي: {e}")
        
        # إذا لم ينجح الصوت، حاول إرسال ملف
        if not sent and memory.settings.get('welcome_document'):
            try:
                bot.send_document(
                    chat_id,
                    memory.settings['welcome_document'],
                    caption=welcome_text,
                    reply_markup=create_admin_panel() if memory.is_admin(user_id) else create_main_menu(),
                    parse_mode='Markdown'
                )
                sent = True
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال الملف الترحيبي: {e}")
        
        # إذا لم تنجح أي وسائط، أرسل نص فقط
        if not sent:
            if memory.is_admin(user_id):
                bot.send_message(chat_id, welcome_text, reply_markup=create_admin_panel(), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, welcome_text, reply_markup=create_main_menu(), parse_mode='Markdown')
                
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الترحيب: {e}")
        # إرسال رسالة بديلة في حالة الخطأ
        bot.send_message(chat_id, "🤖 مرحباً! أنا موبي البوت الذكي. كيف يمكنني مساعدتك؟")

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

@bot.message_handler(commands=['help'])
@require_subscription
def handle_help(message):
    help_text = f"""
🆘 **مساعدة موبي**

📋 **الأوامر:**
/start - بدء المحادثة
/help - المساعدة
/status - حالة حسابك
/upgrade - ترقية إلى VIP
/memory - إدارة الذاكرة
/new - محادثة جديدة
/developer - المطور

💡 **الوضع المجاني:**
• {memory.settings.get('free_messages', 50)} رسالة مجانية
• إمكانية الترقية

💎 **مميزات VIP:**
• رسائل غير محدودة
• أولوية في الردود
• دعم فوري

👑 **المطور:** {DEVELOPER_USERNAME}
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/help")

@bot.message_handler(commands=['upgrade'])
def handle_upgrade(message):
    if memory.is_vip(message.from_user.id):
        vip_text = f"""
🌟 **أنت مستخدم VIP بالفعل!**

🎁 **مميزاتك:**
✅ وصول غير محدود
✅ أولوية في الردود
✅ دعم فوري
✅ مميزات حصرية

👑 للمزيد: {DEVELOPER_USERNAME}
        """
    else:
        vip_text = f"""
💎 **ترقية إلى VIP**

🔓 **الوضع الحالي:** مجاني ({memory.settings.get('free_messages', 50)} رسالة)
💫 **بعد الترقية:** غير محدود!

🎁 **مميزات VIP:**
✅ رسائل غير محدودة
✅ أولوية في الردود
✅ دعم فوري
✅ مميزات حصرية

💰 **للترقية:** تواصل مع {DEVELOPER_USERNAME}
        """
    
    bot.send_message(
        message.chat.id, 
        vip_text, 
        parse_mode='Markdown',
        reply_markup=create_developer_button()
    )
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/upgrade")

@bot.message_handler(commands=['status'])
@require_subscription
def handle_status(message):
    user_id = message.from_user.id
    user_stats = memory.user_stats.get(user_id, {})
    
    can_send, status = memory.can_send_message(user_id)
    
    status_text = f"""
📊 **حالة حسابك**

👤 **المستخدم:** {user_stats.get('first_name', 'بدون اسم')}
🆔 **المعرف:** @{user_stats.get('username', 'بدون معرف')}
📅 **أول ظهور:** {user_stats.get('first_seen', 'غير معروف')}
🔄 **آخر ظهور:** {user_stats.get('last_seen', 'غير معروف')}

📨 **الرسائل:** {user_stats.get('message_count', 0)}
💬 **الحالة:** {status}

🎖️ **الرتبة:** {'🛡️ مشرف' if memory.is_admin(user_id) else '🌟 VIP' if memory.is_vip(user_id) else '🔓 مجاني'}
🎯 **النقاط:** {user_stats.get('points', 0)}
    """
    
    bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
    memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, "/status")

@bot.message_handler(commands=['developer'])
def handle_developer(message):
    developer_text = f"""
👑 **مطور موبي**

💫 **السيد موبي**
{DEVELOPER_USERNAME}

⚡ **مطور محترف**
🎯 **متخصص في الذكاء الاصطناعي**
💎 **صانع البوتات المتقدمة**

📧 **للتواصل:** {DEVELOPER_USERNAME}
    """
    bot.send_message(
        message.chat.id, 
        developer_text, 
        parse_mode='Markdown',
        reply_markup=create_developer_button()
    )
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/developer")

@bot.message_handler(commands=['memory'])
@require_subscription
def handle_memory(message):
    user_id = message.from_user.id
    conversation = memory.get_user_conversation(user_id)
    
    if not conversation:
        memory_text = "💭 **الذاكرة فارغة**\n\nلم تبدأ محادثة بعد!"
    else:
        memory_text = f"💭 **آخر {len(conversation)} رسالة في الذاكرة:**\n\n"
        for i, msg in enumerate(conversation[-5:], 1):
            role = "🧑‍💻 أنت" if msg['role'] == 'user' else "🤖 موبي"
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            memory_text += f"{i}. {role}: {content}\n\n"
    
    keyboard = InlineKeyboardMarkup()
    clear_btn = InlineKeyboardButton("🗑️ مسح الذاكرة", callback_data="clear_memory")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="user_back")
    keyboard.add(clear_btn, back_btn)
    
    bot.send_message(message.chat.id, memory_text, reply_markup=keyboard, parse_mode='Markdown')
    memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, "/memory")

@bot.message_handler(commands=['new'])
@require_subscription
def handle_new(message):
    user_id = message.from_user.id
    memory.clear_conversation(user_id)
    bot.send_message(message.chat.id, "🔄 **بدأت محادثة جديدة!**\n\n💫 ذاكرتك نظيفة الآن، يمكنك البدء من جديد!", parse_mode='Markdown')
    memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, "/new")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    user_id = message.from_user.id
    if not memory.is_admin(user_id):
        bot.send_message(message.chat.id, "❌ **ليس لديك صلاحية الوصول!**\n\nهذا القسم للمشرفين فقط.", parse_mode='Markdown')
        return
    
    admin_text = f"""
🛡️ **لوحة التحكم - موبي**

📊 **إحصائيات البوت:**
👥 **المستخدمين:** {memory.get_total_users()}
🔄 **النشط اليوم:** {memory.get_active_today()}
🌟 **VIP:** {len(memory.vip_users)}
🛡️ **المشرفين:** {len(memory.admins)}
🚫 **المحظورين:** {len(memory.banned_users)}

⚡ **اختر من القائمة:**
    """
    bot.send_message(message.chat.id, admin_text, reply_markup=create_admin_panel(), parse_mode='Markdown')
    memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, "/admin")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'audio', 'document'])
@require_subscription
def handle_all_messages(message):
    user_id = message.from_user.id
    username = message.from_user.username or "بدون معرف"
    first_name = message.from_user.first_name or "بدون اسم"
    
    if memory.is_banned(user_id):
        bot.send_message(message.chat.id, "❌ **تم حظرك من استخدام موبي.**\n\nللاستفسار تواصل مع المطور.", parse_mode='Markdown')
        return
    
    if message.content_type == 'text':
        message_text = message.text
    else:
        if message.caption:
            message_text = f"[{message.content_type.upper()}] {message.caption}"
        else:
            message_text = f"[{message.content_type.upper()}] تم إرسال وسائط"
    
    memory.update_user_stats(user_id, username, first_name, message_text)
    
    if message.content_type == 'text':
        bot.send_chat_action(message.chat.id, 'typing')
        
        try:
            response = AIService.generate_response(user_id, message.text)
            bot.reply_to(message, response)
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
            bot.reply_to(message, "⚠️ عذراً، حدث خطأ في المعالجة. جرب مرة أخرى!")
    else:
        bot.reply_to(message, "📁 **تم استلام الوسائط بنجاح!**\n\n💫 موبي يدعم الوسائط، لكن الذكاء الاصطناعي يحتاج إلى نص للرد. اكتب سؤالك!", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        if call.data == "user_help":
            handle_help(call.message)
            bot.answer_callback_query(call.id, "🆘 المساعدة")
            
        elif call.data == "user_status":
            handle_status(call.message)
            bot.answer_callback_query(call.id, "📊 الحالة")
            
        elif call.data == "user_vip":
            handle_upgrade(call.message)
            bot.answer_callback_query(call.id, "💎 الترقية")
            
        elif call.data == "user_back":
            send_welcome_message(chat_id, user_id)
            bot.answer_callback_query(call.id, "🔙 رجوع")
            
        elif call.data == "clear_memory":
            memory.clear_conversation(user_id)
            bot.answer_callback_query(call.id, "🗑️ تم مسح الذاكرة")
            bot.send_message(chat_id, "✅ **تم مسح الذاكرة بنجاح!**\n\n💫 يمكنك البدء بمحادثة جديدة.", parse_mode='Markdown')
            
        elif call.data == "check_subscription":
            if check_subscription(user_id):
                bot.answer_callback_query(call.id, "✅ تم الاشتراك!")
                send_welcome_message(chat_id, user_id)
            else:
                bot.answer_callback_query(call.id, "❌ لم تشترك بعد!")
                
        elif call.data.startswith("admin_"):
            if not memory.is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية!")
                return
                
            if call.data == "admin_stats":
                total_users = memory.get_total_users()
                active_today = memory.get_active_today()
                total_vip = len(memory.vip_users)
                total_admins = len(memory.admins)
                total_banned = len(memory.banned_users)
                
                stats_text = f"""
📊 **إحصائيات متقدمة - موبي**

👥 **المستخدمين:** {total_users}
🔄 **النشط اليوم:** {active_today}
🌟 **VIP:** {total_vip}
🛡️ **المشرفين:** {total_admins}
🚫 **المحظورين:** {total_banned}

💬 **الرسائل اليوم:** جاري العد...
⚡ **أداء النظام:** ممتاز
                """
                bot.edit_message_text(
                    stats_text,
                    chat_id,
                    message_id,
                    reply_markup=create_admin_panel(),
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "📊 الإحصائيات")
                
            elif call.data == "admin_users":
                users_text = f"👥 **آخر 10 مستخدمين:**\n\n"
                recent_users = list(memory.user_stats.items())[-10:]
                
                for user_id, stats in recent_users:
                    status = "🛡️" if memory.is_admin(user_id) else "🌟" if memory.is_vip(user_id) else "🔓"
                    users_text += f"{status} {stats.get('first_name', 'بدون اسم')} (@{stats.get('username', 'بدون معرف')})\n"
                    users_text += f"   📨 {stats.get('message_count', 0)} رسالة | 🎯 {stats.get('points', 0)} نقطة\n\n"
                
                bot.edit_message_text(
                    users_text,
                    chat_id,
                    message_id,
                    reply_markup=create_admin_panel(),
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "👥 المستخدمين")
                
            elif call.data == "admin_manage":
                admins_list = memory.get_admins_list()
                admins_text = "🛡️ **قائمة المشرفين:**\n\n"
                
                for admin in admins_list:
                    admins_text += f"👑 {admin['first_name']} (@{admin['username']})\n"
                    admins_text += f"   📨 {admin['message_count']} رسالة | 🎯 {admin['points']} نقطة\n\n"
                
                keyboard = InlineKeyboardMarkup()
                add_admin_btn = InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")
                remove_admin_btn = InlineKeyboardButton("➖ إزالة مشرف", callback_data="remove_admin")
                back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
                keyboard.add(add_admin_btn, remove_admin_btn)
                keyboard.add(back_btn)
                
                bot.edit_message_text(
                    admins_text,
                    chat_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "🛡️ المشرفين")
                
            elif call.data == "admin_vip":
                vip_list = memory.get_vip_list()
                vip_text = "🌟 **قائمة VIP:**\n\n"
                
                for vip in vip_list:
                    vip_text += f"💎 {vip['first_name']} (@{vip['username']})\n"
                    vip_text += f"   📨 {vip['message_count']} رسالة | 🎯 {vip['points']} نقطة\n\n"
                
                keyboard = InlineKeyboardMarkup()
                add_vip_btn = InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")
                remove_vip_btn = InlineKeyboardButton("➖ إزالة VIP", callback_data="remove_vip")
                back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
                keyboard.add(add_vip_btn, remove_vip_btn)
                keyboard.add(back_btn)
                
                bot.edit_message_text(
                    vip_text,
                    chat_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "🌟 VIP")
                
            elif call.data == "admin_broadcast":
                broadcast_text = "📢 **نظام البث:**\n\n"
                broadcast_text += "يمكنك إرسال رسالة لجميع المستخدمين:\n"
                broadcast_text += "• 📝 نص\n• 🖼️ صورة\n• 🎥 فيديو\n• 🎵 صوت\n• 📄 ملف\n"
                
                bot.edit_message_text(
                    broadcast_text,
                    chat_id,
                    message_id,
                    reply_markup=create_broadcast_menu(),
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "📢 البث")
                
            elif call.data == "admin_ban":
                banned_text = "🚫 **إدارة المحظورين:**\n\n"
                banned_text += f"عدد المحظورين: {len(memory.banned_users)}\n\n"
                
                keyboard = InlineKeyboardMarkup()
                ban_user_btn = InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user")
                unban_user_btn = InlineKeyboardButton("✅ فك حظر", callback_data="unban_user")
                back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
                keyboard.add(ban_user_btn, unban_user_btn)
                keyboard.add(back_btn)
                
                bot.edit_message_text(
                    banned_text,
                    chat_id,
                    message_id,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "🚫 الحظر")
                
            elif call.data == "admin_points":
                points_text = "🎯 **نظام النقاط:**\n\n"
                points_text += "إدارة نقاط المستخدمين:\n"
                points_text += "• ➕ إضافة نقاط\n• ➖ نزع نقاط\n• 📤 إرسال لمستخدم\n"
                
                bot.edit_message_text(
                    points_text,
                    chat_id,
                    message_id,
                    reply_markup=create_points_menu(),
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "🎯 النقاط")
                
            elif call.data == "admin_settings":
                settings_text = f"""
⚙️ **إعدادات موبي:**

📢 **القناة:** {memory.settings.get('required_channel', 'غير معين')}
🔐 **الاشتراك:** {'مفعل' if memory.settings.get('subscription_enabled', False) else 'معطل'}
💬 **الرسائل المجانية:** {memory.settings.get('free_messages', 50)}
🎊 **الترحيب:** {'مفعل' if any([memory.settings.get('welcome_text'), memory.settings.get('welcome_photo'), memory.settings.get('welcome_video')]) else 'معطل'}

⚡ **اختر الإعداد الذي تريد تعديله:**
                """
                bot.edit_message_text(
                    settings_text,
                    chat_id,
                    message_id,
                    reply_markup=create_settings_menu(),
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "⚙️ الإعدادات")
                
            elif call.data == "admin_back":
                handle_admin(call.message)
                bot.answer_callback_query(call.id, "🔙 رجوع")
                
        elif call.data.startswith("settings_"):
            if not memory.is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية!")
                return
                
            if call.data == "settings_channel":
                msg = bot.send_message(chat_id, "📢 **إعداد القناة:**\n\nأرسل معرف القناة (مثال: @channel_username)", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_channel_setting)
                bot.answer_callback_query(call.id, "📢 القناة")
                
            elif call.data == "settings_subscription":
                current_status = memory.settings.get('subscription_enabled', False)
                memory.settings['subscription_enabled'] = not current_status
                memory.save_settings()
                
                status_text = "مفعل" if memory.settings['subscription_enabled'] else "معطل"
                bot.answer_callback_query(call.id, f"🔐 الاشتراك: {status_text}")
                bot.send_message(chat_id, f"✅ **تم {'تفعيل' if memory.settings['subscription_enabled'] else 'تعطيل'} الاشتراك الإجباري**", parse_mode='Markdown')
                
            elif call.data == "settings_messages":
                msg = bot.send_message(chat_id, "💬 **عدد الرسائل المجانية:**\n\nأرسل الرقم الجديد (مثال: 50)", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_messages_setting)
                bot.answer_callback_query(call.id, "💬 الرسائل")
                
            elif call.data == "settings_welcome":
                welcome_text = "🎊 **إعدادات الترحيب:**\n\n"
                welcome_text += "يمكنك إعداد:\n"
                welcome_text += "• 📝 نص ترحيب\n• 🖼️ صورة ترحيب\n• 🎥 فيديو ترحيب\n• 🎵 صوت ترحيب\n• 📄 ملف ترحيب\n"
                
                bot.edit_message_text(
                    welcome_text,
                    chat_id,
                    message_id,
                    reply_markup=create_welcome_menu(),
                    parse_mode='Markdown'
                )
                bot.answer_callback_query(call.id, "🎊 الترحيب")
                
        elif call.data.startswith("welcome_"):
            if not memory.is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية!")
                return
                
            if call.data == "welcome_text":
                msg = bot.send_message(chat_id, "📝 **نص الترحيب:**\n\nأرسل النص الجديد للترحيب", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_welcome_text)
                bot.answer_callback_query(call.id, "📝 النص")
                
            elif call.data == "welcome_photo":
                msg = bot.send_message(chat_id, "🖼️ **صورة الترحيب:**\n\nأرسل الصورة الجديدة للترحيب", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_welcome_photo)
                bot.answer_callback_query(call.id, "🖼️ الصورة")
                
            elif call.data == "welcome_video":
                msg = bot.send_message(chat_id, "🎥 **فيديو الترحيب:**\n\nأرسل الفيديو الجديد للترحيب", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_welcome_video)
                bot.answer_callback_query(call.id, "🎥 الفيديو")
                
            elif call.data == "welcome_audio":
                msg = bot.send_message(chat_id, "🎵 **صوت الترحيب:**\n\nأرسل الملف الصوتي الجديد للترحيب", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_welcome_audio)
                bot.answer_callback_query(call.id, "🎵 الصوت")
                
            elif call.data == "welcome_document":
                msg = bot.send_message(chat_id, "📄 **ملف الترحيب:**\n\nأرسل الملف الجديد للترحيب", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_welcome_document)
                bot.answer_callback_query(call.id, "📄 الملف")
                
        elif call.data.startswith("broadcast_"):
            if not memory.is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية!")
                return
                
            if call.data == "broadcast_text":
                msg = bot.send_message(chat_id, "📝 **بث نصي:**\n\nأرسل النص الذي تريد بثه لجميع المستخدمين", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_broadcast_text)
                bot.answer_callback_query(call.id, "📝 النص")
                
            elif call.data == "broadcast_photo":
                msg = bot.send_message(chat_id, "🖼️ **بث صورة:**\n\nأرسل الصورة مع التسمية التوضيحية للبث", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_broadcast_photo)
                bot.answer_callback_query(call.id, "🖼️ الصورة")
                
            elif call.data == "broadcast_video":
                msg = bot.send_message(chat_id, "🎥 **بث فيديو:**\n\nأرسل الفيديو مع التسمية التوضيحية للبث", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_broadcast_video)
                bot.answer_callback_query(call.id, "🎥 الفيديو")
                
            elif call.data == "broadcast_audio":
                msg = bot.send_message(chat_id, "🎵 **بث صوت:**\n\nأرسل الملف الصوتي مع التسمية التوضيحية للبث", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_broadcast_audio)
                bot.answer_callback_query(call.id, "🎵 الصوت")
                
            elif call.data == "broadcast_document":
                msg = bot.send_message(chat_id, "📄 **بث ملف:**\n\nأرسل الملف مع التسمية التوضيحية للبث", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_broadcast_document)
                bot.answer_callback_query(call.id, "📄 الملف")
                
        elif call.data.startswith("add_") or call.data.startswith("remove_"):
            if not memory.is_admin(user_id):
                bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية!")
                return
                
            if call.data == "add_admin":
                msg = bot.send_message(chat_id, "🛡️ **إضافة مشرف:**\n\nأرسل معرف المستخدم (user_id) للإضافة", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_add_admin)
                bot.answer_callback_query(call.id, "➕ مشرف")
                
            elif call.data == "remove_admin":
                msg = bot.send_message(chat_id, "🛡️ **إزالة مشرف:**\n\nأرسل معرف المستخدم (user_id) للإزالة", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_remove_admin)
                bot.answer_callback_query(call.id, "➖ مشرف")
                
            elif call.data == "add_vip":
                msg = bot.send_message(chat_id, "🌟 **إضافة VIP:**\n\nأرسل معرف المستخدم (user_id) للإضافة", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_add_vip)
                bot.answer_callback_query(call.id, "➕ VIP")
                
            elif call.data == "remove_vip":
                msg = bot.send_message(chat_id, "🌟 **إزالة VIP:**\n\nأرسل معرف المستخدم (user_id) للإزالة", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_remove_vip)
                bot.answer_callback_query(call.id, "➖ VIP")
                
            elif call.data == "ban_user":
                msg = bot.send_message(chat_id, "🚫 **حظر مستخدم:**\n\nأرسل معرف المستخدم (user_id) للحظر", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_ban_user)
                bot.answer_callback_query(call.id, "🚫 حظر")
                
            elif call.data == "unban_user":
                msg = bot.send_message(chat_id, "✅ **فك حظر:**\n\nأرسل معرف المستخدم (user_id) لفك الحظر", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_unban_user)
                bot.answer_callback_query(call.id, "✅ فك حظر")
                
            elif call.data == "add_points":
                msg = bot.send_message(chat_id, "➕ **إضافة نقاط:**\n\nأرسل معرف المستخدم وعدد النقاط (مثال: 123456 100)", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_add_points)
                bot.answer_callback_query(call.id, "➕ نقاط")
                
            elif call.data == "remove_points":
                msg = bot.send_message(chat_id, "➖ **نزع نقاط:**\n\nأرسل معرف المستخدم وعدد النقاط (مثال: 123456 50)", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_remove_points)
                bot.answer_callback_query(call.id, "➖ نقاط")
                
            elif call.data == "send_to_user":
                msg = bot.send_message(chat_id, "📤 **إرسال لمستخدم:**\n\nأرسل معرف المستخدم والرسالة (مثال: 123456 مرحبا!)", parse_mode='Markdown')
                bot.register_next_step_handler(msg, process_send_to_user)
                bot.answer_callback_query(call.id, "📤 إرسال")
                
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الاستدعاء: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!")

# دوال معالجة الإعدادات
def process_channel_setting(message):
    try:
        channel_username = message.text.strip()
        if not channel_username.startswith('@'):
            channel_username = '@' + channel_username
            
        memory.settings['required_channel'] = channel_username
        memory.save_settings()
        
        bot.send_message(message.chat.id, f"✅ **تم تعيين القناة:** {channel_username}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في تعيين القناة: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في تعيين القناة!**", parse_mode='Markdown')

def process_messages_setting(message):
    try:
        new_limit = int(message.text.strip())
        memory.settings['free_messages'] = new_limit
        memory.save_settings()
        
        # تحديث حدود المستخدمين الحاليين
        for user_id in memory.user_stats:
            if not memory.is_vip(user_id) and not memory.is_admin(user_id):
                memory.user_stats[user_id]['message_limit'] = new_limit
        memory.save_user_stats()
        
        bot.send_message(message.chat.id, f"✅ **تم تعيين الرسائل المجانية:** {new_limit}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال رقم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في تعيين الرسائل: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في تعيين الرسائل!**", parse_mode='Markdown')

def process_welcome_text(message):
    try:
        welcome_text = message.text
        memory.settings['welcome_text'] = welcome_text
        memory.save_settings()
        
        bot.send_message(message.chat.id, "✅ **تم حفظ نص الترحيب!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ نص الترحيب: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في حفظ النص!**", parse_mode='Markdown')

def process_welcome_photo(message):
    try:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            memory.settings['welcome_photo'] = file_id
            memory.save_settings()
            bot.send_message(message.chat.id, "✅ **تم حفظ صورة الترحيب!**", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال صورة!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ صورة الترحيب: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في حفظ الصورة!**", parse_mode='Markdown')

def process_welcome_video(message):
    try:
        if message.content_type == 'video':
            file_id = message.video.file_id
            memory.settings['welcome_video'] = file_id
            memory.save_settings()
            bot.send_message(message.chat.id, "✅ **تم حفظ فيديو الترحيب!**", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال فيديو!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ فيديو الترحيب: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في حفظ الفيديو!**", parse_mode='Markdown')

def process_welcome_audio(message):
    try:
        if message.content_type == 'audio':
            file_id = message.audio.file_id
            memory.settings['welcome_audio'] = file_id
            memory.save_settings()
            bot.send_message(message.chat.id, "✅ **تم حفظ صوت الترحيب!**", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال ملف صوتي!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ صوت الترحيب: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في حفظ الصوت!**", parse_mode='Markdown')

def process_welcome_document(message):
    try:
        if message.content_type == 'document':
            file_id = message.document.file_id
            memory.settings['welcome_document'] = file_id
            memory.save_settings()
            bot.send_message(message.chat.id, "✅ **تم حفظ ملف الترحيب!**", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال ملف!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ ملف الترحيب: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في حفظ الملف!**", parse_mode='Markdown')

# دوال معالجة البث
def process_broadcast_text(message):
    try:
        broadcast_text = message.text
        users = list(memory.user_stats.keys())
        success_count = 0
        fail_count = 0
        
        progress_msg = bot.send_message(message.chat.id, f"📤 **جاري البث...**\n\n👥 المستهدفين: {len(users)}", parse_mode='Markdown')
        
        for user_id in users:
            try:
                if memory.is_banned(user_id):
                    continue
                    
                bot.send_message(user_id, broadcast_text, parse_mode='Markdown')
                success_count += 1
                time.sleep(0.1)  # تجنب التحميل الزائد
                
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ خطأ في البث للمستخدم {user_id}: {e}")
        
        bot.edit_message_text(
            f"✅ **تم البث بنجاح!**\n\n✅ الناجح: {success_count}\n❌ الفاشل: {fail_count}",
            message.chat.id,
            progress_msg.message_id,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"❌ خطأ في البث النصي: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في البث!**", parse_mode='Markdown')

def process_broadcast_photo(message):
    try:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            caption = message.caption or ""
            users = list(memory.user_stats.keys())
            success_count = 0
            fail_count = 0
            
            progress_msg = bot.send_message(message.chat.id, f"📤 **جاري بث الصورة...**\n\n👥 المستهدفين: {len(users)}", parse_mode='Markdown')
            
            for user_id in users:
                try:
                    if memory.is_banned(user_id):
                        continue
                        
                    bot.send_photo(user_id, file_id, caption=caption, parse_mode='Markdown')
                    success_count += 1
                    time.sleep(0.1)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ خطأ في بث الصورة للمستخدم {user_id}: {e}")
            
            bot.edit_message_text(
                f"✅ **تم بث الصورة بنجاح!**\n\n✅ الناجح: {success_count}\n❌ الفاشل: {fail_count}",
                message.chat.id,
                progress_msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال صورة!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في بث الصورة: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في البث!**", parse_mode='Markdown')

def process_broadcast_video(message):
    try:
        if message.content_type == 'video':
            file_id = message.video.file_id
            caption = message.caption or ""
            users = list(memory.user_stats.keys())
            success_count = 0
            fail_count = 0
            
            progress_msg = bot.send_message(message.chat.id, f"📤 **جاري بث الفيديو...**\n\n👥 المستهدفين: {len(users)}", parse_mode='Markdown')
            
            for user_id in users:
                try:
                    if memory.is_banned(user_id):
                        continue
                        
                    bot.send_video(user_id, file_id, caption=caption, parse_mode='Markdown')
                    success_count += 1
                    time.sleep(0.1)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ خطأ في بث الفيديو للمستخدم {user_id}: {e}")
            
            bot.edit_message_text(
                f"✅ **تم بث الفيديو بنجاح!**\n\n✅ الناجح: {success_count}\n❌ الفاشل: {fail_count}",
                message.chat.id,
                progress_msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال فيديو!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في بث الفيديو: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في البث!**", parse_mode='Markdown')

def process_broadcast_audio(message):
    try:
        if message.content_type == 'audio':
            file_id = message.audio.file_id
            caption = message.caption or ""
            users = list(memory.user_stats.keys())
            success_count = 0
            fail_count = 0
            
            progress_msg = bot.send_message(message.chat.id, f"📤 **جاري بث الصوت...**\n\n👥 المستهدفين: {len(users)}", parse_mode='Markdown')
            
            for user_id in users:
                try:
                    if memory.is_banned(user_id):
                        continue
                        
                    bot.send_audio(user_id, file_id, caption=caption, parse_mode='Markdown')
                    success_count += 1
                    time.sleep(0.1)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ خطأ في بث الصوت للمستخدم {user_id}: {e}")
            
            bot.edit_message_text(
                f"✅ **تم بث الصوت بنجاح!**\n\n✅ الناجح: {success_count}\n❌ الفاشل: {fail_count}",
                message.chat.id,
                progress_msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال ملف صوتي!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في بث الصوت: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في البث!**", parse_mode='Markdown')

def process_broadcast_document(message):
    try:
        if message.content_type == 'document':
            file_id = message.document.file_id
            caption = message.caption or ""
            users = list(memory.user_stats.keys())
            success_count = 0
            fail_count = 0
            
            progress_msg = bot.send_message(message.chat.id, f"📤 **جاري بث الملف...**\n\n👥 المستهدفين: {len(users)}", parse_mode='Markdown')
            
            for user_id in users:
                try:
                    if memory.is_banned(user_id):
                        continue
                        
                    bot.send_document(user_id, file_id, caption=caption, parse_mode='Markdown')
                    success_count += 1
                    time.sleep(0.1)
                    
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ خطأ في بث الملف للمستخدم {user_id}: {e}")
            
            bot.edit_message_text(
                f"✅ **تم بث الملف بنجاح!**\n\n✅ الناجح: {success_count}\n❌ الفاشل: {fail_count}",
                message.chat.id,
                progress_msg.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ **الرجاء إرسال ملف!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في بث الملف: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في البث!**", parse_mode='Markdown')

# دوال إدارة المستخدمين
def process_add_admin(message):
    try:
        user_id = int(message.text.strip())
        username = message.from_user.username or "بدون معرف"
        first_name = message.from_user.first_name or "بدون اسم"
        
        if memory.add_admin(user_id, username, first_name):
            bot.send_message(message.chat.id, f"✅ **تمت إضافة المشرف:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **المستخدم مشرف بالفعل:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة المشرف: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الإضافة!**", parse_mode='Markdown')

def process_remove_admin(message):
    try:
        user_id = int(message.text.strip())
        
        if memory.remove_admin(user_id):
            bot.send_message(message.chat.id, f"✅ **تمت إزالة المشرف:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **المستخدم ليس مشرفاً:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إزالة المشرف: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الإزالة!**", parse_mode='Markdown')

def process_add_vip(message):
    try:
        user_id = int(message.text.strip())
        username = message.from_user.username or "بدون معرف"
        first_name = message.from_user.first_name or "بدون اسم"
        
        if memory.add_vip(user_id, username, first_name):
            bot.send_message(message.chat.id, f"✅ **تمت إضافة VIP:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **المستخدم VIP بالفعل:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة VIP: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الإضافة!**", parse_mode='Markdown')

def process_remove_vip(message):
    try:
        user_id = int(message.text.strip())
        
        if memory.remove_vip(user_id):
            bot.send_message(message.chat.id, f"✅ **تمت إزالة VIP:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **المستخدم ليس VIP:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إزالة VIP: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الإزالة!**", parse_mode='Markdown')

def process_ban_user(message):
    try:
        user_id = int(message.text.strip())
        username = message.from_user.username or "بدون معرف"
        first_name = message.from_user.first_name or "بدون اسم"
        
        if memory.ban_user(user_id, username, first_name):
            bot.send_message(message.chat.id, f"✅ **تم حظر المستخدم:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **المستخدم محظور بالفعل:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في حظر المستخدم: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الحظر!**", parse_mode='Markdown')

def process_unban_user(message):
    try:
        user_id = int(message.text.strip())
        
        if memory.unban_user(user_id):
            bot.send_message(message.chat.id, f"✅ **تم فك حظر المستخدم:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"⚠️ **المستخدم غير محظور:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في فك حظر المستخدم: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في فك الحظر!**", parse_mode='Markdown')

def process_add_points(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ **الصيغة غير صحيحة!**\n\nاستخدم: user_id points", parse_mode='Markdown')
            return
            
        user_id = int(parts[0])
        points = int(parts[1])
        
        if memory.add_points(user_id, points):
            bot.send_message(message.chat.id, f"✅ **تم إضافة {points} نقطة للمستخدم:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"❌ **المستخدم غير موجود:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال أرقام صحيحة!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة النقاط: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الإضافة!**", parse_mode='Markdown')

def process_remove_points(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ **الصيغة غير صحيحة!**\n\nاستخدم: user_id points", parse_mode='Markdown')
            return
            
        user_id = int(parts[0])
        points = int(parts[1])
        
        if memory.remove_points(user_id, points):
            bot.send_message(message.chat.id, f"✅ **تم نزع {points} نقطة من المستخدم:** {user_id}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"❌ **المستخدم غير موجود:** {user_id}", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال أرقام صحيحة!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في نزع النقاط: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في النزع!**", parse_mode='Markdown')

def process_send_to_user(message):
    try:
        parts = message.text.strip().split(' ', 1)
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ **الصيغة غير صحيحة!**\n\nاستخدم: user_id message", parse_mode='Markdown')
            return
            
        user_id = int(parts[0])
        user_message = parts[1]
        
        try:
            bot.send_message(user_id, f"📨 **رسالة من الإدارة:**\n\n{user_message}", parse_mode='Markdown')
            bot.send_message(message.chat.id, f"✅ **تم إرسال الرسالة للمستخدم:** {user_id}", parse_mode='Markdown')
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ **فشل إرسال الرسالة للمستخدم:** {user_id}", parse_mode='Markdown')
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ **الرجاء إدخال معرف مستخدم صحيح!**", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")
        bot.send_message(message.chat.id, "❌ **خطأ في الإرسال!**", parse_mode='Markdown')

def start_bot():
    """بدء تشغيل البوت مع التعامل مع الأخطاء"""
    logger.info("🚀 بدء تشغيل موبي...")
    
    try:
        # اختبار الاتصال
        bot_info = bot.get_me()
        logger.info(f"✅ موبي جاهز: @{bot_info.username}")
        logger.info(f"👑 المطور: {DEVELOPER_USERNAME}")
        
        # بدء التنظيف التلقائي
        memory.start_cleanup_thread()
        
        # تشغيل البوت
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل موبي: {e}")
        time.sleep(10)
        start_bot()  # إعادة التشغيل التلقائي

if __name__ == "__main__":
    start_bot()
