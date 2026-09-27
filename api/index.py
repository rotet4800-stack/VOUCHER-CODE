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
        selected_group_id = query_params.get('group_id', [None])[0]
        selected_group_name = query_params.get('group_name', ['Group'])[0]

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
                
                total_groups = ug_data.get("count", 0)
                group_list = ug_data.get("data", [])
                
                if selected_group_id:
                    v_list = []
                    
                    acc_url = f"{BASE_URL}/service/api/open/auth/account/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                    acc_res = requests.get(acc_url, headers=headers)
                    if acc_res.status_code == 200 and acc_res.json().get("code") == 0:
                        for acc in acc_res.json().get("list", []):
                            if str(acc.get("userGroupId")) == str(selected_group_id) or str(acc.get("groupId")) == str(selected_group_id):
                                v_list.append({
                                    "codeNo": acc.get("username") or acc.get("account"),
                                    "status": acc.get("status", "1")
                                })
                    
                    if not v_list:
                        v_url = f"{BASE_URL}/service/api/open/auth/voucher/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                        v_res = requests.get(v_url, headers=headers)
                        if v_res.status_code == 200 and v_res.json().get("voucherData", {}).get("code") == 0:
                            for v in v_res.json().get("voucherData", {}).get("list", []):
                                if str(v.get("userGroupId")) == str(selected_group_id) or str(v.get("groupId")) == str(selected_group_id):
                                    v_list.append({
                                        "codeNo": v.get("codeNo") or v.get("voucherCode"),
                                        "status": v.get("status", "1")
                                    })

                    if not v_list and acc_res.status_code == 200:
                        raw_acc = acc_res.json().get("list", [])
                        for acc in raw_acc:
                            v_list.append({
                                "codeNo": acc.get("username") or acc.get("account"),
                                "status": acc.get("status", "1")
                            })
                    
                    v_count = len(v_list)
                    vouchers_html = ""
                    for v_idx, v in enumerate(v_list, 1):
                        code_no = v.get("codeNo") or "N/A"
                        status = str(v.get("status", "1"))
                        status_text = "In-Use" if status == "2" else ("Expired" if status == "3" else "Available")
                        status_color = "#198754" if status == "2" else ("#dc3545" if status == "3" else "#0d6efd")
                        
                        vouchers_html += f"""
                        <div style="background: #f8f9fa; padding: 12px 16px; margin-bottom: 8px; border-radius: 10px; border: 1px solid #ced4da; display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 14px; font-weight: 700; color: #1f1f1f;">{v_idx}. Code: <b style="color: #0d6efd; font-family: monospace; font-size: 15px;">{code_no}</b></span>
                            <span style="background: {status_color}20; color: {status_color}; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">{status_text}</span>
                        </div>
                        """
                    
                    content_html = f"""
                    <div class="sticky-header">
                        <div class="nav-tabs">
                            <a href="?tab=devices" class="nav-tab">Connected Devices</a>
                            <a href="?tab=groups" class="nav-tab active">User Groups</a>
                        </div>
                        <a href="?tab=groups" style="display: block; text-align: center; background: #cfe2ff; color: #084298; padding: 10px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 14px; margin-bottom: 8px; border: 1px solid #b6d4fe;">Back to Groups</a>
                        <div class="blue-box">{selected_group_name} - Total Cards: {v_count}</div>
                    </div>
                    <div class="scrollable-list">
                        {vouchers_html if vouchers_html else '<p style="text-align:center; color:#495057; margin-top:20px;">No vouchers found in this group.</p>'}
                    </div>
                    """
                else:
                    total_vouchers = 0
                    used_vouchers = 0
                    expired_vouchers = 0
                    
                    acc_url = f"{BASE_URL}/service/api/open/auth/account/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                    acc_res = requests.get(acc_url, headers=headers)
                    if acc_res.status_code == 200 and acc_res.json().get("code") == 0:
                        acc_list = acc_res.json().get("list", [])
                        total_vouchers = len(acc_list)
                        for acc in acc_list:
                            status = str(acc.get("status", "1"))
                            if status == "2":
                                used_vouchers += 1
                            elif status == "3":
                                expired_vouchers += 1
                    
                    if total_vouchers == 0:
                        v_url = f"{BASE_URL}/service/api/open/auth/voucher/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                        v_res = requests.get(v_url, headers=headers)
                        if v_res.status_code == 200:
                            v_root = v_res.json().get("voucherData", {})
                            if v_root.get("code") == 0:
                                v_list = v_root.get("list", [])
                                total_vouchers = len(v_list)
                                for v in v_list:
                                    status = str(v.get("status", "1"))
                                    if status == "2":
                                        used_vouchers += 1
                                    elif status == "3":
                                        expired_vouchers += 1

                    items_html = ""
                    for index, g in enumerate(group_list, 1):
                        name = g.get("userGroupName") or g.get("name") or "Unknown Group"
                        g_id = g.get("id")
                        
                        items_html += f"""
                        <a href="?tab=groups&group_id={g_id}&group_name={name}" style="text-decoration: none; display: block;">
                            <div class="blue-card">
                                <span style="color: #0d6efd; font-weight: 800; font-size: 15px;">{index}.</span> 
                                <span style="font-size: 15px; font-weight: 700; color: #1f1f1f; letter-spacing: 0.5px;">{name}</span>
                            </div>
                        </a>
                        """
                    
                    content_html = f"""
                    <div class="sticky-header">
                        <div class="nav-tabs">
                            <a href="?tab=devices" class="nav-tab {'active' if current_tab == 'devices' else ''}">Connected Devices</a>
                            <a href="?tab=groups" class="nav-tab {'active' if current_tab == 'groups' else ''}">User Groups</a>
                        </div>
                        <div class="blue-box">Total Groups: {total_groups}</div>
                        <div class="footer-summary" style="margin-top: 8px;">
                            <div class="summary-card">Total: <b>{total_vouchers}</b></div>
                            <div class="summary-card">In-Use: <b>{used_vouchers}</b></div>
                            <div class="summary-card">Expired: <b>{expired_vouchers}</b></div>
                        </div>
                    </div>
                    <div class="scrollable-list">
                        {items_html if items_html else '<p style="text-align:center; color:#495057;">No groups found.</p>'}
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
                    <div style="background: #f8f9fa; padding: 14px 18px; margin-bottom: 10px; border-radius: 12px; border: 1px solid #ced4da; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div>
                            <div style="font-size: 14px; font-weight: 700; color: #1f1f1f; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #0d6efd; font-weight: 800;">{index}.</span> 
                                <span style="text-transform: uppercase; letter-spacing: 0.5px;">{brand}</span>
                            </div>
                            <div style="font-size: 12px; color: #6c757d; margin-top: 2px; padding-left: 20px;">
                                Model: <b style="color: #343a40;">{model}</b>
                            </div>
                        </div>
                        <div style="background: #cfe2ff; color: #084298; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #b6d4fe;">
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
                    <div class="blue-box">Total Connected: {total_count} Devices</div>
                </div>
                <div class="scrollable-list">
                    {items_html if items_html else '<p style="text-align:center; color:#495057;">No connected devices found.</p>'}
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
                    html, body {{ height: 100%; margin: 0; padding: 0; overflow: hidden; background: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #212529; }}
                    .container {{ max-width: 500px; height: 100%; margin: 0 auto; background: #e9ecef; padding: 12px; box-sizing: border-box; display: flex; flex-direction: column; border-left: 2px solid #dee2e6; border-right: 2px solid #dee2e6; }}
                    .sticky-header {{ flex-shrink: 0; background: #e9ecef; padding-bottom: 6px; z-index: 10; }}
                    .nav-tabs {{ display: flex; gap: 8px; margin-bottom: 8px; }}
                    .nav-tab {{ flex: 1; text-align: center; padding: 10px; background: #ced4da; color: #495057; text-decoration: none; border-radius: 10px; font-weight: 700; font-size: 13px; transition: all 0.2s; border: 1px solid #adb5bd; }}
                    .nav-tab.active {{ background: #0d6efd; color: #ffffff; box-shadow: 0 3px 6px rgba(13,110,253,0.3); border-color: #0b5ed7; }}
                    .blue-box {{ background: #0d6efd; color: #ffffff; padding: 16px; border-radius: 14px; text-align: center; font-size: 17px; font-weight: 700; box-shadow: 0 4px 10px rgba(13,110,253,0.3); margin-bottom: 8px; border: 2px solid #084298; }}
                    .blue-card {{ background: #f8f9fa; padding: 14px 18px; margin-bottom: 10px; border-radius: 12px; border: 2px solid #ced4da; box-shadow: 0 2px 4px rgba(0,0,0,0.04); display: flex; align-items: center; gap: 12px; }}
                    .footer-summary {{ display: flex; gap: 6px; }}
                    .summary-card {{ flex: 1; background: #f8f9fa; border: 2px solid #ced4da; padding: 10px 6px; border-radius: 10px; text-align: center; font-size: 12px; font-weight: 600; color: #212529; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }}
                    .summary-card b {{ display: block; color: #0d6efd; font-size: 14px; margin-top: 2px; }}
                    .scrollable-list {{ flex-grow: 1; overflow-y: auto; padding-right: 4px; margin-top: 6px; -webkit-overflow-scrolling: touch; min-height: 0; }}
                    .scrollable-list::-webkit-scrollbar {{ width: 5px; }}
                    .scrollable-list::-webkit-scrollbar-thumb {{ background: #adb5bd; border-radius: 10px; }}
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
