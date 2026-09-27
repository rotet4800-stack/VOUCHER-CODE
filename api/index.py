from http.server import BaseHTTPRequestHandler
import requests
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # API များကို ခေါ်ယူရာတွင် အသုံးပြုမည့် ခေါင်းစဉ် (Header)
        headers = { 'Content-Type': 'application/json' }
        
        # ၁။ Access Token အရင် တောင်းယူခြင်း
        token_url = "https://cloud-as.ruijienetworks.com/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
        token_payload = json.dumps({
            "appid": "openc3be644fb5dc",
            "secret": "0dea886911864f359497a65f94164518"
        })
        
        try:
            # Token အတွက် Request ပို့ခြင်း
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            
            # Error ရှာရန်အတွက် အဖြေကို JSON အနေနဲ့ မဖတ်ခင် ရိုးရိုးစာသားအနေနဲ့ အရင်ဖတ်ထားခြင်း
            raw_response = token_res.text 
            
            # JSON ဖတ်ရန် ကြိုးစားခြင်း
            try:
                token_data = token_res.json()
            except json.decoder.JSONDecodeError:
                # JSON ဖတ်မရပါက Ruijie မှ ပြန်လာသော မူရင်းစာသားကို မျက်နှာပြင်တွင် ပြပေးရန်
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_msg = {"error": "Ruijie API returned invalid JSON", "raw_response": raw_response}
                self.wfile.write(json.dumps(error_msg).encode('utf-8'))
                return

            # JSON ဖတ်လို့ရသွားရင် Token ကို ယူမည်
            access_token = token_data.get("accessToken")
            
            if access_token:
                # ၂။ ရလာတဲ့ Access Token ကို သုံးပြီး Voucher အသစ် ဖန်တီးခြင်း
                
                # သတိပြုရန်။ ။ အောက်ပါ voucher_url နှင့် packageId နေရာတွင် သင်၏ Documentation ထဲကအတိုင်း အမှန်ပြန်ပြောင်းထည့်ပေးရန် လိုအပ်ပါသည်။
                voucher_url = f"https://cloud-as.ruijienetworks.com/service/api/voucher/create?token={access_token}"
                
                # Voucher အတွက် သတ်မှတ်ချက်များ
                voucher_payload = json.dumps({
                    "packageId": "123456",  # မိမိထုတ်လိုသော Voucher Package ၏ ID 
                    "quantity": 1           # ထုတ်မည့် Voucher အရေအတွက်
                })
                
                # Voucher ထုတ်ရန် Request ဆက်ပို့ခြင်း
                voucher_res = requests.post(voucher_url, headers=headers, data=voucher_payload)
                
                # အောင်မြင်ပါက Vercel တွင် ပြသရန် 
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*') 
                self.end_headers()
                
                # Voucher ထွက်လာသော ရလဒ်ကို မျက်နှာပြင်တွင် ဖော်ပြခြင်း
                self.wfile.write(json.dumps(voucher_res.json()).encode('utf-8'))
            else:
                # Token မရပါက အမှားပြရန်
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_msg = {"error": "Failed to get access token", "details": token_data}
                self.wfile.write(json.dumps(error_msg).encode('utf-8'))
                
        except Exception as e:
            # Code အတွင်း အခြား System Error များရှိပါက ပြသရန်
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = {"error": "Internal Server Error", "message": str(e)}
            self.wfile.write(json.dumps(error_msg).encode('utf-8'))
        
        return
