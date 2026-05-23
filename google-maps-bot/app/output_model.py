# app/output_model.py - نسخه نهایی (Canonical Schema)
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import re

@dataclass
class BusinessRecord:
    """
    مدل اصلی بیزینس - Single Source of Truth
    تمام تبدیل‌ها (DB → Excel → API) باید از روی این مدل انجام شوند
    """
    
    # ========== شناسه‌ها ==========
    business_id: int                          # شناسه داخلی دیتابیس
    query_text: str                           # عبارت جستجو
    place_id: Optional[str] = ""              # کلید یکتای گوگل مپ (برای upsert)
    slug: Optional[str] = ""                  # کلید یکتای جایگزین
    
    # ========== اطلاعات اصلی ==========
    name: str = ""                            # نام بیزینس
    
    # ========== اطلاعات تماس ==========
    phone_landline: Optional[str] = ""        # شماره ثابت
    phone_mobile: Optional[str] = ""          # شماره موبایل
    website: Optional[str] = ""               # وبسایت
    email: Optional[str] = ""                 # ایمیل (از وبسایت)
    extra_phones: str = ""                    # شماره‌های اضافی (comma separated)
    
    # ========== شبکه‌های اجتماعی ==========
    instagram: Optional[str] = ""
    telegram: Optional[str] = ""
    whatsapp: Optional[str] = ""
    
    # ========== اطلاعات مکان ==========
    province: Optional[str] = ""
    city: Optional[str] = ""
    address: Optional[str] = ""
    
    # ========== امتیازات گوگل ==========
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    hours: Optional[str] = ""
    
    # ========== کیفیت داده ==========
    quality_score: str = "medium"             # high / medium / low
    extraction_date: str = ""                 # تاریخ استخراج
    
    def __post_init__(self):
     if not self.extraction_date:
         self.extraction_date = datetime.now().isoformat()
    
     # محاسبه quality_score با وزن
     score = 0
     if self.phone_landline or self.phone_mobile:
         score += 1
     if self.website:
         score += 1
     if self.email:
         score += 2
     if self.instagram or self.telegram or self.whatsapp:
         score += 1
     if self.extra_phones:
         score += 1
     if self.rating and self.rating > 0:
         score += 1
    
     if score >= 5:
         self.quality_score = "high"
     elif score >= 3:
         self.quality_score = "medium"
     else:
         self.quality_score = "low"    
    # ========== متدهای کمکی ==========
    @staticmethod
    def clean_phone(phone: str) -> str:
        """پاکسازی شماره تلفن"""
        if not phone:
            return ""
        cleaned = re.sub(r'[^\d]', '', phone)
        if cleaned in ['00000000000', '0'] or len(cleaned) < 8:
            return ""
        return cleaned
    
    @staticmethod
    def clean_social(social: str) -> str:
        """پاکسازی لینک شبکه اجتماعی"""
        if not social:
            return ""
        social = re.sub(r'^https?://', '', social)
        social = re.sub(r'^www\.', '', social)
        return social.lower()
    
    # ========== تبدیل به فرمت‌های مختلف ==========
    def to_afrakala_payload(self) -> dict:
        """تبدیل به فرمت API افراکالا (مطابق مستندات)"""
        return {
            "name": self.name,
            "phone": self.clean_phone(self.phone_landline or self.phone_mobile or ""),
            "mobile_phone": self.clean_phone(self.phone_mobile or ""),
            "website": self.website,
            "address": self.address,
            "province": self.province,
            "city": self.city,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "place_id": self.place_id,
            "extracted_at": self.extraction_date,
            "meta_quality": self.quality_score,
            # اطلاعات اضافی از crawler
            "email": self.email,
            "instagram": self.clean_social(self.instagram),
            "telegram": self.clean_social(self.telegram),
            "whatsapp": self.clean_social(self.whatsapp),
            "extra_phones": self.extra_phones
        }
    
    def to_db_dict(self) -> dict:
        """تبدیل به دیکشنری برای ذخیره در دیتابیس"""
        return {
            "business_id": self.business_id,
            "query_text": self.query_text,
            "name": self.name,
            "phone_landline": self.phone_landline,
            "phone_mobile": self.phone_mobile,
            "website": self.website,
            "address": self.address,
            "province": self.province,
            "city": self.city,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "place_id": self.place_id,
            "slug": self.slug,
            "email": self.email,
            "instagram": self.instagram,
            "telegram": self.telegram,
            "whatsapp": self.whatsapp,
            "extra_phones": self.extra_phones,
            "quality_score": self.quality_score,
            "extraction_date": self.extraction_date
        }
    
    def to_excel_row(self) -> dict:
        """تبدیل به دیکشنری برای خروجی Excel"""
        return {
            "شناسه": self.business_id,
            "عبارت جستجو": self.query_text,
            "نام بیزینس": self.name,
            "شماره ثابت": self.clean_phone(self.phone_landline or ""),
            "شماره موبایل": self.clean_phone(self.phone_mobile or ""),
            "ایمیل": self.email,
            "وبسایت": self.website,
            "اینستاگرام": self.clean_social(self.instagram),
            "تلگرام": self.clean_social(self.telegram),
            "واتساپ": self.clean_social(self.whatsapp),
            "استان": self.province,
            "شهر": self.city,
            "آدرس": self.address,
            "امتیاز": self.rating,
            "تعداد نظرات": self.reviews_count,
            "کیفیت داده": self.quality_score,
            "تاریخ استخراج": self.extraction_date
        }