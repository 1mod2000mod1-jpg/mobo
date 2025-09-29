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
DEVELOPER_ID = 6521966233  # تم تحديثه إلى ID حسابك

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
                    # التأكد من أن المطور الأساسي موجود دائماً
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
            # تحديث إحصائيات المستخدم
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_admin'] = True
            self.update_user_stats(user_id, username, first_name, "تم ترقيته إلى مشرف")
            return True
        return False
    
    def remove_admin(self, user_id):
        """إزالة مشرف"""
        if user_id in self.admins and user_id != DEVELOPER_ID:  # لا يمكن إزالة المطور الأساسي
            self.admins.remove(user_id)
            self.save_admins()
            # تحديث إحصائيات المستخدم
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_admin'] = False
            return True
        return False
    
    def ban_user(self, user_id, username, first_name):
        """حظر مستخدم"""
        if user_id not in self.banned_users and user_id != DEVELOPER_ID:  # لا يمكن حظر المطور
            self.banned_users.append(user_id)
            self.save_banned_users()
            # تحديث إحصائيات المستخدم
            if user_id in self.user_stats:
                self.user_stats[user_id]['is_banned'] = True
            return True
        return False
    
    def unban_user(self, user_id):
        """إلغاء حظر مستخدم"""
        if user_id in self.banned_users:
            self.banned_users.remove(user_id)
            self.save_banned_users()
            # تحديث إحصائيات المستخدم
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
            except:
                return []
        return []
    
    def save_conversation(self, user_id, conversation):
        self.conversations[user_id] = conversation
        user_file = self.get_user_file(user_id)
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(conversation[-15:], f, ensure_ascii=False, indent=2)
    
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

# خدمات الذكاء الاصطناعي مع API الخاص
class CustomAIService:
    
    # رابط API الخاص بك
    API_URL = "http://fi8.bot-hosting.net:20163/elostoracode"
    
    @staticmethod
    def generate_response(user_id, user_message):
        """توليد رد باستخدام API الخاص"""
        try:
            # التحقق إذا كان المستخدم محظور
            if memory.is_banned(user_id):
                return "❌ تم حظرك من استخدام البوت. تواصل مع المطور لإلغاء الحظر."
            
            # إضافة رسالة المستخدم إلى الذاكرة
            memory.add_message(user_id, "user", user_message)
            
            # استخدام API الخاص
            try:
                return CustomAIService.custom_api_call(user_message, user_id)
            except Exception as api_error:
                logger.warning(f"⚠️ موبي الخاص غير متاح: {api_error}")
                # استخدام بديل إذا فشل API
                return CustomAIService.smart_fallback(user_message, user_id)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الذكاء موبي الاصطناعي: {e}")
            return "⚠️ عذراً، حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى."

    @staticmethod
    def custom_api_call(message, user_id):
        """الاتصال بالـ API الخاص"""
        try:
            # بناء رابط API مع النص
            api_url = f"{CustomAIService.API_URL}?text={requests.utils.quote(message)}"
            
            logger.info(f"🔗 جاري الاتصال بالـ API: {api_url}")
            
            # إرسال طلب GET إلى API
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200:
                # محاولة تحليل الرد
                try:
                    # إذا كان الرد JSON
                    result = response.json()
                    ai_response = result.get('response', result.get('text', str(result)))
                except:
                    # إذا كان نص عادي
                    ai_response = response.text.strip()
                
                # تنظيف الرد إذا كان طويلاً
                if len(ai_response) > 2000:
                    ai_response = ai_response[:2000] + "..."
                
                # إذا كان الرد فارغاً
                if not ai_response or ai_response.isspace():
                    ai_response = "🔄 جرب صياغة سؤالك بطريقة أخرى"
                
                # حفظ الرد في الذاكرة
                memory.add_message(user_id, "assistant", ai_response)
                
                logger.info(f"✅ تم الحصول على رد من API: {ai_response[:100]}...")
                return ai_response
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في API الخاص: {e}")
            raise

    @staticmethod
    def smart_fallback(message, user_id):
        """ردود ذكية عندما لا يعمل API"""
        message_lower = message.lower()
        
        # ردود مبرمجة ذكية
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
        
        # البحث عن رد مبرمج
        for key, response in responses.items():
            if key in message_lower:
                memory.add_message(user_id, "assistant", response)
                return response
        
        # إذا لم يكن هناك رد مبرمج، استخدم رد ذكي عام
        general_responses = [
            f"🔍 أحلل سؤالك: '{message}' - دعني أوصل لـ موبي الخاص للحصول على أفضل إجابة...",
            f"💭 سؤالك مثير: '{message}' - جاري الاستعلام من نظام الذكاء موبي الاصطناعي...",
            f"🎯 رائع! '{message}' - سأستخدم API الخاص لتقديم إجابة دقيقة...",
            f"🚀 جاري معالجة سؤالك حول '{message}' عبر نظام الذكاء موبي الاصطناعي المخصص..."
        ]
        
        import random
        response = random.choice(general_responses)
        memory.add_message(user_id, "assistant", response)
        
        return response

