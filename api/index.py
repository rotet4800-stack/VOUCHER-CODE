from http.server import BaseHTTPRequestHandler
import requests
import json
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # အဖြေကို 200 OK အနေဖြင့် အမြဲပေးမည် (Error ဖမ်းရလွယ်အောင်)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # အဆင့် (၁) - Token တောင်းယူခြင်း
        token_url = "https://cloud-as.ruijienetworks.com/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
        token_payload = json.dumps({
            "appid": "openc3be644fb5dc",
            "secret": "0dea886911864f359497a65f94164518"
        })
        
        try:
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            
            # Token အဖြေကို JSON ဖတ်ကြည့်မည်
            try:
                token_data = token_res.json()
            except Exception:
                # Token လင့်ခ်က JSON ပြန်မပေးပါက
                self.wfile.write(json.dumps({
                    "error_at": "Step 1 (Token Request)",
                    "status_code": token_res.status_code,
                    "ruijie_response": token_res.text
                }).encode('utf-8'))
                return
            
            access_token = token_data.get("accessToken")
            if not access_token:
                self.wfile.write(json.dumps({
                    "error_at": "Step 1 (Parsing Token)",
                    "message": "Token မပါလာပါ။",
                    "ruijie_response": token_data
                }).encode('utf-8'))
                return

            # အဆင့် (၂) - Voucher ထုတ်ခြင်း
            # မှတ်ချက် - ဤ URL ကို လက်စွဲစာအုပ်ထဲမှ အမှန်ဖြင့် အစားထိုးရန် လိုအပ်နိုင်ပါသည်။
            voucher_url = f"https://cloud-as.ruijienetworks.com/service/api/v1/voucher/create?token={access_token}"
            voucher_payload = json.dumps({
                "packageId": "123456", # မိမိ၏ Package ID အမှန်
                "quantity": 1
            })

            voucher_res = requests.post(voucher_url, headers=headers, data=voucher_payload)
            
            # Voucher အဖြေကို JSON ဖတ်ကြည့်မည်
            try:
                voucher_data = voucher_res.json()
            except Exception:
                # Voucher လင့်ခ်က JSON ပြန်မပေးပါက ဤနေရာတွင် အတိအကျ ပြမည်
                self.wfile.write(json.dumps({
                    "error_at": "Step 2 (Voucher Request)",
                    "status_code": voucher_res.status_code,
                    "ruijie_response": voucher_res.text,
                    "used_url": voucher_url
                }).encode('utf-8'))
                return
            
            # အားလုံးအောင်မြင်ပါက Voucher Data ကို ပြမည်
            self.wfile.write(json.dumps(voucher_data).encode('utf-8'))
            
        except Exception as e:
            # Code အတွင်း အခြား Error ရှိပါက
            self.wfile.write(json.dumps({
                "error_at": "System Code",
                "message": str(e),
                "traceback": traceback.format_exc()
            }).encode('utf-8'))
        
        return
