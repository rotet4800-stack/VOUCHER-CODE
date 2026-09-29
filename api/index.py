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
        current_tab = query_params.get('tab', ['home'])[0]
        selected_group_id = query_params.get('group_id', [None])[0]
        selected_group_name = query_params.get('group_name', ['Group'])[0]
        action = query_params.get('action', [None])[0]
        filter_status = query_params.get('filter', ['unused'])[0]
        delete_codes = query_params.get('delete_codes', [None])[0]

        APP_ID = "openc3be644fb5dc"
        SECRET = "0dea886911864f359497a65f94164518"
        BASE_URL = "https://cloud-as.ruijienetworks.com"
        GROUP_ID = "7833000"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        def safe_request(method, url, **kwargs):
            kwargs.setdefault('timeout', 3)
            for attempt in range(2):
                try:
                    if method == 'post':
                        return requests.post(url, **kwargs)
                    else:
                        return requests.get(url, **kwargs)
                except requests.exceptions.RequestException:
                    if attempt == 1:
                        raise
        
        try:
            token_url = f"{BASE_URL}/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
            token_payload = json.dumps({"appid": APP_ID, "secret": SECRET})
            token_res = safe_request('post', token_url, headers=headers, data=token_payload)
            token_data = token_res.json()
            
            if token_res.status_code != 200 or token_data.get("code") != 0:
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write("<h3>Failed to fetch token</h3>".encode('utf-8'))
                return

            access_token = token_data.get("accessToken")

            if action == 'delete_vouchers' and delete_codes and selected_group_id:
                codes_to_delete = delete_codes.split(',')
                del_url = f"{BASE_URL}/service/api/open/auth/voucher/delete/{selected_group_id}?access_token={access_token}"
                
                for code in codes_to_delete:
                    if code.strip():
                        del_payload = json.dumps({"voucherCode": code.strip(), "account": code.strip()})
                        safe_request('post', del_url, headers=headers, data=del_payload)
                
                self.send_response(303)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Location', f'/?tab=groups&group_id={selected_group_id}&group_name={selected_group_name}&filter={filter_status}')
                self.end_headers()
                return

            if action == 'generate_now' and selected_group_id:
                quantity = int(query_params.get('quantity', [1])[0])
                
                ug_url = f"{BASE_URL}/service/api/intl/usergroup/list/{GROUP_ID}?pageIndex=0&pageSize=50&access_token={access_token}"
                ug_res = safe_request('get', ug_url, headers=headers)
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
                safe_request('post', create_url, headers=headers, data=create_payload)
                
                self.send_response(303)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Location', f'/?tab=groups&group_id={selected_group_id}&group_name={selected_group_name}&filter={filter_status}')
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            content_html = ""
            
            if current_tab == 'home':
                content_html = """
                <div class="home-container">
                    <div class="menu-list">
                        <a href="?tab=groups" class="menu-row">
                            <div class="row-icon blue">💳</div>
                            <div class="row-info">
                                <div class="row-title">Voucher Manager</div>
                                <div class="row-desc">Voucher Code များ Print ထုတ်ရန်</div>
                            </div>
                        </a>
                        <a href="?tab=devices" class="menu-row">
                            <div class="row-icon blue">💻</div>
                            <div class="row-info">
                                <div class="row-title">Connected Devices</div>
                                <div class="row-desc">ချိတ်ထားသော ဖုန်းများကြည့်ရန်</div>
                            </div>
                        </a>
                        <a href="?tab=print_settings" class="menu-row">
                            <div class="row-icon blue">⚙️</div>
                            <div class="row-info">
                                <div class="row-title">Print Setting</div>
                                <div class="row-desc">Wifi Name နှင့် Voucher Style ရွေးရန်</div>
                            </div>
                        </a>
                    </div>
                </div>
                """
            elif current_tab == 'print_settings':
                content_html = """
                <div class="sticky-header">
                    <div class="blue-box" style="border: 2px solid #198754;">Print Setting</div>
                </div>
                <div class="fixed-setting-container">
                    <div style="background: #1f1f1f; padding: 16px; border-radius: 14px; border: 1px solid #198754; box-shadow: 0 4px 8px rgba(0,0,0,0.2); height: 100%; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div style="margin-bottom: 12px;">
                                <label style="display: block; font-weight: 700; margin-bottom: 4px; color: #ffffff; font-size: 14px;">Wifi Name :</label>
                                <input type="text" id="settingWifiName" value="WIFI-Cafe" style="width: 100%; padding: 10px; border: 1px solid #198754; background: #121212; color: #fff; border-radius: 8px; font-size: 15px; box-sizing: border-box;">
                            </div>

                            <div style="margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px;">
                                <div>
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: #fff; font-size: 14px; margin-bottom: 3px;">
                                        <input type="radio" name="voucherStyle" value="style1" checked style="accent-color: #198754; width: 16px; height: 16px;"> Style 1
                                    </label>
                                    <div style="background: #ffffff; color: #000; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 11px; text-align: center; margin-left: 24px;">
                                        <div>TwoHours: 4 i 7 n i 7</div>
                                    </div>
                                </div>

                                <div>
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: #fff; font-size: 14px; margin-bottom: 3px;">
                                        <input type="radio" name="voucherStyle" value="style2" style="accent-color: #198754; width: 16px; height: 16px;"> Style 2
                                    </label>
                                    <div style="background: #ffffff; color: #000; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 11px; margin-left: 24px; line-height: 1.2;">
                                        <div>WIFI-Cafe</div>
                                        <div>profile : onehour</div>
                                        <div>voucher : ae1xjz</div>
                                    </div>
                                </div>

                                <div>
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: #fff; font-size: 14px; margin-bottom: 3px;">
                                        <input type="radio" name="voucherStyle" value="style3" style="accent-color: #198754; width: 16px; height: 16px;"> Style 3
                                    </label>
                                    <div style="background: #ffffff; color: #000; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 11px; text-align: center; margin-left: 24px; line-height: 1.2;">
                                        <div>Ruijie</div>
                                        <div>- 30minute -</div>
                                        <div style="font-weight: bold;">017866</div>
                                    </div>
                                </div>

                                <div>
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: #fff; font-size: 14px; margin-bottom: 3px;">
                                        <input type="radio" name="voucherStyle" value="style4" style="accent-color: #198754; width: 16px; height: 16px;"> Style 4
                                    </label>
                                    <div style="background: #ffffff; color: #000; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 11px; margin-left: 24px; line-height: 1.2;">
                                        <div>WIFI-Cafe</div>
                                        <div>profile : 100MB</div>
                                        <div>data : 100 MB</div>
                                        <div style="font-weight: bold;">voucher : 117317</div>
                                    </div>
                                </div>

                                <div>
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; color: #fff; font-size: 14px; margin-bottom: 3px;">
                                        <input type="radio" name="voucherStyle" value="style1_plus" style="accent-color: #198754; width: 16px; height: 16px;"> Style 1 Plus
                                    </label>
                                    <div style="background: #ffffff; color: #000; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 11px; text-align: center; margin-left: 24px; line-height: 1.2;">
                                        <div>=== WIFI-Cafe ===</div>
                                        <div>Group: admin</div>
                                        <div style="font-weight: bold;">wzbqk6</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <button onclick="savePrintSettings()" style="width: 100%; background: #0d6efd; color: #ffffff; border: none; padding: 12px; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 8px rgba(13,110,253,0.3);">Save Setting</button>
                    </div>
                </div>
                <script>
                    window.addEventListener('DOMContentLoaded', () => {
                        let savedName = localStorage.getItem('print_wifi_name');
                        if (savedName) {
                            document.getElementById('settingWifiName').value = savedName;
                        }
                        let savedStyle = localStorage.getItem('print_voucher_style');
                        if (savedStyle) {
                            let radio = document.querySelector(`input[name="voucherStyle"][value="${savedStyle}"]`);
                            if (radio) radio.checked = true;
                        }
                    });

                    function savePrintSettings() {
                        let wName = document.getElementById('settingWifiName').value;
                        let selectedStyle = document.querySelector('input[name="voucherStyle"]:checked').value;
                        localStorage.setItem('print_wifi_name', wName);
                        localStorage.setItem('print_voucher_style', selectedStyle);
                        alert("Settings Saved Successfully!");
                        window.location.href = "/";
                    }
                </script>
                """
            elif current_tab == 'groups':
                def fetch_groups():
                    url = f"{BASE_URL}/service/api/intl/usergroup/list/{GROUP_ID}?pageIndex=0&pageSize=50&access_token={access_token}"
                    res = safe_request('get', url, headers=headers)
                    return res.json()

                def fetch_accounts():
                    url = f"{BASE_URL}/service/api/open/auth/account/getList/{GROUP_ID}?access_token={access_token}&start=0&pageSize=200"
                    res = safe_request('get', url, headers=headers)
                    return res.json()

                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_ug = executor.submit(fetch_groups)
                    future_acc = executor.submit(fetch_accounts)
                    
                    ug_data = future_ug.result()
                    acc_res_json = future_acc.result()

                total_groups = ug_data.get("count", 0)
                group_list = ug_data.get("data", [])
                
                if selected_group_id:
                    if action == 'generate_form':
                        content_html = f"""
                        <div class="sticky-header">
                            <div class="blue-box" style="font-size: 15px; margin-bottom: 4px; border: 2px solid #198754;">{selected_group_name}</div>
                            <div style="text-align: center; color: #38bdf8; font-weight: 700; font-size: 16px; margin-bottom: 12px;">Generate Voucher Code</div>
                        </div>
                        <div class="scrollable-list">
                            <div style="background: #1f1f1f; padding: 20px; border-radius: 14px; border: 1px solid #198754; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                                <form action="" method="GET">
                                    <input type="hidden" name="tab" value="groups">
                                    <input type="hidden" name="group_id" value="{selected_group_id}">
                                    <input type="hidden" name="group_name" value="{selected_group_name}">
                                    <input type="hidden" name="action" value="generate_now">
                                    
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; font-weight: 700; margin-bottom: 6px; color: #ffffff;">အရေအတွက် (Quantity)</label>
                                        <input type="number" name="quantity" value="1" min="1" max="500" style="width: 100%; padding: 12px; border: 1px solid #198754; background: #121212; color: #fff; border-radius: 10px; font-size: 16px; box-sizing: border-box;">
                                    </div>
                                    <div style="margin-bottom: 16px;">
                                        <label style="display: block; font-weight: 700; margin-bottom: 6px; color: #ffffff;">Type</label>
                                        <select style="width: 100%; padding: 12px; border: 1px solid #198754; background: #121212; color: #fff; border-radius: 10px; font-size: 16px; box-sizing: border-box;">
                                            <option>a-z 0-9</option>
                                        </select>
                                    </div>
                                    <div style="margin-bottom: 20px;">
                                        <label style="display: block; font-weight: 700; margin-bottom: 6px; color: #ffffff;">Voucher Length</label>
                                        <select style="width: 100%; padding: 12px; border: 1px solid #198754; background: #121212; color: #fff; border-radius: 10px; font-size: 16px; box-sizing: border-box;">
                                            <option>6</option>
                                        </select>
                                    </div>
                                    <button type="submit" style="width: 100%; background: #0d6efd; color: #ffffff; border: none; padding: 14px; border-radius: 12px; font-size: 17px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 8px rgba(13,110,253,0.3);">Generate</button>
                                </form>
                            </div>
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
                            v_res = safe_request('get', v_url, headers=headers)
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
                        
                        filtered_v_list = []
                        if filter_status == 'unused':
                            filtered_v_list = [v for v in v_list if str(v.get("status", "1")) == "1"]
                        elif filter_status == 'inuse':
                            filtered_v_list = [v for v in v_list if str(v.get("status", "1")) == "2"]
                        elif filter_status == 'expired':
                            filtered_v_list = [v for v in v_list if str(v.get("status", "1")) == "3"]
                        else:
                            filtered_v_list = [v for v in v_list if str(v.get("status", "1")) == "1"]

                        current_filter_label = "မသုံးရသေးသောကဒ်များ"
                        if filter_status == 'inuse':
                            current_filter_label = "သုံးနေသောကဒ်များ"
                        elif filter_status == 'expired':
                            current_filter_label = "သုံးပြီးသွားသောကဒ်များ"

                        vouchers_html = ""
                        for v_idx, v in enumerate(filtered_v_list, 1):
                            code_no = v.get("codeNo") or "N/A"
                            
                            # နံပါတ်စဉ်များနှင့် Code စာသားများ လုံးဝမပါဘဲ သန့်ရှင်းသော ကတ်ပြားဒီဇိုင်း
                            vouchers_html += f"""
                            <div onclick="toggleCardSelect(this, '{code_no}')" style="background: #3b5bdb; padding: 14px 18px; margin-bottom: 10px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 3px 6px rgba(0,0,0,0.3); cursor: pointer; transition: background 0.2s;">
                                <div style="display: flex; align-items: center; gap: 14px;">
                                    <input type="checkbox" class="voucher-checkbox" value="{code_no}" onclick="event.stopPropagation(); updateDeleteButton();" style="width: 20px; height: 20px; accent-color: #dc3545; cursor: pointer;">
                                    <div>
                                        <div style="font-size: 18px; font-weight: 800; color: #ffffff; font-family: monospace; letter-spacing: 1px;">{code_no}</div>
                                        <div style="font-size: 12px; color: #cbd5e1; margin-top: 2px;">{selected_group_name}</div>
                                    </div>
                                </div>
                            </div>
                            """
                        
                        codes_json = json.dumps([v.get('codeNo') for v in v_list])
                        
                        content_html = f"""
                        <div class="sticky-header">
                            <div style="background: #ffffff; color: #000000; padding: 12px 16px; border-radius: 12px; font-size: 15px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.3); margin-bottom: 8px; position: relative;" onclick="toggleDropdown(event)">
                                <span>{current_filter_label}</span>
                                <span style="font-size: 12px; color: #000000;">▼</span>
                                <div id="filterDropdown" style="display: none; position: absolute; top: 50px; left: 0; background: #1f1f1f; border: 1px solid #198754; border-radius: 12px; width: 100%; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.4); overflow: hidden; box-sizing: border-box;">
                                    <a href="?tab=groups&group_id={selected_group_id}&group_name={selected_group_name}&filter=unused" style="display: block; padding: 12px 16px; color: #ffffff; text-decoration: none; font-size: 14px; border-bottom: 1px solid #333333;">မသုံးရသေးသောကဒ်များ</a>
                                    <a href="?tab=groups&group_id={selected_group_id}&group_name={selected_group_name}&filter=inuse" style="display: block; padding: 12px 16px; color: #ffffff; text-decoration: none; font-size: 14px; border-bottom: 1px solid #333333;">သုံးနေသောကဒ်များ</a>
                                    <a href="?tab=groups&group_id={selected_group_id}&group_name={selected_group_name}&filter=expired" style="display: block; padding: 12px 16px; color: #ffffff; text-decoration: none; font-size: 14px;">သုံးပြီးသွားသောကဒ်များ</a>
                                </div>
                            </div>
                            
                            <div class="blue-box" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; background: #0d6efd; border-radius: 12px;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <a href="?tab=groups&action=generate_form&group_id={selected_group_id}&group_name={selected_group_name}" style="background: #198754; color: #ffffff; width: 34px; height: 34px; border-radius: 50%; display: flex; justify-content: center; align-items: center; text-decoration: none; font-weight: 800; font-size: 18px;">+</a>
                                    <span style="font-size: 14px; font-weight: 700; color: #ffffff;">Total Unused: {len(v_list)}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <button id="deleteBtn" onclick="executeDelete('{selected_group_id}', '{selected_group_name}', '{filter_status}')" style="display: none; background: #dc3545; color: #fff; border: none; padding: 8px 14px; border-radius: 8px; font-size: 13px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">DELETE (0)</button>
                                    
                                    <a href="?tab=groups" style="background: #ffffff; color: #000; padding: 8px 10px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: bold;">≡</a>
                                    <button onclick='startPrinting("{selected_group_name}", {codes_json})' style="background: #0dcaf0; color: #ffffff; border: none; width: 34px; height: 34px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 16px; cursor: pointer;" title="Print">🖨️</button>
                                </div>
                            </div>
                        </div>
                        <div class="scrollable-list">
                            {vouchers_html if vouchers_html else '<p style="text-align:center; color:#adb5bd; margin-top:20px;">No vouchers found.</p>'}
                        </div>
                        <script>
                            function toggleDropdown(event) {{
                                event.stopPropagation();
                                let drop = document.getElementById('filterDropdown');
                                drop.style.display = drop.style.display === 'block' ? 'none' : 'block';
                            }}
                            window.addEventListener('click', () => {{
                                let drop = document.getElementById('filterDropdown');
                                if (drop) drop.style.display = 'none';
                            }});

                            function toggleCardSelect(cardDiv, codeNo) {{
                                let checkbox = cardDiv.querySelector('.voucher-checkbox');
                                checkbox.checked = !checkbox.checked;
                                updateDeleteButton();
                            }}

                            function updateDeleteButton() {{
                                let checkboxes = document.querySelectorAll('.voucher-checkbox:checked');
                                let deleteBtn = document.getElementById('deleteBtn');
                                if (checkboxes.length > 0) {{
                                    deleteBtn.style.display = 'block';
                                    deleteBtn.innerText = "DELETE (" + checkboxes.length + ")";
                                }} else {{
                                    deleteBtn.style.display = 'none';
                                }}
                            }}

                            function executeDelete(groupId, groupName, filterStatus) {{
                                let checkboxes = document.querySelectorAll('.voucher-checkbox:checked');
                                let codes = Array.from(checkboxes).map(cb => cb.value);
                                if (codes.length === 0) return;

                                if (confirm("ရွေးချယ်ထားသော ကုဒ် " + codes.length + " ခုကို Ruijie ဆာဗာမှ အမှန်တကယ် ဖျက်မှာလား?")) {{
                                    window.location.href = `/?tab=groups&group_id=${groupId}&group_name=${groupName}&action=delete_vouchers&delete_codes=${codes.join(',')}&filter=${filterStatus}`;
                                }}
                            }}
                        </script>
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
                        v_res = safe_request('get', v_url, headers=headers)
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
                            <div class="blue-card" style="background: #3b5bdb; border: none;">
                                <span style="color: #38bdf8; font-weight: 800; font-size: 15px;">{index}.</span> 
                                <span style="font-size: 15px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px;">{name}</span>
                            </div>
                        </a>
                        """
                    
                    content_html = f"""
                    <div class="sticky-header">
                        <div class="footer-summary">
                            <div class="summary-card" style="background: #3b5bdb; border: none;">Total: <b>{total_vouchers}</b></div>
                            <div class="summary-card" style="background: #3b5bdb; border: none;">In-Use: <b>{used_vouchers}</b></div>
                            <div class="summary-card" style="background: #3b5bdb; border: none;">Expired: <b>{expired_vouchers}</b></div>
                        </div>
                    </div>
                    <div class="scrollable-list">
                        {items_html if items_html else '<p style="text-align:center; color:#adb5bd;">No groups found.</p>'}
                    </div>
                    """
            elif current_tab == 'devices':
                client_url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user?group_id={GROUP_ID}&page_index=1&page_size=100&access_token={access_token}"
                client_res = safe_request('get', client_url, headers=headers)
                client_data = client_res.json()
                
                total_count = client_data.get("totalCount", 0)
                raw_list = client_data.get("list", [])
                
                items_html = ""
                for index, client in enumerate(raw_list, 1):
                    brand = client.get("manufacturer") or "Unknown"
                    model = client.get("staModel") or client.get("userName") or "Mobile Device"
                    band = client.get("band") or "-"
                    
                    items_html += f"""
                    <div style="background: #1f1f1f; padding: 14px 18px; margin-bottom: 10px; border-radius: 12px; border: 1px solid #198754; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                        <div>
                            <div style="font-size: 14px; font-weight: 700; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #38bdf8; font-weight: 800;">{index}.</span> 
                                <span style="text-transform: uppercase; letter-spacing: 0.5px;">{brand}</span>
                            </div>
                            <div style="font-size: 12px; color: #adb5bd; margin-top: 2px; padding-left: 20px;">
                                Model: <b style="color: #ffffff;">{model}</b>
                            </div>
                        </div>
                        <div style="background: #1e294b; color: #38bdf8; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; border: 1px solid #334155;">
                            {band}
                        </div>
                    </div>
                    """
                
                content_html = f"""
                <div class="sticky-header">
                    <div class="blue-box" style="border: 2px solid #198754;">Total Connected: {total_count} Devices</div>
                </div>
                <div class="scrollable-list">
                    {items_html if items_html else '<p style="text-align:center; color:#adb5bd;">No connected devices found.</p>'}
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <title>Voucher Manager</title>
                <style>
                    html, body {{ height: 100%; margin: 0; padding: 0; overflow: hidden; background: #121212; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #ffffff; position: fixed; width: 100%; top: 0; left: 0; }}
                    .container {{ max-width: 500px; height: 100%; margin: 0 auto; background: #121212; padding: 0; box-sizing: border-box; display: flex; flex-direction: column; }}
                    
                    /* Home Theme */
                    .home-container {{ display: flex; flex-direction: column; height: 100%; background: #121212; justify-content: flex-start; padding: 16px; }}
                    .menu-list {{ display: flex; flex-direction: column; gap: 12px; width: 100%; }}
                    .menu-row {{ display: flex; align-items: center; gap: 16px; padding: 16px; background: #1f1f1f; border-radius: 14px; border: 1px solid #198754; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
                    .row-icon {{ width: 44px; height: 44px; border-radius: 12px; display: flex; justify-content: center; align-items: center; font-size: 20px; flex-shrink: 0; }}
                    .row-icon.blue {{ background: #0d6efd; color: #ffffff; }}
                    .row-info {{ display: flex; flex-direction: column; }}
                    .row-title {{ font-size: 16px; font-weight: 700; color: #ffffff; margin-bottom: 2px; }}
                    .row-desc {{ font-size: 13px; color: #adb5bd; }}

                    /* Sub Dashboard Styles */
                    .sticky-header {{ flex-shrink: 0; background: #121212; padding: 14px 14px 6px 14px; z-index: 10; }}
                    .blue-box {{ background: #0d6efd; color: #ffffff; padding: 14px 16px; border-radius: 14px; font-size: 16px; font-weight: 700; }}
                    .blue-card {{ background: #3b5bdb; padding: 14px 18px; margin-bottom: 10px; border-radius: 12px; display: flex; align-items: center; gap: 12px; }}
                    .footer-summary {{ display: flex; gap: 6px; }}
                    .summary-card {{ flex: 1; background: #3b5bdb; padding: 10px 6px; border-radius: 10px; text-align: center; font-size: 12px; font-weight: 600; color: #ffffff; }}
                    .summary-card b {{ display: block; color: #38bdf8; font-size: 14px; margin-top: 2px; }}
                    .scrollable-list {{ flex-grow: 1; overflow-y: auto; padding: 0 14px 14px 14px; margin-top: 6px; -webkit-overflow-scrolling: touch; min-height: 0; background: #121212; }}
                    .scrollable-list::-webkit-scrollbar {{ width: 5px; }}
                    .scrollable-list::-webkit-scrollbar-thumb {{ background: #333333; border-radius: 10px; }}
                    
                    /* Fixed Print Setting Container */
                    .fixed-setting-container {{ flex-grow: 1; overflow: hidden; padding: 0 14px 14px 14px; margin-top: 6px; background: #121212; display: flex; flex-direction: column; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {content_html}
                </div>
                <script>
                    if (window.performance && window.performance.navigation.type === window.performance.navigation.TYPE_RELOAD) {{
                        window.location.replace("/");
                    }}

                    let globalBluetoothDevice = null;
                    let globalCharacteristic = null;

                    async function startPrinting(groupName, codes) {{
                        try {{
                            if (!navigator.bluetooth || typeof navigator.bluetooth.requestDevice !== 'function') {{
                                alert("ဒီဘရောက်ဇာ (သို့မဟုတ်) ဖုန်းတွင် Bluetooth (Web Bluetooth API) ကို မပံ့ပိုးပါ။ ကျေးဇူးပြု၍ Google Chrome ဘရောက်ဇာကို အသုံးပြုပေးပါ။");
                                return;
                            }}

                            if (!globalBluetoothDevice || !globalBluetoothDevice.gatt.connected || !globalCharacteristic) {{
                                globalBluetoothDevice = await navigator.bluetooth.requestDevice({{
                                    acceptAllDevices: true,
                                    optionalServices: [ '000018f0-0000-1000-8000-00805f9b34fb' ]
                                }});
                                const server = await globalBluetoothDevice.gatt.connect();
                                const service = await server.getPrimaryService('000018f0-0000-1000-8000-00805f9b34fb');
                                globalCharacteristic = await service.getCharacteristic('00002af1-0000-1000-8000-00805f9b34fb');
                            }}

                            let countStr = prompt("ဘောက်ချာ ဘယ်နှစ်စောင် ထုတ်မလဲ?", "1");
                            if (!countStr) return;
                            let count = parseInt(countStr);
                            if (isNaN(count) || count <= 0) return;

                            let customWifiName = localStorage.getItem('print_wifi_name') || 'WIFI-Cafe';
                            let voucherStyle = localStorage.getItem('print_voucher_style') || 'style1';

                            let encoder = new TextEncoder();
                            let printChunks = [];
                            
                            printChunks.push("\\x1B\\x40\\x1B\\x61\\x01");
                            
                            for (let i = 0; i < count && i < codes.length; i++) {{
                                let spacedCode = codes[i].split('').join(' ');
                                
                                let voucherText = "";
                                if (voucherStyle === 'style1') {{
                                    voucherText += customWifiName + "\\n";
                                    voucherText += "- " + groupName + " -\\n";
                                    voucherText += "\\x1D\\x21\\x01" + spacedCode + "\\x1D\\x21\\x00\\n";
                                }} else if (voucherStyle === 'style2') {{
                                    voucherText += customWifiName + "\\n";
                                    voucherText += "profile : " + groupName + "\\n";
                                    voucherText += "voucher :\\n";
                                    voucherText += "\\x1D\\x21\\x01" + spacedCode + "\\x1D\\x21\\x00\\n";
                                }} else if (voucherStyle === 'style3') {{
                                    voucherText += customWifiName + "\\n";
                                    voucherText += "- " + groupName + " -\\n";
                                    voucherText += "\\x1D\\x21\\x01" + spacedCode + "\\x1D\\x21\\x00\\n";
                                }} else if (voucherStyle === 'style4') {{
                                    voucherText += customWifiName + "\\n";
                                    voucherText += "profile : " + groupName + "\\n";
                                    voucherText += "data : 100 MB\\n";
                                    voucherText += "voucher :\\n";
                                    voucherText += "\\x1D\\x21\\x01" + spacedCode + "\\x1D\\x21\\x00\\n";
                                }} else if (voucherStyle === 'style1_plus') {{
                                    voucherText += "=== " + customWifiName + " ===\\n";
                                    voucherText += "Group: " + groupName + "\\n";
                                    voucherText += "\\x1D\\x21\\x01" + spacedCode + "\\x1D\\x21\\x00\\n";
                                }}
                                
                                voucherText += "--------------------------------\\n";
                                printChunks.push(voucherText);
                            }}

                            printChunks.push("\\n\\n");

                            let finalPrintString = printChunks.join("");
                            
                            let encodedData = encoder.encode(finalPrintString);
                            let chunkSize = 100;
                            for (let offset = 0; offset < encodedData.length; offset += chunkSize) {{
                                let chunk = encodedData.slice(offset, offset + chunkSize);
                                await globalCharacteristic.writeValue(chunk);
                                await new Promise(resolve => setTimeout(resolve, 35));
                            }}

                            alert("ပရင်တာသို့ အောင်မြင်စွာ ပေးပို့ပြီးပါပြီ!");
                        }} catch (error) {{
                            globalBluetoothDevice = null;
                            globalCharacteristic = null;
                            alert("Printer Error: " + error);
                        }}
                    }}
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
