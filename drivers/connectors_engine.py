from system.settings_server import settings_cfg
from lib.database_sql.server_virt_model import server_virt_db, connector_rec, connector_task

#Drivers
from drivers.bacnet_server         import bacnet_server
from drivers.mqtt_client           import mqtt_client
from drivers.mqtt_broker           import mqtt_broker


bacnet_serv      = None
mqtt_client_serv = None
mqtt_broker_serv = None

class CE_SRC():
    BACnet_IP      = "BACnet_IP"
    MQTT_Client    = "MQTT_Client"
    MQTT_Broker    = "MQTT_Broker"
    

async def ce_initialize():
    global bacnet_serv, mile_http_serv, mqtt_client_serv, mqtt_broker_serv

    #settings: settings_cfg
    print('Initializing Connectors Engine')

    settings = settings_cfg()
    settings.read_settings()

    if settings.bacnet_server['net_autostart']:
        bacnet_serv = bacnet_server()
        await bacnet_serv.init_service( settings.bacnet_server )
        
    if settings.mqtt_client_server['net_autostart']:
        mqtt_client_serv = mqtt_client()
        await mqtt_client_serv.init_service( settings.mqtt_client_server )        

    if settings.mqtt_broker_server['net_autostart']:
        mqtt_broker_serv = mqtt_broker() 
        await mqtt_broker_serv.init_service( settings.mqtt_broker_server )


    #Test task
    #await ce_add_task(CE_SRC.BACnet_IP, 'test', {"msg": "test bacnet msg"})


async def ce_terminate():
    global bacnet_serv, mile_http_serv, mqtt_client_serv, mqtt_broker_serv

    print('Terminating Connectors Engine')

    if not bacnet_serv      == None:  await bacnet_serv     .terminate_service()
    if not mqtt_client_serv == None:  await mqtt_client_serv.terminate_service()
    if not mqtt_broker_serv == None:  await mqtt_broker_serv.terminate_service()


async def ce_add_task(src, cmd, params):
    await server_virt_db.add_record(connector_task(
        cmd    = cmd,
        src    = src,
        params = params,
    ))


async def ce_add_tasks(tasks):
    new_tasks = []

    [new_tasks.append( connector_task(
        cmd    = tsk['cmd'] ,
        src    = tsk['src'],
        params = tsk['params'] ,
    )) for tsk in tasks]

    await server_virt_db.add_records(new_tasks)


async def clean_all_tasks():
    await server_virt_db.delete_all_records(connector_task)

