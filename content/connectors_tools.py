import ujson

from lib.database_sql.server_virt_model import server_virt_db, connector_rec, connector_task


from content.users import check_permissions

async def update(content):
    return await server_virt_db.get_all_records(connector_rec, to_json=True)


async def connectors_list(content):
    conns = []

    recs:list[connector_rec] = await server_virt_db.get_all_records(connector_rec)
    for rec in recs:
        conns.append( { "name": f"{rec.device_name} - {rec.object_name}", "value": f"{rec.id}", "item": {
            "src"        : rec.src,
            "net"        : rec.net,
            "device_name": rec.device_name,
            "device_id"  : rec.device_id,
            "object_name": rec.object_name,
            "object_id"  : rec.object_id
        } } )

    return conns


async def add_task(content):   
    tsks = []
    [ tsks.append(connector_task(
        src   = cmd['src'],
        cmd   = cmd['cmd'],
        params= cmd['params'],
    )) for cmd in content ]    
    await server_virt_db.add_records(tsks)

    return  { 'result': 'ok', } 


COMMANDS_DICT = {
    'add_task'         : add_task,           'perm_add_task'          : 'developer, ', 
    'update'           : update,             'perm_update'            : 'developer, ', 
    'connectors_list'  : connectors_list,    'perm_connectors_list'   : 'developer, ', 
}


#DEFAULT
async def default_msg(content):
    print('Request Error connector_mng: ' + str(content))
    return {"result": "error", "error_text": "connector_mng command not found"}


async def connectors_mng(auth, cmd, content):
    content_json = ujson.loads( content )

    if check_permissions(auth, COMMANDS_DICT['perm_' + cmd]):
        return await COMMANDS_DICT.get(cmd, default_msg)(content_json)
    else:
        return { "result": "error", "error_text": f"Permission denied for user '{auth['user']}' accessing '{cmd}'" }
