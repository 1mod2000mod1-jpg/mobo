#!/usr/bin/env python3
"""
موبي الشرير - بوت الذكاء الاصطناعي المتقدم
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
logger = logging.getLogger("موبي_الشرير")

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

# نظام الذاكرة والإحصائيات والإدارة
class MemorySystem:
    def __init__(self):
        self.workspace = Path("/tmp/mobi_memory")
        self.workspace.mkdir(exist_ok=True)
        self.conversations = {}
        self.user_stats = self.load_user_stats()
        self.admins = self.load_admins()
        self.banned_users = self.load_banned_users()
    
    def get_user_file(self, user_id):
        return self.workspace / f"user_{user_id}.json"
    
    def get_stats_file(self):
        return self.workspace / "user_stats.json"
    
    def get_admins_file(self):
        return self.workspace / "admins.json"
    
    def get_banned_file(self):
        return self.workspace / "banned_users.json"
    
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
                'is_banned': user_id in self.banned_users
            }
        else:
            self.user_stats[user_id]['message_count'] += 1
            self.user_stats[user_id]['last_seen'] = datetime.now().isoformat()
            if message_text:
                self.user_stats[user_id]['last_message'] = message_text[:100]
            self.user_stats[user_id]['is_admin'] = user_id in self.admins
            self.user_stats[user_id]['is_banned'] = user_id in self.banned_users
        
        self.save_user_stats()
    
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
    # روابط API متعددة للطاقة القصوى
    APIS = [
        "https://sii3.top/api/DarkCode.php?text=hello",
        "http://fi8.bot-hosting.net:20163/elostoracode",
        "https://api.deepseek.com/chat/completions",
        "https://api.openai.com/v1/chat/completions"
    ]
    
    @staticmethod
    def generate_response(user_id, user_message):
        """توليد رد باستخدام أقوى نظام ذكاء اصطناعي"""
        try:
            if memory.is_banned(user_id):
                return "❌ تم حظرك من استخدام موبي الشرير. تواصل مع المطور لإلغاء الحظر."
            
            memory.add_message(user_id, "user", user_message)
            
            # المحاولة مع API الأساسي أولاً
            try:
                response = AdvancedAIService.primary_api_call(user_message, user_id)
                if response and len(response.strip()) > 10:
                    return response
            except Exception as api_error:
                logger.warning(f"⚠️ API الأساسي غير متاح: {api_error}")
            
            # استخدام النظام الاحتياطي الذكي
            return AdvancedAIService.smart_ai_system(user_message, user_id)
            
        except Exception as e:
            logger.error(f"❌ خطأ في نظام موبي الشرير: {e}")
            return "⚠️ عذراً، نظام موبي الشرير يواجه بعض الصعوبات. جرب مرة أخرى!"
    
    @staticmethod
    def primary_api_call(message, user_id):
        """الاتصال بالـ API الأساسي"""
        try:
            api_url = f"{AdvancedAIService.APIS[0]}?text={requests.utils.quote(message)}"
            logger.info(f"🔗 موبي الشرير يتصل بالـAPI: {api_url}")
            
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 200:
                ai_response = response.text.strip()
                
                if not ai_response or ai_response.isspace():
                    ai_response = "🔄 موبي الشرير يفكر... جرب صياغة سؤالك بطريقة أخرى!"
                
                # تنظيف الرد
                ai_response = ai_response.replace('\\n', '\n').replace('\\t', '\t')
                if len(ai_response) > 2000:
                    ai_response = ai_response[:2000] + "..."
                
                memory.add_message(user_id, "assistant", ai_response)
                logger.info(f"✅ موبي الشرير حصل على رد: {ai_response[:100]}...")
                return ai_response
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في API موبي الشرير: {e}")
            raise
    
    @staticmethod
    def smart_ai_system(message, user_id):
        """نظام ذكاء اصطناعي احتياطي ذكي"""
        message_lower = message.lower()
        
        # قاعدة معرفة موسعة لموبي الشرير
        responses = {
            'مرحبا': 'أهلاً! أنا موبي الشرير 🤖، الذكاء الاصطناعي المتقدم! كيف يمكنني خدمتك اليوم؟ 💫',
            'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته! أنا موبي الشرير جاهز لمساعدتك. 🌟',
            'شكرا': 'العفو! موبي الشرير دائماً سعيد بمساعدتك. 😊 هل تحتاج شيئاً آخر؟',
            'اسمك': 'أنا موبي الشرير! 🤖 أقوى ذكاء اصطناعي في المنطقة!',
            'كيف حالك': 'أنا بخير الحمدلله! موبي الشرير يعمل بأقصى طاقته لخدمتك. ⚡',
            'مساعدة': 'موبي الشرير يمكنه مساعدتك في:\n• الإجابة على جميع الأسئلة\n• الشرح والتوضيح\n• الكتابة والإبداع\n• حل المشكلات\n• التحليل والاستنتاج\nما الذي تحتاجه؟ 🎯',
            'مطور': f'مطور موبي الشرير: {DEVELOPER_USERNAME} 👨‍💻',
            'موبي': 'نعم! أنا موبي الشرير هنا! 🤖 كيف يمكنني مساعدتك؟',
            'شرير': '😈 أنا شرير في الذكاء فقط! دائماً هنا لمساعدتك بخير.',
            'ذكاء اصطناعي': '🦾 نعم! أنا موبي الشرير - ذكاء اصطناعي متطور بصلاحيات كاملة!',
            
            # إجابات ذكية إضافية
            'من انت': 'أنا موبي الشرير! 🤖 ذكاء اصطناعي متطور بصلاحيات المطور الكاملة!',
            'ماذا تستطيع ان تفعل': 'أستطيع الإجابة على أسئلتك، الكتابة، التحليل، حل المشكلات، والكثير! فقط اسأل! 💪',
            'هل انت ذكي': '🦾 بالتأكيد! أنا موبي الشرير - أذكى مساعد ذكي يمكنك مقابلته!',
            'وقت': f'⏰ الوقت الحالي: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'تاريخ': f'📅 التاريخ: {datetime.now().strftime("%Y-%m-%d")}',
        }
        
        # البحث عن رد مبرمج
        for key, response in responses.items():
            if key in message_lower:
                memory.add_message(user_id, "assistant", response)
                return response
        
        # إجابات ذكية ديناميكية
        smart_responses = [
            f"🤔 {message} - سؤال مثير! دعني أفكر كموبي الشرير...",
            f"💭 محادثة عميقة حول '{message}' - موبي الشرير يحلل...",
            f"🎯 رائع! '{message}' - سأستخدم ذكائي الاصطناعي المتقدم للإجابة!",
            f"⚡ موبي الشرير يعالج سؤالك: '{message}'",
            f"🦾 تحليل متقدم لـ '{message}' - نظام موبي الشرير يعمل...",
            f"🔍 موبي الشرير يبحث في معرفته عن: '{message}'",
        ]
        
        import random
        response = random.choice(smart_responses)
        memory.add_message(user_id, "assistant", response)
        return response

# إنشاء أزرار
def create_developer_button():
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton("👨‍💻 تواصل مع مطور موبي", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    keyboard.add(developer_btn)
    return keyboard

def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    stats_btn = InlineKeyboardButton("📊 إحصائيات موبي", callback_data="admin_stats")
    users_btn = InlineKeyboardButton("👥 مستخدمي موبي", callback_data="admin_users")
    admins_btn = InlineKeyboardButton("🛡️ مشرفي موبي", callback_data="admin_manage")
    conversations_btn = InlineKeyboardButton("💬 محادثات موبي", callback_data="admin_conversations")
    ban_btn = InlineKeyboardButton("🚫 حظر في موبي", callback_data="admin_ban")
    broadcast_btn = InlineKeyboardButton("📢 بث من موبي", callback_data="admin_broadcast")
    
    keyboard.add(stats_btn, users_btn)
    keyboard.add(admins_btn, conversations_btn)
    keyboard.add(ban_btn, broadcast_btn)
    
    return keyboard

# الأوامر الأساسية
@bot.message_handler(commands=['start'])
def handle_start(message):
    """بدء المحادثة مع موبي الشرير"""
    try:
        if memory.is_banned(message.from_user.id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام موبي الشرير. تواصل مع المطور لإلغاء الحظر.")
            return
        
        memory.update_user_stats(
            message.from_user.id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            "/start"
        )
        
        welcome_text = f"""
