import os
from   pathlib import Path

ROOT_FOLDER  = os.getcwd()

#if sys.platform == "win32":  
#    WORKSPACE     = rf'{os.path.expanduser("~") }\ADPIOEDGE'
#    ASSET_FOLDER  = rf'{WORKSPACE}\assets'
#    APPS_FOLDER   = rf'{WORKSPACE}\applications'
#    VIRTUAL_SPACE = ''
#else:                        

WORKSPACE     = f'{os.path.expanduser("~")}/.ADPIOEDGE'
ASSET_FOLDER  = f'{WORKSPACE}/assets'      
APPS_FOLDER   = f'{WORKSPACE}/applications'
VIRTUAL_SPACE = '/dev/shm'

    

