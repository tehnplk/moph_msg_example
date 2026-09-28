#!/usr/bin/env python3
"""
ตัวอย่างส่งข้อความเข้าไลน์หมอพร้อมผ่าน MOPH Alert v3.1 (stdlib ล้วน ไม่ต้อง pip)

  1. คัดลอก .env.example เป็น .env แล้วใส่ CLIENT_KEY, SECRET_KEY
  2. python moph_msg.py <เลขบัตร[,เลขบัตร]> "ข้อความ"            ส่ง text
     python moph_msg.py <เลขบัตร[,เลขบัตร]> "ข้อความ" --flex     ส่ง flex card
     เติม --dry = พิมพ์ payload ไม่ยิงจริง

ผู้รับต้องผูกบัญชีหมอพร้อมแล้ว · เลขบัตรเป็นข้อมูลส่วนบุคคล (PDPA) อย่า log
"""
import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

URL = "https://morpromt2c.moph.go.th/alert/v3.1/messages"


def load_env(path=Path(__file__).with_name(".env")):
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.partition("=")
            if sep and not k.strip().startswith("#"):
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def flex(title, text):
    row = lambda label, value: {
        "type": "box", "layout": "baseline", "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 2},
            {"type": "text", "text": value, "size": "sm", "color": "#333333", "flex": 5, "wrap": True},
        ],
    }
    return {
        "type": "bubble",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": "#0F766E", "paddingAll": "md",
            "contents": [{"type": "text", "text": title, "color": "#FFFFFF", "size": "lg", "weight": "bold", "wrap": True}],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                row("ข้อความ", text),
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": datetime.now().strftime("%d/%m/%Y %H:%M"), "size": "xs", "color": "#999999", "align": "end", "margin": "md"},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "button", "style": "primary", "color": "#0F766E", "height": "sm",
                          # openExternalBrowser=1 ให้ไลน์เปิดลิงก์ในเบราว์เซอร์ของเครื่อง
                          "action": {"type": "uri", "label": "เปิดเว็บ", "uri": "https://moph.go.th/?openExternalBrowser=1"}}],
        },
    }


def payload(cids, title, text, use_flex=False):
    msg = ({"type": "flex", "altText": f"{title} — {text}"[:400], "contents": flex(title, text)}
           if use_flex else {"type": "text", "text": f"{title}\n{text}"})
    return {
        "cid": cids,
        "messages": [msg],
        "message_title": title,
        "message_html": f"<strong>{html.escape(title)}</strong><br>{html.escape(text).replace(chr(10), '<br>')}",
        "message_text": f"{title}\n{text}",
        "message_type": "HPT",
    }


def send(body):
    """คืน (ok, response ทั้งก้อน) ไม่ raise — ส่งไม่ผ่านต้องไม่ทำให้งานหลักพัง"""
    req = urllib.request.Request(URL, method="POST", data=json.dumps(body).encode(), headers={
        "content-type": "application/json",
        "client-key": os.environ["CLIENT_KEY"],
        "secret-key": os.environ["SECRET_KEY"],
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = r.read().decode()
    except urllib.error.HTTPError as e:
        return False, e.read().decode() or f"HTTP {e.code}"
    except OSError as e:   # timeout / ต่อไม่ได้
        return False, str(e)
    # สำเร็จ = HTTP 2xx และ message_code 200 ในเนื้อ response (HTTP 200 อย่างเดียวไม่พอ)
    try:
        return json.loads(res).get("message_code") == 200, res
    except ValueError:
        return False, res


def main():
    load_env()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit('ใช้: python moph_msg.py <เลขบัตร[,เลขบัตร]> "ข้อความ" [--flex] [--dry]')
    cids = [c.strip() for c in args[0].split(",") if c.strip()]
    text = args[1] if len(args) > 1 else "ข้อความทดสอบจาก MOPH Alert"
    if not cids or any(not (c.isdigit() and len(c) == 13) for c in cids):
        sys.exit("เลขบัตรต้องเป็นตัวเลข 13 หลัก หลายคนคั่นด้วย ,")

    body = payload(cids, "แจ้งเตือนทดสอบ", text, "--flex" in sys.argv)
    if "--dry" in sys.argv:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return
    if not os.environ.get("CLIENT_KEY") or not os.environ.get("SECRET_KEY"):
        sys.exit("ตั้ง CLIENT_KEY / SECRET_KEY ใน .env")
    ok, res = send(body)
    print(("ส่งสำเร็จ" if ok else "ส่งไม่สำเร็จ") + f" ({len(cids)} ผู้รับ)\n{res[:500]}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
