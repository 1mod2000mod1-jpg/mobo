from flask import Flask, request, jsonify
import threading
from datetime import datetime
import requests
import logging
import os
import sqlite3
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# تهيئة تطبيق Flask
app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# استيراد الملفات الأخرى
from memory import memory
from config import *

# متغيرات الحالة
points_state = {}

@app.route('/')
def home():
    return "✅ موبي بوت يعمل بتقنية الويب هوك - جميع الميزات نشطة!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    معالج الويب هوك الرئيسي لجميع التحديثات
    """
    try:
        if request.content_type == 'application/json':
            json_data = request.get_json()
            logger.info(f"📥 تم استلام تحديث: {json_data}")
            
            # معالجة التحديث في خيط منفصل
            threading.Thread(target=process_update, args=(json_data,)).start()
            
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Invalid content type"}), 400
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الويب هوك: {e}")
        return jsonify({"error": str(e)}), 500

def process_update(update):
    """
    معالجة التحديثات الواردة من تليجرام
    """
    try:
        # معالجة callback queries
        if 'callback_query' in update:
            call = update['callback_query']
            handle_callback_query(call)
        
        # معالجة الرسائل النصية
        elif 'message' in update and 'text' in update['message']:
            message = update['message']
            handle_message(message)

        # معالجة أمر /start
        elif 'message' in update and 'entities' in update['message']:
            message = update['message']
            for entity in message['entities']:
                if entity['type'] == 'bot_command':
                    handle_command(message)
                    break
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة التحديث: {e}")

def handle_command(message):
    """معالجة الأوامر"""
    try:
        text = message['text']
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        if text == '/start':
            handle_start_command(message)
        elif text == '/admin' and memory.is_admin(user_id):
            handle_admin_command(message)
        elif text == '/stats':
            handle_stats_command(message)
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الأمر: {e}")

def handle_start_command(message):
    """معالجة أمر /start"""
    try:
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        user_name = message['from'].get('first_name', 'مستخدم')
        
        # حفظ بيانات المستخدم
        user_info = {
            'username': message['from'].get('username'),
            'first_name': user_name,
            'last_name': message['from'].get('last_name', ''),
            'messages_count': 1,
            'points': 0,
            'join_date': datetime.now().isoformat()
        }
        memory.save_user_stats(user_id, user_info)
        
        # رسالة الترحيب
        welcome_text = f"""🎉 أهلاً وسهلاً بك {user_name}!

🤖 أنا **موبي** - بوت الذكاء الاصطناعي المتقدم

يمكنني مساعدتك في:
• الإجابة على أسئلتك
• المحادثة الذكية
• تقديم المعلومات والنصائح

💡 فقط اكتب رسالتك وسأرد عليك فوراً!"""
        
        bot_send_message(chat_id, welcome_text)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة أمر start: {e}")

def handle_admin_command(message):
    """معالجة أمر /admin"""
    try:
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        if not memory.is_admin(user_id):
            bot_send_message(chat_id, "❌ ليس لديك صلاحية للوصول لوحة المشرفين!")
            return
        
        admin_text = """👑 **لوحة تحكم المشرفين**

اختر أحد الخيارات أدناه:"""
        
        keyboard = {
            'inline_keyboard': [
                [{'text': '👥 إدارة المستخدمين', 'callback_data': 'admin_users'}],
                [{'text': '📊 الإحصائيات', 'callback_data': 'view_stats'}],
                [{'text': '⚙️ الإعدادات', 'callback_data': 'admin_settings'}]
            ]
        }
        
        bot_send_message(chat_id, admin_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة أمر admin: {e}")

def handle_stats_command(message):
    """معالجة أمر /stats"""
    try:
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        user_info = memory.user_stats.get(user_id, {})
        
        stats_text = f"""📊 **إحصائياتك الشخصية**

