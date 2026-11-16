import ujson

from lib.database_sql.server_virt_model import set_server_param, get_server_param, get_data_run, set_data_run, get_data_run_multi, set_data_run_multi

from content.users import check_permissions


async def app_status(content): 
    try:
        results = await get_data_run_multi([f"#{content['app_id']}_status#", f"#{content['app_id']}_loop#"])

        if (results[0] == None): return False, 0
        return results
    except:
        return False, 0


async def get_datapoints(content):
    try:
        return await get_data_run_multi(content['data_ids'])
    except:
        return  ["APP_STOPPED"] 


async def set_datapoints(content):
    print(content)
    try: #id, value
        await set_data_run_multi( content['data_ids'] )
        
        return {'result': 'ok'}
    except Exception as ex:
        return  {"result": "error", "error_text": "Failed to set value: " + str(ex)}


COMMANDS_DICT = {
    'app_status'    :  app_status,      'perm_app_status'     : 'developer, user, view, ',

    'get_datapoints':  get_datapoints,  'perm_get_datapoints' : 'developer, user, view, ',
    'set_datapoints':  set_datapoints,  'perm_set_datapoints'  : 'developer, user, ',
}

#DEFAULT
async def default_msg(content):
    print('Request Error app_view_mng: ' + str(content))

    return {"result": "error", "error_text": "app_view_mng command not found"}

async def app_view_mng(auth, cmd, content):
    content_json = ujson.loads( content )

    if check_permissions(auth, COMMANDS_DICT['perm_' + cmd]):
        return await COMMANDS_DICT.get(cmd, default_msg)(content_json)
    else:
        return { "result": "error", "error_text": f"Permission denied for user '{auth['user']}' accessing '{cmd}'" }
