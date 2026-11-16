import asyncio
import sys
from   datetime import datetime


#<LIBIMPORT/>

#DB
from lib.database_sql.sqlmodel_driver   import engine_db
from lib.database_sql.application_model import application_model, datapoints_rec, trend_rec
from lib.database_sql.server_virt_model import server_virt_db, get_server_param, get_data_run, set_data_run, set_data_run_multi, datapoints_runtime_rec, connector_rec, connector_task, SERVER_PARAMS

from lib.terminal       import terminal_web
from lib.dataconversion import str_to_dp, str_to_dp_datapoint

from lib.globals        import APPS_FOLDER


APP_ID        = "noid"
application_db: engine_db     = None     

async def trends_sync(trend_list, sleep):
    global application_db

    for tr in trend_list:
        try:
            tr["left"] -= sleep

            if tr["left"] <= 0:
                new_value = await get_data_run(tr['datapoint'])
                tr["left"] = tr["refresh"]  

                if tr["old_value"] != new_value:
                    tr["old_value"] = new_value
                    await application_db.add_record( trend_rec (
                        name     = tr['name'],
                        value    = str(new_value),
                        datatype = tr['datatype'],                
                    ) )
        except Exception as ex:
            print(f"Trend Log Event Error: {tr} - {ex}")

    return trend_list        


async def init_net_datapoints():
    net_id_map = [ #Init Network connectors registry
        #<DATAPOINTS_NET_IDS_INIT/>        
    ]

    connectors = [ #Make Connectors in virt mem
        #<DATAPOINTS_NET_INIT/>
    ]
    if connectors == []: pass

    await server_virt_db.update_records_with_autocreate(connectors, connector_rec.id)

    for mp in net_id_map: #add binds to connectors
        rec: connector_rec = await server_virt_db.get_record(connector_rec, connector_rec.id, mp['conn_id'])
        rec.binds.append( mp['bind'] )
        await server_virt_db.update_fields(connector_rec, connector_rec.id, mp['conn_id'], { "binds":  rec.binds })

    return net_id_map


async def term_net_datapoints(net_id_map): #clear binds
    for mp in net_id_map:
        rec: connector_rec = await server_virt_db.get_record(connector_rec, connector_rec.id, mp['conn_id'])
        try:
            for bnd in rec.binds:
                if bnd['app_id'] == APP_ID:
                    rec.binds.remove(bnd)
        finally:
            await server_virt_db.update_fields(connector_rec, connector_rec.id, mp['conn_id'], { "binds":  rec.binds })


async def net_datapoints_read_sync(net_id_map, sleep): #update connectors    
    for mp in net_id_map:
    #sync value with dp
        conn: connector_rec          = await server_virt_db.get_record(connector_rec,  connector_rec.id,  mp['conn_id'])
        if conn != None and conn.online:
            dp:   datapoints_runtime_rec = await server_virt_db.get_record(datapoints_runtime_rec, datapoints_runtime_rec.id, mp['dp_id'])  
            await set_data_run( mp['dp_id']  , str_to_dp(conn.value, dp.datatype) )

    #read task for BACnet
        if mp['protocol'] == 'BACnet_IP':
    #BACnet Read
            if not mp['bind']['bac_read_enable']: continue
            mp['bind']['bac_read_left'] -= sleep
            #print(f"bacnet: {mp['bind']['bac_read_left']}/{mp['bind']['bac_read_refresh']}") 

            if mp['bind']['bac_read_left'] <= 0:
                mp['bind']['bac_read_left'] = mp['bind']['bac_read_refresh']  
     
                await server_virt_db.add_record(connector_task(  
                    src   = 'BACnet_IP',
                    cmd   = 'read_properties_db',
                    params= { 'id': mp['conn_id'], 'requests': [ mp['bind']['bac_property'] ]}
                ))



async def net_datapoints_write_sync(net_id_map):
    #not yet implemented
    if net_id_map == []: pass


async def exec():
    global application_db

    SLEEP      = 1
    status     = True
    loop       = 0

    print(f'App {APP_ID} Initializing...\n')

    if await get_server_param(SERVER_PARAMS.GUI_TERMINAL):  
        terminal_web.initialize(f'app_{APP_ID}', await get_server_param(SERVER_PARAMS.TERMINAL_HDD_OUT))

#Shared Mems
    await server_virt_db.delete_records_recursively(datapoints_runtime_rec, datapoints_runtime_rec.app_id, APP_ID)
    await server_virt_db.add_records([
        datapoints_runtime_rec(id=f"#{APP_ID}_status#", app_id=APP_ID, datatype="bool", value=str(status)), 
        datapoints_runtime_rec(id=f"#{APP_ID}_loop#"  , app_id=APP_ID, datatype="int",  value=str(loop)),
        
        #<DATAPOINTS_DEF/>
        #<BINDS_DEF/>
    ])
    
#Net datapoints
    net_id_map = await init_net_datapoints()

#Trends
    trends = [
        #<TRENDS_INIT>
    ]

    print(f'APP {APP_ID} Started, Loop Delay: {SLEEP}\n')
    
    #await write_defaults(shared_mem) #Writed Defaults
    
    while status:
        try:
            if __debug__: print(f'{APP_ID}: status = {status}, loop = {loop}')

            loop += 1
            if loop >= 254: loop = 0
            status = await get_data_run(f"#{APP_ID}_status#")         
            await asyncio.sleep(SLEEP)

            await net_datapoints_read_sync(net_id_map, SLEEP)

    #Gets
            #<GETTERS_CODE/>

    #Code
            #<BLOCK_CODE/>

            await net_datapoints_write_sync(net_id_map)           

        except Exception as err:
            print(f'APP {APP_ID} Runtime Error : {err} \n')
        except:
            print(f'APP {APP_ID} Unnamed Error\n')
            await set_data_run(f"#{APP_ID}_status#"  , False)
        finally:
    #Sets
            await set_data_run_multi([
                {'data_id': f"#{APP_ID}_loop#", 'value': loop}, 

                #<SETTERS_CODE/>
                #<BINDS_CODE/>
            ])

    #Trends loop
            trends = await trends_sync(trends, SLEEP)                

    #Save values after exit
    await application_db.update_multi_fields(datapoints_rec, datapoints_rec.id, 'id', [
        #<DATAPOINTS_SAVE/>
    ])

    #Clear Memory
    await server_virt_db.delete_records_recursively(datapoints_runtime_rec, datapoints_runtime_rec.app_id, APP_ID)
    await term_net_datapoints(net_id_map )

    print(f'APP {APP_ID} Terminated.\n')
    if terminal_web.terminalIO != None: terminal_web.terminate()
    


if __name__ == "__main__":
    if __debug__: print("DEBUG For APPS is on. Run with -O to turn off debug\n")

    application_db = engine_db(f'sqlite:///{APPS_FOLDER}/{APP_ID}/application.db' , application_model)
    application_db.initialize()    
    server_virt_db.initialize()

    asyncio.run( exec() )    

    server_virt_db.terminate()
    application_db.terminate()

