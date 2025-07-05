# -*- coding: utf-8 -*-
"""
enhanced_combobox.py - نسخة محسنة ومبسطة موحدة مع تتبع النافذة - مع إصلاح مشكلة تخطي الأسهم

قائمة منسدلة محسنة مع:
- آلية نقر محسنة (النقر الأول للتركيز، الثاني لفتح القائمة)
- بحث فوري مع ألوان زرقاء للتمرير
- كود مبسط ومنظم
- دمج جميع الميزات في مكون واحد
- تتبع النافذة وتحديث موقع القائمة تلقائياً
- عرض القائمة أسفل أو أعلى حسب المساحة المتاحة
- فلترة حية مع أسهم تعمل بشكل مثالي (مُصلحة - لا تخطي)
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Callable, Optional
import time


class EnhancedSearchableComboBox(ctk.CTkFrame):
    """قائمة منسدلة محسنة موحدة مع جميع الميزات وتتبع النافذة - مع إصلاح الأسهم"""

    def __init__(self, parent, values: List[str] = None, placeholder: str = "اكتب للبحث...",
                 width: int = 300, height: int = 35, max_results: int = 10,
                 on_select: Callable[[str], None] = None, debug_mode: bool = False, **kwargs):

        super().__init__(parent, width=width, height=height, **kwargs)

        # الإعدادات الأساسية
        self.values = values or []
        self.placeholder = placeholder
        self.max_results = max_results
        self.on_select = on_select
        self.debug_mode = debug_mode

        # الحالة
        self.filtered_values = self.values.copy()
        self.selected_value = ""
        self.selected_index = -1
        self.is_dropdown_open = False

        # متغيرات التحكم في النقر
        self._last_click_time = 0
        self._has_focus = False
        self._updating_text = False
        self._closing = False

        # متغيرات تتبع النافذة
        self._last_window_x = 0
        self._last_window_y = 0
        self._last_entry_x = 0
        self._last_entry_y = 0
        self._position_check_id = None
        self._dropdown_above = False

        # متغيرات الفلترة الحية
        self._last_text = ""
        self._filter_timer = None

        # واجهة المستخدم
        self.text_var = tk.StringVar()
        self.text_var.trace_add('write', self._on_text_change)

        # النافذة المنبثقة
        self.dropdown_window = None
        self.option_buttons = []

        # بناء الواجهة
        self._build_ui()
        self._setup_events()

        if self.debug_mode:
            print(f"✅ تم إنشاء ComboBox مع {len(self.values)} عنصر")

    def _build_ui(self):
        """بناء واجهة المستخدم"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # حقل الإدخال
        self.entry = ctk.CTkEntry(
            self.main_frame,
            textvariable=self.text_var,
            placeholder_text=self.placeholder,
            height=self.cget("height") - 4
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(2, 1))

        # زر القائمة
        self.dropdown_btn = ctk.CTkButton(
            self.main_frame,
            text="▼",
            width=30,
            height=self.cget("height") - 4,
            command=self._toggle_dropdown
        )
        self.dropdown_btn.pack(side="right", padx=(1, 2))

    def _setup_events(self):
        """إعداد الأحداث - مُصلح لتجنب تداخل معالجة الأسهم"""
        # أحداث النقر المحسنة
        self.entry.bind('<Button-1>', self._on_enhanced_click)
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)

        # أحداث لوحة المفاتيح - معالج واحد فقط لتجنب التداخل
        self.entry.bind('<KeyRelease>', self._on_key_release_enhanced)
        self.entry.bind('<KeyPress>', self._on_key_press)

        # تم حذف binds المنفصلة للأسهم لحل مشكلة التخطي:
        # self.entry.bind('<Down>', self._on_arrow_down)      # مُزال
        # self.entry.bind('<Up>', self._on_arrow_up)          # مُزال
        # self.entry.bind('<Return>', self._on_enter)         # مُزال
        # self.entry.bind('<Escape>', self._on_escape)        # مُزال

        # اكتشاف النقر الخارجي
        self._setup_outside_click_detection()

        # تتبع تحرك النافذة
        self._start_position_tracking()

    def _on_key_press(self, event):
        """معالج الضغط على المفاتيح"""
        key = event.keysym

        if self.debug_mode:
            print(f"⌨️ مفتاح مضغوط: {key}")

        # لا نتجاهل أي مفاتيح هنا - نترك للمعالج التالي

    def _on_key_release_enhanced(self, event):
        """معالج تحرير المفاتيح المحسن - معالج واحد لجميع المفاتيح لتجنب التداخل"""
        key = event.keysym

        if self.debug_mode:
            print(f"⌨️ مفتاح محرر: {key} - القائمة مفتوحة: {self.is_dropdown_open} - الفهرس الحالي: {self.selected_index}")

        # معالجة مفاتيح التنقل أولاً - معالج وحيد لتجنب التداخل
        if key == 'Down':
            self._handle_arrow_down_enhanced()
            return "break"
        elif key == 'Up':
            self._handle_arrow_up_enhanced()
            return "break"
        elif key == 'Return':
            self._handle_enter_enhanced()
            return "break"
        elif key == 'Escape':
            self._handle_escape_enhanced()
            return "break"

        # للمفاتيح الأخرى، تنفيذ الفلترة الحية
        control_keys = ['Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                       'Left', 'Right', 'Home', 'End', 'Page_Up', 'Page_Down']

        if key not in control_keys and not self._updating_text:
            # إلغاء التايمر السابق
            if self._filter_timer:
                self.after_cancel(self._filter_timer)

            # جدولة البحث بتأخير قصير
            self._filter_timer = self.after(50, self._perform_live_filtering)

    def _handle_arrow_down_enhanced(self):
        """معالج السهم لأسفل المحسن - مع تمرير ذكي وطبيعي ودعم التنقل الدائري"""
        if self.debug_mode:
            print(f"⬇️ سهم أسفل - مفتوحة: {self.is_dropdown_open}, أزرار: {len(self.option_buttons)}, الفهرس الحالي: {self.selected_index}")

        if not self.is_dropdown_open:
            self._open_dropdown()
            return

        if not self.option_buttons:
            if self.debug_mode:
                print("⚠️ لا توجد أزرار للتنقل بينها")
            return

        # حساب الفهرس الجديد بعناية مع دعم التنقل الدائري
        old_index = self.selected_index
        if self.selected_index == -1:
            new_index = 0
        else:
            new_index = (self.selected_index + 1) % len(self.option_buttons)

        # تحديد نوع التنقل (عادي أم دائري)
        is_circular_navigation = (old_index == len(self.option_buttons) - 1 and new_index == 0)

        # تطبيق التحديد الجديد أولاً
        self._highlight_option(new_index)

        # معالجة التمرير حسب نوع التنقل
        if is_circular_navigation:
            # تمرير للأعلى (العودة للبداية)
            self._scroll_to_top_smooth()
            if self.debug_mode:
                print(f"🔄 تنقل دائري: العودة للأول - {old_index} → {new_index}")
        else:
            # تمرير عادي
            self._scroll_to_option_smooth(new_index, direction="down")

        if self.debug_mode:
            print(f"⬇️ تحديد مؤكد: {old_index} → {new_index} (العنصر: {self.filtered_values[new_index] if new_index < len(self.filtered_values) else 'N/A'})")

    def _handle_arrow_up_enhanced(self):
        """معالج السهم لأعلى المحسن - مع تمرير ذكي وطبيعي ودعم التنقل الدائري"""
        if self.debug_mode:
            print(f"⬆️ سهم أعلى - مفتوحة: {self.is_dropdown_open}, أزرار: {len(self.option_buttons)}, الفهرس الحالي: {self.selected_index}")

        if not self.is_dropdown_open:
            return

        if not self.option_buttons:
            if self.debug_mode:
                print("⚠️ لا توجد أزرار للتنقل بينها")
            return

        # حساب الفهرس الجديد بعناية مع دعم التنقل الدائري
        old_index = self.selected_index
        if self.selected_index == -1:
            new_index = len(self.option_buttons) - 1
        else:
            new_index = (self.selected_index - 1) % len(self.option_buttons)

        # تحديد نوع التنقل (عادي أم دائري)
        is_circular_navigation = (old_index == 0 and new_index == len(self.option_buttons) - 1)

        # تطبيق التحديد الجديد أولاً
        self._highlight_option(new_index)

        # معالجة التمرير حسب نوع التنقل
        if is_circular_navigation:
            # تمرير للأسفل (الذهاب للنهاية)
            self._scroll_to_bottom_smooth()
            if self.debug_mode:
                print(f"🔄 تنقل دائري: الذهاب للآخر - {old_index} → {new_index}")
        else:
            # تمرير عادي
            self._scroll_to_option_smooth(new_index, direction="up")

        if self.debug_mode:
            print(f"⬆️ تحديد مؤكد: {old_index} → {new_index} (العنصر: {self.filtered_values[new_index] if new_index < len(self.filtered_values) else 'N/A'})")

    def _handle_enter_enhanced(self):
        """معالج مفتاح Enter المحسن"""
        if self.debug_mode:
            print(f"⏎ Enter - مفتوحة: {self.is_dropdown_open}, محدد: {self.selected_index}")

        if self.is_dropdown_open and 0 <= self.selected_index < len(self.filtered_values):
            selected_value = self.filtered_values[self.selected_index]
            if self.debug_mode:
                print(f"⏎ اختيار: {selected_value}")
            self._select_value(selected_value)

    def _handle_escape_enhanced(self):
        """معالج مفتاح Escape المحسن"""
        if self.debug_mode:
            print(f"⎋ Escape - مفتوحة: {self.is_dropdown_open}")

        if self.is_dropdown_open:
            self._close_dropdown()
        else:
            self.clear()

    def _perform_live_filtering(self):
        """تنفيذ الفلترة الحية - نسخة محسنة"""
        try:
            current_text = self.entry.get()

            # تجنب الفلترة المتكررة
            if current_text == self._last_text:
                return

            self._last_text = current_text

            if self.debug_mode:
                print(f"🔄 فلترة حية: '{current_text}' - مفتوحة: {self.is_dropdown_open}")

            # حفظ القيمة المحددة حالياً
            previously_selected_value = None
            if 0 <= self.selected_index < len(self.filtered_values):
                previously_selected_value = self.filtered_values[self.selected_index]

            # البحث والفلترة
            previous_count = len(self.filtered_values)
            self._search_values(current_text)
            current_count = len(self.filtered_values)

            # إذا كانت القائمة مفتوحة، حدثها
            if self.is_dropdown_open:
                if self.debug_mode:
                    print(f"🔄 تحديث القائمة: {previous_count} → {current_count}")

                self._update_dropdown_live()

                # إعادة تحديد العنصر أو تحديد الأول
                if previously_selected_value and previously_selected_value in self.filtered_values:
                    new_index = self.filtered_values.index(previously_selected_value)
                    self._highlight_option(new_index)
                elif self.filtered_values:
                    self._highlight_option(0)

                # تحديث حجم القائمة إذا تغير عدد العناصر
                if current_count != previous_count:
                    self._resize_dropdown_for_new_content()

            elif current_text.strip() and self._has_focus and len(self.filtered_values) > 0:
                # فتح القائمة تلقائياً إذا كان هناك نتائج
                if self.debug_mode:
                    print(f"🎯 فتح تلقائي مع {len(self.filtered_values)} نتيجة")
                self._open_dropdown_with_animation()

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في الفلترة الحية: {e}")
                import traceback
                traceback.print_exc()

    def _start_position_tracking(self):
        """بدء تتبع موقع النافذة"""
        def track_position():
            try:
                if self.is_dropdown_open and self.dropdown_window:
                    self._update_dropdown_position_if_needed()

                # جدولة التحقق التالي
                self._position_check_id = self.after(50, track_position)
            except:
                if self._position_check_id:
                    self.after_cancel(self._position_check_id)
                    self._position_check_id = None

        self._position_check_id = self.after(100, track_position)

    def _update_dropdown_position_if_needed(self):
        """تحديث موقع القائمة إذا تغير موقع النافذة أو الحقل"""
        try:
            # الحصول على موقع النافذة الحالي
            main_window = self.winfo_toplevel()
            current_window_x = main_window.winfo_x()
            current_window_y = main_window.winfo_y()

            # الحصول على موقع الحقل الحالي
            current_entry_x = self.winfo_rootx()
            current_entry_y = self.winfo_rooty()

            # التحقق من تغيير الموقع
            if (current_window_x != self._last_window_x or
                current_window_y != self._last_window_y or
                current_entry_x != self._last_entry_x or
                current_entry_y != self._last_entry_y):

                # تحديث الموقع المحفوظ
                self._last_window_x = current_window_x
                self._last_window_y = current_window_y
                self._last_entry_x = current_entry_x
                self._last_entry_y = current_entry_y

                # تحديث موقع القائمة
                self._reposition_dropdown()

                if self.debug_mode:
                    print(f"🔄 تحديث موقع القائمة: ({current_entry_x}, {current_entry_y})")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في تتبع الموقع: {e}")

    def _calculate_best_dropdown_position(self):
        """حساب أفضل موقع للقائمة (أعلى أو أسفل) مع دعم الفلترة الحية"""
        try:
            # الحصول على معلومات الشاشة
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # موقع وحجم الحقل
            entry_x = self.winfo_rootx()
            entry_y = self.winfo_rooty()
            entry_width = self.winfo_width()
            entry_height = self.winfo_height()

            # حجم القائمة المتوقع مع مراعاة الفلترة
            dropdown_width = max(entry_width, 300)

            # حساب ارتفاع القائمة بناءً على عدد النتائج المفلترة
            items_count = len(self.filtered_values) if self.filtered_values else 1  # 1 للرسالة
            dropdown_height = min(items_count * 35 + 20, 350)  # حد أقصى 350 بكسل

            # إضافة مساحة إضافية للتمرير إذا كان هناك عدد كبير من العناصر
            if items_count > 10:
                dropdown_height = min(10 * 35 + 20, 350)

            # المساحة المتاحة أسفل وأعلى الحقل
            space_below = screen_height - (entry_y + entry_height)
            space_above = entry_y

            # تحديد الموقع الأمثل
            show_above = space_below < dropdown_height and space_above > space_below

            if show_above:
                # عرض أعلى الحقل
                final_y = entry_y - dropdown_height
                self._dropdown_above = True
            else:
                # عرض أسفل الحقل
                final_y = entry_y + entry_height
                self._dropdown_above = False

            # التأكد من عدم خروج القائمة من حدود الشاشة
            final_x = max(0, min(entry_x, screen_width - dropdown_width))
            final_y = max(0, min(final_y, screen_height - dropdown_height))

            if self.debug_mode:
                direction = "أعلى" if show_above else "أسفل"
                print(f"📍 موقع القائمة: {direction} - ({final_x}, {final_y}) - {dropdown_width}x{dropdown_height} - عناصر: {items_count}")

            return final_x, final_y, dropdown_width, dropdown_height

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في حساب الموقع: {e}")
            # قيم افتراضية في حالة الخطأ
            return self.winfo_rootx(), self.winfo_rooty() + self.winfo_height(), 300, 200

    def _reposition_dropdown(self):
        """إعادة تموضع القائمة المنسدلة"""
        if not self.dropdown_window:
            return

        try:
            x, y, width, height = self._calculate_best_dropdown_position()
            self.dropdown_window.geometry(f"{width}x{height}+{x}+{y}")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في إعادة التموضع: {e}")

    def _on_enhanced_click(self, event):
        """آلية النقر المحسنة: الأول للتركيز، الثاني للقائمة"""
        current_time = time.time()
        time_since_last = current_time - self._last_click_time

        if self.debug_mode:
            print(f"🖱️ نقر - التركيز: {self._has_focus}, القائمة: {self.is_dropdown_open}")

        if not self._has_focus:
            # النقرة الأولى: التركيز وتحديد النص
            self._handle_first_click()
        elif time_since_last < 0.5:
            # النقرة الثانية: فتح/إغلاق القائمة
            self._toggle_dropdown()
        else:
            # نقرة بعد فترة: إعادة وضع المؤشر
            self._position_cursor(event)

        self._last_click_time = current_time
        return "break"

    def _handle_first_click(self):
        """معالجة النقرة الأولى"""
        self.entry.focus_set()
        self._has_focus = True

        # تحديد النص الموجود
        current_text = self.entry.get()
        if current_text:
            self.entry.select_range(0, 'end')

        if self.debug_mode:
            print(f"🎯 التركيز الأول - النص: '{current_text}'")

    def _position_cursor(self, event):
        """وضع المؤشر في موقع النقر"""
        try:
            text = self.entry.get()
            if text:
                # تقدير موقع المؤشر
                entry_width = self.entry.winfo_width()
                char_width = entry_width / max(len(text), 1)
                cursor_pos = min(len(text), max(0, int(event.x / char_width)))
                self.entry.icursor(cursor_pos)
        except:
            self.entry.icursor(tk.END)

    def _on_focus_in(self, event):
        """الحصول على التركيز"""
        self._has_focus = True
        if self.debug_mode:
            print("🎯 حصل على التركيز")

    def _on_focus_out(self, event):
        """فقدان التركيز"""
        self._has_focus = False
        if self.debug_mode:
            print("🔍 فقد التركيز")

        # تأخير قصير للتحقق من إغلاق القائمة
        self.after(50, self._check_and_close)

    def _check_and_close(self):
        """فحص وإغلاق القائمة إذا لزم الأمر"""
        if not self.is_dropdown_open or self._closing:
            return

        try:
            focused = self.focus_get()
            if not self._is_focus_inside(focused):
                self._close_dropdown()
        except:
            self._close_dropdown()

    def _is_focus_inside(self, widget):
        """فحص إذا كان التركيز داخل المكون"""
        if not widget:
            return False

        safe_widgets = [self, self.entry, self.dropdown_btn, self.main_frame]
        if self.dropdown_window:
            safe_widgets.append(self.dropdown_window)
        safe_widgets.extend(self.option_buttons)

        # فحص مباشر وهرمي محدود
        current = widget
        for _ in range(5):
            if current in safe_widgets:
                return True
            try:
                current = current.master
            except:
                break
        return False

    def _setup_outside_click_detection(self):
        """إعداد اكتشاف النقر الخارجي"""
        def check_outside():
            try:
                if self.is_dropdown_open and not self._is_focus_inside(self.focus_get()):
                    self._close_dropdown()
            except:
                pass
            self.after(100, check_outside)

        self.after(100, check_outside)

    def _toggle_dropdown(self):
        """تبديل حالة القائمة"""
        if self.is_dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """فتح القائمة المنسدلة - النسخة المحسنة"""
        if self.is_dropdown_open or self._closing:
            return

        try:
            # تحضير البيانات مع الفلترة
            current_text = self.entry.get().strip()
            if current_text:
                self._search_values(current_text)
            else:
                self.filtered_values = self.values.copy()

            # إنشاء النافذة حتى لو لم توجد نتائج (لعرض رسالة)
            self._create_dropdown_window()
            self.is_dropdown_open = True

            # تحديث رمز الزر حسب موقع القائمة
            self.dropdown_btn.configure(text="▲")

            # عرض المحتوى أو رسالة عدم وجود نتائج
            if not self.filtered_values and current_text:
                self._show_no_results_message()
            elif self.filtered_values:
                self._populate_dropdown()
                # تحديد العنصر الأول تلقائياً لتمكين التنقل بالأسهم
                if self.option_buttons:
                    self._highlight_option(0)
                    if self.debug_mode:
                        print(f"🎯 تحديد العنصر الأول تلقائياً: {self.filtered_values[0]}")

            if self.debug_mode:
                direction = "أعلى" if self._dropdown_above else "أسفل"
                if self.filtered_values:
                    print(f"✅ فتح القائمة {direction} مع {len(self.filtered_values)} عنصر")
                else:
                    print(f"✅ فتح القائمة {direction} - لا توجد نتائج")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في فتح القائمة: {e}")

    def _create_dropdown_window(self):
        """إنشاء نافذة القائمة المنسدلة"""
        # تنظيف سابق
        if self.dropdown_window:
            try:
                self.dropdown_window.destroy()
            except:
                pass

        self.option_buttons.clear()

        try:
            # حساب الموقع والحجم الأمثل
            x, y, width, height = self._calculate_best_dropdown_position()

            # حفظ المواقع الحالية
            self._last_window_x = self.winfo_toplevel().winfo_x()
            self._last_window_y = self.winfo_toplevel().winfo_y()
            self._last_entry_x = self.winfo_rootx()
            self._last_entry_y = self.winfo_rooty()

            # إنشاء النافذة
            main_window = self.winfo_toplevel()
            self.dropdown_window = ctk.CTkToplevel(main_window)
            self.dropdown_window.wm_overrideredirect(True)
            self.dropdown_window.geometry(f"{width}x{height}+{x}+{y}")

            # التأكد من أن النافذة تظهر فوق النافذة الرئيسية
            self.dropdown_window.lift()
            self.dropdown_window.attributes('-topmost', True)

            # إطار قابل للتمرير
            self.list_frame = ctk.CTkScrollableFrame(
                self.dropdown_window,
                width=width-10,
                height=height-10
            )
            self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في إنشاء النافذة: {e}")

    def _populate_dropdown(self):
        """ملء القائمة بالخيارات - محسن للعمل مع الأسهم"""
        if not self.filtered_values:
            if self.debug_mode:
                print("⚠️ لا توجد قيم لعرضها في القائمة")
            return

        if self.debug_mode:
            print(f"📋 ملء القائمة بـ {len(self.filtered_values)} عنصر")

        for i, value in enumerate(self.filtered_values):
            try:
                btn = ctk.CTkButton(
                    self.list_frame,
                    text=value,
                    height=35,
                    anchor="w",
                    fg_color="transparent",
                    text_color=("#1976D2", "#FFFFFF"),
                    hover_color=("#E3F2FD", "#1E90FF"),  # الألوان الزرقاء
                    command=lambda v=value: self._select_value(v)
                )
                btn.pack(fill="x", pady=1, padx=2)

                # أحداث التمرير بالماوس فقط (لا تتدخل مع الأسهم)
                btn.bind('<Enter>', lambda e, idx=i: self._on_mouse_enter(idx))
                btn.bind('<Leave>', lambda e, idx=i: self._on_mouse_leave(idx))

                self.option_buttons.append(btn)

                if self.debug_mode and i < 3:  # طباعة أول 3 عناصر فقط
                    print(f"  ✅ تم إنشاء زر {i}: {value}")

            except Exception as e:
                if self.debug_mode:
                    print(f"❌ خطأ في إنشاء الزر {i}: {e}")

        # فرض تحديث العرض
        try:
            self.list_frame.update_idletasks()
            if self.debug_mode:
                print(f"✅ تم ملء القائمة بنجاح: {len(self.option_buttons)} زر")
        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في تحديث العرض: {e}")

    def _select_value(self, value: str):
        """اختيار قيمة"""
        if self.debug_mode:
            print(f"🎯 اختيار: {value}")

        self._updating_text = True
        try:
            self.selected_value = value
            self.text_var.set(value)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, value)

            self._close_dropdown()
            self.entry.focus_set()

            # استدعاء callback
            if self.on_select:
                self.after(20, lambda: self.on_select(value))

        finally:
            self._updating_text = False

    def _close_dropdown(self):
        """إغلاق القائمة مع إعادة تعيين الفلترة"""
        if not self.is_dropdown_open or self._closing:
            return

        self._closing = True
        try:
            if self.dropdown_window:
                self.dropdown_window.destroy()
                self.dropdown_window = None

            self.option_buttons.clear()
            self.is_dropdown_open = False
            self.selected_index = -1
            self.dropdown_btn.configure(text="▼")
            self._dropdown_above = False

            # إعادة تعيين الفلترة للقيم الكاملة عند الإغلاق
            if not self.entry.get().strip():
                self.filtered_values = self.values.copy()

            if self.debug_mode:
                print("🔒 تم إغلاق القائمة مع إعادة تعيين الفلترة")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في الإغلاق: {e}")
        finally:
            self._closing = False

    def _search_values(self, query: str):
        """البحث في القيم مع دعم الفلترة الحية المحسنة"""
        if not query:
            self.filtered_values = self.values.copy()
            if self.debug_mode:
                print(f"🔍 مسح البحث: عودة لجميع القيم ({len(self.filtered_values)} عنصر)")
            return

        query_lower = query.lower().strip()
        if not query_lower:
            self.filtered_values = self.values.copy()
            return

        results = []
        exact_matches = []
        start_matches = []
        contains_matches = []

        # تصنيف النتائج حسب نوع التطابق لفلترة أفضل
        for value in self.values:
            value_lower = value.lower()

            if value_lower == query_lower:
                # تطابق تام
                exact_matches.append(value)
            elif value_lower.startswith(query_lower):
                # تطابق من البداية
                start_matches.append(value)
            elif query_lower in value_lower:
                # تطابق في أي مكان
                contains_matches.append(value)

        # ترتيب النتائج: التطابق التام أولاً، ثم من البداية، ثم في أي مكان
        results = exact_matches + start_matches + contains_matches
        self.filtered_values = results[:self.max_results]

        if self.debug_mode:
            total_matches = len(exact_matches) + len(start_matches) + len(contains_matches)
            print(f"🔍 بحث محسن '{query}':")
            print(f"  📊 النتائج: {len(exact_matches)} تام + {len(start_matches)} بداية + {len(contains_matches)} محتوى = {total_matches}")
            print(f"  📋 معروض: {len(self.filtered_values)} من أصل {total_matches}")
            if self.filtered_values:
                print(f"  🎯 أول 3 نتائج: {self.filtered_values[:3]}")

    def _on_text_change(self, *args):
        """معالج تغيير النص - يتكامل مع الفلترة الحية"""
        if self._updating_text:
            return

        # الفلترة الحية ستتم عبر _on_key_release_enhanced

    def _update_dropdown_live(self):
        """تحديث القائمة المنسدلة بالفلترة الحية - محسن"""
        if not self.dropdown_window or not self.list_frame:
            if self.debug_mode:
                print("❌ لا توجد نافذة قائمة لتحديثها")
            return

        try:
            if self.debug_mode:
                print(f"🔄 تحديث القائمة: {len(self.filtered_values)} عنصر")

            # مسح المحتوى السابق
            for widget in self.list_frame.winfo_children():
                widget.destroy()

            # إعادة تعيين قائمة الأزرار والفهرس
            self.option_buttons.clear()
            self.selected_index = -1  # سيتم إعادة تعيينه في _perform_live_filtering

            # عرض المحتوى الجديد
            current_text = self.entry.get().strip()

            if not self.filtered_values and current_text:
                # عرض رسالة عدم وجود نتائج
                self._show_no_results_message()
            elif not self.filtered_values and not current_text:
                # إذا تم مسح النص، أعد عرض جميع القيم
                self.filtered_values = self.values.copy()
                self._populate_dropdown()
            else:
                # عرض النتائج المفلترة
                self._populate_dropdown()

            # فرض تحديث العرض
            self.list_frame.update_idletasks()
            self.dropdown_window.update_idletasks()

            if self.debug_mode:
                print(f"✅ تم تحديث القائمة: {len(self.option_buttons)} زر معروض")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التحديث الحي: {e}")
                import traceback
                traceback.print_exc()

    def _show_no_results_message(self):
        """عرض رسالة عدم وجود نتائج"""
        if not self.dropdown_window or not self.list_frame:
            return

        try:
            if self.debug_mode:
                print("📭 عرض رسالة عدم وجود نتائج")

            # مسح المحتوى السابق
            for widget in self.list_frame.winfo_children():
                widget.destroy()

            self.option_buttons.clear()
            self.selected_index = -1

            # إضافة رسالة "لا توجد نتائج"
            no_results_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            no_results_frame.pack(fill="both", expand=True, pady=10, padx=10)

            no_results_label = ctk.CTkLabel(
                no_results_frame,
                text="🔍 لا توجد نتائج مطابقة",
                height=35,
                text_color=("gray", "lightgray"),
                font=ctk.CTkFont(size=12, slant="italic")
            )
            no_results_label.pack(expand=True)

            # فرض تحديث العرض
            self.list_frame.update_idletasks()
            self.dropdown_window.update_idletasks()

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في عرض رسالة عدم النتائج: {e}")

    def _resize_dropdown_for_new_content(self):
        """تغيير حجم القائمة حسب المحتوى الجديد"""
        if not self.dropdown_window:
            return

        try:
            # حساب الحجم الجديد
            x, y, width, height = self._calculate_best_dropdown_position()

            # تطبيق الحجم الجديد مع تأثير سلس
            current_geometry = self.dropdown_window.geometry()
            if f"{width}x{height}+{x}+{y}" != current_geometry:
                self.dropdown_window.geometry(f"{width}x{height}+{x}+{y}")

                # تحديث إطار القائمة
                if hasattr(self, 'list_frame'):
                    self.list_frame.configure(width=width-10, height=height-10)

                if self.debug_mode:
                    print(f"📏 تغيير حجم القائمة إلى: {width}x{height}")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في تغيير الحجم: {e}")

    def _open_dropdown_with_animation(self):
        """فتح القائمة تلقائياً مع تأثير سلس"""
        if self.is_dropdown_open or self._closing:
            return

        try:
            # فتح القائمة
            self._open_dropdown()

            # إضافة تأثير ظهور سلس
            if self.dropdown_window:
                # بداية بشفافية منخفضة
                self.dropdown_window.attributes('-alpha', 0.7)

                # زيادة الشفافية تدريجياً
                def fade_in(alpha=0.7):
                    if alpha < 1.0 and self.dropdown_window:
                        try:
                            self.dropdown_window.attributes('-alpha', alpha)
                            self.after(20, lambda: fade_in(min(1.0, alpha + 0.1)))
                        except:
                            pass

                fade_in()

                if self.debug_mode:
                    print("✨ فتح القائمة تلقائياً مع تأثير")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في الفتح التلقائي: {e}")

    def _highlight_option(self, index: int):
        """تمييز خيار بالأسهم - مُصلح لضمان تحديث الفهرس بدقة"""
        if not (0 <= index < len(self.option_buttons)):
            if self.debug_mode:
                print(f"⚠️ فهرس غير صالح للتمييز: {index} (المتاح: 0-{len(self.option_buttons)-1})")
            return

        try:
            # إزالة التمييز من جميع الأزرار
            for i, btn in enumerate(self.option_buttons):
                btn.configure(fg_color="transparent")

            # تمييز الزر المحدد بالأزرق
            self.option_buttons[index].configure(fg_color=("#E3F2FD", "#1E90FF"))

            # تحديث الفهرس المحدد - هذا مهم لتجنب التخطي!
            self.selected_index = index

            if self.debug_mode:
                value = self.filtered_values[index] if index < len(self.filtered_values) else "غير معروف"
                print(f"🎯 تمييز مؤكد: العنصر {index}: {value} - الفهرس محدث إلى: {self.selected_index}")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في تمييز الخيار {index}: {e}")

    def _on_mouse_enter(self, index: int):
        """تمييز عند التمرير بالماوس (لا يغير selected_index)"""
        if not (0 <= index < len(self.option_buttons)):
            return

        try:
            # تمييز بصري خفيف فقط
            if index != self.selected_index:
                self.option_buttons[index].configure(fg_color=("#F8F9FA", "#2A2D3A"))
        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في تمييز الماوس {index}: {e}")

    def _on_mouse_leave(self, index: int):
        """إزالة تمييز الماوس (الحفاظ على تحديد الأسهم)"""
        if 0 <= index < len(self.option_buttons):
            try:
                if index != self.selected_index:
                    self.option_buttons[index].configure(fg_color="transparent")
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ خطأ في إزالة تمييز الماوس {index}: {e}")

    def _scroll_to_option(self, index: int):
        """تمرير ذكي وتدريجي للقائمة - يعرض العناصر التالية عند الحاجة فقط"""
        if not (0 <= index < len(self.option_buttons)) or not hasattr(self, 'list_frame'):
            return

        try:
            # الحصول على canvas الخاص بالإطار القابل للتمرير
            if not hasattr(self.list_frame, '_parent_canvas') or not self.list_frame._parent_canvas:
                return

            canvas = self.list_frame._parent_canvas

            # الحصول على معلومات التمرير الحالية
            canvas_height = canvas.winfo_height()
            scroll_top, scroll_bottom = canvas.yview()

            # حساب موقع العنصر المحدد
            item_height = 37  # ارتفاع كل عنصر (35 + padding)
            item_top = index * item_height
            item_bottom = item_top + item_height

            # حساب المنطقة المرئية الحالية
            total_height = len(self.option_buttons) * item_height
            visible_top = scroll_top * total_height
            visible_bottom = scroll_bottom * total_height

            # هامش أمان للتمرير (لإظهار العنصر بوضوح)
            margin = item_height * 0.5

            # فحص ما إذا كان العنصر مرئياً بالفعل
            is_visible = (item_top >= visible_top - margin and
                         item_bottom <= visible_bottom + margin)

            if is_visible:
                # العنصر مرئي - لا حاجة للتمرير
                if self.debug_mode:
                    print(f"📜 العنصر {index} مرئي بالفعل - لا تمرير")
                return

            # تحديد نوع التمرير المطلوب
            if item_top < visible_top:
                # العنصر أعلى المنطقة المرئية - تمرير لأعلى
                self._scroll_up_to_show(canvas, index, item_height, total_height)
            else:
                # العنصر أسفل المنطقة المرئية - تمرير لأسفل
                self._scroll_down_to_show(canvas, index, item_height, total_height)

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير الذكي: {e}")

    def _scroll_up_to_show(self, canvas, index, item_height, total_height):
        """تمرير تدريجي لأعلى لإظهار العنصر"""
        try:
            # حساب الموقع المطلوب (مع هامش صغير)
            target_top = max(0, (index - 1) * item_height)
            new_scroll_position = target_top / total_height

            # التمرير التدريجي
            current_position = canvas.yview()[0]
            step = min(0.1, abs(new_scroll_position - current_position) / 3)

            if new_scroll_position < current_position:
                target_position = max(new_scroll_position, current_position - step)
                canvas.yview_moveto(target_position)

                if self.debug_mode:
                    print(f"📜⬆️ تمرير لأعلى: العنصر {index} (موقع: {target_position:.3f})")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير لأعلى: {e}")

    def _scroll_down_to_show(self, canvas, index, item_height, total_height):
        """تمرير تدريجي لأسفل لإظهار العناصر التالية"""
        try:
            canvas_height = canvas.winfo_height()
            visible_items = max(1, int(canvas_height / item_height))

            # حساب الموقع المطلوب لإظهار العنصر في أسفل القائمة المرئية
            target_bottom_item = min(len(self.option_buttons) - 1, index + 1)
            target_top_item = max(0, target_bottom_item - visible_items + 1)

            target_top = target_top_item * item_height
            new_scroll_position = min(1.0, target_top / total_height)

            # التمرير التدريجي
            current_position = canvas.yview()[0]
            step = min(0.1, abs(new_scroll_position - current_position) / 3)

            if new_scroll_position > current_position:
                target_position = min(new_scroll_position, current_position + step)
                canvas.yview_moveto(target_position)

                if self.debug_mode:
                    print(f"📜⬇️ تمرير لأسفل: العنصر {index} (موقع: {target_position:.3f}) - عناصر مرئية: {visible_items}")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير لأسفل: {e}")

    def _scroll_to_option_smooth(self, index: int, direction: str = "auto"):
        """تمرير سلس ومحسن للعنصر مع مراعاة الاتجاه"""
        if not (0 <= index < len(self.option_buttons)) or not hasattr(self, 'list_frame'):
            return

        try:
            # الحصول على canvas الخاص بالإطار القابل للتمرير
            if not hasattr(self.list_frame, '_parent_canvas') or not self.list_frame._parent_canvas:
                return

            canvas = self.list_frame._parent_canvas

            # تأخير قصير للسماح للتحديد بالحدوث أولاً
            def perform_smooth_scroll():
                try:
                    # الحصول على معلومات التمرير الحالية
                    canvas_height = canvas.winfo_height()
                    scroll_top, scroll_bottom = canvas.yview()

                    # حساب موقع العنصر المحدد
                    item_height = 37  # ارتفاع كل عنصر
                    item_top = index * item_height
                    item_bottom = item_top + item_height

                    # حساب المنطقة المرئية الحالية
                    total_height = len(self.option_buttons) * item_height
                    visible_top = scroll_top * total_height
                    visible_bottom = scroll_bottom * total_height

                    # هامش أمان (نصف عنصر)
                    margin = item_height * 0.5

                    # فحص ما إذا كان العنصر مرئياً بالكامل
                    is_fully_visible = (item_top >= visible_top + margin and
                                       item_bottom <= visible_bottom - margin)

                    if is_fully_visible:
                        if self.debug_mode:
                            print(f"📜✅ العنصر {index} مرئي بالكامل - لا تمرير مطلوب")
                        return

                    # حساب التمرير المطلوب حسب الاتجاه
                    if direction == "down":
                        self._smart_scroll_down(canvas, index, item_height, total_height, canvas_height)
                    elif direction == "up":
                        self._smart_scroll_up(canvas, index, item_height, total_height, canvas_height)
                    else:
                        # تمرير تلقائي حسب الموقع
                        self._scroll_to_option(index)

                except Exception as e:
                    if self.debug_mode:
                        print(f"❌ خطأ في التمرير السلس: {e}")

            # تنفيذ التمرير بتأخير قصير
            self.after(10, perform_smooth_scroll)

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في إعداد التمرير السلس: {e}")

    def _smart_scroll_down(self, canvas, index, item_height, total_height, canvas_height):
        """تمرير ذكي لأسفل - يعرض العناصر التالية تدريجياً"""
        try:
            visible_items = max(1, int(canvas_height / item_height) - 1)  # ترك مساحة للتمرير

            # إذا كان العنصر في النصف السفلي من القائمة المرئية، قم بالتمرير
            current_scroll_top = canvas.yview()[0]
            current_top_item = int((current_scroll_top * total_height) / item_height)

            # إذا كان العنصر المحدد قريباً من نهاية القائمة المرئية
            if index >= current_top_item + visible_items - 2:
                # حساب موقع التمرير الجديد لإظهار عناصر إضافية
                new_top_item = min(len(self.option_buttons) - visible_items,
                                 max(0, index - visible_items + 3))

                new_scroll_position = (new_top_item * item_height) / total_height
                new_scroll_position = min(1.0, new_scroll_position)

                # تطبيق التمرير
                canvas.yview_moveto(new_scroll_position)

                if self.debug_mode:
                    print(f"📜⬇️ تمرير ذكي لأسفل: العنصر {index} - عرض من {new_top_item}")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير الذكي لأسفل: {e}")

    def _smart_scroll_up(self, canvas, index, item_height, total_height, canvas_height):
        """تمرير ذكي لأعلى - يعرض العناصر السابقة تدريجياً"""
        try:
            visible_items = max(1, int(canvas_height / item_height) - 1)

            # إذا كان العنصر في النصف العلوي من القائمة المرئية، قم بالتمرير
            current_scroll_top = canvas.yview()[0]
            current_top_item = int((current_scroll_top * total_height) / item_height)

            # إذا كان العنصر المحدد قريباً من بداية القائمة المرئية
            if index <= current_top_item + 1:
                # حساب موقع التمرير الجديد لإظهار عناصر سابقة إضافية
                new_top_item = max(0, index - 2)

                new_scroll_position = (new_top_item * item_height) / total_height
                new_scroll_position = max(0.0, new_scroll_position)

                # تطبيق التمرير
                canvas.yview_moveto(new_scroll_position)

                if self.debug_mode:
                    print(f"📜⬆️ تمرير ذكي لأعلى: العنصر {index} - عرض من {new_top_item}")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير الذكي لأعلى: {e}")

    def _scroll_to_top_smooth(self):
        """تمرير سلس للأعلى (للتنقل الدائري - العودة للبداية)"""
        if not hasattr(self, 'list_frame') or not hasattr(self.list_frame, '_parent_canvas'):
            return

        try:
            canvas = self.list_frame._parent_canvas
            if not canvas:
                return

            # تمرير تدريجي للأعلى
            def smooth_scroll_to_top(current_position=None):
                if current_position is None:
                    current_position = canvas.yview()[0]

                if current_position <= 0.05:  # وصل للأعلى تقريباً
                    canvas.yview_moveto(0.0)  # تأكيد الوصول للأعلى تماماً
                    if self.debug_mode:
                        print("🔄⬆️ وصل للأعلى - تنقل دائري مكتمل")
                    return

                # تمرير تدريجي
                step = min(0.15, current_position / 3)
                new_position = max(0.0, current_position - step)
                canvas.yview_moveto(new_position)

                # الاستمرار في التمرير
                self.after(30, lambda: smooth_scroll_to_top(new_position))

            smooth_scroll_to_top()

            if self.debug_mode:
                print("🔄⬆️ بدء التمرير السلس للأعلى (تنقل دائري)")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير للأعلى: {e}")

    def _scroll_to_bottom_smooth(self):
        """تمرير سلس للأسفل (للتنقل الدائري - الذهاب للنهاية)"""
        if not hasattr(self, 'list_frame') or not hasattr(self.list_frame, '_parent_canvas'):
            return

        try:
            canvas = self.list_frame._parent_canvas
            if not canvas:
                return

            # تمرير تدريجي للأسفل
            def smooth_scroll_to_bottom(current_position=None):
                if current_position is None:
                    current_position = canvas.yview()[0]

                if current_position >= 0.95:  # وصل للأسفل تقريباً
                    canvas.yview_moveto(1.0)  # تأكيد الوصول للأسفل تماماً
                    if self.debug_mode:
                        print("🔄⬇️ وصل للأسفل - تنقل دائري مكتمل")
                    return

                # تمرير تدريجي
                step = min(0.15, (1.0 - current_position) / 3)
                new_position = min(1.0, current_position + step)
                canvas.yview_moveto(new_position)

                # الاستمرار في التمرير
                self.after(30, lambda: smooth_scroll_to_bottom(new_position))

            smooth_scroll_to_bottom()

            if self.debug_mode:
                print("🔄⬇️ بدء التمرير السلس للأسفل (تنقل دائري)")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التمرير للأسفل: {e}")

    # معالجات لوحة المفاتيح الأصلية (للتوافق - لكن لن تستخدم بعد الآن)
    def _on_arrow_down(self, event):
        """السهم لأسفل - للتوافق فقط (مُعطل لتجنب التداخل)"""
        if self.debug_mode:
            print("⚠️ تم استدعاء _on_arrow_down المكرر (مُتجاهل لتجنب التخطي)")
        # لا نفعل شيئاً لتجنب التداخل
        return "break"

    def _on_arrow_up(self, event):
        """السهم لأعلى - للتوافق فقط (مُعطل لتجنب التداخل)"""
        if self.debug_mode:
            print("⚠️ تم استدعاء _on_arrow_up المكرر (مُتجاهل لتجنب التخطي)")
        # لا نفعل شيئاً لتجنب التداخل
        return "break"

    def _on_enter(self, event):
        """مفتاح Enter - للتوافق فقط (مُعطل لتجنب التداخل)"""
        if self.debug_mode:
            print("⚠️ تم استدعاء _on_enter المكرر (مُتجاهل لتجنب التخطي)")
        # لا نفعل شيئاً لتجنب التداخل
        return "break"

    def _on_escape(self, event):
        """مفتاح Escape - للتوافق فقط (مُعطل لتجنب التداخل)"""
        if self.debug_mode:
            print("⚠️ تم استدعاء _on_escape المكرر (مُتجاهل لتجنب التخطي)")
        # لا نفعل شيئاً لتجنب التداخل
        return "break"

    # الواجهة العامة
    def get(self) -> str:
        """الحصول على القيمة"""
        return self.selected_value

    def set(self, value: str):
        """تعيين قيمة"""
        if self.debug_mode:
            print(f"🔧 تعيين: '{value}'")

        self._updating_text = True
        try:
            if value and value not in self.values:
                self.add_value(value)

            self.selected_value = value
            self.text_var.set(value)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, value)
        finally:
            self._updating_text = False

    def clear(self):
        """مسح القيمة"""
        self._updating_text = True
        try:
            self.selected_value = ""
            self.text_var.set("")
            self.entry.delete(0, tk.END)
            self.filtered_values = self.values.copy()
            if self.is_dropdown_open:
                self._close_dropdown()
        finally:
            self._updating_text = False

    def set_values(self, values: List[str]):
        """تحديث قائمة القيم"""
        self.values = values.copy() if values else []
        self.filtered_values = self.values.copy()
        if self.debug_mode:
            print(f"📋 تحديث: {len(self.values)} عنصر")

    def add_value(self, value: str):
        """إضافة قيمة جديدة"""
        if value and value not in self.values:
            self.values.append(value)
            self.filtered_values = self.values.copy()

    def is_valid_selection(self) -> bool:
        """التحقق من صحة الاختيار"""
        return self.selected_value in self.values

    def focus_set(self):
        """التركيز على الحقل"""
        self.entry.focus_set()
        self._has_focus = True

    def apply_blue_theme(self, theme_manager=None):
        """تطبيق الثيم الأزرق"""
        try:
            blue_colors = {
                'entry_bg': '#F8F9FA',
                'border_color': '#2196F3',
                'text_color': '#1976D2',
                'button_hover': '#E3F2FD'
            }

            # تطبيق على حقل الإدخال
            if hasattr(self, 'entry'):
                self.entry.configure(
                    fg_color=blue_colors['entry_bg'],
                    border_color=blue_colors['border_color'],
                    text_color=blue_colors['text_color']
                )

            # تطبيق على زر القائمة
            if hasattr(self, 'dropdown_btn'):
                self.dropdown_btn.configure(
                    hover_color=blue_colors['button_hover'],
                    border_color=blue_colors['border_color']
                )

            if self.debug_mode:
                print("✅ تم تطبيق الثيم الأزرق")

        except Exception as e:
            if self.debug_mode:
                print(f"❌ فشل تطبيق الثيم: {e}")

    def destroy(self):
        """تنظيف الموارد عند الحذف"""
        try:
            # إيقاف التايمرات
            if hasattr(self, '_filter_timer') and self._filter_timer:
                self.after_cancel(self._filter_timer)
                self._filter_timer = None

            # إيقاف تتبع الموقع
            if self._position_check_id:
                self.after_cancel(self._position_check_id)
                self._position_check_id = None

            # إغلاق القائمة
            if self.is_dropdown_open:
                self._close_dropdown()

            # استدعاء destroy الأساسي
            super().destroy()

        except Exception as e:
            if self.debug_mode:
                print(f"❌ خطأ في التنظيف: {e}")


