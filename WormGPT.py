import telebot
from telebot import types
import os
import subprocess
import time
import threading
import sqlite3
import logging
import traceback
import re
import ast
import importlib
import tempfile
import shutil
from datetime import datetime, timedelta
import requests
import sys

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TOKEN = "8125153556:AAETI_EUr00QbH1eK4l0qEUtDIb1FQDTLeA"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# مسارات متوافقة مع Render
UPLOAD_FOLDER = "uploaded_files"
DB_FILE = "bot_data.db"
ANALYSIS_FOLDER = "file_analysis"
TOKENS_FOLDER = "tokens_data"

# إنشاء المجلدات إذا لم تكن موجودة
for folder in [UPLOAD_FOLDER, ANALYSIS_FOLDER, TOKENS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# قائمة بالمكتبات الخطرة
DANGEROUS_LIBRARIES = [
    'os', 'sys', 'subprocess', 'shutil', 'ctypes', 'socket', 
    'paramiko', 'ftplib', 'urllib', 'requests', 'selenium',
    'scrapy', 'mechanize', 'webbrowser', 'pyautogui', 'pynput'
]

# قائمة بأنماط الهجمات المعروفة
MALICIOUS_PATTERNS = [
    r"eval\s*\(", r"exec\s*\(", r"__import__\s*\(", r"open\s*\(", 
    r"subprocess\.Popen\s*\(", r"os\.system\s*\(", r"os\.popen\s*\(",
    r"shutil\.rmtree\s*\(", r"os\.remove\s*\(", r"os\.unlink\s*\(",
    r"requests\.(get|post)\s*\(", r"urllib\.request\.urlopen\s*\(",
    r"while True:", r"fork\s*\(", r"pty\s*\(", r"spawn\s*\("
]

running_processes = {}
developer = "@xtt19x"
DEVELOPER_ID = 6521966233

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # إنشاء جميع الجداول
        tables = [
            '''CREATE TABLE IF NOT EXISTS files
            (id INTEGER PRIMARY KEY, filename TEXT, user_id INTEGER, 
             upload_time TIMESTAMP, status TEXT, analysis_result TEXT,
             token TEXT, libraries TEXT)''',
            
            '''CREATE TABLE IF NOT EXISTS admins
            (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, 
             added_by INTEGER, added_time TIMESTAMP)''',
            
            '''CREATE TABLE IF NOT EXISTS banned_users
            (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, 
             banned_by INTEGER, ban_time TIMESTAMP, reason TEXT)''',
            
            '''CREATE TABLE IF NOT EXISTS force_subscribe
            (id INTEGER PRIMARY KEY, channel_id TEXT UNIQUE, 
             channel_username TEXT, added_by INTEGER, added_time TIMESTAMP)''',
            
            '''CREATE TABLE IF NOT EXISTS bot_settings
            (id INTEGER PRIMARY KEY, setting_key TEXT UNIQUE, 
             setting_value TEXT)''',
            
            '''CREATE TABLE IF NOT EXISTS file_analysis
            (id INTEGER PRIMARY KEY, filename TEXT, user_id INTEGER, 
             analysis_time TIMESTAMP, issues_found INTEGER,
             dangerous_libs TEXT, malicious_patterns TEXT,
             file_size INTEGER, lines_of_code INTEGER)''',
            
            '''CREATE TABLE IF NOT EXISTS security_settings
            (id INTEGER PRIMARY KEY, setting_key TEXT UNIQUE, 
             setting_value TEXT, description TEXT)''',
            
            '''CREATE TABLE IF NOT EXISTS vip_users
            (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE, 
             activated_by INTEGER, activation_time TIMESTAMP,
             expiry_date TIMESTAMP, status TEXT)''',
            
            '''CREATE TABLE IF NOT EXISTS blocked_libraries
            (id INTEGER PRIMARY KEY, library_name TEXT UNIQUE, 
             blocked_by INTEGER, block_time TIMESTAMP, reason TEXT)'''
        ]
        
        for table in tables:
            cursor.execute(table)
        
        # إضافة الإعدادات الافتراضية
        default_settings = [
            ('free_mode', 'enabled'),
            ('paid_mode', 'disabled'),
            ('bot_status', 'enabled')
        ]
        
        for setting in default_settings:
            cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)", setting)
        
        # إعدادات الأمان الافتراضية
        default_security_settings = [
            ('auto_scan_files', 'true', 'فحص الملفات تلقائياً قبل الرفع'),
            ('block_dangerous_libs', 'true', 'منع المكتبات الخطرة'),
            ('notify_on_threat', 'true', 'الإشعار عند اكتشاف تهديد'),
            ('max_file_size', '5120', 'أقصى حجم للملف بالكيلوبايت (5120 = 5MB)'),
            ('allowed_file_types', 'py,txt,json', 'أنواع الملفات المسموحة'),
            ('cleanup_interval', '24', 'فترة تنظيف الملفات بالساعات'),
            ('vip_mode', 'false', 'تفعيل وضع VIP'),
            ('auto_install_libs', 'false', 'تثبيت المكتبات تلقائياً')
        ]
        
        for setting in default_security_settings:
            cursor.execute('''INSERT OR IGNORE INTO security_settings 
                            (setting_key, setting_value, description) 
                            VALUES (?, ?, ?)''', setting)
        
        # إضافة المطور كأدمن تلقائياً
        cursor.execute('INSERT OR IGNORE INTO admins (user_id, added_by, added_time) VALUES (?, ?, ?)',
                      (DEVELOPER_ID, DEVELOPER_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        logger.info("✅ تم إنشاء/تهيئة قاعدة البيانات بنجاح")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
        conn.rollback()
    finally:
        conn.close()

def db_execute(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
    except Exception as e:
        logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
        conn.rollback()
    finally:
        conn.close()

def db_fetchone(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result

def db_fetchall(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result

def is_admin(user_id):
    result = db_fetchone("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    return result is not None or user_id == DEVELOPER_ID

def is_vip(user_id):
    result = db_fetchone("SELECT user_id FROM vip_users WHERE user_id = ? AND status = 'active'", (user_id,))
    return result is not None

def
