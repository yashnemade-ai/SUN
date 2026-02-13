import requests
import json
import os
import urllib.parse
import time

# GitHub Secrets se data fetch karna
MAC = os.getenv('STALKER_MAC')
PORTAL = os.getenv('STALKER_PORTAL')
NPOINT_ID = os.getenv('NPOINT_ID')
UA = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3"

def get_fresh_link(base_url):
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': UA})

        # 1. Handshake - Session Token lene ke liye
        handshake_url = f"{PORTAL}?type=stb&action=handshake&token=&JsHttpRequest=1-xml"
        res1 = session.get(handshake_url, headers={'Cookie': f'mac={MAC}'}, timeout=15)
        token = res1.json()['js']['token']

        # 2. Get Profile - Session ko active rakhne ke liye zaroori hai
        profile_url = f"{PORTAL}?type=stb&action=get_profile&JsHttpRequest=1-xml"
        session.get(profile_url, headers={'Authorization': f'Bearer {token}', 'Cookie': f'mac={MAC}'}, timeout=15)

        # 3. Create Link - Naya 24-hours token generate karna
        cmd = f"ffrt {base_url}"
        encoded_cmd = urllib.parse.quote(cmd)
        
        create_link_url = f"{PORTAL}?type=itv&action=create_link&cmd={encoded_cmd}&JsHttpRequest=1-xml"
        res3 = session.get(create_link_url, 
                           headers={
                               'Authorization': f'Bearer {token}', 
                               'Cookie': f'mac={MAC}; stb_lang=en; timezone=GMT;',
                               'X-User-Agent': 'Model: MAG200; Link: WiFi'
                           }, timeout=15)
        
        fresh_url_raw = res3.json()['js']['cmd']
        # 'ffrt ' prefix hatakar asli URL nikaalna
        fresh_url = fresh_url_raw.replace("ffrt ", "").strip()
        
        return fresh_url
    except Exception as e:
        print(f"Error grabbing link for {base_url}: {str(e)}")
        return None

# --- MAIN LOGIC ---
print(f"Connecting to npoint bin: {NPOINT_ID}...")
try:
    # 1. npoint se current JSON download karo
    response = requests.get(f"https://api.npoint.io/{NPOINT_ID}", timeout=20)
    if response.status_code != 200:
        print(f"Failed to fetch JSON. Status code: {response.status_code}")
        exit()
    
    channels = response.json()
    updated_count = 0

    # 2. Loop through channels and find #auto
    for channel in channels:
        url = channel.get('url', "")
        if "#auto" in url:
            print(f"Refreshing: {channel.get('name', 'Unknown Channel')}")
            
            # Base link nikaalna: #auto aur purana ?token dono hata kar
            clean_url = url.split('#')[0]
            base_link = clean_url.split('?')[0]
            
            # Fresh token generate karo
            new_token_url = get_fresh_link(base_link)
            
            if new_token_url:
                # Nayi link ke piche wapas #auto lagao agli cycle ke liye
                channel['url'] = f"{new_token_url}#auto"
                updated_count += 1
                print(f"Done.")
            else:
                print(f"Skipped (Error in grabbing).")

    # 3. Agar kuch update hua hai toh npoint par save karo
    if updated_count > 0:
        print(f"Total {updated_count} links refreshed. Saving to npoint...")
        update_res = requests.post(f"https://api.npoint.io/{NPOINT_ID}", json=channels, timeout=20)
        
        if update_res.status_code == 200:
            print("✅ SUCCESS: npoint JSON updated successfully!")
        else:
            print(f"❌ ERROR: npoint update failed. Status: {update_res.status_code}")
    else:
        print("ℹ️ No channels found with #auto tag.")

except Exception as main_e:
    print(f"Fatal Error: {str(main_e)}")
