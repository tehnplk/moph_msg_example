# moph_msg_example

ตัวอย่างส่งข้อความเข้าไลน์หมอพร้อม (MOPH) ด้วย Python — ใช้ stdlib ล้วน ไม่ต้อง `pip install`

มี 2 แบบ ใช้คนละ API และคนละคู่ key:

| | `moph_msg.py` — MESSAGE | `moph_notify.py` — NOTIFY |
|---|---|---|
| ส่งถึง | **รายบุคคล** ระบุด้วยเลขบัตรประชาชน 13 หลัก | **ไลน์กลุ่ม** ที่ผูกกับ key คู่นั้น |
| API | MOPH Alert v3.1 | MOPH Notify |
| Endpoint | `POST https://morpromt2c.moph.go.th/alert/v3.1/messages` | `POST https://morpromt2f.moph.go.th/api/notify/send` |
| Key ใน `.env` | `MOPH_MESSAGE_CLIENT_KEY`, `MOPH_MESSAGE_SECRET_KEY` | `MOPH_NOTIFY_CLIENT_KEY`, `MOPH_NOTIFY_SECRET_KEY` |
| ถือว่าส่งสำเร็จเมื่อ | HTTP 2xx **และ** `message_code` = 200 ใน response | HTTP 2xx |

อยากส่งหาใครคนหนึ่ง → MESSAGE · อยากประกาศเข้ากลุ่มทีม → NOTIFY
(ต้องการส่งกลุ่มหลายกลุ่ม = ต้องมี key หลายคู่ กลุ่มละคู่)

## ติดตั้ง

ต้องมี Python 3.8+ เท่านั้น

```bash
git clone https://github.com/tehnplk/moph_msg_example.git
cd moph_msg_example
cp .env.example .env      # แล้วใส่ key จริงลงใน .env
```

`.env` อยู่ใน `.gitignore` แล้ว — **ห้าม commit key**

ยังไม่มี key: ดูเอกสารขอใช้งานระบบเพื่อขอ KEY ที่ [Google Drive](https://drive.google.com/drive/folders/16xx_uBwA1kLmWNwX3aBhvrScwLZdOWkI)

## ใช้งานจาก command line

```bash
# MESSAGE — ส่งรายบุคคล (หลายคนคั่นด้วย , ไม่เว้นวรรค)
python moph_msg.py 1234567890123 "ข้อความ"
python moph_msg.py 1234567890123,1111111111111 "ข้อความ" --flex

# NOTIFY — ส่งเข้าไลน์กลุ่ม
python moph_notify.py "ข้อความ"
python moph_notify.py "ข้อความ" --flex
```

- `--flex` ส่งเป็นการ์ด (Flex Message) มีปุ่มลิงก์ · ไม่ใส่ = ข้อความธรรมดา
- `--dry` พิมพ์ payload ออกมาดูเฉย ๆ ไม่ยิงจริง — ลองอันนี้ก่อนเสมอ
- Windows แล้วภาษาไทยในหน้าจอเพี้ยน: ตั้ง `PYTHONUTF8=1` ก่อนรัน (ข้อมูลที่ส่งไม่เพี้ยน เพี้ยนแค่ตอนแสดงผล)

ผลการส่งดูจาก exit code: `0` = สำเร็จ, `1` = ไม่สำเร็จ (พิมพ์ response ของ API ให้ดู)

## เรียกใช้จากโค้ดตัวเอง

```python
from moph_msg import load_env, payload, send as send_message
from moph_notify import text_message, button_flex_message, send as send_notify

load_env()   # อ่าน .env เข้า os.environ — หรือตั้ง env เองก็ได้

# MESSAGE — รายบุคคล
ok, res = send_message(payload(["1234567890123"], "หัวเรื่อง", "เนื้อความ", use_flex=True))

# NOTIFY — ไลน์กลุ่ม (ส่งได้หลายข้อความในครั้งเดียว)
ok, res = send_notify([
    text_message("สวัสดี"),
    button_flex_message("ข้อความสั้นบนแจ้งเตือน", "เนื้อความ", "รายละเอียด", "https://example.com"),
])
```

ทั้งสองแบบ `send()` คืน `(ok: bool, response: str)` และ **ไม่ raise** — timeout / ต่อไม่ได้ / HTTP error จะได้ `ok=False` พร้อมข้อความ error
ตั้งใจให้เป็นแบบนี้: แจ้งเตือนส่งไม่ผ่านต้องไม่ทำให้งานหลัก (เช่น บันทึกข้อมูล) พังตาม — ผู้เรียกเช็ก `ok` แล้ว log เอง

## รูปแบบ payload

**MESSAGE** (`moph_msg.payload()`)

```json
{
  "cid": ["1234567890123"],
  "messages": [{ "type": "text", "text": "หัวเรื่อง\nเนื้อความ" }],
  "message_title": "หัวเรื่อง",
  "message_html": "<strong>หัวเรื่อง</strong><br>เนื้อความ",
  "message_text": "หัวเรื่อง\nเนื้อความ",
  "message_type": "HPT"
}
```

`messages` คือสิ่งที่ขึ้นในไลน์ (text หรือ flex) · `message_title/html/text` เป็นข้อความสำรองให้ช่องทางอื่นของหมอพร้อม

**NOTIFY** (`moph_notify.send()`)

```json
{ "messages": [{ "type": "text", "text": "ข้อความ" }] }
```

ไม่มี `cid` — ผู้รับคือกลุ่มที่ผูกกับ key

Header ทั้งสองแบบเหมือนกัน:

```
Content-Type: application/json
client-key: <client key>
secret-key: <secret key>
```

`messages` ใช้รูปแบบเดียวกับ LINE Messaging API — ออกแบบการ์ดได้ที่ [LINE Flex Message Simulator](https://developers.line.biz/flex-simulator/) แล้วเอา JSON มาใส่ใน `contents`

## ข้อควรรู้

- **ผู้รับ MESSAGE ต้องผูกบัญชีหมอพร้อมแล้ว** ไม่งั้นส่งไม่ถึง
- **PDPA**: เลขบัตรเป็นข้อมูลส่วนบุคคล อย่า print/log เลขบัตรผู้รับ (สคริปต์นี้บอกแค่จำนวนผู้รับ) · ข้อความในไลน์อยู่นอกระบบ อย่าใส่ข้อมูลผู้ป่วยเต็ม ๆ เช่น ชื่อ-สกุลเต็ม เลขบัตร บ้านเลขที่
- **ปุ่มลิงก์ใน flex**: ต่อท้าย URL ด้วย `openExternalBrowser=1` ให้ไลน์เปิดในเบราว์เซอร์ของเครื่อง — จำเป็นถ้าหน้าปลายทางต้อง login ด้วย SSO/ThaiD ซึ่งใช้ในเบราว์เซอร์ของไลน์ไม่ได้
- `altText` ของ flex คือข้อความที่ขึ้นบนแจ้งเตือนมือถือ ยาวได้ไม่เกิน 400 ตัวอักษร
