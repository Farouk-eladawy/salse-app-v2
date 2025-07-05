"""
محلل حقول Airtable المتقدم
============================

هذا السكريبت يحلل جميع حقول جدول محدد في Airtable ويصنفها إلى مجموعات منطقية.

متطلبات الإعداد:
1. مفتاح API من Airtable (يبدأ بـ pat)
2. معرف القاعدة (يبدأ بـ app)
3. اسم الجدول

خطوات الحصول على مفتاح API:
1. اذهب إلى https://airtable.com/create/tokens
2. أنشئ Personal Access Token جديد
3. اختر الصلاحيات المطلوبة (data.records:read و schema.bases:read)
4. انسخ المفتاح واستخدمه في الكود

خطوات الحصول على معرف القاعدة:
1. افتح قاعدة البيانات في Airtable
2. انسخ الجزء الذي يبدأ بـ app من الرابط
3. مثال: https://airtable.com/appXXXXXXXXXXXXXX/...

استخدام السكريبت:
1. عدّل القيم في دالة main()
2. شغّل السكريبت
3. ستحصل على تقرير مفصل وملف JSON
"""

import requests
import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class FieldInfo:
    name: str
    field_type: str
    description: str
    options: Any
    logical_group: str

class AirtableFieldAnalyzer:
    def __init__(self, api_key: str, base_id: str):
        # تنظيف وتحقق من المعرفات
        self.api_key = api_key.strip()
        self.base_id = self.extract_base_id(base_id.strip())

        # التحقق من صحة المعرفات
        if not self.api_key.startswith('pat'):
            print(f"⚠️  تحذير: مفتاح API يجب أن يبدأ بـ 'pat', القيمة الحالية: {self.api_key[:10]}...")

        if not self.base_id.startswith('app'):
            print(f"⚠️  تحذير: معرف القاعدة يجب أن يبدأ بـ 'app', القيمة الحالية: {self.base_id}")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # تعريف المجموعات المنطقية
        self.field_groups = {
            'معلومات_أساسية': [
                'singleLineText', 'email', 'url', 'phoneNumber'
            ],
            'نصوص_ووصف': [
                'multilineText', 'richText'
            ],
            'أرقام_وحسابات': [
                'number', 'currency', 'percent', 'duration',
                'rating', 'formula', 'rollup', 'count', 'autoNumber'
            ],
            'تواريخ_وأوقات': [
                'date', 'dateTime', 'createdTime', 'lastModifiedTime'
            ],
            'خيارات_ومراجع': [
                'singleSelect', 'multipleSelects', 'singleCollaborator',
                'multipleCollaborators', 'multipleRecordLinks', 'lookup',
                'createdBy', 'lastModifiedBy'
            ],
            'مرفقات_ووسائط': [
                'multipleAttachments', 'barcode'
            ],
            'أخرى': [
                'checkbox', 'button'
            ]
        }

        print(f"🔧 إعداد المحلل:")
        print(f"   - مفتاح API: {self.api_key[:10]}...")
        print(f"   - معرف القاعدة: {self.base_id}")
        print(f"   - URL الأساسي: https://api.airtable.com/v0/meta/bases/{self.base_id}/tables")

    def extract_base_id(self, input_str: str) -> str:
        """استخراج معرف القاعدة من URL أو نص"""
        # إذا كان المدخل URL كامل
        if 'airtable.com' in input_str:
            match = re.search(r'/(app[a-zA-Z0-9]{14})/', input_str)
            if match:
                return match.group(1)

        # إذا كان معرف مباشر
        if input_str.startswith('app') and len(input_str) == 17:
            return input_str

        return input_str

        # تعريف المجموعات المنطقية
        self.field_groups = {
            'معلومات_أساسية': [
                'singleLineText', 'email', 'url', 'phoneNumber'
            ],
            'نصوص_ووصف': [
                'multilineText', 'richText'
            ],
            'أرقام_وحسابات': [
                'number', 'currency', 'percent', 'duration',
                'rating', 'formula', 'rollup', 'count', 'autoNumber'
            ],
            'تواريخ_وأوقات': [
                'date', 'dateTime', 'createdTime', 'lastModifiedTime'
            ],
            'خيارات_ومراجع': [
                'singleSelect', 'multipleSelects', 'singleCollaborator',
                'multipleCollaborators', 'multipleRecordLinks', 'lookup',
                'createdBy', 'lastModifiedBy'
            ],
            'مرفقات_ووسائط': [
                'multipleAttachments', 'barcode'
            ],
            'أخرى': [
                'checkbox', 'button'
            ]
        }

    def get_table_schema(self, table_name: str) -> Dict:
        """جلب schema الجدول"""
        url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables'

        print(f"🌐 محاولة الاتصال بـ: {url}")

        try:
            response = requests.get(url, headers=self.headers)

            # طباعة تفاصيل الاستجابة للتشخيص
            print(f"📡 كود الاستجابة: {response.status_code}")

            if response.status_code == 401:
                print("❌ خطأ 401: مفتاح API غير صحيح أو منتهي الصلاحية")
                print("💡 تأكد من:")
                print("   - صحة مفتاح API")
                print("   - أن المفتاح يبدأ بـ 'pat'")
                print("   - أن المفتاح لم تنته صلاحيته")
                return None

            elif response.status_code == 404:
                print("❌ خطأ 404: لم يتم العثور على القاعدة")
                print("💡 تأكد من:")
                print("   - صحة معرف القاعدة")
                print("   - أن المعرف يبدأ بـ 'app'")
                print("   - أن لديك صلاحية الوصول للقاعدة")
                return None

            elif response.status_code == 403:
                print("❌ خطأ 403: ليس لديك صلاحية للوصول")
                print("💡 تأكد من أن لديك صلاحية قراءة القاعدة")
                return None

            response.raise_for_status()

            data = response.json()
            print(f"✅ تم جلب معلومات {len(data.get('tables', []))} جدول")

            # طباعة أسماء الجداول المتاحة
            available_tables = [table['name'] for table in data.get('tables', [])]
            print(f"📋 الجداول المتاحة: {', '.join(available_tables)}")

            # البحث عن الجدول المطلوب
            for table in data.get('tables', []):
                if table['name'] == table_name:
                    print(f"✅ تم العثور على جدول '{table_name}'")
                    return table

            print(f"❌ لم يتم العثور على جدول '{table_name}'")
            print(f"💡 الجداول المتاحة: {', '.join(available_tables)}")
            return None

        except requests.exceptions.RequestException as e:
            print(f'❌ خطأ في الاتصال بـ Airtable: {e}')
            if hasattr(e, 'response') and e.response is not None:
                print(f"📄 محتوى الاستجابة: {e.response.text}")
            return None

    def categorize_field_type(self, field_type: str) -> str:
        """تصنيف نوع الحقل إلى مجموعة منطقية"""
        for group_name, field_types in self.field_groups.items():
            if field_type in field_types:
                return group_name
        return 'أخرى'

    def analyze_table_fields(self, table_name: str) -> Dict[str, List[FieldInfo]]:
        """تحليل جميع حقول الجدول"""
        table_schema = self.get_table_schema(table_name)

        if not table_schema:
            return {}

        # تجميع الحقول حسب المجموعة المنطقية
        grouped_fields = {}

        for field in table_schema.get('fields', []):
            field_info = FieldInfo(
                name=field['name'],
                field_type=field['type'],
                description=field.get('description', 'لا يوجد وصف'),
                options=field.get('options'),
                logical_group=self.categorize_field_type(field['type'])
            )

            group = field_info.logical_group
            if group not in grouped_fields:
                grouped_fields[group] = []

            grouped_fields[group].append(field_info)

        return grouped_fields

    def get_sample_record(self, table_name: str, record_id: str = None) -> Dict:
        """جلب سجل عينة من الجدول"""
        if record_id:
            url = f'https://api.airtable.com/v0/{self.base_id}/{table_name}/{record_id}'
        else:
            url = f'https://api.airtable.com/v0/{self.base_id}/{table_name}?maxRecords=1'

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            if record_id:
                return data.get('fields', {})
            else:
                records = data.get('records', [])
                return records[0].get('fields', {}) if records else {}

        except requests.exceptions.RequestException as e:
            print(f'خطأ في جلب السجل: {e}')
            return {}

    def print_analysis_report(self, table_name: str, record_id: str = None):
        """طباعة تقرير شامل عن حقول الجدول"""
        print(f"🔍 تحليل شامل لجدول '{table_name}' في Airtable")
        print("=" * 60)

        # تحليل الحقول
        grouped_fields = self.analyze_table_fields(table_name)

        if not grouped_fields:
            print("❌ فشل في جلب معلومات الجدول")
            return

        # عرض الحقول حسب المجموعة
        total_fields = sum(len(fields) for fields in grouped_fields.values())
        print(f"\n📊 إجمالي الحقول: {total_fields}")
        print("-" * 40)

        for group_name, fields in grouped_fields.items():
            if fields:
                print(f"\n📂 {group_name.replace('_', ' ')} ({len(fields)} حقل)")
                print("-" * 30)

                for i, field in enumerate(fields, 1):
                    print(f"{i}. {field.name}")
                    print(f"   النوع: {field.field_type}")
                    print(f"   الوصف: {field.description}")

                    if field.options:
                        print(f"   خيارات: {json.dumps(field.options, ensure_ascii=False, indent=6)}")
                    print()

        # عرض مثال على سجل
        print("\n📋 مثال على سجل من الجدول:")
        print("=" * 40)

        sample_record = self.get_sample_record(table_name, record_id)

        if sample_record:
            for field_name, value in sample_record.items():
                print(f"{field_name}: {json.dumps(value, ensure_ascii=False, indent=2)}")
        else:
            print("لا توجد سجلات في الجدول أو فشل في جلبها")

    def export_field_mapping(self, table_name: str) -> Dict:
        """تصدير خريطة كاملة للحقول"""
        grouped_fields = self.analyze_table_fields(table_name)

        field_mapping = {
            'table_name': table_name,
            'total_fields': sum(len(fields) for fields in grouped_fields.values()),
            'groups': {}
        }

        for group_name, fields in grouped_fields.items():
            field_mapping['groups'][group_name] = [
                {
                    'name': field.name,
                    'type': field.field_type,
                    'description': field.description,
                    'has_options': field.options is not None
                }
                for field in fields
            ]

    def test_connection(self) -> bool:
        """اختبار الاتصال بـ Airtable"""
        print("🔍 اختبار الاتصال بـ Airtable...")

        url = f'https://api.airtable.com/v0/meta/bases/{self.base_id}/tables'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                tables_count = len(data.get('tables', []))
                print(f"✅ الاتصال ناجح! تم العثور على {tables_count} جدول")
                return True
            else:
                print(f"❌ فشل الاتصال: كود الخطأ {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            print("❌ انتهت مهلة الاتصال")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في الشبكة: {e}")
            return False

    def validate_credentials(self) -> Dict[str, bool]:
        """التحقق من صحة البيانات"""
        validation = {
            'api_key_format': self.api_key.startswith('pat') and len(self.api_key) > 10,
            'base_id_format': self.base_id.startswith('app') and len(self.base_id) == 17,
            'connection_test': False
        }

        print("🔍 التحقق من صحة البيانات...")

        if not validation['api_key_format']:
            print("❌ تنسيق مفتاح API غير صحيح")
            print("💡 يجب أن يبدأ بـ 'pat' ويكون أطول من 10 أحرف")
        else:
            print("✅ تنسيق مفتاح API صحيح")

        if not validation['base_id_format']:
            print("❌ تنسيق معرف القاعدة غير صحيح")
            print("💡 يجب أن يبدأ بـ 'app' ويكون طوله 17 حرف بالضبط")
        else:
            print("✅ تنسيق معرف القاعدة صحيح")

        if validation['api_key_format'] and validation['base_id_format']:
            validation['connection_test'] = self.test_connection()

        return validation

