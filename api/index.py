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

        APP_ID = "openc3be644fb5dc"
        SECRET = "0dea886911864f359497a65f94164518"
        BASE_URL = "https://cloud-as.ruijienetworks.com"
        GROUP_ID = "7833000"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            # ၁။ Access Token တောင်းယူခြင်း
            token_url = f"{BASE_URL}/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
            token_payload = json.dumps({
                "appid": APP_ID,
                "secret": SECRET
            })
            
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            token_data = token_res.json()
            
            if token_res.status_code != 200 or token_data.get("code") != 0:
                self.wfile.write(json.dumps({"error": "Token ရယူရန် မအောင်မြင်ပါ", "details": token_data}).encode('utf-8'))
                return

            access_token = token_data.get("accessToken")

            # ၂။ ချိတ်ဆက်ထားသော ဖုန်း/စက်ပစ္စည်းစာရင်းကို ဆွဲထုတ်ခြင်း (Client Information API)
            client_url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user?group_id={GROUP_ID}&page_index=1&page_size=100&access_token={access_token}"
            client_res = requests.get(client_url, headers=headers)
            client_data = client_res.json()
            
            if client_res.status_code != 200 or client_data.get("code") != 0:
                self.wfile.write(json.dumps({"error": "ဖုန်းစာရင်း ရယူရန် မအောင်မြင်ပါ", "details": client_data}).encode('utf-8'))
                return

            total_count = client_data.get("totalCount", 0)
            raw_list = client_data.get("list", [])
            
            # လိုအပ်မည့် အချက်အလက်များကိုသာ စစ်ထုတ်ခြင်း
            formatted_clients = []
            for client in raw_list:
                formatted_clients.append({
                    "brand": client.get("manufacturer") or "Unknown",
                    "model": client.get("staModel") or client.get("userName") or "Mobile Device",
                    "ip": client.get("ip"),
                    "mac": client.get("mac"),
                    "band": client.get("band")
                })

            response_output = {
                "code": 0,
                "msg": "Success",
                "totalConnectedDevices": total_count,
                "devices": formatted_clients
            }
            
            # ရလဒ်ကို JSON ဖြင့် ပြသခြင်း
            self.wfile.write(json.dumps(response_output, indent=2).encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(json.dumps({
                "error": "System Error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }).encode('utf-8'))
        
        return
