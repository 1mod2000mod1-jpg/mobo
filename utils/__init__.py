#!/usr/bin/env python3
"""
أدوات مساعدة لموبي
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger("موبي_الأدوات")

def format_time(dt):
    """تنسيق الوقت بشكل مقروء"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def time_ago(dt):
    """حساب الوقت المنقضي منذ تاريخ معين"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"منذ {diff.days} يوم"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"منذ {hours} ساعة"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"منذ {minutes} دقيقة"
    else:
        return "الآن"

def safe_int(value, default=0):
    """تحويل قيمة إلى عدد صحيح بشكل آمن"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def truncate_text(text, max_length=100):
    """تقصير النص مع إضافة نقاط إذا كان طويلاً"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_arabic(text):
    """التحقق إذا كان النص يحتوي على أحرف عربية"""
    arabic_range = range(0x0600, 0x06FF)
    return any(ord(char) in arabic_range for char in text)

def get_file_size(size_in_bytes):
    """تحويل حجم الملف إلى صيغة مقروءة"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"
