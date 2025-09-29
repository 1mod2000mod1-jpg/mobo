#!/usr/bin/env python3
"""
Telegram AI Bot - بوت الذكاء الاصطناعي مع صلاحيات المطور الكاملة
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
logger = logging.getLogger("AIBot")

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
        self.workspace = Path("/tmp/ai_bot_memory")
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

# خدمات الذكاء الاصطناعي
class CustomAIService:
    API_URL = "http://fi8.bot-hosting.net:20163/elostoracode"
    
    @staticmethod
    def generate_response(user_id, user_message):
        """توليد رد باستخدام موبي الخاص"""
        try:
            if memory.is_banned(user_id):
                return "❌ تم حظرك من استخدام البوت. تواصل مع المطور لإلغاء الحظر."
            
            memory.add_message(user_id, "user", user_message)
            
            try:
                return CustomAIService.custom_MOBI_call(user_message, user_id)
            except Exception as api_error:
                logger.warning(f"⚠️ موبي الشرير الخاص غير متاح: {api_error}")
                return CustomAIService.smart_fallback(user_message, user_id)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الذكاء موبي الاصطناعي: {e}")
            return "⚠️ عذراً، حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى."

    @staticmethod
    def custom_api_call(message, user_id):
        """الاتصال بالـ موبي الخاص الشرير"""
        try:
            api_url = f"{CustomAIService.API_URL}?text={requests.utils.quote(message)}"
            logger.info(f"🔗 جاري الاتصال بالـ موبي الشرير: {api_url}")
            
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    ai_response = result.get('response', result.get('text', str(result)))
                except:
                    ai_response = response.text.strip()
                
                if len(ai_response) > 2000:
                    ai_response = ai_response[:2000] + "..."
                
                if not ai_response or ai_response.isspace():
                    ai_response = "🔄 جرب صياغة سؤالك بطريقة أخرى"
                
                memory.add_message(user_id, "assistant", ai_response)
                logger.info(f"✅ تم الحصول على رد من API: {ai_response[:100]}...")
                return ai_response
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في موبي الخاص الشرير: {e}")
            raise

    @staticmethod
    def smart_fallback(message, user_id):
        """ردود ذكية عندما لا يعمل API"""
        message_lower = message.lower()
        
        responses = {
            'مرحبا': 'أهلاً وسهلاً! أنا بوت الذكاء موبي الاصطناعي. كيف يمكنني مساعدتك؟ 🎉',
            'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته! أنا هنا لمساعدتك. 🌟',
            'شكرا': 'العفو! دائماً سعيد بمساعدتك. هل تحتاج مساعدة في شيء آخر؟ 😊',
            'اسمك': 'أنا بوت الذكاء الاصطناعي! 🤖',
            'كيف حالك': 'أنا بخير الحمدلله! جاهز لمساعدتك في أي استفسار. 💫',
            'مساعدة': 'يمكنني مساعدتك في:\n• الإجابة على الأسئلة\n• الشرح والتوضيح\n• الكتابة والإبداع\n• حل المشكلات\nما الذي تحتاج مساعدة فيه؟ 🎯',
            'مطور': f'المطور: {DEVELOPER_USERNAME} 👨‍💻',
            'xtt19x': f'هذا هو المطور! {DEVELOPER_USERNAME} 👨‍💻'
        }
        
        for key, response in responses.items():
            if key in message_lower:
                memory.add_message(user_id, "assistant", response)
                return response
        
        import random
        general_responses = [
            f"🔍 أحلل سؤالك: '{message}' - دعني أوصل لـ موبي  للحصول على أفضل إجابة...",
            f"💭 سؤالك مثير: '{message}' - جاري الاستعلام من نظام الذكاء موبي الاصطناعي...",
            f"🎯 رائع! '{message}' - سأستخدم موبي  لتقديم إجابة دقيقة...",
        ]
        
        response = random.choice(general_responses)
        memory.add_message(user_id, "assistant", response)
        return response

# إنشاء أزرار
def create_developer_button():
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    keyboard.add(developer_btn)
    return keyboard

def create_admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    stats_btn = InlineKeyboardButton("📊 إحصائيات الأعضاء", callback_data="admin_stats")
    users_btn = InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users")
    admins_btn = InlineKeyboardButton("🛡️ إدارة المشرفين", callback_data="admin_manage")
    conversations_btn = InlineKeyboardButton("💬 محادثات الأعضاء", callback_data="admin_conversations")
    ban_btn = InlineKeyboardButton("🚫 إدارة الحظر", callback_data="admin_ban")
    broadcast_btn = InlineKeyboardButton("📢 بث للمستخدمين", callback_data="admin_broadcast")
    
    keyboard.add(stats_btn, users_btn)
    keyboard.add(admins_btn, conversations_btn)
    keyboard.add(ban_btn, broadcast_btn)
    
    return keyboard

def create_users_keyboard(users_data, action):
    """إنشاء كيبورد لقائمة المستخدمين"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for user_id, user_info in users_data[:10]:
        btn_text = f"{user_info['first_name']} ({user_info['message_count']} رسالة)"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"{action}_{user_id}"))
    
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    keyboard.add(back_btn)
    
    return keyboard

