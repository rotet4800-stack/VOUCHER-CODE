from http.server import BaseHTTPRequestHandler
import requests
import json
import traceback
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        current_tab = query_params.get('tab', ['devices'])[0]
        selected_group_id = query_params.get('group_id', [None])[0]
        selected_group_name = query_params.get('group_name', ['Group'])[0]
        action = query_params.get('action', [None])[0]

        # Cookie စစ်ဆေးခြင်း (တစ်ခါဝင်ထားရင် နောက်တစ်ခါ ထပ်မလိုတော့ရန်)
        cookie_header = self.headers.get('Cookie', '')
        is_logged_in = 'auth_session=true' in cookie_header

        if action == 'do_login':
            u = query_params.get('username', [''])[0]
            p = query_params.get('password', [''])[0]
            if u == 'admin' and p == '1234':
                self.send_response(303)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Set-Cookie', 'auth_session=true; Path=/; Max-Age=2592000; HttpOnly')
                self.send_header('Location', '/?tab=devices')
                self.end_headers()
                return
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write("""
                <script>
                    alert('Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။');
                    window.location.href = '/';
                </script>
                """.encode('utf-8'))
                return

        if action == 'logout':
            self.send_response(303)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Set-Cookie', 'auth_session=false; Path=/; Max-Age=0; HttpOnly')
            self.send_header('Location', '/')
            self.end_headers()
            return

        if not is_logged_in:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            login_html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <title>Login - Network Dashboard</title>
                <style>
                    html, body { height: 100%; margin: 0; padding: 0; overflow: hidden; background: #0d6efd; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; width: 100%; position: fixed; top: 0; left: 0; touch-action: none; }
                    .login-card { background: transparent; padding: 20px; width: 90%; max-width: 380px; box-sizing: border-box; text-align: center; z-index: 999; }
                    .login-title { font-size: 22px; font-weight: 800; color: #ffffff; margin-bottom: 24px; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .input-group { margin-bottom: 16px; text-align: left; position: relative; }
                    .input-group label { display: block; font-weight: 700; margin-bottom: 6px; color: #ffffff; font-size: 14px; }
                    .input-container { position: relative; display: flex; align-items: center; }
                    .input-icon { position: absolute; left: 12px; font-size: 18px; color: #6c757d; }
                    .input-group input { width: 100%; padding: 12px 12px 12px 40px; border: 2px solid #ced4da; border-radius: 10px; font-size: 16px; box-sizing: border-box; outline: none; background: #ffffff; color: #212529; }
                    .input-group input:focus { border-color: #ffffff; }
                    .toggle-eye { position: absolute; right: 12px; cursor: pointer; font-size: 18px; color: #6c757d; }
                    .login-btn { width: 100%; background: #ffffff; color: #0d6efd; border: none; padding: 14px; border-radius: 12px; font-size: 17px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.15); margin-top: 10px; }
                </style>
            </head>
            <body>
                <div class="login-card">
                    <div class="login-title">Network Management Login</div>
                    <form action="" method="GET">
                        <input type="hidden" name="action" value="do_login">
                        <div class="input-group">
                            <label>Username</label>
                            <div class="input-container">
                                <span class="input-icon">👤</span>
                                <input type="text" name="username" required autocomplete="off">
                            </div>
                        </div>
                        <div class="input-group">
                            <label>Password</label>
                            <div class="input-container">
                                <span class="input-icon">🔒</span>
                                <input type="password" name="password" id="password-field" required>
                                <span class="toggle-eye" onclick="togglePassword()">👁️</span>
                            </div>
                        </div>
                        <button type="submit" class="login-btn">Login</button>
                    </form>
                </div>
                <script>
                    function togglePassword() {
                        let pwd = document.getElementById("password-field");
                        if (pwd.type === "password") {
                            pwd.type = "text";
                        } else {
                            pwd.type = "password";
                        }
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(login_html.encode('utf-8'))
            return

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
            token_res = requests.post(token_url, headers=headers, data=token_payload, timeout=5)
            token_data = token_res.json()
            
            if token_res.status_code != 200 or token_data.get("code") != 0:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write("<h3>Failed to fetch token</h3>".encode('utf-8'))
                return

            access_token = token_data.get("accessToken")

            if action == 'generate_now' and selected_group_id:
                quantity = int(query_params.get('quantity', [1])[0])
                
                ug_url = f"{BASE_URL}/service/api/intl/usergroup/list/{GROUP_ID}?pageIndex=0&pageSize=50&access_token={access_token}"
                ug_res = requests.get(ug_url, headers=headers, timeout=5)
                profile_id = "30113648274480073538014045592098"
                user_group_id = int(selected_group_id)
                
                if ug_res.status_code == 200:
                    for g in ug_res.json().get("data", []):
                        if str(g.get("id")) == str(selected_group_id):
                            profile_id = g.get("authProfileId", profile_id)
                            user_group_id = g.get("id", user_group_id)
                            break

                create_url = f"{BASE_URL}/service/api/open/auth/voucher/create/{GROUP_ID}?access_token={access_token}"
                create_payload = json.dumps({
                    "quantity": quantity,
                    "profile": str(profile_id),
                    "userGroupId": int(user_group_id),
                    "comment": f"Generated for {selected_group_name}"
                })
                requests.post(create_url, headers=headers, data=create_payload, timeout=5)
                
                self.send_response(303)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Location', f'/?tab=groups&group_id={selected_group_id}&group_name={selected_group_name}')
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            content_html = ""
            
            if current_tab == 'groups':
                def fetch_groups():
                    url = f"{BASE_URL}/service/api/intl/usergroup/list/{GROUP_ID}?pageIndex=0&pageSize=50&access_token={access_token}"
                    return requests.get(url, headers=headers, timeout=5).json()

                def fetch_accounts():
                    url = f"{BASE_URL}/service/api/open/auth/account/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                    return requests.get(url, headers=headers, timeout=5).json()

                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_ug = executor.submit(fetch_groups)
                    future_acc = executor.submit(fetch_accounts)
                    
                    ug_data = future_ug.result()
                    acc_res_json = future_acc.result()

                total_groups = ug_data.get("count", 0)
                group_list = ug_data.get("data", [])
                
                if selected_group_id:
                    if action == 'generate_form':
                        content_html = """
                        <div class="sticky-header">
                            <div class="nav-tabs">
                                <a href="?tab=devices" class="nav-tab">Connected Devices</a>
                                <a href="?tab=groups" class="nav-tab active">User Groups</a>
                                <a href="?action=logout" class="nav-tab" style="background: #dc3545; color: #fff; max-width: 60px;" title="Logout">🚪</a>
                            </div>
                            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                                <a href="?tab=groups&group_id=""" + str(selected_group_id) + """&group_name=""" + str(selected_group_name) + """" style="flex: 1; text-align: center; background: #ced4da; color: #495057; padding: 12px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 15px; border: 1px solid #adb5bd;">Back</a>
                            </div>
                            <div class="blue-box" style="font-size: 15px; margin-bottom: 4px;">""" + str(selected_group_name) + """</div>
                            <div style="text-align: center; color: #084298; font-weight: 700; font-size: 16px; margin-bottom: 12px;">Generate Voucher Code</div>
                        </div>
                        <div style="background: #ffffff; padding: 20px; border-radius: 14px; border: 2px solid #ced4da; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-top: 10px;">
                            <form action="" method="GET">
                                <input type="hidden" name="tab" value="groups">
                                <input type="hidden" name="group_id" value="""" + str(selected_group_id) + """"">
                                <input type="hidden" name="group_name" value="""" + str(selected_group_name) + """"">
                                <input type="hidden" name="action" value="generate_now">
                                
                                <div style="margin-bottom: 16px;">
                                    <label style="display: block; font-weight: 700; margin-bottom: 6px; color: #212529;">အရေအတွက် (Quantity)</label>
                                    <input type="number" name="quantity" value="1" min="1" max="500" style="width: 100%; padding: 12px; border: 2px solid #ced4da; border-radius: 10px; font-size: 16px; box-sizing: border-box;">
                                </div>
                                <div style="margin-bottom: 16px;">
                                    <label style="display: block; font-weight: 700; margin-bottom: 6px; color: #212529;">Type</label>
                                    <select style="width: 100%; padding: 12px; border: 2px solid #ced4da; border-radius: 10px; font-size: 16px; background: #fff; box-sizing: border-box;">
                                        <option>a-z 0-9</option>
                                    </select>
                                </div>
                                <div style="margin-bottom: 20px;">
                                    <label style="display: block; font-weight: 700; margin-bottom: 6px; color: #212529;">Voucher Length</label>
                                    <select style="width: 100%; padding: 12px; border: 2px solid #ced4da; border-radius: 10px; font-size: 16px; background: #fff; box-sizing: border-box;">
                                        <option>6</option>
                                    </select>
                                </div>
                                <button type="submit" style="width: 100%; background: #0d6efd; color: #ffffff; border: none; padding: 14px; border-radius: 12px; font-size: 17px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 8px rgba(13,110,253,0.3);">Generate</button>
                            </form>
                        </div>
                        """
                    else:
                        v_list = []
                        if acc_res_json.get("code") == 0:
                            for acc in acc_res_json.get("list", []):
                                if str(acc.get("userGroupId")) == str(selected_group_id) or str(acc.get("groupId")) == str(selected_group_id):
                                    v_list.append({
                                        "codeNo": acc.get("username") or acc.get("account"),
                                        "status": acc.get("status", "1")
                                    })
                        
                        if not v_list:
                            v_url = f"{BASE_URL}/service/api/open/auth/voucher/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                            v_res = requests.get(v_url, headers=headers, timeout=5)
                            if v_res.status_code == 200:
                                v_root = v_res.json().get("voucherData", {})
                                if v_root.get("code") == 0:
                                    for v in v_root.get("list", []):
                                        if str(v.get("userGroupId")) == str(selected_group_id) or str(v.get("groupId")) == str(selected_group_id):
                                            v_list.append({
                                                "codeNo": v.get("codeNo") or v.get("voucherCode"),
                                                "status": v.get("status", "1")
                                            })

                        if not v_list and acc_res_json.get("code") == 0:
                            raw_acc = acc_res_json.get("list", [])
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
                        
                        codes_json = json.dumps([v.get('codeNo') for v in v_list])
                        content_html = f"""
                        <div class="sticky-header">
                            <div class="nav-tabs">
                                <a href="?tab=devices" class="nav-tab">Connected Devices</a>
                                <a href="?tab=groups" class="nav-tab active">User Groups</a>
                                <a href="?action=logout" class="nav-tab" style="background: #dc3545; color: #fff; max-width: 60px;" title="Logout">🚪</a>
                            </div>
                            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                                <a href="?tab=groups" style="flex: 1; text-align: center; background: #ced4da; color: #495057; padding: 12px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 15px; border: 1px solid #adb5bd;">Groups</a>
                                <a href="?tab=groups&action=generate_form&group_id={selected_group_id}&group_name={selected_group_name}" style="width: 45px; text-align: center; background: #198754; color: #ffffff; padding: 12px; border-radius: 12px; text-decoration: none; font-weight: 800; font-size: 20px; box-shadow: 0 4px 8px rgba(25,135,84,0.3);">+</a>
                                <button onclick='startPrinting("{selected_group_name}", {codes_json})' style="width: 45px; background: #0dcaf0; color: #ffffff; border: none; padding: 10px; border-radius: 12px; font-size: 18px; cursor: pointer; box-shadow: 0 4px 8px rgba(13,202,240,0.3);" title="Print">🖨️</button>
                            </div>
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
                    
                    if acc_res_json.get("code") == 0:
                        acc_list = acc_res_json.get("list", [])
                        total_vouchers = len(acc_list)
                        for acc in acc_list:
                            status = str(acc.get("status", "1"))
                            if status == "2":
                                used_vouchers += 1
                            elif status == "3":
                                expired_vouchers += 1
                    
                    if total_vouchers == 0:
                        v_url = f"{BASE_URL}/service/api/open/auth/voucher/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                        v_res = requests.get(v_url, headers=headers, timeout=5)
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
                            <a href="?action=logout" class="nav-tab" style="background: #dc3545; color: #fff; max-width: 60px;" title="Logout">🚪</a>
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
                client_res = requests.get(client_url, headers=headers, timeout=5)
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
                        <a href="?action=logout" class="nav-tab" style="background: #dc3545; color: #fff; max-width: 60px;" title="Logout">🚪</a>
                    </div>
                    <div class="blue-box">Total Connected: {total_count} Devices</div>
                </div>
                <div class="scrollable-list">
                    {items_html if items_html else '<p style="text-align:center; color:#495057;">No connected devices found.</p>'}
                </div>
                """

            html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <title>Network Management Dashboard</title>
                <style>
                    html, body { height: 100%; margin: 0; padding: 0; overflow: hidden; background: #f8f9fa; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #212529; position: fixed; width: 100%; top: 0; left: 0; touch-action: none; }
                    .container { max-width: 500px; height: 100%; margin: 0 auto; background: #e9ecef; padding: 24px 14px 14px 14px; box-sizing: border-box; display: flex; flex-direction: column; border-left: 2px solid #dee2e6; border-right: 2px solid #dee2e6; touch-action: pan-y; }
                    .sticky-header { flex-shrink: 0; background: #e9ecef; padding-bottom: 6px; z-index: 10; }
                    .nav-tabs { display: flex; gap: 8px; margin-bottom: 10px; }
                    .nav-tab { flex: 1; text-align: center; padding: 14px; background: #ced4da; color: #495057; text-decoration: none; border-radius: 12px; font-weight: 700; font-size: 15px; transition: all 0.2s; border: 1px solid #adb5bd; }
                    .nav-tab.active { background: #0d6efd; color: #ffffff; box-shadow: 0 4px 8px rgba(13,110,253,0.3); border-color: #0b5ed7; }
                    .blue-box { background: #0d6efd; color: #ffffff; padding: 16px; border-radius: 14px; text-align: center; font-size: 17px; font-weight: 700; box-shadow: 0 4px 10px rgba(13,110,253,0.3); margin-bottom: 8px; border: 2px solid #084298; }
                    .blue-card { background: #f8f9fa; padding: 14px 18px; margin-bottom: 10px; border-radius: 12px; border: 2px solid #ced4da; box-shadow: 0 2px 4px rgba(0,0,0,0.04); display: flex; align-items: center; gap: 12px; }
                    .footer-summary { display: flex; gap: 6px; }
                    .summary-card { flex: 1; background: #f8f9fa; border: 2px solid #ced4da; padding: 10px 6px; border-radius: 10px; text-align: center; font-size: 12px; font-weight: 600; color: #212529; box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
                    .summary-card b { display: block; color: #0d6efd; font-size: 14px; margin-top: 2px; }
                    .scrollable-list { flex-grow: 1; overflow-y: auto; padding-right: 4px; margin-top: 6px; -webkit-overflow-scrolling: touch; min-height: 0; touch-action: pan-y; }
                    .scrollable-list::-webkit-scrollbar { width: 5px; }
                    .scrollable-list::-webkit-scrollbar-thumb { background: #adb5bd; border-radius: 10px; }
                    
                    #loading-overlay {
                        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background: rgba(233, 236, 239, 0.85); display: none;
                        justify-content: center; align-items: center; z-index: 9999;
                    }
                    .spinner {
                        width: 45px; height: 45px; border: 5px solid #ced4da;
                        border-top: 5px solid #0d6efd; border-radius: 50%;
                        animation: spin 0.7s linear infinite;
                    }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div id="loading-overlay">
                    <div class="spinner"></div>
                </div>
                <div class="container">
                    """ + content_html + """
                </div>
                <script>
                    document.addEventListener("click", function(e) {
                        let target = e.target.closest("a");
                        if (target && target.getAttribute("href")) {
                            let href = target.getAttribute("href");
                            if (href.startsWith("?") || href.startsWith("/")) {
                                document.getElementById("loading-overlay").style.display = "flex";
                            }
                        }
                    });

                    let globalBluetoothDevice = null;
                    let globalCharacteristic = null;

                    async function startPrinting(groupName, codes) {
                        try {
                            if (!globalBluetoothDevice || !globalBluetoothDevice.gatt.connected || !globalCharacteristic) {
                                globalBluetoothDevice = await navigator.bluetooth.requestDevice({
                                    acceptAllDevices: true,
                                    optionalServices: [ '000018f0-0000-1000-8000-00805f9b34fb' ]
                                });
                                const server = await globalBluetoothDevice.gatt.connect();
                                const service = await server.getPrimaryService('000018f0-0000-1000-8000-00805f9b34fb');
                                globalCharacteristic = await service.getCharacteristic('00002af1-0000-1000-8000-00805f9b34fb');
                            }

                            let countStr = prompt("ဘောက်ချာ ဘယ်နှစ်စောင် ထုတ်မလဲ?", "1");
                            if (!countStr) return;
                            let count = parseInt(countStr);
                            if (isNaN(count) || count <= 0) return;

                            let encoder = new TextEncoder();
                            let printData = "\\x1B\\x40\\x1B\\x61\\x01\\n"; // Initialize and Center align
                            
                            for (let i = 0; i < count && i < codes.length; i++) {
                                // Normal size for Wifi-Cafe and Group name
                                printData += "\\x1D\\x21\\x00"; 
                                printData += "Wifi-Cafe\\n";
                                printData += "- " + groupName + " -\\n";
                                
                                // Double width & height for large clear voucher code numbers
                                printData += "\\x1D\\x21\\x11"; 
                                printData += codes[i] + "\\n";
                                
                                // Reset to normal size for spacing
                                printData += "\\x1D\\x21\\x00\\n\\n\\n";
                            }

                            await globalCharacteristic.writeValue(encoder.encode(printData));
                            alert("ပရင်တာသို့ အောင်မြင်စွာ ပေးပို့ပြီးပါပြီ!");
                        } catch (error) {
                            globalBluetoothDevice = null;
                            globalCharacteristic = null;
                            alert("Printer Error: " + error);
                        }
                    }
                </script>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"<h3>System Error: {str(e)}</h3>".encode('utf-8'))
        
        return
