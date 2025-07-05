# -*- coding: utf-8 -*-
"""
components/enhanced_autocomplete_entry.py - النسخة المحسنة والمثبتة

إصلاح جميع المشاكل:
✅ إدارة محسنة للنوافذ المنبثقة
✅ معالجة أحداث مستقرة
✅ بحث مرن فعال
✅ أداء محسن
✅ سهولة الاستخدام
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Callable, Optional, Any, Union
import threading
import time
from dataclasses import dataclass
from enum import Enum


class SuggestionType(Enum):
    EXACT = "exact"
    STARTS_WITH = "starts"
    CONTAINS = "contains"
    FUZZY = "fuzzy"


@dataclass
class Suggestion:
    text: str
    type: SuggestionType = SuggestionType.EXACT
    score: float = 1.0
    description: str = ""


class EnhancedAutoCompleteEntry(ctk.CTkFrame):
    """حقل إدخال مع إكمال تلقائي محسن ومثبت"""

    def __init__(self,
                 parent,
                 values: List[str] = None,
                 placeholder: str = "ابحث...",
                 width: int = 300,
                 height: int = 35,
                 max_suggestions: int = 8,
                 min_chars: int = 1,
                 enable_fuzzy: bool = True,
                 fuzzy_threshold: float = 0.6,
                 on_select: Callable[[str], None] = None,
                 **kwargs):

        super().__init__(parent, width=width, height=height, **kwargs)

        # الإعدادات
        self.values = values or []
        self.placeholder = placeholder
        self.max_suggestions = max_suggestions
        self.min_chars = min_chars
        self.enable_fuzzy = enable_fuzzy
        self.fuzzy_threshold = fuzzy_threshold
        self.on_select = on_select

        # الحالة
        self.suggestions: List[Suggestion] = []
        self.selected_index = -1
        self.is_popup_open = False
        self.current_value = ""

        # متغيرات واجهة المستخدم
        self.text_var = tk.StringVar()
        self.text_var.trace_add('write', self._on_text_change)

        # بناء الواجهة
        self._build_ui()
        self._setup_bindings()

        # النافذة المنبثقة
        self.popup_window = None
        self.suggestion_widgets = []

        # تخزين مؤقت للبحث
        self._search_cache = {}
        self._last_search_time = 0
        self._search_delay = 0.3  # ثانية

    def _build_ui(self):
        """بناء واجهة المستخدم البسيطة"""
        # إطار البحث
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # أيقونة البحث
        self.search_icon = ctk.CTkLabel(
            self.search_frame,
            text="🔍",
            width=25,
            font=ctk.CTkFont(size=14)
        )
        self.search_icon.pack(side="left", padx=(5, 0))

        # حقل النص
        self.entry = ctk.CTkEntry(
            self.search_frame,
            textvariable=self.text_var,
            placeholder_text=self.placeholder,
            height=self.cget("height") - 4
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=5)

        # زر المسح
        self.clear_btn = ctk.CTkButton(
            self.search_frame,
            text="✕",
            width=25,
            height=25,
            command=self.clear,
            font=ctk.CTkFont(size=10)
        )
        # إخفاء زر المسح بداية

    def _setup_bindings(self):
        """إعداد أحداث لوحة المفاتيح والماوس"""
        # أحداث لوحة المفاتيح
        self.entry.bind('<Down>', self._on_arrow_down)
        self.entry.bind('<Up>', self._on_arrow_up)
        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind('<Escape>', self._on_escape)
        self.entry.bind('<Tab>', self._on_tab)

        # أحداث التركيز
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)

        # أحداث النقر
        self.entry.bind('<Button-1>', self._on_click)

    def _on_text_change(self, *args):
        """معالج تغيير النص المحسن"""
        text = self.text_var.get()
        self.current_value = text

        # إظهار/إخفاء زر المسح
        if text:
            self.clear_btn.pack(side="right", padx=(0, 5))
        else:
            self.clear_btn.pack_forget()

        # تحديث وقت البحث
        self._last_search_time = time.time()

        # جدولة البحث بتأخير
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)

        self._search_timer = self.after(
            int(self._search_delay * 1000),
            self._perform_search
        )

    def _perform_search(self):
        """تنفيذ البحث"""
        text = self.current_value.strip()

        if len(text) < self.min_chars:
            self._close_popup()
            return

        # استخدام التخزين المؤقت
        if text in self._search_cache:
            suggestions = self._search_cache[text]
        else:
            suggestions = self._generate_suggestions(text)
            # حفظ في التخزين المؤقت (مع حد أقصى)
            if len(self._search_cache) < 50:
                self._search_cache[text] = suggestions

        self.suggestions = suggestions

        if suggestions:
            self._show_popup()
        else:
            self._close_popup()

    def _generate_suggestions(self, query: str) -> List[Suggestion]:
        """إنشاء قائمة الاقتراحات"""
        suggestions = []
        query_lower = query.lower()

        for value in self.values:
            value_lower = value.lower()

            # تطابق تام
            if query_lower == value_lower:
                suggestions.append(Suggestion(
                    text=value,
                    type=SuggestionType.EXACT,
                    score=1.0
                ))
            # يبدأ بالاستعلام
            elif value_lower.startswith(query_lower):
                suggestions.append(Suggestion(
                    text=value,
                    type=SuggestionType.STARTS_WITH,
                    score=0.9
                ))
            # يحتوي على الاستعلام
            elif query_lower in value_lower:
                suggestions.append(Suggestion(
                    text=value,
                    type=SuggestionType.CONTAINS,
                    score=0.7
                ))
            # بحث مرن
            elif self.enable_fuzzy:
                similarity = self._calculate_similarity(query_lower, value_lower)
                if similarity >= self.fuzzy_threshold:
                    suggestions.append(Suggestion(
                        text=value,
                        type=SuggestionType.FUZZY,
                        score=similarity * 0.6
                    ))

        # ترتيب حسب النقاط
        suggestions.sort(key=lambda s: -s.score)
        return suggestions[:self.max_suggestions]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """حساب التشابه بين نصين (بخوارزمية بسيطة)"""
        if not text1 or not text2:
            return 0.0

        # حساب الأحرف المشتركة
        common = sum(1 for c in text1 if c in text2)
        max_len = max(len(text1), len(text2))

        return common / max_len if max_len > 0 else 0.0

    def _show_popup(self):
        """عرض النافذة المنبثقة"""
        if self.is_popup_open:
            self._update_popup()
            return

        try:
            # إنشاء النافذة المنبثقة
            self._create_popup()
            self.is_popup_open = True

        except Exception as e:
            print(f"خطأ في عرض النافذة المنبثقة: {e}")

    def _create_popup(self):
        """إنشاء النافذة المنبثقة"""
        # تدمير النافذة القديمة إن وجدت
        if self.popup_window:
            try:
                self.popup_window.destroy()
            except:
                pass

        # حساب الموقع
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()
        height = min(250, len(self.suggestions) * 35 + 10)

        # إنشاء النافذة
        self.popup_window = ctk.CTkToplevel(self)
        self.popup_window.wm_overrideredirect(True)
        self.popup_window.geometry(f"{width}x{height}+{x}+{y}")

        # إطار التمرير
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.popup_window,
            width=width-10,
            height=height-10
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._populate_suggestions()

    def _populate_suggestions(self):
        """ملء الاقتراحات"""
        # مسح الاقتراحات السابقة
        for widget in self.suggestion_widgets:
            try:
                widget.destroy()
            except:
                pass

        self.suggestion_widgets.clear()

        # إضافة الاقتراحات الجديدة
        for i, suggestion in enumerate(self.suggestions):
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=suggestion.text,
                height=30,
                anchor="w",
                command=lambda s=suggestion: self._select_suggestion(s)
            )
            btn.pack(fill="x", pady=1)

            # ربط أحداث الماوس
            btn.bind('<Enter>', lambda e, idx=i: self._highlight_suggestion(idx))

            self.suggestion_widgets.append(btn)

    def _update_popup(self):
        """تحديث محتوى النافذة المنبثقة"""
        if self.popup_window and self.popup_window.winfo_exists():
            self._populate_suggestions()

    def _close_popup(self):
        """إغلاق النافذة المنبثقة"""
        if self.popup_window:
            try:
                self.popup_window.destroy()
            except:
                pass
            finally:
                self.popup_window = None

        self.is_popup_open = False
        self.selected_index = -1

    def _select_suggestion(self, suggestion: Suggestion):
        """اختيار اقتراح"""
        self.text_var.set(suggestion.text)
        self.current_value = suggestion.text
        self._close_popup()

        # استدعاء callback
        if self.on_select:
            try:
                self.on_select(suggestion.text)
            except Exception as e:
                print(f"خطأ في callback: {e}")

    def _highlight_suggestion(self, index: int):
        """تمييز اقتراح"""
        self.selected_index = index

        # إزالة التمييز من جميع الأزرار
        for btn in self.suggestion_widgets:
            btn.configure(fg_color=["gray75", "gray25"])

        # تمييز الزر المحدد
        if 0 <= index < len(self.suggestion_widgets):
            self.suggestion_widgets[index].configure(fg_color=["gray65", "gray35"])

    # معالجات الأحداث
    def _on_arrow_down(self, event):
        """السهم لأسفل"""
        if not self.is_popup_open or not self.suggestions:
            return

        if self.selected_index < len(self.suggestions) - 1:
            self.selected_index += 1
        else:
            self.selected_index = 0

        self._highlight_suggestion(self.selected_index)
        return "break"

    def _on_arrow_up(self, event):
        """السهم لأعلى"""
        if not self.is_popup_open or not self.suggestions:
            return

        if self.selected_index > 0:
            self.selected_index -= 1
        else:
            self.selected_index = len(self.suggestions) - 1

        self._highlight_suggestion(self.selected_index)
        return "break"

    def _on_enter(self, event):
        """مفتاح Enter"""
        if self.is_popup_open and 0 <= self.selected_index < len(self.suggestions):
            self._select_suggestion(self.suggestions[self.selected_index])
        return "break"

    def _on_escape(self, event):
        """مفتاح Escape"""
        if self.is_popup_open:
            self._close_popup()
        else:
            self.clear()
        return "break"

    def _on_tab(self, event):
        """مفتاح Tab"""
        if self.is_popup_open and 0 <= self.selected_index < len(self.suggestions):
            self._select_suggestion(self.suggestions[self.selected_index])
            return "break"

    def _on_focus_in(self, event):
        """التركيز على الحقل"""
        if self.current_value and len(self.current_value) >= self.min_chars:
            self._perform_search()

    def _on_focus_out(self, event):
        """فقدان التركيز"""
        # تأخير قصير لإتاحة النقر على الاقتراحات
        self.after(100, self._check_focus_out)

    def _check_focus_out(self):
        """فحص فقدان التركيز الفعلي"""
        try:
            focused = self.focus_get()
            if not focused or focused not in [self.entry] + self.suggestion_widgets:
                self._close_popup()
        except:
            self._close_popup()

    def _on_click(self, event):
        """النقر على حقل النص"""
        if self.current_value and len(self.current_value) >= self.min_chars:
            self._perform_search()

    # الواجهة العامة
    def get(self) -> str:
        """الحصول على القيمة"""
        return self.current_value

    def set(self, value: str):
        """تعيين قيمة"""
        self.text_var.set(value)
        self.current_value = value

    def clear(self):
        """مسح المحتوى"""
        self.text_var.set("")
        self.current_value = ""
        self._close_popup()

    def set_values(self, values: List[str]):
        """تحديث قائمة القيم"""
        self.values = values
        self._search_cache.clear()  # مسح التخزين المؤقت

    def add_value(self, value: str):
        """إضافة قيمة جديدة"""
        if value and value not in self.values:
            self.values.append(value)
            self._search_cache.clear()

    def focus_set(self):
        """التركيز على الحقل"""
        self.entry.focus_set()


# مثال للاختبار
if __name__ == "__main__":
    import customtkinter as ctk

    class TestApp:
        def __init__(self):
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")

            self.root = ctk.CTk()
            self.root.title("Enhanced AutoComplete Entry - Test")
            self.root.geometry("600x400")

            # بيانات تجريبية
            self.test_values = [
                "القاهرة", "الإسكندرية", "الجيزة", "شرم الشيخ", "الغردقة",
                "أسوان", "الأقصر", "مرسى مطروح", "طابا", "دهب",
                "Cairo", "Alexandria", "Giza", "Sharm El Sheikh", "Hurghada",
                "Aswan", "Luxor", "Marsa Matrouh", "Taba", "Dahab",
                "New York", "Los Angeles", "Chicago", "Houston",
                "London", "Paris", "Berlin", "Rome", "Madrid"
            ]

            self.setup_ui()

        def setup_ui(self):
            """إعداد واجهة الاختبار"""
            # العنوان
            title = ctk.CTkLabel(
                self.root,
                text="🔍 Enhanced AutoComplete Entry",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)

            # وصف التحسينات
            improvements = """
