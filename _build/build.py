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
import json
import datetime
import os
import posixpath
import re
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ROOT)
BASE_URL = "https://ehsmeds.com"
ASSET_V = "161"  # bump when css/js/logo change so returning visitors get fresh assets

# WhatsApp enquiry line: Eng. Mostafa Ahmed Remah, General Manager.
# Supplied by the client 15 Aug 2026 as the number to use "for now" — confirm
# it is still the right destination before the public launch. International
# format, digits only: +20 100 679 0182.
WHATSAPP_NUMBER = "201006790182"

# Company phone. Confirmed for publication by the company owner 17 Aug 2026.
# The email address is still not cleared, so it stays unpublished.
PHONE_E164 = "+201006790182"
PHONE_DISPLAY = "+20 100 679 0182"

# Company email. Chosen by the client 17 Aug 2026 after being shown that this is
# an individual's address rather than a role address like info@ — his call.
# The mailbox is Microsoft 365; MX and SPF were corrected the same day.
EMAIL_ADDRESS = "info@ehsmeds.com"

# Social profiles for the floating contact button. WhatsApp is not listed —
# it is always the first item. An empty string means the profile URL has not
# been supplied yet: the icon still shows, but as a shape rather than a link,
# so nothing ever points somewhere that does not exist. Paste the real URL in
# and that icon becomes clickable with no other change.
SOCIAL = {
    "instagram": "https://www.instagram.com/ehsmeds/",
    # no ?lang= param: the profile should open in the visitor's own language,
    # not be forced to English on an Arabic page
    "tiktok": "https://www.tiktok.com/@ehsmeds",
    "facebook": "https://www.facebook.com/profile.php?id=61593060106191",
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
    "prevent":                    {"nav": "products"},
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
                  "EHS manufactures medical supplies and healthcare support products in Egypt — MedPress compression stockings, the MasterCast orthopedic range and Prevent gauze."),
        "about": ("About EHS | Egyptian Hospital Supplies",
                  "Founded in 1988, EHS combines practical medical engineering with dependable manufacturing. The company, its leadership, values and locations."),
        "products": ("Products | EHS — Egyptian Hospital Supplies",
                     "Since 1988 EHS has manufactured gauze and wound care, elastic bandages, MedPress compression therapy, orthopedic products, face masks and PPE."),
        "gauze-wound-care": ("Gauze, Wound Care &amp; Medical Textiles | EHS",
                             "Sterile and non-sterile gauze, gauze rolls, swabs and laparotomy sponges — manufactured by EHS for hospitals, operating rooms and clinics."),
        "medical-textiles": ("Medical Textiles &amp; Disposables | EHS",
                             "Laparotomy sponges, disposable products and medical textiles for clinical environments, manufactured by EHS since 1988."),
        "orthopedic": ("MasterCast — Orthopedic Range | EHS",
                       "Cast padding, stockinette, cast net, orthopedic cotton and splint accessories — the MasterCast orthopedic range manufactured by EHS."),
        "masks-ppe": ("Face Masks &amp; PPE | EHS",
                      "Surgical, procedure and protective face masks plus disposable medical PPE, manufactured by EHS."),
        "prevent": ("Prevent — Gauze, Wound Care &amp; Protection | EHS",
                    "The Prevent range by EHS — gauze and wound care, medical textiles and disposables, and face masks and protective equipment."),
        "mastercast-tube-grip": ("MasterCast Tube Grip — Elasticated Tubular Bandage | EHS",
                                 "MasterCast Tube Grip by EHS: a dense, smooth knitted tubular sleeve for even support around the arm, elbow, knee or lower leg. Gallery and details."),
        "mastercast-cast-net": ("MasterCast Cast-Net — Tubular Elastic Net | EHS",
                                "MasterCast Cast-Net by EHS: an open diamond-pattern tubular elastic mesh designed to hold dressings securely in place. Gallery and details."),
        "mastercast-skin-traction-kit": ("MasterCast Skin Traction Kit — Non-Adhesive | EHS",
                                   "Non-adhesive skin traction kit for limb alignment and immobilization — ventilated components, foam foot protection and a cotton crepe bandage. By EHS."),
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
        "404": ("Page not found | EHS — Egyptian Hospital Supplies",
                "This page could not be found. Browse the EHS product range or contact us for help."),
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
        "prevent": ("بريفنت — الشاش والعناية بالجروح والوقاية | EHS",
                    "مجموعة بريفنت من EHS — الشاش والعناية بالجروح، والمنسوجات الطبية والمنتجات أحادية الاستخدام، والكمامات ومستلزمات الوقاية."),
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
        "404": ("الصفحة غير موجودة | شركة مصر لإمداد المستشفيات EHS",
                "تعذّر العثور على هذه الصفحة. تصفّح منتجات EHS أو تواصل معنا للمساعدة."),
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
                    ("about.html#certifications", "Certifications"),
                    ("about.html#leadership", "Leadership"),
                    ("about.html#locations", "Locations"),
                    ("factory.html", "The Factory"),
                ]),
                ("products", "products.html", "Products", [
                    ("products.html", "All products"),
                    ("medpress.html", "MedPress"),
                    ("orthopedic.html", "MasterCast"),
                    ("prevent.html", "Prevent"),
                ]),
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
        "mail_label": "Email us",
        "mail_subject": "Product enquiry",
        "mail_bulk_subject": "Bulk order enquiry",
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
                    ("about.html#certifications", "الاعتمادات"),
                    ("about.html#leadership", "فريق القيادة"),
                    ("about.html#locations", "مواقعنا"),
                    ("factory.html", "المصنع"),
                ]),
                ("products", "products.html", "المنتجات", [
                    ("products.html", "كل المنتجات"),
                    ("medpress.html", "ميدبريس"),
                    ("orthopedic.html", "ماستركاست"),
                    ("prevent.html", "بريفنت"),
                ]),
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
        "mail_label": "راسلنا بالبريد",
        "mail_subject": "استفسار عن المنتجات",
        "mail_bulk_subject": "استفسار عن طلب بالجملة",
    },
}


