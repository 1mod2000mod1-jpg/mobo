import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEVELOPER_USERNAME = os.getenv('DEVELOPER_USERNAME', '@Developer')
DEVELOPER_ID = int(os.getenv('DEVELOPER_ID', 0))

# إعدادات الويب هوك
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')

# إعدادات API
API_URL = os.getenv('API_URL', 'https://api.example.com/chat')

# قائمة المشرفين
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# إعدادات قاعدة البيانات
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# إعدادات التحديث
MAX_MESSAGE_LENGTH = 4096
CONVERSATION_LIMIT = 20
RECENT_MESSAGES_MINUTES = 10
