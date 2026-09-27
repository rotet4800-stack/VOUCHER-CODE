from http.server import BaseHTTPRequestHandler
import requests
import json
import traceback
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        current_tab = query_params.get('tab', ['devices'])[0]

        APP_ID = "openc3be644fb5dc"
        SECRET = "0dea886911864f359497a65f94164518"
        BASE_URL = "https://cloud-as.ruijienetworks.com"
        GROUP_ID = "7833000"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            token_url = f"{BASE_URL}/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
            token_payload = json.dumps({"appid": APP_ID, "secret": SECRET})
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            token_data = token_res.json()
            
            if token_res.status_code != 200 or token_data.get("code") != 0:
                self.wfile.write("<h3>Failed to fetch token</h3>".encode('utf-8'))
                return

            access_token = token_data.get("accessToken")

            content_html = ""
            
            if current_tab == 'groups':
                ug_url = f"{BASE_URL}/service/api/intl/usergroup/list/{GROUP_ID}?pageIndex=0&pageSize=50&access_token={access_token}"
                ug_res = requests.get(ug_url, headers=headers)
                ug_data = ug_res.json()
                
                total_count = ug_data.get("count", 0)
                group_list = ug_data.get("data", [])
                
                items_html = ""
                for index, g in enumerate(group_list, 1):
                    name = g.get("userGroupName") or g.get("name") or "Unknown Group"
                    
                    items_html += f"""
                    <div style="background: #ffffff; padding: 18px 20px; margin-bottom: 12px; border-radius: 12px; border: 1px solid #d1e7dd; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; align-items: center; gap: 12px;">
                        <span style="color: #198754; font-weight: 800; font-size: 16px;">{index}.</span> 
                        <span style="font-size: 16px; font-weight: 700; color: #1f1f1f; letter-spacing: 0.5px;">{name}</span>
                    </div>
                    """
                
                content_html = f"""
                <div class="sticky-header">
                    <div class="nav-tabs">
                        <a href="?tab=devices" class="nav-tab {'active' if current_tab == 'devices' else ''}">Connected Devices</a>
                        <a href="?tab=groups" class="nav-tab {'active' if current_tab == 'groups' else ''}">User Groups</a>
                    </div>
                    <div class="counter">Total Groups: {total_count}</div>
                </div>
                <div class="scrollable-list">
                    {items_html if items_html else '<p style="text-align:center; color:#2e7d32;">No groups found.</p>'}
                </div>
                """
            else:
                client_url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user?group_id={GROUP_ID}&page_index=1&page_size=100&access_token={access_token}"
                client_res = requests.get(client_url, headers=headers)
                client_data = client_res.json()
                
                total_count = client_data.get("totalCount", 0)
                raw_list = client_data.get("list", [])
                
                items_html = ""
                for index, client in enumerate(raw_list, 1):
                    brand = client.get("manufacturer") or "Unknown"
                    model = client.get("staModel") or client.get("userName") or "Mobile Device"
                    band = client.get("band") or "-"
                    
                    items_html += f"""
                    <div style="background: #ffffff; padding: 16px 20px; margin-bottom: 12px; border-radius: 12px; border: 1px solid #d1e7dd; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div>
                            <div style="font-size: 15px; font-weight: 700; color: #1f1f1f; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #198754; font-weight: 800;">{index}.</span> 
                                <span style="text-transform: uppercase; letter-spacing: 0.5px;">{brand}</span>
                            </div>
                            <div style="font-size: 13px; color: #605e5c; margin-top: 4px; padding-left: 20px;">
                                Model: <b style="color: #323130;">{model}</b>
                            </div>
                        </div>
                        <div style="background: #d1e7dd; color: #0f5132; padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #badbcc;">
                            {band}
                        </div>
                    </div>
                    """
                
                content_html = f"""
                <div class="sticky-header">
                    <div class="nav-tabs">
                        <a href="?tab=devices" class="nav-tab {'active' if current_tab == 'devices' else ''}">Connected Devices</a>
                        <a href="?tab=groups" class="nav-tab {'active' if current_tab == 'groups' else ''}">User Groups</a>
                    </div>
                    <div class="counter">Total Connected: {total_count} Devices</div>
                </div>
                <div class="scrollable-list">
                    {items_html if items_html else '<p style="text-align:center; color:#2e7d32;">No connected devices found.</p>'}
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <title>Network Management Dashboard</title>
                <style>
                    html, body {{ height: 100%; margin: 0; padding: 0; overflow: hidden; background: #e8f5e9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #323130; }}
                    .container {{ max-width: 500px; height: 100vh; margin: 0 auto; background: #c8e6c9; padding: 16px; box-sizing: border-box; display: flex; flex-direction: column; border-left: 1px solid #a5d6a7; border-right: 1px solid #a5d6a7; }}
                    .sticky-header {{ flex-shrink: 0; background: #c8e6c9; padding-bottom: 10px; z-index: 10; }}
                    .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 12px; }}
                    .nav-tab {{ flex: 1; text-align: center; padding: 10px; background: #a5d6a7; color: #1b5e20; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 14px; transition: all 0.2s; }}
                    .nav-tab.active {{ background: #198754; color: #ffffff; box-shadow: 0 3px 6px rgba(25,135,84,0.3); }}
                    .counter {{ background: #198754; color: #ffffff; padding: 14px; border-radius: 12px; text-align: center; font-size: 16px; font-weight: 600; box-shadow: 0 4px 8px rgba(25,135,84,0.3); }}
                    .scrollable-list {{ flex-grow: 1; overflow-y: auto; padding-right: 4px; margin-top: 8px; -webkit-overflow-scrolling: touch; }}
                    .scrollable-list::-webkit-scrollbar {{ width: 6px; }}
                    .scrollable-list::-webkit-scrollbar-thumb {{ background: #a5d6a7; border-radius: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {content_html}
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(f"<h3>System Error: {str(e)}</h3>".encode('utf-8'))
        
        return
