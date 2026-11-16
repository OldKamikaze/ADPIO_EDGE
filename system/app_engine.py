import asyncio
import os
import sys
from pathlib import Path

from py_compile             import compile
from system.settings_server import settings_cfg
from lib.globals            import ROOT_FOLDER, WORKSPACE, APPS_FOLDER

from drivers.drivers_tools import connect_id_gen, connect_id_gen_jsn, connect_id_decode_jsn

from content.app_ide_datapoints import load_datapoints
from content.app_ide_graphics   import reorder_graphics
from content.app_ide_logic      import load_blocks #save_bind_alloc
#from lib.dataconversion         import set_mem_value, get_mem, get_binds

#from drivers.loraWAN_conn_sever import add_app_loraWAN_sync, free_app_loraWAN_sync
#from drivers.bacnet_server      import add_app_BACnet_sync, free_app_BACnet_sync

from content.logger import print_app_event
from lib.database_sql.application_model import datapoints_rec, logic_rec, trend_rec
from lib.database_sql.server_virt_model import server_virt_db, clear_virtual_db, init_virtual_db, set_server_param, get_server_param, get_data_run, set_data_run, datapoints_runtime_rec, SERVER_PARAMS, SERVER_STATUS_SIGNALS

from content.app_view import app_status


PYTHON_SYS = ""

def init_settings():
    global PYTHON_SYS

    settings = settings_cfg()
    settings.read_settings()
    PYTHON_SYS = settings.python


async def build_app(app_id):
    #if sys.platform == "win32":
    #    APP_SRC  = rf'{ROOT_FOLDER}\assets\app_main_src.py' #do not confuse with assets in workfolder 
    #    APP_EXE  = rf'{APPS_FOLDER}\{app}\app_main.py'
    #else: 
    APP_SRC  = f'{ROOT_FOLDER}/assets/app_main_src.py' #do not confuse with assets in workfolder 
    APP_EXE  = f'{APPS_FOLDER}/{app_id}/app_main.py'

    print(f'\n\n>>>> Building {app_id} <<<<')  

    datapoints      = await load_datapoints(app_id)
    block_list      = await load_blocks    (app_id)

    libimport, getters, setters, constants, blocks = sort_blocks(block_list)   


#read contents
    with open(APP_SRC, "r") as src_file:
        src_code = src_file.read()
        src_file.close()

#Do code shenanigans 
    src_code        = build_header_app_info(app_id, src_code, libimport, datapoints)
    src_code        = build_datapoints     (app_id, src_code, datapoints)
    src_code        = build_net_datapoints (app_id, src_code, datapoints)
    
    binds = []
    src_code, binds = build_gets   (app_id, src_code, blocks, binds, datapoints, getters, constants)
    src_code, binds = build_blocks (app_id, src_code, blocks, binds)
    src_code        = build_sets   (app_id, src_code, datapoints, setters)
    src_code        = build_binds  (app_id, src_code, binds)
    src_code        = build_trends (app_id, src_code, datapoints)

#write contents    
    with open(APP_EXE, "w") as app_file:
        app_file.write(src_code)
        app_file.close()

    compile(APP_EXE) #compile from pycompiller stuff

#graphics
    await reorder_graphics(app_id)

    print(f'>>>> {app_id} Done <<<<')  
    print(' ')


#***** Build Header *****
def build_header_app_info(app_id, src_code, libimport_list, datapoints: list[datapoints_rec]):
    src_code = src_code.replace('APP_ID        = "noid"', f'APP_ID        = "{app_id}"')

    #src_code = src_code.replace('#<DATAPOINTS_LENGTH/>',    f'{len(datapoints)},')

    ws = WORKSPACE
    #if sys.platform == "win32": ws = rf'{ws.replace('\\', '\\\\')}' #windows path fix...

    libimport_src = ''
    libimport_src += f"sys.path.append('{ws}') #Fix for parent folder import embed_lib\n"
    
    for rec in libimport_list:  libimport_src += f'{rec}\n'

    src_code = src_code.replace('#<LIBIMPORT/>', libimport_src)    

    return src_code


def check_bind(blocks, f_id, io_indx):
    for block in blocks:
        for io in block.io:
            if io['bind'] != {}:
                if f_id == io['bind']['bind_id'] and io_indx == io['bind']['bind_io_index']:
                    return True
            
    return False