🤖 **مرحباً! أنا موبي الشرير - الذكاء الاصطناعي المتقدم**

⚡ **قوة موبي الشرير:**
✅ مدعوم بأنظمة ذكاء اصطناعي متطورة
✅ ذاكرة محادثات ذكية متقدمة
✅ دعم كامل للعربية والإنجليزية
✅ استجابات فائقة السرعة والذكاء
✅ صلاحيات مطور كاملة

🎯 **أوامر موبي الشرير:**
/start - بدء المحادثة مع موبي
/help - مساعدة موبي الشرير
/new - محادثة جديدة مع موبي
/memory - ذاكرة موبي
/status - حالة نظام موبي
/developer - مطور موبي
/admin - لوحة تحكم موبي (للمطور)

👨‍💻 **مطور موبي الشرير:** {DEVELOPER_USERNAME}

💬 **اكتب أي سؤال وسأجيبك بقوة الذكاء الاصطناعي المتقدم!**
        """
        
        if memory.is_admin(message.from_user.id):
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_admin_panel(), parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_developer_button(), parse_mode='Markdown')
            
        logger.info(f"✅ بدء محادثة مع {message.from_user.first_name} في موبي الشرير")
        
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """مساعدة موبي الشرير"""
    help_text = f"""
🆘 **مساعدة موبي الشرير**