# ------------------------------------------------------- structured data (JSON-LD)
# Search engines read this to understand who EHS is, where it operates and what
# it makes. It is generated from the same source of truth as the visible page,
# so it can never drift out of sync with the content.

ORG_ID = f"{BASE_URL}/#organization"
WEBSITE_ID = f"{BASE_URL}/#website"
FOUNDED = "1988"

# Per-language organisation facts. Addresses mirror STR[lang]["addr_*"].
SD_ORG = {
    "en": {
        "name": "EHS — Egyptian Hospital Supplies",
        "legal": "Egyptian Hospital Supplies",
        "alt_names": ["Egyptian Hospital Supplies", "EHS",
                      "EHS Egypt", "EHS Medical Supplies",
                      "شركة مصر لإمداد المستشفيات"],
        "desc": ("Egyptian manufacturer of medical supplies and healthcare support products "
                 "since 1988 — gauze and wound care, MedPress medical compression stockings, "
                 "the MasterCast orthopedic range, face masks and PPE."),
        "office_name": "EHS Cairo Office",
        "office_street": "El-Abour Buildings No. 7, Salah Salem Street",
        "office_city": "Cairo",
        "factory_name": "EHS Factory — 10th of Ramadan City",
        "factory_street": "Industrial Zone A2, Area No. 2/5/1",
        "factory_city": "10th of Ramadan City",
        "region": "Sharqia",           # the factory; the Cairo office overrides this
        "office_region": "Cairo",
        "country": "EG",
    },
    "ar": {
        "name": "EHS — شركة مصر لإمداد المستشفيات",
        "legal": "شركة مصر لإمداد المستشفيات",
        "alt_names": ["شركة مصر لإمداد المستشفيات", "EHS",
                      "Egyptian Hospital Supplies", "EHS Egypt",
                      "EHS Medical Supplies"],
        "desc": ("شركة مصرية لتصنيع المستلزمات الطبية ومنتجات الدعم الصحي منذ عام 1988 — "
                 "الشاش والعناية بالجروح، وجوارب ميدبريس الطبية الضاغطة، "
                 "ومجموعة ماستركاست للعظام، والكمامات ومستلزمات الوقاية."),
        "office_name": "مكتب EHS بالقاهرة",
        "office_street": "عمارات العبور رقم 7، شارع صلاح سالم",
        "office_city": "القاهرة",
        "factory_name": "مصنع EHS — مدينة العاشر من رمضان",
        "factory_street": "المنطقة الصناعية A2، القطعة رقم 2/5/1",
        "factory_city": "مدينة العاشر من رمضان",
        "region": "الشرقية",
        "office_region": "القاهرة",
        "country": "EG",
    },
}

