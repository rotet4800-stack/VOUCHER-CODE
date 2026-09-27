import os
import json
import html
import secrets
import traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor

import requests


# ============================================================
# Ruijie Cloud Multi-User Voucher Manager
# ============================================================
# IMPORTANT:
# 1. Put your Ruijie API App ID and Secret in environment variables:
# RUIJIE_APP_ID
# RUIJIE_APP_SECRET
#
# 2. DO NOT put the App Secret in browser/JavaScript code.
#
# 3. Users log in with THEIR OWN Ruijie Cloud account.
# The app does not create a separate local account for them.
#
# 4. Each login session uses the access_token + root groupId returned
# by Ruijie Cloud, so the fixed GROUP_ID from the old version is gone.
# ============================================================

BASE_URL = "https://cloud-as.ruijienetworks.com"
APP_ID = os.environ.get("RUIJIE_APP_ID", "")
APP_SECRET = os.environ.get("RUIJIE_APP_SECRET", "")

# Ruijie Cloud application token endpoint used by the existing app.
APP_TOKEN_URL = (
    f"{BASE_URL}/service/api/oauth20/client/access_token"
    "?token=d63dss0a81e4415a889ac5b78fsc904a"
)

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Simple in-memory sessions.
# Good for testing / one Python process.
# For production with multiple workers, use Redis/database sessions.
SESSIONS = {}
SESSION_COOKIE = "ruijie_session"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {}


def request(method, url, **kwargs):
    kwargs.setdefault("timeout", 10)
    if method.lower() == "post":
        return requests.post(url, **kwargs)
    return requests.get(url, **kwargs)


def get_app_token():
    """Validate that the application's appid/secret can obtain an API token."""
    if not APP_ID or not APP_SECRET:
        return None, "RUIJIE_APP_ID / RUIJIE_APP_SECRET မသတ်မှတ်ရသေးပါ။"

    payload = json.dumps({
        "appid": APP_ID,
        "secret": APP_SECRET
    })

    try:
        res = request("post", APP_TOKEN_URL, headers=HEADERS, data=payload)
        data = safe_json(res)

        if res.status_code != 200 or data.get("code") != 0:
            return None, data.get("msg") or f"HTTP {res.status_code}"

        return data.get("accessToken"), None
    except Exception as e:
        return None, str(e)


def ruijie_login(account, password):
    """ Login using the user's own Ruijie Cloud account. Ruijie API reference documents: GET /service/api/login?appid=...&secret=...&account=...&password=... and returns: access_token, groupId, tenantId, account, etc. """
    if not APP_ID or not APP_SECRET:
        return None, "Server မှာ Ruijie APP_ID / APP_SECRET မထည့်ရသေးပါ။"

    url = f"{BASE_URL}/service/api/login"
    params = {
        "appid": APP_ID,
        "secret": APP_SECRET,
        "account": account,
        "password": password,
    }

    try:
        res = request("get", url, headers=HEADERS, params=params)
        data = safe_json(res)

        if res.status_code != 200 or data.get("code") != 0:
            return None, data.get("msg") or "Ruijie Login failed"

        access_token = data.get("access_token") or data.get("accessToken")
        root_group_id = data.get("groupId")
        tenant_id = data.get("tenantId")

        if not access_token:
            return None, "Ruijie က access_token မပြန်ပေးပါ။"

        if not root_group_id:
            return None, "Ruijie က groupId မပြန်ပေးပါ။"

        return {
            "access_token": access_token,
            "group_id": str(root_group_id),
            "tenant_id": str(tenant_id or ""),
            "account": data.get("account") or account,
            "account_id": data.get("accountId"),
        }, None

    except Exception as e:
        return None, f"Ruijie API Error: {e}"


def refresh_user_token(session):
    """Refresh a user's Ruijie access token."""
    old_token = session.get("access_token")
    if not old_token:
        return False

    url = f"{BASE_URL}/service/api/token/refresh"
    params = {
        "appid": APP_ID,
        "secret": APP_SECRET,
        "access_token": old_token,
    }

    try:
        res = request("get", url, headers=HEADERS, params=params)
        data = safe_json(res)
        if res.status_code == 200 and data.get("code") == 0:
            new_token = data.get("accessToken") or data.get("access_token")
            if new_token:
                session["access_token"] = new_token
                return True
    except Exception:
        pass

    return False


