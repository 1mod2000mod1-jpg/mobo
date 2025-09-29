#!/usr/bin/env python3
"""
موبي الشرير - بوت الذكاء الاصطناعي المتقدم VIP مع الوضع المجاني
"""

import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("موبي_الشرير_VIP")

# التوكن - هذا فقط المطلوب
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN غير معروف")
    logger.info("💡 تأكد من تعيين TELEGRAM_BOT_TOKEN في Render Environment")
    exit(1)

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# معلومات المطور
DEVELOPER_USERNAME = "@xtt19x"
DEVELOPER_ID = 6521966233

# قناة الاشتراك الإجباري (يمكن تعطيلها بجعلها فارغة)
REQUIRED_CHANNEL = ""  # ضع رابط قناتك هنا أو اتركه فارغاً لتعطيل الاشتراك الإجباري
CHANNEL_LINK = f"https://t.me/{REQUIRED_CHANNEL[1:]}" if REQUIRED_CHANNEL else ""

# نظام الذاكرة والإحصائيات والإدارة
class MemorySystem:
    def __init__(self):
        self.workspace = Path("/tmp/mobi_vip_memory")
        self.workspace.mkdir(exist_ok=True)
        self.conversations = {}
        self.user_stats = self.load_user_stats()
        self.admins = self.load_admins()
        self.banned_users = self.load_banned_users()
        self.vip_users = self.load_vip_users()
    
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
    
    def load_user_stats(self):
        """تحميل إحصائيات المستخدمين"""
        stats_file = self.get_stats_file()
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def load_admins(self):
        """تحميل قائمة المشرفين"""
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
        """تحميل قائمة المحظورين"""
        banned_file = self.get_banned_file()
        if banned_file.exists():
            try:
                with open(banned_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def load_vip_users(self):
        """تحميل قائمة VIP"""
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
    
    def save_user_stats(self):
        """حفظ إحصائيات المستخدمين"""
        stats_file = self.get_stats_file()
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_stats, f, ensure_ascii=False, indent=2)
    
    def save_admins(self):
        """حفظ قائمة المشرفين"""
        admins_file = self.get_admins_file()
        with open(admins_file, 'w', encoding='utf-8') as f:
            json.dump(self.admins, f, ensure_ascii=False, indent=2)
    
    def save_banned_users(self):
        """حفظ قائمة المحظورين"""
        banned_file = self.get_banned_file()
        with open(banned_file, 'w', encoding='utf-8') as f:
            json.dump(self.banned_users, f, ensure_ascii=False, indent=2)
    
    def save_vip_users(self):
        """حفظ قائمة VIP"""
        vip_file = self.get_vip_file()
        with open(vip_file, 'w', encoding='utf-8') as f:
            json.dump(self.vip_users, f, ensure_ascii=False, indent=2)
    
    def update_user_stats(self, user_id, username, first_name, message_text=""):
        """تحديث إحصائيات المستخدم"""
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
                'message_limit': 50,  # حد الرسائل للمستخدمين العاديين
                'used_messages': 0
            }
        else:
            self.user_stats[user_id]['message_count'] += 1
            self.user_stats[user_id]['last_seen'] = datetime.now().isoformat()
            if message_text:
                self.user_stats[user_id]['last_message'] = message_text[:100]
            self.user_stats[user_id]['is_admin'] = user_id in self.admins
            self.user_stats[user_id]['is_banned'] = user_id in self.banned_users
            self.user_stats[user_id]['is_vip'] = user_id in self.vip_users
            
            # زيادة عدد الرسائل المستخدمة للمستخدمين العاديين
            if not self.is_vip(user_id) and not self.is_admin(user_id):
                self.user_stats[user_id]['used_messages'] += 1
        
        self.save_user_stats()
    
    def can_send_message(self, user_id):
        """التحقق إذا كان يمكن للمستخدم إرسال رسالة"""
        if self.is_vip(user_id) or self.is_admin(user_id):
            return True, "VIP"
        
        if user_id not in self.user_stats:
            return True, "جديد"
        
        used = self.user_stats[user_id].get('used_messages', 0)
        limit = self.user_stats[user_id].get('message_limit', 50)
        
        if used < limit:
            return True, f"مجاني ({limit - used} متبقي)"
        else:
            return False, f"انتهت الرسائل ({used}/{limit})"
    
    def add_vip(self, user_id, username, first_name):
        """إضافة مستخدم VIP"""
        if user_id not in self.vip_users:
            self.vip_users.append(user_id)
            self.save_vip_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_vip'] = True
            self.update_user_stats(user_id, username, first_name, "تم ترقيته إلى VIP")
            return True
        return False
    
    def remove_vip(self, user_id):
        """إزالة مستخدم VIP"""
        if user_id in self.vip_users and user_id != DEVELOPER_ID:
            self.vip_users.remove(user_id)
            self.save_vip_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_vip'] = False
            return True
        return False
    
    def is_vip(self, user_id):
        """التحقق إذا كان المستخدم VIP"""
        return user_id in self.vip_users
    
    def add_admin(self, user_id, username, first_name):
        """إضافة مشرف جديد"""
        if user_id not in self.admins:
            self.admins.append(user_id)
            self.save_admins()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_admin'] = True
            self.update_user_stats(user_id, username, first_name, "تم ترقيته إلى مشرف")
            return True
        return False
    
    def remove_admin(self, user_id):
        """إزالة مشرف"""
        if user_id in self.admins and user_id != DEVELOPER_ID:
            self.admins.remove(user_id)
            self.save_admins()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_admin'] = False
            return True
        return False
    
    def ban_user(self, user_id, username, first_name):
        """حظر مستخدم"""
        if user_id not in self.banned_users and user_id != DEVELOPER_ID:
            self.banned_users.append(user_id)
            self.save_banned_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_banned'] = True
            return True
        return False
    
    def unban_user(self, user_id):
        """إلغاء حظر مستخدم"""
        if user_id in self.banned_users:
            self.banned_users.remove(user_id)
            self.save_banned_users()
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_banned'] = False
            return True
        return False
    
    def is_admin(self, user_id):
        """التحقق إذا كان المستخدم مشرف"""
        return user_id in self.admins
    
    def is_banned(self, user_id):
        """التحقق إذا كان المستخدم محظور"""
        return user_id in self.banned_users
    
    def get_user_conversation(self, user_id):
        """الحصول على محادثة مستخدم معين"""
        return self.load_conversation(user_id)
    
    def get_user_stats(self):
        """الحصول على إحصائيات جميع المستخدمين"""
        return self.user_stats
    
    def get_total_users(self):
        """عدد المستخدمين الإجمالي"""
        return len(self.user_stats)
    
    def get_active_today(self):
        """المستخدمين النشطين اليوم"""
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
        """قائمة المشرفين"""
        admins_info = []
        for admin_id in self.admins:
            if admin_id in self.user_stats:
                stats = self.user_stats[admin_id]
                admins_info.append({
                    'id': admin_id,
                    'username': stats.get('username', 'بدون معرف'),
                    'first_name': stats.get('first_name', 'بدون اسم'),
                    'message_count': stats.get('message_count', 0)
                })
        return admins_info
    
    def get_vip_list(self):
        """قائمة VIP"""
        vip_info = []
        for vip_id in self.vip_users:
            if vip_id in self.user_stats:
                stats = self.user_stats[vip_id]
                vip_info.append({
                    'id': vip_id,
                    'username': stats.get('username', 'بدون معرف'),
                    'first_name': stats.get('first_name', 'بدون اسم'),
                    'message_count': stats.get('message_count', 0)
                })
        return vip_info
    
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

