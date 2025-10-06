#!/usr/bin/env python3
"""
إعدادات موبي - البوت الذكي المتقدم
"""

import os

# إعدادات البوت
class Config:
    # التوكن - استخدم متغير البيئة أو التوكن المباشر
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8253064655:AAExNIiYf09aqEsW42A-rTFQDG-P4skucx4')
    
    # معلومات المطور
    DEVELOPER_USERNAME = "@xtt19x"
    DEVELOPER_ID = 6521966233  # ⚠️ غير هذا إلى رقمك الحقيقي!
    
    # إعدادات البوت
    BOT_SETTINGS = {
        "required_channel": "",
        "free_messages": 50,
        "welcome_content": {"type": "text", "content": ""},
        "subscription_enabled": False
    }
    
    # إعدادات API الذكاء الاصطناعي
    AI_API_URL = "https://sii3.top/api/grok4.php"
    AI_TIMEOUT = 15
    
    # إعدادات الذاكرة
    MEMORY_WORKSPACE = "/tmp/mobi_memory"
    MAX_CONVERSATION_LENGTH = 15
    CLEANUP_INTERVAL = 300  # 5 دقائق
    
    # إعدادات التسجيل
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# التحقق من الإعدادات
def validate_config():
    if not Config.BOT_TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN غير معروف")
    
    if Config.DEVELOPER_ID == 6521966233:
        print("⚠️  تنبيه: لم يتم تغيير DEVELOPER_ID، تأكد من تعيين رقمك الحقيقي!")
    
    return True