#***** Datapoints *****
def build_datapoints(app_id, src_code, datapoints: list[datapoints_rec]):
    #inject_code_load = '\n'
    inject_code_list = ''
    inject_code_save = ''

    for dp in datapoints: 
        inject_code_list += f"        datapoints_runtime_rec(id='{app_id}_{dp.group}_{dp.name}', app_id='{app_id}', dp_id='{dp.id}', datatype='{dp.datatype}', "
        inject_code_list += f"value=((await application_db.get_record(datapoints_rec, datapoints_rec.id, {dp.id})).value)"
        inject_code_list += f"), #{dp.group}/{dp.name}\n"

        inject_code_save += "       {"
        inject_code_save += f"'id': {dp.id}, 'value': str(await get_data_run('{app_id}_{dp.group}_{dp.name}'))"
        inject_code_save += "},\n"

    src_code = src_code.replace('        #<DATAPOINTS_DEF/>',  inject_code_list) #Load
    src_code = src_code.replace('        #<DATAPOINTS_SAVE/>', inject_code_save) #Save
    return src_code    


def build_net_datapoints(app_id, src_code, datapoints: list[datapoints_rec]):
    inject_code_init = ""
    inject_code_ids  = ""

    for dp in datapoints:
        decode_conn = connect_id_decode_jsn(dp.protocol['connector_id'])
        if decode_conn == None: continue

        key_conn = dp.protocol['connector_id'] #connect_id_gen_jsn(dp.protocol) #f"{dp.protocol['src']}[{dp.protocol['net']}]:({dp.protocol['device_id']}):,{dp.protocol['object_id']}"
        key_dp   = f"{app_id}_{dp.group}_{dp.name}"

        id_inj_jsn = {"dp_id": key_dp, "conn_id": key_conn, "protocol": decode_conn['src'], "bind": {}}
        
        #    #{'connector_id': 'BACnet_IP[6630:3]:877003,device,877003', 'src': 'BACnet_IP', 'net': '6630:3', 
        #    # 'device_id': '877003', 'object_id': 'device,877003', 'device_name': 'VAV T4RT', 'object_name': '', 
        #    # 'bac_read_enable': True, 'bac_property': 'objectName', 'bac_read_refresh': 10}            
        
        id_inj_jsn['bind']['app_id'] = app_id
        if decode_conn['src'] == 'BACnet_IP':
            id_inj_jsn['bind']['bac_read_enable']   =  dp.protocol['bac_read_enable'] 
            id_inj_jsn['bind']['bac_property']      =  dp.protocol['bac_property']    
            id_inj_jsn['bind']['bac_read_refresh']  =  dp.protocol['bac_read_refresh']
            id_inj_jsn['bind']['bac_read_left']     =  dp.protocol['bac_read_refresh']

        inject_code_ids  += f"""        {id_inj_jsn},\n"""

        inject_code_init += f"""
        connector_rec(
            id           =  "{key_conn}",
            src          =  "{decode_conn['src']}",
            net          =  "{decode_conn['net']}",
            device_id    =  "{decode_conn['device_id']}",
            device_name  =  "",
            object_id    =  "{decode_conn['object_id']}",
            object_name  =  "",
            value        =  "",
            online       =  False,
            last_updated =  datetime.now(),
            properties   =  {{}},
            binds        =  [],
        ),"""

    src_code = src_code.replace('        #<DATAPOINTS_NET_INIT/>',       inject_code_init) #init
    src_code = src_code.replace('        #<DATAPOINTS_NET_IDS_INIT/>',   inject_code_ids) #init ids

    return src_code    


def build_gets(app_id, src_code, blocks: list[logic_rec], binds: list[logic_rec], datapoints: list[datapoints_rec], g_list: list[logic_rec], cons_list: list[logic_rec]): 
    inject_code = ''

    for g_rec in g_list:
        binded = check_bind(blocks, g_rec.id, 0)
        if not binded: continue
        bnd = f'bind_{g_rec.id}_0'
        binds.append(bnd)

        for dp in datapoints:
            if f'{dp.group}:{dp.name}' == f'{g_rec.name}':
                inject_code += f"            {bnd} = await get_data_run('{app_id}_{dp.group}_{dp.name}')\n"

    for c_rec in cons_list:
        binded = check_bind(blocks, c_rec.id, 0)
        if not binded: continue
        bnd = f'bind_{c_rec.id}_0'
        binds.append(bnd)
        inject_code += f'            {bnd} = {c_rec.io[0]['value']}\n'

    src_code = src_code.replace('            #<GETTERS_CODE/>',          inject_code) #Define Defaults
    return src_code, binds  