# خدمات الذكاء الاصطناعي المتقدم
class AdvancedAIService:
    # API الأساسي
    API_URL = "https://sii3.top/api/DarkCode.php"
    
    @staticmethod
    def generate_response(user_id, user_message):
        """توليد رد باستخدام نظام الذكاء الاصطناعي"""
        try:
            # التحقق من حالة المستخدم أولاً
            can_send, status = memory.can_send_message(user_id)
            if not can_send:
                return f"❌ انتهت رسائلك المجانية! ({status})\n\n💎 ترقى إلى VIP للاستخدام غير المحدود!\n/upgrade للترقية"
            
            if memory.is_banned(user_id):
                return "❌ تم حظرك من استخدام موبي الشرير."
            
            memory.add_message(user_id, "user", user_message)
            
            # استخدام API الأساسي
            try:
                response = AdvancedAIService.primary_api_call(user_message, user_id)
                if response and len(response.strip()) > 5:
                    return response
            except Exception as api_error:
                logger.warning(f"⚠️ API غير متاح: {api_error}")
            
            # استخدام النظام الاحتياطي
            return AdvancedAIService.smart_fallback(user_message, user_id)
            
        except Exception as e:
            logger.error(f"❌ خطأ في نظام موبي: {e}")
            return "⚠️ عذراً، نظام موبي يواجه صعوبات. جرب مرة أخرى!"
    
    @staticmethod
    def primary_api_call(message, user_id):
        """الاتصال بالـ API الأساسي"""
        try:
            api_url = f"{AdvancedAIService.API_URL}?text={requests.utils.quote(message)}"
            logger.info(f"🔗 موبي يتصل بالـAPI: {api_url}")
            
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 200:
                # معالجة الرد
                ai_response = response.text.strip()
                
                # تنظيف الرد من JSON إذا كان موجوداً
                if '{"date"' in ai_response and '"response"' in ai_response:
                    import re
                    match = re.search(r'"response":"([^"]+)"', ai_response)
                    if match:
                        ai_response = match.group(1)
                
                # تنظيف الرد من معلومات المطور
                lines = ai_response.split('\n')
                clean_lines = []
                for line in lines:
                    if not any(x in line.lower() for x in ['dev:', 'support', 'channel', '@', 'don\'t forget']):
                        clean_lines.append(line)
                ai_response = '\n'.join(clean_lines).strip()
                
                if not ai_response or ai_response.isspace():
                    ai_response = "🔄 موبي يفكر... جرب صياغة سؤالك بطريقة أخرى!"
                
                # تنظيف النهائي
                ai_response = ai_response.replace('\\n', '\n').replace('\\t', '\t')
                if len(ai_response) > 2000:
                    ai_response = ai_response[:2000] + "..."
                
                memory.add_message(user_id, "assistant", ai_response)
                logger.info(f"✅ موبي رد: {ai_response[:100]}...")
                return ai_response
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في API: {e}")
            raise
    
    @staticmethod
    def smart_fallback(message, user_id):
        """نظام احتياطي ذكي"""
        message_lower = message.lower()
        
        responses = {
            'مرحبا': 'أهلاً! أنا موبي الشرير 🤖! كيف يمكنني مساعدتك؟ 💫',
            'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته! موبي جاهز لخدمتك. 🌟',
            'شكرا': 'العفو! دائماً سعيد بمساعدتك. 😊',
            'اسمك': 'أنا موبي الشرير! 🤖 الذكاء الاصطناعي الذكي!',
            'كيف حالك': 'أنا بخير الحمدلله! جاهز لمساعدتك. ⚡',
            'مساعدة': 'موبي يمكنه مساعدتك في:\n• الإجابة على الأسئلة\n• الشرح والتوضيح\n• الكتابة والإبداع\n• حل المشكلات\nما الذي تحتاج؟ 🎯',
            'مطور': f'المطور: {DEVELOPER_USERNAME} 👨‍💻',
            'موبي': 'نعم! أنا موبي الشرير هنا! 🤖 كيف يمكنني مساعدتك؟',
            'شرير': '😈 أنا شرير في الذكاء فقط! دائماً هنا لمساعدتك بخير.',
            'ذكاء اصطناعي': '🦾 نعم! أنا موبي الشرير - ذكاء اصطناعي متطور!',
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

# التحقق من الاشتراك في القناة (إذا مفعل)
def check_subscription(user_id):
    """التحقق من اشتراك المستخدم في القناة"""
    if not REQUIRED_CHANNEL:
        return True  # إذا لم يتم تعيين قناة، يعتبر مشتركاً
        
    try:
        chat_member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من الاشتراك: {e}")
        return False

# إنشاء أزرار
def create_subscription_button():
    """زر الاشتراك الإجباري"""
    if not REQUIRED_CHANNEL:
        return None
        
    keyboard = InlineKeyboardMarkup()
    channel_btn = InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)
    check_btn = InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")
    keyboard.add(channel_btn, check_btn)
    return keyboard

