import threading
import ujson
import asyncio
from   datetime import datetime

from drivers.drivers_tools import connect_id_gen, connect_id_gen_jsn

from amqtt.broker import Broker, CancelledError

from dataclasses import dataclass
from amqtt.plugins.base import BasePlugin
from amqtt.plugins.manager import BaseContext
from amqtt.session import ApplicationMessage, Session
from amqtt.plugins.base import BasePlugin
 
from content.logger    import print_log_mqtt

from lib.database_sql.server_virt_model import server_virt_db, connector_rec, connector_task


class IPAddressPlugin(BasePlugin):

    @dataclass
    class Config:
        debug: bool = False
        src  : str = "nosrc"


    async def on_broker_message_received(self, client_id: str, message: ApplicationMessage) -> None:
        try:
            src = self.config.src
            tpc = message.topic
            jsn = ujson.loads( message.data.decode('utf-8', errors='ignore') )

            if self.config.debug: print(f"MQTT Broker Recieve: {client_id}, {tpc} - {jsn}")
            #MQTT Broker Recieve: mile_gate, /ug65/up - {'applicationID': 2, 'devEUI': '24e124408f073237', 'deviceName': 'LORA Stat', 'humidity': 58, 'system_status': 1, 'temperature': 23.3}

            if "devEUI"     in jsn: rec_dev_id = jsn['devEUI']
            else:                   rec_dev_id = tpc

            if "deviceName" in jsn: rec_dev_name = jsn['deviceName']
            else:                   rec_dev_name = tpc

            connectors_list = []
            [connectors_list.append(connector_rec(
                id           =  connect_id_gen(src, client_id, rec_dev_id, key),
                src          =  src,
                net          =  client_id,
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

        except Exception as ex:
            await print_log_mqtt(f"MQTT Broker MSG Error: {ex}") 


class mqtt_broker:
    def __init__(self):
        self.src        = "MQTT_Broker"    
        self.debug      = False
        self.status     = False

        self.config = {}
            #"listeners": {
            #    "default": {
            #        "type": "tcp",
            #        "bind": "0.0.0.0:1883",
            #    },
            #},
            #"plugins": {
            #    "amqtt.plugins.authentication.AnonymousAuthPlugin": { "allow_anonymous": True},
            #    "amqtt.plugins.sys.broker.BrokerSysPlugin"        : { "sys_interval": 10},
            #    "drivers.mqtt_broker.IPAddressPlugin"             : { "debug":  self.debug, "src": self.src },
            #}
        
        self.thrd = None


    def __run_service(self):
        asyncio.run( self.run_service() )


    async def run_service(self):
        try:
            broker = Broker(self.config)
            self.status = True
        except Exception as ex:
            await print_log_mqtt(f"MQTT Broker Init Exception: {ex}") 

        await print_log_mqtt(f"MQTT Broker Status: {self.status}") 

        try:    
            await broker.start()
            while self.status: await asyncio.sleep(3)            
        except Exception as ex:
            await print_log_mqtt(f"MQTT Broker Exception: {ex}") 
            
        await broker.shutdown()
        await print_log_mqtt("MQTT Broker Service Terminated") 


    async def init_service(self, settings_adapter):
        await print_log_mqtt("MQTT Broker Initializing") 

        self.debug      = settings_adapter['debug']
        self.config     = settings_adapter['settings']
        self.config["plugins"] = {
            "amqtt.plugins.authentication.AnonymousAuthPlugin": { "allow_anonymous": True},
            "amqtt.plugins.sys.broker.BrokerSysPlugin"        : { "sys_interval"   : 10  },
            "drivers.mqtt_broker.IPAddressPlugin"             : { "debug":  self.debug, "src": self.src },
        }

        self.thrd = threading.Thread(target=self.__run_service, args=())
        self.thrd.start()        


    async def terminate_service(self):
        self.status = False
        await server_virt_db.delete_records_recursively(connector_task, connector_task.src, self.src)

        
        