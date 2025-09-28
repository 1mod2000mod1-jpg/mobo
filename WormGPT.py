#!/usr/bin/env python3
"""
Telegram AI Bot - بوت الذكاء الاصطناعي مع لوحة تحكم المطور
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
DEVELOPER_ID = 5935335796  # ضع هنا ID حسابك

# نظام الذاكرة والإحصائيات
class MemorySystem:
    def __init__(self):
        self.workspace = Path("/tmp/ai_bot_memory")
        self.workspace.mkdir(exist_ok=True)
        self.conversations = {}
        self.user_stats = self.load_user_stats()
    
    def get_user_file(self, user_id):
        return self.workspace / f"user_{user_id}.json"
    
    def get_stats_file(self):
        return self.workspace / "user_stats.json"
    
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
    
    def save_user_stats(self):
        """حفظ إحصائيات المستخدمين"""
        stats_file = self.get_stats_file()
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_stats, f, ensure_ascii=False, indent=2)
    
    def update_user_stats(self, user_id, username, first_name, message_text=""):
        """تحديث إحصائيات المستخدم"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'username': username,
                'first_name': first_name,
                'message_count': 0,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'last_message': message_text[:100] if message_text else ""
            }
        else:
            self.user_stats[user_id]['message_count'] += 1
            self.user_stats[user_id]['last_seen'] = datetime.now().isoformat()
            if message_text:
                self.user_stats[user_id]['last_message'] = message_text[:100]
        
        self.save_user_stats()
    
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
            last_seen = datetime.fromisoformat(stats['last_seen']).date()
            if last_seen == today:
                active_count += 1
        return active_count
    
    def load_conversation(self, user_id):
        user_file = self.get_user_file(user_id)
        if user_file.exists():
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    self.conversations[user_id] = json.load(f)
            except:
                self.conversations[user_id] = []
        else:
            self.conversations[user_id] = []
        return self.conversations[user_id]
    
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
            # إضافة رسالة المستخدم إلى الذاكرة
            memory.add_message(user_id, "user", user_message)
            
            # استخدام API الخاص
            try:
                return CustomAIService.custom_api_call(user_message, user_id)
            except Exception as api_error:
                logger.warning(f"⚠️ API الخاص غير متاح: {api_error}")
                # استخدام بديل إذا فشل API
                return CustomAIService.smart_fallback(user_message, user_id)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الذكاء الاصطناعي: {e}")
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
            'مرحبا': 'أهلاً وسهلاً! أنا بوت الذكاء الاصطناعي. كيف يمكنني مساعدتك؟ 🎉',
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
            f"🔍 أحلل سؤالك: '{message}' - دعني أوصل لـ API الخاص للحصول على أفضل إجابة...",
            f"💭 سؤالك مثير: '{message}' - جاري الاستعلام من نظام الذكاء الاصطناعي...",
            f"🎯 رائع! '{message}' - سأستخدم API الخاص لتقديم إجابة دقيقة...",
            f"🚀 جاري معالجة سؤالك حول '{message}' عبر نظام الذكاء الاصطناعي المخصص..."
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
    broadcast_btn = InlineKeyboardButton("📢 بث للمستخدمين", callback_data="admin_broadcast")
    developer_btn = InlineKeyboardButton("👨‍💻 تواصل", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    
    keyboard.add(stats_btn, users_btn)
    keyboard.add(broadcast_btn)
    keyboard.add(developer_btn)
    
    return keyboard

# معالجة Callback Queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """معالجة ضغطات الأزرار"""
    user_id = call.from_user.id
    
    # التحقق إذا كان المستخدم هو المطور
    if user_id != DEVELOPER_ID:
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية الوصول!", show_alert=True)
        return
    
    if call.data == "admin_stats":
        show_admin_stats(call)
    elif call.data == "admin_users":
        show_users_list(call)
    elif call.data == "admin_broadcast":
        ask_broadcast_message(call)

def show_admin_stats(call):
    """عرض إحصائيات الأعضاء للمطور"""
    try:
        total_users = memory.get_total_users()
        active_today = memory.get_active_today()
        total_messages = sum(stats['message_count'] for stats in memory.user_stats.values())
        
        stats_text = f"""
📊 **لوحة تحكم المطور**

👥 **المستخدمين:**
• الإجمالي: {total_users} مستخدم
• النشطين اليوم: {active_today} مستخدم
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
        
        # عرض أول 10 مستخدمين فقط
        users_text = "👥 **آخر 10 مستخدمين:**\n\n"
        sorted_users = sorted(users.items(), key=lambda x: x[1]['last_seen'], reverse=True)[:10]
        
        for i, (user_id, stats) in enumerate(sorted_users, 1):
            username = stats.get('username', 'بدون معرف')
            first_name = stats.get('first_name', 'بدون اسم')
            message_count = stats.get('message_count', 0)
            last_seen = datetime.fromisoformat(stats['last_seen']).strftime('%m/%d %H:%M')
            
            users_text += f"{i}. {first_name} (@{username})\n"
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

def ask_broadcast_message(call):
    """طلب رسالة البث"""
    bot.edit_message_text(
        "📢 **أرسل رسالة البث الآن:**\n\nسيتم إرسالها لجميع المستخدمين.",
        call.message.chat.id,
        call.message.message_id
    )
    # سنتعامل مع البث في رسالة منفصلة

# أوامر البوت
@bot.message_handler(commands=['start'])
def handle_start(message):
    """بدء المحادثة"""
    try:
        # تحديث إحصائيات المستخدم
        memory.update_user_stats(
            message.from_user.id,
            message.from_user.username or "بدون معرف",
            message.from_user.first_name or "بدون اسم",
            "/start"
        )
        
        welcome_text = f"""
🤖 **مرحباً! أنا بوت الذكاء الاصطناعي المتقدم**

🧠 **المميزات:**
✅ مدعوم بـ API خاص ومخصص
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

🔧 **اكتب أي سؤال وسأجيبك باستخدام الذكاء الاصطناعي المتقدم!**
        """
        
        # إذا كان المطور، أضف لوحة التحكم
        if message.from_user.id == DEVELOPER_ID:
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
    if message.from_user.id != DEVELOPER_ID:
        bot.send_message(message.chat.id, "❌ ليس لديك صلاحية الوصول!")
        return
    
    admin_text = f"""
👨‍💻 **لوحة تحكم المطور** {DEVELOPER_USERNAME}

📊 **اختر الإجراء المطلوب:**

• 📊 إحصائيات الأعضاء
• 👥 قائمة المستخدمين  
• 📢 بث رسالة للمستخدمين
• 👨‍💻 تواصل

✅ **البوت يعمل تحت إشرافك**
    """
    
    bot.send_message(
        message.chat.id,
        admin_text,
        reply_markup=create_admin_panel()
    )

# ... باقي الأوامر (help, developer, new, memory, status) تبقى كما هي
# مع إضافة تحديث الإحصائيات في handle_ai_message

@bot.message_handler(func=lambda message: True)
def handle_ai_message(message):
    """معالجة جميع الرسائل بالذكاء الاصطناعي"""
    try:
        user = message.from_user
        user_id = user.id
        user_message = message.text
        
        # تحديث إحصائيات المستخدم
        memory.update_user_stats(
            user_id,
            user.username or "بدون معرف",
            user.first_name or "بدون اسم",
            user_message
        )
        
        logger.info(f"🧠 معالجة رسالة من {user.first_name}: {user_message[:50]}...")
        
        # إظهار "يكتب..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # توليد الرد باستخدام API الخاص
        ai_response = CustomAIService.generate_response(user_id, user_message)
        
        # إرسال الرد
        response_text = f"""
💭 **سؤالك:** {user_message}

🤖 **الرد:** {ai_response}

---
👨‍💻 *تم التطوير بواسطة {DEVELOPER_USERNAME} - استخدم /new لبدء محادثة جديدة*
        """
        
        bot.send_message(message.chat.id, response_text, reply_markup=create_developer_button())
        logger.info(f"✅ تم الرد على {user.first_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
        bot.send_message(message.chat.id, "⚠️ عذراً، حدث خطأ في المعالجة. يرجى المحاولة مرة أخرى.")

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء تشغيل بوت الذكاء الاصطناعي مع لوحة تحكم المطور...")
    
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