# إنشاء أزرار
def create_developer_button():
    """إنشاء زر للتواصل مع المطور"""
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    keyboard.add(developer_btn)
    return keyboard

def create_admin_panel():
    """إنشاء لوحة تحكم المطور"""
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
    
    for user_id, user_info in users_data[:10]:  # أول 10 مستخدمين فقط
        btn_text = f"{user_info['first_name']} ({user_info['message_count']} رسالة)"
        keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"{action}_{user_id}"))
    
    back_btn = InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")
    keyboard.add(back_btn)
    
    return keyboard

# معالجة Callback Queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة ضغطات الأزرار"""
    user_id = call.from_user.id
    
    # التحقق إذا كان المستخدم هو المطور أو مشرف
    if not memory.is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية الوصول!", show_alert=True)
        return
    
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
    """عرض إحصائيات الأعضاء للمطور"""
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
        banned_users = len(memory.banned_users)
        admins_count = len(memory.get_admins_list())
        
        stats_text = f"""
📊 **لوحة تحكم المطور**

👥 **المستخدمين:**
• الإجمالي: {total_users} مستخدم
• النشطين اليوم: {active_today} مستخدم
• المحظورين: {banned_users} مستخدم
• المشرفين: {admins_count} مشرف
• مجموع الرسائل: {total_messages} رسالة

📈 **النشاط:**
• متوسط الرسائل/مستخدم: {total_messages/max(total_users, 1):.1f}
• نسبة النشاط: {(active_today/max(total_users, 1))*100:.1f}%

🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ **البوت يعمل بشكل طبيعي**
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
        
        users_text = "👥 **قائمة المستخدمين:**\n\n"
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

def show_admins_management(call):
    """إدارة المشرفين"""
    try:
        admins = memory.get_admins_list()
        users = memory.get_user_stats()
        
        admins_text = "🛡️ **إدارة المشرفين:**\n\n"
        
        for i, admin in enumerate(admins, 1):
            admins_text += f"{i}. {admin['first_name']} (@{admin['username']})\n"
            admins_text += f"   📝 {admin['message_count']} رسالة\n\n"
        
        # إنشاء كيبورد للمستخدمين لجعلهم مشرفين
        normal_users = [(uid, info) for uid, info in users.items() 
                       if not info.get('is_admin') and uid != DEVELOPER_ID]
        
        if normal_users:
            keyboard = create_users_keyboard(normal_users[:10], "make_admin")
            admins_text += "🔽 اختر مستخدم لترقيته إلى مشرف:"
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
            admins_text += "❌ لا يوجد مستخدمين متاحين للترقية"
        
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

def show_conversations_list(call):
    """عرض قائمة محادثات الأعضاء"""
    try:
        users = memory.get_user_stats()
        if not users:
            bot.answer_callback_query(call.id, "❌ لا يوجد مستخدمين بعد!", show_alert=True)
            return
        
        conversations_text = "💬 **محادثات الأعضاء:**\n\n"
        
        # إنشاء كيبورد للمحادثات
        active_users = [(uid, info) for uid, info in users.items() 
                       if memory.load_conversation(uid)]
        
        if active_users:
            keyboard = create_users_keyboard(active_users[:10], "view_conversation")
            conversations_text += "🔽 اختر مستخدم لعرض محادثته:"
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
            conversations_text += "❌ لا توجد محادثات نشطة"
        
        bot.edit_message_text(
            conversations_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثات: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

def show_ban_management(call):
    """إدارة الحظر"""
    try:
        users = memory.get_user_stats()
        
        ban_text = "🚫 **إدارة الحظر:**\n\n"
        
        # إنشاء كيبورد للمستخدمين لحظرهم
        unbanned_users = [(uid, info) for uid, info in users.items() 
                         if not info.get('is_banned') and uid != DEVELOPER_ID]
        
        banned_users = [(uid, info) for uid, info in users.items() 
                       if info.get('is_banned')]
        
        if unbanned_users:
            keyboard = create_users_keyboard(unbanned_users[:10], "ban_user")
            ban_text += "🔽 اختر مستخدم لحظره:"
        elif banned_users:
            keyboard = create_users_keyboard(banned_users[:10], "unban_user")
            ban_text += "🔽 اختر مستخدم لإلغاء حظره:"
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
            ban_text += "❌ لا يوجد مستخدمين متاحين للإدارة"
        
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
        
        for msg in conversation[-10:]:  # آخر 10 رسائل
            role = "👤" if msg['role'] == 'user' else "🤖"
            time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            conv_text += f"{role} [{time}]: {msg['content'][:100]}...\n\n"
        
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

def make_user_admin(call):
    """ترقية مستخدم إلى مشرف"""
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
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

def ban_user_action(call):
    """حظر مستخدم"""
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
        bot.answer_callback_query(call.id, "❌ حدث خطأ!", show_alert=True)

# ... باقي الدوال (unban_user_action, ask_broadcast_message) تبقى كما هي

# الأوامر الأساسية
@bot.message_handler(commands=['start'])
def handle_start(message):
    """بدء المحادثة"""
    try:
        # التحقق إذا كان المستخدم محظور
        if memory.is_banned(message.from_user.id):
            bot.send_message(message.chat.id, "❌ تم حظرك من استخدام البوت. تواصل مع المطور لإلغاء الحظر.")
            return
        
        # تحديث إحصائيات المستخدم
        memory.update_user_stats(
            message.from_user.id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            "/start"
        )
        
        welcome_text = f"""