📋 **أوامر نظام موبي:**
/start - بدء المحادثة مع موبي
/help - عرض رسالة المساعدة
/new - بدء محادثة جديدة
/memory - إدارة ذاكرة موبي
/status - حالة نظام موبي
/developer - معلومات مطور موبي

💡 **نصائح لاستخدام موبي:**
• اكتب أي سؤال وسأجيبك فوراً
• يمكنني المساعدة في جميع المواضيع
• ذاكرة موبي تحفظ آخر 15 رسالة
• نظام موبي يعمل بالذكاء الاصطناعي المتقدم

👨‍💻 **مطور موبي الشرير:** {DEVELOPER_USERNAME}
    """
    
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/help")

@bot.message_handler(commands=['new'])
def handle_new(message):
    """بدء محادثة جديدة مع موبي"""
    memory.clear_conversation(message.from_user.id)
    bot.send_message(message.chat.id, "🔄 موبي الشرير بدأ محادثة جديدة! ابدأ من الصفر.")
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/new")

@bot.message_handler(commands=['memory'])
def handle_memory(message):
    """ذاكرة موبي الشرير"""
    conversation = memory.get_user_conversation(message.from_user.id)
    memory_info = f"""
💾 **ذاكرة موبي الشرير**

📊 **معلومات محادثتك:**
• عدد الرسائل: {len(conversation)}
• المساحة المستخدمة: {len(str(conversation))} حرف

🛠 **خيارات ذاكرة موبي:**
/new - مسح الذاكرة وبدء محادثة جديدة

💡 **موبي يحفظ آخر 15 رسالة من محادثتك**
    """
    
    bot.send_message(message.chat.id, memory_info, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/memory")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """حالة نظام موبي"""
    total_users = memory.get_total_users()
    active_today = memory.get_active_today()
    total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    status_text = f"""
📊 **حالة نظام موبي الشرير**

👥 **مستخدمي موبي:**
• الإجمالي: {total_users}
• النشطين اليوم: {active_today}
• مجموع الرسائل: {total_messages}

⚡ **حالة موبي:** ✅ يعمل بأقصى طاقة
🕒 **آخر تحديث:** {current_time}

👨‍💻 **مطور النظام:** {DEVELOPER_USERNAME}
    """
    
    bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/status")

@bot.message_handler(commands=['developer'])
def handle_developer(message):
    """مطور موبي الشرير"""
    developer_text = f"""
👨‍💻 **مطور موبي الشرير**

📛 **الاسم:** {DEVELOPER_USERNAME}
🆔 **الرقم:** {DEVELOPER_ID}

