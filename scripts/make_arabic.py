#!/usr/bin/env python3
import csv
import re
import sys
from pathlib import Path

import torch
from transformers import MarianMTModel, MarianTokenizer

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "hushfeed")
src = repo / "extensions/tiktok/src/main/l10n/en.csv"
out = repo / "extensions/tiktok/src/main/l10n/ar.tsv"

# Human-curated translations for the most visible Hushfeed UI.
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
BRANDS = ["Hushfeed", "TikTok", "Google", "SIM", "JSON", "URL", "Android", "Circle to Search"]

def protect(text):
    items = []
    def ph(m):
        token = f"ZXPH{len(items)}XZ"
        items.append((token, m.group(0)))
        return token
    text = PLACEHOLDER.sub(ph, text)
    for brand in BRANDS:
        if brand in text:
            token = f"ZXBR{len(items)}XZ"
            items.append((token, brand))
            text = text.replace(brand, token)
    return text, items

def restore(text, items):
    for token, value in items:
        # Marian can add spaces around synthetic tokens.
        text = re.sub(r"\\s*"+re.escape(token)+r"\\s*", value, text)
    return text.strip()

with src.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

model_name = "Helsinki-NLP/opus-mt-en-ar"
print("Loading offline translation model:", model_name, flush=True)
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)
model.eval()

pending = []
protected_meta = {}
translated = dict(AR)

for row in rows:
    source = row["source"]
    if source in translated:
        continue
    text, meta = protect(source)
    pending.append((source, text))
    protected_meta[source] = meta

BATCH = 12
for start in range(0, len(pending), BATCH):
    batch = pending[start:start+BATCH]
    texts = [x[1] for x in batch]
    encoded = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            max_new_tokens=512,
            num_beams=3,
            early_stopping=True,
        )
    outputs = tokenizer.batch_decode(generated, skip_special_tokens=True)
    for (source, _), target in zip(batch, outputs):
        target = restore(target, protected_meta[source])
        wanted = sorted(PLACEHOLDER.findall(source))
        got = sorted(PLACEHOLDER.findall(target))
        if wanted != got:
            raise SystemExit(f"Placeholder mismatch: {source!r} -> {target!r}: {wanted} != {got}")
        translated[source] = target
    print(f"Translated {min(start+BATCH, len(pending))}/{len(pending)} non-curated strings", flush=True)

lines = ["# Arabic translation for Hushfeed 0.64.0 — full static Arabic"]
for row in rows:
    source = row["source"]
    target = translated[source]
    s = source.replace("\t", " ").replace("\n", "\\n")
    t = target.replace("\t", " ").replace("\n", "\\n")
    lines.append(s + "\t" + t)

out.write_text("\n".join(lines) + "\n", encoding="utf-8")

unchanged = []
for source, target in translated.items():
    if target == source and re.search(r"[A-Za-z]", source) and not re.search(r"[\\u0600-\\u06FF]", target):
        # Brand-only / format-only strings are okay; ordinary UI strings are not.
        stripped = source
        for b in BRANDS:
            stripped = stripped.replace(b, "")
        stripped = PLACEHOLDER.sub("", stripped)
        if re.search(r"[A-Za-z]{2,}", stripped):
            unchanged.append(source)

print(f"Wrote {out}: {len(rows)} entries, {len(AR)} curated, {len(pending)} offline-translated.")
print(f"Unchanged ordinary Latin strings: {len(unchanged)}")
if unchanged:
    print("Examples:", unchanged[:20])
if len(unchanged) > 20:
    raise SystemExit("Too many untranslated Latin strings remain")
