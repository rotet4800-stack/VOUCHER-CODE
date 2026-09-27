from http.server import BaseHTTPRequestHandler
import requests
import json
import traceback

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # ၁။ Access Token တောင်းယူခြင်း[span_5](start_span)[span_5](end_span)
        token_url = "https://cloud-as.ruijienetworks.com/service/api/oauth20/client/access_token?token=d63dss0a81e4415a889ac5b78fsc904a"
        token_payload = json.dumps({
            "appid": "openc3be644fb5dc",
            "secret": "0dea886911864f359497a65f94164518"
        })
        
        try:
            token_res = requests.post(token_url, headers=headers, data=token_payload)
            token_data = token_res.json()
            access_token = token_data.get("accessToken")
            
            if not access_token:
                self.wfile.write(json.dumps({"error": "Token မရရှိပါ။", "details": token_data}).encode('utf-8'))
                return

            # ၂။ Group ID ရယူရန် Network Group List လှမ်းခေါ်ခြင်း[span_6](start_span)[span_6](end_span)
            group_url = f"https://cloud-as.ruijienetworks.com/service/api/group/single/tree?depth=BUILDING&access_token={access_token}"
            group_res = requests.get(group_url, headers=headers)
            group_data = group_res.json()
            
            # Group ID ကို ရှာဖွေခြင်း (ပထမဆုံးတွေ့သည့် Group ID ကို ယူမည်)
            group_id = None
            try:
                # Documentation ဖွဲ့စည်းပုံအရ groups အောက်မှ groupId ကို ယူမည်[span_7](start_span)[span_7](end_span)
                groups_info = group_data.get("groups", {})
                if "subGroups" in groups_info and len(groups_info["subGroups"]) > 0:
                    group_id = groups_info["subGroups"][0]["groupId"]
                else:
                    group_id = groups_info.get("groupId", 0)
            except Exception:
                group_id = 0

            if not group_id:
                group_id = 0  # ရှာမတွေ့ပါက Default 0 ဖြင့် သုံးမည်

            # ၃။ Voucher ထုတ်လုပ်ခြင်း (Generate Voucher API)[span_8](start_span)[span_8](end_span)
            voucher_url = f"https://cloud-as.ruijienetworks.com/service/api/open/auth/voucher/create/{group_id}?access_token={access_token}"
            
            # Documentation တွင် ဖော်ပြထားသော လိုအပ်သော Parameter များ[span_9](start_span)[span_9](end_span)
            voucher_payload = json.dumps({
                "quantity": 1,
                "profile": "30113648274480073538014045592098", # သင့်အကောင့်ထဲရှိ Profile UUID ဖြင့် လဲရန်
                "userGroupId": 18067                       # သင့်အကောင့်ထဲရှိ User Group ID ဖြင့် လဲရန်
            })

            voucher_res = requests.post(voucher_url, headers=headers, data=voucher_payload)
            voucher_data = voucher_res.json()
            
            # ရလဒ်ကို ပြသခြင်း[span_10](start_span)[span_10](end_span)
            self.wfile.write(json.dumps(voucher_data).encode('utf-8'))
            
        except Exception as e:
            self.wfile.write(json.dumps({
                "error": "System Error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }).encode('utf-8'))
        
        return
