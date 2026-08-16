#!/usr/bin/env python3
"""
EHS website builder.
Assembles the bilingual static site from shared templates + per-page content.

  content/en/<slug>.html  ->  ../<slug>.html        (English, LTR)
  content/ar/<slug>.html  ->  ../ar/<slug>.html     (Arabic, RTL)

Placeholders available inside content files:
  {{A}}            -> asset path prefix ("assets" or "../assets")
  {{WA_NUMBER}}    -> WhatsApp number, digits only (for the enquiry forms)
  {{ICON:name}}    -> inline SVG icon
  {{WAVE}}         -> large support-line SVG
  {{WAVE_SMALL}}   -> small support-line divider SVG
Run:  python3 build.py
"""
import os
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ROOT)
BASE_URL = "https://ehsmeds.com"
ASSET_V = "125"  # bump when css/js change so returning visitors get fresh assets

# WhatsApp enquiry line: Eng. Mostafa Ahmed Remah, General Manager.
# Supplied by the client 15 Aug 2026 as the number to use "for now" — confirm
# it is still the right destination before the public launch. International
# format, digits only: +20 100 679 0182.
WHATSAPP_NUMBER = "201006790182"

# Social profiles for the floating contact button. WhatsApp is not listed —
# it is always the first item. An empty string means the profile URL has not
# been supplied yet: the icon still shows, but as a shape rather than a link,
# so nothing ever points somewhere that does not exist. Paste the real URL in
# and that icon becomes clickable with no other change.
SOCIAL = {
    "instagram": "",
    "tiktok": "",
    "facebook": "",
}
SOCIAL_NAMES = {"instagram": "Instagram", "tiktok": "TikTok", "facebook": "Facebook"}

WA_ICON = """<svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M16.1 3C9.03 3 3.3 8.73 3.3 15.8c0 2.25.59 4.45 1.71 6.39L3.2 29l7-1.84a12.77 12.77 0 0 0 5.9 1.45h.01c7.07 0 12.8-5.73 12.8-12.8C28.9 8.73 23.17 3 16.1 3Zm0 23.47h-.01c-1.9 0-3.77-.51-5.4-1.48l-.39-.23-4.15 1.09 1.11-4.05-.25-.42a10.63 10.63 0 0 1-1.63-5.66c0-5.88 4.79-10.66 10.68-10.66 2.85 0 5.53 1.11 7.54 3.13a10.6 10.6 0 0 1 3.12 7.55c0 5.88-4.78 10.66-10.66 10.66Zm5.85-7.99c-.32-.16-1.9-.94-2.19-1.04-.29-.11-.51-.16-.72.16-.21.32-.83 1.04-1.01 1.25-.19.21-.37.24-.69.08-.32-.16-1.35-.5-2.57-1.59-.95-.85-1.59-1.9-1.78-2.22-.19-.32-.02-.49.14-.65.14-.14.32-.37.48-.56.16-.19.21-.32.32-.53.11-.21.05-.4-.03-.56-.08-.16-.72-1.73-.98-2.37-.26-.62-.52-.54-.72-.55l-.61-.01c-.21 0-.56.08-.85.4-.29.32-1.12 1.09-1.12 2.66 0 1.57 1.14 3.08 1.3 3.29.16.21 2.25 3.44 5.45 4.82.76.33 1.36.53 1.82.67.77.24 1.46.21 2.01.13.61-.09 1.9-.78 2.16-1.53.27-.75.27-1.39.19-1.53-.08-.13-.29-.21-.61-.37Z"/></svg>"""


# ----------------------------------------------------------------- SVG assets
MONOGRAM = """<svg viewBox="0 0 1140 440" fill="currentColor" aria-hidden="true" focusable="false"><path d="M410 103C374 48 306 20 220 20C110 20 20 110 20 220C20 330 110 420 220 420C306 420 374 392 410 337L332 287C310 320 270 340 220 340C154 340 100 286 100 220C100 154 154 100 220 100C270 100 310 120 332 153Z"/><rect x="66" y="186" width="344" height="68" rx="4"/><path d="M440 20H528V180H622V20H710V420H622V260H528V420H440Z"/><g transform="translate(35 0)"><path d="M1082 92C1034 41 967 18 891 22C794 27 731 78 730 151C729 233 804 257 881 272C944 284 989 294 988 330C987 361 951 379 900 379C844 379 797 358 758 317L698 379C749 424 816 440 894 440C1007 440 1078 391 1080 318C1082 230 1003 204 915 187C857 176 820 165 820 135C820 108 850 87 897 85C943 83 986 101 1021 132Z"/></g></svg>"""

WAVE = """<svg viewBox="0 0 1200 200" fill="none" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M-40 150 C 160 30, 300 210, 520 120 S 860 20, 1040 110 S 1240 190, 1360 90" stroke="currentColor" stroke-width="30" stroke-linecap="round"/></svg>"""

WAVE_SMALL = """<svg viewBox="0 0 130 22" fill="none" aria-hidden="true" focusable="false"><path d="M4 14 C 22 2, 38 22, 60 12 S 100 2, 126 12" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg>"""

