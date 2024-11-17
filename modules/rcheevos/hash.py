import os.path
import re
import subprocess

################################################################################

rahasher_path = ''
dtool_path = ''

################################################################################

def init(hasher: str, dtool: str):
    '''
    Initializes the module
    
    Args:
        hasher (str): Path to RAHasher.exe
        dtool (str): Path to DolphinTool.exe
    '''

    # TODO: Validate that hasher path appears correct
    global rahasher_path
    rahasher_path = hasher

    # TODO: Validate that dtool path appears correct
    global dtool_path
    dtool_path = dtool

    return 0

################################################################################

def calculate_hash(system: int, file_path: str) -> str:
    '''
    Calculate hash
    '''
    result = 0

    if system == 16:
        if not os.path.exists(dtool_path):
            return 0
        r = subprocess.run([dtool_path, 'verify', '-i', file_path, '-a' , 'rchash'], capture_output=True, text=True)
        h = r.stdout.strip()
        if re.findall(r"([a-fA-F\d]{32})", h):
            result = h
    else:
        r = subprocess.run([rahasher_path, str(system), file_path], capture_output=True, text=True)
        h = r.stdout.strip()
        if re.findall(r"([a-fA-F\d]{32})", h):
            result = h
    
    return result
