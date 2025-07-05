# -*- coding: utf-8 -*-
"""
airtable_field_analyzer.py - نظام تحليل وتصنيف حقول Airtable

نظام شامل لـ:
- جلب جميع الحقول من Airtable
- تحديد نوع كل حقل
- تصنيف الحقول حسب المجموعات
- إنشاء تقارير مفصلة
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from core.logger import logger


@dataclass
class FieldInfo:
    """معلومات شاملة عن الحقل"""
    name: str
    airtable_type: str
    mapped_type: str
    group: str
    is_required: bool = False
    is_readonly: bool = False
    has_options: bool = False
    options: List[str] = None
    description: str = ""


class AirtableFieldAnalyzer:
    """محلل حقول Airtable مع التصنيف التلقائي"""

    def __init__(self, airtable_model=None, config_mgr=None):
        self.airtable_model = airtable_model
        self.config_mgr = config_mgr

        # المجموعات المُعرّفة مسبقاً
        self.predefined_groups = {
            "Basic Information": [
                "Customer Name", "Hotel Name", "Agency", "Booking Nr.", "Room number"
            ],
            "Trip Details": [
                "trip Name", "Date Trip", "Option", "des", "Guide",
                "Product ID", "pickup time", "Remarks", "Add - Ons"
            ],
            "Passenger Info": [
                "ADT", "CHD", "STD", "Youth", "Inf", "CHD Age"
            ],
            "Contact Info": [
                "Customer Phone", "Customer Email", "Customer Country"
            ],
            "Pricing Info": [
                "Total price USD", "Total price EUR", "Total price GBP",
                "Net Rate", "Currency", "Cost EGP", "Collecting on date Trip",
                "Management Option", "Add-on"
            ]
        }

        # أنواع الحقول المُعرّفة مسبقاً
        self.predefined_types = {
            "Customer Name": "text", "Hotel Name": "text", "Agency": "dropdown",
            "Booking Nr.": "readonly", "Room number": "text", "trip Name": "dropdown",
            "Date Trip": "date", "Option": "dropdown", "des": "dropdown",
            "Guide": "dropdown", "Product ID": "text", "pickup time": "text",
            "Remarks": "text", "Add - Ons": "text", "ADT": "number",
            "CHD": "number", "STD": "number", "Youth": "number", "Inf": "number",
            "CHD Age": "text", "Customer Phone": "phone", "Customer Email": "email",
            "Customer Country": "text", "Total price USD": "currency",
            "Total price EUR": "currency", "Total price GBP": "currency",
            "Net Rate": "currency", "Currency": "text", "Cost EGP": "currency",
            "Collecting on date Trip": "text", "Management Option": "dropdown",
            "Add-on": "dropdown"
        }

        # خريطة تحويل أنواع Airtable إلى أنواع النظام
        self.type_mapping = {
            'singleLineText': 'text',
            'multilineText': 'text',
            'richText': 'text',
            'email': 'email',
            'phoneNumber': 'phone',
            'url': 'text',
            'number': 'number',
            'percent': 'number',
            'currency': 'currency',
            'singleSelect': 'dropdown',
            'multipleSelects': 'dropdown',
            'date': 'date',
            'dateTime': 'date',
            'checkbox': 'checkbox',
            'rating': 'number',
            'multipleAttachments': 'file',
            'barcode': 'text',
            'formula': 'readonly',
            'rollup': 'readonly',
            'count': 'readonly',
            'lookup': 'readonly',
            'multipleRecordLinks': 'dropdown',
            'createdTime': 'readonly',
            'createdBy': 'readonly',
            'lastModifiedTime': 'readonly',
            'lastModifiedBy': 'readonly'
        }

    def get_table_schema(self, table_name: str = None) -> Dict[str, Any]:
        """جلب مخطط الجدول من Airtable"""
        try:
            if self.airtable_model:
                # استخدام API المباشر
                schema = self.airtable_model.get_table_schema(table_name)
                return schema
            else:
                # محاولة جلب المخطط من مصادر أخرى
                logger.warning("Airtable model غير متوفر، سيتم استخدام المخطط الافتراضي")
                return self._get_default_schema()

        except Exception as e:
            logger.error(f"خطأ في جلب مخطط الجدول: {e}")
            return self._get_default_schema()

    def _get_default_schema(self) -> Dict[str, Any]:
        """مخطط افتراضي في حالة فشل الاتصال"""
        return {
            "fields": [
                {"name": field_name, "type": "singleLineText"}
                for group_fields in self.predefined_groups.values()
                for field_name in group_fields
            ]
        }

    def analyze_all_fields(self, table_name: str = None) -> Dict[str, FieldInfo]:
        """تحليل جميع حقول الجدول"""
        logger.info(f"🔍 بدء تحليل حقول الجدول: {table_name}")

        schema = self.get_table_schema(table_name)
        analyzed_fields = {}

        if "fields" in schema:
            for field_data in schema["fields"]:
                field_info = self._analyze_single_field(field_data)
                analyzed_fields[field_info.name] = field_info

        logger.info(f"✅ تم تحليل {len(analyzed_fields)} حقل")
        return analyzed_fields

    def _analyze_single_field(self, field_data: Dict[str, Any]) -> FieldInfo:
        """تحليل حقل واحد"""
        field_name = field_data.get("name", "")
        airtable_type = field_data.get("type", "singleLineText")

        # تحديد النوع المطلوب
        mapped_type = self._get_mapped_type(field_name, airtable_type)

        # تحديد المجموعة
        group = self._determine_group(field_name)

        # تحديد الخصائص الإضافية
        is_required = self._is_required_field(field_name)
        is_readonly = self._is_readonly_field(field_name, airtable_type)
        has_options, options = self._get_field_options(field_data)

        return FieldInfo(
            name=field_name,
            airtable_type=airtable_type,
            mapped_type=mapped_type,
            group=group,
            is_required=is_required,
            is_readonly=is_readonly,
            has_options=has_options,
            options=options or [],
            description=field_data.get("description", "")
        )

    def _get_mapped_type(self, field_name: str, airtable_type: str) -> str:
        """تحديد النوع المطلوب للحقل"""
        # أولاً: فحص النوع المُعرّف مسبقاً
        if field_name in self.predefined_types:
            return self.predefined_types[field_name]

        # ثانياً: التحويل من نوع Airtable
        if airtable_type in self.type_mapping:
            return self.type_mapping[airtable_type]

        # ثالثاً: استنتاج ذكي بناءً على اسم الحقل
        return self._smart_type_detection(field_name, airtable_type)

    def _smart_type_detection(self, field_name: str, airtable_type: str) -> str:
        """استنتاج ذكي لنوع الحقل"""
        field_lower = field_name.lower()

        # فحص الكلمات المفتاحية
        if any(keyword in field_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in field_lower for keyword in ['phone', 'mobile', 'tel']):
            return 'phone'
        elif any(keyword in field_lower for keyword in ['date', 'time', 'day']):
            return 'date'
        elif any(keyword in field_lower for keyword in ['price', 'cost', 'amount', 'total', 'rate']):
            return 'currency'
        elif any(keyword in field_lower for keyword in ['number', 'count', 'qty', 'quantity']):
            return 'number'
        elif any(keyword in field_lower for keyword in ['option', 'type', 'category', 'status']):
            return 'dropdown'
        elif 'readonly' in field_lower or airtable_type in ['formula', 'rollup', 'count']:
            return 'readonly'
        else:
            return 'text'

    def _determine_group(self, field_name: str) -> str:
        """تحديد المجموعة التي ينتمي إليها الحقل"""
        # فحص المجموعات المُعرّفة مسبقاً
        for group_name, fields in self.predefined_groups.items():
            if field_name in fields:
                return group_name

        # استنتاج ذكي للمجموعة
        return self._smart_group_detection(field_name)

    def _smart_group_detection(self, field_name: str) -> str:
        """استنتاج ذكي للمجموعة"""
        field_lower = field_name.lower()

        # معلومات أساسية
        if any(keyword in field_lower for keyword in ['customer', 'name', 'hotel', 'agency', 'booking', 'room']):
            return "Basic Information"

        # تفاصيل الرحلة
        elif any(keyword in field_lower for keyword in ['trip', 'tour', 'destination', 'guide', 'pickup', 'option']):
            return "Trip Details"

        # معلومات الركاب
        elif any(keyword in field_lower for keyword in ['adt', 'chd', 'std', 'youth', 'inf', 'passenger', 'age']):
            return "Passenger Info"

        # معلومات الاتصال
        elif any(keyword in field_lower for keyword in ['phone', 'email', 'contact', 'country']):
            return "Contact Info"

        # معلومات الأسعار
        elif any(keyword in field_lower for keyword in ['price', 'cost', 'rate', 'currency', 'total', 'payment']):
            return "Pricing Info"

        else:
            return "Other"

    def _is_required_field(self, field_name: str) -> bool:
        """تحديد ما إذا كان الحقل مطلوباً"""
        required_fields = ["Customer Name", "Agency", "Date Trip"]
        return field_name in required_fields

    def _is_readonly_field(self, field_name: str, airtable_type: str) -> bool:
        """تحديد ما إذا كان الحقل للقراءة فقط"""
        readonly_types = ['formula', 'rollup', 'count', 'lookup', 'createdTime', 'createdBy', 'lastModifiedTime', 'lastModifiedBy']
        readonly_fields = ["Booking Nr."]

        return (airtable_type in readonly_types) or (field_name in readonly_fields)

    def _get_field_options(self, field_data: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        """استخراج خيارات الحقل إن وجدت"""
        field_type = field_data.get("type", "")
        options_data = field_data.get("options", {})

        if field_type == "singleSelect":
            choices = options_data.get("choices", [])
            options = [choice.get("name", "") for choice in choices]
            return len(options) > 0, options

        elif field_type == "multipleSelects":
            choices = options_data.get("choices", [])
            options = [choice.get("name", "") for choice in choices]
            return len(options) > 0, options

        elif field_type == "multipleRecordLinks":
            linked_table = options_data.get("linkedTableId", "")
            return True, [f"Linked to: {linked_table}"]

        return False, None

    def generate_field_groups_dict(self, analyzed_fields: Dict[str, FieldInfo]) -> Dict[str, List[str]]:
        """إنشاء قاموس المجموعات بناءً على التحليل"""
        groups = {}

        for field_info in analyzed_fields.values():
            group = field_info.group
            if group not in groups:
                groups[group] = []
            groups[group].append(field_info.name)

        return groups

    def generate_field_types_dict(self, analyzed_fields: Dict[str, FieldInfo]) -> Dict[str, str]:
        """إنشاء قاموس أنواع الحقول بناءً على التحليل"""
        return {
            field_info.name: field_info.mapped_type
            for field_info in analyzed_fields.values()
        }

    def generate_detailed_report(self, analyzed_fields: Dict[str, FieldInfo]) -> Dict[str, Any]:
        """إنشاء تقرير مفصل"""
        report = {
            "total_fields": len(analyzed_fields),
            "fields_by_group": {},
            "fields_by_type": {},
            "required_fields": [],
            "readonly_fields": [],
            "dropdown_fields": [],
            "field_details": {}
        }

        # تجميع حسب المجموعة
        for field_info in analyzed_fields.values():
            group = field_info.group
            if group not in report["fields_by_group"]:
                report["fields_by_group"][group] = []
            report["fields_by_group"][group].append(field_info.name)

        # تجميع حسب النوع
        for field_info in analyzed_fields.values():
            field_type = field_info.mapped_type
            if field_type not in report["fields_by_type"]:
                report["fields_by_type"][field_type] = []
            report["fields_by_type"][field_type].append(field_info.name)

        # الحقول المطلوبة
        report["required_fields"] = [
            field_info.name for field_info in analyzed_fields.values()
            if field_info.is_required
        ]

        # الحقول المحمية
        report["readonly_fields"] = [
            field_info.name for field_info in analyzed_fields.values()
            if field_info.is_readonly
        ]

        # القوائم المنسدلة
        report["dropdown_fields"] = [
            field_info.name for field_info in analyzed_fields.values()
            if field_info.mapped_type == "dropdown"
        ]

        # التفاصيل الكاملة
        report["field_details"] = {
            field_info.name: {
                "airtable_type": field_info.airtable_type,
                "mapped_type": field_info.mapped_type,
                "group": field_info.group,
                "is_required": field_info.is_required,
                "is_readonly": field_info.is_readonly,
                "has_options": field_info.has_options,
                "options": field_info.options,
                "description": field_info.description
            }
            for field_info in analyzed_fields.values()
        }

        return report

    def export_configuration(self, analyzed_fields: Dict[str, FieldInfo], filename: str = "field_config.json"):
        """تصدير التكوين لاستخدامه في النظام"""
        config = {
            "field_groups": self.generate_field_groups_dict(analyzed_fields),
            "field_type_map": self.generate_field_types_dict(analyzed_fields),
            "required_fields": [
                field_info.name for field_info in analyzed_fields.values()
                if field_info.is_required
            ],
            "readonly_fields": [
                field_info.name for field_info in analyzed_fields.values()
                if field_info.is_readonly
            ],
            "dropdown_fields": {
                field_info.name: field_info.options
                for field_info in analyzed_fields.values()
                if field_info.has_options and field_info.options
            }
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ تم تصدير التكوين إلى {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ فشل في تصدير التكوين: {e}")
            return False

    def print_analysis_summary(self, analyzed_fields: Dict[str, FieldInfo]):
        """طباعة ملخص التحليل"""
        report = self.generate_detailed_report(analyzed_fields)

        print("="*60)
        print("📊 تقرير تحليل حقول Airtable")
        print("="*60)
        print(f"إجمالي الحقول: {report['total_fields']}")
        print()

        print("📂 الحقول حسب المجموعة:")
        for group, fields in report["fields_by_group"].items():
            print(f"  {group}: {len(fields)} حقل")
            for field in fields:
                field_info = analyzed_fields[field]
                status_icons = []
                if field_info.is_required:
                    status_icons.append("⚠️")
                if field_info.is_readonly:
                    status_icons.append("🔒")
                if field_info.has_options:
                    status_icons.append("📋")

                status_str = " ".join(status_icons)
                print(f"    - {field} ({field_info.mapped_type}) {status_str}")
        print()

        print("🏷️ الحقول حسب النوع:")
        for field_type, fields in report["fields_by_type"].items():
            print(f"  {field_type}: {len(fields)} حقل")
        print()

        if report["required_fields"]:
            print("⚠️ الحقول المطلوبة:")
            for field in report["required_fields"]:
                print(f"  - {field}")
            print()

        if report["readonly_fields"]:
            print("🔒 الحقول المحمية:")
            for field in report["readonly_fields"]:
                print(f"  - {field}")
            print()

        if report["dropdown_fields"]:
            print("📋 القوائم المنسدلة:")
            for field in report["dropdown_fields"]:
                field_info = analyzed_fields[field]
                options_count = len(field_info.options) if field_info.options else 0
                print(f"  - {field} ({options_count} خيار)")


# مثال على الاستخدام
def main():
    """مثال على كيفية استخدام المحلل"""

    # إنشاء المحلل
    analyzer = AirtableFieldAnalyzer()

    # تحليل جميع الحقول
    analyzed_fields = analyzer.analyze_all_fields("your_table_name")

    # طباعة ملخص التحليل
    analyzer.print_analysis_summary(analyzed_fields)

    # إنشاء تقرير مفصل
    detailed_report = analyzer.generate_detailed_report(analyzed_fields)

    # تصدير التكوين
    analyzer.export_configuration(analyzed_fields, "new_field_config.json")

    # الحصول على المجموعات الجديدة
    new_groups = analyzer.generate_field_groups_dict(analyzed_fields)
    new_types = analyzer.generate_field_types_dict(analyzed_fields)

    print("✅ تم الانتهاء من التحليل!")
    return analyzed_fields, new_groups, new_types


if __name__ == "__main__":
    main()