# Modified from https://github.com/RetroAchievements/api-python/

import requests
import time

################################################################################

RC_BASE_URL = "https://retroachievements.org/API/"

username = ""
api_key = ""

################################################################################

def init(user: str, key: str):
    """
    Initializes the module
    
    Args:
        user (str): Username
        key (str): API Key
    """

    # TODO: Validate that username value appears to be valid
    global username
    username = user

    # TODO: Validate that api_key value appears to be valid
    global api_key
    api_key = key

    # TODO: Do a test request to the API, make sure things are okay

    return 0

################################################################################

def url_params(params=None):
    '''
    Inserts the auth and query params into the request
    '''
    if params is None:
        params = {}
    params.update({"z": username, "y": api_key})
    return params

################################################################################

def call_api(endpoint=None, params=None, timeout=30, headers=None):
    if endpoint is None:
        endpoint = {}

    # Rough rate limit - 180 per minute (3 per second)

    attempts = 0
    while attempts < 5:

        req = requests.get(
            f"{RC_BASE_URL}{endpoint}",
            params = url_params(params),
            timeout = timeout,
            headers = headers,
        )

        if req.status_code == 200:
            break
        else:
            print(f"  {req.status_code} - {req.reason}")
            attempts = attempts + 1
            time.sleep(1.0)

    return req

################################################################################

def get_console_ids(active = 0, is_game_system = 0) -> list:
    '''
    Retrieve the complete list of all system ID and name pairs on the site.
    Params:
        a: If 1, only return active systems
        g: If 1, only return gaming systems (not Hubs, Events, etc)
    '''
    result = call_api("API_GetConsoleIDs.php?",
        {"a": active, "g": is_game_system}
    ).json()
    return result

################################################################################

def get_game_list(system: int, has_cheevos = 0, hashes = 0, offset = 0, max_results = 0) -> dict:
    '''
    Retrieve the complete list of games for a specified console on the site, 
    targeted by the console ID.
    Params:
        i: The target system ID
        f: If 1, only return games that have achievements
        h: If 1, also return supported hashes for games
        o: Offset of the list of results. Ignores the first X results set in this parameter
        c: Number of max results desired
    '''
    result = call_api("API_GetGameList.php?",
        {"i": system, "f": has_cheevos, "h": hashes, "o": offset, "c": max_results}
    ).json()
    return result

################################################################################

def get_game_hashes(game_id: int) -> dict:
    '''
    Retrieve the hashes linked to a game, targeted via its unique ID.
    Params:
        i: The target game ID
    '''
    result = call_api("API_GetGameHashes.php?",
        {"i": game_id}
    ).json()
    return result
