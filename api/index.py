from http.server import BaseHTTPRequestHandler
import requests
import json
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
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
            token_payload = json.dumps({"appid": APP_ID, "secret": SECRET})
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            token_data = token_res.json()
            
            if token_res.status_code != 200 or token_data.get("code") != 0:
                self.wfile.write("<h3>Token ရယူရန် မအောင်မြင်ပါ</h3>".encode('utf-8'))
                return

            access_token = token_data.get("accessToken")

            # ၂။ ဖုန်း/စက်ပစ္စည်းစာရင်း ဆွဲထုတ်ခြင်း
            client_url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user?group_id={GROUP_ID}&page_index=1&page_size=100&access_token={access_token}"
            client_res = requests.get(client_url, headers=headers)
            client_data = client_res.json()
            
            if client_res.status_code != 200 or client_data.get("code") != 0:
                self.wfile.write("<h3>ဖုန်းစာရင်း ရယူရန် မအောင်မြင်ပါ</h3>".encode('utf-8'))
                return

            total_count = client_data.get("totalCount", 0)
            raw_list = client_data.get("list", [])
            
            devices_html = ""
            for index, client in enumerate(raw_list, 1):
                brand = client.get("manufacturer") or "Unknown"
                model = client.get("staModel") or client.get("userName") or "Mobile Device"
                band = client.get("band") or "-"
                
                devices_html += f"""
                <div style="background: #f8f9fa; padding: 14px 18px; margin-bottom: 10px; border-radius: 8px; border-left: 4px solid #1a73e8; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div>
                        <div style="font-size: 16px; font-weight: bold; color: #202124;">
                            {index}. Brand: <span style="color: #1a73e8;">{brand}</span>
                        </div>
                        <div style="font-size: 14px; color: #5f6368; margin-top: 4px;">
                            Model: <b>{model}</b>
                        </div>
                    </div>
                    <div style="background: #e8f0fe; color: #1a73e8; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;">
                        {band}
                    </div>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html lang="my">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Ruijie Connected Devices</title>
                <style>
                    body {{ font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #fff; padding: 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                    h2 {{ color: #1a73e8; text-align: center; margin-bottom: 20px; }}
                    .counter {{ background: #e8f0fe; color: #1a73e8; padding: 14px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Ruijie Wi-Fi ချိတ်ဆက်ထားသော ဖုန်းများ</h2>
                    <div class="counter">စုစုပေါင်း ချိတ်ဆက်ထားသူ: {total_count} လုံး</div>
                    <div>{devices_html if devices_html else '<p style="text-align:center; color:#777;">ချိတ်ဆက်ထားသော စက်ပစ္စည်း မရှိသေးပါ။</p>'}</div>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(f"<h3>System Error: {str(e)}</h3>".encode('utf-8'))
        
        return
