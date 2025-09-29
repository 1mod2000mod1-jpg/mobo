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
    image_btn = InlineKeyboardButton("🖼️ الصورة الترحيبية", callback_data="settings_image")
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    
    keyboard.add(channel_btn, subscription_btn)
    keyboard.add(messages_btn, image_btn)
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

📞 **رابط التواصل:** https://t.me/{DEVELOPER_USERNAME[1:]}
        """
    
    bot.send_message(message.chat.id, vip_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/upgrade")

@bot.message_handler(commands=['status'])
@require_subscription
def handle_status(message):
    user_id = message.from_user.id
    can_send, status = memory.can_send_message(user_id)
    user_stats = memory.user_stats.get(user_id, {})
    points = user_stats.get('points', 0)
    
    if memory.is_vip(user_id):
        status_text = f"""
📊 **حالة حسابك - VIP 🌟**

💎 **النوع:** VIP مميز
📨 **الرسائل:** غير محدود
🎯 **النقاط:** {points}
⚡ **الحالة:** نشط

🎁 **أنت تتمتع بجميع المميزات!**
        """
    elif memory.is_admin(message.from_user.id):
        status_text = f"""
📊 **حالة حسابك - مشرف 🛡️**

👑 **النوع:** مشرف
📨 **الرسائل:** غير محدود
🎯 **النقاط:** {points}
⚡ **الحالة:** نشط

🔧 **صلاحيات إدارية كاملة**
        """
    else:
        used = user_stats.get('used_messages', 0)
        limit = user_stats.get('message_limit', memory.settings.get('free_messages', 50))
        remaining = limit - used
        
        status_text = f"""
📊 **حالة حسابك - مجاني 🔓**

📨 **الرسائل:** {used}/{limit}
🎯 **المتبقي:** {remaining}
🎯 **النقاط:** {points}
⚡ **الحالة:** {status}

💎 **للترقية:** /upgrade
        """
    
    bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/status")

@bot.message_handler(commands=['memory'])
@require_subscription
def handle_memory(message):
    conversation = memory.get_user_conversation(message.from_user.id)
    memory_info = f"""
💾 **ذاكرة موبي**

📊 **معلومات محادثتك:**
• عدد الرسائل: {len(conversation)}
• المساحة: {len(str(conversation))} حرف

🛠️ **الخيارات:**
/new - بدء محادثة جديدة

💡 **موبي يحفظ آخر 15 رسالة**
    """
    bot.send_message(message.chat.id, memory_info, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/memory")

@bot.message_handler(commands=['new'])
@require_subscription
def handle_new(message):
    memory.clear_conversation(message.from_user.id)
    bot.send_message(message.chat.id, "🔄 بدأت محادثة جديدة! ابدأ من الصفر.")
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/new")

@bot.message_handler(commands=['developer'])
def handle_developer(message):
    developer_text = f"""
👑 **مطور موبي**

📛 **الاسم:** {DEVELOPER_USERNAME}
🆔 **الرقم:** {DEVELOPER_ID}