def api_call(session, method, url, **kwargs):
    """ Call Ruijie API using the logged-in user's access token. If Ruijie reports an expired token (code 4), refresh once and retry. """
    token = session.get("access_token")
    if not token:
        raise RuntimeError("Login session မရှိပါ။")

    kwargs.setdefault("headers", HEADERS.copy())
    params = dict(kwargs.pop("params", {}) or {})
    params["access_token"] = token
    kwargs["params"] = params

    res = request(method, url, **kwargs)
    data = safe_json(res)

    if data.get("code") == 4:
        if refresh_user_token(session):
            params["access_token"] = session["access_token"]
            res = request(method, url, **kwargs)
            data = safe_json(res)

    return res, data


def extract_list(data):
    """Handle common Ruijie response list shapes."""
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in ("list", "data", "rows", "items"):
        value = data.get(key)
        if isinstance(value, list):
            return value

    # Some endpoints wrap the list again.
    for key in ("data", "voucherData", "result"):
        value = data.get(key)
        if isinstance(value, dict):
            for subkey in ("list", "data", "rows", "items"):
                subvalue = value.get(subkey)
                if isinstance(subvalue, list):
                    return subvalue

    return []


def fetch_network_groups(session):
    """ Get network/project groups belonging to the logged-in Ruijie account. """
    url = f"{BASE_URL}/service/api/maint/network/list"
    res, data = api_call(
        session,
        "get",
        url,
        params={"page": 1, "per_page": 100},
    )

    if res.status_code != 200 or data.get("code") not in (0, None):
        raise RuntimeError(data.get("msg") or "Project/Group list ရယူမရပါ။")

    groups = extract_list(data)

    # Normalize group objects for the UI.
    normalized = []
    for g in groups:
        if not isinstance(g, dict):
            continue

        gid = (
            g.get("groupId")
            or g.get("group_id")
            or g.get("id")
            or g.get("buildingId")
            or g.get("networkId")
        )
        name = (
            g.get("groupName")
            or g.get("group_name")
            or g.get("name")
            or g.get("buildingName")
            or "Unknown Group"
        )

        if gid is not None:
            normalized.append({
                "id": str(gid),
                "name": str(name),
            })

    # Fallback: some API versions expose the root group as data.
    if not normalized:
        root_id = session.get("group_id")
        if root_id:
            normalized.append({
                "id": str(root_id),
                "name": "My Ruijie Network",
            })

    return normalized


def fetch_user_groups(session, group_id):
    url = (
        f"{BASE_URL}/service/api/intl/usergroup/list/{group_id}"
        "?pageIndex=0&pageSize=200"
    )
    res, data = api_call(session, "get", url)

    if res.status_code != 200:
        return []

    return extract_list(data)


def fetch_accounts(session, group_id):
    url = f"{BASE_URL}/service/api/open/auth/account/getList/{group_id}"
    res, data = api_call(
        session,
        "get",
        url,
        params={"start": 0, "pageSize": 200},
    )
    if res.status_code != 200:
        return {}
    return data


def fetch_vouchers(session, group_id):
    url = f"{BASE_URL}/service/api/open/auth/voucher/getList/{group_id}"
    res, data = api_call(
        session,
        "get",
        url,
        params={"start": 0, "pageSize": 500},
    )
    if res.status_code != 200:
        return []
    return extract_list(data)


def create_vouchers(session, group_id, user_group_id, profile_id, quantity):
    url = f"{BASE_URL}/service/api/open/auth/voucher/create/{group_id}"

    payload = {
        "quantity": int(quantity),
        "profile": str(profile_id),
        "userGroupId": int(user_group_id),
        "comment": "Generated by Multi-User Voucher Manager",
    }

    res, data = api_call(
        session,
        "post",
        url,
        data=json.dumps(payload),
    )

    if res.status_code != 200 or data.get("code") not in (0, None):
        raise RuntimeError(data.get("msg") or f"Voucher create failed: HTTP {res.status_code}")

    return data


