#!/usr/bin/env python3
import csv
import re
import sys
import time
from pathlib import Path

from deep_translator import GoogleTranslator

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "hushfeed")
src = repo / "extensions/tiktok/src/main/l10n/en.csv"
out = repo / "extensions/tiktok/src/main/l10n/ar.tsv"

# Curated translations for the most visible Hushfeed UI.
AR = {
    "About":"حول",
    "Activity":"النشاط",
    "Add":"إضافة",
    "Ads":"الإعلانات",
    "Advanced":"متقدم",
    "All":"الكل",
    "Allow screenshots and Circle to Search":"السماح بلقطات الشاشة وميزة Circle to Search",
    "Always show publish date":"إظهار تاريخ النشر دائمًا",
    "App":"التطبيق",
    "Appearance":"المظهر",
    "Apply":"تطبيق",
    "Audio":"الصوت",
    "Auto translate comments":"ترجمة التعليقات تلقائيًا",
    "Auto-advance":"الانتقال التلقائي",
    "Back":"رجوع",
    "Back up settings":"نسخ الإعدادات احتياطيًا",
    "Backup and restore":"النسخ الاحتياطي والاستعادة",
    "Block contact list access":"منع الوصول إلى جهات الاتصال",
    "Block installed app scanning":"منع فحص التطبيقات المثبتة",
    "Block location":"منع الموقع",
    "Blocked":"محظور",
    "Browse":"استعراض",
    "Cancel":"إلغاء",
    "Captions":"الترجمة النصية",
    "Comments":"التعليقات",
    "Copy":"نسخ",
    "Country":"الدولة",
    "Custom":"مخصص",
    "Default":"الافتراضي",
    "Diagnostics":"التشخيص",
    "Done":"تم",
    "Download":"تنزيل",
    "Downloads":"التنزيلات",
    "Download quality":"جودة التنزيل",
    "Download video":"تنزيل الفيديو",
    "Download audio":"تنزيل الصوت",
    "Download subtitles":"تنزيل الترجمة النصية",
    "Enable":"تفعيل",
    "Enabled":"مفعّل",
    "Disabled":"معطّل",
    "Feed filter":"تصفية الصفحة",
    "Feed screen":"واجهة الفيديو",
    "Feed tabs":"تبويبات الصفحة",
    "Feature Gate Lab":"مختبر ميزات TikTok",
    "Fix Google login":"إصلاح تسجيل الدخول بحساب Google",
    "Hide AI content":"إخفاء محتوى الذكاء الاصطناعي",
    "Hide ads":"إخفاء الإعلانات",
    "Hide livestreams":"إخفاء البث المباشر",
    "Hide photo posts":"إخفاء منشورات الصور",
    "Hide Shop":"إخفاء متجر TikTok",
    "Hide stories":"إخفاء القصص",
    "Hide suggested accounts":"إخفاء الحسابات المقترحة",
    "Hushfeed":"هاشفيد",
    "Hushfeed is active":"هاشفيد مفعّل",
    "Find a setting by name or description":"ابحث عن إعداد بالاسم أو الوصف",
    "What's new":"ما الجديد",
    "Changes in Hushfeed 0.64.0":"التغييرات في هاشفيد 0.64.0",
    "YOUR FEED":"صفحتك",
    "Choose what reaches your feed":"اختر ما يصل إلى صفحتك",
    "Arrange your feed and bottom tabs":"رتّب صفحتك والتبويبات السفلية",
    "Captions, gestures and on-screen controls":"الترجمات والإيماءات وأدوات التحكم على الشاشة",
    "Inbox":"صندوق الوارد",
    "Language":"اللغة",
    "Languages":"اللغات",
    "Low":"منخفض",
    "Medium":"متوسط",
    "High":"عالٍ",
    "Mute feed videos":"كتم فيديوهات الصفحة",
    "No results":"لا توجد نتائج",
    "None":"لا شيء",
    "Not interested":"غير مهتم",
    "Open external links directly":"فتح الروابط الخارجية مباشرة",
    "Pause Hushfeed":"إيقاف Hushfeed مؤقتًا",
    "Playback":"التشغيل",
    "Playback quality":"جودة التشغيل",
    "Playback speed":"سرعة التشغيل",
    "Privacy":"الخصوصية",
    "Region":"المنطقة",
    "Region preset":"إعداد منطقة جاهز",
    "Remove feed ads":"إزالة إعلانات الصفحة",
    "Reset":"إعادة ضبط",
    "Reset settings":"إعادة ضبط الإعدادات",
    "Restart":"إعادة التشغيل",
    "Restart required":"إعادة التشغيل مطلوبة",
    "Restore":"استعادة",
    "Restore settings":"استعادة الإعدادات",
    "Retry":"إعادة المحاولة",
    "Save":"حفظ",
    "Search":"بحث",
    "Search settings":"البحث في الإعدادات",
    "Screen time":"وقت الشاشة",
    "Settings":"الإعدادات",
    "Show seekbar":"إظهار شريط التقدم",
    "SIM spoof":"تغيير بيانات SIM",
    "Stop video looping":"إيقاف تكرار الفيديو",
    "Translate comments":"ترجمة التعليقات",
    "Turn Hushfeed back on":"إعادة تشغيل Hushfeed",
    "Undo":"تراجع",
    "Unblock":"إلغاء الحظر",
    "Use system font":"استخدام خط النظام",
    "Video":"الفيديو",
    "Video quality":"جودة الفيديو",
    "Watermark":"العلامة المائية",
    "Yes":"نعم",
}

