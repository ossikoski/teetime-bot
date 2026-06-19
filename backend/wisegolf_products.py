import json
import re
import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.utils import typoless


def _extract_hosts(js_text):
    """
    Hardcoded way to get the list under "hosts" key from the js response text listing all golfclubs as objects
    
    Returns
    -------
    [dict]
        List of dicts with each club as an object, having keys e.g. name, golfGlubId, baseUrl, displayName
    """
    # locate the hosts array
    m = re.search(r'hosts\s*:\s*\[', js_text)
    if not m:
        raise ValueError("hosts array not found")
    start = m.end() - 1                      # opening '['

    # bracket-count to the matching ']' (skips nested [1] arrays, stops before .sort)
    depth = 0
    for i in range(start, len(js_text)):
        if js_text[i] == '[':
            depth += 1
        elif js_text[i] == ']':
            depth -= 1
            if depth == 0:
                end = i
                break
    else:
        raise ValueError("unterminated hosts array")

    arr = js_text[start:end + 1]

    # JS literal -> JSON
    arr = arr.replace('`', '"')                                       # backtick strings
    arr = re.sub(r'!0\b', 'true', arr)                                # !0 -> true
    arr = re.sub(r'!1\b', 'false', arr)                               # !1 -> false
    arr = re.sub(r'([{,]\s*)([A-Za-z_]\w*)(\s*:)', r'\1"\2"\3', arr)  # quote keys

    return json.loads(arr)

def get_clubs(club_name=None):
    assets_url = 'https://app.wisegolf.fi/assets/WiseSettings-BgR3J8yt.js'
    assets_text = requests.get(assets_url).text
    
    hosts = _extract_hosts(assets_text)
    
    if club_name:
        hosts = [c for c in hosts if typoless(club_name) in typoless(c.get('name', '')) or typoless(club_name) in typoless(c.get('displayName', ''))]


    for club in hosts:
        if club['golfClubId'] in [99998, 99999]:
            continue
            
        club['products'] = []

        url = f'{club['restUrl']}/products/?type=6'

        try:
            res_json = requests.get(url).json()
        except Exception:
            print(f'Exception with {club['restUrl']}')
        
        
        if res_json.get('statistics', {}).get('records') == 0:
            continue

        club['products'] = res_json.get('rows', [])

    # Handle filter params
    return hosts


if __name__ == '__main__':
    print(get_clubs('tammergolf'))
