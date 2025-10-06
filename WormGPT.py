#!/usr/bin/env python3
"""
🤖 موبي - البوت الذكي المتقدم
🛠️ الإصدار: 4.0 | ⚡ الأكثر تطوراً وسرعة
👑 المطور: @xtt19x
"""

import os
import json
import logging
import requests
import threading
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🎨 إعدادات التصميم المتقدم
class Colors:
    RED = '🔴'
    GREEN = '🟢'
    BLUE = '🔵'
    YELLOW = '🟡'
    PURPLE = '🟣'
    ORANGE = '🟠'
    WHITE = '⚪'
    BLACK = '⚫'

class Emojis:
    ROBOT = '🤖'
    CROWN = '👑'
    FIRE = '🔥'
    STAR = '⭐'
    GEM = '💎'
    SHIELD = '🛡️'
    WARNING = '⚠️'
    SUCCESS = '✅'
    ERROR = '❌'
    SETTINGS = '⚙️'
    USERS = '👥'
    CHART = '📊'
    MESSAGE = '💬'
    VIP = '🌟'
    ADMIN = '🛡️'
    BAN = '🚫'
    BROADCAST = '📢'
    POINTS = '🎯'
    MEMORY = '💾'
    NEW = '🔄'
    DEVELOPER = '💻'
    HELP = '🆘'
    STATUS = '📈'
    UPGRADE = '🚀'
    PHOTO = '🖼️'
    VIDEO = '🎥'
    AUDIO = '🎵'
    DOCUMENT = '📄'
    CHANNEL = '📢'
    SUBSCRIPTION = '🔐'
    MONEY = '💰'
    GIFT = '🎁'
    LIGHTNING = '⚡'
    BRAIN = '🧠'
    CLOUD = '☁️'
    HEART = '❤️'
    MAGIC = '🎩'
    ROCKET = '🚀'
    ZAP = '⚡'
    GLOBE = '🌐'
    PARTY = '🎉'
    MEDAL = '🏅'
    TROPHY = '🏆'
    DIAMOND = '💎'
    CLOVER = '🍀'
    HOURGLASS = '⏳'
    CHECK = '✅'