def fetch_devices(session, group_id):
    url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user"

    res, data = api_call(
        session,
        "get",
        url,
        params={
            "group_id": group_id,
            "page_index": 1,
            "page_size": 100,
        },
    )

    if res.status_code != 200:
        return 0, []

    devices = extract_list(data)
    total = data.get("totalCount") or data.get("count") or len(devices)
    return total, devices


def page_shell(content, title="Ruijie Voucher Manager"):
    return f""" <!DOCTYPE html> <html lang="my"> <head> <meta charset="UTF-8"> <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"> <title>{esc(title)}</title> <style> html,body {{ height:100%; margin:0; padding:0; background:#121212; color:#fff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif; }} * {{ box-sizing:border-box; }} body {{ min-height:100%; }} .container {{ width:100%; max-width:520px; min-height:100vh; margin:auto; background:#121212; padding:16px; }} .card {{ background:#1f1f1f; border:1px solid #198754; border-radius:14px; padding:18px; margin-bottom:12px; }} .input {{ width:100%; padding:14px; border-radius:10px; border:1px solid #444; background:#121212; color:#fff; font-size:16px; outline:none; }} .input:focus {{ border-color:#0d6efd; }} .btn {{ width:100%; border:0; border-radius:11px; padding:14px; font-size:16px; font-weight:700; cursor:pointer; }} .btn-blue {{ background:#0d6efd; color:#fff; }} .btn-green {{ background:#198754; color:#fff; }} .btn-red {{ background:#dc3545; color:#fff; }} .link {{ color:#38bdf8; text-decoration:none; font-weight:700; }} .top {{ display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:12px; }} .title {{ font-size:20px; font-weight:800; }} .small {{ color:#adb5bd; font-size:13px; }} .group {{ display:block; text-decoration:none; color:#fff; background:#1f1f1f; border:1px solid #198754; border-radius:12px; padding:15px; margin-bottom:10px; }} .summary {{ display:flex; gap:7px; margin-bottom:12px; }} .summary > div {{ flex:1; background:#1f1f1f; border:1px solid #198754; border-radius:10px; padding:10px 4px; text-align:center; font-size:12px; }} .summary b {{ display:block; color:#38bdf8; font-size:16px; margin-top:3px; }} .row {{ background:#1f1f1f; border:1px solid #198754; border-radius:11px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; gap:10px; }} .badge {{ padding:4px 9px; border-radius:20px; font-size:11px; font-weight:800; }} .nav {{ display:flex; gap:7px; margin-bottom:12px; }} .nav a {{ flex:1; text-align:center; padding:10px 4px; border-radius:9px; background:#1f1f1f; border:1px solid #333; color:#fff; text-decoration:none; font-size:12px; }} .error {{ background:#3a1717; border:1px solid #dc3545; color:#ffb3b3; padding:12px; border-radius:10px; margin-bottom:12px; }} .notice {{ background:#102c1e; border:1px solid #198754; color:#b9f6cf; padding:12px; border-radius:10px; margin-bottom:12px; }} </style> </head> <body> <div class="container"> {content} </div> </body> </html> """


def login_page(error=""):
    err = f'<div class="error">{esc(error)}</div>' if error else ""
    content = f""" <div style="padding-top:50px;"> <div class="card"> <div class="title" style="text-align:center;margin-bottom:8px;"> Ruijie Cloud </div> <div class="small" style="text-align:center;margin-bottom:22px;"> ကိုယ့် Ruijie/Reyee Account နဲ့ Login ဝင်ပါ </div> {err} <form method="POST" action="/login"> <label class="small">Ruijie Account / Email</label> <input class="input" name="account" type="text" autocomplete="username" required style="margin-top:6px;margin-bottom:14px;"> <label class="small">Password</label> <input class="input" name="password" type="password" autocomplete="current-password" required style="margin-top:6px;margin-bottom:18px;"> <button class="btn btn-blue" type="submit"> Login </button> </form> <div class="small" style="text-align:center;margin-top:16px;"> Password ကို ဒီ App ထဲမှာ database အဖြစ် မသိမ်းထားပါ။ </div> </div> </div> """
    return page_shell(content, "Ruijie Login")