def create_developer_button():
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
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
    
    keyboard.add(stats_btn, users_btn)
    keyboard.add(admins_btn, conversations_btn)
    keyboard.add(vip_btn, broadcast_btn)
    keyboard.add(ban_btn)
    
    return keyboard

def create_main_menu():
    """القائمة الرئيسية للمستخدمين"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    help_btn = InlineKeyboardButton("🆘 المساعدة", callback_data="user_help")
    status_btn = InlineKeyboardButton("📊 الحالة", callback_data="user_status")
    vip_btn = InlineKeyboardButton("💎 ترقية", callback_data="user_vip")
    developer_btn = InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    
    keyboard.add(help_btn, status_btn)
    keyboard.add(vip_btn, developer_btn)
    
    return keyboard

# معالجة الاشتراك الإجباري (إذا مفعل)
def require_subscription(func):
    """ديكوراتور للتحقق من الاشتراك"""
    def wrapper(message):
        if not REQUIRED_CHANNEL:
            return func(message)
            
        user_id = message.from_user.id
        
        # المستخدمين VIP والمشرفين معفيين
        if memory.is_vip(user_id) or memory.is_admin(user_id):
            return func(message)
        
        # التحقق من الاشتراك
        if not check_subscription(user_id):
            subscription_msg = f"""