# Pages that describe one specific product get Product markup.
# category: the medical device category shown to search engines.
# Share image per page, so a link to the factory does not preview a stocking.
OG_DEFAULT = "ehs-leadership-portrait.jpg"
OG_IMAGES = {
    "index": "ehs-leadership-portrait.jpg",
    "about": "ehs-leadership-portrait.jpg",
    "factory": "factory-exterior.jpg",
    "medpress": "medpress-open-closed-toe.jpg",
    "orthopedic": "mastercast/mastercast-box.jpg",
    "gauze-wound-care": "prevent/gauze-and-textiles-cover.jpg",
    "masks-ppe": "masks/mask-surgical-blue.jpg",
    "prevent": "prevent/gauze-and-textiles-cover.jpg",
    "size-guide": "size-guide-diagram-en.jpg",
    "how-to-wear": "medpress-how-to-wear-steps.jpg",
}

SD_PRODUCTS = {
    "medpress-stockings": {
        "brand": "MedPress",
        "en": "MedPress Medical Compression Stockings",
        "ar": "جوارب ميدبريس الطبية الضاغطة",
        "img": "medpress-open-closed-toe.jpg",
    },
    "mastercast-tube-grip": {
        "brand": "MasterCast",
        "en": "MasterCast Tube Grip — Elasticated Tubular Bandage",
        "ar": "ماستركاست تيوب جريب — رباط أنبوبي مرن",
        "img": "mastercast/tube-grip-hero.jpg",
    },
    "mastercast-cast-net": {
        "brand": "MasterCast",
        "en": "MasterCast Cast-Net — Tubular Elastic Net",
        "ar": "ماستركاست كاست-نت — شبكة أنبوبية مرنة",
        "img": "mastercast/cast-net-hero.jpg",
    },
    "mastercast-elastic-bandage": {
        "brand": "MasterCast",
        "en": "MasterCast Elastic Bandage",
        "ar": "ماستركاست الرباط المرن",
        "img": "mastercast/elastic-bandage-hero.jpg",
    },
    "mastercast-collar-cuff": {
        "brand": "MasterCast",
        "en": "MasterCast Collar & Cuff — Padded Arm Support",
        "ar": "ماستركاست كولار آند كاف — دعامة ذراع مبطّنة",
        "img": "mastercast/collar-cuff-hero-clinic.jpg",
    },
    "mastercast-skin-traction-kit": {
        "brand": "MasterCast",
        "en": "MasterCast Skin Traction Kit — Non-Adhesive",
        "ar": "ماستركاست طقم الشد الجلدي — غير لاصق",
        "img": "mastercast/skin-traction-kit-hero.jpg",
    },
    "mastercast-stockinet": {
        "brand": "MasterCast",
        "en": "MasterCast Stockinet — 100% Cotton Tubular",
        "ar": "ماستركاست ستوكينيت — أنبوبي من القطن 100%",
        "img": "mastercast/stockinet-hero.jpg",
    },
}

# Pages that list a range rather than one item.
SD_COLLECTIONS = {"products", "medpress", "orthopedic", "prevent", "gauze-wound-care", "masks-ppe"}

# Breadcrumb parent for pages that sit under a section.
SD_PARENT = {
    "medpress-stockings": "medpress", "size-guide": "medpress", "how-to-wear": "medpress",
    "faq": "medpress",
    "mastercast-tube-grip": "orthopedic", "mastercast-cast-net": "orthopedic",
    "mastercast-elastic-bandage": "orthopedic", "mastercast-collar-cuff": "orthopedic",
    "mastercast-skin-traction-kit": "orthopedic", "mastercast-stockinet": "orthopedic",
    "orthopedic": "products", "medpress": "products", "prevent": "products",
    "gauze-wound-care": "prevent", "masks-ppe": "prevent", "factory": "about",
}

FAQ_RE = re.compile(
    r"<summary>(?P<q>.*?)(?:<span class=\"acc-icon\">.*?</span>)?\s*</summary>\s*"
    r"<div class=\"acc-body\">(?P<a>.*?)</div>",
    re.S)
