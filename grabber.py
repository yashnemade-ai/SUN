import requests
import json
import os
import urllib.parse

MAC = os.getenv('STALKER_MAC')
PORTAL = os.getenv('STALKER_PORTAL')
NPOINT_ID = os.getenv('NPOINT_ID')
# Purana MAG254 User-Agent try karte hain jo zyada stable hai
UA = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3"

def get_fresh_link(base_url):
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': UA,
            'X-User-Agent': 'Model: MAG254; Link: WiFi'
        })

        # 1. Handshake
        url1 = f"{PORTAL}?type=stb&action=handshake&token=&JsHttpRequest=1-xml"
        res1 = session.get(url1, headers={'Cookie': f'mac={MAC}'}, timeout=20)
        
        if res1.status_code != 200:
            print(f"-> Handshake HTTP Error: {res1.status_code}")
            return None
            
        try:
            data1 = res1.json()
            token = data1['js']['token']
        except:
            print(f"-> Handshake Response is not JSON: {res1.text[:100]}")
            return None

        # 2. Get Profile
        session.get(f"{PORTAL}?type=stb&action=get_profile&JsHttpRequest=1-xml", 
                    headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}'}, timeout=20)

        # 3. Create Link
        cmd = f"ffrt {base_url}"
        url3 = f"{PORTAL}?type=itv&action=create_link&cmd={urllib.parse.quote(cmd)}&JsHttpRequest=1-xml"
        res3 = session.get(url3, headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}'}, timeout=20)
        
        try:
            fresh_url = res3.json()['js']['cmd'].replace("ffrt ", "").strip()
            return fresh_url
        except:
            print(f"-> Create Link Failed. Portal said: {res3.text[:100]}")
            return None

    except Exception as e:
        print(f"-> Script Error: {str(e)}")
        return None

# --- MAIN ---
print(f"Fetching npoint: {NPOINT_ID}")
response = requests.get(f"https://api.npoint.io/{NPOINT_ID}")
channels = response.json()
updated_count = 0

for channel in channels:
    if "#auto" in channel['url']:
        print(f"Refreshing: {channel['name']}")
        base = channel['url'].split('#')[0].split('?')[0]
        new_link = get_fresh_link(base)
        if new_link:
            channel['url'] = f"{new_link}#auto"
            updated_count += 1

if updated_count > 0:
    res = requests.post(f"https://api.npoint.io/{NPOINT_ID}", json=channels)
    print(f"Successfully updated {updated_count} links!")
else:
    print("No updates made. Check errors above.")
