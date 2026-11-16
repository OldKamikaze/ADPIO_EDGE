import ujson
import os
from shutil import rmtree
from pathlib import Path

#settings
from lib.globals import APPS_FOLDER

#DB
from lib.database_sql.workspace_model   import workspace_db, application_rec
from lib.database_sql.application_model import create_application, delete_application

#app exec
from system.app_engine import build_app, run_app, stop_app, get_app_status

from content.users import check_permissions


async def to_json(app_jsn):
    status, loop = await get_app_status( app_jsn['id'] ) 

    app_jsn['status']        = status
    app_jsn['selected_view'] = app_jsn['view_list'][0]['value'] #Set Default View

    return app_jsn


async def update_list(content):            
    try:
        return [ await to_json(app) for app in await workspace_db.get_all_records(application_rec, to_json=True) ]     
    except Exception as ex:
        print(str(ex))
        return  {"result": "error", "error_text": f"Failed to obtain app list: {ex}"}


async def get_app(content):
    try:
        app = await workspace_db.get_record(application_rec, application_rec.id, content['id'], to_json=True)
        return await to_json(app)
    except Exception as ex:
        return  {"result": "error", "error_text": "Failed to obtain app data: {ex}", "group": "err", "id": "err", "name": "err", "status": False}            
            
            
async def add_app(content):
    try:
        new_id = f"{content["group"]}_{content["name"]}"
        await workspace_db.add_record( application_rec(
            id            =  new_id ,
            name          =  content["name"],
            description   =  content["description"],
            group         =  content["group"],
            version       =  content["version"],
            autostart     =  content["autostart"],
            #t_created     =  content[""]
            #t_updated     =  content[""]
            #t_built       =  content[""]
            #view          =  content[""]
        ) )

        if ( not os.path.isdir(f"{APPS_FOLDER}/{new_id}" )):
            try:  os.mkdir(f"{APPS_FOLDER}/{new_id}")
            except OSError as error:  print(error)
        
        create_application(new_id)

        return  {"result": "ok"}
    except Exception as ex:
        print(str(ex))
        return  {"result": "error", "error_text": f"Failed to add new app: {ex}"}


async def save_app(content):
    try:              
        for rec in content: 
            old_id = rec['id']
            new_id = f"{rec["group"]}_{rec["name"]}"

            await workspace_db.update_record(
                application_rec(
                    id           = new_id ,
                    name         = rec['name'],
                    description  = rec['description'],
                    group        = rec['group'],
                    version      = rec['version'],
                    autostart    = rec['autostart'],
                    #t_created    = str(content.t_created),
                    #t_updated    = str(content.t_updated),
                    #t_built      = str(content.t_built), 
                ), application_rec.id, old_id )

            if old_id != new_id:
                if (os.path.isdir(f'{APPS_FOLDER}/{old_id}')):
                    try: await stop_app(old_id)
                    except OSError as error:  print(error)

                delete_application(old_id)
                os.rename(
                    f"{APPS_FOLDER}{Path(f'/{old_id}')}", 
                    f"{APPS_FOLDER}{Path(f'/{new_id}')}"
                )
                create_application(new_id)            

        return  {"result": "ok"}
    except  Exception as ex:
        print(str(ex))
        return  {"result": "error", "error_text": f"Failed to save app: {ex}"}


async def delete_app(content): 
    try:
        #stop app before delete
        if (os.path.isdir(f'{APPS_FOLDER}/{content['id']}')):
            try: await stop_app(content['id'])
            except OSError as error: print(error)

        try:  rmtree(f'{APPS_FOLDER}/{content['id']}')
        except OSError as error:  print(error)          
        
        delete_application(content['id'])
        await workspace_db.delete_record(application_rec, application_rec.id, content['id'])
            
        return  {"result": "ok"} 
    except Exception as ex:
        print(str(ex))
        return  {"result": "error", "error_text": f"Failed to delete app: {ex}"}


async def add_view(content):
    try:
        app = await workspace_db.get_record(application_rec, application_rec.id, content['id'])

        for rec in app.view_list:
            if rec['value'] == content['view']:
                return  {"result": "error", "error_text": "View already exists"}

        app.view_list.append( {'name': content['view'], 'value': content['view']} ) 
        
        app_upd = await workspace_db.update_fields(
            application_rec, application_rec.name, app.name, 
            {"view_list": app.view_list},
            to_json=True
        )

        return await to_json(app_upd)  
    except Exception as ex:            
        return  {"result": "error", "error_text": f"Failed to add new view: {ex}"}


async def delete_view(content):
    try:
        app = await workspace_db.get_record(application_rec, application_rec.id, content['id'])

        if len(app.view_list) == 1:
            return  {"result": "error", "error_text": f"At least one view should exist: {ex}"}

        for rec in app.view_list:
            if rec['value'] == content['view']:
                app.view_list.remove(rec)
                break

        app_upd = await workspace_db.update_fields(
            application_rec, application_rec.id, app.id, 
            {"view_list": app.view_list},
            to_json=True
        )

        return await to_json(app_upd)
    except Exception as ex:               
        return  {"result": "error", "error_text": f"Failed to delete view: {ex}"}


#async def app_status(content):
#    try:
#        print('cccccccccc')
#        status, loop = await get_app_status(content['id'])  #loop_cnt/{loop_cnt
#        print(f"{content['id']} Status/Loop: {status}/{loop}")
#    except:
#        print(f'App {content['name']} Offline')
#    
#    return { 'result': 'ok', }


async def build_apk(content):
    await build_app(content['name'])
    return { 'result': 'ok', }


async def run_apk(content):
    return await run_app(content['name'])
    
        
async def stop_apk(content):
    try:
        await stop_app(content['name'])
    except:
        print(f'App {content['name']} Already Stopped')  
        return {"result": "error", "error_text": f'App already stopped: {content['name']}'}
            
    return { 'result': 'ok', } 


COMMANDS_DICT = {
    'update_list'   :  update_list  , 'perm_update_list'  : 'developer, ',
    'get_app'       :  get_app      , 'perm_get_app'      : 'developer, user, view, ',
    'add_app'       :  add_app      , 'perm_add_app'      : 'developer, ',
    'save_app'      :  save_app     , 'perm_save_app'     : 'developer, ',
    'delete_app'    :  delete_app   , 'perm_delete_app'   : 'developer, ',
    'add_view'      :  add_view     , 'perm_add_view'     : 'developer, ',
    'delete_view'   :  delete_view  , 'perm_delete_view'  : 'developer, ',
    #'app_status'    :  app_status   , 'perm_app_status'   : 'developer, user, view, ',
    'build_app'     :  build_apk    , 'perm_build_app'    : 'developer, ',
    'run_app'       :  run_apk      , 'perm_run_app'      : 'developer, ',
    'stop_app'      :  stop_apk     , 'perm_stop_app'     : 'developer, ',
}


#DEFAULT
async def default_msg(content):
    print('Request Error app_ide_mng: ' + str(content))
    return {"result": "error", "error_text": "app_ide_mng command not found"}

async def app_ide_mng(auth, cmd, content):
    content_json = ujson.loads( content )

    if check_permissions(auth, COMMANDS_DICT['perm_' + cmd]):
        return await COMMANDS_DICT.get(cmd, default_msg)(content_json)
    else:
        return { "result": "error", "error_text": f"Permission denied for user '{auth['user']}' accessing '{cmd}'" }
