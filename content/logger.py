import ujson

from lib.database_sql.workspace_model import workspace_db, logs_rec
from lib.terminal                     import terminal_rec, terminal_web
from content.users import check_permissions

__MAX_LEN = 2044


async def update(content):
    try:
        return await workspace_db.get_all_records(logs_rec, to_json=True, order_by_desc=logs_rec.date, limit=1200)
    except  Exception as ex:
        print(str(ex))
        return  {"result": "error", "error_text": f"Failed update logs... ({ex})"}


async def clear_all(content):
    try:
        await workspace_db.delete_all_records(logs_rec)
        return { "result": "ok", } 
    except  Exception as ex:
        print(str(ex))
        return  {"result": "error", "error_text": f"Failed to delete all logs... ({ex})"}    


async def print_log_system(txt):
    """global last_records_info

    if txt not in last_records_info:
        last_records_info.insert(0, txt)
        if len( last_records_info ) > __max_back_log:
            last_records_info.pop(__max_back_log)
    """

    #txt_trim = txt
    #if (len(txt) > __MAX_LEN):
    #    txt_trim = txt[:__MAX_LEN] + '...'

    await workspace_db.add_record( logs_rec (type='system', text=txt[:__MAX_LEN]) )
    
    print( f'System: {txt}' )
    return {'system' : txt}


async def print_log_error(txt):
    await workspace_db.add_record( logs_rec (type='error', text=txt[:__MAX_LEN]) )
    
    print( f'Error: {txt}' )
    return {'error' : txt}


async def print_log_lora(txt):
    await workspace_db.add_record( logs_rec (type='LoRaWAN', text=txt[:__MAX_LEN]) )
    
    print( f'LoRaWAN: {txt}' )
    return {'LoRaWAN' : txt}



async def print_log_mqtt(txt):
    await workspace_db.add_record( logs_rec (type='MQTT', text=txt[:__MAX_LEN]) )
    
    print( f'MQTT: {txt}' )
    return {'MQTT' : txt}



async def print_log_bacnet(txt):    
    await workspace_db.add_record( logs_rec (type='BACnet', text=txt[:__MAX_LEN]) )
    
    print( f'BACnet: {txt}' )
    return {'BACnet' : txt}


async def print_app_event(txt):
    await workspace_db.add_record( logs_rec (type='APPS', text=txt[:__MAX_LEN]) )
    
    print( f'APPS: {txt}' )
    return {'APPS' : txt}


async def show_logs(content):
    try:
        return {'content':  await terminal_web.database.get_all_records(terminal_rec, limit=256, to_json=True) }
    except Exception as ex:
        return {"content": [{"date": "0", "rec_src": "system", "text": f"Failed to get terminal records... ({ex})"}] }
         

async def clear_logs(content):
    try:
        await terminal_web.database.delete_all_records(terminal_rec)
        return []
    except Exception as ex:
       return  {"result": "error", "error_text": f"Failed to clear terminal... ({ex})"}    


COMMANDS_DICT = {
    'update'    : update,    'perm_update'       : 'developer, user, view, ', #Note: This on is DB records, controled by server
    'clear_all' : clear_all, 'perm_clear_all'    : 'developer, ',

    'show_logs' : show_logs,  'perm_show_logs'   : 'developer, ',             #Logs from console, python errors
    'clear_logs': clear_logs, 'perm_clear_logs'  : 'developer, ',
}


#DEFAULT
async def default_msg(content):
    print('Request Error log_task_mng: ' + str(content))
    return {"result": "error", "error_text": "log_task_mng command not found"}


async def log_task_mng(auth, cmd, content):
    content_json = ujson.loads( content )

    if check_permissions(auth, COMMANDS_DICT['perm_' + cmd]):
        return await COMMANDS_DICT.get(cmd, default_msg)(content_json)
    else:
        return { "result": "error", "error_text": f"Permission denied for user '{auth['user']}' accessing '{cmd}'" }