TAG_RE = re.compile(r"<[^>]+>")


def _plain(html_fragment):
    """Strip tags/placeholders and collapse whitespace — JSON-LD wants plain text."""
    txt = ICON_RE.sub("", html_fragment)
    txt = TAG_RE.sub(" ", txt)
    txt = (txt.replace("&amp;", "&").replace("&nbsp;", " ")
              .replace("&rsquo;", "’").replace("&mdash;", "—"))
    return re.sub(r"\s+", " ", txt).strip()


def _page_url(lang, slug):
    """The URL the edge actually serves. Cloudflare drops the .html extension,
    so a canonical or sitemap entry ending in .html points at a redirect rather
    than at the page — every such URL was costing a hop and muddying which
    address search engines should treat as the real one."""
    if lang == "en":
        return f"{BASE_URL}/" if slug == "index" else f"{BASE_URL}/{slug}"
    return f"{BASE_URL}/ar/" if slug == "index" else f"{BASE_URL}/ar/{slug}"


def _nav_label(lang, slug):
    """Human label for a slug, taken from the page title before its separator."""
    title = META[lang][slug][0]
    for sep in (" | ", " — "):
        if sep in title:
            title = title.split(sep)[0]
            break
    return _plain(title)


def json_ld(lang, slug, body=""):
    """Build the JSON-LD graph for one page. Returns a <script> block."""
    o = SD_ORG[lang]
    url = _page_url(lang, slug)
    home = _page_url(lang, "index")
    title, desc = _plain(META[lang][slug][0]), _plain(META[lang][slug][1])

    def place(kind, name, street, city, sid):
        return {
            "@type": kind, "@id": f"{BASE_URL}/#{sid}", "name": name,
            # coordinates only where we have them from our own published map
            # link; the factory link resolves to a place id with no lat/long,
            # so it deliberately carries no geo rather than a guessed one
            **({"geo": {"@type": "GeoCoordinates",
                        "latitude": 30.079528, "longitude": 31.3132399}}
               if sid == "office" else {}),
            "parentOrganization": {"@id": ORG_ID},
            "address": {"@type": "PostalAddress", "streetAddress": street,
                        "addressLocality": city,
                        "addressRegion": o["office_region"] if sid == "office" else o["region"],
                        "addressCountry": o["country"]},
        }

    org = {
        "@type": ["Organization", "MedicalBusiness"], "@id": ORG_ID,
        "name": o["name"], "legalName": o["legal"], "description": o["desc"],
        # The names people actually search for. schema.org's own property for
        # this, so it is not keyword stuffing and it changes nothing visible —
        # it just tells Google these strings are the same company.
        "alternateName": o["alt_names"],
        "url": f"{BASE_URL}/", "foundingDate": FOUNDED,
        "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/assets/logos/EHS-app-icon.svg"},
        "image": f"{BASE_URL}/assets/img/factory-exterior.jpg",
        "address": {"@type": "PostalAddress", "streetAddress": o["office_street"],
                    "addressLocality": o["office_city"], "addressCountry": o["country"]},
        "areaServed": {"@type": "Country", "name": "Egypt"},
        "knowsLanguage": ["ar", "en"],
        "contactPoint": [{
            "@type": "ContactPoint",
            "contactType": "sales",
            "telephone": PHONE_E164,
            "email": EMAIL_ADDRESS,
            "url": f"https://wa.me/{WHATSAPP_NUMBER}",
            "availableLanguage": ["ar", "en"],
        }],
        "location": [
            place("Place", o["office_name"], o["office_street"], o["office_city"], "office"),
            place("Place", o["factory_name"], o["factory_street"], o["factory_city"], "factory"),
        ],
    }
    social = [u for u in SOCIAL.values() if u]
    if social:
        org["sameAs"] = social

    website = {
        "@type": "WebSite", "@id": WEBSITE_ID, "url": f"{BASE_URL}/",
        "name": o["name"], "publisher": {"@id": ORG_ID},
        "inLanguage": ["en", "ar"],
    }

    page_type = "CollectionPage" if slug in SD_COLLECTIONS else (
        "FAQPage" if slug == "faq" else (
            "ContactPage" if slug == "contact" else (
                "AboutPage" if slug == "about" else "WebPage")))
    webpage = {
        "@type": page_type, "@id": f"{url}#webpage", "url": url,
        "name": title, "description": desc,
        "isPartOf": {"@id": WEBSITE_ID}, "about": {"@id": ORG_ID},
        "inLanguage": STR[lang]["lang"],
    }

    graph = [org, website, webpage]

    # Breadcrumbs — home > (section) > page
    if slug != "index":
        trail, cur = [], slug
        while cur in SD_PARENT:
            cur = SD_PARENT[cur]
            trail.insert(0, cur)
        items, pos = [], 1
        items.append({"@type": "ListItem", "position": pos,
                      "name": STR[lang]["nav_home"], "item": home})
        for step in trail:
            pos += 1
            items.append({"@type": "ListItem", "position": pos,
                          "name": _nav_label(lang, step), "item": _page_url(lang, step)})
        pos += 1
        items.append({"@type": "ListItem", "position": pos, "name": _nav_label(lang, slug)})
        graph.append({"@type": "BreadcrumbList", "@id": f"{url}#breadcrumb",
                      "itemListElement": items})
        webpage["breadcrumb"] = {"@id": f"{url}#breadcrumb"}

    # Product pages
    if slug in SD_PRODUCTS:
        p = SD_PRODUCTS[slug]
        graph.append({
            "@type": "Product", "@id": f"{url}#product", "name": p[lang],
            "description": desc,
            "image": f"{BASE_URL}/assets/img/{p['img']}",
            "brand": {"@type": "Brand", "name": p["brand"]},
            "manufacturer": {"@id": ORG_ID},
            "countryOfOrigin": {"@type": "Country", "name": "Egypt"},
            "category": "Medical device",
            "isRelatedTo": {"@id": ORG_ID},
            "mainEntityOfPage": {"@id": f"{url}#webpage"},
        })

    # FAQ page — questions and answers lifted straight from the page content
    if slug == "faq" and body:
        qa = []
        for m in FAQ_RE.finditer(body):
            q, a = _plain(m.group("q")), _plain(m.group("a"))
            if q and a:
                qa.append({"@type": "Question", "name": q,
                           "acceptedAnswer": {"@type": "Answer", "text": a}})
        if qa:
            webpage["mainEntity"] = qa

    payload = {"@context": "https://schema.org", "@graph": graph}
    return ('<script type="application/ld+json">'
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            + "</script>\n")


