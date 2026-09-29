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

PLACEHOLDER = re.compile(r"%(?:\\d+\\$)?[a-zA-Z]|%%")
BRANDS = ["Circle to Search", "Hushfeed", "TikTok", "Android", "Google", "SIM", "JSON", "URL"]
PROTECTED = re.compile(
    "(" + PLACEHOLDER.pattern + "|" + "|".join(re.escape(x) for x in sorted(BRANDS, key=len, reverse=True)) + ")"
)

def split_for_translation(source):
    """Return literal/protected parts and translatable text parts without ever feeding protected tokens to MT."""
    parts = []
    for piece in PROTECTED.split(source):
        if not piece:
            continue
        if PROTECTED.fullmatch(piece):
            parts.append(("literal", piece))
            continue
        # Preserve surrounding whitespace exactly; translate only the human-language core.
        m = re.match(r"^(\\s*)(.*?)(\\s*)$", piece, flags=re.S)
        lead, core, tail = m.groups()
        if lead:
            parts.append(("literal", lead))
        if core:
            parts.append(("text", core))
        if tail:
            parts.append(("literal", tail))
    return parts

with src.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

model_name = "Helsinki-NLP/opus-mt-en-ar"
print("Loading offline translation model:", model_name, flush=True)
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)
model.eval()

translated = dict(AR)
parts_by_source = {}
unique_texts = []
seen_texts = set()

for row in rows:
    source = row["source"]
    if source in translated:
        continue
    parts = split_for_translation(source)
    parts_by_source[source] = parts
    for kind, value in parts:
        if kind == "text" and value not in seen_texts:
            seen_texts.add(value)
            unique_texts.append(value)

print(f"Unique translatable fragments: {len(unique_texts)}", flush=True)

fragment_translation = {}
BATCH = 16
for start_at in range(0, len(unique_texts), BATCH):
    batch = unique_texts[start_at:start_at+BATCH]
    encoded = tokenizer(
        batch,
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
    for source_fragment, target_fragment in zip(batch, outputs):
        fragment_translation[source_fragment] = target_fragment.strip()
    print(f"Translated fragments {min(start_at+BATCH, len(unique_texts))}/{len(unique_texts)}", flush=True)

for source, parts in parts_by_source.items():
    rebuilt = []
    for kind, value in parts:
        rebuilt.append(value if kind == "literal" else fragment_translation[value])
    target = "".join(rebuilt).strip()

    wanted = sorted(PLACEHOLDER.findall(source))
    got = sorted(PLACEHOLDER.findall(target))
    if wanted != got:
        raise SystemExit(f"Placeholder mismatch: {source!r} -> {target!r}: {wanted} != {got}")

    # Protected product/brand tokens that occur in the source must survive literally.
    for brand in BRANDS:
        if brand in source and brand not in target:
            raise SystemExit(f"Protected token lost: {brand!r}: {source!r} -> {target!r}")

    translated[source] = target

# Coverage checks before generating ar.tsv.
missing = [row["source"] for row in rows if row["source"] not in translated]
if missing:
    raise SystemExit(f"Missing translations: {len(missing)}; examples: {missing[:10]}")

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

print(f"Wrote {out}: {len(rows)} entries, {len(AR)} curated, {len(rows)-len(AR)} offline-translated.")
print(f"Unchanged ordinary Latin strings: {len(unchanged)}")
if unchanged:
    print("Examples:", unchanged[:20])
if len(unchanged) > 20:
    raise SystemExit("Too many untranslated Latin strings remain")
