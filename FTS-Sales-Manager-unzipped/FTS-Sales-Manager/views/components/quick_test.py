#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع للقائمة المحسنة - لحل مشكلة الإغلاق السريع
"""

import customtkinter as ctk
from enhanced_searchable_combobox import EnhancedSearchableComboBox

def test_fixed_dropdown():
    """اختبار سريع للقائمة المصححة"""

    app = ctk.CTk()
    app.title("🔧 اختبار القائمة المصححة - لا تختفي بسرعة")
    app.geometry("600x500")

    # تعليمات
    instructions = ctk.CTkLabel(
        app,
        text="""🔧 اختبار حل مشكلة الإغلاق السريع:

1. اضغط على زر ▼ - يجب أن تفتح القائمة وتبقى مفتوحة
2. حرك الماوس فوق الخيارات - يجب أن تبقى القائمة مفتوحة
3. انقر على خيار - يجب أن يتم اختياره
4. راقب رسائل التشخيص في Console

إذا كانت القائمة لا تزال تختفي، سنحتاج لمزيد من التحسينات.""",
        font=ctk.CTkFont(size=12),
        justify="left"
    )
    instructions.pack(pady=20, padx=20)

    # القائمة المحسنة
    test_values = [
        "Cairo", "Alexandria", "Luxor", "Aswan",
        "Hurghada", "Sharm El Sheikh", "Giza"
    ]

    combo = EnhancedSearchableComboBox(
        app,
        values=test_values,
        placeholder="اختبر هنا - يجب ألا تختفي بسرعة",
        width=500,
        height=40,
        debug_mode=True,  # مهم للتشخيص
        on_select=lambda v: print(f"🎯 تم اختيار: {v}")
    )
    combo.pack(pady=30)

    # زر اختبار يدوي
    def manual_test():
        print("\n🧪 اختبار يدوي للقائمة:")
        combo._show_all_results()
        combo._open_dropdown()
        print("📝 تم فتح القائمة يدوياً - يجب أن تبقى مفتوحة")

    test_btn = ctk.CTkButton(
        app,
        text="🧪 فتح القائمة يدوياً",
        command=manual_test,
        height=40
    )
    test_btn.pack(pady=10)

    # نصائح
    tips = ctk.CTkLabel(
        app,
        text="""💡 نصائح الاختبار:
• إذا اختفت القائمة بسرعة، راجع رسائل Console
• ابحث عن رسائل "❌ إغلاق القائمة" في Console
• جرب النقر ببطء على الخيارات
• لا تحرك الماوس بسرعة خارج القائمة""",
        font=ctk.CTkFont(size=11),
        justify="left"
    )
    tips.pack(pady=20)

    print("🚀 تشغيل اختبار القائمة المصححة")
    print("📋 راقب هذه النافذة للرسائل التشخيصية")

    app.mainloop()

if __name__ == "__main__":
    test_fixed_dropdown()