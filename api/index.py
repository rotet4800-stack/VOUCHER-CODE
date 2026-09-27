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

            # ၂။ User Group List အစစ်အမှန် ဆွဲထုတ်ခြင်း (API 2.7.1)
            ug_url = f"{BASE_URL}/service/api/intl/usergroup/list/{GROUP_ID}?pageIndex=0&pageSize=50&access_token={access_token}"
            ug_res = requests.get(ug_url, headers=headers)
            ug_data = ug_res.json()
            
            if ug_res.status_code != 200 or ug_data.get("code") != 0:
                self.wfile.write(f"<h3>User Group စာရင်း ရယူရန် မအောင်မြင်ပါ: {ug_data.get('msg')}</h3>".encode('utf-8'))
                return

            total_count = ug_data.get("count", 0)
            group_list = ug_data.get("data", [])
            
            groups_html = ""
            for index, g in enumerate(group_list, 1):
                name = g.get("userGroupName") or g.get("name") or "Unknown Group"
                ug_id = g.get("id")
                profile_id = g.get("authProfileId")
                quota = g.get("quota", 0)
                devices = g.get("noOfDevice", 0)
                
                groups_html += f"""
                <div style="background: #ffffff; padding: 16px 20px; margin-bottom: 12px; border-radius: 12px; border: 1px solid #d1e7dd; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                    <div style="font-size: 16px; font-weight: 700; color: #1f1f1f; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="color: #198754; font-weight: 800;">{index}.</span> 
                        <span style="letter-spacing: 0.5px;">{name}</span>
                    </div>
                    <div style="font-size: 13px; color: #605e5c; display: flex; flex-direction: column; gap: 4px; padding-left: 20px;">
                        <div>Group ID: <b style="color: #323130;">{ug_id}</b></div>
                        <div>Profile ID: <b style="color: #323130; word-break: break-all;">{profile_id}</b></div>
                        <div>Traffic Quota: <b style="color: #198754;">{quota} MB</b></div>
                    </div>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html lang="my">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>User Group Management</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #e8f5e9; margin: 0; padding: 16px; color: #323130; }}
                    .container {{ max-width: 500px; margin: 10px auto; background: #c8e6c9; padding: 20px; border-radius: 20px; box-shadow: 0 6px 16px rgba(0,0,0,0.08); border: 1px solid #a5d6a7; display: flex; flex-direction: column; height: 85vh; box-sizing: border-box; }}
                    h2 {{ color: #1b5e20; text-align: center; margin-top: 0; margin-bottom: 16px; font-size: 20px; font-weight: 700; }}
                    .sticky-header {{ position: sticky; top: 0; background: #c8e6c9; z-index: 10; padding-bottom: 10px; }}
                    .counter {{ background: #198754; color: #ffffff; padding: 14px; border-radius: 12px; text-align: center; font-size: 16px; font-weight: 600; box-shadow: 0 4px 8px rgba(25,135,84,0.3); }}
                    .scrollable-list {{ overflow-y: auto; flex-grow: 1; padding-right: 4px; margin-top: 5px; }}
                    .scrollable-list::-webkit-scrollbar {{ width: 6px; }}
                    .scrollable-list::-webkit-scrollbar-thumb {{ background: #a5d6a7; border-radius: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="sticky-header">
                        <h2>အသုံးပြုသူ အုပ်စုများ (User Groups)</h2>
                        <div class="counter">စုစုပေါင်း အုပ်စုအရေအတွက်: {total_count} ခု</div>
                    </div>
                    <div class="scrollable-list">
                        {groups_html if groups_html else '<p style="text-align:center; color:#2e7d32;">အုပ်စု အချက်အလက် မရှိသေးပါ။</p>'}
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(f"<h3>စနစ် အမှားအယွင်းရှိပါသည်: {str(e)}</h3>".encode('utf-8'))
        
        return