# --------------------------------------------------------------- WebP delivery
# Every photo is shipped as both .jpg and .webp. Browsers that understand WebP
# take the smaller file; everything else falls back to the original JPEG, so no
# visitor is ever left without an image.
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I)
IMG_SRC_RE = re.compile(r'\ssrc="([^"]+)"', re.I)


def webp_sources(html):
    """Wrap each JPEG <img> in a <picture> offering a WebP alternative.
    Only rewrites when the .webp file actually exists on disk."""
    def repl(m):
        tag = m.group(0)
        src_m = IMG_SRC_RE.search(tag)
        if not src_m:
            return tag
        src = src_m.group(1)
        if not src.lower().endswith((".jpg", ".jpeg")):
            return tag
        idx = src.find("assets/")
        if idx == -1:
            return tag
        rel = src[idx:]
        stem = os.path.splitext(rel)[0]
        if not os.path.exists(os.path.join(SITE, stem + ".webp")):
            return tag
        webp_src = os.path.splitext(src)[0] + ".webp"
        return (f'<picture><source srcset="{webp_src}" type="image/webp">'
                f"{tag}</picture>")
    return IMG_TAG_RE.sub(repl, html)


def head(lang, slug, jsonld="", robots=""):
    s = STR[lang]
    title, desc = META[lang][slug]
    a = "assets" if lang == "en" else "../assets"
    en_url = _page_url("en", slug)
    ar_url = _page_url("ar", slug)
    canonical = en_url if lang == "en" else ar_url
    # Share image: a product page shares its own product, not a stock photo of a
    # different one. Kept as JPEG — social scrapers are inconsistent with WebP.
    if slug in SD_PRODUCTS:
        og_img = f"{BASE_URL}/assets/img/{SD_PRODUCTS[slug]['img']}"
    else:
        og_img = f"{BASE_URL}/assets/img/{OG_IMAGES.get(slug, OG_DEFAULT)}"
    og_type = "product" if slug in SD_PRODUCTS else "website"
    return f"""<!doctype html>
<html lang="{s['lang']}" dir="{s['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{robots}<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="ar" href="{ar_url}">
<link rel="alternate" hreflang="x-default" href="{en_url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="EHS — Egyptian Hospital Supplies">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:alt" content="{title}">
<meta property="og:locale" content="{s['locale']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<meta name="theme-color" content="#4F7A12">
<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48 64x64">
<link rel="icon" type="image/svg+xml" href="{a}/logos/EHS-app-icon.svg">
<link rel="icon" type="image/png" sizes="512x512" href="/favicon.png">
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
{jsonld}</head>
<body>
<div class="loader" id="ehs-loader" role="presentation" aria-hidden="true">
  <svg class="loader__ribbon" viewBox="0 0 1200 620" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
    <path pathLength="1" d="M-120 400C140 190 320 180 520 330S770 560 930 400S1140 180 1340 300"/>
  </svg>
  <div class="loader__center">
    <img class="loader__logo" src="{a}/logos/EHS-logo-white.svg?v={ASSET_V}" alt="" width="762" height="114">
  </div>
</div>
<a class="skip-link" href="#main">{s['skip']}</a>
<div class="curtain" id="ehs-curtain" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
"""


