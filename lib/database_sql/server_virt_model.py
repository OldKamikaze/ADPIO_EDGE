import os
from typing   import Any, Dict
from datetime import datetime
from pathlib  import Path

from sqlalchemy.orm  import registry
from sqlmodel        import Field, SQLModel, JSON, Column
from lib.database_sql.sqlmodel_driver import engine_db

from lib.globals import WORKSPACE, APPS_FOLDER
from lib.dataconversion import  str_to_dp

from lib.database_sql.workspace_model import workspace_db, application_rec
from lib.globals  import WORKSPACE, VIRTUAL_SPACE

from enum import Enum
from lib.dataconversion import str_to_dp


class server_model(SQLModel, registry=registry()): #application model
    pass


class params_runtime_rec(server_model, table=True):
    param       : str  =  Field(primary_key = True, max_length = 16    )
    value       : str  =  Field(max_length = 128,   default = 'novalue')
    datatype    : str  =  Field(max_length = 8,     default = 'str',   )
    
    def to_json(self):
        return {
            "param"   :  self.param,
            "value"   :  self.value,
            "datatype": self.datatype
        }
    

class datapoints_runtime_rec(server_model, table=True):
    id          : str  =  Field(max_length = 128,  default = 'App1', primary_key = True) 

    app_id      : str  =  Field(max_length = 68,   default = 'No Group',    )
    dp_id       : int  =  Field(                   default = -1,            )

    datatype    : str  =  Field(max_length = 8,    default = '',           )
    value       : str  =  Field(max_length = 128,  default = '',           )
    #writable    : bool =  Field(default = False,                           )

    def to_json(self):
        return {
            'id'         : self.id,      #ID FORMAT - app_grp, app_name, dp_grp, dp_name

            'app_id'     : self.app_id,  #ID FORMAT - app_grp, app_name
            'dp_id'      : self.dp_id,

            #'name'       : self.name,
            #'group'      : self.group,

            'datatype'   : self.datatype,
            'value'      : str_to_dp(self.value, self.datatype),
            #'writable'   : self.writable,
        }


class connector_rec(server_model, table=True): #drivers connector
    id           : str  =  Field(max_length = 128,   primary_key = True)             #src:deviceid-objectid
    
    src          : str  =  Field(max_length = 12,   default = None,  )  #protocol, aka bacnet, mqtt
    net          : str  =  Field(max_length = 32,   default = None,  )

    device_id    : str  =  Field(max_length = 64,   default = None,  )
    device_name  : str  =  Field(max_length = 64,   default = None,  )
    object_id    : str  =  Field(max_length = 64,   default = None,  )
    object_name  : str  =  Field(max_length = 64,   default = None,  )

    #datatype    : str  =  Field(max_length = 24,    default = None,  )
    value        : str  =  Field(max_length = 128,  default = None,  )

    properties   : Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    online       : bool           = Field(default = False,                  )
    last_updated : datetime       = Field(default_factory = datetime.now    )
    binds        : Dict[str, Any] = Field(default=[], sa_column=Column(JSON))


    def to_json(self):
        return {
            'id'          : self.id,
            
            'src'         : self.src,
            'net'         : self.net,

            'device_id'   : self.device_id,
            'device_name' : self.device_name,

            'object_id'   : self.object_id,
            'object_name' : self.object_name,

            #'datatype'    : self.datatype,
            'value'       : self.value,

            'properties'  : self.properties,
            
            'online'      : self.online,
            'last_updated': str(self.last_updated),
            'binds'       : str(self.binds)
        }


class connector_task(server_model, table=True): #drivers connector
    id          : int  =  Field(primary_key = True)
    src         : str  =  Field(max_length = 12,   default = 'No Protocol',     )  #protocol, aka bacnet, mqtt

    cmd        : str  =  Field(max_length = 32,   default = 'no command',      )
    params     : Dict[str, Any] = Field(default={}, sa_column=Column(JSON)     )

    def to_json(self):
        return {
            'id'         : self.id,
            'src'        : self.src,

            'cmd'        : self.cmd,
            'params'     : self.params,           
        }


def clear_virtual_db():
    try:
        pth = Path(f'{VIRTUAL_SPACE}/adpio_virtual.db')
        if pth.exists(): os.remove(pth)
    except:
        print('Failed to delete virtual database')


server_virt_db:engine_db  =  engine_db(f"sqlite:///{VIRTUAL_SPACE}{Path('/adpio_virtual.db')}", server_model)


class SERVER_PARAMS():
    SERVER_STATUS     = "SERVER_STATUS"
    GUI_TERMINAL      = "GUI_TERMINAL"
    TERMINAL_HDD_OUT  = "TERMINAL_HDD_OUT"
    WORKERS_COUNT     = "WORKERS_COUNT"
    AUTO_RELOAD       = "AUTO_RELOAD"

class SERVER_STATUS_SIGNALS():
    NOT_INITIALIZED = "NOT INITIALIZED"
    INITIALIZED     = "INITIALIZED"
    TERMINATE       = "TERMINATE"


def init_virtual_db(GUI_TERMINAL = False, FAPI_AUTO_RELOAD = False, TERMINAL_HDD_OUT = False): #server status, #terminal gui
    term = GUI_TERMINAL
    if  __debug__: term = False
    params: list[params_runtime_rec] = [
        params_runtime_rec( param=SERVER_PARAMS.SERVER_STATUS   , datatype="str" , value=SERVER_STATUS_SIGNALS.NOT_INITIALIZED ), #NOT_INIT, INIT, TERMINATE
        params_runtime_rec( param=SERVER_PARAMS.GUI_TERMINAL    , datatype="bool", value=str(term)                             ), #GUI Terminal or normal
        params_runtime_rec( param=SERVER_PARAMS.TERMINAL_HDD_OUT, datatype="bool", value=str(TERMINAL_HDD_OUT)                 ), #GUI Terminal to hdd, otherwise - virtual space
        params_runtime_rec( param=SERVER_PARAMS.WORKERS_COUNT   , datatype="int",  value=str(0)                                ), #WORKER COUNT
        params_runtime_rec( param=SERVER_PARAMS.AUTO_RELOAD     , datatype="bool", value=str(FAPI_AUTO_RELOAD)                 ), #FAST API AUTO RELOAD
    ]
    server_virt_db.add_records_na(params)


async def set_server_param(param, value):
    await server_virt_db.update_fields(params_runtime_rec, params_runtime_rec.param, param, {"value": str(value)})


async def get_server_param(pram_val):
    val:params_runtime_rec = await server_virt_db.get_record(params_runtime_rec, params_runtime_rec.param, pram_val)
    return str_to_dp(val.value, val.datatype)


async def set_data_run(id, value):
    await server_virt_db.update_fields(datapoints_runtime_rec, datapoints_runtime_rec.id, id, {"value": str(value)})


async def get_data_run(id):
    val:datapoints_runtime_rec =  await server_virt_db.get_record(datapoints_runtime_rec, datapoints_runtime_rec.id, id)
    return str_to_dp(val.value, val.datatype)


async def get_data_run_multi(ids: list):
    vals: list[datapoints_runtime_rec] = await server_virt_db.get_records_multi(datapoints_runtime_rec, datapoints_runtime_rec.id, ids)
    return [str_to_dp(val.value, val.datatype) for val in vals] #returns array of values [ex1, ex2, ex3]


async def set_data_run_multi(ids: list):
    await server_virt_db.update_multi_fields(datapoints_runtime_rec, datapoints_runtime_rec.id, 'data_id', ids) #files = [{key: val, "fieldname": "123"},] etc