📞 **للتواصل:** [اضغط هنا](https://t.me/{DEVELOPER_USERNAME[1:]})

🔧 **البوت مبرمج خصيصاً باستخدام:**
• أقوى الأنظمة وأفضلها
• خدمات سريعة ودقيقة
• أنظمة ذكاء اصطناعي متطورة

💬 **للإبلاغ عن مشاكل أو اقتراحات، تواصل مباشرة**
    """
    bot.send_message(message.chat.id, developer_text, reply_markup=create_developer_button(), parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/developer")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    if not memory.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ ليس لديك صلاحية الوصول!")
        return
    
    admin_text = f"""
👑 **لوحة تحكم موبي**

📊 **اختر الإدارة:**
• 📊 الإحصائيات
• 👥 المستخدمين
• 🛡️ المشرفين
• 💬 المحادثات
• 🌟 إدارة VIP
• 📢 البث للمستخدمين
• 🚫 إدارة الحظر
• 🎯 النقاط
• ⚙️ الإعدادات

✅ **النظام تحت إشرافك**
    """
    bot.send_message(message.chat.id, admin_text, reply_markup=create_admin_panel(), parse_mode='Markdown')

# حالات المستخدم
broadcast_state = {}
admin_state = {}
ban_state = {}
vip_state = {}
settings_state = {}
points_state = {}
send_user_state = {}

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'audio', 'document'])
@require_subscription  
def handle_all_messages(message):
    try:
        user_id = message.from_user.id
        
        # معالجة البث
        if user_id in broadcast_state:
            broadcast_type = broadcast_state[user_id]['type']
            success_count = 0
            total_users = len(memory.user_stats)
            
            for chat_id in memory.user_stats.keys():
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
                except:
                    continue
            
            bot.send_message(user_id, f"✅ تم إرسال البث إلى {success_count}/{total_users} مستخدم")
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
        
        # معالجة حالات أخرى
        if user_id in admin_state:
            if admin_state[user_id] == 'waiting_admin_id':
                try:
                    target_user_id = int(message.text)
                    target_user = bot.get_chat(target_user_id)
                    if memory.add_admin(target_user_id, target_user.username, target_user.first_name):
                        bot.send_message(user_id, f"✅ تمت إضافة {target_user.first_name} كمشرف")
                    else:
                        bot.send_message(user_id, "❌ المستخدم مشرف بالفعل!")
                    admin_state.pop(user_id, None)
                except:
                    bot.send_message(user_id, "❌ خطأ في إضافة المشرف!")
                return
        
        if user_id in ban_state:
            if ban_state[user_id] == 'waiting_ban_id':
                try:
                    target_user_id = int(message.text)
                    target_user = bot.get_chat(target_user_id)
                    if memory.ban_user(target_user_id, target_user.username, target_user.first_name):
                        bot.send_message(user_id, f"✅ تم حظر {target_user.first_name}")
                    else:
                        bot.send_message(user_id, "❌ لا يمكن حظر هذا المستخدم!")
                    ban_state.pop(user_id, None)
                except:
                    bot.send_message(user_id, "❌ خطأ في الحظر!")
                return
        
        if user_id in vip_state:
            if vip_state[user_id] == 'waiting_vip_id':
                try:
                    target_user_id = int(message.text)
                    target_user = bot.get_chat(target_user_id)
                    if memory.add_vip(target_user_id, target_user.username, target_user.first_name):
                        bot.send_message(user_id, f"✅ تمت إضافة {target_user.first_name} إلى VIP")
                    else:
                        bot.send_message(user_id, "❌ المستخدم VIP بالفعل!")
                    vip_state.pop(user_id, None)
                except:
                    bot.send_message(user_id, "❌ خطأ في إضافة VIP!")
                return
        
        if user_id in points_state:
            if points_state[user_id]['action'] == 'add':
                try:
                    target_user_id = points_state[user_id]['user_id']
                    points = int(message.text)
                    if memory.add_points(target_user_id, points):
                        bot.send_message(user_id, f"✅ تمت إضافة {points} نقطة للمستخدم")
                    else:
                        bot.send_message(user_id, "❌ خطأ في إضافة النقاط!")
                    points_state.pop(user_id, None)
                except:
                    bot.send_message(user_id, "❌ أدخل رقم صحيح!")
                return
            elif points_state[user_id]['action'] == 'remove':
                try:
                    target_user_id = points_state[user_id]['user_id']
                    points = int(message.text)
                    if memory.remove_points(target_user_id, points):
                        bot.send_message(user_id, f"✅ تم نزع {points} نقطة من المستخدم")
                    else:
                        bot.send_message(user_id, "❌ خطأ في نزع النقاط!")
                    points_state.pop(user_id, None)
                except:
                    bot.send_message(user_id, "❌ أدخل رقم صحيح!")
                return
        
        if user_id in settings_state:
            if settings_state[user_id] == 'waiting_channel':
                memory.update_settings({'required_channel': message.text})
                bot.send_message(user_id, f"✅ تم تعيين القناة: {message.text}")
                settings_state.pop(user_id, None)
                return
            elif settings_state[user_id] == 'waiting_messages':
                try:
                    messages_count = int(message.text)
                    memory.update_settings({'free_messages': messages_count})
                    bot.send_message(user_id, f"✅ تم تعيين عدد الرسائل المجانية: {messages_count}")
                    settings_state.pop(user_id, None)
                except:
                    bot.send_message(user_id, "❌ أدخل رقم صحيح!")
                return
            elif settings_state[user_id] == 'waiting_image':
                if message.photo:
                    memory.update_settings({'welcome_image': message.photo[-1].file_id})
                    bot.send_message(user_id, "✅ تم تعيين الصورة الترحيبية")
                else:
                    bot.send_message(user_id, "❌ أرسل صورة!")
                settings_state.pop(user_id, None)
                return
        
        # معالجة الرسائل العادية
        if message.content_type == 'text':
            message_text = message.text
        else:
            if message.caption:
                message_text = f"[{message.content_type.upper()}] {message.caption}"
            else:
                message_text = f"[{message.content_type.upper()}] تم إرسال وسائط"
        
        memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, message_text)
        
        if memory.is_banned(user_id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام البوت.")
            return
        
        can_send, status = memory.can_send_message(user_id)
        if not can_send:
            bot.send_message(message.chat.id, f"❌ انتهت رسائلك المجانية! ({status})\n\n💎 ترقى إلى VIP للاستخدام غير المحدود!\n/upgrade للترقية")
            return
        
        if message.content_type == 'text':
            bot.send_chat_action(message.chat.id, 'typing')
            
            response = AIService.generate_response(user_id, message.text)
            
            if response:
                bot.send_message(message.chat.id, response)
        else:
            bot.reply_to(message, "📁 **تم استلام الوسائط بنجاح!**\n\n💫 موبي يدعم الوسائط، لكن الذكاء الاصطناعي يحتاج إلى نص للرد. اكتب سؤالك!", parse_mode='Markdown')
        
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
    
    # أزرار الإدارة
    elif call.data == "add_admin":
        admin_state[user_id] = 'waiting_admin_id'
        bot.send_message(user_id, "👤 أرسل رقم المستخدم الذي تريد ترقيته إلى مشرف:")
        bot.answer_callback_query(call.id, "➕ إضافة مشرف")
    
    elif call.data == "remove_admin":
        admin_state[user_id] = 'waiting_remove_admin_id'
        bot.send_message(user_id, "👤 أرسل رقم المشرف الذي تريد إزالته:")
        bot.answer_callback_query(call.id, "➖ إزالة مشرف")
    
    elif call.data == "add_ban":
        ban_state[user_id] = 'waiting_ban_id'
        bot.send_message(user_id, "🚫 أرسل رقم المستخدم الذي تريد حظره:")
        bot.answer_callback_query(call.id, "🚫 حظر مستخدم")
    
    elif call.data == "remove_ban":
        ban_state[user_id] = 'waiting_unban_id'
        bot.send_message(user_id, "✅ أرسل رقم المستخدم الذي تريد إلغاء حظره:")
        bot.answer_callback_query(call.id, "✅ إلغاء حظر")
    
    elif call.data == "add_vip":
        vip_state[user_id] = 'waiting_vip_id'
        bot.send_message(user_id, "🌟 أرسل رقم المستخدم الذي تريد إضافته إلى VIP:")
        bot.answer_callback_query(call.id, "🌟 إضافة VIP")
    
    elif call.data == "remove_vip":
        vip_state[user_id] = 'waiting_remove_vip_id'
        bot.send_message(user_id, "🌟 أرسل رقم المستخدم الذي تريد إزالته من VIP:")
        bot.answer_callback_query(call.id, "➖ إزالة VIP")
    
    # أزرار النقاط
    elif call.data == "add_points":
        points_state[user_id] = {'action': 'add', 'step': 'waiting_user'}
        bot.send_message(user_id, "🎯 أرسل رقم المستخدم الذي تريد إضافة نقاط له:")
        bot.answer_callback_query(call.id, "➕ إضافة نقاط")
    
    elif call.data == "remove_points":
        points_state[user_id] = {'action': 'remove', 'step': 'waiting_user'}
        bot.send_message(user_id, "🎯 أرسل رقم المستخدم الذي تريد نزع نقاط منه:")
        bot.answer_callback_query(call.id, "➖ نزع نقاط")
    
    elif call.data == "send_to_user":
        send_user_state[user_id] = {'step': 'waiting_user'}
        bot.send_message(user_id, "📤 أرسل رقم المستخدم الذي تريد إرسال رسالة له:")
        bot.answer_callback_query(call.id, "📤 إرسال لمستخدم")
    
    # إعدادات
    elif call.data == "settings_channel":
        settings_state[user_id] = 'waiting_channel'
        bot.send_message(user_id, "📢 أرسل رابط القناة (مثال: @channel_name):")
        bot.answer_callback_query(call.id, "📢 إعداد القناة")
    
    elif call.data == "settings_subscription":
        current_state = memory.settings.get('subscription_enabled', False)
        memory.update_settings({'subscription_enabled': not current_state})
        status = "مفعل" if not current_state else "معطل"
        bot.answer_callback_query(call.id, f"🔐 الاشتراك الإجباري {status}")
        show_settings_menu(call)
    
    elif call.data == "settings_messages":
        settings_state[user_id] = 'waiting_messages'
        bot.send_message(user_id, "💬 أرسل عدد الرسائل المجانية:")
        bot.answer_callback_query(call.id, "💬 عدد الرسائل")
    
    elif call.data == "settings_image":
        settings_state[user_id] = 'waiting_image'
        bot.send_message(user_id, "🖼️ أرسل الصورة الترحيبية:")
        bot.answer_callback_query(call.id, "🖼️ الصورة الترحيبية")
    
    # معالجة المستخدمين
    elif call.data.startswith("view_conversation_"):
        view_user_conversation(call)
    elif call.data.startswith("view_recent_"):
        view_recent_messages(call)
    elif call.data.startswith("make_admin_"):
        make_user_admin(call)
    elif call.data.startswith("remove_admin_"):
        remove_user_admin(call)
    elif call.data.startswith("ban_user_"):
        ban_user_action(call)
    elif call.data.startswith("unban_user_"):
        unban_user_action(call)
    elif call.data.startswith("add_points_"):
        add_points_action(call)
    elif call.data.startswith("remove_points_"):
        remove_points_action(call)

# دوال العرض
def show_admin_panel(call):
    admin_text = f"""
👑 **لوحة تحكم موبي**

📊 **اختر الإدارة:**
• 📊 الإحصائيات
• 👥 المستخدمين
• 🛡️ المشرفين
• 💬 المحادثات
• 🌟 إدارة VIP
• 📢 البث للمستخدمين
• 🚫 إدارة الحظر
• 🎯 النقاط
• ⚙️ الإعدادات

✅ **النظام تحت إشرافك**
    """
    bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id,
                        reply_markup=create_admin_panel(), parse_mode='Markdown')

def show_admin_stats(call):
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        vip_count = len(memory.get_vip_list())
        banned_count = len(memory.banned_users)
        total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
        total_points = sum(stats.get('points', 0) for stats in memory.user_stats.values())
        
        stats_text = f"""
📊 **إحصائيات موبي**

👥 **المستخدمين:**
• الإجمالي: {total_users}
• النشطين: {active_today} 
• VIP: {vip_count}
• المحظورين: {banned_count}
• الرسائل: {total_messages}
• النقاط: {total_points}

🕒 **التحديث:** {datetime.now().strftime('%H:%M:%S')}
        """
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, 
                            reply_markup=create_admin_panel(), parse_mode='Markdown')
        bot.answer_callback_query(call.id, "✅ تم تحديث الإحصائيات")
    except Exception as e:
        logger.error(f"❌ خطأ في الإحصائيات: {e}")

def show_users_list(call):
    try:
        users = memory.get_user_stats()
        users_text = "👥 **آخر 10 مستخدمين:**\n\n"
        
        sorted_users = sorted(users.items(), key=lambda x: x[1]['last_seen'], reverse=True)
        
        for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
            status = "🌟" if stats.get('is_vip') else "🛡️" if stats.get('is_admin') else "✅"
            username = stats.get('username', 'بدون معرف')
            points = stats.get('points', 0)
            users_text += f"{i}. {status} {stats['first_name']} (@{username})\n"
            users_text += f"   📝 {stats['message_count']} رسالة | 🎯 {points} نقطة\n\n"
        
        users_text += f"📊 الإجمالي: {len(users)} مستخدم"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        view_btn = InlineKeyboardButton("💬 عرض المحادثات", callback_data="admin_conversations")
        recent_btn = InlineKeyboardButton("🕒 الرسائل الأخيرة", callback_data="view_recent_all")
        points_btn = InlineKeyboardButton("🎯 إدارة النقاط", callback_data="admin_points")
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(view_btn, recent_btn)
        keyboard.add(points_btn)
        keyboard.add(back_btn)
        
        bot.edit_message_text(users_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "✅ تم تحميل المستخدمين")
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المستخدمين: {e}")

def show_admins_management(call):
    try:
        admins = memory.get_admins_list()
        admins_text = "🛡️ **قائمة المشرفين:**\n\n"
        
        for i, admin in enumerate(admins, 1):
            admins_text += f"{i}. {admin['first_name']} (@{admin['username']})\n"
            admins_text += f"   📝 {admin['message_count']} رسالة | 🎯 {admin['points']} نقطة\n\n"
        
        keyboard = InlineKeyboardMarkup()
        add_admin_btn = InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")
        remove_admin_btn = InlineKeyboardButton("➖ إزالة مشرف", callback_data="remove_admin")
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(add_admin_btn, remove_admin_btn)
        keyboard.add(back_btn)
        
        bot.edit_message_text(admins_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "🛡️ إدارة المشرفين")
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة المشرفين: {e}")

def show_conversations_list(call):
    try:
        users = memory.get_user_stats()
        users_with_conv = [(uid, info) for uid, info in users.items() if memory.get_user_conversation(uid)]
        
        if not users_with_conv:
            conv_text = "💬 **لا توجد محادثات نشطة**"
            keyboard = InlineKeyboardMarkup()
        else:
            conv_text = "💬 **المستخدمين النشطين:**\n\n"
            keyboard = InlineKeyboardMarkup(row_width=2)
            
            for i, (user_id, user_info) in enumerate(users_with_conv[:10], 1):
                conv = memory.get_user_conversation(user_id)
                conv_text += f"{i}. {user_info['first_name']} - {len(conv)} رسالة\n"
                
                if i <= 6:
                    keyboard.add(InlineKeyboardButton(
                        f"{user_info['first_name']} ({len(conv)})", 
                        callback_data=f"view_conversation_{user_id}"
                    ))
        
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")
        keyboard.add(back_btn)
        
        bot.edit_message_text(conv_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "💬 المحادثات")
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثات: {e}")

def show_vip_management(call):
    try:
        vip_users = memory.get_vip_list()
        vip_text = "🌟 **قائمة VIP:**\n\n"
        
        if not vip_users:
            vip_text += "❌ لا يوجد مستخدمين VIP"
        else:
            for i, user in enumerate(vip_users, 1):
                vip_text += f"{i}. {user['first_name']} (@{user['username']})\n"
                vip_text += f"   📝 {user['message_count']} رسالة | 🎯 {user['points']} نقطة\n\n"
        
        keyboard = InlineKeyboardMarkup()
        add_vip_btn = InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")
        remove_vip_btn = InlineKeyboardButton("➖ إزالة VIP", callback_data="remove_vip")
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(add_vip_btn, remove_vip_btn)
        keyboard.add(back_btn)
        
        bot.edit_message_text(vip_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "🌟 إدارة VIP")
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة VIP: {e}")

def show_broadcast_menu(call):
    broadcast_text = "📢 **اختر نوع البث:**\n\nيمكنك إرسال:\n• 📝 نصوص\n• 🖼️ صور\n• 🎥 فيديوهات\n• 🎵 صوتيات\n• 📄 ملفات"
    bot.edit_message_text(broadcast_text, call.message.chat.id, call.message.message_id,
                        reply_markup=create_broadcast_menu(), parse_mode='Markdown')
    bot.answer_callback_query(call.id, "📢 البث")

def show_ban_management(call):
    try:
        banned_users = []
        for user_id in memory.banned_users:
            if user_id in memory.user_stats:
                banned_users.append(memory.user_stats[user_id])
        
        ban_text = "🚫 **المستخدمين المحظورين:**\n\n"
        
        if not banned_users:
            ban_text += "❌ لا يوجد مستخدمين محظورين"
        else:
            for i, user in enumerate(banned_users, 1):
                ban_text += f"{i}. {user['first_name']} (@{user['username']})\n\n"
        
        keyboard = InlineKeyboardMarkup()
        add_ban_btn = InlineKeyboardButton("➕ حظر مستخدم", callback_data="add_ban")
        remove_ban_btn = InlineKeyboardButton("✅ إلغاء حظر", callback_data="remove_ban")
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(add_ban_btn, remove_ban_btn)
        keyboard.add(back_btn)
        
        bot.edit_message_text(ban_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "🚫 إدارة الحظر")
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة الحظر: {e}")

def show_points_menu(call):
    points_text = "🎯 **إدارة النقاط:**\n\nيمكنك:\n• ➕ إضافة نقاط للمستخدمين\n• ➖ نزع نقاط من المستخدمين\n• 📤 إرسال رسائل لمستخدم معين"
    bot.edit_message_text(points_text, call.message.chat.id, call.message.message_id,
                        reply_markup=create_points_menu(), parse_mode='Markdown')
    bot.answer_callback_query(call.id, "🎯 النقاط")

def show_settings_menu(call):
    settings_text = f"""
⚙️ **إعدادات موبي**

📢 **القناة:** {memory.settings.get('required_channel', 'غير معينة')}
🔐 **الاشتراك الإجباري:** {'✅ مفعل' if memory.settings.get('subscription_enabled', False) else '❌ معطل'}
💬 **الرسائل المجانية:** {memory.settings.get('free_messages', 50)}
🖼️ **الصورة الترحيبية:** {'✅ معينة' if memory.settings.get('welcome_image') else '❌ غير معينة'}

🛠️ **اختر الإعداد الذي تريد تعديله:**
    """
    bot.edit_message_text(settings_text, call.message.chat.id, call.message.message_id,
                        reply_markup=create_settings_menu(), parse_mode='Markdown')
    bot.answer_callback_query(call.id, "⚙️ الإعدادات")

def view_user_conversation(call):
    try:
        user_id = int(call.data.split("_")[2])
        conversation = memory.get_user_conversation(user_id)
        user_info = memory.user_stats.get(user_id, {})
        
        if not conversation:
            bot.answer_callback_query(call.id, "❌ لا توجد محادثات لهذا المستخدم!", show_alert=True)
            return
        
        conv_text = f"💬 **محادثة {user_info.get('first_name', 'مستخدم')}:**\n\n"
        
        for msg in conversation[-8:]:
            role = "👤" if msg['role'] == 'user' else "🤖 موبي"
            time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            content = msg['content']
            if len(content) > 60:
                content = content[:60] + "..."
            conv_text += f"{role} [{time}]: {content}\n\n"
        
        conv_text += f"📊 إجمالي الرسائل: {len(conversation)}"
        
        bot.edit_message_text(conv_text, call.message.chat.id, call.message.message_id,
                            reply_markup=create_admin_panel(), parse_mode='Markdown')
        bot.answer_callback_query(call.id, "✅ تم تحميل المحادثة")
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثة: {e}")

def view_recent_messages(call):
    try:
        if call.data == "view_recent_all":
            users_text = "🕒 **اختر مستخدم لعرض رسائله الأخيرة:**\n\n"
            users = memory.get_user_stats()
            keyboard = InlineKeyboardMarkup(row_width=2)
            
            for user_id, user_info in list(users.items())[:6]:
                recent = memory.get_recent_messages(user_id, 10)
                if recent:
                    keyboard.add(InlineKeyboardButton(
                        f"{user_info['first_name']} ({len(recent)})",
                        callback_data=f"view_recent_{user_id}"
                    ))
        else:
            user_id = int(call.data.split("_")[2])
            user_info = memory.user_stats.get(user_id, {})
            recent_messages = memory.get_recent_messages(user_id, 10)
            
            users_text = f"🕒 **آخر رسائل {user_info.get('first_name', 'مستخدم')} (10 دقائق):**\n\n"
            
            if not recent_messages:
                users_text += "❌ لا توجد رسائل في آخر 10 دقائق"
            else:
                for msg in recent_messages[-5:]:
                    role = "👤" if msg['role'] == 'user' else "🤖"
                    time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
                    content = msg['content']
                    if len(content) > 50:
                        content = content[:50] + "..."
                    users_text += f"{role} [{time}]: {content}\n\n"
            
            keyboard = InlineKeyboardMarkup()
        
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")
        keyboard.add(back_btn)
        
        bot.edit_message_text(users_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
        bot.answer_callback_query(call.id, "🕒 الرسائل الأخيرة")
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الرسائل الأخيرة: {e}")

def make_user_admin(call):
    try:
        user_id = int(call.data.split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.add_admin(user_id, user_info.get('username', ''), user_info.get('first_name', '')):
            bot.answer_callback_query(call.id, f"✅ تم ترقية {user_info.get('first_name', 'المستخدم')} إلى مشرف!")
            show_admins_management(call)
        else:
            bot.answer_callback_query(call.id, "❌ المستخدم مشرف بالفعل!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في ترقية المشرف: {e}")

def remove_user_admin(call):
    try:
        user_id = int(call.data.split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.remove_admin(user_id):
            bot.answer_callback_query(call.id, f"✅ تم إزالة {user_info.get('first_name', 'المستخدم')} من المشرفين!")
            show_admins_management(call)
        else:
            bot.answer_callback_query(call.id, "❌ لا يمكن إزالة هذا المشرف!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في إزالة المشرف: {e}")

def ban_user_action(call):
    try:
        user_id = int(call.data.split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.ban_user(user_id, user_info.get('username', ''), user_info.get('first_name', '')):
            bot.answer_callback_query(call.id, f"✅ تم حظر {user_info.get('first_name', 'المستخدم')}!")
            show_ban_management(call)
        else:
            bot.answer_callback_query(call.id, "❌ لا يمكن حظر هذا المستخدم!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في حظر المستخدم: {e}")

def unban_user_action(call):
    try:
        user_id = int(call.data.split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.unban_user(user_id):
            bot.answer_callback_query(call.id, f"✅ تم إلغاء حظر {user_info.get('first_name', 'المستخدم')}!")
            show_ban_management(call)
        else:
            bot.answer_callback_query(call.id, "❌ المستخدم غير محظور!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في إلغاء الحظر: {e}")

def add_points_action(call):
    try:
        user_id = int(call.data.split("_")[2])
        points_state[call.from_user.id] = {'action': 'add', 'user_id': user_id}
        bot.send_message(call.from_user.id, "🎯 أرسل عدد النقاط التي تريد إضافتها:")
        bot.answer_callback_query(call.id, "➕ إضافة نقاط")
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة النقاط: {e}")

def remove_points_action(call):
    try:
        user_id = int(call.data.split("_")[2])
        points_state[call.from_user.id] = {'action': 'remove', 'user_id': user_id}
        bot.send_message(call.from_user.id, "🎯 أرسل عدد النقاط التي تريد نزعها:")
        bot.answer_callback_query(call.id, "➖ نزع نقاط")
    except Exception as e:
        logger.error(f"❌ خطأ في نزع النقاط: {e}")

# تشغيل البوت مع الحفاظ على الحياة
def keep_alive():
    while True:
        try:
            # إرسال طلب للحفاظ على النشاط
            logger.info("🫀 البوت حي ويعمل...")
            threading.Event().wait(300)  # انتظر 5 دقائق
        except Exception as e:
            logger.error(f"❌ خطأ في الحفاظ على الحياة: {e}")

def main():
    logger.info("🚀 بدء تشغيل موبي مع جميع الميزات...")
    
    try:
        bot.remove_webhook()
        
        # اختبار النظام
        try:
            test_url = f"{AIService.API_URL}?text=test"
            response = requests.get(test_url, timeout=10)
            logger.info(f"✅ النظام يعمل: {response.status_code}")
        except Exception as api_error:
            logger.warning(f"⚠️ النظام غير متاح: {api_error}")
        
        logger.info(f"✅ موبي جاهز - المطور: {DEVELOPER_USERNAME}")
        logger.info("🤖 البوت يعمل الآن ويستمع للرسائل...")
        
        # بدء خيط الحفاظ على الحياة
        threading.Thread(target=keep_alive, daemon=True).start()
        
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")
        import time
        time.sleep(10)
        main()
# إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # البدء
    logger.info("🚀 بدء تشغيل البوت...")
    application.run_polling()
    logger.info("✅ البوت يعمل!")

if __name__ == "__main__":
    main()
