from flask import Flask, request, jsonify
import threading
from datetime import datetime
import requests
import logging

# تهيئة تطبيق Flask
app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            # إضافة الدالة المناسبة هنا
            pass
            
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
        
        # معالجة إضافة النقاط
        if user_id in points_state:
            handle_points_input(user_id, text, chat_id)
            return
            
        # باقي معالجة الرسائل العادية
        # ... (أضف منطق معالجة الرسائل هنا)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}")

# النسخ المعدلة من الدوال لتتوافق مع الويب هوك
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
            keyboard = create_inline_keyboard(users, "view_recent")
            
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
            
            keyboard = create_back_button()
        
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

# دوال مساعدة للتفاعل مع API تليجرام
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

# دوال إنشاء لوحات المفاتيح (احتفظ بالدوال الأصلية)
def create_admin_panel():
    """إنشاء لوحة تحكم المشرفين"""
    # ... (نفس الدالة الأصلية)

def create_inline_keyboard(users, prefix):
    """إنشاء لوحة مفاتيح للمستخدمين"""
    # ... (نفس الدالة الأصلية)

def create_back_button():
    """إنشاء زر الرجوع"""
    # ... (نفس الدالة الأصلية)

# دوال العرض (احتفظ بنفس المنطق)
def show_admins_management_webhook(call):
    """عرض إدارة المشرفين"""
    # ... (نفس المنطق الأصلي)

def show_ban_management_webhook(call):
    """عرض إدارة الحظر"""
    # ... (نفس المنطق الأصلي)

def show_welcome_settings_webhook(call):
    """عرض إعدادات الترحيب"""
    # ... (نفس المنطق الأصلي)

def handle_points_input(user_id, text, chat_id):
    """معالجة إدخال النقاط"""
    # ... (نفس المنطق الأصلي)

# تهيئة المتغيرات
points_state = {}
memory = None  # سيتم تهيئتها من ملفك الرئيسي

def setup_webhook():
    """إعداد الويب هوك في تليجرام"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"  # URL التطبيق على ريندر
    
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
        
        # اختبار النظام
        try:
            test_url = f"{AIService.API_URL}?text=test"
            response = requests.get(test_url, timeout=10)
            logger.info(f"✅ النظام يعمل: {response.status_code}")
        except Exception as api_error:
            logger.warning(f"⚠️ النظام غير متاح: {api_error}")
        
        logger.info(f"✅ موبي جاهز - المطور: {DEVELOPER_USERNAME}")
        logger.info("🤖 البوت يعمل الآن مع الويب هوك!")
        
        # لا حاجة لـ infinity_polling في الويب هوك
        # التطبيق سيعمل على البورت المحدد من ريندر
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")

if __name__ == "__main__":
    # تشغيل التطبيق على البورت المحدد من ريندر
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