👤 الاسم: {user_info.get('first_name', 'مستخدم')}
📨 عدد الرسائل: {user_info.get('messages_count', 0)}
🎯 النقاط: {user_info.get('points', 0)}
📅 تاريخ الانضمام: {user_info.get('join_date', 'غير معروف')}"""
        
        bot_send_message(chat_id, stats_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة أمر stats: {e}")

def handle_callback_query(call):
    """
    معالجة استعلامات الـ callback
    """
    try:
        data = call['data']
        user_id = call['from']['id']
        
        # التحقق من صلاحية المشرف للوحة التحكم
        if data in ['admin_users', 'view_stats', 'admin_settings', 'view_recent_all', 
                   'manage_admins', 'manage_bans'] and not memory.is_admin(user_id):
            bot_answer_callback_query(call['id'], "❌ ليس لديك صلاحية للوصول لهذا القسم!", show_alert=True)
            return
        
        if data.startswith('view_conversation_'):
            view_conversation_webhook(call)
        elif data.startswith('view_recent_'):
            view_recent_messages_webhook(call)
        elif data.startswith('make_admin_'):
            make_user_admin_webhook(call)
        elif data.startswith('remove_admin_'):
            remove_user_admin_webhook(call)
        elif data.startswith('ban_user_'):
            ban_user_action_webhook(call)
        elif data.startswith('unban_user_'):
            unban_user_action_webhook(call)
        elif data.startswith('add_points_'):
            add_points_action_webhook(call)
        elif data.startswith('remove_points_'):
            remove_points_action_webhook(call)
        elif data == 'welcome_settings':
            handle_welcome_settings_webhook(call)
        elif data == 'view_recent_all':
            view_recent_messages_webhook(call)
        elif data == 'admin_users':
            show_admin_users_webhook(call)
        elif data == 'view_stats':
            show_stats_webhook(call)
        elif data == 'admin_settings':
            show_admin_settings_webhook(call)
        elif data == 'manage_admins':
            show_admins_management_webhook(call)
        elif data == 'manage_bans':
            show_ban_management_webhook(call)
        elif data == 'admin_panel':
            show_admin_panel_webhook(call)
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الـ callback: {e}")

def handle_message(message):
    """
    معالجة الرسائل النصية
    """
    try:
        user_id = message['from']['id']
        text = message['text']
        chat_id = message['chat']['id']
        
        # تخطي الأوامر (يتم معالجتها في handle_command)
        if text.startswith('/'):
            return
        
        # التحقق إذا كان المستخدم محظوراً
        if memory.is_banned(user_id):
            bot_send_message(chat_id, "❌ تم حظرك من استخدام البوت.")
            return
        
        # معالجة إضافة النقاط
        if user_id in points_state:
            handle_points_input(user_id, text, chat_id)
            return
        
        # معالجة الرسائل العادية
        handle_normal_message(user_id, text, chat_id, message)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")

def handle_normal_message(user_id, text, chat_id, message):
    """معالجة الرسائل العادية"""
    try:
        # حفظ إحصائيات المستخدم
        user_info = memory.user_stats.get(user_id, {})
        updated_info = {
            'username': message['from'].get('username'),
            'first_name': message['from'].get('first_name', 'مستخدم'),
            'last_name': message['from'].get('last_name', ''),
            'messages_count': user_info.get('messages_count', 0) + 1,
            'points': user_info.get('points', 0),
            'join_date': user_info.get('join_date', datetime.now().isoformat()),
            'last_seen': datetime.now().isoformat()
        }
        memory.save_user_stats(user_id, updated_info)
        
        # حفظ المحادثة
        memory.add_conversation(user_id, 'user', text)
        
        # توليد الرد (مؤقت - يمكنك إضافة خدمة الذكاء الاصطناعي لاحقاً)
        response = generate_ai_response(text, user_id)
        
        # إرسال الرد
        bot_send_message(chat_id, response)
        
        # حفظ رد البوت
        memory.add_conversation(user_id, 'assistant', response)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة العادية: {e}")
        bot_send_message(chat_id, "❌ عذراً، حدث خطأ في معالجة رسالتك. يرجى المحاولة لاحقاً.")

def generate_ai_response(message, user_id):
    """توليد رد من الذكاء الاصطناعي (مؤقت)"""
    try:
        # ردود افتراضية - يمكنك استبدالها بخدمة الذكاء الاصطناعي الحقيقية
        responses = [
            "أهلاً بك! كيف يمكنني مساعدتك اليوم؟ 🌟",
            "شكراً لرسالتك! هل تحتاج مساعدة في شيء محدد؟ 🤔",
            "مرحباً! أنا هنا لمساعدتك في أي استفسار لديك 💫",
            "أهلاً وسهلاً! اشرح لي ما تحتاج وسأ尽力 لمساعدتك 🚀",
            "شكراً لتواصلك معي! كيف يمكنني خدمتك اليوم؟ 📚"
        ]
        
        # إضافة بعض الردود الذكية البسيطة
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['مرحبا', 'اهلا', 'السلام']):
            return "أهلاً وسهلاً بك! 🌸 كيف حالك اليوم؟"
        elif any(word in message_lower for word in ['شكرا', 'مشكور', 'يعطيك']):
            return "العفو! 😊 دائماً سعيد بمساعدتك. هل هناك شيء آخر تحتاجه؟"
        elif any(word in message_lower for word in ['اسمك', 'من انت', 'البوت']):
            return "أنا **موبي** - بوت الذكاء الاصطناعي المتقدم! 🤖\nأساعدك في الإجابة على أسئلتك وتقديم المعلومات المفيلة."
        elif '?' in message:
            return "سؤال ممتاز! 💡 للأسف إمكانياتي حالياً محدودة، لكنني أتطور باستمرار. يمكنك تجربة سؤال آخر!"
        else:
            # رد عشوائي من القائمة
            import random
            return random.choice(responses)
            
    except Exception as e:
        logger.error(f"❌ خطأ في توليد الرد: {e}")
        return "أهلاً بك! شكراً لرسالتك. كيف يمكنني مساعدتك؟ 🌟"

# باقي الدوال保持不变 (نفس الدوال السابقة)
def view_conversation_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        conversation = memory.get_user_conversation(user_id)
        user_info = memory.user_stats.get(user_id, {})
        
        if not conversation:
            bot_answer_callback_query(call['id'], "❌ لا توجد محادثات لهذا المستخدم!", show_alert=True)
            return
        
        conv_text = f"💬 **محادثة {user_info.get('first_name', 'مستخدم')}:**\n\n"
        
        for msg in conversation[-8:]:
            role = "👤" if msg['role'] == 'user' else "🤖 موبي"
            time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            content = msg['content']
            if len(content) > 60:
                content = content[:60] + "..."
            conv_text += f"{role} [{time}]: {content}\n\n"
        
        conv_text += f"📊 إجمالي الرسائل: {len(conversation)}"
        
        bot_edit_message_text(conv_text, call['message']['chat']['id'], call['message']['message_id'],
                            reply_markup=create_admin_panel(), parse_mode='Markdown')
        bot_answer_callback_query(call['id'], "✅ تم تحميل المحادثة")
    except Exception as e:
        logger.error(f"❌ خطأ في عرض المحادثة: {e}")

def view_recent_messages_webhook(call):
    try:
        if call['data'] == "view_recent_all":
            users_text = "🕒 **اختر مستخدم لعرض رسائله الأخيرة:**\n\n"
            users = memory.get_user_stats()
            keyboard = create_users_keyboard(users, "view_recent")
            
        else:
            user_id = int(call['data'].split("_")[2])
            user_info = memory.user_stats.get(user_id, {})
            recent_messages = memory.get_recent_messages(user_id, 10)
            
            users_text = f"🕒 **آخر رسائل {user_info.get('first_name', 'مستخدم')} (10 دقائق):**\n\n"
            
            if not recent_messages:
                users_text += "❌ لا توجد رسائل في آخر 10 دقائق"
            else:
                for msg in recent_messages[-5:]:
                    role = "👤" if msg['role'] == 'user' else "🤖"
                    time = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
                    content = msg['content']
                    if len(content) > 50:
                        content = content[:50] + "..."
                    users_text += f"{role} [{time}]: {content}\n\n"
            
            keyboard = create_back_button("admin_users")
        
        bot_edit_message_text(users_text, call['message']['chat']['id'], call['message']['message_id'],
                            reply_markup=keyboard, parse_mode='Markdown')
        bot_answer_callback_query(call['id'], "🕒 الرسائل الأخيرة")
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الرسائل الأخيرة: {e}")

# ... (باقي الدوال كما هي من الإصدار السابق)

def show_admin_panel_webhook(call):
    """عرض لوحة التحكم الرئيسية"""
    admin_text = """👑 **لوحة تحكم المشرفين**

