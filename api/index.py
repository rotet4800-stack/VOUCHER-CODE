import os
import json
import requests
from flask import Flask, request, render_template_string

# Vercel မှ အသိအမှတ်ပြုမည့် top-level app variable
app = Flask(__name__)

# Environment Variables များမှ App ID နှင့် Secret ကို ယူခြင်း
APP_ID = os.environ.get("RUIJIE_APP_ID", "openc3be644fb5dc")
APP_SECRET = os.environ.get("RUIJIE_APP_SECRET", "0dea886911864f359497a65f94164518")
BASE_URL = "https://cloud-as.ruijienetworks.com"
HEADERS = {"Content-Type": "application/json"}

def safe_json(res):
    try:
        return res.json()
    except Exception:
        return {}

def ruijie_login(account, password):
    if not APP_ID or not APP_SECRET:
        return None, "Server မှာ Ruijie APP_ID / APP_SECRET မထည့်ရသေးပါ။"

    url = f"{BASE_URL}/service/api/login"
    
    # Ruijie Support ညွှန်ကြားချက်အတိုင်း JSON body ပုံစံဖြင့် POST ပို့ရန်
    payload = json.dumps({
        "appid": APP_ID,
        "secret": APP_SECRET,
        "account": account,
        "password": password,
    })

    try:
        res = requests.post(url, headers=HEADERS, data=payload)
        data = safe_json(res)

        if res.status_code != 200 or data.get("code") != 0:
            return None, data.get("msg") or "Login failed"

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

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        account = request.form.get("account")
        password = request.form.get("password")
        user_data, err = ruijie_login(account, password)
        if err:
            error = err
        else:
            return "Login Successful! အောင်မြင်ပါသည်။"

    html_template = """
    <!DOCTYPE html>
    <html lang="my">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ruijie Cloud Login</title>
    </head>
    <body style="background:#121212; color:#fff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <div style="background:#1e1e1e; padding:30px; border-radius:10px; border:1px solid #333; width:320px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
            <h2 style="text-align:center; margin-bottom:5px;">Ruijie Cloud</h2>
            <p style="text-align:center; color:#aaa; font-size:12px; margin-bottom:20px;">ကိုယ့် Ruijie/Reyee Account နဲ့ Login ဝင်ပါ</p>
            
            {% if error %}
                <div style="background:#4a1515; color:#ff8888; padding:10px; margin-bottom:15px; border-radius:5px; text-align:center; font-size:14px; border:1px solid #772222;">{{ error }}</div>
            {% endif %}
            
            <form method="POST">
                <label style="font-size:13px; color:#ccc;">Ruijie Account / Email</label>
                <input type="text" name="account" style="width:100%; box-sizing:border-box; padding:10px; margin:5px 0 15px 0; background:#2c2c2c; border:1px solid #444; color:#fff; border-radius:5px;" required>
                
                <label style="font-size:13px; color:#ccc;">Password</label>
                <input type="password" name="password" style="width:100%; box-sizing:border-box; padding:10px; margin:5px 0 20px 0; background:#2c2c2c; border:1px solid #444; color:#fff; border-radius:5px;" required>
                
                <button type="submit" style="width:100%; padding:11px; background:#0066ff; color:#fff; border:none; border-radius:5px; font-weight:bold; cursor:pointer; font-size:14px;">Login</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, error=error)