def header_html(lang, slug):
    s = STR[lang]
    a = "assets" if lang == "en" else "../assets"
    active = PAGES.get(slug, {}).get("nav", "")
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
      <img class="brand__lockup" src="{a}/logos/EHS-logo.svg?v={ASSET_V}" alt="EHS — {s['brand_name']}" width="762" height="114">
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
        items.append('<a class="fab__item" href="%s" aria-label="%s">'
                     '<span class="fab__label">%s</span><span class="fab__dot">%s</span></a>'
                     % (mailto(s["mail_subject"], s["wa_prefill"]),
                        s["mail_label"], s["mail_label"], ICONS["mail"]))
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
        <span class="logo-reg"><img class="footer__logo" src="{a}/logos/EHS-logo-white.svg?v={ASSET_V}" alt="EHS — {s['brand_name']}" width="762" height="114"><span class="reg" aria-hidden="true">&reg;</span></span>
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
MAILBULK_RE = re.compile(r"\{\{MAILBULK:([^}]+)\}\}")


def mailto(subject, body):
    """mailto: URL for an href. The separator is written as &amp; because the
    result goes straight into an HTML attribute."""
    return (f"mailto:{EMAIL_ADDRESS}?subject={quote(subject, safe='')}"
            f"&amp;body={quote(body, safe='')}")


def build_page(lang, slug):
    src = os.path.join(ROOT, "content", lang, f"{slug}.html")
    with open(src, encoding="utf-8") as f:
        body = f.read()
    a = "assets" if lang == "en" else "../assets"
    body = body.replace("{{A}}", a)
    body = body.replace("{{WA_URL}}", f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(STR[lang]['wa_prefill'])}")
    body = body.replace("{{WA_NUMBER}}", WHATSAPP_NUMBER)
    body = body.replace("{{PHONE}}", PHONE_DISPLAY)
    body = body.replace("{{PHONE_HREF}}", f"tel:{PHONE_E164}")
    body = body.replace("{{EMAIL}}", EMAIL_ADDRESS)
    body = body.replace("{{EMAIL_HREF}}", f"mailto:{EMAIL_ADDRESS}")
    body = body.replace("{{MAIL_URL}}", mailto(STR[lang]["mail_subject"], STR[lang]["wa_prefill"]))
    body = MAILBULK_RE.sub(
        lambda m: mailto(f"{STR[lang]['mail_bulk_subject']} — {m.group(1)}",
                         STR[lang]["wa_bulk_prefix"] + m.group(1)),
        body)
    body = WABULK_RE.sub(
        lambda m: f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(STR[lang]['wa_bulk_prefix'] + m.group(1))}",
        body)
    body = body.replace("{{WAVE_SMALL}}", WAVE_SMALL)
    body = body.replace("{{WAVE}}", WAVE)
    body = ICON_RE.sub(lambda m: ICONS[m.group(1)], body)
    html = (head(lang, slug, jsonld=json_ld(lang, slug, body))
            + header_html(lang, slug) + body + footer_html(lang, slug))
    html = webp_sources(html)
    html = _clean_links(html, lang)
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
        new = new[: -len(".html")] if new.endswith(".html") else new
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


