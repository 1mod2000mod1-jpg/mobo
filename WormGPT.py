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
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة التحديث: {e}")

def handle_callback_query(call):
    """
    معالجة استعلامات الـ callback
    """
    try:
        data = call['data']
        
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
        user_info = {
            'username': message['from'].get('username'),
            'first_name': message['from'].get('first_name', 'مستخدم'),
            'last_name': message['from'].get('last_name', ''),
            'messages_count': memory.user_stats.get(user_id, {}).get('messages_count', 0) + 1
        }
        memory.save_user_stats(user_id, user_info)
        
        # حفظ المحادثة
        memory.add_conversation(user_id, 'user', text)
        
        # توليد الرد من الذكاء الاصطناعي
        conversation_history = memory.get_user_conversation(user_id)
        # response = AI_SERVICE.generate_response(text, user_id, conversation_history)
        response = f"تم استلام رسالتك: {text}"  # مؤقتاً
        
        # إرسال الرد
        bot_send_message(chat_id, response)
        
        # حفظ رد البوت
        memory.add_conversation(user_id, 'assistant', response)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة العادية: {e}")

def handle_points_input(user_id, text, chat_id):
    """معالجة إدخال النقاط"""
    try:
        if user_id in points_state:
            action_data = points_state[user_id]
            target_user_id = action_data['user_id']
            action = action_data['action']
            
            try:
                points = int(text)
                if points <= 0:
                    bot_send_message(chat_id, "❌ يرجى إدخال عدد صحيح موجب!")
                    return
                
                current_points = memory.user_stats.get(target_user_id, {}).get('points', 0)
                
                if action == 'add':
                    new_points = current_points + points
                    memory.update_user_points(target_user_id, new_points)
                    bot_send_message(chat_id, f"✅ تم إضافة {points} نقطة للمستخدم. المجموع: {new_points}")
                elif action == 'remove':
                    new_points = max(0, current_points - points)
                    memory.update_user_points(target_user_id, new_points)
                    bot_send_message(chat_id, f"✅ تم نزع {points} نقطة من المستخدم. المجموع: {new_points}")
                
                # مسح الحالة
                del points_state[user_id]
                
            except ValueError:
                bot_send_message(chat_id, "❌ يرجى إدخال عدد صحيح فقط!")
                
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة النقاط: {e}")

# دوال الويب هوك المحولة
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

def make_user_admin_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.add_admin(user_id, user_info.get('username', ''), user_info.get('first_name', '')):
            bot_answer_callback_query(call['id'], f"✅ تم ترقية {user_info.get('first_name', 'المستخدم')} إلى مشرف!")
            show_admins_management_webhook(call)
        else:
            bot_answer_callback_query(call['id'], "❌ المستخدم مشرف بالفعل!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في ترقية المشرف: {e}")

def remove_user_admin_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.remove_admin(user_id):
            bot_answer_callback_query(call['id'], f"✅ تم إزالة {user_info.get('first_name', 'المستخدم')} من المشرفين!")
            show_admins_management_webhook(call)
        else:
            bot_answer_callback_query(call['id'], "❌ لا يمكن إزالة هذا المشرف!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في إزالة المشرف: {e}")

def ban_user_action_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.ban_user(user_id, user_info.get('username', ''), user_info.get('first_name', '')):
            bot_answer_callback_query(call['id'], f"✅ تم حظر {user_info.get('first_name', 'المستخدم')}!")
            show_ban_management_webhook(call)
        else:
            bot_answer_callback_query(call['id'], "❌ لا يمكن حظر هذا المستخدم!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في حظر المستخدم: {e}")

def unban_user_action_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        user_info = memory.user_stats.get(user_id, {})
        
        if memory.unban_user(user_id):
            bot_answer_callback_query(call['id'], f"✅ تم إلغاء حظر {user_info.get('first_name', 'المستخدم')}!")
            show_ban_management_webhook(call)
        else:
            bot_answer_callback_query(call['id'], "❌ المستخدم غير محظور!", show_alert=True)
    except Exception as e:
        logger.error(f"❌ خطأ في إلغاء الحظر: {e}")

def add_points_action_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        points_state[call['from']['id']] = {'action': 'add', 'user_id': user_id}
        bot_send_message(call['from']['id'], "🎯 أرسل عدد النقاط التي تريد إضافتها:")
        bot_answer_callback_query(call['id'], "➕ إضافة نقاط")
    except Exception as e:
        logger.error(f"❌ خطأ في إضافة النقاط: {e}")

def remove_points_action_webhook(call):
    try:
        user_id = int(call['data'].split("_")[2])
        points_state[call['from']['id']] = {'action': 'remove', 'user_id': user_id}
        bot_send_message(call['from']['id'], "🎯 أرسل عدد النقاط التي تريد نزعها:")
        bot_answer_callback_query(call['id'], "➖ نزع نقاط")
    except Exception as e:
        logger.error(f"❌ خطأ في نزع النقاط: {e}")