class handler(BaseHTTPRequestHandler):

    def send_html(self, body, status=200, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def get_session(self):
        cookie = self.headers.get("Cookie", "")
        for item in cookie.split(";"):
            item = item.strip()
            if item.startswith(SESSION_COOKIE + "="):
                sid = item.split("=", 1)[1]
                return sid, SESSIONS.get(sid)
        return None, None

    def new_session(self, session_data):
        sid = secrets.token_urlsafe(32)
        SESSIONS[sid] = session_data
        return sid

    def destroy_session(self):
        sid, _ = self.get_session()
        if sid:
            SESSIONS.pop(sid, None)

    def require_session(self):
        sid, session = self.get_session()
        if not session:
            self.send_html(login_page(), 200)
            return None
        return session

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            form = parse_qs(raw)

            if path != "/login":
                self.send_html(login_page("Invalid request."))
                return

            account = form.get("account", [""])[0].strip()
            password = form.get("password", [""])[0]

            if not account or not password:
                self.send_html(login_page("Account နဲ့ Password နှစ်ခုလုံးထည့်ပါ။"))
                return

            session, error = ruijie_login(account, password)

            if error:
                self.send_html(login_page(error))
                return

            sid = self.new_session(session)

            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}={sid}; HttpOnly; SameSite=Lax; Path=/"
            )
            self.end_headers()

        except Exception as e:
            self.send_html(page_shell(
                f'<div class="error">System Error: {esc(e)}</div>'
            ))

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            path = parsed.path

            if path == "/login":
                self.send_html(login_page())
                return

            if path == "/logout":
                self.destroy_session()
                self.send_response(303)
                self.send_header("Location", "/login")
                self.send_header(
                    "Set-Cookie",
                    f"{SESSION_COOKIE}=deleted; Max-Age=0; HttpOnly; SameSite=Lax; Path=/"
                )
                self.end_headers()
                return

            session = self.require_session()
            if not session:
                return

            tab = query.get("tab", ["home"])[0]
            group_id = query.get("group_id", [None])[0]
            group_name = query.get("group_name", ["Group"])[0]
            action = query.get("action", [None])[0]

            # ----------------------------------------------------
            # HOME
            # ----------------------------------------------------
            if tab == "home":
                content = f""" <div class="top"> <div> <div class="title">Ruijie Manager</div> <div class="small">{esc(session.get("account"))}</div> </div> <a class="link" href="/logout">Logout</a> </div> <div class="notice"> Login အောင်မြင်ပါတယ်။ ဒီ Session မှာ <b>မင်းဝင်ထားတဲ့ Ruijie Account</b> ရဲ့ data ကိုပဲ အသုံးပြုပါတယ်။ </div> <div class="card"> <a class="group" href="/?tab=groups"> 💳 &nbsp; <b>Voucher Manager</b><br> <span class="small">Voucher Code များ Generate / Print</span> </a> <a class="group" href="/?tab=devices"> 💻 &nbsp; <b>Connected Devices</b><br> <span class="small">ချိတ်ထားသော Device များကြည့်ရန်</span> </a> </div> """
                self.send_html(page_shell(content))
                return

            # ----------------------------------------------------
            # GROUP / PROJECT LIST
            # ----------------------------------------------------
            if tab == "groups":
                groups = fetch_network_groups(session)

                if group_id:
                    # Security: selected group must belong to this user's
                    # own project list. Do not trust a URL group_id blindly.
                    allowed = next(
                        (g for g in groups if str(g["id"]) == str(group_id)),
                        None
                    )

                    if not allowed:
                        self.send_html(page_shell(
                            '<div class="error">ဒီ Project/Group ကို ဒီ Account က အသုံးပြုခွင့်မရှိပါ။</div>'
                            '<a class="link" href="/?tab=groups">← Back</a>'
                        ))
                        return

                    real_name = allowed["name"]

                    if action == "generate_form":
                        user_groups = fetch_user_groups(session, group_id)

                        options = ""
                        for g in user_groups:
                            gid = g.get("id")
                            name = g.get("userGroupName") or g.get("name") or gid
                            profile = (
                                g.get("authProfileId")
                                or g.get("profileId")
                                or ""
                            )
                            if gid is not None:
                                options += (
                                    f'<option value="{esc(gid)}" '
                                    f'data-profile="{esc(profile)}">'
                                    f'{esc(name)}</option>'
                                )

                        content = f""" <div class="top"> <a class="link" href="/?tab=groups&group_id={esc(group_id)}&group_name={esc(real_name)}">← Back</a> <a class="link" href="/logout">Logout</a> </div> <div class="title" style="margin-bottom:12px;">Generate Voucher</div> <div class="card"> <form method="GET" action="/"> <input type="hidden" name="tab" value="groups"> <input type="hidden" name="group_id" value="{esc(group_id)}"> <input type="hidden" name="group_name" value="{esc(real_name)}"> <input type="hidden" name="action" value="generate_now"> <label class="small">User Group</label> <select class="input" name="user_group_id" style="margin-top:6px;margin-bottom:14px;" required> {options or '<option value="">No user groups found</option>'} </select> <label class="small">Quantity</label> <input class="input" type="number" name="quantity" value="1" min="1" max="500" style="margin-top:6px;margin-bottom:18px;" required> <button class="btn btn-blue" type="submit">Generate</button> </form> </div> """
                        self.send_html(page_shell(content))
                        return

                    if action == "generate_now":
                        try:
                            quantity = int(query.get("quantity", ["1"])[0])
                            user_group_id = query.get("user_group_id", [None])[0]

                            if quantity < 1 or quantity > 500:
                                raise ValueError("Quantity 1 မှ 500 အတွင်း ဖြစ်ရပါမယ်။")
                            if not user_group_id:
                                raise ValueError("User Group မရွေးရသေးပါ။")

                            user_groups = fetch_user_groups(session, group_id)
                            selected = next(
                                (
                                    g for g in user_groups
                                    if str(g.get("id")) == str(user_group_id)
                                ),
                                None
                            )

                            if not selected:
                                raise ValueError("ဒီ User Group ကို ဒီ Account က အသုံးပြုခွင့်မရှိပါ။")

                            profile_id = (
                                selected.get("authProfileId")
                                or selected.get("profileId")
                            )
                            if not profile_id:
                                raise ValueError("ဒီ User Group အတွက် profile ID မတွေ့ပါ။")

                            create_vouchers(
                                session,
                                group_id,
                                user_group_id,
                                profile_id,
                                quantity,
                            )

                            location = (
                                "/?" + urlencode({
                                    "tab": "groups",
                                    "group_id": group_id,
                                    "group_name": real_name,
                                    "generated": quantity,
                                })
                            )
                            self.send_response(303)
                            self.send_header("Location", location)
                            self.end_headers()
                            return

                        except Exception as e:
                            self.send_html(page_shell(
                                f'<div class="error">Voucher Generate Error: {esc(e)}</div>'
                                f'<a class="link" href="/?tab=groups&group_id={esc(group_id)}">← Back</a>'
                            ))
                            return

                    # Group voucher list.
                    with ThreadPoolExecutor(max_workers=2) as ex:
                        f_acc = ex.submit(fetch_accounts, session, group_id)
                        f_v = ex.submit(fetch_vouchers, session, group_id)
                        acc_data = f_acc.result()
                        vouchers = f_v.result()

                    # Prefer voucher endpoint.
                    v_list = []
                    for v in vouchers:
                        if not isinstance(v, dict):
                            continue
                        code = (
                            v.get("codeNo")
                            or v.get("voucherCode")
                            or v.get("username")
                            or v.get("account")
                        )
                        if code:
                            v_list.append({
                                "codeNo": code,
                                "status": str(v.get("status", "1")),
                            })

                    if not v_list:
                        for acc in extract_list(acc_data):
                            if not isinstance(acc, dict):
                                continue
                            code = acc.get("username") or acc.get("account")
                            if code:
                                v_list.append({
                                    "codeNo": code,
                                    "status": str(acc.get("status", "1")),
                                })

                    total = len(v_list)
                    used = sum(1 for x in v_list if x["status"] == "2")
                    expired = sum(1 for x in v_list if x["status"] == "3")

                    rows = ""
                    codes = []

                    for i, v in enumerate(v_list, 1):
                        code = str(v["codeNo"])
                        codes.append(code)
                        status = v["status"]

                        if status == "2":
                            st = "In-Use"
                            color = "#ffc107"
                        elif status == "3":
                            st = "Expired"
                            color = "#dc3545"
                        else:
                            st = "Available"
                            color = "#198754"

                        rows += f""" <div class="row"> <div> <span style="color:#38bdf8;font-weight:800;">{i}.</span> <b style="font-family:monospace;">{esc(code)}</b> </div> <span class="badge" style="background:{color}30;color:{color};"> {st} </span> </div> """

                    generated = query.get("generated", [None])[0]
                    notice = (
                        f'<div class="notice">{esc(generated)} voucher generate လုပ်ပြီးပါပြီ။</div>'
                        if generated else ""
                    )

                    codes_json = json.dumps(codes, ensure_ascii=False)

                    content = f""" <div class="top"> <div> <div class="title">{esc(real_name)}</div> <div class="small">{esc(session.get("account"))}</div> </div> <a class="link" href="/logout">Logout</a> </div> <div class="nav"> <a href="/?tab=groups">Projects</a> <a href="/?tab=devices">Devices</a> <a href="/?tab=home">Home</a> </div> {notice} <div class="summary"> <div>Total<b>{total}</b></div> <div>In-Use<b>{used}</b></div> <div>Expired<b>{expired}</b></div> </div> <div style="display:flex;gap:8px;margin-bottom:12px;"> <a class="btn btn-green" style="text-decoration:none;text-align:center;" href="/?tab=groups&group_id={esc(group_id)}&group_name={esc(real_name)}&action=generate_form"> + Generate </a> <button class="btn btn-blue" style="flex:1;" onclick='startPrinting({json.dumps(real_name)}, {codes_json})'> 🖨 Print </button> </div> {rows or '<div class="small" style="text-align:center;padding:20px;">No vouchers found.</div>'} <script> let bluetoothDevice = null; let characteristic = null; async function startPrinting(groupName, codes) {{ try {{ if (!navigator.bluetooth || typeof navigator.bluetooth.requestDevice !== "function") {{ alert("ဒီ Browser မှာ Web Bluetooth မပံ့ပိုးပါ။ Chrome ကိုအသုံးပြုပါ။"); return; }} if (!bluetoothDevice || !bluetoothDevice.gatt.connected || !characteristic) {{ bluetoothDevice = await navigator.bluetooth.requestDevice({{ acceptAllDevices: true, optionalServices: [ "000018f0-0000-1000-8000-00805f9b34fb" ] }}); const server = await bluetoothDevice.gatt.connect(); const service = await server.getPrimaryService( "000018f0-0000-1000-8000-00805f9b34fb" ); characteristic = await service.getCharacteristic( "00002af1-0000-1000-8000-00805f9b34fb" ); }} let countStr = prompt("ဘောက်ချာ ဘယ်နှစ်စောင် ထုတ်မလဲ?", "1"); if (!countStr) return; let count = parseInt(countStr); if (isNaN(count) || count <= 0) return; let encoder = new TextEncoder(); let printData = "\\x1B\\x40\\x1B\\x61\\x01\\n"; for (let i = 0; i < count && i < codes.length; i++) {{ printData += "\\x1D\\x21\\x00"; printData += "Wifi-Cafe\\n"; printData += "- " + groupName + " -\\n"; printData += "\\x1D\\x21\\x11"; printData += codes[i] + "\\n"; printData += "\\x1D\\x21\\x00\\n\\n\\n"; }} await characteristic.writeValue(encoder.encode(printData)); alert("Printer သို့ အောင်မြင်စွာ ပေးပို့ပြီးပါပြီ။"); }} catch (error) {{ bluetoothDevice = null; characteristic = null; alert("Printer Error: " + error); }} }} </script> """
                    self.send_html(page_shell(content))
                    return

                # Project list
                items = ""
                for i, g in enumerate(groups, 1):
                    items += f""" <a class="group" href="/?tab=groups&group_id={esc(g['id'])}&group_name={esc(g['name'])}"> <span style="color:#38bdf8;font-weight:800;">{i}.</span> <b>{esc(g['name'])}</b> <div class="small">Group ID: {esc(g['id'])}</div> </a> """

                content = f""" <div class="top"> <div> <div class="title">My Projects</div> <div class="small">{esc(session.get("account"))}</div> </div> <a class="link" href="/logout">Logout</a> </div> <div class="notice"> ဒီစာရင်းက Login ဝင်ထားတဲ့ Ruijie Account ရဲ့ Project/Group တွေပါ။ </div> {items or '<div class="card small" style="text-align:center;">Project / Group မတွေ့ပါ။</div>'} """
                self.send_html(page_shell(content))
                return

            # ----------------------------------------------------
            # DEVICES
            # ----------------------------------------------------
            if tab == "devices":
                groups = fetch_network_groups(session)

                if not group_id:
                    items = ""
                    for i, g in enumerate(groups, 1):
                        items += f""" <a class="group" href="/?tab=devices&group_id={esc(g['id'])}&group_name={esc(g['name'])}"> <span style="color:#38bdf8;font-weight:800;">{i}.</span> <b>{esc(g['name'])}</b> </a> """
                    content = f""" <div class="top"> <div> <div class="title">Connected Devices</div> <div class="small">{esc(session.get("account"))}</div> </div> <a class="link" href="/logout">Logout</a> </div> {items or '<div class="card small">Project မတွေ့ပါ။</div>'} """
                    self.send_html(page_shell(content))
                    return

                allowed = next(
                    (g for g in groups if str(g["id"]) == str(group_id)),
                    None
                )

                if not allowed:
                    self.send_html(page_shell(
                        '<div class="error">ဒီ Project ကို အသုံးပြုခွင့်မရှိပါ။</div>'
                    ))
                    return

                total, devices = fetch_devices(session, group_id)
                rows = ""

                for i, device in enumerate(devices, 1):
                    brand = (
                        device.get("manufacturer")
                        or device.get("manufacture")
                        or "Unknown"
                    )
                    model = (
                        device.get("staModel")
                        or device.get("userName")
                        or device.get("name")
                        or "Mobile Device"
                    )
                    band = device.get("band") or "-"

                    rows += f""" <div class="row"> <div> <div> <span style="color:#38bdf8;font-weight:800;">{i}.</span> <b>{esc(brand)}</b> </div> <div class="small">Model: {esc(model)}</div> </div> <span class="badge" style="background:#1e294b;color:#38bdf8;"> {esc(band)} </span> </div> """

                content = f""" <div class="top"> <div> <div class="title">{esc(allowed['name'])}</div> <div class="small">Connected: {esc(total)} Devices</div> </div> <a class="link" href="/logout">Logout</a> </div> <div class="nav"> <a href="/?tab=groups">Voucher</a> <a href="/?tab=devices&group_id={esc(group_id)}">Refresh</a> <a href="/?tab=home">Home</a> </div> {rows or '<div class="card small" style="text-align:center;">No connected devices found.</div>'} """
                self.send_html(page_shell(content))
                return

            self.send_html(page_shell(
                '<div class="error">Unknown page.</div>'
            ))

        except Exception as e:
            traceback.print_exc()
            self.send_html(page_shell(
                f'<div class="error"><b>System Error</b><br>{esc(e)}</div>'
            ))


# The hosting platform used by the old file imports `handler`.
# If running this file directly, start a local server.
if __name__ == "__main__":
    from http.server import HTTPServer

    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8080"))

    if not APP_ID or not APP_SECRET:
        print("WARNING: Set RUIJIE_APP_ID and RUIJIE_APP_SECRET first.")

    print(f"Starting server on http://{host}:{port}")
    HTTPServer((host, port), handler).serve_forever()