# ------------------------------------------------------------------- 404 page
# Apache serves this file for any unknown URL (see .htaccess ErrorDocument).
# Because the browser's address bar still shows the URL the visitor typed,
# every link and asset path on this one page has to be absolute — relative
# paths would resolve against the missing URL and the page would load unstyled.

BODY_404 = {
    "en": """
<main id="main">
<section class="page-hero">
  <div class="support-line" aria-hidden="true">{WAVE}</div>
  <div class="container">
    <div class="page-hero__content">
      <span class="eyebrow">Error 404</span>
      <h1 class="h1">This page isn't here.</h1>
      <p class="lead">The link may be out of date, or the address slightly mistyped.
         Everything below will get you back on track.</p>
      <div class="hero__actions" style="display:flex; flex-wrap:wrap; gap:12px; margin-block-start:28px;">
        <a class="btn btn--primary" href="index.html">Back to home</a>
        <a class="btn btn--outline" href="products.html">Browse products</a>
        <a class="btn btn--outline" href="contact.html">Contact EHS</a>
      </div>
    </div>
  </div>
</section>
<section class="section--tight" style="padding-block-end: clamp(64px, 9vw, 110px);">
  <div class="container maxw-820">
    <h2 class="h3">Popular pages</h2>
    <ul class="link-list" style="margin-block-start:16px; line-height:2.2;">
      <li><a href="medpress.html">MedPress — compression solutions</a></li>
      <li><a href="orthopedic.html">MasterCast — orthopedic range</a></li>
      <li><a href="size-guide.html">Size &amp; measurement guide</a></li>
      <li><a href="factory.html">The factory</a></li>
      <li><a href="professionals.html">Professional &amp; distributor enquiries</a></li>
    </ul>
  </div>
</section>
</main>
""",
    "ar": """
<main id="main">
<section class="page-hero">
  <div class="support-line" aria-hidden="true">{WAVE}</div>
  <div class="container">
    <div class="page-hero__content">
      <span class="eyebrow">خطأ 404</span>
      <h1 class="h1">هذه الصفحة غير موجودة.</h1>
      <p class="lead">قد يكون الرابط قديمًا أو به خطأ بسيط في الكتابة.
         الروابط التالية ستعيدك إلى المسار الصحيح.</p>
      <div class="hero__actions" style="display:flex; flex-wrap:wrap; gap:12px; margin-block-start:28px;">
        <a class="btn btn--primary" href="index.html">العودة للرئيسية</a>
        <a class="btn btn--outline" href="products.html">تصفّح المنتجات</a>
        <a class="btn btn--outline" href="contact.html">تواصل معنا</a>
      </div>
    </div>
  </div>
</section>
<section class="section--tight" style="padding-block-end: clamp(64px, 9vw, 110px);">
  <div class="container maxw-820">
    <h2 class="h3">صفحات مهمة</h2>
    <ul class="link-list" style="margin-block-start:16px; line-height:2.2;">
      <li><a href="medpress.html">ميدبريس — حلول الضغط الطبي</a></li>
      <li><a href="orthopedic.html">ماستركاست — مجموعة العظام</a></li>
      <li><a href="size-guide.html">دليل المقاسات والقياس</a></li>
      <li><a href="factory.html">المصنع</a></li>
      <li><a href="professionals.html">استفسارات المؤسسات والموزّعين</a></li>
    </ul>
  </div>
</section>
</main>
""",
}


_LINK_RE = re.compile(r'\b(href|action)="([^"]*)"')


