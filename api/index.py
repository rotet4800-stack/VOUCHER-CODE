def ruijie_login(account, password):
    # Environment Variables မှ အမှန်တကယ် ဝင်လာခြင်း ရှိမရှိ စစ်ဆေးရန်
    current_app_id = os.environ.get("RUIJIE_APP_ID", APP_ID)
    current_secret = os.environ.get("RUIJIE_APP_SECRET", APP_SECRET)

    if not current_app_id or not current_secret:
        return None, "Server မှာ Ruijie APP_ID / APP_SECRET မထည့်ရသေးပါ။"

    url = f"{BASE_URL}/service/api/login"
    
    # Ruijie Support ညွှန်ကြားချက်အတိုင်း JSON body ဖြင့် တိုက်ရိုက်သေချာစွာ ပို့ရန်
    payload = json.dumps({
        "appid": current_app_id,
        "secret": current_secret,
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