📢 **اشتراك إجباري مطلوب!**

🔐 للوصول إلى موبي الشرير، يجب الاشتراك في قناتنا أولاً:

{REQUIRED_CHANNEL}

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

# الأوامر الأساسية
@bot.message_handler(commands=['start'])
@require_subscription
def handle_start(message):
    """بدء المحادثة"""
    try:
        memory.update_user_stats(
            message.from_user.id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            "/start"
        )
        
        user_status = ""
        if memory.is_vip(message.from_user.id):
            user_status = "🌟 **أنت مستخدم VIP** - وصول غير محدود!\n"
        elif memory.is_admin(message.from_user.id):
            user_status = "🛡️ **أنت مشرف** - صلاحيات كاملة!\n"
        else:
            can_send, status = memory.can_send_message(message.from_user.id)
            user_status = f"🔓 **وضع مجاني** - {status}\n"
        
        welcome_text = f"""
🤖 **مرحباً! أنا موبي الشرير**

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

👨‍💻 **المطور:** {DEVELOPER_USERNAME}
        """
        
        if memory.is_admin(message.from_user.id):
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_admin_panel(), parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_main_menu(), parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['help'])
@require_subscription
def handle_help(message):
    """المساعدة"""
    help_text = f"""
🆘 **مساعدة موبي الشرير**

📋 **الأوامر:**
/start - بدء المحادثة
/help - المساعدة
/status - حالة حسابك
/upgrade - ترقية إلى VIP
/memory - إدارة الذاكرة
/new - محادثة جديدة
/developer - المطور

💡 **الوضع المجاني:**
• 50 رسالة مجانية
• إمكانية الترقية

💎 **مميزات VIP:**
• رسائل غير محدودة
• أولوية في الردود
• دعم فوري

👨‍💻 **المطور:** {DEVELOPER_USERNAME}
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/help")

@bot.message_handler(commands=['upgrade'])
def handle_upgrade(message):
    """ترقية إلى VIP"""
    if memory.is_vip(message.from_user.id):
        vip_text = f"""
