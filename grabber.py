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

        # 2. Get Profile
        session.get(f"{PORTAL}?type=stb&action=get_profile&JsHttpRequest=1-xml", 
                    headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}'})

        # 3. Create Link
        cmd = f"ffrt {base_url}"
        encoded_cmd = urllib.parse.quote(cmd)
        
        res3 = session.get(f"{PORTAL}?type=itv&action=create_link&cmd={encoded_cmd}&JsHttpRequest=1-xml", 
                           headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}; stb_lang=en; timezone=GMT;'})
        
        fresh_url = res3.json()['js']['cmd'].replace("ffrt ", "").strip()
        return fresh_url
    except Exception as e:
        print(f"Error grabbing link: {e}")
        return None

# --- MAIN LOGIC ---
print("Fetching current JSON from npoint...")
response = requests.get(f"https://api.npoint.io/{NPOINT_ID}")
if response.status_code != 200:
    print("Failed to fetch JSON from npoint. Check your ID.")
    exit()

channels = response.json()
updated_count = 0

for channel in channels:
    url = channel.get('url', "")
    # 🔥 Sirf unhi links ko update karega jisme #auto likha hai
    if "#auto" in url:
        print(f"Target Found: {channel.get('name', 'Unknown')}")
        
        # 1. #auto ko hata kar aur purane token ko hata kar base link nikaalein
        clean_url = url.split('#')[0] # #auto hataya
        base_link = clean_url.split('?')[0] # purana token hataya
        
        # 2. Naya token mangwayein
        new_token_url = get_fresh_link(base_link)
        
        if new_token_url:
            # 3. Nayi link ke piche wapas #auto laga dein taaki agli baar phir update ho sake
            channel['url'] = f"{new_token_url}#auto"
            print(f"Successfully Refreshed: {channel.get('name')}")
            updated_count += 1
        else:
            print(f"Failed to refresh: {channel.get('name')}")

# Naya JSON npoint par update karo
if updated_count > 0:
    print(f"Updating npoint.io with {updated_count} new links...")
    update_res = requests.post(f"https://api.npoint.io/{NPOINT_ID}", json=channels)
    if update_res.status_code == 200:
        print("SUCCESS: JSON updated on npoint!")
    else:
        print(f"ERROR: Failed to update npoint. Status: {update_res.status_code}")
else:
    print("No channels with #auto found. Nothing to update.")
