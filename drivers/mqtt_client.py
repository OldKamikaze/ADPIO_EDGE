import threading
import ujson
import asyncio
from   datetime import datetime

from drivers.drivers_tools import connect_id_gen

#required dacite and transitions
from amqtt.client import MQTTClient, ClientError
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2
 
from content.logger    import print_log_mqtt

from lib.database_sql.server_virt_model import server_virt_db, connector_rec, connector_task


class mqtt_client:
    def __init__(self):
        self.src        = "MQTT_Client"    
        self.debug      = False
        self.status     = False

        self.port       = 1883
        self.broker     = "broker.emqx.io"
        self.keepalive  = 60

        self.topics     = ["home/sensor/temperature"]

        self.thrd = None


    def get_QOS(self, q_indx):
        match q_indx:
            case 0: return QOS_0
            case 1: return QOS_1
            case 2: return QOS_2
            case _:
                print("QOS ERROR")
                return False


    def __run_service(self):
        asyncio.run( self.run_service() )


    async def run_service(self):
        self.status = True

        clnt_mqtt = MQTTClient( config={
            "auto_reconnect": False,
            "keep_alive"    : self.keepalive,
        } ) #client_id

        uri = f"mqtt://{self.broker}:{self.port}"
        try:
            sts = await clnt_mqtt.connect( uri )
            await print_log_mqtt (f"MQTT Client Connected: {uri} - {sts}")
        except  ClientError as ex:
            await print_log_mqtt (f"MQTT Client Failed To Connect: {uri} - {ex}")
            return

        try:#topic, QOS_x
            await clnt_mqtt.subscribe( [(topic[0], self.get_QOS(topic[1])) for topic in self.topics] )
        except  ClientError as ex:
            await print_log_mqtt (f"MQTT Client Failed To Subscribe: {uri} - {ex}")
            return

        while self.status:
            try:
                if msg := await clnt_mqtt.deliver_message():
                    msg_str = msg.data.decode()
                    tpc = msg.topic

                    if not ("{" in msg_str and "}" in msg_str):
                        if self.debug: print(f'MQTT Client not a json - skip: {tpc} = {msg_str}')
                        continue

                    jsn = ujson.loads( msg_str )
                   
                    if self.debug: print(f"MQTT Client Sub Msg: {tpc}: {jsn}")

                    if "devEUI"     in jsn: rec_dev_id = jsn['devEUI']
                    else:                   rec_dev_id = tpc

                    if "deviceName" in jsn: rec_dev_name = jsn['deviceName']
                    else:                   rec_dev_name = tpc

                    connectors_list = []
                    [connectors_list.append(connector_rec(
                        id           =  connect_id_gen(self.src, self.broker, rec_dev_id, key),
                        src          =  self.src,
                        net          =  self.broker,
                        device_id    =  rec_dev_id,
                        device_name  =  rec_dev_name,
                        object_id    =  key,
                        object_name  =  key.replace('_', ' '),
                        value        =  jsn[key],
                        online       =  True,
                        last_updated =  datetime.now(),
                        binds        =  [],
                    )) for key in list(jsn.keys())]
                    await server_virt_db.update_records_with_autocreate(connectors_list, connector_rec.id)

            except ClientError as ex:
                await print_log_mqtt(f"MQTT Client MSG Error: {ex}") 

        await clnt_mqtt.unsubscribe( [topic[0] for topic in self.topics] )
        await clnt_mqtt.disconnect()

        await print_log_mqtt("MQTT Client Service Terminated") 


    async def init_service(self, settings_adapter):
        await print_log_mqtt("MQTT Client Initializing") 

        self.debug      = settings_adapter['debug']
        self.port       = settings_adapter['port']
        self.broker     = settings_adapter['broker']
        self.keepalive  = settings_adapter['keepalive']
        self.topics     = settings_adapter['topics']

        self.thrd = threading.Thread(target=self.__run_service, args=())
        self.thrd.start()        


    async def terminate_service(self):
        self.status = False
        await server_virt_db.delete_records_recursively(connector_task, connector_task.src, self.src)

        
        