def build_sets(app_id, src_code, datapoints: list[datapoints_rec], s_list):
    inject_code = ''

    for s_rec in s_list:
        for dp in datapoints:
            if s_rec.io[0]['bind'] != {} and f'{dp.group}:{dp.name}' == f'{s_rec.name}':
                bnd = f"bind_{s_rec.io[0]['bind']['bind_id']}_{s_rec.io[0]['bind']['bind_io_index']}" #find_bind(b_list, s_rec.io[0]['bind']['bind_id'], s_rec.io[0]['bind']['bind_io_index'])
                inject_code += '                {'
                inject_code += f"'data_id': '{app_id}_{dp.group}_{dp.name}', 'value': {bnd}"
                inject_code += '}, \n'
                
    src_code = src_code.replace('                #<SETTERS_CODE/>',          inject_code) #Define Defaults    
    return src_code  


def build_blocks(app_id, src_code, blocks: list[logic_rec], binds: list[logic_rec]):
    inject_code = ''
    blocks_sorted: list[logic_rec] = []

    antiloop = len(blocks) #antiloop is used to avoid the cases when block can not be filtered, when something is not binded to input 
    loop_count = 0

    while len(blocks) > 0 and antiloop > 0:
        antiloop   -= 1
        loop_count += 1

        for blk in blocks[:]:      #[:] makes shadow copy of array
            inputs_count    = 0
            inputs_binded   = 0    #binded to existing binds
            potential_binds = []   #Potential binds if success

            for io_index, io_rec in enumerate(blk.io):
                match io_rec['type']:
                    case 'input':
                        inputs_count += 1
                        if io_rec['bind'] != {} and f'bind_{io_rec['bind']['bind_id']}_{io_rec['bind']['bind_io_index']}' in binds:  
                            inputs_binded += 1                    
                    case 'output':
                        potential_binds.append(f'bind_{blk.id}_{io_index}')
                    case _: print('Err, unknown input/output type')

            if inputs_count == inputs_binded: #add new potential bind
                binds.extend(potential_binds)
                blocks_sorted.append(blk)
                blocks.remove(blk)

    print(f">>> Block Sorted in {loop_count} loops: sorted {len(blocks_sorted)}, not sorted {len(blocks)}" )

    for b_rec in blocks_sorted:
        code = b_rec.function
        out_code = ''
        outputs_exists = False

        for io_index, io_rec in  enumerate(b_rec.io):
            match io_rec['type']:
                case 'input':
                    if io_rec['bind'] != {}:
                        bnd = f"bind_{io_rec['bind']['bind_id']}_{io_rec['bind']['bind_io_index']}"                         
                        code_splt = code.split( "(" ) #Make sure that we replace only in (var1, var2 ...)
                        code_splt[1] = code_splt[1].replace(io_rec['id'], bnd)  
                        code = f"{code_splt[0]}({code_splt[1]}" 
                case 'output':
                    bnd = f"bind_{b_rec.id}_{io_index}" 
                    outputs_exists = True
                    if out_code == '': out_code += bnd
                    else:              out_code += f', {bnd}'
                case _:  print('Err, unknown input/output type')

        if outputs_exists: code = f'{out_code} = {code}' #if outputs exists
        else:              code = f'{code}' #Block WO outputs

        inject_code += f'            {code}\n'

    src_code = src_code.replace('            #<BLOCK_CODE/>',          inject_code) #Define Defaults
    return src_code, binds

def build_binds(app_id, src_code, binds: list[logic_rec]): #Optional, onlyc creates record in virt db
    inject_bind_def  = ''
    inject_bind_code = ''

    for bnd in binds:
        inject_bind_def += f"        datapoints_runtime_rec(id='#{app_id}_{bnd}#', app_id='{app_id}', dp_id='-1', datatype='str', "
        inject_bind_def += f"value=str(None)"
        inject_bind_def += f"),\n"

        inject_bind_code += '                {'
        inject_bind_code += f"'data_id': '#{app_id}_{bnd}#', 'value': {bnd}"
        inject_bind_code += '}, \n'

    src_code = src_code.replace('        #<BINDS_DEF/>',           inject_bind_def)
    src_code = src_code.replace('                #<BINDS_CODE/>',  inject_bind_code)

    return src_code


