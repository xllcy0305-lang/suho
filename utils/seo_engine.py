# -*- coding: utf-8 -*-
"""SEO 标题生成引擎 — 产品精准匹配 + AI 评分"""

import random
import itertools
import logging

from config import TARGET_TITLE_COUNT, MAX_SAMPLE_COMBOS, CN_QUALITIES, CN_FEATURES, THAI_PLATFORMS, CN_PLATFORMS

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50000

# ═══════════════════════════════════════════════════════════════════════════════
# 产品映射库：中文产品名 → 泰语/英语/材质/场景/长尾词
# ═══════════════════════════════════════════════════════════════════════════════
PRODUCT_MAPPING = {
    # ── 居家/户外 ──
    "月亮椅": {
        "thai": ["เก้าอี้พระจันทร์", "เก้าอี้นั่งพระจันทร์", "Moon Chair"],
        "english": ["moon chair", "outdoor moon chair"],
        "category": "home_outdoor",
        "materials": ["อลูมิเนียม", "ผ้า Oxford 600D", "ผ้า Canvas", "ผ้า Ripstop", "โพลีเอสเตอร์"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "ชายหาด", "สนามหญ้า", "ระเบียงคอนโด", "สวนหลังบ้าน", "ลานกางเต็นท์"],
        "longtail": ["นั่งสบาย", "น้ำหนักเบาพกพา", "พับเก็บง่าย", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "พร้อมส่งด่วน"],
    },
    "折叠桌": {
        "thai": ["โต๊ะพับ", "โต๊ะพับสนาม", "โต๊ะพกพา"],
        "english": ["folding table", "portable table"],
        "category": "home_outdoor",
        "materials": ["อลูมิเนียม", "ไม้สนแท้", "ไม้ไผ่", "สแตนเลส 304", "พลาสติก PP"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "ตลาดนัด", "ออฟฟิศ", "ระเบียงคอนโด"],
        "longtail": ["พับเก็บง่าย", "ติดตั้งเร็ว", "น้ำหนักเบา", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "蛋卷桌": {
        "thai": ["โต๊ะไม้พับ", "โต๊ะแคมป์ปิ้ง", "โต๊ะไม้ไผ่พับ"],
        "english": ["roll up table", "bamboo camping table"],
        "category": "home_outdoor",
        "materials": ["ไม้สนแท้", "ไม้ไผ่", "อลูมิเนียม", "สแตนเลส 304"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "ชายหาด", "สวนหลังบ้าน"],
        "longtail": ["ลายไม้สวยงาม", "พับเก็บง่าย", "ทนทานใช้งานกลางแจ้ง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "帐篷": {
        "thai": ["เต็นท์แคมป์ปิ้ง", "เต็นท์สนาม", "เต็นท์กางนอน"],
        "english": ["camping tent", "outdoor tent"],
        "category": "home_outdoor",
        "materials": ["โพลีเอสเตอร์", "ผ้า Ripstop", "ผ้า Canvas", "อลูมิเนียม"],
        "scenes": ["แคมป์ปิ้ง", "ลานกางเต็นท์", "ชายหาด", "ภูเขา", "ป่า"],
        "longtail": ["กันฝนกันลม", "ติดตั้งเร็ว", "น้ำหนักเบาพกพา", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "Outdoor ขายดี"],
    },
    "收纳箱": {
        "thai": ["กล่องเก็บของ", "กล่องอเนกประสงค์", "กล่องจัดระเบียบ"],
        "english": ["storage box", "organization box"],
        "category": "home_outdoor",
        "materials": ["พลาสติก PP", "ผ้า Canvas", "ไม้สนแท้"],
        "scenes": ["ออฟฟิศ", "ห้องนอน", "ห้องครัว", "ระเบียงคอนโด"],
        "longtail": ["จัดระเบียบดี", "ประหยัดพื้นที่", "ทนทานใช้งานนาน", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "吊床": {
        "thai": ["เปลญวน", "เปลสนาม", "เปลแขวน"],
        "english": ["hammock", "camping hammock"],
        "category": "home_outdoor",
        "materials": ["ผ้า Ripstop", "โพลีเอสเตอร์", "ผ้า Canvas", "ไนลอน"],
        "scenes": ["แคมป์ปิ้ง", "ชายหาด", "สวนหลังบ้าน", "ระเบียงคอนโด"],
        "longtail": ["นั่งสบาย", "น้ำหนักเบาพกพา", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "折叠躺椅": {
        "thai": ["เก้าอี้นอนพับ", "เก้าอี้สนามพับ", "เก้าอี้เอนหลัง"],
        "english": ["folding lounge chair", "reclining camp chair"],
        "category": "home_outdoor",
        "materials": ["อลูมิเนียม", "ผ้า Oxford 600D", "โพลีเอสเตอร์", "ผ้า Canvas"],
        "scenes": ["แคมป์ปิ้ง", "ชายหาด", "ปิกนิก", "สวนหลังบ้าน", "สระว่ายน้ำ"],
        "longtail": ["นั่งสบายปรับเอนได้", "น้ำหนักเบาพกพา", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "藤编家具": {
        "thai": ["เฟอร์นิเจอร์หวายเทียม", "เก้าอี้หวาย", "ชุดหวายสนาม"],
        "english": ["rattan furniture", "wicker furniture set"],
        "category": "home_outdoor",
        "materials": ["หวายเทียม PE", "อลูมิเนียม", "สแตนเลส 304"],
        "scenes": ["ระเบียงคอนโด", "สวนหลังบ้าน", "รีสอร์ท", "ร้านกาแฟ", "สนามหญ้า"],
        "longtail": ["ดีไซน์สวยงาม", "ทนทานแดดฝน", "คุณภาพดีเยี่ยม", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "收纳架": {
        "thai": ["ชั้นวางของ", "ชั้นเก็บของ", "ชั้นวางอเนกประสงค์"],
        "english": ["storage shelf", "organizer rack"],
        "category": "home_outdoor",
        "materials": ["สแตนเลส 304", "อลูมิเนียม", "ไม้สนแท้", "พลาสติก PP"],
        "scenes": ["ออฟฟิศ", "ห้องนอน", "ห้องครัว", "ห้องน้ำ", "ระเบียงคอนโด"],
        "longtail": ["จัดระเบียบดี", "ประหยัดพื้นที่", "ทนทานใช้งานนาน", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "户外桌椅套装": {
        "thai": ["ชุดโต๊ะเก้าอี้สนาม", "ชุดโต๊ะเก้าอี้แคมป์ปิ้ง", "ชุดเฟอร์นิเจอร์สนาม"],
        "english": ["outdoor furniture set", "camping table chair set"],
        "category": "home_outdoor",
        "materials": ["อลูมิเนียม", "ผ้า Oxford 600D", "ไม้ไผ่", "สแตนเลส 304"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "สวนหลังบ้าน", "ระเบียงคอนโด", "รีสอร์ท"],
        "longtail": ["ครบเซ็ตคุ้มค่า", "น้ำหนักเบาพกพา", "ทนทานใช้งานกลางแจ้ง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },

    # ── 数码3C ──
    "智能手表": {
        "thai": ["สมาร์ทวอทช์", "นาฬิกาอัจฉริยะ", "Smart Watch"],
        "english": ["smart watch", "smartwatch"],
        "category": "electronics",
        "materials": ["กันน้ำ IP68", "Bluetooth 5.3", "แบตอึด 5000mAh", "สายซิลิโคน", "กระจก Gorilla Glass"],
        "scenes": ["ออกกำลังกาย", "วิ่งมาราธอน", "ฟิตเนส", "ทำงาน Office", "ขับรถ"],
        "longtail": ["ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "ทนทานใช้งานนาน", "น้ำหนักเบาพกพา", "ของแท้ 100%"],
    },
    "蓝牙耳机": {
        "thai": ["หูฟังบลูทูธ", "หูฟังไร้สาย", "หูฟัง TWS"],
        "english": ["bluetooth earphone", "wireless earbuds"],
        "category": "electronics",
        "materials": ["Bluetooth 5.3", "ANC ตัดเสียงรบกวน", "ไร้สาย TWS", "กันน้ำ IPX5", "แบตอึด 30 ชม."],
        "scenes": ["ฟังเพลง", "เล่นเกม", "ออกกำลังกาย", "เรียนออนไลน์", "ขับรถ"],
        "longtail": ["คุณภาพเสียงดีเยี่ยม", "ใส่สบายไม่เจ็บหู", "เสียงชัดใส", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "手机壳": {
        "thai": ["เคสมือถือ", "เคสโทรศัพท์", "กรอบมือถือ"],
        "english": ["phone case", "mobile phone case"],
        "category": "electronics",
        "materials": ["TPU นิ่ม", "ซิลิโคน", "หนัง PU", "เคสกันกระแทก", "กระจก Tempered"],
        "scenes": ["ปกป้องมือถือ", "ของขวัญ", "แฟชั่น", "ทุกวัน"],
        "longtail": ["กันกระแทกดีเยี่ยม", "ลายสวยงาม", "พอดีเครื่อง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "充电宝": {
        "thai": ["พาวเวอร์แบงค์", "แบตสำรอง", "Power Bank"],
        "english": ["power bank", "portable charger"],
        "category": "electronics",
        "materials": ["แบตอึด 20000mAh", "PD 65W Fast Charge", "USB-C", "ลิเธียมโพลิเมอร์"],
        "scenes": ["เดินทาง", "ท่องเที่ยว", "ทำงาน", "ออกกำลังกาย", "แคมป์ปิ้ง"],
        "longtail": ["ชาร์จเร็วทันใจ", "แบตอึดทนนาน", "น้ำหนักเบาพกพา", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "蓝牙音箱": {
        "thai": ["ลำโพงบลูทูธ", "ลำโพงพกพา", "Speaker ไร้สาย"],
        "english": ["bluetooth speaker", "portable speaker"],
        "category": "electronics",
        "materials": ["กันน้ำ IPX7", "Bluetooth 5.3", "แบตอึด 12 ชม.", "ไดรเวอร์ 40mm"],
        "scenes": ["ฟังเพลง", "ปาร์ตี้", "แคมป์ปิ้ง", "ชายหาด", "ห้องนอน"],
        "longtail": ["เสียงเบสหนักแน่น", "น้ำหนักเบาพกพา", "กันน้ำกันฝุ่น", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "机械键盘": {
        "thai": ["คีย์บอร์ด机械", "คีย์บอร์ดเกมมิ่ง", "Mechanical Keyboard"],
        "english": ["mechanical keyboard", "gaming keyboard"],
        "category": "electronics",
        "materials": ["RGB 16 ล้านสี", "Switch Blue/Red/Brown", "PBT Keycap", "USB-C", "อลูมิเนียม"],
        "scenes": ["เล่นเกม", "ทำงาน Office", "พิมพ์งาน", "程序员"],
        "longtail": ["เสียงคลิกเพราะมาก", "ทนทานกดได้ 50 ล้านครั้ง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "RGB สวยมาก"],
    },
    "数据线": {
        "thai": ["สายชาร์จ", "สาย USB-C", "สายชาร์จเร็ว"],
        "english": ["charging cable", "USB-C cable"],
        "category": "electronics",
        "materials": ["PD 65W Fast Charge", "USB-C", "ไนลอนถัก", "อลูมิเนียม"],
        "scenes": ["ชาร์จมือถือ", "ชาร์จโน๊ตบุ๊ค", "เดินทาง", "ทำงาน"],
        "longtail": ["ชาร์จเร็วทันใจ", "ทนทานใช้งานนาน", "สายแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },

    # ── 美妆个护 ──
    "防晒霜": {
        "thai": ["กันแดด", "ครีมกันแดด", "Sunscreen"],
        "english": ["sunscreen", "sunblock cream"],
        "category": "fashion_beauty",
        "materials": ["SPF50+ PA++++", "SPF30 PA+++", "วิตามินซี", "Aloe Vera", "Niacinamide"],
        "scenes": ["กันแดดทุกวัน", "ออกกำลังกาย", "ท่องเที่ยว", "ชายหาด", "แต่งหน้าทำงาน"],
        "longtail": ["ผิวขาวใส", "กันแดดดีเยี่ยม", "ไม่เหนียวเหนอะหนะ", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ผิวแพ้ง่ายใช้ได้"],
    },
    "面霜": {
        "thai": ["ครีมบำรุงผิว", "มอยส์เจอไรเซอร์", "ครีมทาหน้า"],
        "english": ["face cream", "moisturizer"],
        "category": "fashion_beauty",
        "materials": ["คอลลาเจน", "วิตามินซี", "เซราไมด์", "กรดไฮยาลูรอนิก", "Retinol", "Niacinamide"],
        "scenes": ["ผิวขาวใส", "ลดรอยสิว", "บำรุงผิวทุกวัน", "สาวออฟฟิศ"],
        "longtail": ["ผิวชุ่มชื่น", "ลดริ้วรอย", "คุณภาพดีมาก", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ผิวแพ้ง่ายใช้ได้"],
    },
    "口红": {
        "thai": ["ลิปสติก", "ลิปสี", "ลิปแมท"],
        "english": ["lipstick", "matte lipstick"],
        "category": "fashion_beauty",
        "materials": ["Vitamin E", "Moisturizing", "Long-lasting", "Non-drying"],
        "scenes": ["แต่งหน้าทำงาน", "ออกงานกลางคืน", "ลุค Everyday", "วัยรุ่น"],
        "longtail": ["สีสวยติดทนนาน", "ไม่แห้งปาก", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ยอดนิยม 2026"],
    },
    "香水": {
        "thai": ["น้ำหอม", "น้ำหอมผู้หญิง", "น้ำหอมผู้ชาย"],
        "english": ["perfume", "fragrance"],
        "category": "fashion_beauty",
        "materials": ["Alcohol-free", "Essential Oil", "Natural Extract"],
        "scenes": ["ออกงานกลางคืน", "ทำงาน", "ออกเดท", "ทุกวัน"],
        "longtail": ["กลิ่นหอมติดทนนาน", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ของแท้แบรนด์ดัง", "ยอดนิยม 2026"],
    },

    # ── 母婴 ──
    "婴儿推车": {
        "thai": ["รถเข็นเด็ก", "รถเข็นทารก", "Stroller"],
        "english": ["baby stroller", "infant stroller"],
        "category": "mother_baby",
        "materials": ["อลูมิเนียม", "ผ้า Organic Cotton", "ผ้าฝ้าย 100%", "ABS ปลอดสารพิษ"],
        "scenes": ["เด็กแรกเกิด", "ทารก 0-6 เดือน", "วัยหัดเดิน", "คุณแม่มือใหม่"],
        "longtail": ["ปลอดภัยสำหรับเด็ก", "พับเก็บง่าย", "น้ำหนักเบา", "ขายดีอันดับ 1", "ราคาถูกปลอดภัย", "คุณแม่แนะนำ"],
    },
    "纸尿裤": {
        "thai": ["ผ้าอ้อมสำเร็จรูป", "แพมเพิส", "Diaper"],
        "english": ["baby diaper", "nappy"],
        "category": "mother_baby",
        "materials": ["ผ้า Organic Cotton", "BPA-free Food Grade", "Non-toxic", "Super Absorbent"],
        "scenes": ["เด็กแรกเกิด", "ทารก 0-6 เดือน", "วัยหัดเดิน", "นอนหลับ"],
        "longtail": ["ซึมซับดีเยี่ยม", "ไม่ระคายเคือง", "ปลอดภัยสำหรับเด็ก", "ขายดีอันดับ 1", "ราคาถูกปลอดภัย"],
    },
    "奶瓶": {
        "thai": ["ขวดนมเด็ก", "ขวดนมทารก", "Baby Bottle"],
        "english": ["baby bottle", "feeding bottle"],
        "category": "mother_baby",
        "materials": ["BPA-free Food Grade", "PP Food Grade", "Silicone ทางการแพทย์", "ผ้ามัสลิน"],
        "scenes": ["เด็กแรกเกิด", "ให้นมลูก", "ทารก 0-6 เดือน", "คุณแม่มือใหม่"],
        "longtail": ["ปลอดภัยสำหรับเด็ก", "ทำความสะอาดง่าย", "ทนทานใช้งานนาน", "ขายดีอันดับ 1", "คุณแม่แนะนำ"],
    },
    "爬行垫": {
        "thai": ["เบาะรองคลาน", "เสื่อรองคลาน", "Play Mat"],
        "english": ["baby play mat", "crawling mat"],
        "category": "mother_baby",
        "materials": ["EVA ปลอดสารพิษ", "XPE Foam", "Non-toxic", "กันน้ำ"],
        "scenes": ["เด็กแรกเกิด", "วัยหัดเดิน", "เล่นสนุก", "คุณแม่มือใหม่"],
        "longtail": ["ปลอดภัยสำหรับเด็ก", "กันกระแทกดี", "ทำความสะอาดง่าย", "ขายดีอันดับ 1", "คุณแม่แนะนำ"],
    },

    # ── 食品 ──
    "零食": {
        "thai": ["ขนมขบเคี้ยว", "ขนมทานเล่น", "Snack"],
        "english": ["snack", "chips"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "น้ำตาล 0%", "Non-GMO", "HACCP รับรอง"],
        "scenes": ["ลดน้ำหนัก", "ดูแลสุขภาพ", "เด็กนักเรียน", "สาวออฟฟิศ", "ทุกเพศทุกวัย"],
        "longtail": ["อร่อยถูกใจ", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
    "咖啡": {
        "thai": ["กาแฟสำเร็จรูป", "กาแฟสด", "กาแฟคั่ว"],
        "english": ["instant coffee", "ground coffee"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "น้ำตาล 0%", "Non-GMO", "โปรตีนสูง"],
        "scenes": ["ดูแลสุขภาพ", "ทำงาน Office", "สาวออฟฟิศ", "ทุกเพศทุกวัย"],
        "longtail": ["หอมอร่อยเข้มข้น", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
    "茶叶": {
        "thai": ["ชาไทย", "ชาเขียว", "ชาสมุนไพร"],
        "english": ["thai tea", "green tea"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "สารสกัดจากธรรมชาติ", "Non-GMO"],
        "scenes": ["ดูแลสุขภาพ", "ลดน้ำหนัก", "ผู้สูงอายุ", "ทุกเพศทุกวัย"],
        "longtail": ["หอมอร่อย", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
    "蜂蜜": {
        "thai": ["น้ำผึ้งแท้", "น้ำผึ้งป่า", "น้ำผึ้งดอกไม้"],
        "english": ["pure honey", "organic honey"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "สารสกัดจากธรรมชาติ", "Non-GMO", "HACCP รับรอง"],
        "scenes": ["ดูแลสุขภาพ", "บำรุงสมอง", "เสริมภูมิคุ้มกัน", "ทุกเพศทุกวัย"],
        "longtail": ["หวานหอมจากธรรมชาติ", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
}


def _sample(pool: list, max_items: int) -> list:
    if len(pool) <= max_items:
        return pool
    return random.sample(pool, max_items)


def _ai_score(title: str) -> int:
    score = 50
    if 30 <= len(title) <= 80:
        score += 15
    elif len(title) > 100:
        score -= 10
    if any(c.isdigit() for c in title):
        score += 10
    promo = ("ขายดี", "ราคาถูก", "ลดราคา", "พร้อมส่ง", "100%", "高品质", "热销", "特价")
    if any(w in title for w in promo):
        score += 8
    if any(kw in title for kw in ("IP68", "Bluetooth", "SPF", "4K", "USB", "PD")):
        score += 7
    return min(100, max(0, score))


def _match_product(product_cn: str, cat_data: dict) -> dict | None:
    """根据中文产品名匹配产品映射库，返回匹配的产品数据"""
    # 1. 精确匹配
    if product_cn in PRODUCT_MAPPING:
        return PRODUCT_MAPPING[product_cn]

    # 2. 模糊匹配：输入包含映射库的 key，或 key 包含输入
    for name, data in PRODUCT_MAPPING.items():
        if name in product_cn or product_cn in name:
            return data

    # 3. 在类目子类目中查找
    subs = cat_data.get("subcategories", [])
    bases = cat_data.get("base", [])
    for i, sub in enumerate(subs):
        if sub in product_cn or product_cn in sub:
            if i < len(bases):
                return {
                    "thai": [bases[i]],
                    "english": [],
                    "category": "",
                    "materials": cat_data.get("material_specs", []),
                    "scenes": cat_data.get("scene_audience", []),
                    "longtail": cat_data.get("longtail", []),
                }

    return None


def _get_generic_product(product_cn: str, cat_data: dict) -> dict:
    """无匹配时的通用方案：用类目词库但标记为通用"""
    return {
        "thai": [product_cn],
        "english": [],
        "category": "",
        "materials": cat_data.get("material_specs", []),
        "scenes": cat_data.get("scene_audience", []),
        "longtail": cat_data.get("longtail", []),
    }


def generate_thai_titles(product_cn: str, cat_data: dict, max_chars: int,
                          count: int = TARGET_TITLE_COUNT) -> list[dict]:
    """根据输入产品名生成精准泰语标题"""
    # 匹配产品
    prod = _match_product(product_cn, cat_data)
    if not prod:
        prod = _get_generic_product(product_cn, cat_data)

    bases = prod.get("thai", [])
    mats = prod.get("materials", [])
    scenes = prod.get("scenes", [])
    lts = prod.get("longtail", [])

    if not bases:
        return []

    # 补充类目通用长尾词（如果产品专属的不够）
    cat_lts = cat_data.get("longtail", [])
    for lt in cat_lts:
        if lt not in lts:
            lts.append(lt)

    titles_set: set[str] = set()
    sample_limit = max(3, int((MAX_SAMPLE_COMBOS / max(len(bases), 1)) ** 0.66))
    s_mats = _sample(mats, sample_limit) if mats else []
    s_scenes = _sample(scenes, sample_limit) if scenes else []
    iters = 0

    # 优先级1: base + material + scene + longtail
    if s_mats and s_scenes:
        for b, m, s, l in itertools.product(bases, s_mats, s_scenes, lts):
            t = f"{b} {m} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # 优先级2: base + material + longtail
    if len(titles_set) < count and iters < MAX_ITERATIONS and s_mats:
        for b, m, l in itertools.product(bases, s_mats, lts):
            t = f"{b} {m} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # 优先级3: base + scene + longtail
    if len(titles_set) < count and iters < MAX_ITERATIONS and s_scenes:
        for b, s, l in itertools.product(bases, s_scenes, lts):
            t = f"{b} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # 优先级4: base + longtail
    if len(titles_set) < count and iters < MAX_ITERATIONS:
        for b, l in itertools.product(bases, lts):
            t = f"{b} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    result = list(titles_set)
    random.shuffle(result)
    return [{"title": t, "chars": len(t), "score": _ai_score(t)} for t in result[:count]]


def generate_cn_titles(cat_data: dict, product_cn: str, max_chars: int,
                        count: int = TARGET_TITLE_COUNT) -> list[dict]:
    """根据输入产品名生成中文标题"""
    # 尝试匹配产品获取专属材质
    prod = _match_product(product_cn, cat_data)
    if prod and prod.get("materials"):
        mats = prod["materials"]
    else:
        mats = cat_data.get("material_specs", [])

    if not mats:
        return []

    templates = [
        lambda m, q, f: f"{product_cn} {m} {q} {f}",
        lambda m, q, f: f"{product_cn} {q} {f} {m}",
        lambda m, q, f: f"{q}{product_cn} {f} {m}",
        lambda m, q, f: f"{product_cn}{f} {m} {q}",
        lambda m, q, f: f"{product_cn} {m} {f}",
        lambda m, q, f: f"{q}{product_cn} {f}",
        lambda m, q, f: f"{product_cn} {f} {q}",
    ]

    s_mats = _sample(mats, 5)
    titles_set: set[str] = set()
    iters = 0

    for tpl in templates:
        for m, q, f in itertools.product(s_mats, CN_QUALITIES, CN_FEATURES):
            t = tpl(m, q, f)
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 2 or iters >= MAX_ITERATIONS:
                break
        if len(titles_set) >= count or iters >= MAX_ITERATIONS:
            break

    result = list(titles_set)
    random.shuffle(result)
    return [{"title": t, "chars": len(t), "score": _ai_score(t)} for t in result[:count]]


def dispatch(product_cn: str, plat_key: str, cat_data: dict, max_chars: int) -> list[dict]:
    if plat_key in THAI_PLATFORMS:
        return generate_thai_titles(product_cn, cat_data, max_chars)
    if plat_key in CN_PLATFORMS:
        return generate_cn_titles(cat_data, product_cn, max_chars)
    return []
