import asyncio

#if sys.platform == 'win32':
#    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()) #otherwise create_subprocess_exec does not work on

import uvicorn
from   pydantic import BaseModel

#FAST API
from fastapi                 import FastAPI, Request
from fastapi.responses       import HTMLResponse
from fastapi.staticfiles     import StaticFiles
from contextlib              import asynccontextmanager

from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

#This more advanced, for future
#from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
#from pydantic import BaseModel

#SYSTEM
from lib.globals            import ROOT_FOLDER, WORKSPACE
from system.settings_server import settings_cfg

#DB
from lib.database_sql.server_virt_model import server_virt_db, clear_virtual_db, init_virtual_db, set_server_param, get_server_param, SERVER_PARAMS, SERVER_STATUS_SIGNALS
from lib.database_sql.workspace_model   import workspace_db
from lib.terminal                       import terminal_web

#app_ide
from content.app_ide            import app_ide_mng
from content.app_ide_datapoints import app_ide_datapoints_mng
from content.app_ide_graphics   import app_ide_graphics_mng
from content.app_ide_logic      import app_ide_logic_mng
from content.app_view           import app_view_mng

#System Managers
from drivers.connectors_engine import ce_initialize, ce_terminate

from content.users  import user_mng, cached_auth, auth_no_users_fix
from content.logger import log_task_mng, print_log_system, print_app_event

#Tools 
from content.trends_tools  import trends_tools_mng
from content.system_tools  import system_tools_mng, rebuild_logic_db
from content.connectors_tools    import connectors_mng

#APPS
from system.app_engine                  import stop_app, run_app
from lib.database_sql.application_model import application_db_initialize, application_db_terminate, applciation_db


user_cache  = []
worker      = -1


async def on_server_startup(database_lib_rebuild = True):
    #Check If Workspace properly initialized
    if database_lib_rebuild or __debug__:
        print("\n\nFirst DB Initialization, Auto Rebuild Mode On\n\n")
        await rebuild_logic_db({})
        print("\n\nAuto Rebuild Complete!!!\n\n")

    print('\n')

    #Initialize drivers
    await ce_initialize()


    await set_server_param(SERVER_PARAMS.SERVER_STATUS, SERVER_STATUS_SIGNALS.INITIALIZED)

    if await get_server_param(SERVER_PARAMS.GUI_TERMINAL):  
        print('Starting Terminal (system)... STD AND ERR In GUI!')
        terminal_web.initialize('system', await get_server_param(SERVER_PARAMS.TERMINAL_HDD_OUT))

    #Start Apps
    print('Starting Apps on server startup...')

    appliacations = await application_db_initialize()

    print(f"\nApplications Count - {len(applciation_db)}:\n" )

    for app in appliacations:
        print(f"{app.id} Autostart: {app.autostart}" )
        if app.autostart:
            try:  await run_app(app.id)
            except Exception as ex:  print(f"Failed to autostart {app.name}: {ex}" )

    print('\n')    
    await application_db_terminate()

    await print_log_system(f"ADPIO Edge Started! Debug Mode: {__debug__}")


async def on_server_shutdown():
    #Stop Apps
    print('Terminating Apps on server shutdown...')

    appliacations = await application_db_initialize()

    for app in appliacations:
        try: await stop_app(app.id)
        except Exception as ex: await print_app_event(f'App {app.id} stopped')
    await application_db_terminate()

    #Stop Drivers
    await ce_terminate()

    await set_server_param(SERVER_PARAMS.SERVER_STATUS, SERVER_STATUS_SIGNALS.TERMINATE)

    #Stop Apps
    if terminal_web.terminalIO != None:  
        terminal_web.terminate()
        print('Terminating Terminal (system)...')

    await print_log_system("ADPIO Edge Terminated...")

    
