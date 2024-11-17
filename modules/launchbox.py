from collections import defaultdict
import logging as log
import os.path
import xml.etree.ElementTree as ET

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

lb_dir = 'Test'

def init(directory: str):
    """
    Initializes the module by setting the main LaunchBox directory.
    
    This is required for other module functions to work.
    
    Args:
        directory (str): Path to LaunchBox directory

    """

    # TODO: Validate and format the directory

    global lb_dir
    lb_dir = directory

################################################################################

def get_platform_data(platform_name: str) -> dict:
    '''

    '''
    found_platform = False

    # Load platform list, check both 'Name' and 'ScrapeAs'
    xml_tree = ET.parse(os.path.join(lb_dir, "Data", "Platforms.xml"))
    for p in xml_tree.getroot().findall('Platform'):
        if (p.findtext('Name')) == platform_name:
            found_platform = True
            break
        elif (p.findtext('ScrapeAs')) == platform_name:
            platform_name = p.findtext('Name')
            found_platform = True
            break

    if not found_platform:
        print(f"ERROR: Could not find platform matching '{platform_name}' in LB Platforms.xml")
        return None
    
    p_path = os.path.join(lb_dir, "Data", "Platforms", platform_name + ".xml")
    log.debug(f"Parsing element tree")
    p_xml = ET.parse(p_path)
    log.debug(f"Converting to dictionary")
    p_dict = etree_to_dict(p_xml.getroot())["LaunchBox"]

    return p_dict
    