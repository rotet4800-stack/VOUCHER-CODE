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
                self.wfile.write("<h3>ဒေတာရယူရန် မအောင်မြင်ပါ</h3>".encode('utf-8'))
                return

            access_token = token_data.get("accessToken")

            # ၂။ ဖုန်း/စက်ပစ္စည်းစာရင်း ဆွဲထုတ်ခြင်း
            client_url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user?group_id={GROUP_ID}&page_index=1&page_size=100&access_token={access_token}"
            client_res = requests.get(client_url, headers=headers)
            client_data = client_res.json()
            
            if client_res.status_code != 200 or client_data.get("code") != 0:
                self.wfile.write("<h3>ချိတ်ဆက်မှုစာရင်း ရယူရန် မအောင်မြင်ပါ</h3>".encode('utf-8'))
                return

            total_count = client_data.get("totalCount", 0)
            raw_list = client_data.get("list", [])
            
            devices_html = ""
            for index, client in enumerate(raw_list, 1):
                brand = client.get("manufacturer") or "Unknown"
                model = client.get("staModel") or client.get("userName") or "Mobile Device"
                band = client.get("band") or "-"
                
                devices_html += f"""
                <div style="background: #ffffff; padding: 16px 20px; margin-bottom: 12px; border-radius: 12px; border: 1px solid #e1dfdd; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s ease;">
                    <div>
                        <div style="font-size: 15px; font-weight: 700; color: #1f1f1f; display: flex; align-items: center; gap: 8px;">
                            <span style="color: #0078d4; font-weight: 800;">{index}.</span> 
                            <span style="text-transform: uppercase; letter-spacing: 0.5px;">{brand}</span>
                        </div>
                        <div style="font-size: 13px; color: #605e5c; margin-top: 4px; padding-left: 20px;">
                            Model: <b style="color: #323130;">{model}</b>
                        </div>
                    </div>
                    <div style="background: #eff6fc; color: #0078d4; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #c7e0f4;">
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
                <title>Connected Devices Overview</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f3f2f1; margin: 0; padding: 16px; color: #323130; }}
                    .container {{ max-width: 500px; margin: 20px auto; background: #faf9f8; padding: 24px; border-radius: 16px; box-shadow: 0 6px 16px rgba(0,0,0,0.06); border: 1px id #edebe9; }}
                    h2 {{ color: #201f1e; text-align: center; margin-bottom: 20px; font-size: 20px; font-weight: 700; }}
                    .counter {{ background: #0078d4; color: #ffffff; padding: 14px; border-radius: 10px; text-align: center; font-size: 16px; font-weight: 600; margin-bottom: 24px; box-shadow: 0 4px 8px rgba(0,120,212,0.2); }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>ကြိုးမဲ့အင်တာနက် ချိတ်ဆက်ထားသော စက်များ</h2>
                    <div class="counter">စုစုပေါင်း ချိတ်ဆက်ထားသူ: {total_count} လုံး</div>
                    <div>{devices_html if devices_html else '<p style="text-align:center; color:#605e5c;">ချိတ်ဆက်ထားသော စက်ပစ္စည်း မရှိသေးပါ။</p>'}</div>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(f"<h3>စနစ် အမှားအယွင်းရှိပါသည်: {str(e)}</h3>".encode('utf-8'))
        
        return
