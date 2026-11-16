import threading
import ujson
import asyncio
from   datetime import datetime

from content.logger         import print_log_bacnet
from drivers.drivers_tools import connect_id_gen, connect_id_gen_jsn, connect_id_decode

from lib.database_sql.server_virt_model import server_virt_db, connector_rec, connector_task

from bacpypes3.debugging import bacpypes_debugging, ModuleLogger
from bacpypes3.argparse import SimpleArgumentParser
from bacpypes3.app import Application
from bacpypes3.pdu import Address, LocalBroadcast, RemoteBroadcast, GlobalBroadcast
from bacpypes3.primitivedata import Unsigned, ObjectIdentifier, PropertyIdentifier
from bacpypes3.errors import MissingRequiredParameter
from bacpypes3.constructeddata import AnyAtomic
from bacpypes3.apdu import ErrorRejectAbortNack

#import bacpypes3.object import AnalogValueObject
#import bacpypes3.object as _client_object

#from bacpypes3.object        import Object as _client_object
#from bacpypes3.local.object  import Object as _server_object


class device_properties:
    def __init__(self, net="", device_id=-1, device_name="", segment_rx=False, segment_tx=False, object_list_size=0):
        self.net         = net #ip dress, mac and etc
        self.device_id   = device_id
        self.device_name = device_name

        self.segment_rx  = segment_rx
        self.segment_tx  = segment_tx

        self.object_list_size = object_list_size
        self.object_list_read = 0
    

class bacnet_server():
    def __init__(self, *args):
        self.thrd = None
        self.debug           = False
        self.task_mng_sleep  = 1

        self.status          = False #status
        self.bacnet_app      = None
        self.settings        = []

        self.who_is_onstart  = False
        self.src             = "BACnet_IP"

        self.device_list: list[device_properties]  = [] #custom fields for BACnet driver only

        self.CMDS_DICT = {
            'who_is'                  : self.who_is,                 #low_limit = 0, high_limit = 4194303
            'clear_db'                : self.clear_db,             
            'sleep_bacnet'            : self.sleep_bacnet,
            'test'                    : self.test,

            'read_property'          : self.read_property,   
            #'read_property_multi'    : self.read_property_multi, 

            'read_properties_db'     : self.read_properties_db,      #Register in db, only from one property
            'read_device_list'       : self.read_device_list,        #Register in db
            
            #'write_property'         : self.write_property, 
        }       


    async def init_service(self, settings_adapter):
        #Set general settings
        self.task_mng_sleep = settings_adapter['task_mng_sleep']
        self.debug          = settings_adapter['debug']
        self.who_is_onstart = settings_adapter['whois_autostart']

        #Set adapter's settings
        settings_adapter['server'][0][1]["bacnet-ip-udp-port"] = settings_adapter['bip_port']
        settings_adapter['server'][0][1]["ip-address" ]        = settings_adapter['bip_ip']
        settings_adapter['server'][0][1]["ip-subnet-mask"]     = settings_adapter['bip_mask']
        settings_adapter['server'][0][1]["mac-address"]        = f"{settings_adapter['bip_ip']}:{settings_adapter['bip_port']}"

        self.settings = settings_adapter['server'][0]

        self.thrd = threading.Thread(target=self.__run_service, args=())
        self.thrd.start()


    def __run_service(self):
        asyncio.run( self.run_service(self.settings) )


    async def run_service(self, settings):
        await print_log_bacnet(f"BACnet Service Started: {settings[1]["mac-address"]}, {settings[0]["object-identifier"]}")

        #build BACnet application        
        self.bacnet_app = Application.from_json(settings)        
        self.bacnet_app.i_am()

        self.status = True
        
        if self.who_is_onstart: 
            await server_virt_db.add_records([
                connector_task(src=self.src, cmd='who_is',       params={}),
                #connector_task(src=self.src, cmd='sleep_bacnet', params={ 'time': 4 }),
            ])

        #await self.add_task({'cmd': 'test',       'params': { 'msg': 'hello' }})


        while self.status:  #BACnet task manager Loop
            try: 
                tsk: connector_task = await server_virt_db.get_record(connector_task, connector_task.src, self.src)               

                if tsk != None:
                    if self.debug:  print(f"Executing Command {tsk.src}: {tsk.cmd} = {tsk.params}")
                    await server_virt_db.delete_record(connector_task, connector_task.id, tsk.id)
                    await self.CMDS_DICT.get(tsk.cmd, self.cmd_error)(tsk.params) #default_msg
                    
            except ErrorRejectAbortNack as ex:
                print(f"Err1, BACnet: {ex}")
            except Exception as ex:  
                print(f"Err10, BACnet: {ex}")
            except OSError as ex:
                print(f"Err11, BACnet: {ex}") 
            except:
                print(f"Err12, BACnet: Unknown error")
            finally:
                await asyncio.sleep(self.task_mng_sleep) 
                
        
        self.bacnet_app.close()
        await print_log_bacnet("BACnet Service Terminated")

    async def terminate_service(self):
        self.status = False
        await server_virt_db.delete_records_recursively(connector_task, connector_task.src, self.src)


    def find_device(self, net_addr: str)->device_properties:
        for dev in self.device_list:
            if net_addr == dev.net:
                return dev
            
        return None


    #async def add_task(self, cmd, params):
    #    self.tasks.append({'cmd': cmd, 'params': params})


    #async def add_tasks(self, cmds):
    #    self.tasks.extend(cmds) #add list [{cmd, params}, ...]

    async def clear_db(self, params):
        await server_virt_db.delete_records_recursively(connector_task, connector_task.src, self.src)


    async def sleep_bacnet (self, cmds):
        await asyncio.sleep(cmds['time'])


    async def test(self, cmds):
        print(str(self.device_list))
        print_log_bacnet(f'************ BACnet Server Test: {cmds['msg']} ******** ')


    async def cmd_error(self, params):
        print(f'BACnet CMD Error: not found {params}')
        return {"result": "error", "error_text": "app_ide_mng command not found"}       


    async def who_is(self, params): #//low_limit = 0, high_limit = 4194303
        if 'low_limit' in params and 'high_limit' in params:
            low_limit  = params['low_limit']
            high_limit = params['high_limit']
        else:
            low_limit = 0
            high_limit = 4194303
            
        i_ams = await self.bacnet_app.who_is(low_limit, high_limit)

