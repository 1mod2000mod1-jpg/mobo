import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_url: str):
        self.API_URL = api_url

    def generate_response(self, message: str, user_id: int, conversation_history: list = None) -> Optional[str]:
        """
        توليد رد من الخدمة الذكية
        """
        try:
            payload = {
                "text": message,
                "user_id": str(user_id),
                "conversation_history": conversation_history or []
            }
            
            response = requests.post(
                self.API_URL,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "عذراً، لم أستطع فهم ذلك. يمكنك إعادة صياغة سؤالك.")
            else:
                logger.error(f"❌ خطأ في API: {response.status_code}")
                return "عذراً، حدث خطأ في الخدمة. يرجى المحاولة لاحقاً."
                
        except requests.exceptions.Timeout:
            logger.error("⏰ انتهت المهلة في الاتصال بالخدمة الذكية")
            return "عذراً، الخدمة مشغولة حالياً. يرجى المحاولة لاحقاً."
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطأ في الاتصال بالخدمة الذكية: {e}")
            return "عذراً، لا يمكن الوصول للخدمة حالياً. يرجى المحاولة لاحقاً."
        
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع في الخدمة الذكية: {e}")
            return "عذراً، حدث خطأ غير متوقع. يرجى المحاولة لاحقاً."

# استخدام الخدمة
AI_SERVICE = AIService(API_URL="https://your-ai-api.com/chat")
