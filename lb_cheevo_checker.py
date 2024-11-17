import configparser
import json
import logging as log
import xml.etree.ElementTree as ET
from collections import defaultdict
import os
import re
import subprocess
import sys

import modules.launchbox as LB
import modules.rcheevos.api as RC_API
import modules.rcheevos.hash as RC_HASH

try:
    import requests_cache
except ImportError:
    print("Module 'requests-cache' not found, installing from pip...\n")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests-cache'])
    print("")
finally:
    import requests_cache 

################################################################################

def etree_to_dict(t):
    """https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary"""

    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

################################################################################

# Load config settings file
# TODO: ADD WAY MORE VALIDATION
config = configparser.ConfigParser()
config_file = 'dev/config_settings.ini' if os.path.exists('dev/config_settings.ini') else 'config_settings.ini'
if os.path.exists(config_file):
    config.read(config_file)
else:
    print("Couldn't find config_settings.ini, quitting")
    quit()

# Load config consoles file
# TODO: ADD WAY MORE VALIDATION
consoles_file = 'dev/config_consoles.json' if os.path.exists('dev/config_consoles.json') else 'config_consoles.json'
if os.path.exists(consoles_file):
    with open(consoles_file) as f:
        consoles = json.load(f)
else:
    print("Couldn't find config_consoles.json, quitting")
    quit()

# Set up logging
log.basicConfig(level=log.WARNING)

# Initialize modules
LB.init(config['LAUNCHBOX']['directory'])
RC_API.init(config['RETROACHIEVEMENTS']['username'], config['RETROACHIEVEMENTS']['api_key'])

rahasher_path = os.path.join(LB.lb_dir, 'ThirdParty', 'RetroAchievements', 'RAHasher.exe')
# TODO: Pull this properly from Emulators.xml in LB data
dolphintool_path = ''
RC_HASH.init(rahasher_path, dolphintool_path)

# Set up cache for API requests
cache_path = os.path.join(os.getcwd(), 'cache', 'cache')
url_expire_rules = {
    '*API_GetGameList*': 60 * 60 * 24
}
requests_cache.install_cache(cache_path, urls_expire_after = url_expire_rules)

data_path = os.path.join(os.getcwd(), 'data')
if not os.path.exists(data_path):
    os.makedirs(data_path)

hashes_path = os.path.join(os.getcwd(), 'hashes')
if not os.path.exists(hashes_path):
    os.makedirs(hashes_path)

print("Requesting RetroAchievements API data...")

rc_consoles = RC_API.get_console_ids()
print(f"  Requested Console ID data - {len(rc_consoles)} systems")

if config['CHEEVO_CHECKER']['dump_ra_data']:
    f_path = os.path.join(data_path, 'ra_console_ids.json')
    with open(f_path, 'w', encoding='utf-8') as f:
        json.dump(rc_consoles, f, ensure_ascii = False, indent = 4)

rc_hashes = {}
for c in consoles:

    if not c['should_scan']:
        continue

    # Request RA game list for console
    c_name = c['rc_name']
    c_dict = next(i for i in rc_consoles if i["Name"] == c_name)
    c_id = c_dict['ID']
    c['rc_games'] = RC_API.get_game_list(c_id, 1, 1)

    # Make sure hash is lowercase, add to hash lookup table
    h_count = 0
    for g in c['rc_games']:
        g['Hashes'] = [h.casefold() for h in g['Hashes']]
        for h in g['Hashes']:
            h_count = h_count + 1
            if h not in rc_hashes:
                rc_hashes[h] = g
            else:
                print(f"ERROR: Hash {h} already exists in RA lookup table?") 

    print(f"  Requested '{c_name}' game data - {len(c['rc_games'])} games, {h_count} hashes")

    if config['CHEEVO_CHECKER']['dump_ra_data']:
        f_path = os.path.join(data_path, 'ra_console_' + str(c_id) + '.json')
        with open(f_path, 'w', encoding='utf-8') as f:
            json.dump(c['rc_games'], f, ensure_ascii = False, indent = 4)

print()
print("Loading LaunchBox data...")

