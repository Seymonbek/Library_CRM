"""
Text formatting utilities.

HTML parse_mode ishlatganda foydalanuvchi kiritgan ma'lumotlarda
<, >, & belgilari bo'lsa xabar yuborilmaydi yoki buziladi.
Shuning uchun barcha foydalanuvchi inputlarini escape qilamiz.
"""

from html import escape


def safe(text: str | None) -> str:
    """
    HTML maxsus belgilarni escape qilish.
    Foydalanuvchi kiritgan har qanday textga qo'llaniladi.

    Misol:
        safe("<script>alert(1)</script>")
        → "&lt;script&gt;alert(1)&lt;/script&gt;"
    """
    if text is None:
        return ""
    return escape(str(text))


def format_loan_status(status: str) -> str:
    """Ijara statusini emoji bilan formatlash."""
    status_map = {
        "pending": "🕐 Kutilmoqda",
        "borrowed": "📖 Ijarada",
        "returned": "✅ Qaytarildi",
        "overdue": "⚠️ Muddati o'tdi",
        "lost": "❌ Yo'qolgan",
    }
    return status_map.get(status, status)


def format_fine_reason(reason: str) -> str:
    """Jarima sababini o'zbekchaga formatlash."""
    reason_map = {
        "late_return": "Kech qaytarish",
        "book_damaged": "Kitob shikastlangan",
        "book_lost": "Kitob yo'qolgan",
    }
    return reason_map.get(reason, reason)
