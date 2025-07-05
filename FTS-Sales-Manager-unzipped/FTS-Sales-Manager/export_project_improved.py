import os
import datetime

output_file = f"project_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# المجلدات المستثناة
EXCLUDED_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.idea', '.vscode'}
# الامتدادات المستثناة
EXCLUDED_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', '.exe'}

with open(output_file, 'w', encoding='utf-8') as out:
    # كتابة هيكل المشروع
    out.write("=" * 80 + "\n")
    out.write("PROJECT STRUCTURE\n")
    out.write("=" * 80 + "\n\n")

    # طريقة محسنة لرسم الشجرة
    for root, dirs, files in os.walk('.'):
        # استثناء المجلدات غير المرغوبة
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        # حساب المستوى بشكل صحيح
        if root == '.':
            level = 0
            display_path = 'PROJECT_ROOT/'
        else:
            # إزالة ./ أو .\ من البداية
            relative_path = os.path.relpath(root, '.')
            level = relative_path.count(os.sep) + 1
            display_path = relative_path.replace(os.sep, '/') + '/'

        # رسم المسار الهرمي
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
        out.write(f'{indent}{display_path}\n')

        # رسم الملفات
        for i, file in enumerate(files):
            # استثناء الملفات المخفية والملفات المترجمة
            if file.startswith('.') or any(file.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
                continue

            # تحديد الرمز المناسب (آخر ملف أم لا)
            is_last = (i == len(files) - 1) and not dirs
            file_indent = '│   ' * level + ('└── ' if is_last else '├── ')
            out.write(f'{file_indent}{file}\n')

    # كتابة محتوى الملفات
    out.write("\n" + "=" * 80 + "\n")
    out.write("FILE CONTENTS\n")
    out.write("=" * 80 + "\n")

    # امتدادات الملفات المراد قراءتها
    READ_EXTENSIONS = {'.py', '.json', '.txt', '.md', '.yml', '.yaml', '.js', '.html', '.css',
                      '.jsx', '.tsx', '.ts', '.vue', '.sql', '.sh', '.bat', '.env.example'}

    files_read = 0
    errors = []

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            # التحقق من الامتداد
            if any(file.endswith(ext) for ext in READ_EXTENSIONS):
                filepath = os.path.join(root, file)
                relative_path = os.path.relpath(filepath, '.')

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    out.write(f"\n\n{'='*60}\n")
                    out.write(f"FILE: {relative_path}\n")
                    out.write(f"SIZE: {len(content)} characters\n")
                    out.write(f"{'='*60}\n\n")
                    out.write(content)
                    files_read += 1

                except Exception as e:
                    error_msg = f"Error reading {relative_path}: {e}"
                    out.write(f"\n\n{'='*60}\n")
                    out.write(f"ERROR: {error_msg}\n")
                    out.write(f"{'='*60}\n")
                    errors.append(error_msg)

    # ملخص التصدير
    out.write(f"\n\n{'='*80}\n")
    out.write("EXPORT SUMMARY\n")
    out.write(f"{'='*80}\n")
    out.write(f"Total files read: {files_read}\n")
    out.write(f"Errors encountered: {len(errors)}\n")
    out.write(f"Export date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if errors:
        out.write("\nErrors details:\n")
        for error in errors:
            out.write(f"  - {error}\n")

print(f"✅ تم تصدير المشروع إلى: {output_file}")
print(f"📁 عدد الملفات المقروءة: {files_read}")
if errors:
    print(f"⚠️  عدد الأخطاء: {len(errors)}")