# الأوامر الأساسية
@bot.message_handler(commands=['start'])
def handle_start(message):
    """بدء المحادثة"""
    try:
        if memory.is_banned(message.from_user.id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام البوت. تواصل مع المطور لإلغاء الحظر.")
            return
        
        memory.update_user_stats(
            message.from_user.id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            "/start"
        )
        
        welcome_text = f"""
🤖 **مرحباً! أنا بوت الذكاء موبي الاصطناعي المتقدم**

🧠 **المميزات:**
✅ ذاكرة محادثات ذكية
✅ دعم كامل للعربية
✅ استجابات فائقة السرعة

💡 **الأوامر المتاحة:**
/start - بدء المحادثة
/help - المساعدة
/new - محادثة جديدة
/memory - إدارة الذاكرة
/status - حالة النظام
/developer - المطور

👨‍💻 **المطور:** {DEVELOPER_USERNAME}

🔧 **اكتب أي سؤال وسأجيبك باستخدام الذكاء موبي الاصطناعي المتقدم والشرير!**
        """
        
        if memory.is_admin(message.from_user.id):
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_admin_panel())
        else:
            bot.send_message(message.chat.id, welcome_text, reply_markup=create_developer_button())
            
        logger.info(f"✅ بدء محادثة مع {message.from_user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """عرض المساعدة"""
    help_text = f"""
🆘 **مساعدة البوت**

📋 **الأوامر المتاحة:**
/start - بدء المحادثة
/help - عرض هذه الرسالة
/new - بدء محادثة جديدة
/memory - إدارة الذاكرة
/status - حالة النظام
/developer - معلومات المطور

💡 **نصائح الاستخدام:**
• اكتب أي سؤال وسأجيبك فوراً
• يمكنني المساعدة في مواضيع متنوعة
• لدي ذاكرة للمحادثة تذكر آخر 15 رسالة

👨‍💻 **المطور:** {DEVELOPER_USERNAME}
    """
    
    bot.send_message(message.chat.id, help_text)
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/help")

@bot.message_handler(commands=['new'])
def handle_new(message):
    """بدء محادثة جديدة"""
    memory.clear_conversation(message.from_user.id)
    bot.send_message(message.chat.id, "🔄 تم بدء محادثة جديدة! يمكنك البدء من الصفر.")
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/new")

@bot.message_handler(commands=['memory'])
def handle_memory(message):
    """إدارة الذاكرة"""
    conversation = memory.get_user_conversation(message.from_user.id)
    memory_info = f"""
💾 **إدارة الذاكرة**

📊 **معلومات المحادثة:**
• عدد الرسائل: {len(conversation)}
• المساحة المستخدمة: {len(str(conversation))} حرف

🛠 **خيارات:**
/new - مسح الذاكرة وبدء محادثة جديدة

💡 **الذاكرة تحفظ آخر 15 رسالة من المحادثة**
    """
    
    bot.send_message(message.chat.id, memory_info)
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/memory")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """حالة النظام"""
    total_users = memory.get_total_users()
    active_today = memory.get_active_today()
    total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    status_text = f"""
📊 **حالة النظام**

👥 **المستخدمين:**
• الإجمالي: {total_users}
• النشطين اليوم: {active_today}
• مجموع الرسائل: {total_messages}

🔄 **الحالة:** ✅ يعمل بشكل طبيعي
🕒 **آخر تحديث:** {current_time}

👨‍💻 **المطور:** {DEVELOPER_USERNAME}
    """
    
    bot.send_message(message.chat.id, status_text)
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/status")

@bot.message_handler(commands=['developer'])
def handle_developer(message):
    """معلومات المطور"""
    developer_text = f"""
👨‍💻 **معلومات المطور السيد موب**

📛 **الاسم:** {DEVELOPER_USERNAME}
🆔 **الرقم:** {DEVELOPER_ID}

📞 **للتواصل:** [اضغط هنا](https://t.me/{DEVELOPER_USERNAME[1:]})

🔧 **لبوت مبرمج خصيصاً باستخدام:**
• 
• السيد
• موب

💬 **للإبلاغ عن مشاكل أو اقتراحات، تواصل مع المطور مباشرة**
    """
    
    bot.send_message(message.chat.id, developer_text, reply_markup=create_developer_button(), parse_mode='Markdown')
    memory.update_user_stats(message.from_user.id, message.from_user.username, message.from_user.first_name, "/developer")

@bot.message_handler(commands=['admin'])
def handle_admin(message):
    """لوحة تحكم المطور"""
    if not memory.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ ليس لديك صلاحية الوصول!")
        return
    
    admin_text = f"""
👨‍💻 **لوحة تحكم المطور** {DEVELOPER_USERNAME}

📊 **اختر الإجراء المطلوب:**

• 📊 إحصائيات الأعضاء
• 👥 قائمة المستخدمين  
• 🛡️ إدارة المشرفين
• 💬 محادثات الأعضاء
• 🚫 إدارة الحظر
• 📢 بث رسالة للمستخدمين

✅ **البوت يعمل تحت إشرافك**
    """
    
    bot.send_message(message.chat.id, admin_text, reply_markup=create_admin_panel())

# معالجة جميع الرسائل النصية
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة جميع الرسائل النصية"""
    try:
        user_id = message.from_user.id
        
        # تحديث الإحصائيات
        memory.update_user_stats(
            user_id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            message.text
        )
        
        # إذا كان محظور
        if memory.is_banned(user_id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام البوت. تواصل مع المطور لإلغاء الحظر.")
            return
        
        # إظهار "يكتب..." 
        bot.send_chat_action(message.chat.id, 'typing')
        
        # توليد الرد
        response = CustomAIService.generate_response(user_id, message.text)
        
        # إرسال الرد
        bot.send_message(message.chat.id, response)
        
        logger.info(f"💬 معالجة رسالة من {message.from_user.first_name}: {message.text[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
        bot.send_message(message.chat.id, "⚠️ عذراً، حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى.")

# معالجة Callback Queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة ضغطات الأزرار"""
    user_id = call.from_user.id
    
    if not memory.is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية الوصول!", show_alert=True)
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
        logger.error(f"❌ خطأ في معالجة الكallback: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في المعالجة!", show_alert=True)

def show_admin_panel(call):
    """عرض لوحة التحكم الرئيسية"""
    admin_text = f"""
👨‍💻 **لوحة تحكم المطور** {DEVELOPER_USERNAME}

📊 **اختر الإجراء المطلوب:**

• 📊 إحصائيات الأعضاء
• 👥 قائمة المستخدمين  
• 🛡️ إدارة المشرفين
• 💬 محادثات الأعضاء
• 🚫 إدارة الحظر
• 📢 بث رسالة للمستخدمين

✅ **البوت يعمل تحت إشرافك**
    """
    
    bot.edit_message_text(
        admin_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_admin_panel(),
        parse_mode='Markdown'
    )

def show_admin_stats(call):
    """عرض إحصائيات الأعضاء"""
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
        banned_users = len(memory.banned_users)
        admins_count = len(memory.get_admins_list())
        
        stats_text = f"""
📊 **إحصائيات البوت**

👥 **المستخدمين:**
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
        bot.answer_callback_query(call.id, "✅ تم تحديث الإحصائيات")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الإحصائيات: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

def show_users_list(call):
    """عرض قائمة المستخدمين"""
    try:
        users = memory.get_user_stats()
        if not users:
            bot.answer_callback_query(call.id, "❌ لا يوجد مستخدمين بعد!", show_alert=True)
            return
        
        users_text = "👥 **آخر 10 مستخدمين:**\n\n"
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
        bot.answer_callback_query(call.id, "✅ تم تحميل قائمة المستخدمين")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المستخدمين: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

def show_conversations_list(call):
    """عرض قائمة محادثات الأعضاء"""
    try:
        users = memory.get_user_stats()
        if not users:
            bot.answer_callback_query(call.id, "❌ لا يوجد مستخدمين بعد!", show_alert=True)
            return
        
        # البحث عن المستخدمين الذين لديهم محادثات
        users_with_conversations = []
        for user_id, user_info in users.items():
            conversation = memory.get_user_conversation(user_id)
            if conversation:
                users_with_conversations.append((user_id, user_info))
        
        if not users_with_conversations:
            bot.answer_callback_query(call.id, "❌ لا توجد محادثات نشطة!", show_alert=True)
            return
        
        conversations_text = "💬 **المستخدمين النشطين:**\n\n"
        
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
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "✅ تم تحميل المحادثات")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثات: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

def view_user_conversation(call):
    """عرض محادثة مستخدم معين"""
    try:
        user_id = int(call.data.split("_")[2])
        conversation = memory.get_user_conversation(user_id)
        user_info = memory.user_stats.get(user_id, {})
        
        if not conversation:
            bot.answer_callback_query(call.id, "❌ لا توجد محادثات لهذا المستخدم!", show_alert=True)
            return
        
        conv_text = f"💬 **محادثة {user_info.get('first_name', 'مستخدم')}:**\n\n"
        
        for msg in conversation[-10:]:
            role = "👤" if msg['role'] == 'user' else "🤖"
            time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            content = msg['content']
            if len(content) > 50:
                content = content[:50] + "..."
            conv_text += f"{role} [{time}]: {content}\n\n"
        
        conv_text += f"📊 إجمالي الرسائل: {len(conversation)}"
        
        bot.edit_message_text(
            conv_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_panel(),
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "✅ تم تحميل المحادثة")
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثة: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

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
        
        bot.edit_message_text(
            admins_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة المشرفين: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

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
        
        bot.edit_message_text(
            ban_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في إدارة الحظر: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

def ask_broadcast_message(call):
    """طلب رسالة البث"""
    bot.answer_callback_query(call.id, "📢 سيتم إضافة خاصية البث قريباً!", show_alert=True)

def make_user_admin(call):
    """ترقية مستخدم إلى مشرف"""
    bot.answer_callback_query(call.id, "🛡️ سيتم إضافة هذه الخاصية قريباً!", show_alert=True)

def remove_user_admin(call):
    """إزالة مشرف"""
    bot.answer_callback_query(call.id, "🛡️ سيتم إضافة هذه الخاصية قريباً!", show_alert=True)

def ban_user_action(call):
    """حظر مستخدم"""
    bot.answer_callback_query(call.id, "🚫 سيتم إضافة هذه الخاصية قريباً!", show_alert=True)

def unban_user_action(call):
    """إلغاء حظر مستخدم"""
    bot.answer_callback_query(call.id, "✅ سيتم إضافة هذه الخاصية قريباً!", show_alert=True)

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء تشغيل بوت الذكاء موبي الاصطناعي...")
    
    try:
        bot.remove_webhook()
        
        # اختبار الاتصال بالـAPI
        logger.info("🔗 اختبار الاتصال بالـAPI الخاص...")
        try:
            test_url = f"{CustomAIService.API_URL}?text=test"
            response = requests.get(test_url, timeout=10)
            logger.info(f"✅ API الخاص يعمل: {response.status_code}")
        except Exception as api_error:
            logger.warning(f"⚠️ API الخاص غير متاح: {api_error}")
        
        logger.info(f"✅ بوت الذكاء موبي الاصطناعي جاهز - المطور: {DEVELOPER_USERNAME}")
        logger.info("🤖 البوت يعمل الآن ويستمع للرسائل...")
        
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")
        logger.info("🔄 إعادة المحاولة بعد 10 ثواني...")
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