# 🎯 إعداد التسجيل المتقدم
logging.basicConfig(
    level=logging.INFO,
    format=f'{Emojis.ROBOT} %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("موبي_المتقدم")

# 🔑 التوكن
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    logger.error(f"{Emojis.ERROR} TELEGRAM_BOT_TOKEN غير معروف")
    exit(1)

# 🤖 إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# 👑 معلومات المطور
DEVELOPER_USERNAME = "@xtt19x"
DEVELOPER_ID = 6521966233
DEVELOPER_CHANNEL = "@xtt19x"

# ⚙️ إعدادات البوت المتقدمة
BOT_SETTINGS = {
    "required_channel": DEVELOPER_CHANNEL,
    "free_messages": 25,
    "welcome_image": "",
    "welcome_video": "",
    "welcome_audio": "",
    "welcome_document": "",
    "welcome_text": "",
    "subscription_enabled": True,
    "auto_backup": True,
    "maintenance_mode": False,
    "points_system": True,
    "vip_price": "15$",
    "premium_price": "25$"
}

# 💾 نظام الذاكرة المتقدم
class MemorySystem:
    def __init__(self):
        self.workspace = Path("./mobi_memory")
        self.workspace.mkdir(exist_ok=True)
        self.conversations = {}
        self.user_stats = self.load_user_stats()
        self.admins = self.load_admins()
        self.banned_users = self.load_banned_users()
        self.vip_users = self.load_vip_users()
        self.settings = self.load_settings()
        
        # 🚀 بدء الأنظمة المساعدة
        self.start_cleanup_thread()
        self.start_auto_backup()
        logger.info(f"{Emojis.SUCCESS} نظام الذاكرة المتقدم جاهز!")
    
    def start_cleanup_thread(self):
        """نظام تنظيف ذكي للمحادثات"""
        def cleanup_old_conversations():
            while True:
                try:
                    self.cleanup_old_messages()
                    time.sleep(300)  # كل 5 دقائق
                except Exception as e:
                    logger.error(f"{Emojis.ERROR} خطأ في التنظيف: {e}")
                    time.sleep(300)
        
        thread = threading.Thread(target=cleanup_old_conversations, daemon=True)
        thread.start()
        logger.info(f"{Emojis.SUCCESS} نظام التنظيف التلقائي مفعل!")
    
    def start_auto_backup(self):
        """نظام نسخ احتياطي تلقائي"""
        def auto_backup():
            while True:
                try:
                    if self.settings.get('auto_backup', True):
                        self.create_backup()
                    time.sleep(3600)  # كل ساعة
                except Exception as e:
                    logger.error(f"{Emojis.ERROR} خطأ في النسخ الاحتياطي: {e}")
                    time.sleep(1800)
        
        thread = threading.Thread(target=auto_backup, daemon=True)
        thread.start()
        logger.info(f"{Emojis.SUCCESS} النظام الاحتياطي التلقائي مفعل!")
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        try:
            backup_data = {
                'users': self.user_stats,
                'admins': self.admins,
                'vip': self.vip_users,
                'banned': self.banned_users,
                'settings': self.settings,
                'backup_time': datetime.now().isoformat(),
                'total_users': len(self.user_stats),
                'total_messages': sum(stats.get('message_count', 0) for stats in self.user_stats.values())
            }
            
            backup_file = self.workspace / f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # حذف النسخ القديمة (احتفظ بآخر 5 فقط)
            backup_files = sorted(self.workspace.glob("backup_*.json"))
            for old_file in backup_files[:-5]:
                old_file.unlink()
                
            logger.info(f"{Emojis.SUCCESS} تم إنشاء نسخة احتياطية: {backup_file.name}")
            return True
        except Exception as e:
            logger.error(f"{Emojis.ERROR} فشل في النسخ الاحتياطي: {e}")
            return False
    
    def cleanup_old_messages(self):
        """تنظيف المحادثات الأقدم من 15 دقيقة"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=15)
            deleted_count = 0
            
            for user_file in self.workspace.glob("user_*.json"):
                try:
                    with open(user_file, 'r', encoding='utf-8') as f:
                        conversation = json.load(f)
                    
                    filtered_conversation = []
                    for msg in conversation:
                        msg_time = datetime.fromisoformat(msg['timestamp'])
                        if msg_time > cutoff_time:
                            filtered_conversation.append(msg)
                        else:
                            deleted_count += 1
                    
                    if filtered_conversation:
                        with open(user_file, 'w', encoding='utf-8') as f:
                            json.dump(filtered_conversation, f, ensure_ascii=False, indent=2)
                    else:
                        user_file.unlink()
                        
                except Exception as e:
                    continue
            
            if deleted_count > 0:
                logger.info(f"{Emojis.SUCCESS} تم تنظيف {deleted_count} رسالة قديمة")
                
        except Exception as e:
            logger.error(f"{Emojis.ERROR} خطأ عام في التنظيف: {e}")
    
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
                'message_limit': self.settings.get('free_messages', 25),
                'used_messages': 0,
                'points': 100,  # نقاط مجانية عند التسجيل
                'level': 1,
                'xp': 0,
                'join_date': datetime.now().strftime('%Y-%m-%d')
            }
        else:
            self.user_stats[user_id]['message_count'] += 1
            self.user_stats[user_id]['last_seen'] = datetime.now().isoformat()
            if message_text:
                self.user_stats[user_id]['last_message'] = message_text[:100]
            self.user_stats[user_id]['is_admin'] = user_id in self.admins
            self.user_stats[user_id]['is_banned'] = user_id in self.banned_users
            self.user_stats[user_id]['is_vip'] = user_id in self.vip_users
            
            # إضافة XP للنشاط
            self.user_stats[user_id]['xp'] = self.user_stats[user_id].get('xp', 0) + 1
            
            # ترقية المستوى
            current_xp = self.user_stats[user_id]['xp']
            current_level = self.user_stats[user_id]['level']
            if current_xp >= current_level * 100:
                self.user_stats[user_id]['level'] = current_level + 1
                self.user_stats[user_id]['points'] += current_level * 10
            
            if not self.is_vip(user_id) and not self.is_admin(user_id):
                self.user_stats[user_id]['used_messages'] += 1
        
        self.save_user_stats()
    
    def can_send_message(self, user_id):
        if self.is_vip(user_id) or self.is_admin(user_id):
            return True, f"{Emojis.VIP} VIP"
        
        if user_id not in self.user_stats:
            return True, f"{Emojis.NEW} جديد"
        
        used = self.user_stats[user_id].get('used_messages', 0)
        limit = self.user_stats[user_id].get('message_limit', self.settings.get('free_messages', 25))
        
        if used < limit:
            remaining = limit - used
            return True, f"{Emojis.SUCCESS} مجاني ({remaining} متبقي)"
        else:
            return False, f"{Emojis.ERROR} انتهت الرسائل ({used}/{limit})"
    
    def add_vip(self, user_id, username, first_name):
        if user_id not in self.vip_users:
            self.vip_users.append(user_id)
            self.save_vip_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_vip'] = True
                self.user_stats[user_id]['points'] += 500  # مكافأة VIP
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
                self.user_stats[user_id]['points'] += 1000  # مكافأة مشرف
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
                    'points': stats.get('points', 0),
                    'level': stats.get('level', 1)
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
                    'points': stats.get('points', 0),
                    'level': stats.get('level', 1)
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
        
        new_limit = self.settings.get('free_messages', 25)
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
                logger.error(f"{Emojis.ERROR} خطأ في تحميل محادثة المستخدم {user_id}: {e}")
                return []
        return []
    
    def save_conversation(self, user_id, conversation):
        self.conversations[user_id] = conversation
        user_file = self.get_user_file(user_id)
        try:
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(conversation[-20:], f, ensure_ascii=False, indent=2)  # حفظ 20 رسالة
        except Exception as e:
            logger.error(f"{Emojis.ERROR} خطأ في حفظ محادثة المستخدم {user_id}: {e}")
    
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

# 🤖 تهيئة النظام المتقدم
memory = MemorySystem()

# 🧠 نظام الذكاء الاصطناعي المتقدم
class AIService:
    API_URL = "http://sii3.top/DARK/api/wormgpt.php"
    
    @staticmethod
    def generate_response(user_id, user_message):
        try:
            can_send, status = memory.can_send_message(user_id)
            if not can_send:
                return f"""
{Emojis.ERROR} **انتهت رسائلك المجانية!**

{status}

{Emojis.VIP} **ترقى إلى VIP للاستخدام غير المحدود!**
{Emojis.MONEY} **مميزات حصرية وسرعة فائقة**

{Emojis.UPGRADE} استخدم /upgrade للترقية الآن!
"""
            
            if memory.is_banned(user_id):
                return f"{Emojis.BAN} **تم حظرك من استخدام موبي.**\n\nللاستفسار تواصل مع المطور."
            
            memory.add_message(user_id, "user", user_message)
            
            try:
                response = AIService.api_call(user_message, user_id)
                if response and len(response.strip()) > 5:
                    return response
            except Exception as api_error:
                logger.warning(f"{Emojis.WARNING} النظام غير متاح: {api_error}")
            
            return AIService.smart_response(user_message, user_id)
            
        except Exception as e:
            logger.error(f"{Emojis.ERROR} خطأ في النظام: {e}")
            return f"{Emojis.WARNING} **عذراً، النظام يواجه صعوبات تقنية.**\n\n{Emojis.LIGHTNING} جرب مرة أخرى بعد قليل!"
    
    @staticmethod
    def api_call(message, user_id):
        try:
            api_url = f"{AIService.API_URL}?text={requests.utils.quote(message)}"
            logger.info(f"{Emojis.BRAIN} موبي يتصل بالنظام: {api_url}")
            
            response = requests.get(api_url, timeout=20)
            
            if response.status_code == 200:
                ai_response = response.text.strip()
                
                # تنظيف الرد من المعلومات غير المرغوب فيها
                lines = ai_response.split('\n')
                clean_lines = []
                for line in lines:
                    if not any(x in line.lower() for x in ['dev:', 'support', 'channel', '@', 'don\'t forget', 'telegram']):
                        clean_lines.append(line)
                ai_response = '\n'.join(clean_lines).strip()
                
                if not ai_response or ai_response.isspace():
                    ai_response = f"{Emojis.BRAIN} **موبي يفكر...**\n\n{Emojis.LIGHTNING} جرب صياغة سؤالك بطريقة أخرى!"
                
                ai_response = ai_response.replace('\\n', '\n').replace('\\t', '\t')
                if len(ai_response) > 2000:
                    ai_response = ai_response[:2000] + "..."
                
                memory.add_message(user_id, "assistant", ai_response)
                
                # إضافة نقاط للمستخدم
                memory.add_points(user_id, 2)
                
                logger.info(f"{Emojis.SUCCESS} موبي رد: {ai_response[:100]}...")
                return ai_response
            else:
                raise Exception(f"خطأ في النظام: {response.status_code}")
                
        except Exception as e:
            logger.error(f"{Emojis.ERROR} خطأ في النظام: {e}")
            raise
    
    @staticmethod
    def smart_response(message, user_id):
        message_lower = message.lower()
        
        responses = {
            'مرحبا': f'{Emojis.PARTY} **أهلاً! أنا موبي** 🤖\n\n{Emojis.LIGHTNING} البوت الأذكى والأسرع!\n{Emojis.BRAIN} كيف يمكنني مساعدتك اليوم؟ 💫',
            'السلام عليكم': f'{Emojis.HEART} **وعليكم السلام ورحمة الله وبركاته!**\n\n{Emojis.ROBOT} موبي جاهز لخدمتك. 🌟',
            'شكرا': f'{Emojis.HEART} **العفو!**\n\n{Emojis.STAR} دائماً سعيد بمساعدتك. 😊',
            'اسمك': f'{Emojis.ROBOT} **أنا موبي!**\n\n{Emojis.BRAIN} المساعد الذكي المتطور!',
            'من صنعك': f'{Emojis.CROWN} **السيد موبي** - {DEVELOPER_USERNAME} 👑',
            'مطورك': f'{Emojis.CROWN} **المطور:** {DEVELOPER_USERNAME}\n{Emojis.STAR} **محترف في الذكاء الاصطناعي**',
            'كيف حالك': f'{Emojis.SUCCESS} **أنا بخير الحمدلله!**\n\n{Emojis.LIGHTNING} جاهز لمساعدتك بأقصى سرعة. ⚡',
            'مساعدة': f'{Emojis.HELP} **موبي يمكنه مساعدتك في:**\n\n{Emojis.BRAIN} • الإجابة على الأسئلة\n{Emojis.MAGIC} • الشرح والتوضيح\n{Emojis.MESSAGE} • الكتابة والإبداع\n{Emojis.LIGHTNING} • حل المشكلات\n\n{Emojis.ROCKET} **ما الذي تحتاج؟** 🎯',
            'موبي': f'{Emojis.ROBOT} **نعم! أنا موبي هنا!**\n\n{Emojis.LIGHTNING} كيف يمكنني مساعدتك؟',
            'vip': f'{Emojis.VIP} **نظام VIP المتقدم**\n\n{Emojis.STAR} يمنحك صلاحيات متقدمة!\n{Emojis.LIGHTNING} سرعة فائقة ووصول غير محدود!\n\n{Emojis.MONEY} للتفاصيل: /upgrade',
            'بريميوم': f'{Emojis.GEM} **باقة البريميوم الحصرية**\n\n{Emojis.STAR} أقصى درجات التميز!\n{Emojis.LIGHTNING} كل الميزات المتقدمة!\n\n{Emojis.UPGRADE} /upgrade للترقية',
        }
        
        for key, response in responses.items():
            if key in message_lower:
                memory.add_message(user_id, "assistant", response)
                memory.add_points(user_id, 1)
                return response
        
        # ردود ذكية عشوائية
        smart_responses = [
            f"{Emojis.BRAIN} **أحلل سؤالك:** '{message}'\n\n{Emojis.LIGHTNING} جاري البحث عن أفضل إجابة...",
            f"{Emojis.ROBOT} **سؤال مثير!** '{message}'\n\n{Emojis.BRAIN} دعني أفكر في هذا بعمق...",
            f"{Emojis.STAR} **رائع!** '{message}'\n\n{Emojis.LIGHTNING} سأستخدم ذكائي المتقدم للإجابة!",
            f"{Emojis.MAGIC} **موبي يعالج:** '{message}'\n\n{Emojis.BRAIN} جاري تحليل الطلب...",
        ]
        
        response = random.choice(smart_responses)
        memory.add_message(user_id, "assistant", response)
        memory.add_points(user_id, 1)
        return response

# 🔧 الدوال المساعدة المتقدمة
def check_subscription(user_id):
    if not memory.settings.get('required_channel') or not memory.settings.get('subscription_enabled', True):
        return True
        
    try:
        chat_member = bot.get_chat_member(memory.settings['required_channel'], user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"{Emojis.ERROR} خطأ في التحقق من الاشتراك: {e}")
        return False

def create_subscription_button():
    if not memory.settings.get('required_channel') or not memory.settings.get('subscription_enabled', True):
        return None
        
    channel_link = f"https://t.me/{memory.settings['required_channel'][1:]}"
    keyboard = InlineKeyboardMarkup()
    channel_btn = InlineKeyboardButton(f"{Emojis.CHANNEL} اشترك في القناة", url=channel_link)
    check_btn = InlineKeyboardButton(f"{Emojis.CHECK} تحقق من الاشتراك", callback_data="check_subscription")
    keyboard.add(channel_btn, check_btn)
    return keyboard

def create_developer_button():
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton(f"{Emojis.CROWN} السيد موبي", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    keyboard.add(developer_btn)
    return keyboard

# 🎨 لوحات التحكم المتقدمة
def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    stats_btn = InlineKeyboardButton(f"{Emojis.CHART} الإحصائيات", callback_data="admin_stats")
    users_btn = InlineKeyboardButton(f"{Emojis.USERS} المستخدمين", callback_data="admin_users")
    admins_btn = InlineKeyboardButton(f"{Emojis.ADMIN} المشرفين", callback_data="admin_manage")
    conversations_btn = InlineKeyboardButton(f"{Emojis.MESSAGE} المحادثات", callback_data="admin_conversations")
    vip_btn = InlineKeyboardButton(f"{Emojis.VIP} إدارة VIP", callback_data="admin_vip")
    broadcast_btn = InlineKeyboardButton(f"{Emojis.BROADCAST} البث", callback_data="admin_broadcast")
    ban_btn = InlineKeyboardButton(f"{Emojis.BAN} الحظر", callback_data="admin_ban")
    points_btn = InlineKeyboardButton(f"{Emojis.POINTS} النقاط", callback_data="admin_points")
    settings_btn = InlineKeyboardButton(f"{Emojis.SETTINGS} الإعدادات", callback_data="admin_settings")
    
    keyboard.add(stats_btn, users_btn)
    keyboard.add(admins_btn, conversations_btn)
    keyboard.add(vip_btn, broadcast_btn)
    keyboard.add(ban_btn, points_btn)
    keyboard.add(settings_btn)
    
    return keyboard

def create_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    help_btn = InlineKeyboardButton(f"{Emojis.HELP} المساعدة", callback_data="user_help")
    status_btn = InlineKeyboardButton(f"{Emojis.STATUS} الحالة", callback_data="user_status")
    vip_btn = InlineKeyboardButton(f"{Emojis.VIP} ترقية", callback_data="user_vip")
    developer_btn = InlineKeyboardButton(f"{Emojis.CROWN} السيد موبي", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    
    keyboard.add(help_btn, status_btn)
    keyboard.add(vip_btn, developer_btn)
    
    return keyboard

# 🚀 تشغيل البوت
def main():
    logger.info(f"{Emojis.ROCKET} بدء تشغيل موبي المتقدم...")
    
    try:
        # تنظيف أي نسخ سابقة
        try:
            bot.remove_webhook()
            time.sleep(3)
            logger.info(f"{Emojis.SUCCESS} تم تنظيف النسخ السابقة")
        except:
            pass
        
        # اختبار الاتصال
        bot_info = bot.get_me()
        logger.info(f"{Emojis.SUCCESS} البوت متصل: @{bot_info.username}")
        logger.info(f"{Emojis.GLOBE} التشغيل على السحابة: نعم")
        logger.info(f"{Emojis.ROBOT} اسم البوت: {bot_info.first_name}")
        logger.info(f"{Emojis.ID} ID البوت: {bot_info.id}")
        logger.info(f"{Emojis.CROWN} المطور: {DEVELOPER_USERNAME}")
        
        # بدء الاستماع
        logger.info(f"{Emojis.SUCCESS} البوت يعمل الآن ويستمع للرسائل...")
        logger.info(f"{Emojis.PARTY} موبي المتقدم جاهز للعمل!")
        
        bot.infinity_polling(
            timeout=60, 
            long_polling_timeout=60,
            logger_level=logging.INFO
        )
        
    except Exception as e:
        logger.error(f"{Emojis.ERROR} خطأ في التشغيل: {e}")
        logger.info(f"{Emojis.LIGHTNING} إعادة المحاولة بعد 10 ثواني...")
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