# الأسماء البديلة للتوافق
EnhancedSearchableComboBoxImproved = EnhancedSearchableComboBox
SearchableComboBox = EnhancedSearchableComboBox


def create_enhanced_dropdown_with_improved_click(parent, field_name: str, initial_value: str = "",
                                                values: List[str] = None, themed_window=None,
                                                debug_mode: bool = False, theme_manager=None):
    """إنشاء قائمة منسدلة محسنة مع آلية النقر المحسنة وتتبع النافذة"""

    # تحضير القيم
    if not values:
        values = []

    if initial_value and initial_value not in values:
        values = [initial_value] + values

    # إنشاء المكون
    combo = EnhancedSearchableComboBox(
        parent=parent,
        values=values,
        placeholder=f"ابحث في {field_name}...",
        width=300,
        height=35,
        max_results=15,
        debug_mode=debug_mode
    )

    # تطبيق الثيم
    if theme_manager:
        try:
            combo.apply_blue_theme(theme_manager)
        except Exception as e:
            print(f"⚠️ فشل في تطبيق الثيم: {e}")

    if themed_window:
        try:
            themed_window.apply_to_widget(combo.entry, 'entry')
            themed_window.apply_to_widget(combo.dropdown_btn, 'button_secondary')
        except Exception as e:
            print(f"تحذير: فشل في تطبيق الثيم العادي: {e}")

    # تعيين القيمة الأولية
    if initial_value:
        combo.set(initial_value)

    # إنشاء متغير للتوافق
    var = tk.StringVar(value=initial_value)

    # ربط المتغير مع المكون
    def sync_var():
        try:
            current_value = combo.get()
            if var.get() != current_value:
                var.set(current_value)
        except:
            pass

    def sync_combo(*args):
        try:
            current_value = var.get()
            if current_value != combo.get():
                combo.set(current_value)
        except:
            pass

    # ربط التحديثات
    var.trace('w', sync_combo)

    # تحديث دوري
    def periodic_sync():
        try:
            sync_var()
            combo.after(2000, periodic_sync)
        except:
            pass

    combo.after(100, periodic_sync)

    return var, combo


