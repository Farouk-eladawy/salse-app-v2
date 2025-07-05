# -*- coding: utf-8 -*-
"""
components/enhanced_searchable_combobox.py - النسخة المبسطة والمثبتة

الإصلاحات المطبقة:
✅ كود مبسط وأكثر استقراراً
✅ معالجة أحداث محسنة
✅ بحث مرن فعال
✅ أداء محسن
✅ سهولة في الاستخدام
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Callable, Optional, Any
import threading
import time


class EnhancedSearchableComboBox(ctk.CTkFrame):
    """قائمة منسدلة مدعومة بالبحث - نسخة مبسطة ومحسنة"""

    def __init__(self,
                 parent,
                 values: List[str] = None,
                 placeholder: str = "اكتب للبحث...",
                 width: int = 300,
                 height: int = 35,
                 max_results: int = 10,
                 enable_fuzzy: bool = True,
                 fuzzy_threshold: float = 0.6,
                 on_select: Callable[[str], None] = None,
                 **kwargs):

        super().__init__(parent, width=width, height=height, **kwargs)

        # الإعدادات
        self.values = values or []
        self.placeholder = placeholder
        self.max_results = max_results
        self.enable_fuzzy = enable_fuzzy
        self.fuzzy_threshold = fuzzy_threshold
        self.on_select = on_select

        # الحالة
        self.filtered_values = self.values.copy()
        self.selected_value = ""
        self.selected_index = -1
        self.is_dropdown_open = False

        # متغيرات واجهة المستخدم
        self.text_var = tk.StringVar()
        self.text_var.trace_add('write', self._on_text_change)

        # بناء الواجهة
        self._build_ui()
        self._setup_bindings()

        # النافذة المنبثقة
        self.dropdown_window = None
        self.option_buttons = []

        # تخزين مؤقت للبحث
        self._search_cache = {}

    def _build_ui(self):
        """بناء واجهة مستخدم بسيطة وفعالة"""
        # الإطار الرئيسي
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # حقل النص
        self.entry = ctk.CTkEntry(
            self.main_frame,
            textvariable=self.text_var,
            placeholder_text=self.placeholder,
            height=self.cget("height") - 4
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(2, 1))

        # زر القائمة المنسدلة
        self.dropdown_btn = ctk.CTkButton(
            self.main_frame,
            text="▼",
            width=30,
            height=self.cget("height") - 4,
            command=self._toggle_dropdown
        )
        self.dropdown_btn.pack(side="right", padx=(1, 2))

    def _setup_bindings(self):
        """إعداد أحداث بسيطة ومستقرة"""
        # أحداث لوحة المفاتيح
        self.entry.bind('<Down>', self._on_arrow_down)
        self.entry.bind('<Up>', self._on_arrow_up)
        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind('<Escape>', self._on_escape)
        self.entry.bind('<Tab>', self._on_tab)

        # أحداث التركيز - مبسطة
        self.entry.bind('<FocusIn>', self._on_focus_in)

        # فحص دوري للنقر خارج المكون
        self._check_outside_click()

    def _check_outside_click(self):
        """فحص دوري للنقر خارج المكون"""
        def check():
            try:
                if self.is_dropdown_open:
                    focused = self.focus_get()
                    if not self._is_focus_inside(focused):
                        self._close_dropdown()
            except:
                pass

            # إعادة جدولة الفحص
            self.after(200, check)

        self.after(200, check)

    def _is_focus_inside(self, widget) -> bool:
        """فحص إذا كان التركيز داخل المكون"""
        if not widget:
            return False

        # فحص العناصر الرئيسية
        main_widgets = [self, self.entry, self.dropdown_btn, self.main_frame]
        if widget in main_widgets:
            return True

        # فحص عناصر القائمة المنسدلة
        if widget in self.option_buttons:
            return True

        return False

    def _on_text_change(self, *args):
        """معالج تغيير النص - مبسط وفعال"""
        text = self.text_var.get()

        # البحث الفوري
        self._perform_search(text)

    def _perform_search(self, query: str):
        """تنفيذ البحث المحسن"""
        if not query:
            self.filtered_values = self.values.copy()
        else:
            # استخدام التخزين المؤقت
            if query in self._search_cache:
                self.filtered_values = self._search_cache[query]
            else:
                self.filtered_values = self._search_values(query)
                # حفظ في التخزين المؤقت
                if len(self._search_cache) < 50:
                    self._search_cache[query] = self.filtered_values.copy()

        # تحديث القائمة المنسدلة
        if self.is_dropdown_open:
            self._update_dropdown()
        elif self.filtered_values and query:
            self._open_dropdown()

    def _search_values(self, query: str) -> List[str]:
        """البحث في القيم مع دعم البحث المرن"""
        if not query:
            return self.values.copy()

        query_lower = query.lower()
        results = []

        # البحث بالأولوية
        for value in self.values:
            value_lower = value.lower()

            # تطابق تام
            if query_lower == value_lower:
                results.append((value, 1.0))
            # يبدأ بالاستعلام
            elif value_lower.startswith(query_lower):
                results.append((value, 0.9))
            # يحتوي على الاستعلام
            elif query_lower in value_lower:
                results.append((value, 0.7))
            # بحث مرن
            elif self.enable_fuzzy:
                similarity = self._calculate_similarity(query_lower, value_lower)
                if similarity >= self.fuzzy_threshold:
                    results.append((value, similarity * 0.6))

        # ترتيب حسب النقاط
        results.sort(key=lambda x: -x[1])

        # إرجاع النتائج (بدون النقاط)
        return [value for value, score in results[:self.max_results]]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """حساب التشابه بخوارزمية بسيطة وسريعة"""
        if not text1 or not text2:
            return 0.0

        # نسبة الأحرف المشتركة
        common_chars = sum(1 for c in text1 if c in text2)
        max_len = max(len(text1), len(text2))

        return common_chars / max_len if max_len > 0 else 0.0

    def _toggle_dropdown(self):
        """تبديل حالة القائمة المنسدلة"""
        if self.is_dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """فتح القائمة المنسدلة"""
        if self.is_dropdown_open:
            return

        try:
            self._create_dropdown()
            self.is_dropdown_open = True
            self.dropdown_btn.configure(text="▲")

        except Exception as e:
            print(f"خطأ في فتح القائمة: {e}")

    def _create_dropdown(self):
        """إنشاء القائمة المنسدلة"""
        # تدمير النافذة القديمة
        if self.dropdown_window:
            try:
                self.dropdown_window.destroy()
            except:
                pass

        # حساب الموقع والحجم
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()
        height = min(200, len(self.filtered_values) * 35 + 10)

        # إنشاء النافذة
        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.geometry(f"{width}x{height}+{x}+{y}")

        # إطار القائمة
        self.list_frame = ctk.CTkScrollableFrame(
            self.dropdown_window,
            width=width-10,
            height=height-10
        )
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self._populate_dropdown()

    def _populate_dropdown(self):
        """ملء القائمة المنسدلة"""
        # مسح الأزرار السابقة
        for btn in self.option_buttons:
            try:
                btn.destroy()
            except:
                pass

        self.option_buttons.clear()

        # إضافة الخيارات الجديدة
        for i, value in enumerate(self.filtered_values):
            btn = ctk.CTkButton(
                self.list_frame,
                text=value,
                height=30,
                anchor="w",
                command=lambda v=value: self._select_value(v)
            )
            btn.pack(fill="x", pady=1)

            # ربط أحداث الماوس
            btn.bind('<Enter>', lambda e, idx=i: self._highlight_option(idx))

            self.option_buttons.append(btn)

    def _update_dropdown(self):
        """تحديث محتوى القائمة المنسدلة"""
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self._populate_dropdown()

    def _close_dropdown(self):
        """إغلاق القائمة المنسدلة"""
        if self.dropdown_window:
            try:
                self.dropdown_window.destroy()
            except:
                pass
            finally:
                self.dropdown_window = None

        self.is_dropdown_open = False
        self.selected_index = -1
        self.dropdown_btn.configure(text="▼")

    def _select_value(self, value: str):
        """اختيار قيمة"""
        self.selected_value = value
        self.text_var.set(value)
        self._close_dropdown()

        # استدعاء callback
        if self.on_select:
            try:
                self.on_select(value)
            except Exception as e:
                print(f"خطأ في callback: {e}")

    def _highlight_option(self, index: int):
        """تمييز خيار"""
        self.selected_index = index

        # إزالة التمييز من جميع الأزرار
        for btn in self.option_buttons:
            btn.configure(fg_color=["gray75", "gray25"])

        # تمييز الزر المحدد
        if 0 <= index < len(self.option_buttons):
            self.option_buttons[index].configure(fg_color=["gray65", "gray35"])

    # معالجات الأحداث
    def _on_arrow_down(self, event):
        """السهم لأسفل"""
        if not self.is_dropdown_open:
            self._open_dropdown()
            return "break"

        if self.option_buttons:
            if self.selected_index < len(self.option_buttons) - 1:
                self.selected_index += 1
            else:
                self.selected_index = 0

            self._highlight_option(self.selected_index)

        return "break"

    def _on_arrow_up(self, event):
        """السهم لأعلى"""
        if not self.is_dropdown_open:
            return "break"

        if self.option_buttons:
            if self.selected_index > 0:
                self.selected_index -= 1
            else:
                self.selected_index = len(self.option_buttons) - 1

            self._highlight_option(self.selected_index)

        return "break"

    def _on_enter(self, event):
        """مفتاح Enter"""
        if self.is_dropdown_open and 0 <= self.selected_index < len(self.filtered_values):
            self._select_value(self.filtered_values[self.selected_index])
        return "break"

    def _on_escape(self, event):
        """مفتاح Escape"""
        if self.is_dropdown_open:
            self._close_dropdown()
        else:
            self.clear()
        return "break"

    def _on_tab(self, event):
        """مفتاح Tab"""
        if self.is_dropdown_open and 0 <= self.selected_index < len(self.filtered_values):
            self._select_value(self.filtered_values[self.selected_index])
            return "break"

    def _on_focus_in(self, event):
        """التركيز على الحقل"""
        text = self.text_var.get()
        if text:
            self._perform_search(text)

    # الواجهة العامة
    def get(self) -> str:
        """الحصول على القيمة المحددة"""
        return self.selected_value

    def set(self, value: str):
        """تعيين قيمة"""
        if value in self.values:
            self.selected_value = value
            self.text_var.set(value)
        else:
            # إضافة القيمة إذا لم تكن موجودة
            self.add_value(value)
            self.selected_value = value
            self.text_var.set(value)

    def clear(self):
        """مسح القيمة"""
        self.selected_value = ""
        self.text_var.set("")
        self.filtered_values = self.values.copy()
        self._close_dropdown()

    def set_values(self, values: List[str]):
        """تحديث قائمة القيم"""
        self.values = values.copy()
        self.filtered_values = values.copy()
        self._search_cache.clear()

    def add_value(self, value: str):
        """إضافة قيمة جديدة"""
        if value and value not in self.values:
            self.values.append(value)
            self.filtered_values = self.values.copy()
            self._search_cache.clear()

    def remove_value(self, value: str):
        """حذف قيمة"""
        if value in self.values:
            self.values.remove(value)
            self.filtered_values = self.values.copy()
            self._search_cache.clear()

            if self.selected_value == value:
                self.clear()

    def is_valid_selection(self) -> bool:
        """التحقق من صحة الاختيار"""
        return self.selected_value in self.values

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
            self.root.title("Enhanced SearchableComboBox - Test")
            self.root.geometry("700x500")

            # بيانات تجريبية
            self.cities = [
                "القاهرة", "الإسكندرية", "الجيزة", "شرم الشيخ", "الغردقة",
                "أسوان", "الأقصر", "مرسى مطروح", "طابا", "دهب", "سفاجا",
                "Cairo", "Alexandria", "Giza", "Sharm El Sheikh", "Hurghada",
                "Aswan", "Luxor", "Marsa Matrouh", "Taba", "Dahab", "Safaga",
                "New York", "Los Angeles", "Chicago", "Houston", "Philadelphia",
                "London", "Paris", "Berlin", "Rome", "Madrid", "Barcelona",
                "Tokyo", "Sydney", "Toronto", "Dubai", "Kuwait", "Riyadh"
            ]

            self.setup_ui()

        def setup_ui(self):
            """إعداد واجهة الاختبار"""
            # العنوان
            title = ctk.CTkLabel(
                self.root,
                text="🔽 Enhanced SearchableComboBox",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title.pack(pady=20)

            # وصف التحسينات
            improvements = """