def handle_welcome_settings_webhook(call):
    show_welcome_settings_webhook(call)

def show_admin_users_webhook(call):
    """عرض إدارة المستخدمين للمشرفين"""
    try:
        users_text = "👥 **إدارة المستخدمين:**\n\n"
        users = memory.get_user_stats()
        
        keyboard = {
            'inline_keyboard': [
                [{'text': '📊 عرض الإحصائيات', 'callback_data': 'view_stats'}],
                [{'text': '🕒 الرسائل الأخيرة', 'callback_data': 'view_recent_all'}],
                [{'text': '👑 إدارة المشرفين', 'callback_data': 'manage_admins'}],
                [{'text': '🚫 إدارة الحظر', 'callback_data': 'manage_bans'}],
                [{'text': '🔙 رجوع', 'callback_data': 'admin_panel'}]
            ]
        }
        
        bot_edit_message_text(users_text, call['message']['chat']['id'], call['message']['message_id'],
                            reply_markup=keyboard, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ خطأ في عرض إدارة المستخدمين: {e}")

# دوال إنشاء لوحات المفاتيح
def create_admin_panel():
    """إنشاء لوحة تحكم المشرفين"""
    return {
        'inline_keyboard': [
            [{'text': '👥 إدارة المستخدمين', 'callback_data': 'admin_users'}],
            [{'text': '⚙️ الإعدادات', 'callback_data': 'admin_settings'}],
            [{'text': '📊 الإحصائيات', 'callback_data': 'view_stats'}]
        ]
    }

def create_users_keyboard(users, prefix):
    """إنشاء لوحة مفاتيح للمستخدمين"""
    keyboard = {'inline_keyboard': []}
    row = []
    
    for user_id, user_info in list(users.items())[:6]:
        recent = memory.get_recent_messages(user_id, 10)
        button_text = f"{user_info['first_name']} ({len(recent)})"
        row.append({'text': button_text, 'callback_data': f'{prefix}_{user_id}'})
        
        if len(row) == 2:
            keyboard['inline_keyboard'].append(row)
            row = []
    
    if row:
        keyboard['inline_keyboard'].append(row)
    
    keyboard['inline_keyboard'].append([{'text': '🔙 رجوع', 'callback_data': 'admin_users'}])
    return keyboard

def create_back_button(callback_data="admin_panel"):
    """إنشاء زر الرجوع"""
    return {
        'inline_keyboard': [
            [{'text': '🔙 رجوع', 'callback_data': callback_data}]
        ]
    }

# دوال العرض
def show_admins_management_webhook(call):
    """عرض إدارة المشرفين"""
    admins_text = "👑 **إدارة المشرفين:**\n\n"
    admins = memory.admins
    
    keyboard = {'inline_keyboard': []}
    
    for admin_id, admin_info in admins.items():
        button_text = f"👤 {admin_info['first_name']}"
        keyboard['inline_keyboard'].append([
            {'text': button_text, 'callback_data': f'view_admin_{admin_id}'},
            {'text': '❌ إزالة', 'callback_data': f'remove_admin_{admin_id}'}
        ])
    
    keyboard['inline_keyboard'].append([{'text': '🔙 رجوع', 'callback_data': 'admin_users'}])
    
    bot_edit_message_text(admins_text, call['message']['chat']['id'], call['message']['message_id'],
                         reply_markup=keyboard, parse_mode='Markdown')

def show_ban_management_webhook(call):
    """عرض إدارة الحظر"""
    bans_text = "🚫 **إدارة المستخدمين المحظورين:**\n\n"
    banned_users = memory.banned_users
    
    keyboard = {'inline_keyboard': []}
    
    for user_id, user_info in banned_users.items():
        button_text = f"👤 {user_info['first_name']}"
        keyboard['inline_keyboard'].append([
            {'text': button_text, 'callback_data': f'view_user_{user_id}'},
            {'text': '✅ فك الحظر', 'callback_data': f'unban_user_{user_id}'}
        ])
    
    keyboard['inline_keyboard'].append([{'text': '🔙 رجوع', 'callback_data': 'admin_users'}])
    
    bot_edit_message_text(bans_text, call['message']['chat']['id'], call['message']['message_id'],
                         reply_markup=keyboard, parse_mode='Markdown')

def show_welcome_settings_webhook(call):
    """عرض إعدادات الترحيب"""
    welcome_text = "🎉 **إعدادات رسالة الترحيب:**\n\n"
    welcome_text += "يمكنك تخصيص رسالة الترحيب من هنا."
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '✏️ تعديل الترحيب', 'callback_data': 'edit_welcome'}],
            [{'text': '👀 معاينة الترحيب', 'callback_data': 'preview_welcome'}],
            [{'text': '🔙 رجوع', 'callback_data': 'admin_settings'}]
        ]
    }
    
    bot_edit_message_text(welcome_text, call['message']['chat']['id'], call['message']['message_id'],
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
            logger.info("✅ تم إعداد الويب هوك بنجاح!")
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
