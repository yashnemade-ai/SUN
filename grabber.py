import requests
import json
import os
import urllib.parse

# GitHub Secrets se details lena
MAC = os.getenv('STALKER_MAC')
PORTAL = os.getenv('STALKER_PORTAL')
NPOINT_ID = os.getenv('NPOINT_ID')
UA = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3"

def get_fresh_link(base_url):
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': UA})

        # 1. Handshake
        res1 = session.get(f"{PORTAL}?type=stb&action=handshake&token=&JsHttpRequest=1-xml", headers={'Cookie': f'mac={MAC}'})
        token = res1.json()['js']['token']

        # 2. Get Profile (Necessary for session stability)
        session.get(f"{PORTAL}?type=stb&action=get_profile&JsHttpRequest=1-xml", 
                    headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}'})

        # 3. Create Link
        # Portal ko CMD bhejne ke liye 'ffrt ' zaroori hai
        cmd = f"ffrt {base_url}"
        encoded_cmd = urllib.parse.quote(cmd)
        
        res3 = session.get(f"{PORTAL}?type=itv&action=create_link&cmd={encoded_cmd}&JsHttpRequest=1-xml", 
                           headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}; stb_lang=en; timezone=GMT;'})
        
        fresh_url = res3.json()['js']['cmd'].replace("ffrt ", "").strip()
        print(f"Generated Fresh Link: {fresh_url[:50]}...")
        return fresh_url
    except Exception as e:
        print(f"Error grabbing link: {e}")
        return base_url

# --- MAIN LOGIC ---
print("Fetching current JSON from npoint...")
response = requests.get(f"https://api.npoint.io/{NPOINT_ID}")
if response.status_code != 200:
    print("Failed to fetch JSON from npoint. Check your ID.")
    exit()

channels = response.json()

# Har channel ki link refresh karo jisme packetcdn ya stalker link ho
for channel in channels:
    if "packetcdn.me" in channel['url'] or "localhost" in channel['url']:
        # Token hata kar sirf base link nikaalo
        base_link = channel['url'].split('?')[0]
        print(f"Refreshing Channel: {channel.get('name', 'Unknown')}")
        channel['url'] = get_fresh_link(base_link)

# Naya JSON npoint par update karo
print("Updating npoint.io...")
update_res = requests.post(f"https://api.npoint.io/{NPOINT_ID}", json=channels)

if update_res.status_code == 200:
    print("SUCCESS: All links updated in npoint!")
else:
    print(f"ERROR: Failed to update npoint. Status: {update_res.status_code}")