def create_airtable_combo_for_field(parent, field_name: str, dropdown_manager=None,
                                   themed_window=None, values: List[str] = None,
                                   debug_mode: bool = False, **kwargs):
    """إنشاء قائمة منسدلة لحقل Airtable مع تتبع النافذة"""

    placeholder_map = {
        "Agency": "ابحث عن وكالة...",
        "Guide": "ابحث عن مرشد...",
        "Option": "ابحث عن خيار...",
        "des": "ابحث عن وجهة...",
        "trip Name": "ابحث عن اسم رحلة...",
        "Management Option": "ابحث عن خيار إدارة...",
        "Add-on": "ابحث عن إضافة..."
    }

    if not kwargs.get('placeholder'):
        kwargs['placeholder'] = placeholder_map.get(field_name, f"ابحث في {field_name}...")

    kwargs.setdefault('max_results', 15)
    kwargs.setdefault('debug_mode', debug_mode)

    if values:
        kwargs['values'] = values

    return EnhancedSearchableComboBox(parent=parent, **kwargs)


# دالة اختبار مُحدثة مع التأكيد على إصلاح مشكلة تخطي الأسهم
def test_natural_scroll_navigation():
    """اختبار التنقل الطبيعي مع التمرير الذكي والتنقل الدائري المحسن"""

    app = ctk.CTk()
    app.title("🌊 اختبار التنقل الدائري والتمرير الذكي")
    app.geometry("700x650")

    # قائمة كبيرة للاختبار (أكثر من المساحة المرئية)
    test_values = [f"العنصر رقم {i+1:02d}" for i in range(25)]

    # متغيرات تتبع التنقل
    navigation_log = []
    scroll_log = []
    circular_navigation_count = 0

    def log_navigation(action, old_index, new_index):
        """تسجيل حركات التنقل مع التعرف على التنقل الدائري"""
        nonlocal circular_navigation_count

        # تحديد نوع التنقل
        is_circular = False
        if (old_index == len(test_values) - 1 and new_index == 0):
            is_circular = True
            action = "🔄 تنقل دائري (النهاية→البداية)"
            circular_navigation_count += 1
        elif (old_index == 0 and new_index == len(test_values) - 1):
            is_circular = True
            action = "🔄 تنقل دائري (البداية→النهاية)"
            circular_navigation_count += 1

        log_entry = f"{action}: {old_index} → {new_index}"
        if is_circular:
            log_entry += " ✨"

        navigation_log.append(log_entry)
        log_text.configure(text="\n".join(navigation_log[-6:]))  # آخر 6 حركات

        # تحديث عداد التنقل الدائري
        circular_count_label.configure(text=f"تنقلات دائرية: {circular_navigation_count} 🔄")

    def log_scroll(action):
        """تسجيل أحداث التمرير"""
        scroll_log.append(action)
        scroll_text.configure(text="\n".join(scroll_log[-4:]))  # آخر 4 أحداث تمرير

    # تعليمات الاختبار المحدثة
    instructions = ctk.CTkLabel(
        app,
        text="🌊 اختبار التنقل الدائري والتمرير الذكي:\n\n" +
             "✨ الميزات الجديدة:\n" +
             "• تنقل دائري: من النهاية للبداية والعكس 🔄\n" +
             "• تمرير ذكي وسلس للتنقل الدائري\n" +
             "• عرض طبيعي مثل التطبيقات الحديثة\n\n" +
             "🧪 جرب الوصول لنهاية القائمة ثم اضغط ↓:",
        font=ctk.CTkFont(size=12, weight="bold"),
        justify="center"
    )
    instructions.pack(pady=15)

    # ComboBox مُحسن مع تتبع التنقل الدائري
    class CircularNavigationComboBox(EnhancedSearchableComboBox):
        def _highlight_option(self, index: int):
            """تمييز مع تسجيل التنقل الدائري"""
            old_index = self.selected_index
            super()._highlight_option(index)
            new_index = self.selected_index

            if old_index != new_index:
                action = "تنقل بالأسهم"
                log_navigation(action, old_index, new_index)

                if new_index < len(self.filtered_values):
                    value = self.filtered_values[new_index]
                    position_info = ""
                    if new_index == 0:
                        position_info = " (البداية ⬆️)"
                    elif new_index == len(self.filtered_values) - 1:
                        position_info = " (النهاية ⬇️)"

                    current_selection.configure(text=f"محدد: {value} (فهرس: {new_index}){position_info}")

        def _scroll_to_top_smooth(self):
            """تمرير للأعلى مع تسجيل"""
            log_scroll("🔄⬆️ تمرير دائري للأعلى")
            super()._scroll_to_top_smooth()

        def _scroll_to_bottom_smooth(self):
            """تمرير للأسفل مع تسجيل"""
            log_scroll("🔄⬇️ تمرير دائري للأسفل")
            super()._scroll_to_bottom_smooth()

        def _smart_scroll_down(self, canvas, index, item_height, total_height, canvas_height):
            """تمرير ذكي مع تسجيل"""
            log_scroll(f"⬇️ تمرير عادي للعنصر {index}")
            super()._smart_scroll_down(canvas, index, item_height, total_height, canvas_height)

        def _smart_scroll_up(self, canvas, index, item_height, total_height, canvas_height):
            """تمرير ذكي مع تسجيل"""
            log_scroll(f"⬆️ تمرير عادي للعنصر {index}")
            super()._smart_scroll_up(canvas, index, item_height, total_height, canvas_height)

    # إنشاء ComboBox محسن
    combo_frame = ctk.CTkFrame(app)
    combo_frame.pack(pady=20, padx=20, fill="x")

    combo_label = ctk.CTkLabel(
        combo_frame,
        text="📋 قائمة طويلة (25 عنصر) - اختبار التنقل الدائري:",
        font=ctk.CTkFont(size=12, weight="bold")
    )
    combo_label.pack(pady=(10, 5))

    combo = CircularNavigationComboBox(
        parent=combo_frame,
        values=test_values,
        placeholder="افتح القائمة واختبر التنقل الدائري...",
        width=500,
        height=40,
        max_results=25,  # عرض جميع العناصر
        debug_mode=True
    )
    combo.pack(pady=10)

    # عرض العنصر المحدد حالياً
    current_selection = ctk.CTkLabel(
        app,
        text="محدد حالياً: لا شيء",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=("#2196F3", "#64B5F6")
    )
    current_selection.pack(pady=10)

    # عداد التنقل الدائري
    circular_count_label = ctk.CTkLabel(
        app,
        text="تنقلات دائرية: 0 🔄",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=("#FF9800", "#FFA726")
    )
    circular_count_label.pack(pady=5)

    # إطار لعرض السجلات
    logs_frame = ctk.CTkFrame(app)
    logs_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # سجل حركات التنقل
    nav_frame = ctk.CTkFrame(logs_frame)
    nav_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    nav_title = ctk.CTkLabel(
        nav_frame,
        text="📋 سجل التنقل (آخر 6 حركات):",
        font=ctk.CTkFont(size=11, weight="bold")
    )
    nav_title.pack(pady=(10, 5))

    log_text = ctk.CTkLabel(
        nav_frame,
        text="لم يتم التنقل بعد...",
        font=ctk.CTkFont(size=10, family="monospace"),
        justify="left",
        anchor="w"
    )
    log_text.pack(pady=10, padx=10, fill="both", expand=True)

    # سجل أحداث التمرير
    scroll_frame = ctk.CTkFrame(logs_frame)
    scroll_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

    scroll_title = ctk.CTkLabel(
        scroll_frame,
        text="📜 سجل التمرير (آخر 4 أحداث):",
        font=ctk.CTkFont(size=11, weight="bold")
    )
    scroll_title.pack(pady=(10, 5))

    scroll_text = ctk.CTkLabel(
        scroll_frame,
        text="لم يحدث تمرير بعد...",
        font=ctk.CTkFont(size=10, family="monospace"),
        justify="left",
        anchor="w"
    )
    scroll_text.pack(pady=10, padx=10, fill="both", expand=True)

    # إرشادات الاختبار المحدثة
    test_guide = ctk.CTkFrame(app)
    test_guide.pack(pady=10, padx=20, fill="x")

    guide_text = [
        "🧪 اختبارات التنقل الدائري المحسن:",
        "• افتح القائمة واستخدم ↓ للوصول لنهاية القائمة",
        "• عند الوصول للعنصر الأخير، اضغط ↓ → سينتقل للأول 🔄",
        "• من العنصر الأول، اضغط ↑ → سينتقل للأخير 🔄",
        "• راقب التمرير السلس أثناء التنقل الدائري",
        "• التنقل الدائري مميز بـ ✨ في السجل"
    ]

    for i, text in enumerate(guide_text):
        label = ctk.CTkLabel(
            test_guide,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold" if i == 0 else "normal"),
            text_color=("#2196F3", "#64B5F6") if i == 0 else ("gray", "lightgray"),
            anchor="e"
        )
        label.pack(pady=1, padx=10, anchor="e")

    # أزرار التحكم المحدثة
    button_frame = ctk.CTkFrame(app)
    button_frame.pack(pady=10)

    def open_and_select_first():
        combo._open_dropdown()
        if combo.option_buttons:
            combo._highlight_option(0)

    def open_and_select_last():
        combo._open_dropdown()
        if combo.option_buttons:
            last_index = len(combo.option_buttons) - 1
            combo._highlight_option(last_index)
            combo._scroll_to_bottom_smooth()

    def test_circular_down():
        """اختبار التنقل الدائري لأسفل"""
        if not combo.is_dropdown_open:
            combo._open_dropdown()
        if combo.option_buttons:
            last_index = len(combo.option_buttons) - 1
            combo._highlight_option(last_index)
            combo._scroll_to_bottom_smooth()
            combo.after(1000, lambda: combo._handle_arrow_down_enhanced())

    def test_circular_up():
        """اختبار التنقل الدائري لأعلى"""
        if not combo.is_dropdown_open:
            combo._open_dropdown()
        if combo.option_buttons:
            combo._highlight_option(0)
            combo._scroll_to_top_smooth()
            combo.after(1000, lambda: combo._handle_arrow_up_enhanced())

    def clear_logs():
        nonlocal circular_navigation_count
        navigation_log.clear()
        scroll_log.clear()
        circular_navigation_count = 0
        log_text.configure(text="تم مسح سجل التنقل...")
        scroll_text.configure(text="تم مسح سجل التمرير...")
        circular_count_label.configure(text="تنقلات دائرية: 0 🔄")
        current_selection.configure(text="محدد حالياً: لا شيء")

    ctk.CTkButton(button_frame, text="فتح + الأول",
                  command=open_and_select_first).pack(side="left", padx=2)
    ctk.CTkButton(button_frame, text="فتح + الأخير",
                  command=open_and_select_last).pack(side="left", padx=2)
    ctk.CTkButton(button_frame, text="اختبار ↓ دائري",
                  command=test_circular_down,
                  text_color=("#FF9800", "#FFA726")).pack(side="left", padx=2)
    ctk.CTkButton(button_frame, text="اختبار ↑ دائري",
                  command=test_circular_up,
                  text_color=("#FF9800", "#FFA726")).pack(side="left", padx=2)
    ctk.CTkButton(button_frame, text="مسح السجلات",
                  command=clear_logs).pack(side="left", padx=2)
    ctk.CTkButton(button_frame, text="إغلاق",
                  command=combo._close_dropdown).pack(side="left", padx=2)

    print("🌊 بدء اختبار التنقل الدائري والتمرير الذكي")
    print("✨ الميزات الجديدة:")
    print("  🔄 تنقل دائري - من النهاية للبداية والعكس")
    print("  🎯 تمرير ذكي - يحدث عند الحاجة فقط")
    print("  📱 سلوك طبيعي - مثل التطبيقات الحديثة")
    print("  💫 تمرير سلس للتنقل الدائري")
    print("=" * 60)

    app.mainloop()


