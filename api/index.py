def ruijie_login(account, password):
    if not APP_ID or not APP_SECRET:
        return None, "Server မှာ Ruijie APP_ID / APP_SECRET မထည့်ရသေးပါ။"

    url = f"{BASE_URL}/service/api/login"
    
    # Ruijie Support ညွှန်ကြားချက်အတိုင်း JSON body ပုံစံဖြင့် ပို့ရန်
    payload = json.dumps({
        "appid": APP_ID,
        "secret": APP_SECRET,
        "account": account,
        "password": password,
    })

    try:
        # GET အစား POST ဖြင့် ပြောင်းလဲပေးခြင်း
        res = request("post", url, headers=HEADERS, data=payload)
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
