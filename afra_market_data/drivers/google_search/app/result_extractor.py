# app/result_extractor.py - Phase 2
# پردازش عمیق snippet برای استخراج اطلاعات تماس

import re
from typing import Dict, List

# نگاشت اعداد فارسی/عربی به ASCII
PERSIAN_DIGITS = str.maketrans(
    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
    '01234567890123456789'
)

# پترن‌های تلفن ایرانی — از دقیق‌ترین به کلی‌ترین
PHONE_PATTERNS = [
    re.compile(r'\+98[\s\-]?\d{10}'),          # +98xxxxxxxxxx
    re.compile(r'09[0-9]{9}'),                  # موبایل 09x
    re.compile(r'0?21[\s\-]?\d{8}'),            # تهران 021
    re.compile(r'0[1-9]\d{1,2}[\s\-]\d{7,8}'), # استان‌ها با dash
    re.compile(r'0[1-9]\d{9}'),                 # 11 رقم بدون dash
]

PROVINCES = [
    'تهران', 'اصفهان', 'فارس', 'خراسان رضوی', 'آذربایجان شرقی',
    'آذربایجان غربی', 'کرمان', 'مازندران', 'گیلان', 'البرز',
    'همدان', 'کرمانشاه', 'خوزستان', 'لرستان', 'مرکزی',
    'قم', 'قزوین', 'زنجان', 'سمنان', 'گلستان', 'اردبیل',
    'بوشهر', 'چهارمحال و بختیاری', 'کهگیلویه و بویراحمد',
    'خراسان شمالی', 'خراسان جنوبی', 'سیستان و بلوچستان',
    'هرمزگان', 'ایلام', 'کردستان', 'یزد',
]

MAJOR_CITIES = [
    'تهران', 'مشهد', 'اصفهان', 'شیراز', 'تبریز', 'کرج', 'اهواز',
    'قم', 'رشت', 'ارومیه', 'زاهدان', 'همدان', 'کرمانشاه', 'کرمان',
    'اراک', 'یزد', 'اردبیل', 'قزوین', 'زنجان', 'سنندج', 'بندرعباس',
    'ساری', 'گرگان', 'بیرجند', 'شهرکرد', 'ایلام', 'یاسوج', 'بجنورد',
    'سمنان', 'خرم‌آباد', 'بوشهر', 'اسلامشهر',
]

# suffix های زائد در عنوان گوگل
NAME_SUFFIX_RE = re.compile(
    r'\s*[\|\-–]\s*(?:سایت رسمی|وبسایت رسمی|وب سایت|خرید آنلاین|'
    r'فروشگاه اینترنتی|نمایندگی رسمی|صفحه اصلی).*$'
)


class ResultExtractor:
    """
    ورودی:  business dict (name, result_snippet, city, province, phone)
    خروجی: همان dict غنی‌شده — بدون دسترسی DB یا browser
    """

    def enrich(self, business: Dict) -> Dict:
        result = dict(business)

        snippet = self._normalize(result.get('result_snippet', '') or '')
        name    = self._normalize(result.get('name', '') or '')
        full_text = snippet + ' ' + name

        # ۱. پاکسازی نام
        result['name'] = self._clean_name(name)

        # ۲. همه شماره‌ها
        all_phones = self._extract_all_phones(full_text)
        if all_phones:
            mobile   = next((p for p in all_phones if p.startswith('09')), None)
            landline = next((p for p in all_phones if not p.startswith('09')), None)

            # phone اصلی: اگه خالیه پر کن
            if not result.get('phone'):
                result['phone'] = mobile or landline or ''

            # extra_phones: بقیه (حداکثر 5)
            extra = [p for p in all_phones if p != result.get('phone', '')]
            result['extra_phones'] = ','.join(extra[:5])

        # ۳. استان/شهر اگه خالیه
        if not result.get('province'):
            result['province'] = self._detect_province(snippet)
        if not result.get('city'):
            result['city'] = self._detect_city(snippet)

        return result

    def enrich_batch(self, businesses: List[Dict]) -> List[Dict]:
        return [self.enrich(b) for b in businesses]

    # ----------------------------------------------------------

    def _normalize(self, text: str) -> str:
        """فارسی/عربی digit → ASCII"""
        return text.translate(PERSIAN_DIGITS)

    def _clean_name(self, name: str) -> str:
        return NAME_SUFFIX_RE.sub('', name).strip()

    def _extract_all_phones(self, text: str) -> List[str]:
        """همه شماره‌های ایرانی را بدون تکرار برمی‌گرداند"""
        found: List[str] = []
        seen: set = set()
        for pattern in PHONE_PATTERNS:
            for m in pattern.finditer(text):
                raw = re.sub(r'[\s\-]', '', m.group())
                if raw.startswith('+98'):
                    raw = '0' + raw[3:]
                if raw not in seen and 10 <= len(raw) <= 12:
                    seen.add(raw)
                    found.append(raw)
        return found

    def _detect_province(self, text: str) -> str:
        for p in PROVINCES:
            if p in text:
                return p
        return ''

    def _detect_city(self, text: str) -> str:
        for c in MAJOR_CITIES:
            if c in text:
                return c
        return ''
