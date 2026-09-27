from http.server import BaseHTTPRequestHandler
import requests
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        url = "https://cloud-as.ruijienetworks.com/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
        payload = json.dumps({
            "appid": "openc3be644fb5dc",
            "secret": "0dea886911864f359497a65f94164518"
        })
        headers = { 'Content-Type': 'application/json' }

        # Ruijie ဆီမှ Token တောင်းခြင်း
        res = requests.post(url, headers=headers, data=payload)
        
        # ရလာတဲ့ ရလဒ်ကို မျက်နှာပြင်မှာ ပြပေးခြင်း
        self.wfile.write(json.dumps(res.json()).encode('utf-8'))
        return