def _clean_links(html, lang):
    """Point every internal page link at the URL the edge actually serves.

    Cloudflare drops the .html extension, so a link ending in .html costs the
    visitor a 301 on every click. Rewriting here — on the finished page rather
    than in the templates — catches nav, footer, breadcrumbs, product cards and
    body copy in one pass, whichever data structure the slug came from.

    Links come out root-absolute so they resolve identically from /, from /ar/,
    and from a 404 served at an arbitrary depth.
    """
    base_dir = "/" if lang == "en" else "/ar/"

    def sub(m):
        attr, val = m.group(1), m.group(2)
        if val.startswith(("http://", "https://", "//", "mailto:", "tel:",
                           "#", "data:", "javascript:")):
            return m.group(0)
        path, hsep, frag = val.partition("#")
        path, qsep, query = path.partition("?")
        if not path.endswith(".html"):
            return m.group(0)
        if not path.startswith("/"):
            path = posixpath.normpath(posixpath.join(base_dir, path))
        clean = (path[: -len("index.html")] if path.endswith("/index.html")
                 else path[: -len(".html")])
        return f'{attr}="{clean}{qsep}{query}{hsep}{frag}"'

    return _LINK_RE.sub(sub, html)


def _absolutize(html, lang):
    """Rewrite every relative link/asset path to a root-absolute one."""
    if lang == "en":
        html = re.sub(r'(href|src|srcset)="assets/', r'\1="/assets/', html)
        html = re.sub(r'href="ar/', 'href="/ar/', html)
        html = re.sub(r'(href|src)="(?!/|https?:|#|mailto:|tel:|data:)([\w.-]+\.html)',
                      r'\1="/\2', html)
    else:
        html = re.sub(r'(href|src|srcset)="\.\./assets/', r'\1="/assets/', html)
        html = re.sub(r'href="\.\./([\w.-]+\.html)', r'href="/\1', html)
        html = re.sub(r'(href|src)="(?!/|https?:|#|mailto:|tel:|data:|\.\./)([\w.-]+\.html)',
                      r'\1="/ar/\2', html)
    return html


def write_404():
    count = 0
    for lang in ("en", "ar"):
        body = BODY_404[lang].replace("{WAVE}", WAVE)
        html = (head(lang, "404", jsonld="",
                     robots='<meta name="robots" content="noindex, follow">\n')
                + header_html(lang, "404") + body + footer_html(lang, "404"))
        html = webp_sources(html)
        html = _absolutize(html, lang)
        html = _clean_links(html, lang)
        outdir = SITE if lang == "en" else os.path.join(SITE, "ar")
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "404.html"), "w", encoding="utf-8") as f:
            f.write(html)
        count += 1
    return count


def write_sitemap():
    """Sitemap listing every real page in both languages, each carrying its
    hreflang alternates. Redirect stubs are left out on purpose — they are
    noindex and only exist to forward old URLs."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for slug in PAGES:
        en = _page_url("en", slug)
        ar = _page_url("ar", slug)
        for lang, url in (("en", en), ("ar", ar)):
            # lastmod comes from the source file's own timestamp, so it says
            # when the page really changed rather than when we last built
            src = os.path.join(ROOT, "content", lang, f"{slug}.html")
            stamp = datetime.date.fromtimestamp(os.path.getmtime(src)).isoformat()
            lines.append("  <url>")
            lines.append(f"    <loc>{url}</loc>")
            lines.append(f"    <lastmod>{stamp}</lastmod>")
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="ar" href="{ar}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en}"/>')
            lines.append("  </url>")
    lines.append("</urlset>")
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(PAGES) * 2


def write_robots():
    """Allow the site, and explicitly refuse the build tree and internal files.
    Belt and braces: a correct deploy contains none of these, but a robots rule
    costs nothing and stops a crawler indexing them if one ever slips through."""
    txt = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "# Never crawl the generator source or internal files\n"
        "Disallow: /_build/\n"
        "Disallow: /_to_delete/\n"
        "Disallow: /README.md\n"
        "Disallow: /render.yaml\n"
        "Disallow: /.git/\n"
        "Disallow: /CLAUDE-SECURITY-\n"
        "\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n"
    )
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(txt)


if __name__ == "__main__":
    built = []
    for lang in ("en", "ar"):
        for slug in PAGES:
            src = os.path.join(ROOT, "content", lang, f"{slug}.html")
            if not os.path.exists(src):
                print(f"!! missing content: {lang}/{slug}.html", file=sys.stderr)
                continue
            built.append(build_page(lang, slug))
    stubs = write_redirects()
    errpages = write_404()
    urls = write_sitemap()
    write_robots()
    print(f"Built {len(built)} pages + {stubs} redirect stubs + {errpages} error pages, "
          f"{urls} sitemap URLs, robots.txt.")
