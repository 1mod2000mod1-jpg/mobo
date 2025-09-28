#!/usr/bin/env python3
"""
Telegram Bot - النسخة النهائية المضمونة
بدون أخطاء syntax
"""

import os
import logging
import telebot

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TelegramBot")

# التوكن
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN غير معروف")
    exit(1)

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    """معالجة أمر /start"""
    try:
        welcome_text = """
🎉 **مرحباً! البوت يعمل بنجاح**

🤖 **تم النشر على Render بنجاح**

✅ **الحالة: نشط ومستقر**

💡 **جرب هذه الأوامر:**
/start - هذه الرسالة
/ping - فحص الاتصال
/help - المساعدة
/about - معلومات عن البوت
/status - حالة الخادم
        """
        bot.send_message(message.chat.id, welcome_text)
        logger.info(f"✅ تم معالجة /start من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /start: {e}")

@bot.message_handler(commands=['ping'])
def handle_ping(message):
    """معالجة أمر /ping"""
    try:
        bot.send_message(message.chat.id, "🏓 **pong!**\n\n✅ البوت يعمل بشكل ممتاز!")
        logger.info(f"✅ تم معالجة /ping من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /ping: {e}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """معالجة أمر /help"""
    try:
        help_text = """
🆘 **مركز المساعدة**

**الأوامر المتاحة:**
/start - بدء البوت
/ping - فحص الاتصال
/help - هذه الرسالة
/about - معلومات عن البوت
/status - حالة الخادم

**معلومات تقنية:**
• يعمل على Render.com
• Python 3.10+
• إصدار مستقر 100%
        """
        bot.send_message(message.chat.id, help_text)
        logger.info(f"✅ تم معالجة /help من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /help: {e}")

@bot.message_handler(commands=['about'])
def handle_about(message):
    """معالجة أمر /about"""
    try:
        about_text = """
🤖 **معلومات عن البوت**

**المميزات:**
✅ يعمل على السحابة (Render)
✅ مستقر وسريع
✅ يدعم الأوامر الأساسية
✅ سهل التطوير

**التقنيات:**
• Python
• pyTelegramBotAPI
• Render.com

**التواصل:**
@YourUsername
        """
        bot.send_message(message.chat.id, about_text)
        logger.info(f"✅ تم معالجة /about من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /about: {e}")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """معالجة أمر /status"""
    try:
        import psutil
        import platform
        from datetime import datetime
        
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status_text = f"""
📊 **حالة الخادم**

**🖥️ معلومات النظام:**
• النظام: {platform.system()} {platform.release()}
• الذاكرة: {memory.percent}% مستخدم
• التخزين: {disk.percent}% مستخدم

**🤖 حالة البوت:**
• الحالة: ✅ نشط
• الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• الإصدار: 1.0.0

**✅ كل شيء يعمل بشكل ممتاز**
        """
        bot.send_message(message.chat.id, status_text)
        logger.info(f"✅ تم معالجة /status من {message.from_user.first_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في /status: {e}")
        bot.send_message(message.chat.id, "⚠️ حدث خطأ في الحصول على حالة الخادم")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة جميع الرسائل النصية"""
    try:
        user = message.from_user
        response = f"""
💬 **شكراً على رسالتك يا {user.first_name}!**

📝 **نص رسالتك:** {message.text}

💡 **للمساعدة، استخدم:** /help

🎯 **البوت يعمل بشكل مثالي على Render!**
        """
        bot.send_message(message.chat.id, response)
        logger.info(f"📩 رسالة من {user.first_name}: {message.text}")
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")

def main():
    """الدالة الرئيسية"""
    logger.info("🚀 بدء تشغيل البوت...")
    
    try:
        # إزالة أي webhook سابق
        logger.info("🔄 إزالة webhooks سابقة...")
        bot.remove_webhook()
        
        logger.info("✅ البوت جاهز، بدء الاستماع...")
        
        # بدء الاستماع للرسائل
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ خطأ رئيسي: {e}")
        logger.info("🔄 إعادة المحاولة بعد 10 ثواني...")
        
        # إعادة المحاولة بعد 10 ثواني
        import time
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()