اختر أحد الخيارات أدناه:"""
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '👥 إدارة المستخدمين', 'callback_data': 'admin_users'}],
            [{'text': '📊 الإحصائيات', 'callback_data': 'view_stats'}],
            [{'text': '⚙️ الإعدادات', 'callback_data': 'admin_settings'}]
        ]
    }
    
    bot_edit_message_text(admin_text, call['message']['chat']['id'], call['message']['message_id'],
                         reply_markup=keyboard, parse_mode='Markdown')

def show_stats_webhook(call):
    """عرض الإحصائيات العامة"""
    try:
        users = memory.get_user_stats()
        total_users = len(users)
        total_messages = sum(user.get('messages_count', 0) for user in users.values())
        
        stats_text = f"""📊 **الإحصائيات العامة**

👥 إجمالي المستخدمين: {total_users}
📨 إجمالي الرسائل: {total_messages}
🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}

**أحدث المستخدمين:**
"""
        
        # عرض آخر 5 مستخدمين
        recent_users = list(users.items())[-5:]
        for user_id, user_info in recent_users:
            stats_text += f"• {user_info.get('first_name', 'مستخدم')} - {user_info.get('messages_count', 0)} رسالة\n"
        
        keyboard = create_back_button("admin_panel")
        
        bot_edit_message_text(stats_text, call['message']['chat']['id'], call['message']['message_id'],
                             reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطأ في عرض الإحصائيات: {e}")

def show_admin_settings_webhook(call):
    """عرض إعدادات المشرف"""
    settings_text = """⚙️ **إعدادات المشرف**