# مثال على الاستخدام
def main():
    print("🚀 محلل حقول Airtable")
    print("=" * 50)

    # إعداد المحلل - قم بتعديل هذه القيم
    API_KEY = 'your_api_key_here'  # ضع مفتاح API الخاص بك هنا
    BASE_ID = 'appTp5YgSp9DV2HYc'  # أزلت المسافات الإضافية
    TABLE_NAME = 'List'

    # إنشاء المحلل
    analyzer = AirtableFieldAnalyzer(API_KEY, BASE_ID)

    # التحقق من صحة البيانات أولاً
    validation = analyzer.validate_credentials()

    if not all(validation.values()):
        print("\n❌ هناك مشاكل في الإعداد. يرجى إصلاحها والمحاولة مرة أخرى.")
        print("\n📝 خطوات الإصلاح:")
        print("1. تأكد من مفتاح API صحيح ويبدأ بـ 'pat'")
        print("2. تأكد من معرف القاعدة صحيح ويبدأ بـ 'app'")
        print("3. تأكد من أن لديك صلاحية الوصول للقاعدة")
        return

    print("\n" + "=" * 50)

    # تشغيل التحليل الشامل
    analyzer.print_analysis_report(TABLE_NAME)

    # تصدير خريطة الحقول
    field_mapping = analyzer.export_field_mapping(TABLE_NAME)

    if field_mapping and field_mapping.get('total_fields', 0) > 0:
        # حفظ النتائج في ملف JSON
        filename = f'{TABLE_NAME}_field_mapping.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(field_mapping, f, ensure_ascii=False, indent=2)

        print(f"\n💾 تم حفظ خريطة الحقول في {filename}")
    else:
        print(f"\n❌ لم يتم العثور على حقول في جدول {TABLE_NAME}")

def interactive_setup():
    """إعداد تفاعلي للمحلل"""
    print("🔧 إعداد محلل حقول Airtable")
    print("=" * 40)

    # الحصول على البيانات من المستخدم
    api_key = input("أدخل مفتاح API (يبدأ بـ pat): ").strip()
    base_id = input("أدخل معرف القاعدة (يبدأ بـ app): ").strip()
    table_name = input("أدخل اسم الجدول [List]: ").strip() or "List"

    # إنشاء المحلل
    analyzer = AirtableFieldAnalyzer(api_key, base_id)

    # التحقق من صحة البيانات
    validation = analyzer.validate_credentials()

    if not all(validation.values()):
        print("\n❌ هناك مشاكل في البيانات المدخلة")
        return None

    # تشغيل التحليل
    analyzer.print_analysis_report(table_name)

    return analyzer

if __name__ == "__main__":
    # يمكنك اختيار أحد الخيارين:

    # الخيار 1: استخدام القيم المثبتة في الكود
    main()

    # الخيار 2: الإعداد التفاعلي (قم بإلغاء التعليق لاستخدامه)
    # interactive_setup()