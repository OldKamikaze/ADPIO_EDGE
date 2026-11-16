import ujson
import os
import shutil
import asyncio 
from   pathlib import Path

from lib.globals       import ROOT_FOLDER, WORKSPACE, APPS_FOLDER, ASSET_FOLDER
from lib.database_sql.server_virt_model import server_virt_db, params_runtime_rec

class settings_cfg:
    def __init__(self):
        self.uvicorn            = None
        self.bacnet_server      = None
        self.mqtt_client_server = None
        self.mqtt_broker_server = None

        self.python         = ''
        self.terminal       = {}
        self.auto_rebuild   = False
        
        self.create_work_folder()        
        
    def create_work_folder(self):
        #make workspace
        if not os.path.isdir(WORKSPACE):
            try: 
                os.mkdir(WORKSPACE)
                self.auto_rebuild = True
            except OSError as error:  
                print(error)
                
        #make default setings file
        if not os.path.isfile( f"{WORKSPACE}{Path('/settings.json')}" ) :
            try: 
                shutil.copy2(  f"{ROOT_FOLDER}{Path('/assets/settings.json')}", f"{WORKSPACE}{Path('/settings.json')}" )
            except OSError as error:  
                print(error)

        #make apps folder
        if not os.path.isdir(APPS_FOLDER):
            try: 
                os.mkdir(APPS_FOLDER)
            except OSError as error:  
                print(error)
        
        #make assets folder
        if not os.path.isdir(ASSET_FOLDER):
            try: 
                os.mkdir(ASSET_FOLDER)
            except OSError as error:  
                print(error)      

        #LOGS - HDD
        #if not os.path.isdir( f"{WORKSPACE}{Path('/log')}" ):
        #    try: 
        #        os.mkdir( f"{WORKSPACE}{Path('/log')}" )
        #    except OSError as error:  
        #        print(error)      
                                      
        
    def read_settings(self):
        with open ( f"{WORKSPACE}{Path('/settings.json')}" ) as f:
            rd  = f.read()
            cls = ujson.loads( rd )
            
            self.python         = cls['python_exe']
            self.terminal       = cls['terminal']
            
            self.uvicorn        = cls['uvicorn']

            self.bacnet_server      = cls['BACnet_server']
            self.mqtt_client_server = cls['MQTT_client']
            self.mqtt_broker_server = cls['MQTT_broker']
            


    """
    def write_settings(self):
        jsn = {
            'uvicorn':         self.uvicorn,
            'app_ids':         self.app_ids,
            'loraWAN':       self.loraWAN,
        }
        with open(WORK_FOLDER + '/settings.json', 'w') as f:
            f.write( ujson.dumps(jsn,  default = lambda o: o.__dict__, indent=4) )
    """