اختر الإعداد الذي تريد تعديله:"""
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🎉 إعدادات الترحيب', 'callback_data': 'welcome_settings'}],
            [{'text': '👑 إدارة المشرفين', 'callback_data': 'manage_admins'}],
            [{'text': '🚫 إدارة الحظر', 'callback_data': 'manage_bans'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
        ]
    }
    
    bot_edit_message_text(settings_text, call['message']['chat']['id'], call['message']['message_id'],
                         reply_markup=keyboard, parse_mode='Markdown')

# دوال API تليجرام
def bot_send_message(chat_id, text, reply_markup=None, parse_mode=None):
    """إرسال رسالة عبر API تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    if parse_mode:
        payload['parse_mode'] = parse_mode
    
    try:
        response = requests.post(url, json=payload)
        logger.info(f"✅ تم إرسال رسالة لـ {chat_id}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")

def bot_edit_message_text(text, chat_id, message_id, reply_markup=None, parse_mode=None):
    """تعديل نص الرسالة عبر API تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    if parse_mode:
        payload['parse_mode'] = parse_mode
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"❌ خطأ في تعديل الرسالة: {e}")

def bot_answer_callback_query(callback_query_id, text, show_alert=False):
    """الرد على استعلام الـ callback"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {
        'callback_query_id': callback_query_id,
        'text': text,
        'show_alert': show_alert
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"❌ خطأ في الرد على الـ callback: {e}")

def setup_webhook():
    """إعداد الويب هوك في تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    
    payload = {
        'url': webhook_url,
        'drop_pending_updates': True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.json().get('ok'):
            logger.info(f"✅ تم إعداد الويب هوك بنجاح! الرابط: {webhook_url}")
        else:
            logger.error("❌ فشل في إعداد الويب هوك")
    except Exception as e:
        logger.error(f"❌ خطأ في إعداد الويب هوك: {e}")

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    logger.info("🚀 بدء تشغيل موبي مع تقنية الويب هوك...")
    
    try:
        # إعداد الويب هوك
        setup_webhook()
        
        logger.info(f"✅ موبي جاهز - المطور: {DEVELOPER_USERNAME}")
        logger.info("🤖 البوت يعمل الآن مع الويب هوك!")
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")

if __name__ == "__main__":
    # تشغيل التطبيق على البورت المحدد من ريندر
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
