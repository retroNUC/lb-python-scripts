from collections import defaultdict
import logging as log
import os.path
import xml.etree.ElementTree as ET

################################################################################

main_directory = ''
platforms = {}
"""Dictionary storing data about available LB platforms, loaded from Platforms.xml, with 'Name' as key."""
gamedata = {}
"""Dictionary storing data about games/apps/etc for each LB platform, loaded from platform XML files, with LB platform name as key."""

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

def init(directory: str):
    """
    Initializes the module by setting the main LaunchBox directory.
    
    This is required for other module functions to work.
    
    Args:
        directory (str): Path to LaunchBox directory

    """

    # TODO: Validate and format the directory

    global main_directory
    main_directory = directory

################################################################################

def load_platform_list() -> int:

    '''
    Loads XML data from Platforms.xml and stores in module as dictionary.
    '''
    global main_directory
    if main_directory == '':
        log.error(f"Main LaunchBox directory is not set, has the module been initialized?")
        return 1
    
    global platforms

    if platforms:
        log.debug(f"Platform data is already loaded")
        return 0

    xml_tree = ET.parse(os.path.join(main_directory, "Data", "Platforms.xml"))
    xml_dict = etree_to_dict(xml_tree.getroot())

    # Restructure to dictionary
    if (p_list := xml_dict['LaunchBox'].get('Platform')):
        for p in p_list:
            if (p_name := p.get('Name')):
                platforms[p_name] = p

    return 0

################################################################################

def load_game_data(platform: str) -> int:
    """
    Loads game data for a LaunchBox platform name and stores in module as a 
    dictionary.

    Platform name provided has to be the exact name, not the 'ScrapeAs' name.
    
    Args:
        platform (str): Name of LaunchBox platform to load
    """
    global gamedata
    if gamedata.get(platform):
        log.debug(f"Game data for this platform is already loaded")
        return 0

    gd_path = os.path.join(main_directory, "Data", "Platforms", platform + ".xml")
    xml_tree = ET.parse(gd_path)
    xml_dict = etree_to_dict(xml_tree.getroot())["LaunchBox"]

    gamedata[platform] = xml_dict

    return 0

################################################################################

def get_game_data(platform: str) -> dict:
    '''
    Loads and returns a dictionary containing all game entries for a LB platform.
    '''

    global platforms
    global gamedata

    if not platforms:
        load_platform_list()

    found = False

    if platforms.get(platform):
        found = True
    else:
        for p_name, p_data in platforms.items():
            if p_data.get('ScrapeAs') == platform:
                platform = p_name
                found = True
                break

    if not found:
        log.error(f"ERROR: Could not find platform matching '{platform}' in LB Platforms.xml")
        return None
    
    if not gamedata.get(platform):
        load_game_data(platform)

    return gamedata[platform]
    