# تحديث الدوال للتوافق
def test_enhanced_combobox_arrow_fix():
    """دالة للتوافق - تستدعي اختبار التمرير الطبيعي"""
    print("📌 استدعاء اختبار التمرير الطبيعي المحسن...")
    return test_natural_scroll_navigation()

def test_enhanced_combobox_with_live_filtering():
    """دالة للتوافق مع الاسم السابق"""
    print("📌 استدعاء اختبار التمرير الطبيعي...")
    return test_natural_scroll_navigation()

def test_enhanced_combobox_with_tracking():
    """دالة للتوافق مع الاسم السابق"""
    print("📌 استدعاء اختبار التمرير الطبيعي...")
    return test_natural_scroll_navigation()

def test_enhanced_combobox():
    """دالة اختبار بسيطة للتوافق مع الإصدار السابق"""
    print("📌 استدعاء اختبار التمرير الطبيعي...")
    return test_natural_scroll_navigation()


if __name__ == "__main__":
    test_natural_scroll_navigation()


# ✅ ملخص الإصلاحات والتحسينات المطبقة:
#
# 🔧 إصلاح مشكلة تخطي الأسهم:
#   1. إزالة المعالجات المكررة في _setup_events()
#   2. معالج واحد فقط: _on_key_release_enhanced()
#   3. تحسين _highlight_option() لضمان تحديث الفهرس
#   4. تعطيل الدوال المكررة لتجنب التداخل
#
# 🔄 إضافة التنقل الدائري المحسن:
#   1. من النهاية للبداية عند الضغط على ↓
#   2. من البداية للنهاية عند الضغط على ↑
#   3. تمرير سلس ومتحرك للتنقل الدائري
#   4. كشف تلقائي للتنقل الدائري مع تسجيل مميز
#
# 🌊 تحسين التمرير الطبيعي:
#   1. _scroll_to_option() الآن ذكي - يفحص الرؤية أولاً
#   2. تمرير تدريجي بدلاً من القفز المباشر
#   3. _smart_scroll_down() و _smart_scroll_up() للتمرير الطبيعي
#   4. _scroll_to_top_smooth() و _scroll_to_bottom_smooth() للتنقل الدائري
#   5. التمرير يحدث فقط عند الحاجة (وصول لحافة القائمة)
#
# 🎯 النتائج:
#   ✅ تنقل صحيح عنصر واحد بكل ضغطة سهم
#   ✅ تنقل دائري سلس من النهاية للبداية والعكس 🔄
#   ✅ تمرير طبيعي وذكي مثل التطبيقات الحديثة
#   ✅ لا مزيد من القفزات المفاجئة في التمرير
#   ✅ سلوك بديهي ومألوف للمستخدم
#   ✅ تأثيرات بصرية سلسة للتنقل الدائري
#
# 🧪 للاختبار: python combobox.py