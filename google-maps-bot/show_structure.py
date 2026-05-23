# show_structure.py - نسخه کامل بدون حذف فایل‌ها
#use python show_structure.py | Out-File -FilePath project_structure.txt -Encoding UTF8
import os
from pathlib import Path

def show_structure(base_path='.', indent=0, max_depth=4, show_all=True):
    """نمایش ساختار پوشه‌ها به صورت درختی"""
    if indent > max_depth:
        return
    
    try:
        items = sorted(Path(base_path).iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        return
    
    for item in items:
        # فقط پوشه‌ها و فایل‌های پایتون را نشان بده
        if item.is_dir():
            # پوشه‌های خاص را حذف نکن
            prefix = '    ' * indent
            print(f"{prefix}📁 {item.name}/")
            show_structure(item, indent + 1, max_depth, show_all)
        elif item.suffix == '.py':
            prefix = '    ' * indent
            print(f"{prefix}📄 {item.name}")
        elif show_all and item.suffix in ['.json', '.xlsx', '.db', '.txt', '.md']:
            prefix = '    ' * indent
            print(f"{prefix}📄 {item.name}")

def show_file_content(file_path):
    """نمایش محتوای یک فایل"""
    if not os.path.exists(file_path):
        print(f"❌ فایل پیدا نشد: {file_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"📄 {file_path}")
    print('='*70)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # نمایش حداکثر 200 خط (برای جلوگیری از زیاد شدن خروجی)
        max_lines = 200
        total_lines = len(lines)
        
        for i, line in enumerate(lines[:max_lines], 1):
            # حذف کاراکترهای خاص از انتهای خط
            clean_line = line.rstrip('\n\r')
            print(f"{i:4d} | {clean_line}")
        
        if total_lines > max_lines:
            print(f"\n     ... ({total_lines - max_lines} lines skipped) ...")
            
    except Exception as e:
        print(f"⚠️ خطا در خواندن فایل: {e}")

def show_all_files_content(base_path='.', max_depth=3):
    """نمایش محتوای همه فایل‌های پایتون"""
    py_files = []
    other_files = []
    
    for root, dirs, files in os.walk(base_path):
        # محاسبه عمق پوشه
        depth = root.replace(base_path, '').count(os.sep)
        if depth > max_depth:
            continue
        
        # حذف پوشه‌هایی که نمی‌خواهیم وارد شویم
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.vscode', 'logs', 'screenshots', 'checkpoints']]
        
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.py'):
                py_files.append(file_path)
            elif file.endswith('.json') and 'temp' not in file:
                other_files.append(file_path)
    
    # نمایش فایل‌های پایتون
    print("\n" + "="*70)
    print("📄 فایل‌های پایتون:")
    print("="*70)
    
    for file_path in sorted(py_files):
        show_file_content(file_path)
    
    # نمایش فایل‌های JSON مهم (اختیاری)
    if other_files:
        print("\n" + "="*70)
        print("📄 فایل‌های JSON مهم:")
        print("="*70)
        for file_path in sorted(other_files):
            if 'phase3_output' in file_path or 'phase4_result' in file_path or 'final_output' in file_path:
                show_file_content(file_path)

def show_full_structure():
    """نمایش کامل ساختار و محتوا"""
    print("="*70)
    print("📁 Google Maps Scraper - کاملترین نمایش ساختار")
    print("="*70)
    
    # نمایش ساختار پوشه‌ها
    print("\n📁 ساختار پروژه:")
    print("-"*50)
    show_structure('.', max_depth=3, show_all=False)
    
    # نمایش فایل‌های پیکربندی مهم
    print("\n\n📋 فایل‌های مهم خارج از پوشه app:")
    print("-"*50)
    
    important_files = ['run.py', 'requirements.txt', 'show_structure.py']
    for file in important_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (ندارد)")
    
    # نمایش همه محتوای فایل‌های پایتون
    show_all_files_content('.', max_depth=2)
    
    print("\n" + "="*70)
    print("✅ نمایش کامل ساختار به پایان رسید")
    print("="*70)

if __name__ == "__main__":
    # ذخیره خروجی در فایل
    import sys
    
    # اگر آرگومان --save داده شد، خروجی را در فایل ذخیره کن
    if '--save' in sys.argv:
        output_file = 'project_structure_full.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            # ذخیره stdout اصلی
            original_stdout = sys.stdout
            sys.stdout = f
            show_full_structure()
            sys.stdout = original_stdout
        print(f"✅ خروجی در فایل {output_file} ذخیره شد")
    else:
        show_full_structure()