✅ أداء محسن ومستقر
✅ بحث مرن فعال
✅ واجهة مستخدم سلسة
✅ معالجة أحداث محسنة
✅ تخزين مؤقت ذكي
            """

            desc_label = ctk.CTkLabel(
                self.root,
                text=improvements,
                font=ctk.CTkFont(size=12),
                justify="left"
            )
            desc_label.pack(pady=10)

            # حقل الاختبار الأول - بحث عادي
            label1 = ctk.CTkLabel(
                self.root,
                text="🌍 بحث المدن (بحث عادي):",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label1.pack(pady=(20, 5))

            self.autocomplete1 = EnhancedAutoCompleteEntry(
                self.root,
                values=self.test_values,
                placeholder="ابحث عن مدينة...",
                width=500,
                enable_fuzzy=False,
                on_select=self.on_select1
            )
            self.autocomplete1.pack(pady=5)

            # حقل الاختبار الثاني - بحث مرن
            label2 = ctk.CTkLabel(
                self.root,
                text="🔍 بحث مرن (جرب: Cair أو قاهر):",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label2.pack(pady=(20, 5))

            self.autocomplete2 = EnhancedAutoCompleteEntry(
                self.root,
                values=self.test_values,
                placeholder="البحث المرن...",
                width=500,
                enable_fuzzy=True,
                fuzzy_threshold=0.5,
                on_select=self.on_select2
            )
            self.autocomplete2.pack(pady=5)

            # عرض النتائج
            self.result_label = ctk.CTkLabel(
                self.root,
                text="🎯 لم يتم الاختيار بعد",
                font=ctk.CTkFont(size=16)
            )
            self.result_label.pack(pady=20)

            # أزرار التحكم
            controls_frame = ctk.CTkFrame(self.root)
            controls_frame.pack(pady=20)

            clear_btn = ctk.CTkButton(
                controls_frame,
                text="🗑️ مسح الكل",
                command=self.clear_all,
                width=120
            )
            clear_btn.pack(side="left", padx=5)

            add_btn = ctk.CTkButton(
                controls_frame,
                text="➕ إضافة عنصر",
                command=self.add_item,
                width=120
            )
            add_btn.pack(side="left", padx=5)

        def on_select1(self, value):
            """معالج الاختيار الأول"""
            self.result_label.configure(
                text=f"🌍 اختيار عادي: {value}",
                text_color="green"
            )

        def on_select2(self, value):
            """معالج الاختيار المرن"""
            self.result_label.configure(
                text=f"🔍 اختيار مرن: {value}",
                text_color="blue"
            )

        def clear_all(self):
            """مسح جميع الحقول"""
            self.autocomplete1.clear()
            self.autocomplete2.clear()
            self.result_label.configure(
                text="🗑️ تم مسح جميع الحقول",
                text_color="orange"
            )

        def add_item(self):
            """إضافة عنصر جديد"""
            import random
            new_items = ["طوكيو", "سيدني", "تورونتو", "دبي", "الكويت"]
            new_item = random.choice(new_items)

            self.autocomplete1.add_value(new_item)
            self.autocomplete2.add_value(new_item)

            self.result_label.configure(
                text=f"➕ تم إضافة: {new_item}",
                text_color="purple"
            )

        def run(self):
            """تشغيل التطبيق"""
            self.root.mainloop()

    # تشغيل الاختبار
    app = TestApp()
    app.run()