✅ كود مبسط ومستقر
✅ أداء محسن وسريع
✅ بحث مرن فعال
✅ واجهة سهلة الاستخدام
✅ معالجة أحداث محسنة
            """

            desc_label = ctk.CTkLabel(
                self.root,
                text=improvements,
                font=ctk.CTkFont(size=12),
                justify="left"
            )
            desc_label.pack(pady=10)

            # الاختبار الأول - قائمة المدن
            label1 = ctk.CTkLabel(
                self.root,
                text="🌍 اختيار المدينة:",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label1.pack(pady=(20, 5))

            self.combo1 = EnhancedSearchableComboBox(
                self.root,
                values=self.cities,
                placeholder="ابحث عن مدينة...",
                width=500,
                enable_fuzzy=True,
                on_select=self.on_city_select
            )
            self.combo1.pack(pady=5)

            # الاختبار الثاني - قائمة بدون بحث مرن
            label2 = ctk.CTkLabel(
                self.root,
                text="📋 بحث دقيق (بدون مرونة):",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label2.pack(pady=(20, 5))

            self.combo2 = EnhancedSearchableComboBox(
                self.root,
                values=self.cities[:10],  # قائمة أصغر
                placeholder="بحث دقيق فقط...",
                width=500,
                enable_fuzzy=False,
                on_select=self.on_exact_select
            )
            self.combo2.pack(pady=5)

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

            buttons = [
                ("🗑️ مسح الكل", self.clear_all),
                ("📊 عرض القيم", self.show_values),
                ("➕ إضافة مدينة", self.add_city),
                ("🔄 تحديث القوائم", self.refresh_lists),
                ("🧪 اختبار البحث", self.test_search)
            ]

            for i, (text, command) in enumerate(buttons):
                btn = ctk.CTkButton(
                    controls_frame,
                    text=text,
                    command=command,
                    width=140,
                    height=35
                )
                btn.grid(row=i//3, column=i%3, padx=5, pady=5)

        def on_city_select(self, value):
            """معالج اختيار المدينة"""
            self.result_label.configure(
                text=f"🌍 المدينة المختارة: {value}",
                text_color="green"
            )

        def on_exact_select(self, value):
            """معالج البحث الدقيق"""
            self.result_label.configure(
                text=f"📋 البحث الدقيق: {value}",
                text_color="blue"
            )

        def clear_all(self):
            """مسح جميع الاختيارات"""
            self.combo1.clear()
            self.combo2.clear()
            self.result_label.configure(
                text="🗑️ تم مسح جميع الاختيارات",
                text_color="orange"
            )

        def show_values(self):
            """عرض القيم المحددة"""
            value1 = self.combo1.get() or "غير محدد"
            value2 = self.combo2.get() or "غير محدد"

            self.result_label.configure(
                text=f"📊 القيم: مدن({value1}) | دقيق({value2})",
                text_color="purple"
            )

        def add_city(self):
            """إضافة مدينة جديدة"""
            import random
            new_cities = ["أبو ظبي", "الدوحة", "بيروت", "عمان", "الكويت", "المنامة"]
            new_city = random.choice(new_cities)

            self.combo1.add_value(new_city)
            self.combo2.add_value(new_city)

            self.result_label.configure(
                text=f"➕ تم إضافة: {new_city}",
                text_color="green"
            )

        def refresh_lists(self):
            """تحديث القوائم"""
            # إضافة بعض المدن الجديدة
            additional_cities = ["أغادير", "فاس", "الرباط", "الدار البيضاء"]

            current_cities = self.combo1.values + additional_cities
            self.combo1.set_values(list(set(current_cities)))
            self.combo2.set_values(current_cities[:15])

            self.result_label.configure(
                text="🔄 تم تحديث القوائم",
                text_color="blue"
            )

        def test_search(self):
            """اختبار البحث"""
            import random
            test_terms = ["Cair", "Alex", "قاهر", "اسكند", "Lond", "باري"]
            test_term = random.choice(test_terms)

            self.combo1.clear()
            self.combo1.text_var.set(test_term)

            self.result_label.configure(
                text=f"🧪 اختبار البحث عن: '{test_term}'",
                text_color="purple"
            )

        def run(self):
            """تشغيل التطبيق"""
            self.root.mainloop()

    # تشغيل الاختبار
    app = TestApp()
    app.run()
