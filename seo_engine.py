# -*- coding: utf-8 -*-
"""SEO 标题生成引擎 — 产品精准匹配 + 平台差异化 + AI 评分"""

import random
import itertools
import logging

from config import TARGET_TITLE_COUNT, MAX_SAMPLE_COMBOS, CN_QUALITIES, CN_FEATURES

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 50000

# ═══════════════════════════════════════════════════════════════════════════════
# 产品映射库：中文产品名 → 泰语/英语/材质/场景/长尾词
# ═══════════════════════════════════════════════════════════════════════════════
PRODUCT_MAPPING = {
    # ── 居家/户外 ──
    "月亮椅": {
        "thai": ["เก้าอี้พระจันทร์", "เก้าอี้นั่งพระจันทร์", "Moon Chair"],
        "english": ["Moon Chair", "Outdoor Moon Chair", "Folding Moon Chair"],
        "category": "outdoor_camping",
        "materials": ["อลูมิเนียม", "ผ้า Oxford 600D", "ผ้า Canvas", "ผ้า Ripstop", "โพลีเอสเตอร์"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "ชายหาด", "สนามหญ้า", "ระเบียงคอนโด", "สวนหลังบ้าน", "ลานกางเต็นท์"],
        "longtail": ["นั่งสบาย", "น้ำหนักเบาพกพา", "พับเก็บง่าย", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "พร้อมส่งด่วน"],
    },
    "折叠桌": {
        "thai": ["โต๊ะพับ", "โต๊ะพับสนาม", "โต๊ะพกพา"],
        "english": ["Folding Table", "Portable Table", "Camping Folding Table"],
        "category": "outdoor_camping",
        "materials": ["อลูมิเนียม", "ไม้สนแท้", "ไม้ไผ่", "สแตนเลส 304", "พลาสติก PP"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "ตลาดนัด", "ออฟฟิศ", "ระเบียงคอนโด"],
        "longtail": ["พับเก็บง่าย", "ติดตั้งเร็ว", "น้ำหนักเบา", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "蛋卷桌": {
        "thai": ["โต๊ะไม้พับ", "โต๊ะแคมป์ปิ้ง", "โต๊ะไม้ไผ่พับ"],
        "english": ["Roll Up Table", "Bamboo Camping Table", "Portable Picnic Table"],
        "category": "outdoor_camping",
        "materials": ["ไม้สนแท้", "ไม้ไผ่", "อลูมิเนียม", "สแตนเลส 304"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "ชายหาด", "สวนหลังบ้าน"],
        "longtail": ["ลายไม้สวยงาม", "พับเก็บง่าย", "ทนทานใช้งานกลางแจ้ง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "帐篷": {
        "thai": ["เต็นท์แคมป์ปิ้ง", "เต็นท์สนาม", "เต็นท์กางนอน"],
        "english": ["Camping Tent", "Outdoor Tent", "Family Tent"],
        "category": "outdoor_camping",
        "materials": ["โพลีเอสเตอร์", "ผ้า Ripstop", "ผ้า Canvas", "อลูมิเนียม"],
        "scenes": ["แคมป์ปิ้ง", "ลานกางเต็นท์", "ชายหาด", "ภูเขา", "ป่า"],
        "longtail": ["กันฝนกันลม", "ติดตั้งเร็ว", "น้ำหนักเบาพกพา", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "Outdoor ขายดี"],
    },
    "收纳箱": {
        "thai": ["กล่องเก็บของ", "กล่องอเนกประสงค์", "กล่องจัดระเบียบ"],
        "english": ["Storage Box", "Organization Box", "Home Storage Container"],
        "category": "storage_organization",
        "materials": ["พลาสติก PP", "ผ้า Canvas", "ไม้สนแท้"],
        "scenes": ["ออฟฟิศ", "ห้องนอน", "ห้องครัว", "ระเบียงคอนโด"],
        "longtail": ["จัดระเบียบดี", "ประหยัดพื้นที่", "ทนทานใช้งานนาน", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "吊床": {
        "thai": ["เปลญวน", "เปลสนาม", "เปลแขวน"],
        "english": ["Hammock", "Camping Hammock", "Outdoor Hammock"],
        "category": "outdoor_camping",
        "materials": ["ผ้า Ripstop", "โพลีเอสเตอร์", "ผ้า Canvas", "ไนลอน"],
        "scenes": ["แคมป์ปิ้ง", "ชายหาด", "สวนหลังบ้าน", "ระเบียงคอนโด"],
        "longtail": ["นั่งสบาย", "น้ำหนักเบาพกพา", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "折叠躺椅": {
        "thai": ["เก้าอี้นอนพับ", "เก้าอี้สนามพับ", "เก้าอี้เอนหลัง"],
        "english": ["Folding Lounge Chair", "Reclining Camp Chair", "Beach Chair"],
        "category": "outdoor_camping",
        "materials": ["อลูมิเนียม", "ผ้า Oxford 600D", "โพลีเอสเตอร์", "ผ้า Canvas"],
        "scenes": ["แคมป์ปิ้ง", "ชายหาด", "ปิกนิก", "สวนหลังบ้าน", "สระว่ายน้ำ"],
        "longtail": ["นั่งสบายปรับเอนได้", "น้ำหนักเบาพกพา", "ทนทานแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "藤编家具": {
        "thai": ["เฟอร์นิเจอร์หวายเทียม", "เก้าอี้หวาย", "ชุดหวายสนาม"],
        "english": ["Rattan Furniture", "Wicker Furniture Set", "Outdoor Rattan Set"],
        "category": "home_furniture",
        "materials": ["หวายเทียม PE", "อลูมิเนียม", "สแตนเลส 304"],
        "scenes": ["ระเบียงคอนโด", "สวนหลังบ้าน", "รีสอร์ท", "ร้านกาแฟ", "สนามหญ้า"],
        "longtail": ["ดีไซน์สวยงาม", "ทนทานแดดฝน", "คุณภาพดีเยี่ยม", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "收纳架": {
        "thai": ["ชั้นวางของ", "ชั้นเก็บของ", "ชั้นวางอเนกประสงค์"],
        "english": ["Storage Shelf", "Organizer Rack", "Display Shelf"],
        "category": "storage_organization",
        "materials": ["สแตนเลส 304", "อลูมิเนียม", "ไม้สนแท้", "พลาสติก PP"],
        "scenes": ["ออฟฟิศ", "ห้องนอน", "ห้องครัว", "ห้องน้ำ", "ระเบียงคอนโด"],
        "longtail": ["จัดระเบียบดี", "ประหยัดพื้นที่", "ทนทานใช้งานนาน", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "户外桌椅套装": {
        "thai": ["ชุดโต๊ะเก้าอี้สนาม", "ชุดโต๊ะเก้าอี้แคมป์ปิ้ง", "ชุดเฟอร์นิเจอร์สนาม"],
        "english": ["Outdoor Furniture Set", "Camping Table Chair Set", "Picnic Set"],
        "category": "outdoor_camping",
        "materials": ["อลูมิเนียม", "ผ้า Oxford 600D", "ไม้ไผ่", "สแตนเลส 304"],
        "scenes": ["แคมป์ปิ้ง", "ปิกนิก", "สวนหลังบ้าน", "ระเบียงคอนโด", "รีสอร์ท"],
        "longtail": ["ครบเซ็ตคุ้มค่า", "น้ำหนักเบาพกพา", "ทนทานใช้งานกลางแจ้ง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    # ── 数码3C ──
    "智能手表": {
        "thai": ["สมาร์ทวอทช์", "นาฬิกาอัจฉริยะ", "Smart Watch"],
        "english": ["Smart Watch", "Smartwatch", "Fitness Tracker Watch"],
        "category": "electronics_3c",
        "materials": ["กันน้ำ IP68", "Bluetooth 5.3", "แบตอึด 5000mAh", "สายซิลิโคน", "กระจก Gorilla Glass"],
        "scenes": ["ออกกำลังกาย", "วิ่งมาราธอน", "ฟิตเนส", "ทำงาน Office", "ขับรถ"],
        "longtail": ["ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "ทนทานใช้งานนาน", "น้ำหนักเบาพกพา", "ของแท้ 100%"],
    },
    "蓝牙耳机": {
        "thai": ["หูฟังบลูทูธ", "หูฟังไร้สาย", "หูฟัง TWS"],
        "english": ["Bluetooth Earphone", "Wireless Earbuds", "TWS Earbuds"],
        "category": "electronics_3c",
        "materials": ["Bluetooth 5.3", "ANC ตัดเสียงรบกวน", "ไร้สาย TWS", "กันน้ำ IPX5", "แบตอึด 30 ชม."],
        "scenes": ["ฟังเพลง", "เล่นเกม", "ออกกำลังกาย", "เรียนออนไลน์", "ขับรถ"],
        "longtail": ["คุณภาพเสียงดีเยี่ยม", "ใส่สบายไม่เจ็บหู", "เสียงชัดใส", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "手机壳": {
        "thai": ["เคสมือถือ", "เคสโทรศัพท์", "กรอบมือถือ"],
        "english": ["Phone Case", "Mobile Phone Case", "Protective Case"],
        "category": "phone_accessories",
        "materials": ["TPU นิ่ม", "ซิลิโคน", "หนัง PU", "เคสกันกระแทก", "กระจก Tempered"],
        "scenes": ["ปกป้องมือถือ", "ของขวัญ", "แฟชั่น", "ทุกวัน"],
        "longtail": ["กันกระแทกดีเยี่ยม", "ลายสวยงาม", "พอดีเครื่อง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "充电宝": {
        "thai": ["พาวเวอร์แบงค์", "แบตสำรอง", "Power Bank"],
        "english": ["Power Bank", "Portable Charger", "External Battery"],
        "category": "electronics_3c",
        "materials": ["แบตอึด 20000mAh", "PD 65W Fast Charge", "USB-C", "ลิเธียมโพลิเมอร์"],
        "scenes": ["เดินทาง", "ท่องเที่ยว", "ทำงาน", "ออกกำลังกาย", "แคมป์ปิ้ง"],
        "longtail": ["ชาร์จเร็วทันใจ", "แบตอึดทนนาน", "น้ำหนักเบาพกพา", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "蓝牙音箱": {
        "thai": ["ลำโพงบลูทูธ", "ลำโพงพกพา", "Speaker ไร้สาย"],
        "english": ["Bluetooth Speaker", "Portable Speaker", "Wireless Speaker"],
        "category": "electronics_3c",
        "materials": ["กันน้ำ IPX7", "Bluetooth 5.3", "แบตอึด 12 ชม.", "ไดรเวอร์ 40mm"],
        "scenes": ["ฟังเพลง", "ปาร์ตี้", "แคมป์ปิ้ง", "ชายหาด", "ห้องนอน"],
        "longtail": ["เสียงเบสหนักแน่น", "น้ำหนักเบาพกพา", "กันน้ำกันฝุ่น", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    "机械键盘": {
        "thai": ["คีย์บอร์ดเกมมิ่ง", "Mechanical Keyboard", "คีย์บอร์ด机械"],
        "english": ["Mechanical Keyboard", "Gaming Keyboard", "RGB Keyboard"],
        "category": "gaming_esports",
        "materials": ["RGB 16 ล้านสี", "Switch Blue/Red/Brown", "PBT Keycap", "USB-C", "อลูมิเนียม"],
        "scenes": ["เล่นเกม", "ทำงาน Office", "พิมพ์งาน"],
        "longtail": ["เสียงคลิกเพราะมาก", "ทนทานกดได้ 50 ล้านครั้ง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "RGB สวยมาก"],
    },
    "数据线": {
        "thai": ["สายชาร์จ", "สาย USB-C", "สายชาร์จเร็ว"],
        "english": ["Charging Cable", "USB-C Cable", "Fast Charging Cable"],
        "category": "phone_accessories",
        "materials": ["PD 65W Fast Charge", "USB-C", "ไนลอนถัก", "อลูมิเนียม"],
        "scenes": ["ชาร์จมือถือ", "ชาร์จโน๊ตบุ๊ค", "เดินทาง", "ทำงาน"],
        "longtail": ["ชาร์จเร็วทันใจ", "ทนทานใช้งานนาน", "สายแข็งแรง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า"],
    },
    # ── 美妆个护 ──
    "防晒霜": {
        "thai": ["กันแดด", "ครีมกันแดด", "Sunscreen"],
        "english": ["Sunscreen", "Sunblock Cream", "SPF50 Sunscreen"],
        "category": "beauty_care",
        "materials": ["SPF50+ PA++++", "SPF30 PA+++", "วิตามินซี", "Aloe Vera", "Niacinamide"],
        "scenes": ["กันแดดทุกวัน", "ออกกำลังกาย", "ท่องเที่ยว", "ชายหาด", "แต่งหน้าทำงาน"],
        "longtail": ["ผิวขาวใส", "กันแดดดีเยี่ยม", "ไม่เหนียวเหนอะหนะ", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ผิวแพ้ง่ายใช้ได้"],
    },
    "面霜": {
        "thai": ["ครีมบำรุงผิว", "มอยส์เจอไรเซอร์", "ครีมทาหน้า"],
        "english": ["Face Cream", "Moisturizer", "Face Moisturizer Cream"],
        "category": "beauty_care",
        "materials": ["คอลลาเจน", "วิตามินซี", "เซราไมด์", "กรดไฮยาลูรอนิก", "Retinol", "Niacinamide"],
        "scenes": ["ผิวขาวใส", "ลดรอยสิว", "บำรุงผิวทุกวัน", "สาวออฟฟิศ"],
        "longtail": ["ผิวชุ่มชื่น", "ลดริ้วรอย", "คุณภาพดีมาก", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ผิวแพ้ง่ายใช้ได้"],
    },
    "口红": {
        "thai": ["ลิปสติก", "ลิปสี", "ลิปแมท"],
        "english": ["Lipstick", "Matte Lipstick", "Long Lasting Lipstick"],
        "category": "beauty_care",
        "materials": ["Vitamin E", "Moisturizing", "Long-lasting", "Non-drying"],
        "scenes": ["แต่งหน้าทำงาน", "ออกงานกลางคืน", "ลุค Everyday", "วัยรุ่น"],
        "longtail": ["สีสวยติดทนนาน", "ไม่แห้งปาก", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ยอดนิยม 2026"],
    },
    "香水": {
        "thai": ["น้ำหอม", "น้ำหอมผู้หญิง", "น้ำหอมผู้ชาย"],
        "english": ["Perfume", "Fragrance", "Eau de Parfum"],
        "category": "beauty_care",
        "materials": ["Alcohol-free", "Essential Oil", "Natural Extract"],
        "scenes": ["ออกงานกลางคืน", "ทำงาน", "ออกเดท", "ทุกวัน"],
        "longtail": ["กลิ่นหอมติดทนนาน", "ขายดีที่สุด", "ราคาถูกสุดคุ้ม", "ของแท้แบรนด์ดัง", "ยอดนิยม 2026"],
    },
    # ── 母婴 ──
    "婴儿推车": {
        "thai": ["รถเข็นเด็ก", "รถเข็นทารก", "Stroller"],
        "english": ["Baby Stroller", "Infant Stroller", "Foldable Baby Stroller"],
        "category": "mother_baby",
        "materials": ["อลูมิเนียม", "ผ้า Organic Cotton", "ผ้าฝ้าย 100%", "ABS ปลอดสารพิษ"],
        "scenes": ["เด็กแรกเกิด", "ทารก 0-6 เดือน", "วัยหัดเดิน", "คุณแม่มือใหม่"],
        "longtail": ["ปลอดภัยสำหรับเด็ก", "พับเก็บง่าย", "น้ำหนักเบา", "ขายดีอันดับ 1", "ราคาถูกปลอดภัย", "คุณแม่แนะนำ"],
    },
    "纸尿裤": {
        "thai": ["ผ้าอ้อมสำเร็จรูป", "แพมเพิส", "Diaper"],
        "english": ["Baby Diaper", "Nappy", "Baby Nappy"],
        "category": "mother_baby",
        "materials": ["ผ้า Organic Cotton", "BPA-free Food Grade", "Non-toxic", "Super Absorbent"],
        "scenes": ["เด็กแรกเกิด", "ทารก 0-6 เดือน", "วัยหัดเดิน", "นอนหลับ"],
        "longtail": ["ซึมซับดีเยี่ยม", "ไม่ระคายเคือง", "ปลอดภัยสำหรับเด็ก", "ขายดีอันดับ 1", "ราคาถูกปลอดภัย"],
    },
    "奶瓶": {
        "thai": ["ขวดนมเด็ก", "ขวดนมทารก", "Baby Bottle"],
        "english": ["Baby Bottle", "Feeding Bottle", "Anti-Colic Baby Bottle"],
        "category": "mother_baby",
        "materials": ["BPA-free Food Grade", "PP Food Grade", "Silicone ทางการแพทย์", "ผ้ามัสลิน"],
        "scenes": ["เด็กแรกเกิด", "ให้นมลูก", "ทารก 0-6 เดือน", "คุณแม่มือใหม่"],
        "longtail": ["ปลอดภัยสำหรับเด็ก", "ทำความสะอาดง่าย", "ทนทานใช้งานนาน", "ขายดีอันดับ 1", "คุณแม่แนะนำ"],
    },
    "爬行垫": {
        "thai": ["เบาะรองคลาน", "เสื่อรองคลาน", "Play Mat"],
        "english": ["Baby Play Mat", "Crawling Mat", "Foam Play Mat"],
        "category": "mother_baby",
        "materials": ["EVA ปลอดสารพิษ", "XPE Foam", "Non-toxic", "กันน้ำ"],
        "scenes": ["เด็กแรกเกิด", "วัยหัดเดิน", "เล่นสนุก", "คุณแม่มือใหม่"],
        "longtail": ["ปลอดภัยสำหรับเด็ก", "กันกระแทกดี", "ทำความสะอาดง่าย", "ขายดีอันดับ 1", "คุณแม่แนะนำ"],
    },
    # ── 食品 ──
    "零食": {
        "thai": ["ขนมขบเคี้ยว", "ขนมทานเล่น", "Snack"],
        "english": ["Snack", "Chips", "Healthy Snack"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "น้ำตาล 0%", "Non-GMO", "HACCP รับรอง"],
        "scenes": ["ลดน้ำหนัก", "ดูแลสุขภาพ", "เด็กนักเรียน", "สาวออฟฟิศ", "ทุกเพศทุกวัย"],
        "longtail": ["อร่อยถูกใจ", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
    "咖啡": {
        "thai": ["กาแฟสำเร็จรูป", "กาแฟสด", "กาแฟคั่ว"],
        "english": ["Instant Coffee", "Ground Coffee", "Coffee Beans"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "น้ำตาล 0%", "Non-GMO", "โปรตีนสูง"],
        "scenes": ["ดูแลสุขภาพ", "ทำงาน Office", "สาวออฟฟิศ", "ทุกเพศทุกวัย"],
        "longtail": ["หอมอร่อยเข้มข้น", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
    "茶叶": {
        "thai": ["ชาไทย", "ชาเขียว", "ชาสมุนไพร"],
        "english": ["Thai Tea", "Green Tea", "Herbal Tea"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "สารสกัดจากธรรมชาติ", "Non-GMO"],
        "scenes": ["ดูแลสุขภาพ", "ลดน้ำหนัก", "ผู้สูงอายุ", "ทุกเพศทุกวัย"],
        "longtail": ["หอมอร่อย", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
    "蜂蜜": {
        "thai": ["น้ำผึ้งแท้", "น้ำผึ้งป่า", "น้ำผึ้งดอกไม้"],
        "english": ["Pure Honey", "Organic Honey", "Natural Honey"],
        "category": "food_beverage",
        "materials": ["ออร์แกนิค 100%", "สารสกัดจากธรรมชาติ", "Non-GMO", "HACCP รับรอง"],
        "scenes": ["ดูแลสุขภาพ", "บำรุงสมอง", "เสริมภูมิคุ้มกัน", "ทุกเพศทุกวัย"],
        "longtail": ["หวานหอมจากธรรมชาติ", "ปลอดภัย อย. รับรอง", "ขายดีอันดับ 1", "ราคาถูกคุ้มค่า", "คุณภาพระดับพรีเมียม"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════════

def _sample(pool: list, max_items: int) -> list:
    if len(pool) <= max_items:
        return pool
    return random.sample(pool, max_items)


def _get_cat_field(cat_data: dict, new_key: str, old_key: str) -> list:
    """兼容新旧词库格式取字段"""
    return cat_data.get(new_key) or cat_data.get(old_key) or []


def _get_platform_base(cat_data: dict, product_data: dict | None,
                       platform: str) -> list:
    """获取平台对应的产品基础词列表"""
    # 1. 优先产品映射
    if product_data:
        if platform in ("shopee", "lazada", "tiktok"):
            thai = product_data.get("thai", [])
            if thai:
                return thai
        elif platform in ("temu", "amazon"):
            eng = product_data.get("english", [])
            if eng:
                return eng

    # 2. 类目 base（新格式：dict 按平台分）
    bases = cat_data.get("base", [])
    if isinstance(bases, dict):
        return bases.get(platform, bases.get("shopee", []))
    # 旧格式：flat list
    return bases


def _ai_score(title: str) -> int:
    score = 50
    if 30 <= len(title) <= 80:
        score += 15
    elif len(title) > 100:
        score -= 10
    if any(c.isdigit() for c in title):
        score += 10
    promo = ("ขายดี", "ราคาถูก", "ลดราคา", "พร้อมส่ง", "100%", "热销", "特价",
             "Best Seller", "Hot Deal", "Free Shipping")
    if any(w in title for w in promo):
        score += 8
    if any(kw in title for kw in ("IP68", "Bluetooth", "SPF", "4K", "USB", "PD")):
        score += 7
    return min(100, max(0, score))


# ═══════════════════════════════════════════════════════════════════════════════
# 产品匹配
# ═══════════════════════════════════════════════════════════════════════════════

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
    bases_raw = cat_data.get("base", [])
    if isinstance(bases_raw, dict):
        bases_list = bases_raw.get("shopee", [])
    else:
        bases_list = bases_raw
    for i, sub in enumerate(subs):
        if sub in product_cn or product_cn in sub:
            if i < len(bases_list):
                return {
                    "thai": [bases_list[i]],
                    "english": [],
                    "category": "",
                    "materials": _get_cat_field(cat_data, "material_specs", "materials"),
                    "scenes": _get_cat_field(cat_data, "scene_keywords", "scene_audience"),
                    "longtail": _get_cat_field(cat_data, "longtail_keywords", "longtail"),
                }

    return None


def _get_generic_product(product_cn: str, cat_data: dict) -> dict:
    """无匹配时的通用方案：用类目词库但标记为通用"""
    return {
        "thai": [product_cn],
        "english": [],
        "category": "",
        "materials": _get_cat_field(cat_data, "material_specs", "materials"),
        "scenes": _get_cat_field(cat_data, "scene_keywords", "scene_audience"),
        "longtail": _get_cat_field(cat_data, "longtail_keywords", "longtail"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Shopee 风格 — 泰语，关键词丰富，搜索优化
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_shopee(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    prod = _match_product(product_cn, cat_data) or _get_generic_product(product_cn, cat_data)
    bases = _get_platform_base(cat_data, prod, "shopee")
    mats = prod.get("materials", [])
    scenes = prod.get("scenes", [])
    lts = prod.get("longtail", [])
    hot = cat_data.get("shopee_hot", [])
    # 合并长尾词
    for lt in _get_cat_field(cat_data, "longtail_keywords", "longtail"):
        if lt not in lts:
            lts.append(lt)

    if not bases:
        return []

    titles_set: set[str] = set()
    sample_limit = max(3, int((MAX_SAMPLE_COMBOS / max(len(bases), 1)) ** 0.66))
    s_mats = _sample(mats, sample_limit) if mats else []
    s_scenes = _sample(scenes, sample_limit) if scenes else []
    iters = 0

    # P1: base + material + scene + hot
    if s_mats and s_scenes and hot:
        for b, m, s, h in itertools.product(bases, s_mats, s_scenes, hot):
            t = f"{b} {m} {s} {h}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # P2: base + material + scene + longtail
    if len(titles_set) < count and s_mats and s_scenes:
        for b, m, s, l in itertools.product(bases, s_mats, s_scenes, lts):
            t = f"{b} {m} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # P3: base + material + longtail
    if len(titles_set) < count and s_mats:
        for b, m, l in itertools.product(bases, s_mats, lts):
            t = f"{b} {m} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # P4: base + scene + longtail
    if len(titles_set) < count and s_scenes:
        for b, s, l in itertools.product(bases, s_scenes, lts):
            t = f"{b} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # P5: base + longtail
    if len(titles_set) < count:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Lazada 风格 — 泰语，LazMall / 官方店铺风格
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_lazada(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    prod = _match_product(product_cn, cat_data) or _get_generic_product(product_cn, cat_data)
    bases = _get_platform_base(cat_data, prod, "lazada")
    mats = prod.get("materials", [])
    scenes = prod.get("scenes", [])
    lts = prod.get("longtail", [])
    hot = cat_data.get("lazada_hot", [])
    for lt in _get_cat_field(cat_data, "longtail_keywords", "longtail"):
        if lt not in lts:
            lts.append(lt)

    if not bases:
        return []

    titles_set: set[str] = set()
    sample_limit = max(3, int((MAX_SAMPLE_COMBOS / max(len(bases), 1)) ** 0.66))
    s_mats = _sample(mats, sample_limit) if mats else []
    s_scenes = _sample(scenes, sample_limit) if scenes else []
    iters = 0

    # Lazada: base + LazMall hot + material + scene
    if s_mats and s_scenes and hot:
        for b, h, m, s in itertools.product(bases, hot, s_mats, s_scenes):
            t = f"{b} {h} {m} {s}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and s_mats and hot:
        for b, h, m in itertools.product(bases, hot, s_mats):
            t = f"{b} {h} {m}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and s_mats:
        for b, m, l in itertools.product(bases, s_mats, lts):
            t = f"{b} {m} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count:
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


# ═══════════════════════════════════════════════════════════════════════════════
# TikTok 风格 — 短标题，病毒式传播，带趋势词
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_tiktok(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    prod = _match_product(product_cn, cat_data) or _get_generic_product(product_cn, cat_data)
    bases = _get_platform_base(cat_data, prod, "tiktok")
    hot = cat_data.get("tiktok_hot", [])
    lts = prod.get("longtail", [])

    if not bases:
        return []

    # TikTok 优先短标题（≤max_chars，尽量 40 字以内）
    effective_max = min(max_chars, 60)
    titles_set: set[str] = set()
    iters = 0

    # P1: base + hot（最短最 viral）
    if hot:
        for b, h in itertools.product(bases, hot):
            t = f"{b} {h}"
            if len(t) <= effective_max:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # P2: base + hot + longtail
    if len(titles_set) < count and hot and lts:
        for b, h, l in itertools.product(bases, hot, lts):
            t = f"{b} {h} {l}"
            if len(t) <= effective_max:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    # P3: base + longtail
    if len(titles_set) < count and lts:
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


# ═══════════════════════════════════════════════════════════════════════════════
# TEMU 风格 — 英语，长标题，关键词堆叠
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_temu(product_cn: str, cat_data: dict, max_chars: int,
              count: int) -> list[dict]:
    prod = _match_product(product_cn, cat_data) or _get_generic_product(product_cn, cat_data)
    bases = _get_platform_base(cat_data, prod, "temu")
    hot = cat_data.get("temu_hot", [])
    scenes = _get_cat_field(cat_data, "scene_keywords", "scene_audience")
    mats = prod.get("materials", [])
    lts = prod.get("longtail", [])

    if not bases:
        return []

    titles_set: set[str] = set()
    s_mats = _sample(mats, 4) if mats else []
    s_scenes = _sample(scenes, 4) if scenes else []
    iters = 0

    # TEMU: base + hot + material + scene（长堆叠）
    if hot and s_mats and s_scenes:
        for b, h, m, s in itertools.product(bases, hot, s_mats, s_scenes):
            t = f"{b} {h} {m} {s}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and hot and s_mats:
        for b, h, m in itertools.product(bases, hot, s_mats):
            t = f"{b} {h} {m}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and hot:
        for b, h, l in itertools.product(bases, hot, lts):
            t = f"{b} {h} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    result = list(titles_set)
    random.shuffle(result)
    return [{"title": t, "chars": len(t), "score": _ai_score(t)} for t in result[:count]]


# ═══════════════════════════════════════════════════════════════════════════════
# Amazon 风格 — 英语，专业关键词丰富
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_amazon(product_cn: str, cat_data: dict, max_chars: int,
                count: int) -> list[dict]:
    prod = _match_product(product_cn, cat_data) or _get_generic_product(product_cn, cat_data)
    bases = _get_platform_base(cat_data, prod, "amazon")
    mats = prod.get("materials", [])
    scenes = _get_cat_field(cat_data, "scene_keywords", "scene_audience")
    lts = prod.get("longtail", [])

    if not bases:
        return []

    titles_set: set[str] = set()
    s_mats = _sample(mats, 4) if mats else []
    s_scenes = _sample(scenes, 4) if scenes else []
    iters = 0

    # Amazon: base + material + scene
    if s_mats and s_scenes:
        for b, m, s in itertools.product(bases, s_mats, s_scenes):
            t = f"{b} {m} {s}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and s_mats and lts:
        for b, m, l in itertools.product(bases, s_mats, lts):
            t = f"{b} {m} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count:
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


# ═══════════════════════════════════════════════════════════════════════════════
# 中文平台风格 — 淘宝/拼多多/抖音
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_cn_platform(cat_data: dict, product_cn: str, max_chars: int,
                     count: int) -> list[dict]:
    # 中文平台：使用中文品质词 + 中文特性词（不用泰语材质）
    templates = [
        lambda q, f: f"{product_cn} {q} {f}",
        lambda q, f: f"{q}{product_cn} {f}",
        lambda q, f: f"{product_cn}{f} {q}",
        lambda q, f: f"{product_cn} {f}",
        lambda q, f: f"{q}{product_cn}",
    ]

    titles_set: set[str] = set()
    iters = 0

    for tpl in templates:
        for q, f in itertools.product(CN_QUALITIES, CN_FEATURES):
            t = tpl(q, f)
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


# ═══════════════════════════════════════════════════════════════════════════════
# 旧版通用泰语生成（兼容旧词库 5 类目格式）
# ═══════════════════════════════════════════════════════════════════════════════

def generate_thai_titles(product_cn: str, cat_data: dict, max_chars: int,
                          count: int = TARGET_TITLE_COUNT) -> list[dict]:
    """根据输入产品名生成精准泰语标题（旧版兼容）"""
    prod = _match_product(product_cn, cat_data)
    if not prod:
        prod = _get_generic_product(product_cn, cat_data)

    bases = prod.get("thai", [])
    mats = prod.get("materials", [])
    scenes = prod.get("scenes", [])
    lts = prod.get("longtail", [])

    if not bases:
        return []

    # 补充类目通用长尾词
    cat_lts = _get_cat_field(cat_data, "longtail_keywords", "longtail")
    for lt in cat_lts:
        if lt not in lts:
            lts.append(lt)

    titles_set: set[str] = set()
    sample_limit = max(3, int((MAX_SAMPLE_COMBOS / max(len(bases), 1)) ** 0.66))
    s_mats = _sample(mats, sample_limit) if mats else []
    s_scenes = _sample(scenes, sample_limit) if scenes else []
    iters = 0

    if s_mats and s_scenes:
        for b, m, s, l in itertools.product(bases, s_mats, s_scenes, lts):
            t = f"{b} {m} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and iters < MAX_ITERATIONS and s_mats:
        for b, m, l in itertools.product(bases, s_mats, lts):
            t = f"{b} {m} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

    if len(titles_set) < count and iters < MAX_ITERATIONS and s_scenes:
        for b, s, l in itertools.product(bases, s_scenes, lts):
            t = f"{b} {s} {l}"
            if len(t) <= max_chars:
                titles_set.add(t)
            iters += 1
            if len(titles_set) >= count * 3 or iters >= MAX_ITERATIONS:
                break

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
    """根据输入产品名生成中文标题（旧版兼容）"""
    return _gen_cn_platform(cat_data, product_cn, max_chars, count)


# ═══════════════════════════════════════════════════════════════════════════════
# 统一调度入口
# ═══════════════════════════════════════════════════════════════════════════════

def dispatch(product_cn: str, plat_key: str, cat_data: dict,
             max_chars: int) -> list[dict]:
    """根据平台分发到对应的标题生成器"""
    count = TARGET_TITLE_COUNT

    # ── 平台专属生成器 ──
    if plat_key == "shopee_th":
        return _gen_shopee(product_cn, cat_data, max_chars, count)
    if plat_key == "lazada_th":
        return _gen_lazada(product_cn, cat_data, max_chars, count)
    if plat_key == "tiktok_global":
        return _gen_tiktok(product_cn, cat_data, max_chars, count)
    if plat_key == "temu":
        return _gen_temu(product_cn, cat_data, max_chars, count)
    if plat_key == "amazon":
        return _gen_amazon(product_cn, cat_data, max_chars, count)

    # ── 中文平台 ──
    if plat_key in ("taobao", "pinduoduo", "douyin"):
        return _gen_cn_platform(cat_data, product_cn, max_chars, count)

    # ── 兜底：旧版泰语生成 ──
    return generate_thai_titles(product_cn, cat_data, max_chars, count)