def build_trends(app_id, src_code, datapoints: list[datapoints_rec]):
    inject_code_def = ''

    for dp in datapoints:
        if dp.trend['enable'] == True:
            name = f"{dp.group}_{dp.name}"
            inject_code_def += f'        {{"name": "{name}", "datapoint": "{app_id}_{dp.group}_{dp.name}", "refresh": {dp.trend["refresh"]}, "left": {dp.trend["refresh"]}, "datatype": "{dp.datatype}", "old_value": None }}, \n'

    src_code = src_code.replace('        #<TRENDS_INIT>',          inject_code_def) #Init Trends
    return src_code  


#***** SORT BLOCKS *****
def sort_blocks(blocks: list[logic_rec]):
    getter_list    : list[logic_rec] = []
    setter_list    : list[logic_rec] = []
    constant_list  : list[logic_rec] = []
    block_list     : list[logic_rec] = []
    import_list                      = []

    #bind_list                        = [] #{f_id, io, }
    #ordered_blocks                   = []

    #sort blocks by type
    for blk in blocks:
        match blk.type:
            case 'datapoint-set': setter_list.append(blk)
            case 'datapoint-get': getter_list.append(blk)
            case 'constant':      constant_list.append(blk)
            case _:               block_list.append(blk)

#Import List
    for blk in block_list:
        if blk.libimport not in import_list:
            import_list.append(blk.libimport)

    print(f">>>> App Statistics <<<<"   )
    print(f"    gets   = {len(getter_list)}"   )
    print(f"    sets   = {len(setter_list)}"   )
    print(f"    const  = {len(constant_list)}" )
    print(f"    blocks = {len(block_list)}\n"  )

    return import_list, getter_list, setter_list, constant_list, block_list


#***** Manage APP *****
async def run_app(app):
    global PYTHON_SYS

    print(f'>>>> Launching {app} <<<<')

    if PYTHON_SYS == "": init_settings()
    
    APP_EXE  = Path(f'{APPS_FOLDER}/{app}/app_main.py')
    if (not os.path.isfile(APP_EXE)):
        error_text = f"{app} Error: App was not build yet"
        await print_app_event(error_text)
        return { 'result': 'error', "error_text": error_text} 

    sub_proc = None
    if __debug__:
        sub_proc = await asyncio.create_subprocess_exec(  
            PYTHON_SYS, APP_EXE,             
            stdout = None, stderr = None #,   #None for std note when none it outputs in console may be useful
        ) 
    else:
        sub_proc = await asyncio.create_subprocess_exec(  
            PYTHON_SYS, '-O', APP_EXE,             
            stdout = None, stderr = None, #start_new_session=True
        ) 

    await print_app_event(f'{app} Started: {sub_proc}' )

    await asyncio.sleep(2) #without it app may be not init correctly not elegant

    #Register DP Mapping in drivers
    #dp = await load_datapoints(app)

    #FIX it

    #LoRaWAN
    #bind_count = add_app_loraWAN_sync(app, dp)
    #print(f'LoRaWAN Data Binded: {bind_count} / ({len(dp)})')

    #BACnet
    #bind_count = await add_app_BACnet_sync(app, dp)
    #print(f'BACnet Data Binded: {bind_count} / ({len(dp)})')

    print(f'>>>> {app} Ready <<<<')

    return { 'result': 'ok' }, 
    

async def get_app_status(app_id): 
    return await app_status({ 'app_id': app_id })


async def stop_app(app_id):
    print(f'>>>> Terminating {app_id} <<<< ')

    #FIX it
    
    #bind_count = free_app_loraWAN_sync(app)
    #print(f'LoRaWAN Bindings Cleared: {bind_count}')

    #bind_count = free_app_BACnet_sync(app)
    #print(f'BACnet Bindings Cleared: {bind_count}')

    await set_data_run(f"#{app_id}_status#", False)
    await print_app_event(f'>>>> {app_id} Stopped <<<<')


