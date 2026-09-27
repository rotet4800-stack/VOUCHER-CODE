from http.server import BaseHTTPRequestHandler
import requests
import json
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # ၁။ Access Token တောင်းယူခြင်း
        token_url = "https://cloud-as.ruijienetworks.com/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
        token_payload = json.dumps({
            "appid": "openc3be644fb5dc",
            "secret": "0dea886911864f359497a65f94164518"
        })
        
        try:
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            token_data = token_res.json()
            access_token = token_data.get("accessToken")
            
            if not access_token:
                self.wfile.write(json.dumps({"error": "Token မရရှိပါ။", "details": token_data}).encode('utf-8'))
                return

            # --- ဤနေရာတွင် သင်၏ Ruijie Cloud ထဲမှ မှန်ကန်သော Group ID (Project ID) ကို ထည့်ပါ ---
            # ဥပမာ - group_id = 12482
            group_id = 12482  # <-- ဒီနံပါတ်ကို သင့်အကောင့်ထဲက ID အမှန်နဲ့ လဲပေးပါ
            
            # ၂။ Voucher ထုတ်လုပ်ခြင်း (Generate Voucher API)
            voucher_url = f"https://cloud-as.ruijienetworks.com/service/api/open/auth/voucher/create/{group_id}?access_token={access_token}"
            
            # Voucher အတွက် လိုအပ်သော Parameter များ (Documentation ထဲကအတိုင်း)
            voucher_payload = json.dumps({
                "quantity": 1,
                "profile": "30113648274480073538014045592098", # သင့်အကောင့်ထဲရှိ Profile UUID ဖြင့် လဲရန်
                "userGroupId": 18067                       # သင့်အကောင့်ထဲရှိ User Group ID ဖြင့် လဲရန်
            })

            voucher_res = requests.post(voucher_url, headers=headers, data=voucher_payload)
            voucher_data = voucher_res.json()
            
            # ရလဒ်ကို ပြသခြင်း
            self.wfile.write(json.dumps(voucher_data).encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(json.dumps({
                "error": "System Error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }).encode('utf-8'))
        
        return
