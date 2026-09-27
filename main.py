import requests

APP_ID = "openc3be644fb5dc"
SECRET = "0dea886911864f359497a65f94164518"
BASE_URL = "https://cloud.ruijienetworks.com"
GROUP_ID = "7833000"

def get_ruijie_devices():
    token_url = f"{BASE_URL}/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
    payload = {"appid": APP_ID, "secret": SECRET}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(token_url, json=payload, headers=headers)
        token_data = response.json()
        
        if response.status_code == 200 and token_data.get("code") == 0:
            access_token = token_data.get("accessToken")
            
            device_url = f"{BASE_URL}/service/api/open/v1/dev/user/current-user?group_id={GROUP_ID}&page_index=1&page_size=100&access_token={access_token}"
            device_res = requests.get(device_url, headers=headers)
            device_data = device_res.json()
            
            if device_res.status_code == 200 and device_data.get("code") == 0:
                total_count = device_data.get("totalCount", 0)
                client_list = device_data.get("list", [])
                
                print("\n" + "=" * 45)
                print(f" Ruijie Reyee ကွန်ရက် ချိတ်ဆက်မှု စာရင်း")
                print("=" * 45)
                print(f" ချိတ်ဆက်ထားသော ဖုန်း စုစုပေါင်း အရေအတွက်: {total_count} လုံး")
                print("-" * 45)
                
                if client_list:
                    for index, client in enumerate(client_list, 1):
                        brand = client.get("manufacturer") or client.get("brand") or "Unknown"
                        model = client.get("userName") or client.get("staModel") or "Mobile Device"
                        print(f" {index}. Brand: {brand} | Model: {model}")
                else:
                    print(" • ချိတ်ဆက်ထားသော စက်ပစ္စည်း မရှိသေးပါ။")
                print("=" * 45)
            else:
                print("ဖုန်းစာရင်း ရယူရန် မအောင်မြင်ပါ:", device_data.get("msg"))
        else:
            print("Token ရယူရန် မအောင်မြင်ပါ:", token_data.get("msg"))
            
    except Exception as e:
        print(f"ချိတ်ဆက်မှု အမှားအယွင်းရှိပါသည်: {e}")

if __name__ == "__main__":
    get_ruijie_devices()
