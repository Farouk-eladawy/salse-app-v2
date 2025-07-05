# ملف الإعداد لمحلل حقول Airtable
# ===================================

# خطوات الحصول على مفتاح API:
# 1. اذهب إلى https://airtable.com/create/tokens
# 2. أنشئ Personal Access Token جديد
# 3. اختر الصلاحيات: data.records:read و schema.bases:read
# 4. انسخ المفتاح وضعه أدناه

# مفتاح API (يبدأ بـ pat)
API_KEY = ' patopSdgeINdPJxiN.9a3cfcb6ab46ae14682af5c5b7c648dd3e7fc267a7882f49bc2ec702b7d32d5e '  # ضع مفتاحك الحقيقي هنا

# معرف القاعدة (تم تصحيحه - أزلت المسافات)
BASE_ID = 'appTp5YgSp9DV2HYc'

# اسم الجدول
TABLE_NAME = 'List'

# استيراد المحلل وتشغيله
from airtable_python_analyzer import AirtableFieldAnalyzer

def run_analysis():
    """تشغيل التحليل مع الإعدادات المصححة"""

    print("🚀 بدء تحليل حقول Airtable")
    print("=" * 50)

    # إنشاء المحلل
    analyzer = AirtableFieldAnalyzer(API_KEY, BASE_ID)

    # التحقق من صحة البيانات
    validation = analyzer.validate_credentials()

    if not all(validation.values()):
        print("\n❌ هناك مشاكل في الإعداد:")

        if not validation['api_key_format']:
            print("🔑 مفتاح API غير صحيح")
            print("💡 تأكد من:")
            print("   - أن المفتاح يبدأ بـ 'pat'")
            print("   - أن المفتاح مكتمل وصحيح")
            print("   - لم تنته صلاحيته")

        if not validation['base_id_format']:
            print("🗃️ معرف القاعدة غير صحيح")
            print("💡 تأكد من:")
            print("   - أن المعرف يبدأ بـ 'app'")
            print("   - أن طوله 17 حرف بالضبط")
            print("   - لا توجد مسافات إضافية")

        if not validation['connection_test']:
            print("🌐 فشل الاتصال")
            print("💡 تأكد من:")
            print("   - الاتصال بالإنترنت")
            print("   - صلاحية الوصول للقاعدة")

        return False

    print("\n✅ جميع الإعدادات صحيحة!")
    print("=" * 50)

    # تشغيل التحليل
    analyzer.print_analysis_report(TABLE_NAME)

    # تصدير النتائج
    field_mapping = analyzer.export_field_mapping(TABLE_NAME)

    if field_mapping and field_mapping.get('total_fields', 0) > 0:
        filename = f'{TABLE_NAME}_field_mapping.json'
        with open(filename, 'w', encoding='utf-8') as f:
            import json
            json.dump(field_mapping, f, ensure_ascii=False, indent=2)

        print(f"\n💾 تم حفظ خريطة الحقول في {filename}")

    return True

if __name__ == "__main__":
    # تحقق من الإعدادات أولاً
    if API_KEY == 'pat12345...':
        print("⚠️  يرجى تحديث مفتاح API في الملف أولاً!")
        print("📝 عدّل المتغير API_KEY وضع مفتاحك الحقيقي")
    else:
        run_analysis()