@asynccontextmanager
async def initialize_worker(app: FastAPI):
    global user_cache, worker
    #INDEX = WEB_INF_index() #Relink Files in webinf in index.html

    #Init Databases
    workspace_db  .initialize()
    server_virt_db.initialize()

    await auth_no_users_fix() #if there is no user - create admin/admin
    user_cache = await cached_auth()

    await application_db_initialize()

    worker_num = await get_server_param(SERVER_PARAMS.WORKERS_COUNT)
    await set_server_param(SERVER_PARAMS.WORKERS_COUNT, worker_num + 1)

    if await get_server_param(SERVER_PARAMS.GUI_TERMINAL):
        print('Starting Worker Terminal (system w)... STD AND ERR In GUI!')
        terminal_web.initialize(f'worker {worker_num}', await get_server_param(SERVER_PARAMS.TERMINAL_HDD_OUT))

    print(f'Server Status: { await get_server_param(SERVER_PARAMS.SERVER_STATUS) }, Worker {await get_server_param(SERVER_PARAMS.WORKERS_COUNT)} Started')

    yield   #Before This - Startup, After - Shutdown
    
    if terminal_web.terminalIO != None:
        terminal_web.terminate()
        print('Terminating Worker Terminal (system w)...')

    await application_db_terminate()
    workspace_db  .terminate()
    server_virt_db.terminate()


app = FastAPI( 
    lifespan=initialize_worker, 

    title="ADPIO_EDGE",
    #version=""
    #debug=True 

    #docs_url    = None, # Disable Swagger UI
    #redoc_url   = None, # Disable ReDoc
    #openapi_url = None  # Disable OpenAPI JSON schema        
) 


app.add_middleware(
    GZipMiddleware,
    minimum_size  = 1024 * 8,
    compresslevel = 6
)

class request_jsn(BaseModel): #for standart commands, update, delete record and etc
    cmd:     str = 'command'
    #user:    str = ''
    content: str = ''

#app.mount( "/assets",    StaticFiles(directory = "./WEB-INF/assets"),    name = "assets")    #Svelte Static Resources, ex: bundle, files, pictures    
#app.mount( "/favicon",   StaticFiles(directory = "./WEB-INF/favicon"),   name = "favicon")   #Favicon   
#app.mount( "/resources", StaticFiles(directory = "./WEB-INF/resources"), name = "resources") #Resources   


def check_auth(sessionid):
    global user_cache

    for usr in user_cache :
        if usr['sessionkey'] == sessionid:
           return usr

    #return {"result": "ok", "auth": True}
    return { "result": "error", "auth": False, "error_text": "The Username or Password is Incorrect" }


@app.post("/api/login")
async def login(req_json: request_jsn): #, request: Request 
    global user_cache

    user_cache = await cached_auth()
    res = await user_mng({'user': '', 'profile': ''}, req_json.cmd, req_json.content)

    if (res['result'] == 'ok'):
        return  { "result": "ok", "auth": True, "sessionkey": res['sessionkey'], "user": res['user'], "profile": res['profile'] }
    else :
        return { "result": "error", "auth": False, "error_text": "The Username or password are incorrect" }
    

#User and Navigation
@app.post("/api/app_ide")
async def app_ide(request: Request, req_json: request_jsn ): #, request: Request    
    global user_cache, worker
    user_auth = check_auth(request.headers.get("authorization"))

    return await app_ide_mng(user_auth, req_json.cmd, req_json.content)


@app.post("/api/app_ide_datapoints")
async def app_ide_datapoints(request: Request, req_json: request_jsn ): #, request: Request 
    global user_cache

    user_auth = check_auth(request.headers.get("authorization"))
    return await app_ide_datapoints_mng(user_auth, req_json.cmd, req_json.content)


@app.post("/api/app_ide_graphics")
async def app_ide_graphics(request: Request, req_json: request_jsn ): #, request: Request 
    global user_cache
    user_auth = check_auth(request.headers.get("authorization"))
    return await app_ide_graphics_mng(user_auth, req_json.cmd, req_json.content)


