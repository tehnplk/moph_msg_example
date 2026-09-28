#!/usr/bin/env python3
"""
ตัวอย่างส่งข้อความเข้าไลน์กลุ่มผ่าน MOPH Notify (stdlib ล้วน ไม่ต้อง pip)
ไม่ระบุผู้รับ — เข้ากลุ่มที่ผูกกับ client-key/secret-key คู่นั้น (ส่งรายบุคคลด้วยเลขบัตรใช้ moph_msg.py)

  1. ใส่ MOPH_NOTIFY_CLIENT_KEY, MOPH_NOTIFY_SECRET_KEY ใน .env
  2. python moph_notify.py "ข้อความ"            ส่ง text
     python moph_notify.py "ข้อความ" --flex     ส่ง flex มีปุ่มลิงก์
     เติม --dry = พิมพ์ payload ไม่ยิงจริง
"""
import json
import os
import sys
import urllib.error
import urllib.request

from moph_msg import load_env

URL = "https://morpromt2f.moph.go.th/api/notify/send"


def text_message(text):
    return {"type": "text", "text": text}


def button_flex_message(alt_text, body_text, button_label, button_url):
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box", "layout": "vertical",
                "contents": [{"type": "text", "text": body_text, "wrap": True, "size": "md"}],
            },
            "footer": {
                "type": "box", "layout": "vertical", "spacing": "sm",
                "contents": [{"type": "button", "style": "primary",
                              "action": {"type": "uri", "label": button_label, "uri": button_url}}],
            },
        },
    }


def send(messages):
    """คืน (ok, response) ไม่ raise · ok = HTTP 2xx"""
    req = urllib.request.Request(URL, method="POST", data=json.dumps({"messages": messages}).encode(), headers={
        "Content-Type": "application/json",
        "client-key": os.environ["MOPH_NOTIFY_CLIENT_KEY"],
        "secret-key": os.environ["MOPH_NOTIFY_SECRET_KEY"],
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, r.read().decode()
    except urllib.error.HTTPError as e:
        return False, e.read().decode() or f"HTTP {e.code}"
    except OSError as e:   # timeout / ต่อไม่ได้
        return False, str(e)


def main():
    load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    text = args[0] if args else "ข้อความทดสอบจาก MOPH Notify"
    messages = [button_flex_message(text, text, "รายละเอียด", "https://example.com")
                if "--flex" in sys.argv else text_message(text)]
    if "--dry" in sys.argv:
        print(json.dumps({"messages": messages}, ensure_ascii=False, indent=2))
        return
    if not os.environ.get("MOPH_NOTIFY_CLIENT_KEY") or not os.environ.get("MOPH_NOTIFY_SECRET_KEY"):
        sys.exit("ตั้ง MOPH_NOTIFY_CLIENT_KEY / MOPH_NOTIFY_SECRET_KEY ใน .env")
    ok, res = send(messages)
    print(("ส่งสำเร็จ" if ok else "ส่งไม่สำเร็จ") + f"\n{res[:500]}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