ICONS = {
    "instagram": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.9"/><circle cx="12" cy="12" r="4.1" stroke="currentColor" stroke-width="1.9"/><circle cx="17.4" cy="6.6" r="1.2" fill="currentColor"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14.5 8.5h2.2V5.6h-2.6c-2.5 0-4 1.5-4 4.1v2H8v3h2.1V21h3.1v-6.3h2.3l.4-3h-2.7v-1.6c0-1 .4-1.6 1.3-1.6Z"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M14.3 3h2.6a4.9 4.9 0 0 0 4.1 4.1v2.6a7.4 7.4 0 0 1-4.1-1.4v5.9a5.9 5.9 0 1 1-5.9-5.9c.3 0 .6 0 .9.1v2.7a3.2 3.2 0 1 0 2.3 3.1V3Z"/></svg>',
    "chat": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M21 11.5a8.5 8.5 0 0 1-12.3 7.6L3.5 20.5l1.4-5A8.5 8.5 0 1 1 21 11.5Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/><circle cx="8.5" cy="11.5" r="1.1" fill="currentColor"/><circle cx="12" cy="11.5" r="1.1" fill="currentColor"/><circle cx="15.5" cy="11.5" r="1.1" fill="currentColor"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14m-6-7 7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m4.5 12.5 5 5 10-11" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "plus": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 21s7-5.1 7-11a7 7 0 1 0-14 0c0 5.9 7 11 7 11Z" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="10" r="2.6" stroke="currentColor" stroke-width="1.8"/></svg>',
    "building": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M4 21h16M16 9h3a1 1 0 0 1 1 1v11M8 7h2m-2 4h2m-2 4h2m2-8h2m-2 4h2m-2 4h2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "factory": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 21V9l6 4V9l6 4V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v17M3 21h18M7 17h2m4 0h2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.7 3.8 9S14.5 18.4 12 21c-2.5-2.6-3.8-5.7-3.8-9S9.5 5.6 12 3Z" stroke="currentColor" stroke-width="1.8"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5" stroke="currentColor" stroke-width="1.8"/><path d="m4 7 8 6 8-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "doc": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M6 3h8l4 4v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M14 3v5h4M9 13h6M9 17h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3 5 6v5c0 4.6 3 8.6 7 10 4-1.4 7-5.4 7-10V6l-7-3Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="m9 11.5 2.2 2.2L15.5 9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "gauge": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4.6 18.5a9 9 0 1 1 14.8 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M12 13.5 16 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="14" r="1.6" fill="currentColor"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 20.5S4 15.5 4 9.8A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 8 2.8c0 5.7-8 10.7-8 10.7Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "spark": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 20c2.5-6.5 5.5-9.5 8-10-2.5-.5-5.5-3.5-8-10 6.5 2.5 9.5 5.5 10 8 .5-2.5 3.5-5.5 10-8-6.5 2.5-9.5 5.5-10 8 2.5.5 5.5 3.5 8 10-6.5-2.5-9.5-5.5-10-8-.5 2.5-3.5 5.5-8 10Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>',
    "cross": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9.5 4h5v5.5H20v5h-5.5V20h-5v-5.5H4v-5h5.5V4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "info": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/><path d="M12 11v5.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="7.6" r="1.3" fill="currentColor"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 4 2.8 20h18.4L12 4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M12 10v4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="17.2" r="1.2" fill="currentColor"/></svg>',
    "ruler": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="2.5" y="9" width="19" height="6.5" rx="1.5" transform="rotate(-20 12 12)" stroke="currentColor" stroke-width="1.8"/><path d="m8 12.8 1 2.7m2.4-4 .7 1.9m2.6-3.1 1 2.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>',
    "people": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="9" cy="8.5" r="3.2" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 19.5c.7-3.2 2.9-5 5.5-5s4.8 1.8 5.5 5M15.5 6a3 3 0 1 1-1.2 5.8M16 14.6c2.2.3 3.9 2 4.5 4.9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "steth": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 3v5a5 5 0 0 0 10 0V3M10 13v3.5a4.5 4.5 0 0 0 9 0V14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="19" cy="11.5" r="2" stroke="currentColor" stroke-width="1.8"/></svg>',
    "box": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    "store": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 9 5.5 4h13L20 9M4 9v11h16V9M4 9h16M9.5 20v-6h5v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M2.5 6h11v10h-11zM13.5 10H18l3 3v3h-7.5" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="7" cy="17.5" r="1.8" stroke="currentColor" stroke-width="1.8"/><circle cx="17" cy="17.5" r="1.8" stroke="currentColor" stroke-width="1.8"/></svg>',
    "walk": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="13" cy="4.5" r="2" stroke="currentColor" stroke-width="1.8"/><path d="m8.5 21 2.3-6M11 9.5 8 11v3M11 9.5l2.5-1 2 4 3 1.5M13.5 12.5l1 3.5 1.5 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "download": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3v11m0 0 4.5-4.5M12 14 7.5 9.5M4 18.5h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "bank": '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 9.5 12 4l9 5.5M5 10v7m4.5-7v7m5-7v7m4.5-7v7M3.5 20.5h17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}
ICONS["wa"] = WA_ICON

# --------------------------------------------------------------------- pages
# slug -> per-language {title, desc, h1 handled in content}
PAGES = {
    "index":              {"nav": "home"},
    "about":              {"nav": "about"},
    "products":           {"nav": "products"},
    "mastercast-tube-grip":       {"nav": "products"},
    "mastercast-cast-net":        {"nav": "products"},
    "mastercast-elastic-bandage": {"nav": "products"},
    "mastercast-collar-cuff":     {"nav": "products"},
    "mastercast-skin-traction-kit": {"nav": "products"},
    "mastercast-stockinet":       {"nav": "products"},
    "gauze-wound-care":           {"nav": "products"},
    "orthopedic":                 {"nav": "products"},
    "masks-ppe":                  {"nav": "products"},
    "medpress":           {"nav": "medpress"},
    "medpress-stockings": {"nav": "medpress"},
    "size-guide":         {"nav": "size"},
    "how-to-wear":        {"nav": "size"},
    "professionals":      {"nav": "pro"},
    "factory":            {"nav": "factory"},
    "faq":                {"nav": "faq"},
    "contact":            {"nav": "contact"},
}

META = {
    "en": {
        "index": ("EHS — Egyptian Hospital Supplies | Engineered for better care",
                  "EHS is an Egyptian manufacturer of medical supplies and healthcare support products. Discover MedPress medical compression stockings — graduated support for professional care and everyday movement."),
        "about": ("About EHS | Egyptian Hospital Supplies",
                  "Founded in 1988, EHS combines practical medical engineering, dependable manufacturing and human comfort. Learn about the company, its leadership, values and locations."),
        "products": ("Products | EHS — Egyptian Hospital Supplies",
                     "Since 1988 EHS has manufactured gauze and wound care, elastic bandages, MedPress compression therapy, orthopedic products, face masks and PPE."),
        "gauze-wound-care": ("Gauze, Wound Care &amp; Medical Textiles | EHS",
                             "Sterile and non-sterile gauze, gauze rolls, swabs, laparotomy sponges and disposable medical textiles — manufactured by EHS for hospitals, operating rooms, clinics and emergency care."),
        "medical-textiles": ("Medical Textiles &amp; Disposables | EHS",
                             "Laparotomy sponges, disposable products and medical textiles for clinical environments, manufactured by EHS since 1988."),
        "orthopedic": ("MasterCast — Orthopedic Range | EHS",
                       "Cast padding, stockinette, cast net, orthopedic cotton and splint accessories — the MasterCast orthopedic range manufactured by EHS."),
        "masks-ppe": ("Face Masks &amp; PPE | EHS",
                      "Surgical, procedure and protective face masks plus disposable medical PPE, manufactured by EHS."),
        "mastercast-tube-grip": ("MasterCast Tube Grip — Elasticated Tubular Bandage | EHS",
                                 "MasterCast Tube Grip by EHS: a dense, smooth knitted tubular sleeve for even support around the arm, elbow, knee or lower leg. Gallery and details."),
        "mastercast-cast-net": ("MasterCast Cast-Net — Tubular Elastic Net | EHS",
                                "MasterCast Cast-Net by EHS: an open diamond-pattern tubular elastic mesh designed to hold dressings securely in place. Gallery and details."),
        "mastercast-skin-traction-kit": ("MasterCast Skin Traction Kit — Non-Adhesive | EHS",
                                   "A non-adhesive skin traction kit supporting limb alignment and immobilization — ventilated components, foam foot protection and a cotton crepe bandage. Adult and child. By EHS."),
        "mastercast-stockinet": ("MasterCast Stockinet — 100% Cotton Tubular | EHS",
                                   "Smooth 100% cotton tubular stockinet, open at both ends, protecting skin beneath casts and rigid supports. 10 m rolls in five widths. By EHS."),
        "mastercast-collar-cuff": ("MasterCast Collar &amp; Cuff — Padded Arm Support | EHS",
                                   "A soft, adaptable support for arm slings, clavicle braces and shoulder immobilizers — foam core in a 100% cotton sleeve, cut to length. By EHS."),
        "mastercast-elastic-bandage": ("MasterCast Elastic Bandage | EHS",
                                       "MasterCast Elastic Bandage by EHS: a woven elastic bandage applied in overlapping layers around the ankle, wrist or lower forearm. Gallery and details."),
        "medpress": ("MedPress Compression Solutions | MedPress by EHS",
                     "MedPress by EHS is a medical compression-stocking range designed for graduated, comfortable leg support — for professional recommendation and everyday routines."),
        "medpress-stockings": ("MedPress Medical Compression Stockings — Product Details | EHS",
                               "Specifications, sizes S–XXXL, intended use, care and application guidance for MedPress medical compression stockings by EHS."),
        "size-guide": ("Size &amp; Measurement Guide | MedPress by EHS",
                       "How to measure your ankle, calf and thigh for MedPress medical compression stockings, with the S–XXXL size chart from the current packaging."),
        "how-to-wear": ("How to Wear Compression Stockings | MedPress by EHS",
                        "Step-by-step guidance for putting on, wearing and caring for MedPress medical compression stockings — with safety notes from healthcare guidance."),
        "professionals": ("Professional &amp; Distributor Enquiries | EHS",
                          "Hospitals, clinics, pharmacies and distributors: request MedPress product documentation and partner with EHS, an Egyptian medical manufacturer."),
        "factory": ("The Factory | EHS — Quality &amp; Manufacturing",
                    "Inside the EHS factory: 10 production lines, integrated quality infrastructure and controlled manufacturing at 10th of Ramadan City since 1988."),
        "faq": ("Frequently Asked Questions | EHS — MedPress",
                "Answers to common questions about MedPress medical compression stockings — sizing, wearing, care and professional guidance."),
        "contact": ("Contact EHS | Egyptian Hospital Supplies",
                    "Contact EHS — Egyptian Hospital Supplies. Cairo office: El-Abour Buildings No. 7, Salah Salem Street. Factory: 10th of Ramadan City, Industrial Zone A2."),
    },
    "ar": {
        "index": ("شركة مصر لإمداد المستشفيات EHS | هندسة لرعاية أفضل",
                  "‏EHS شركة مصرية لتصنيع المستلزمات الطبية ومنتجات الدعم الصحي. اكتشف جوارب ميدبريس الطبية الضاغطة — دعم متدرّج للرعاية المهنية والحركة اليومية."),
        "about": ("من نحن | شركة مصر لإمداد المستشفيات EHS",
                  "منذ عام 1988 تجمع EHS بين الهندسة الطبية العملية والتصنيع الموثوق وراحة الإنسان. تعرّف على الشركة وقيادتها وقيمها ومواقعها."),
        "products": ("المنتجات | شركة مصر لإمداد المستشفيات EHS",
                     "منذ عام 1988 تصنّع EHS الشاش والعناية بالجروح والأربطة المرنة والعلاج بالضغط بقيادة ميدبريس ومنتجات العظام والكمامات ومستلزمات الوقاية."),
        "gauze-wound-care": ("الشاش والعناية بالجروح والمنسوجات الطبية | EHS",
                             "شاش معقّم وغير معقّم ولفائف شاش وفُوَط بطن جراحية ومنسوجات طبية أحادية الاستخدام — تصنّعها EHS للمستشفيات وغرف العمليات والعيادات والطوارئ."),
        "medical-textiles": ("المنسوجات الطبية والمنتجات أحادية الاستخدام | EHS",
                             "فُوَط بطن جراحية ومنتجات أحادية الاستخدام ومنسوجات طبية لبيئات العمل السريرية، تصنّعها EHS منذ عام 1988."),
        "orthopedic": ("ماستركاست — مجموعة العظام | EHS",
                       "حشوات الجبس والستوكينيت وشبك الجبس وقطن العظام ومستلزمات الجبائر — مجموعة ماستركاست للعظام تصنّعها EHS."),
        "masks-ppe": ("الكمامات ومستلزمات الوقاية | EHS",
                      "كمامات جراحية وكمامات إجراءات وكمامات واقية ومستلزمات وقاية طبية أحادية الاستخدام من EHS."),
        "mastercast-tube-grip": ("ماستركاست تيوب جريب — رباط أنبوبي مرن | EHS",
                                 "ماستركاست تيوب جريب من EHS: كُمّ أنبوبي بحياكة كثيفة وناعمة لدعم متساوٍ حول الذراع أو المرفق أو الركبة أو أسفل الساق. المعرض والتفاصيل."),
        "mastercast-cast-net": ("ماستركاست كاست-نت — شبكة أنبوبية مرنة | EHS",
                                "ماستركاست كاست-نت من EHS: شبكة أنبوبية مرنة بنقشة معينات مفتوحة مصممة لتثبيت الضمادات في مكانها بأمان. المعرض والتفاصيل."),
        "mastercast-skin-traction-kit": ("ماستركاست طقم الشد الجلدي — غير لاصق | EHS",
                                   "طقم شد جلدي غير لاصق لدعم استقامة الطرف وتثبيته — مكوّنات مثقّبة وحماية إسفنجية للقدم ورباط كريب قطني. للبالغين والأطفال. من EHS."),
        "mastercast-stockinet": ("ماستركاست ستوكينيت — أنبوبي من القطن 100% | EHS",
                                   "رباط أنبوبي ناعم من القطن 100% مفتوح من الطرفين، يحمي الجلد تحت الجبس والدعامات الصلبة. لفات 10 أمتار بخمسة عروض. من EHS."),
        "mastercast-collar-cuff": ("ماستركاست كولار آند كاف — دعامة ذراع مبطّنة | EHS",
                                   "نظام دعم طري لعمل حمّالات ذراع ودعامات ترقوة ومثبّتات كتف — قلب إسفنجي داخل غلاف قطن 100%، يُقصّ بالطول المطلوب. من EHS."),
        "mastercast-elastic-bandage": ("ماستركاست الرباط المرن | EHS",
                                       "الرباط المرن ماستركاست من EHS: رباط مرن منسوج يُلف بطبقات متداخلة حول الكاحل أو المعصم أو أسفل الساعد. المعرض والتفاصيل."),
        "medpress": ("حلول ميدبريس للضغط الطبي | ميدبريس من EHS",
                     "ميدبريس من EHS مجموعة جوارب ضغط طبية مصممة لدعم متدرّج ومريح للساقين — للتوصية المهنية والاستخدام اليومي."),
        "medpress-stockings": ("جوارب ميدبريس الطبية الضاغطة — تفاصيل المنتج | EHS",
                               "المواصفات والمقاسات من S إلى XXXL ودواعي الاستخدام وإرشادات العناية والارتداء لجوارب ميدبريس الطبية الضاغطة من EHS."),
        "size-guide": ("دليل المقاسات والقياس | ميدبريس من EHS",
                       "طريقة قياس محيط الكاحل وبطة الساق والفخذ لاختيار مقاس جوارب ميدبريس الطبية الضاغطة، مع جدول المقاسات من S إلى XXXL كما هو مطبوع على العبوة الحالية."),
        "how-to-wear": ("طريقة ارتداء الجوارب الضاغطة | ميدبريس من EHS",
                        "إرشادات خطوة بخطوة لارتداء جوارب ميدبريس الطبية الضاغطة والعناية بها، مع ملاحظات السلامة."),
        "professionals": ("استفسارات المؤسسات والموزّعين | EHS",
                          "للمستشفيات والعيادات والصيدليات والموزّعين: اطلبوا وثائق منتجات ميدبريس وتعاونوا مع EHS، الشركة المصرية لتصنيع المستلزمات الطبية."),
        "factory": ("المصنع | EHS — الجودة والتصنيع",
                    "داخل مصنع EHS: عشرة خطوط إنتاج وبنية جودة متكاملة وتصنيع منضبط في مدينة العاشر من رمضان منذ عام 1988."),
        "faq": ("الأسئلة الشائعة | ميدبريس من EHS",
                "إجابات عن الأسئلة الشائعة حول جوارب ميدبريس الطبية الضاغطة — المقاسات والارتداء والعناية والتوجيه المهني."),
        "contact": ("تواصل معنا | شركة مصر لإمداد المستشفيات EHS",
                    "تواصل مع EHS — شركة مصر لإمداد المستشفيات. مكتب القاهرة: عمارات العبور رقم 7، شارع صلاح سالم. المصنع: مدينة العاشر من رمضان، المنطقة الصناعية A2."),
    },
}

STR = {
    "en": {
        "dir": "ltr", "lang": "en", "locale": "en_US",
        "skip": "Skip to content",
        "brand_name": "Egyptian Hospital Supplies",
        "brand_sub": "EHS · Medical manufacturer — Egypt",
        "nav": [("about", "about.html", "About", [
                    ("about.html", "About EHS"),
                    ("about.html#story", "Our Story — since 1988"),
                    ("about.html#values", "Our Values"),
                    ("about.html#clients", "Who We Supply"),
                    ("about.html#leadership", "Leadership"),
                    ("about.html#locations", "Locations"),
                    ("factory.html", "The Factory"),
                ]),
                ("products", "products.html", "Products", [
                    ("products.html", "All products"),
                    ("medpress.html", "MedPress"),
                    ("orthopedic.html", "MasterCast"),
                    ("products.html#prevent", "Prevent"),
                ]),
                ("medpress", "medpress.html", "MedPress", [
                    ("medpress.html", "Compression Solutions"),
                    ("medpress-stockings.html", "Product Details"),
                    ("size-guide.html", "Size &amp; Measurement Guide"),
                    ("how-to-wear.html", "How to Wear"),
                ]),
                ("size", "size-guide.html", "Size Guide"),
                ("factory", "factory.html", "Factory"),
                ("faq", "faq.html", "FAQ"),
                ("contact", "contact.html", "Contact")],
        "nav_home": "Home",
        "cta_pro": "For Professionals",
        "lang_switch_label": "العربية",
        "lang_switch_class": "lang-switch--ar",
        "footer_about": "EHS designs and manufactures dependable medical support products for professional care and everyday use.",
        "footer_col_company": "Company",
        "footer_col_medpress": "MedPress",
        "footer_col_locations": "Locations",
        "footer_company_links": [("about.html", "About EHS"), ("factory.html", "The Factory"), ("professionals.html", "Professional Enquiries"), ("contact.html", "Contact")],
        "footer_medpress_links": [("medpress.html", "Compression Solutions"), ("medpress-stockings.html", "Product Details"), ("size-guide.html", "Size &amp; Measurement Guide"), ("how-to-wear.html", "How to Wear"), ("faq.html", "FAQ")],
        "addr_office_t": "Cairo Office",
        "addr_office": "El-Abour Buildings No. 7,<br>Salah Salem Street, Cairo, Egypt",
        "addr_factory_t": "Factory",
        "addr_factory": "10th of Ramadan City, Industrial Zone A2,<br>Area No. 2/5/1, Egypt",
        "footer_disclaimer": "Product selection, compression level and usage should follow the recommendation of a qualified healthcare professional. Consult a healthcare professional before use if you have diabetes, circulatory disorders or another condition affecting leg health. Product details shown on this website are taken from current company materials and remain subject to confirmation by EHS.",
        "rights": "EHS — Egyptian Hospital Supplies. All rights reserved.",
        "wa_label": "Chat on WhatsApp",
        "fab_label": "Contact &amp; follow us",
        "wa_prefill": "Hello EHS, I would like to ask about your products.",
        "wa_bulk_prefix": "Hello EHS, I would like a bulk order quotation for: ",
    },
    "ar": {
        "dir": "rtl", "lang": "ar", "locale": "ar_EG",
        "skip": "تخطَّ إلى المحتوى",
        "brand_name": "شركة مصر لإمداد المستشفيات",
        "brand_sub": "EHS · مصنّع مستلزمات طبية — مصر",
        "nav": [("about", "about.html", "من نحن", [
                    ("about.html", "نبذة عن EHS"),
                    ("about.html#story", "قصتنا — منذ 1988"),
                    ("about.html#values", "قيمنا"),
                    ("about.html#clients", "من نخدمهم"),
                    ("about.html#leadership", "فريق القيادة"),
                    ("about.html#locations", "مواقعنا"),
                    ("factory.html", "المصنع"),
                ]),
                ("products", "products.html", "المنتجات", [
                    ("products.html", "كل المنتجات"),
                    ("medpress.html", "ميدبريس"),
                    ("orthopedic.html", "ماستركاست"),
                    ("products.html#prevent", "بريفنت"),
                ]),
                ("medpress", "medpress.html", "ميدبريس", [
                    ("medpress.html", "حلول الضغط الطبي"),
                    ("medpress-stockings.html", "تفاصيل المنتج"),
                    ("size-guide.html", "دليل المقاسات والقياس"),
                    ("how-to-wear.html", "طريقة الارتداء"),
                ]),
                ("size", "size-guide.html", "دليل المقاسات"),
                ("factory", "factory.html", "المصنع"),
                ("faq", "faq.html", "الأسئلة الشائعة"),
                ("contact", "contact.html", "تواصل معنا")],
        "nav_home": "الرئيسية",
        "cta_pro": "للمؤسسات والموزّعين",
        "lang_switch_label": "English",
        "lang_switch_class": "lang-switch--en",
        "footer_about": "تصمّم EHS وتصنّع منتجات دعم طبية يُعتمد عليها للرعاية المهنية والاستخدام اليومي.",
        "footer_col_company": "الشركة",
        "footer_col_medpress": "ميدبريس",
        "footer_col_locations": "مواقعنا",
        "footer_company_links": [("about.html", "من نحن"), ("factory.html", "المصنع"), ("professionals.html", "استفسارات المؤسسات"), ("contact.html", "تواصل معنا")],
        "footer_medpress_links": [("medpress.html", "حلول الضغط الطبي"), ("medpress-stockings.html", "تفاصيل المنتج"), ("size-guide.html", "دليل المقاسات والقياس"), ("how-to-wear.html", "طريقة الارتداء"), ("faq.html", "الأسئلة الشائعة")],
        "addr_office_t": "مكتب القاهرة",
        "addr_office": "عمارات العبور رقم 7،<br>شارع صلاح سالم، القاهرة، مصر",
        "addr_factory_t": "المصنع",
        "addr_factory": "مدينة العاشر من رمضان، المنطقة الصناعية A2،<br>القطعة رقم 2/5/1، مصر",
        "footer_disclaimer": "يجب أن يتم اختيار المنتج ومستوى الضغط وطريقة الاستخدام وفقًا لتوصية مختصّ رعاية صحية مؤهَّل. واستشر مختصّ رعاية صحية قبل الاستخدام إذا كنت تعاني من السكري أو اضطرابات الدورة الدموية أو أي حالة أخرى تؤثر على صحة الساقين. تفاصيل المنتجات المعروضة على هذا الموقع مأخوذة من مواد الشركة الحالية وتظل خاضعة للتأكيد من EHS.",
        "rights": "EHS — شركة مصر لإمداد المستشفيات. جميع الحقوق محفوظة.",
        "wa_label": "راسلنا على واتساب",
        "fab_label": "تواصل معنا وتابعنا",
        "wa_prefill": "مرحبًا EHS، أودّ الاستفسار عن منتجاتكم.",
        "wa_bulk_prefix": "مرحبًا EHS، أودّ الحصول على عرض سعر لطلب كمية بالجملة من: ",
    },
}


def head(lang, slug):
    s = STR[lang]
    title, desc = META[lang][slug]
    a = "assets" if lang == "en" else "../assets"
    fname = "index.html" if slug == "index" else f"{slug}.html"
    en_url = f"{BASE_URL}/{'' if slug == 'index' else fname}"
    ar_url = f"{BASE_URL}/ar/{fname}"
    canonical = en_url if lang == "en" else ar_url
    og_img = f"{BASE_URL}/assets/img/medpress-studio-wide.jpg"
    return f"""<!doctype html>
<html lang="{s['lang']}" dir="{s['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="ar" href="{ar_url}">
<link rel="alternate" hreflang="x-default" href="{en_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="EHS — Egyptian Hospital Supplies">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:locale" content="{s['locale']}">
<meta name="theme-color" content="#4F7A12">
<link rel="icon" type="image/svg+xml" href="{a}/logos/EHS-app-icon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="{a}/logos/favicon-32.png">
<link rel="apple-touch-icon" href="{a}/logos/apple-touch-icon.png">
<link rel="preload" href="{a}/fonts/{'manrope-latin-800.woff2' if lang == 'en' else 'ibm-plex-sans-arabic-arabic-700.woff2'}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{a}/fonts/fonts.css">
<link rel="stylesheet" href="{a}/css/style.css?v={ASSET_V}">
<script>
(function () {{ try {{
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || sessionStorage.getItem('ehsSeenLoader') || /[?&]noloader/.test(location.search)) {{
    document.documentElement.classList.add('loader-skip');
  }} else {{
    document.documentElement.classList.add('loader-active');
  }}
  if (sessionStorage.getItem('ehsCurtain')) {{ document.documentElement.classList.add('curtain-in'); }}
}} catch (e) {{ document.documentElement.classList.add('loader-skip'); }} }})();
</script>
<noscript><style>.loader {{ display: none; }} .reveal {{ opacity: 1 !important; transform: none !important; }}</style></noscript>
</head>
<body>
<div class="loader" id="ehs-loader" role="presentation" aria-hidden="true">
  <svg class="loader__ribbon" viewBox="0 0 1200 620" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
    <path pathLength="1" d="M-120 400C140 190 320 180 520 330S770 560 930 400S1140 180 1340 300"/>
  </svg>
  <div class="loader__center">
    <img class="loader__logo" src="{a}/logos/EHS-logo-white.svg" alt="" width="800" height="114">
  </div>
</div>
<a class="skip-link" href="#main">{s['skip']}</a>
<div class="curtain" id="ehs-curtain" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
"""


def header_html(lang, slug):
    s = STR[lang]
    a = "assets" if lang == "en" else "../assets"
    active = PAGES[slug]["nav"]
    caret = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    links = []
    for entry in s["nav"]:
        key, href, label = entry[0], entry[1], entry[2]
        children = entry[3] if len(entry) > 3 else None
        cls = ' class="is-active"' if key == active else ""
        if children:
            subs = "".join(f'<a href="{h}">{t}</a>' for h, t in children)
            links.append(
                f'<div class="nav__item"><a href="{href}"{cls}>{label}'
                f'<span class="nav__caret">{caret}</span></a>'
                f'<div class="nav__sub">{subs}</div></div>')
        else:
            links.append(f'<a href="{href}"{cls}>{label}</a>')
    home_active = ' class="is-active"' if active == "home" else ""
    other = "ar" if lang == "en" else "en"
    fname = "index.html" if slug == "index" else f"{slug}.html"
    switch_href = f"ar/{fname}" if lang == "en" else f"../{fname}"
    return f"""<header class="header">
  <div class="container container--wide header__inner">
    <a class="brand" href="index.html" aria-label="EHS — {s['brand_name']}">
      <img class="brand__lockup" src="{a}/logos/EHS-logo.svg" alt="EHS — {s['brand_name']}" width="800" height="114">
      <img class="brand__markonly" src="{a}/logos/EHS-mark.svg" alt="" aria-hidden="true" width="190" height="84">
      <span class="brand__text">
        <span class="brand__name"><span class="brand__name-track"><span>{s['brand_name']}</span><span aria-hidden="true">{s['brand_name']}</span></span></span>
        <span class="brand__sub">{s['brand_sub']}</span>
      </span>
      <span class="reg" aria-hidden="true">&reg;</span>
    </a>
    <nav class="nav" aria-label="Main">
      <a href="index.html"{home_active}>{s['nav_home']}</a>
      {''.join(links)}
    </nav>
    <div class="header__actions">
      <a class="lang-switch {s['lang_switch_class']}" href="{switch_href}" lang="{other}" hreflang="{other}">{s['lang_switch_label']}</a>
      <a class="btn btn--sm nav-cta" href="professionals.html">{s['cta_pro']}</a>
      <button class="nav-toggle" aria-expanded="false" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<main id="main">
"""


def footer_html(lang, slug=""):
    s = STR[lang]
    a = "assets" if lang == "en" else "../assets"
    # The reveal effect now lives on the hero (see .page-flow) rather than the
    # footer. Flip FOOTER_REVEAL to re-enable the under-page footer.
    FOOTER_REVEAL = False
    reveal_attr = " data-footer-reveal" if (FOOTER_REVEAL and slug == "index") else ""
    company = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in s["footer_company_links"])
    medpress = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in s["footer_medpress_links"])
    wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(s['wa_prefill'])}"
    # Floating contact button. Without social profiles it stays the plain
    # WhatsApp button; once they are configured it opens into a channel list.
    if SOCIAL:
        items = ['<a class="fab__item fab__item--wa" href="%s" target="_blank" rel="noopener" aria-label="%s">'
                 '<span class="fab__label">%s</span><span class="fab__dot">%s</span></a>'
                 % (wa_url, s["wa_label"], s["wa_label"], WA_ICON)]
        for name, url in SOCIAL.items():
            if name not in ICONS:
                continue
            label = SOCIAL_NAMES.get(name, name.title())
            if url:
                items.append('<a class="fab__item" href="%s" target="_blank" rel="noopener" aria-label="%s">'
                             '<span class="fab__label">%s</span><span class="fab__dot">%s</span></a>'
                             % (url, label, label, ICONS[name]))
            else:
                # profile not supplied yet — the icon shows but does not link
                items.append('<span class="fab__item fab__item--soon" aria-disabled="true">'
                             '<span class="fab__label">%s</span><span class="fab__dot">%s</span></span>'
                             % (label, ICONS[name]))
        fab = ('<div class="fab" id="ehs-fab">'
               '<div class="fab__menu">%s</div>'
               '<button class="fab__toggle" type="button" aria-expanded="false" aria-label="%s">'
               '<span class="fab__open">%s</span><span class="fab__close">%s</span>'
               '<span class="fab__toggle-label" aria-hidden="true">%s</span></button>'
               '</div>' % ("".join(items), s["fab_label"], ICONS["chat"], ICONS["plus"], s["fab_label"]))
    else:
        fab = ('<a class="wa-fab" href="%s" target="_blank" rel="noopener" aria-label="%s">%s'
               '<span class="wa-fab__label">%s</span></a>'
               % (wa_url, s["wa_label"], WA_ICON, s["wa_label"]))

    return f"""</main>
{fab}
<footer class="footer"{reveal_attr}>
  <div class="container footer__inner">
    <div class="footer__grid">
      <div class="footer__brand">
        <span class="logo-reg"><img class="footer__logo" src="{a}/logos/EHS-logo-white.svg" alt="EHS — {s['brand_name']}" width="800" height="114"><span class="reg" aria-hidden="true">&reg;</span></span>
        <p>{s['footer_about']}</p>
      </div>
      <div>
        <h4>{s['footer_col_company']}</h4>
        <ul>{company}</ul>
      </div>
      <div>
        <h4>{s['footer_col_medpress']}</h4>
        <ul>{medpress}</ul>
      </div>
      <div>
        <h4>{s['footer_col_locations']}</h4>
        <address><strong>{s['addr_office_t']}</strong>{s['addr_office']}</address>
        <address><strong>{s['addr_factory_t']}</strong>{s['addr_factory']}</address>
      </div>
    </div>
    <p class="footer__disclaimer">{s['footer_disclaimer']}</p>
    <div class="footer__bottom">
      <span>© <span data-year>2026</span> {s['rights']}</span>
      <span class="domain">ehsmeds.com</span>
    </div>
  </div>
</footer>
<script src="{a}/js/main.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


ICON_RE = re.compile(r"\{\{ICON:([a-z-]+)\}\}")
WABULK_RE = re.compile(r"\{\{WABULK:([^}]+)\}\}")


def build_page(lang, slug):
    src = os.path.join(ROOT, "content", lang, f"{slug}.html")
    with open(src, encoding="utf-8") as f:
        body = f.read()
    a = "assets" if lang == "en" else "../assets"
    body = body.replace("{{A}}", a)
    body = body.replace("{{WA_URL}}", f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(STR[lang]['wa_prefill'])}")
    body = body.replace("{{WA_NUMBER}}", WHATSAPP_NUMBER)
    body = WABULK_RE.sub(
        lambda m: f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(STR[lang]['wa_bulk_prefix'] + m.group(1))}",
        body)
    body = body.replace("{{WAVE_SMALL}}", WAVE_SMALL)
    body = body.replace("{{WAVE}}", WAVE)
    body = ICON_RE.sub(lambda m: ICONS[m.group(1)], body)
    html = head(lang, slug) + header_html(lang, slug) + body + footer_html(lang, slug)
    outdir = SITE if lang == "en" else os.path.join(SITE, "ar")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "index.html" if slug == "index" else f"{slug}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out


# Old URLs that moved — each generates a tiny page that forwards to the new one
REDIRECTS = {"quality.html": "factory.html",
             "medical-textiles.html": "gauze-wound-care.html"}


def write_redirects():
    count = 0
    for old, new in REDIRECTS.items():
        for lang in ("en", "ar"):
            outdir = SITE if lang == "en" else os.path.join(SITE, "ar")
            canonical = f"{BASE_URL}/{new}" if lang == "en" else f"{BASE_URL}/ar/{new}"
            html = (
                f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
                f'<meta http-equiv="refresh" content="0; url={new}">\n'
                f'<link rel="canonical" href="{canonical}">\n'
                f'<meta name="robots" content="noindex">\n'
                f'<title>Redirecting…</title>\n</head>\n<body>\n'
                f'<p><a href="{new}">Continue…</a></p>\n'
                f'<script>location.replace("{new}");</script>\n</body>\n</html>\n'
            )
            with open(os.path.join(outdir, old), "w", encoding="utf-8") as f:
                f.write(html)
            count += 1
    return count


if __name__ == "__main__":
    built = []
    for lang in ("en", "ar"):
        for slug in PAGES:
            src = os.path.join(ROOT, "content", lang, f"{slug}.html")
            if not os.path.exists(src):
                print(f"!! missing content: {lang}/{slug}.html", file=sys.stderr)
                continue
            built.append(build_page(lang, slug))
    print(f"Built {len(built)} pages + {write_redirects()} redirect stubs.")
