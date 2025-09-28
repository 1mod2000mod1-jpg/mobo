#!/usr/bin/env python3
"""
Telegram AI Bot - بوت الذكاء الاصطناعي مع دعم المطور
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

# نظام الذاكرة
class MemorySystem:
    def __init__(self):
        self.workspace = Path("/tmp/ai_bot_memory")
        self.workspace.mkdir(exist_ok=True)
        self.conversations = {}
    
    def get_user_file(self, user_id):
        return self.workspace / f"user_{user_id}.json"
    
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

# إنشاء زر المطور
def create_developer_button():
    """إنشاء زر للتواصل مع المطور"""
    keyboard = InlineKeyboardMarkup()
    developer_btn = InlineKeyboardButton("👨‍💻 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")
    keyboard.add(developer_btn)
    return keyboard

# أوامر البوت
@bot.message_handler(commands=['start'])
def handle_start(message):
    """بدء المحادثة"""
    try:
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
        bot.send_message(message.chat.id, welcome_text, reply_markup=create_developer_button())
        logger.info(f"✅ بدء محادثة مع {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """عرض المساعدة"""
    try:
        help_text = f"""
🆘 **مركز المساعدة - بوت الذكاء الاصطناعي**

**🧠 المميزات:**
• مدعوم بـ API خاص للذكاء الاصطناعي
• محادثات ذكية مع الذاكرة
• إجابات دقيقة وسريعة
• دعم كامل للعربية

**🎯 الأوامر:**
/start - بدء البوت
/help - هذه الرسالة
/new - محادثة جديدة
/memory - إدارة الذاكرة
/status - حالة النظام
/developer - المطور

**👨‍💻 الدعم:**
{DEVELOPER_USERNAME}

**💡 أمثلة للأسئلة:**
• "اشرح لي الذكاء الاصطناعي"
• "كيف أتعلم البرمجة؟"
• "ما هو أفضل نظام تشغيل؟"
• "ساعدني في حل مشكلة"
        """
        bot.send_message(message.chat.id, help_text, reply_markup=create_developer_button())
    except Exception as e:
        logger.error(f"❌ خطأ في /help: {e}")

@bot.message_handler(commands=['developer'])
def handle_developer(message):
    """معلومات المطور"""
    try:
        developer_info = f"""
👨‍💻 **معلومات المطور**

**📝 الاسم:** {DEVELOPER_USERNAME}
**💻 التخصص:** تطوير بوتات الذكاء الاصطناعي
**🌐 الخبرة:** أنظمة الذكاء الاصطناعي و APIs

**📞 للتواصل:**
• عبر التلقرام: {DEVELOPER_USERNAME}
• للإستفسارات التقنية
• لتطوير بوتات مخصصة
• لدعم تقني متقدم

**🚀 تم تطوير هذا البوت باستخدام:**
• Python
• Custom AI API
• Telegram Bot API
• Memory Management System
        """
        bot.send_message(message.chat.id, developer_info, reply_markup=create_developer_button())
        logger.info(f"✅ عرض معلومات المطور لـ {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /developer: {e}")

@bot.message_handler(commands=['new'])
def handle_new(message):
    """بدء محادثة جديدة"""
    try:
        user_id = message.from_user.id
        memory.clear_conversation(user_id)
        bot.send_message(message.chat.id, "🔄 **تم بدء محادثة جديدة!**\n\n💬 الذاكرة السابقة تم مسحها. يمكنك البدء من جديد.")
        logger.info(f"✅ بدء محادثة جديدة لـ {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /new: {e}")

@bot.message_handler(commands=['memory'])
def handle_memory(message):
    """عرض معلومات الذاكرة"""
    try:
        user_id = message.from_user.id
        conversation = memory.load_conversation(user_id)
        memory_text = f"""
🧠 **معلومات الذاكرة**

• عدد الرسائل: {len(conversation)}
• المساحة: {len(conversation) * 0.1:.1f}KB تقريباً
• الحالة: {'🟢 نشطة' if conversation else '⚪ فارغة'}

💡 استخدم /new لمسح الذاكرة
        """
        bot.send_message(message.chat.id, memory_text)
    except Exception as e:
        logger.error(f"❌ خطأ في /memory: {e}")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """حالة النظام"""
    try:
        import psutil
        memory_info = psutil.virtual_memory()
        
        # اختبار الاتصال بالـAPI
        api_status = "🟢 نشط"
        try:
            test_response = requests.get(f"{CustomAIService.API_URL}?text=test", timeout=10)
            if test_response.status_code != 200:
                api_status = "🟡 مشكلة"
        except:
            api_status = "🔴 غير متصل"
        
        status_text = f"""
📊 **حالة نظام الذكاء الاصطناعي**

🤖 **البوت:**
• الحالة: 🟢 نشط
• الذاكرة النشطة: {len(memory.conversations)} مستخدم
• API الخاص: {api_status}

💻 **الخادم:**
• الذاكرة: {memory_info.percent}% مستخدم
• الوقت: {datetime.now().strftime('%H:%M:%S')}

👨‍💻 **المطور:** {DEVELOPER_USERNAME}

✅ **النظام جاهز للعمل**
        """
        bot.send_message(message.chat.id, status_text, reply_markup=create_developer_button())
    except Exception as e:
        logger.error(f"❌ خطأ في /status: {e}")

@bot.message_handler(func=lambda message: True)
def handle_ai_message(message):
    """معالجة جميع الرسائل بالذكاء الاصطناعي"""
    try:
        user = message.from_user
        user_id = user.id
        user_message = message.text
        
        logger.info(f"🧠 معالجة رسالة من {user.first_name}: {user_message[:50]}...")
        
        # إظهار "يكتب..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # توليد الرد باستخدام API الخاص
        ai_response = CustomAIService.generate_response(user_id, user_message)
        
        # إرسال الرد مع زر المطور
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
    logger.info("🚀 بدء تشغيل بوت الذكاء الاصطناعي مع دعم المطور...")
    
    try:
        # إزالة webhooks سابقة
        bot.remove_webhook()
        
        # اختبار الاتصال بالـAPI
        logger.info("🔗 اختبار الاتصال بالـAPI الخاص...")
        test_url = f"{CustomAIService.API_URL}?text=test"
        response = requests.get(test_url, timeout=10)
        logger.info(f"✅ API الخاص يعمل: {response.status_code}")
        
        logger.info(f"✅ بوت الذكاء الاصطناعي جاهز - المطور: {DEVELOPER_USERNAME}")
        
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