lb_hashes = []
for c in consoles:

    if not c['should_scan']:
        continue

    log.debug(f"Loading LB data - {c['lb_scrapename']}")

    # Load LB platform data
    c_name = c['lb_scrapename']
    c_data = LB.get_platform_data(c_name)
    if c_data == None:
        c['should_scan'] = False
        continue

    # Stub entries if certain data doesn't exist
    if c_data.get('Game') == None:
        c_data['Game'] = []
    if c_data.get('AdditionalApplication') == None:
        c_data['AdditionalApplication'] = []

    c['lb_data'] = c_data
    print(f"  Loaded '{c_name}' game data - {len(c_data['Game'])} Game entries, {len(c_data['AdditionalApplication'])} Additional Application entries")

    c['lb_game_ids'] = {}
    c['lb_game_hashes'] = {}

    for i, g in enumerate(c['lb_data']['Game']):
        log.debug(f"Processing Game entry - {g.get('ApplicationPath')}")

        # Build dictionary for quick lookup based on game ID
        if (g_id := g['ID']):
            c['lb_game_ids'][g_id] = i

        # Build dictionary for quick lookup based on game RA hash
        if (g_h := g['RetroAchievementsHash']):
            g_h = g_h.casefold()
            if re.findall(r"([a-fA-F\d]{32})", g_h):

                # Add to per-console dictionary
                c['lb_game_hashes'][g_h] = i

                # Add to cross-console list
                if g_h not in lb_hashes:
                    lb_hashes.append(g_h)
                else:
                    log.warning(f"Hash already exists in lb_hashes? - {g.get('Title')} ({g_h})")
            else:
                log.warning(f"Hash appears to be invalid? - {g.get('Title')} ({g_h})")

    # Load cached 'AdditionalApplication' hashes
    c['lb_extra_hashes'] = {}
    h_file = os.path.join(hashes_path, c_name + '.json')
    if os.path.exists(h_file):
        with open(h_file) as f:
            c['lb_extra_hashes'] = json.load(f)
        print(f"  Loaded '{c_name}' cached hashes - {len(c['lb_extra_hashes'])} Additional Application hashes")

    # With 'AdditionalApplication' entries, we need to do it ourselves...
    for a in c['lb_data']['AdditionalApplication']:
        log.debug(f"Processing AdditionalApplication entry - {a.get('ApplicationPath')}")
        c_dict = next(i for i in rc_consoles if i["Name"] == c['rc_name'])
        c_id = c_dict['ID']
        a_apppath = a.get('ApplicationPath')

        if a_apppath.casefold().endswith('.m3u'):
            log.debug(f"Skipping AA due to .m3u extension")
            continue

        log.debug(f"Checking if AA entry is same file as main game")
        if (a_gid := a.get('GameID')):
            if (g_i := c['lb_game_ids'].get(a_gid)):
                g = c['lb_data']['Game'][g_i]
                if g.get('ApplicationPath') == a_apppath:
                    log.debug(f"Skipping AA because it's same file as main game")
                    continue

        # If it doesn't exist in the cache, generate the hash
        log.debug(f"Checking if app path already exists in cached hashes")
        if a_apppath not in c['lb_extra_hashes']:
            log.debug(f"App path not found in cached data, going to perform hash")
            a_apppath_local = a_apppath.replace('D:\\', 'X:\\emulation\\')
            h = RC_HASH.calculate_hash(c_id, a_apppath_local)
            print(f"  New Hash: {a_apppath_local} ({h})")
            if re.findall(r"([a-fA-F\d]{32})", str(h)):
                c['lb_extra_hashes'][a_apppath] = h
            else:
                print(f"  WARNING: Hash rejected by regex: {a.get('Title')} ({h})")
        else:
            log.debug(f"App path successfully found in cached hashes ({c['lb_extra_hashes'][a_apppath]})")

        # Add it to the main hash lookup table
        if (h := c['lb_extra_hashes'].get(a_apppath)):
            h = h.casefold()
            log.debug(f"Checking if hash already exists in cross-platform lookup")
            if h not in lb_hashes:
                log.debug(f"Hash and game data added to cross-platform lookup")
                lb_hashes.append(h)
            else:
                log.debug(f"Hash and game data already existed in cross-platform lookup")

    # Save out cache
    with open(h_file, "w") as f:
        json.dump(c['lb_extra_hashes'], f, ensure_ascii = False, indent = 4)


print()

# Compare
for c in consoles:

    if not c['should_scan']:
        continue

    print(f"Checking {c["lb_scrapename"]}...")
    for g in c['rc_games']:
        if (g_hashes := g.get('Hashes')):

            found = False

            for h_rc in g_hashes:
                if h_rc.casefold() in lb_hashes:
                    found = True
                    break

            if not found:
                g_name = g.get('Title')

                skip_data = [ {'config': 'skip_demo',       'string': '~Demo~'},
                              {'config': 'skip_hack',       'string': '~Hack~'},
                              {'config': 'skip_homebrew',   'string': '~Homebrew~'},
                              {'config': 'skip_prototype',  'string': '~Prototype~'},
                              {'config': 'skip_subset',     'string': '[Subset'},
                              {'config': 'skip_unlicensed', 'string': '~Unlicensed~'} ]

                skipped = False
                for s in skip_data:
                    if config.getboolean('CHEEVO_CHECKER', s['config']):
                        if s['string'] in g_name:
                            skipped = True
                            break

                if skipped:
                    log.info(f"Skipped RA entry due to filtering - {g_name}")
                    continue

                print(f"[NOT FOUND] {g_name}")
                if (g_hash_info := RC_API.get_game_hashes(g['ID'])):
                    if (g_hash_info := g_hash_info.get('Results')):
                        for h in g_hash_info:
                            h_labels = h.get('Labels')
                            h_labels = " ".join('[' + str(x).upper() + ']' for x in h_labels)
                            print(f"  Possible RA hash: {h.get('MD5')} - {h.get('Name', 'No Name')} {h_labels}")

    print()