🌟 **أنت مستخدم VIP بالفعل!**

🎁 **مميزاتك:**
✅ وصول غير محدود
✅ أولوية في الردود
✅ دعم فوري
✅ مميزات حصرية

👨‍💻 للمزيد: {DEVELOPER_USERNAME}
        """
    else:
        vip_text = f"""
💎 **ترقية إلى VIP**

🔓 **الوضع الحالي:** مجاني (50 رسالة)
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
    """حالة الحساب"""
    user_id = message.from_user.id
    can_send, status = memory.can_send_message(user_id)
    
    if memory.is_vip(user_id):
        status_text = f"""
📊 **حالة حسابك - VIP 🌟**

💎 **النوع:** VIP مميز
📨 **الرسائل:** غير محدود
⚡ **الحالة:** نشط

🎁 **أنت تتمتع بجميع المميزات!**
        """
    elif memory.is_admin(user_id):
        status_text = f"""
📊 **حالة حسابك - مشرف 🛡️**

👑 **النوع:** مشرف
📨 **الرسائل:** غير محدود
⚡ **الحالة:** نشط

🔧 **صلاحيات إدارية كاملة**
        """
    else:
        user_stats = memory.user_stats.get(user_id, {})
        used = user_stats.get('used_messages', 0)
        limit = user_stats.get('message_limit', 50)
        remaining = limit - used
        
        status_text = f"""
📊 **حالة حسابك - مجاني 🔓**

📨 **الرسائل:** {used}/{limit}
🎯 **المتبقي:** {remaining}
⚡ **الحالة:** {status}

💎 **للترقية:** /upgrade
        """
    
    bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/status")