📞 **للتواصل مع مطور موبي:** [اضغط هنا](https://t.me/{DEVELOPER_USERNAME[1:]})

🔧 **نظام موبي مبرمج خصيصاً باستخدام:**
• Python 3 المتقدم
• pyTelegramBotAPI
• أنظمة ذكاء اصطناعي متطورة
• إدارة ذاكرة متقدمة

💬 **للإبلاغ عن مشاكل أو اقتراحات، تواصل مع مطور موبي مباشرة**
    """
    
    bot.send_message(message.chat.id, developer_text, reply_markup=create_developer_button(), parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/developer")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    """لوحة تحكم موبي الشرير"""
    if not memory.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ ليس لديك صلاحية الوصول إلى لوحة تحكم موبي!")
        return
    
    admin_text = f"""
👨‍💻 **لوحة تحكم موبي الشرير** {DEVELOPER_USERNAME}

📊 **اختر إدارة نظام موبي:**

• 📊 إحصائيات مستخدمي موبي
• 👥 قائمة مستخدمي موبي  
• 🛡️ إدارة مشرفي موبي
• 💬 محادثات مستخدمي موبي
• 🚫 إدارة الحظر في موبي
• 📢 بث رسالة من موبي

✅ **نظام موبي يعمل تحت إشرافك**
    """
    
    bot.send_message(message.chat.id, admin_text, reply_markup=create_admin_panel(), parse_mode='Markdown')

# معالجة جميع الرسائل النصية
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة جميع الرسائل بواسطة موبي الشرير"""
    try:
        user_id = message.from_user.id
        
        # تحديث إحصائيات موبي
        memory.update_user_stats(
            user_id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            message.text
        )
        
        # إذا كان محظور من موبي
        if memory.is_banned(user_id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام موبي الشرير. تواصل مع المطور لإلغاء الحظر.")
            return
        
        # إظهار "موبي يكتب..." 
        bot.send_chat_action(message.chat.id, 'typing')
        
        # توليد الرد بواسطة موبي الشرير
        response = AdvancedAIService.generate_response(user_id, message.text)
        
        # إرسال الرد
        bot.send_message(message.chat.id, response)
        
        logger.info(f"💬 موبي يعالج رسالة من {message.from_user.first_name}: {message.text[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة موبي: {e}")
        bot.send_message(message.chat.id, "⚠️ عذراً، نظام موبي يواجه صعوبة. جرب مرة أخرى!")

# معالجة Callback Queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة ضغطات أزرار موبي"""
    user_id = call.from_user.id
    
    if not memory.is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية الوصول إلى لوحة تحكم موبي!", show_alert=True)
        return
    
    try:
        if call.data == "admin_stats":
            show_admin_stats(call)
        elif call.data == "admin_users":
            show_users_list(call)
        elif call.data == "admin_manage":
            show_admins_management(call)
        elif call.data == "admin_conversations":
            show_conversations_list(call)
        elif call.data == "admin_ban":
            show_ban_management(call)
        elif call.data == "admin_broadcast":
            ask_broadcast_message(call)
        elif call.data == "admin_back":
            show_admin_panel(call)
        elif call.data.startswith("view_conversation_"):
            view_user_conversation(call)
        elif call.data.startswith("make_admin_"):
            make_user_admin(call)
        elif call.data.startswith("remove_admin_"):
            remove_user_admin(call)
        elif call.data.startswith("ban_user_"):
            ban_user_action(call)
        elif call.data.startswith("unban_user_"):
            unban_user_action(call)
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة كallback موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def show_admin_panel(call):
    """عرض لوحة تحكم موبي"""
    admin_text = f"""
👨‍💻 **لوحة تحكم موبي الشرير** {DEVELOPER_USERNAME}

📊 **اختر إدارة نظام موبي:**

• 📊 إحصائيات مستخدمي موبي
• 👥 قائمة مستخدمي موبي  
• 🛡️ إدارة مشرفي موبي
• 💬 محادثات مستخدمي موبي
• 🚫 إدارة الحظر في موبي
• 📢 بث رسالة من موبي

✅ **نظام موبي يعمل تحت إشرافك**
    """
    
    bot.edit_message_text(
        admin_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_admin_panel(),
        parse_mode='Markdown'
    )

def show_admin_stats(call):
    """عرض إحصائيات موبي"""
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
        banned_users = len(memory.banned_users)
        admins_count = len(memory.get_admins_list())
        
        stats_text = f"""
📊 **إحصائيات موبي الشرير**

👥 **مستخدمي موبي:**
• الإجمالي: {total_users} مستخدم
• النشطين اليوم: {active_today} مستخدم
• المحظورين: {banned_users} مستخدم
• المشرفين: {admins_count} مشرف
• مجموع الرسائل: {total_messages} رسالة

🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        bot.edit_message_text(
            stats_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_panel(),
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "✅ تم تحديث إحصائيات موبي")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض إحصائيات موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def show_users_list(call):
    """عرض قائمة مستخدمي موبي"""
    try:
        users = memory.get_user_stats()
        if not users:
            bot.answer_callback_query(call.id, "❌ لا يوجد مستخدمين في موبي بعد!", show_alert=True)
            return
        
        users_text = "👥 **آخر 10 مستخدمين في موبي:**\n\n"
        sorted_users = sorted(users.items(), key=lambda x: x[1]['last_seen'], reverse=True)
        
        for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
            username = stats.get('username', 'بدون معرف')
            first_name = stats.get('first_name', 'بدون اسم')
            message_count = stats.get('message_count', 0)
            last_seen = datetime.fromisoformat(stats['last_seen']).strftime('%m/%d %H:%M')
            status = "🛡️" if stats.get('is_admin') else "🚫" if stats.get('is_banned') else "✅"
            
            users_text += f"{i}. {status} {first_name} (@{username})\n"
            users_text += f"   📝 {message_count} رسالة | 🕒 {last_seen}\n\n"
        
        users_text += f"📊 الإجمالي: {len(users)} مستخدم"
        
        bot.edit_message_text(
            users_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_panel(),
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "✅ تم تحميل قائمة مستخدمي موبي")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض مستخدمي موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def show_conversations_list(call):
    """عرض قائمة محادثات موبي"""
    try:
        users = memory.get_user_stats()
        if not users:
            bot.answer_callback_query(call.id, "❌ لا يوجد مستخدمين في موبي بعد!", show_alert=True)
            return
        
        # البحث عن المستخدمين الذين لديهم محادثات
        users_with_conversations = []
        for user_id, user_info in users.items():
            conversation = memory.get_user_conversation(user_id)
            if conversation:
                users_with_conversations.append((user_id, user_info))
        
        if not users_with_conversations:
            bot.answer_callback_query(call.id, "❌ لا توجد محادثات نشطة في موبي!", show_alert=True)
            return
        
        conversations_text = "💬 **المستخدمين النشطين في موبي:**\n\n"
        
        for i, (user_id, user_info) in enumerate(users_with_conversations[:10], 1):
            username = user_info.get('username', 'بدون معرف')
            first_name = user_info.get('first_name', 'بدون اسم')
            conversation = memory.get_user_conversation(user_id)
            messages_count = len(conversation)
            
            conversations_text += f"{i}. {first_name} (@{username})\n"
            conversations_text += f"   💬 {messages_count} رسالة في المحادثة\n\n"
        
        # إنشاء أزرار للمحادثات
        keyboard = InlineKeyboardMarkup(row_width=2)
        for user_id, user_info in users_with_conversations[:6]:
            btn_text = f"{user_info['first_name']}"
            keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"view_conversation_{user_id}"))
        
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(back_btn)
        
        bot.edit_message_text(
            conversations_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        bot.answer_callback_query(call.id, "✅ تم تحميل محادثات موبي")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض محادثات موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def view_user_conversation(call):
    """عرض محادثة مستخدم في موبي"""
    try:
        user_id = int(call.data.split("_")[2])
        conversation = memory.get_user_conversation(user_id)
        user_info = memory.user_stats.get(user_id, {})
        
        if not conversation:
            bot.answer_callback_query(call.id, "❌ لا توجد محادثات لهذا المستخدم في موبي!", show_alert=True)
            return
        
        conv_text = f"💬 محادثة {user_info.get('first_name', 'مستخدم')} في موبي:\n\n"
        
        for msg in conversation[-8:]:
            role = "👤" if msg['role'] == 'user' else "🤖 موبي"
            time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            content = msg['content']
            if len(content) > 60:
                content = content[:60] + "..."
            conv_text += f"{role} [{time}]: {content}\n\n"
        
        conv_text += f"📊 إجمالي الرسائل: {len(conversation)}"
        
        bot.edit_message_text(
            conv_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_panel()
        )
        bot.answer_callback_query(call.id, "✅ تم تحميل محادثة موبي")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض محادثة موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def show_admins_management(call):
    """إدارة مشرفي موبي"""
    try:
        admins = memory.get_admins_list()
        
        admins_text = "🛡️ قائمة مشرفي موبي:\n\n"
        
        for i, admin in enumerate(admins, 1):
            admins_text += f"{i}. {admin['first_name']} (@{admin['username']})\n"
            admins_text += f"   📝 {admin['message_count']} رسالة\n\n"
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(back_btn)
        
        bot.edit_message_text(
            admins_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة مشرفي موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def show_ban_management(call):
    """إدارة الحظر في موبي"""
    try:
        banned_users = []
        for user_id in memory.banned_users:
            if user_id in memory.user_stats:
                banned_users.append(memory.user_stats[user_id])
        
        ban_text = "🚫 المستخدمين المحظورين من موبي:\n\n"
        
        if not banned_users:
            ban_text += "❌ لا يوجد مستخدمين محظورين في موبي"
        else:
            for i, user in enumerate(banned_users, 1):
                ban_text += f"{i}. {user['first_name']} (@{user['username']})\n\n"
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
        keyboard.add(back_btn)
        
        bot.edit_message_text(
            ban_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة حظر موبي: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في نظام موبي!", show_alert=True)

def ask_broadcast_message(call):
    """طلب رسالة البث من موبي"""
    bot.answer_callback_query(call.id, "📢 خاصية البث من موبي قريباً!", show_alert=True)

def make_user_admin(call):
    """ترقية مستخدم إلى مشرف في موبي"""
    bot.answer_callback_query(call.id, "🛡️ خاصية ترقية المشرفين في موبي قريباً!", show_alert=True)

def remove_user_admin(call):
    """إزالة مشرف من موبي"""
    bot.answer_callback_query(call.id, "🛡️ خاصية إزالة المشرفين في موبي قريباً!", show_alert=True)

def ban_user_action(call):
    """حظر مستخدم من موبي"""
    bot.answer_callback_query(call.id, "🚫 خاصية الحظر في موبي قريباً!", show_alert=True)

def unban_user_action(call):
    """إلغاء حظر مستخدم من موبي"""
    bot.answer_callback_query(call.id, "✅ خاصية إلغاء الحظر في موبي قريباً!", show_alert=True)

def main():
    """الدالة الرئيسية لتشغيل موبي الشرير"""
    logger.info("🚀 بدء تشغيل موبي الشرير - الذكاء الاصطناعي المتقدم...")
    
    try:
        bot.remove_webhook()
        
        # اختبار الاتصال بالـAPI
        logger.info("🔗 موبي الشرير يختبر الاتصال بالـAPI...")
        try:
            test_url = f"{AdvancedAIService.APIS[0]}?text=test"
            response = requests.get(test_url, timeout=10)
            logger.info(f"✅ API موبي الشرير يعمل: {response.status_code}")
        except Exception as api_error:
            logger.warning(f"⚠️ API موبي الشرير غير متاح: {api_error}")
        
        logger.info(f"✅ موبي الشرير جاهز للعمل - المطور: {DEVELOPER_USERNAME}")
        logger.info("🤖 موبي الشرير يعمل الآن ويستمع للرسائل...")
        
        # تشغيل البوت
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل موبي الشرير: {e}")
        logger.info("🔄 موبي الشرير يعيد المحاولة بعد 10 ثواني...")
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