PLACEHOLDER = re.compile(r"%(?:\d+\$)?[a-zA-Z]|%%")
BRAND_TOKENS = ["Hushfeed", "TikTok", "Google", "SIM", "JSON", "URL", "Android", "Circle to Search"]

def protect(text):
    tokens = []
    def sub(m):
        key = f"ZXPH{len(tokens)}XZ"
        tokens.append((key, m.group(0)))
        return key
    text = PLACEHOLDER.sub(sub, text)
    for brand in BRAND_TOKENS:
        if brand in text:
            key = f"ZXBR{len(tokens)}XZ"
            tokens.append((key, brand))
            text = text.replace(brand, key)
    return text, tokens

def restore(text, tokens):
    for key, value in tokens:
        text = text.replace(key, value)
    return text

def translate_one(translator, source):
    protected, tokens = protect(source)
    for attempt in range(4):
        try:
            result = translator.translate(protected)
            if not result:
                raise RuntimeError("empty translation")
            result = restore(result, tokens)
            # Ensure formatting placeholders are byte-for-byte preserved.
            if sorted(PLACEHOLDER.findall(source)) != sorted(PLACEHOLDER.findall(result)):
                raise RuntimeError(f"placeholder mismatch: {source!r} -> {result!r}")
            return result
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("unreachable")

with src.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

translator = GoogleTranslator(source="en", target="ar")
translated = {}
auto_count = 0

for index, row in enumerate(rows, 1):
    source = row["source"]
    if source in AR:
        target = AR[source]
    else:
        target = translate_one(translator, source)
        auto_count += 1
        if auto_count % 50 == 0:
            print(f"Auto-translated {auto_count} strings...", flush=True)
    translated[source] = target

lines = ["# Arabic translation for Hushfeed 0.64.0 — full Arabic"]
for row in rows:
    source = row["source"]
    target = translated[source]
    source = source.replace("\t", " ").replace("\n", "\\n")
    target = target.replace("\t", " ").replace("\n", "\\n")
    lines.append(source + "\t" + target)

out.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Fail the build if ordinary Latin-only UI strings were silently left untranslated.
latin_only = []
for source, target in translated.items():
    has_letters = re.search(r"[A-Za-z]", target)
    has_arabic = re.search(r"[\u0600-\u06FF]", target)
    if has_letters and not has_arabic and target == source and source not in BRAND_TOKENS:
        latin_only.append(source)

print(f"Wrote {out}: {len(rows)} entries; {len(AR)} curated keys; {auto_count} machine-translated.")
print(f"Unchanged Latin-only strings: {len(latin_only)}")
if len(latin_only) > 15:
    print("Examples:", latin_only[:15])
    sys.exit("Too many untranslated Latin-only strings remain")