🤖 **مرحباً! أنا بوت الذكاء موبي المتقدم**

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

🔧 **اكتب أي سؤال وسأجيبك باستخدام الذكاء موبي المتقدم!**
        """
        
        # إذا كان المطور أو مشرف، أضف لوحة التحكم
        if memory.is_admin(message.from_user.id):
            bot.send_message(
                message.chat.id, 
                welcome_text, 
                reply_markup=create_admin_panel()
            )
        else:
            bot.send_message(
                message.chat.id, 
                welcome_text, 
                reply_markup=create_developer_button()
            )
            
        logger.info(f"✅ بدء محادثة مع {message.from_user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

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
    
    bot.send_message(
        message.chat.id,
        admin_text,
        reply_markup=create_admin_panel()
    )

# ... باقي الأوامر تبقى كما هي

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء تشغيل بوت الذكاء الاصطناعي مع صلاحيات المطور الكاملة...")
    
    try:
        # إزالة webhooks سابقة
        bot.remove_webhook()
        
        # اختبار الاتصال بالـAPI
        logger.info("🔗 اختبار الاتصال بالـAPI الخاص...")
        test_url = f"{CustomAIService.API_URL}?text=test"
        response = requests.get(test_url, timeout=10)
        logger.info(f"✅ API الخاص يعمل: {response.status_code}")
        
        logger.info(f"✅ بوت الذكاء الاصطناعي جاهز - المطور: {DEVELOPER_USERNAME} (ID: {DEVELOPER_ID})")
        
        # بدء الاستماع
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")
        logger.info("🔄 إعادة المحاولة بعد 10 ثواني...")
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