@bot.message_handler(commands=['memory'])
@require_subscription
def handle_memory(message):
    """إدارة الذاكرة"""
    conversation = memory.get_user_conversation(message.from_user.id)
    memory_info = f"""
💾 **ذاكرة موبي**

📊 **معلومات محادثتك:**
• عدد الرسائل: {len(conversation)}
• المساحة: {len(str(conversation))} حرف

🛠 **الخيارات:**
/new - بدء محادثة جديدة

💡 **موبي يحفظ آخر 15 رسالة**
    """
    bot.send_message(message.chat.id, memory_info, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/memory")

@bot.message_handler(commands=['new'])
@require_subscription
def handle_new(message):
    """محادثة جديدة"""
    memory.clear_conversation(message.from_user.id)
    bot.send_message(message.chat.id, "🔄 بدأت محادثة جديدة! ابدأ من الصفر.")
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/new")

@bot.message_handler(commands=['developer'])
def handle_developer(message):
    """المطور"""
    developer_text = f"""
👨‍💻 **مطور موبي الشرير**

📛 **الاسم:** {DEVELOPER_USERNAME}
🆔 **الرقم:** {DEVELOPER_ID}

📞 **للتواصل:** [اضغط هنا](https://t.me/{DEVELOPER_USERNAME[1:]})

🔧 **البوت مبرمج خصيصاً باستخدام:**
• Python 3 المتقدم
• pyTelegramBotAPI
• أنظمة ذكاء اصطناعي متطورة

💬 **للإبلاغ عن مشاكل أو اقتراحات، تواصل مباشرة**
    """
    bot.send_message(message.chat.id, developer_text, reply_markup=create_developer_button(), parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/developer")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    """لوحة التحكم"""
    if not memory.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ ليس لديك صلاحية الوصول!")
        return
    
    admin_text = f"""
👨‍💻 **لوحة تحكم موبي الشرير**

📊 **اختر الإدارة:**
• 📊 الإحصائيات
• 👥 المستخدمين
• 🛡️ المشرفين
• 💬 المحادثات
• 🌟 إدارة VIP
• 📢 البث للمستخدمين
• 🚫 إدارة الحظر

✅ **النظام تحت إشرافك**
    """
    bot.send_message(message.chat.id, admin_text, reply_markup=create_admin_panel(), parse_mode='Markdown')

# معالجة البث
broadcast_state = {}

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    """بدء البث"""
    if not memory.is_admin(message.from_user.id):
        return
    
    broadcast_state[message.from_user.id] = 'waiting_message'
    bot.send_message(message.chat.id, "📢 أرسل رسالة البث (نص، صورة، رابط، فيديو، صوت):")

# معالجة جميع الرسائل
@bot.message_handler(func=lambda message: True)
@require_subscription  
def handle_all_messages(message):
    """معالجة جميع الرسائل"""
    try:
        user_id = message.from_user.id
        
        # التحقق من حالة البث
        if user_id in broadcast_state:
            if broadcast_state[user_id] == 'waiting_message':
                # إرسال البث
                success_count = 0
                total_users = len(memory.user_stats)
                
                for chat_id in memory.user_stats.keys():
                    try:
                        if message.text:
                            bot.send_message(chat_id, f"📢 إشعار من الإدارة:\n\n{message.text}")
                        elif message.photo:
                            bot.send_photo(chat_id, message.photo[-1].file_id, caption=message.caption or "📢 إشعار من الإدارة")
                        elif message.video:
                            bot.send_video(chat_id, message.video.file_id, caption=message.caption or "📢 إشعار من الإدارة")
                        elif message.audio:
                            bot.send_audio(chat_id, message.audio.file_id, caption=message.caption or "📢 إشعار من الإدارة")
                        elif message.document:
                            bot.send_document(chat_id, message.document.file_id, caption=message.caption or "📢 إشعار من الإدارة")
                        success_count += 1
                    except:
                        continue
                
                bot.send_message(user_id, f"✅ تم إرسال البث إلى {success_count}/{total_users} مستخدم")
                broadcast_state.pop(user_id, None)
                return
        
        # تحديث الإحصائيات
        memory.update_user_stats(user_id, message.from_user.username, message.from_user.first_name, message.text)
        
        # التحقق من الحظر
        if memory.is_banned(user_id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام البوت.")
            return
        
        # التحقق من حدود الرسائل
        can_send, status = memory.can_send_message(user_id)
        if not can_send:
            bot.send_message(message.chat.id, f"❌ انتهت رسائلك المجانية! ({status})\n\n💎 ترقى إلى VIP للاستخدام غير المحدود!\n/upgrade للترقية")
            return
        
        # إظهار الكتابة
        bot.send_chat_action(message.chat.id, 'typing')
        
        # توليد الرد
        response = AdvancedAIService.generate_response(user_id, message.text)
        
        if response:
            bot.send_message(message.chat.id, response)
        
        logger.info(f"💬 معالجة رسالة من {message.from_user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في المعالجة: {e}")

# معالجة Callback Queries
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
        handle_broadcast(call.message)
    elif call.data == "admin_ban":
        show_ban_management(call)
    elif call.data == "admin_back":
        show_admin_panel(call)

# دوال الإدارة
def show_admin_panel(call):
    """عرض لوحة التحكم"""
    admin_text = f"""
👨‍💻 **لوحة تحكم موبي الشرير**

📊 **اختر الإدارة:**
• 📊 الإحصائيات
• 👥 المستخدمين
• 🛡️ المشرفين
• 💬 المحادثات
• 🌟 إدارة VIP
• 📢 البث للمستخدمين
• 🚫 إدارة الحظر

✅ **النظام تحت إشرافك**
    """
    bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id,
                        reply_markup=create_admin_panel(), parse_mode='Markdown')

def show_admin_stats(call):
    """عرض الإحصائيات"""
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        vip_count = len(memory.get_vip_list())
        banned_count = len(memory.banned_users)
        total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
        
        stats_text = f"""
📊 **إحصائيات موبي الشرير**

👥 **المستخدمين:**
• الإجمالي: {total_users}
• النشطين: {active_today} 
• VIP: {vip_count}
• المحظورين: {banned_count}
• الرسائل: {total_messages}

🕒 **التحديث:** {datetime.now().strftime('%H:%M:%S')}
        """
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, 
                            reply_markup=create_admin_panel(), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في الإحصائيات: {e}")

def show_users_list(call):
    """عرض المستخدمين"""
    try:
        users = memory.get_user_stats()
        users_text = "👥 **آخر 10 مستخدمين:**\n\n"
        
        sorted_users = sorted(users.items(), key=lambda x: x[1]['last_seen'], reverse=True)
        
        for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
            status = "🌟" if stats.get('is_vip') else "🛡️" if stats.get('is_admin') else "✅"
            username = stats.get('username', 'بدون معرف')
            users_text += f"{i}. {status} {stats['first_name']} (@{username})\n"
            users_text += f"   📝 {stats['message_count']} رسالة\n\n"
        
        users_text += f"📊 الإجمالي: {len(users)} مستخدم"
        
        bot.edit_message_text(users_text, call.message.chat.id, call.message.message_id,
                            reply_markup=create_admin_panel(), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المستخدمين: {e}")

def show_admins_management(call):
    """إدارة المشرفين"""
    try:
        admins = memory.get_admins_list()
        admins_text = "🛡️ **قائمة المشرفين:**\n\n"
        
        for i, admin in enumerate(admins, 1):
            admins_text += f"{i}. {admin['first_name']} (@{admin['username']})\n"
            admins_text += f"   📝 {admin['message_count']} رسالة\n\n"
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(back_btn)
        
        bot.edit_message_text(admins_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة المشرفين: {e}")

def show_conversations_list(call):
    """عرض المحادثات"""
    try:
        users = memory.get_user_stats()
        users_with_conv = [(uid, info) for uid, info in users.items() if memory.get_user_conversation(uid)]
        
        if not users_with_conv:
            conv_text = "💬 **لا توجد محادثات نشطة**"
        else:
            conv_text = "💬 **المستخدمين النشطين:**\n\n"
            for i, (user_id, user_info) in enumerate(users_with_conv[:10], 1):
                conv = memory.get_user_conversation(user_id)
                conv_text += f"{i}. {user_info['first_name']} - {len(conv)} رسالة\n"
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(back_btn)
        
        bot.edit_message_text(conv_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثات: {e}")

def show_vip_management(call):
    """إدارة VIP"""
    try:
        vip_users = memory.get_vip_list()
        vip_text = "🌟 **قائمة VIP:**\n\n"
        
        if not vip_users:
            vip_text += "❌ لا يوجد مستخدمين VIP"
        else:
            for i, user in enumerate(vip_users, 1):
                vip_text += f"{i}. {user['first_name']} (@{user['username']})\n"
        
        keyboard = InlineKeyboardMarkup()
        add_vip_btn = InlineKeyboardButton("➕ إضافة VIP", callback_data="add_vip")
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(add_vip_btn, back_btn)
        
        bot.edit_message_text(vip_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة VIP: {e}")

def show_ban_management(call):
    """إدارة الحظر"""
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
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(back_btn)
        
        bot.edit_message_text(ban_text, call.message.chat.id, call.message.message_id,
                            reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة الحظر: {e}")

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء تشغيل موبي الشرير VIP مع الوضع المجاني...")
    
    try:
        bot.remove_webhook()
        
        # اختبار API
        try:
            test_url = f"{AdvancedAIService.API_URL}?text=test"
            response = requests.get(test_url, timeout=10)
            logger.info(f"✅ API يعمل: {response.status_code}")
        except Exception as api_error:
            logger.warning(f"⚠️ API غير متاح: {api_error}")
        
        logger.info(f"✅ موبي الشرير جاهز - المطور: {DEVELOPER_USERNAME}")
        
        # إضافة بعض المستخدمين VIP افتراضياً
        default_vip_users = [123456789]  # أضف أرقام مستخدمين VIP هنا
        
        logger.info("🤖 البوت يعمل الآن ويستمع للرسائل...")
        
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