#        devices = get_devices()

        for i_am in i_ams:  
            device_instance = i_am.iAmDeviceIdentifier[1]
            device_address  = i_am.pduSource

            if self.debug: print(f"BACnet who_is device found: {device_instance} - {device_address}") #1100 - 192.168.1.100
            
            net         = f"{device_address}"
            name        = ""
            #description = ""
            #location    = ""
            list_size   = 0

            segment_rx  = False
            segment_tx  = False

            dev: device_properties = self.find_device(net)
            
        #Get Device Info
            try:    name = await self.read_property({'net': net, 'object': f'device, {device_instance}', 'property': 'object-name'})
            except: print(f"Failed to get device {device_address} name")

            #try:    description = await self.read_property({'net': net, 'object': f'device, {device_instance}', 'property': 'description'})
            #except: print(f"Failed to get device {device_address} desciption")
            #
            #try:    location = await self.read_property({'net': net, 'object': f'device, {device_instance}', 'property': 'location'})
            #except: print(f"Failed to get device {device_address} location")

            try:    
                segment = await self.read_property({'net': net, 'object': f'device, {device_instance}', 'property': 'segmentation-supported'})
                match segment:
                    case 0:
                        segment_rx  = True
                        segment_tx  = True
                    case 1:
                        segment_rx  = False
                        segment_tx  = True
                    case 2:
                        segment_rx  = True
                        segment_tx  = False
                    case 3:
                        segment_rx  = False
                        segment_tx  = False
            except: print(f"Failed to get device {device_address} segmentation")            

            try:    list_size = await self.read_property({'net': net, 'object': f'device, {device_instance}', 'property': 'object-list', 'index': 0})
            except: print(f"Failed to get device {device_address} list_size")
    
            if dev == None:
                self.device_list.append( device_properties(
                   net              = f"{device_address}",
                   device_id        = device_instance,
                   device_name      = name,
                   segment_rx       = segment_rx,
                   segment_tx       = segment_tx,
                   object_list_size = list_size,
                ) )

                new_conn = connector_rec(
                    id          = connect_id_gen(self.src, device_address, device_instance, f"device,{device_instance}"),
                    src         = self.src, 
                    net         = f"{device_address}",
                    device_id   = f"{device_instance}",
                    device_name = name, 
                    object_id   = f"device,{device_instance}",
                    object_name = "", 
                    value       = "",
                    online      = True,
                    last_updated = datetime.now(),
                    properties  = {},
                    binds       = [],
                )

                await server_virt_db.update_records_with_autocreate([new_conn], connector_rec.id)    


    async def read_property(self, params): #net, obj type, obj id, array opt
        #params = {'net': '192.168.1.160:47808', 'object': 'analog-input, 12', 'property': 'presentValue', 'index': 0}

        device_net  = Address           (params["net"])
        object      = ObjectIdentifier  (params["object"])
        property    = PropertyIdentifier(params["property"])
        
        array_index = None
        if 'index' in params: array_index = params["index"]
        
        value = await self.bacnet_app.read_property(device_net, object, property, array_index = array_index )   
        
        if self.debug:  print(f"Property Read: {device_net}: {object}, {property} = {value}")

        return value


    async def read_property_db(self, params): #net, obj type, obj id, array opt
        #params = {'net': '192.168.1.160:47808', 'object': 'analog-input, 12', 'property': 'presentValue', 'index': 0}

        value = self.read_property(params)
        print('***************not implemented yet')
        return value


    async def read_property_multi(self, params): #Register object/property in database
        #'cmd': 'read_property_multi_db', 
        #'params': { 'net' : device.net,  'requests'  : [
        #    'analog-input, 1', ['presentValue', 'objectName'],
        #    'analog-input, 2', ['presentValue']
        #] }         
   
        values = await self.bacnet_app.read_property_multiple(params["net"], params["requests"])

        if self.debug:
            for obj in values:
                print(f'multi req obj/prp [indx?] = value: {obj[0]} / {obj[1]} [{obj[2]}] = {obj[3]}')
        
        return values   


    async def read_properties_db(self, params): #Register object/property in database, multi properties for one object only!
        src, dev_net, dev_id, obj_id = connect_id_decode(params["id"]) #src and dev_id not used

        req_params = { 'net' : dev_net, 'requests'  : [ obj_id, params['requests'] ]}
        values = await self.read_property_multi(req_params)
        
        #analog-input,5 / object-name [None] = MAC1 UIUO\MAC1 - UI5
        # 0                   1          2        3

        obj_exists = await server_virt_db.get_record(connector_rec, connector_rec.id, params['id'])
        update_fields = {}        
        update_fields['properties'] = {}

        for obj in values:
            key = str(obj[1])

            match key:
                case "object-name":   update_fields['object_name'] = str(obj[3])
                case "present-value": update_fields['value']       = str(obj[3])

            update_fields['properties'][str(obj[1])] = str(obj[3])

        if update_fields == {}: return

        update_fields['online']       = True
        update_fields['last_updated'] = datetime.now()

        if obj_exists != None:
            await server_virt_db.update_fields(connector_rec, connector_rec.id, params['id'], update_fields)
        else:
            print("**************************** ERRPR OBJECT DOES NOT EXIST MAKE AUTOCREATE!!!")            


    async def read_device_list(self, params): #Register object/property in database
        #'cmd': 'read_device_list', 
        #'params': { 'net': device.net, 
        #'object': `device, 1`, 'property': 'prop',  'index': i }

        dev: device_properties = self.find_device(params['net'])        
        if dev == None: return
        
        obj_list = []
        dev.object_list_read = 0

        if dev.segment_rx:
            obj_list = await self.read_property({
                'net'     : params['net'], 
                'object'  : f'device,{dev.device_id}', 
                'property': 'object-list', #'index': 0
            }) #ObjectIdentifier Type
            dev.object_list_read = len(obj_list)
        else:
            for indx in range(dev.object_list_size):
                obj_list.append( await self.read_property({
                    'net'     : params['net'], 
                    'object'  : f'device,{dev.device_id}', 
                    'property': 'object-list', 'index': indx + 1
                }))
                dev.object_list_read += 1

        if self.debug: print(f"Object List Read?: {dev.device_id} - {dev.object_list_read} / {dev.object_list_size}")

        for obj in obj_list:           
            new_id = connect_id_gen(self.src, params['net'], dev.device_id, str(obj))
            obj_exists = await server_virt_db.get_record(connector_rec, connector_rec.id, new_id)
            if obj_exists == None:
                try:
                    await server_virt_db.add_record( connector_rec( 
                        id           = new_id, 
                        src          = self.src, 
                        net          = f"{params['net']}",
                        device_id    = f"{dev.device_id}",
                        device_name  = f"{dev.device_name}",
                        object_id    = f"{obj}",
                        object_name  = "",
                        value        = "",
                        online       = True,
                        last_updated = datetime.now(),
                        properties   = {},
                        binds        = [],
                    ) )
                except Exception as ex: print(f"Failed to add new object to database when readong object list {new_id}: {ex} ")
            else:
                update_fields = {}  
                update_fields['device_name'] = f"{dev.device_name}"
                await server_virt_db.update_fields(connector_rec, connector_rec.id, obj_exists.id, update_fields)

