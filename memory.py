import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, db_path="bot_memory.db"):
        self.db_path = db_path
        self.user_stats = {}
        self.conversations = {}
        self.admins = {}
        self.banned_users = {}
        self.init_database()
        self.load_from_database()

    def init_database(self):
        """تهيئة قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # جدول إحصائيات المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    messages_count INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0,
                    join_date TEXT,
                    last_seen TEXT
                )
            ''')
            
            # جدول المحادثات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_stats (user_id)
                )
            ''')
            
            # جدول المشرفين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    added_date TEXT
                )
            ''')
            
            # جدول المستخدمين المحظورين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    ban_date TEXT,
                    reason TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")

    def load_from_database(self):
        """تحميل البيانات من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تحميل إحصائيات المستخدمين
            cursor.execute("SELECT * FROM user_stats")
            for row in cursor.fetchall():
                self.user_stats[row[0]] = {
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'messages_count': row[4],
                    'points': row[5],
                    'join_date': row[6],
                    'last_seen': row[7]
                }
            
            # تحميل المشرفين
            cursor.execute("SELECT * FROM admins")
            for row in cursor.fetchall():
                self.admins[row[0]] = {
                    'username': row[1],
                    'first_name': row[2],
                    'added_date': row[3]
                }
            
            # تحميل المحظورين
            cursor.execute("SELECT * FROM banned_users")
            for row in cursor.fetchall():
                self.banned_users[row[0]] = {
                    'username': row[1],
                    'first_name': row[2],
                    'ban_date': row[3],
                    'reason': row[4]
                }
            
            conn.close()
            logger.info("✅ تم تحميل البيانات من قاعدة البيانات")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل البيانات: {e}")

    def save_user_stats(self, user_id, user_info):
        """حفظ إحصائيات المستخدم"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_stats 
                (user_id, username, first_name, last_name, messages_count, points, join_date, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user_info.get('username'),
                user_info.get('first_name'),
                user_info.get('last_name'),
                user_info.get('messages_count', 0),
                user_info.get('points', 0),
                user_info.get('join_date', datetime.now().isoformat()),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # تحديث الذاكرة
            self.user_stats[user_id] = user_info
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ إحصائيات المستخدم: {e}")
            return False

    def add_conversation(self, user_id, role, content):
        """إضافة محادثة جديدة"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations (user_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, role, content, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المحادثة: {e}")
            return False

    def get_user_conversation(self, user_id, limit=20):
        """الحصول على محادثة المستخدم"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT role, content, timestamp 
                FROM conversations 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'role': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })
            
            conn.close()
            return conversations[::-1]  # عكس الترتيب للحصول على الأقدم أولاً
        except Exception as e:
            logger.error(f"❌ خطأ في جلب المحادثة: {e}")
            return []

    def get_recent_messages(self, user_id, minutes=10):
        """الحصول على الرسائل الحديثة"""
        try:
            time_threshold = (datetime.now() - timedelta(minutes=minutes)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT role, content, timestamp 
                FROM conversations 
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (user_id, time_threshold))
            
            recent_messages = []
            for row in cursor.fetchall():
                recent_messages.append({
                    'role': row[0],
                    'content': row[1],
                    'timestamp': row[2]
                })
            
            conn.close()
            return recent_messages
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الرسائل الحديثة: {e}")
            return []

    def get_user_stats(self):
        """الحصول على إحصائيات جميع المستخدمين"""
        return self.user_stats

    def add_admin(self, user_id, username, first_name):
        """إضافة مشرف"""
        try:
            if user_id in self.admins:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO admins (user_id, username, first_name, added_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.admins[user_id] = {
                'username': username,
                'first_name': first_name,
                'added_date': datetime.now().isoformat()
            }
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المشرف: {e}")
            return False

    def remove_admin(self, user_id):
        """إزالة مشرف"""
        try:
            if user_id not in self.admins:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            del self.admins[user_id]
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إزالة المشرف: {e}")
            return False

    def ban_user(self, user_id, username, first_name, reason="غير محدد"):
        """حظر مستخدم"""
        try:
            if user_id in self.banned_users:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO banned_users (user_id, username, first_name, ban_date, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, datetime.now().isoformat(), reason))
            
            conn.commit()
            conn.close()
            
            self.banned_users[user_id] = {
                'username': username,
                'first_name': first_name,
                'ban_date': datetime.now().isoformat(),
                'reason': reason
            }
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حظر المستخدم: {e}")
            return False

    def unban_user(self, user_id):
        """إلغاء حظر مستخدم"""
        try:
            if user_id not in self.banned_users:
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            del self.banned_users[user_id]
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إلغاء حظر المستخدم: {e}")
            return False

    def is_admin(self, user_id):
        """التحقق إذا كان المستخدم مشرف"""
        return user_id in self.admins

    def is_banned(self, user_id):
        """التحقق إذا كان المستخدم محظور"""
        return user_id in self.banned_users

    def update_user_points(self, user_id, points):
        """تحديث نقاط المستخدم"""
        try:
            if user_id in self.user_stats:
                self.user_stats[user_id]['points'] = points
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE user_stats SET points = ? WHERE user_id = ?
                ''', (points, user_id))
                
                conn.commit()
                conn.close()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث النقاط: {e}")
            return False

# إنشاء كائن الذاكرة العالمي
memory = MemoryManager()