@app.post("/api/app_ide_logic")
async def app_ide_logic(request: Request, req_json: request_jsn ): #, request: Request 
    global user_cache
    user_auth = check_auth(request.headers.get("authorization"))
    return await app_ide_logic_mng(user_auth, req_json.cmd, req_json.content)


@app.post("/api/app_view")
async def app_view(request: Request, req_json: request_jsn ): #, request: Request
    global user_cache
    user_auth = check_auth(request.headers.get("authorization"))
    return await app_view_mng(user_auth, req_json.cmd, req_json.content)


#User and Navigation
@app.post("/api/user")
async def user(request: Request, req_json: request_jsn ): #, request: Request
    global user_cache
    user_auth = check_auth(request.headers.get("authorization"))
    return await user_mng(user_auth, req_json.cmd, req_json.content)  


#User and Navigation
@app.post("/api/logger")
async def logger(request: Request,  req_json: request_jsn ): #, request: Request 
    global user_cache    
    user_auth = check_auth(request.headers.get("authorization"))
    return await log_task_mng(user_auth, req_json.cmd, req_json.content)


#Tools
@app.post("/api/trends")
async def trends_tools(request: Request, req_json: request_jsn ): #, request: Request
    global user_cache    
    user_auth = check_auth(request.headers.get("authorization"))
    return await trends_tools_mng(user_auth, req_json.cmd, req_json.content)  

#Fix IT
@app.post("/api/connectors")
async def network_tools(request: Request, req_json: request_jsn ): #, request: Request
    global user_cache    
    user_auth = check_auth(request.headers.get("authorization"))
    return await connectors_mng(user_auth, req_json.cmd, req_json.content)  


@app.post("/api/system_tools")
async def system_tools(request: Request, req_json: request_jsn ): #, request: Request
    global user_cache    
    user_auth = check_auth(request.headers.get("authorization"))
    return await system_tools_mng(user_auth, req_json.cmd, req_json.content)  


def main():
    print("Initializing APDIO EDGE...\n")

    if __debug__: 
        print("DEBUG is ON. Run with -O or -OO to turn off debug")
        print("!!!!! THIS VERSION NOT FOR DISTRIBUTION !!!!!\n")        
    
    print(f"Global ROOT Folder:      {ROOT_FOLDER}" )
    print(f"Global WORKSPACE Folder: {WORKSPACE}\n" )
    
    settings = settings_cfg()
    settings.read_settings()

    auto_reload = False                         # Fix for pyinstaller, if not done you will get infinite loop,
    workers     = settings.uvicorn["workers"]   # Note reload and workers are exluisive    
    log_lvl     = "error"
    
    if __debug__:               # For Dist reload must be false
        auto_reload = True
        workers     = 1
        log_lvl     = "info"   
        print("DEBUG ON !!!")

    #if sys.platform == "win32":  
    #    auto_reload = False  #otherwise create_subprocess_exec does not work 
    #    workers     = 2

#Init Workspace DB
    clear_virtual_db()
    terminal_web.clear_virtual_db()

    server_virt_db.initialize()
    init_virtual_db( 
        GUI_TERMINAL     = settings.terminal['gui'], 
        FAPI_AUTO_RELOAD = auto_reload, 
        TERMINAL_HDD_OUT = settings.terminal['virtual'] 
    )
    workspace_db  .initialize()

    print(f"Initializing APDIO EDGE... Status: NOT INIT")
    asyncio.run( on_server_startup(database_lib_rebuild=settings.auto_rebuild) )
    
    #Init FastAPI
    uvicorn.run(
        "adpio_edge:app",
        host      = settings.uvicorn["host"],
        port      = settings.uvicorn["port"],

        reload    = auto_reload,
        workers   = workers,
        log_level = log_lvl,

        #loop      = "uvloop",
    )   

    asyncio.run( on_server_shutdown( ) )

    workspace_db  .terminate()
    server_virt_db.terminate()


if __name__ == "__main__":
    #if sys.platform == "win32":  freeze_support()
    main()
