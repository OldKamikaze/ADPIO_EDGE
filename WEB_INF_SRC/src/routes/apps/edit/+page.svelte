<script lang="ts">
    import { onMount }      from 'svelte'
    import { page }         from '$app/state'
    import { user, async_post, popup_add, sleep, set_navigation } from '../../state.svelte.ts'
    import { build_app, run_app, stop_app } from '../../../lib/app_engine.ts'

    import {
        PreviousOutline,
        BuildImage,
        BuildRun,
        StopOutline,
        ColumnDependency,
        DataVolume,
        Screen,
        Terminal,
    } from "carbon-icons-svelte"

    import ControlPanel     from "../../adp_kit/components/ControlPanel.svelte"

    import IDE_datapoints   from "./IDE_datapoints.svelte"
    import IDE_logic        from "./IDE_logic.svelte"
    import IDE_graphics     from "./IDE_graphics.svelte"
    
    let application = $state({group: "nogroup", id: "noid", name: "Loading App...", status: false})
    
    const DNE        = -2 //App does not exists
    const LOADING    = -1
    const VIEW_DATA  = 0
    const VIEW_GRAPH = 1
    const VIEW_PROG  = 2

    let view = $state(LOADING)  // //0 - datapoints, 1 - graph, 2 - prog    

    let buttons = $derived([{
        text                : 'BACK',
        color               : 'normal',
        icon                : PreviousOutline,
        disabled            : false,
        onclick             : (e: any) => { 
            user.active_tree = user.edit_tree        
            set_navigation('/apps/mng') 
        }
    }, {
        text                : 'DATAPOINTS',
        color               : 'normal',
        icon                : DataVolume ,
        disabled            : (view === VIEW_DATA? true : false),
        onclick             : async (e: any) => { view = VIEW_DATA }
    }, {
        text                : 'GRAPHICS IDE',
        color               : 'normal',
        icon                : Screen,
        disabled            : (view === VIEW_GRAPH? true : false),
        onclick             : async (e: any) => { view = VIEW_GRAPH }
    }, {
        text                : 'LOGIC IDE',
        color               : 'normal',
        icon                : ColumnDependency ,
        disabled            : (view === VIEW_PROG? true : false),
        onclick             : async (e: any) => { view = VIEW_PROG  }
    }, {
        text                : 'BUILD APP',
        color               : 'normal',
        icon                : BuildImage,
        disabled            : false,
        onclick             : async (e: any) => { 
            await build_app(application.id) 
            popup_add("Command Finished", "App Build Command Finished")
        }
    }, {
        text                : 'STOP APP',
        color               : 'red',
        icon                : StopOutline,
        disabled            : false,
        rendered            : application.status,
        onclick             : async (e: any) => { 
            popup_add("Executing Stop Command", "Wait Command to Complete")
            await stop_app  (application.id) 
            await sleep(600);
            await get_app(application.id)
            popup_add("Command Finished", "App Stop Command Finished")
        }
    },{
        text                : 'RUN APP',
        color               : 'green',
        icon                : BuildRun,
        disabled            : false,
        rendered            : !application.status,
        onclick             : async (e: any) => { 
            popup_add("Executing Run Command", "Wait Command to Complete")
            await run_app   (application.id) 
            await sleep(1600);
            await get_app(application.id)
            popup_add("Command Finished", "App Run Command Finished")
        }
    },/*{
        text                : 'APP TERMINAL',
        color               : 'normal',
        icon                : Terminal,
        disabled            : false,
        rendered            : true,
        onclick             : async (e: any) => { 
            //await terminal_modal.open(e)
        }        
    }*/])
     
    
    async function get_app(appid: string){
        const temp_app = await async_post( 'app_ide', 'get_app', {id: appid} )
        
        if (temp_app?.result === 'error'){
            application.name = `Failed To Load App ${appid}`
            view = DNE
        }else {
            application = temp_app
            if (view < 0) view        = VIEW_DATA            
        }
    }

    onMount(async () => {                
        await get_app(page.url.searchParams.get('app'))        
        user.active_header = `APP EDITOR: ${application.name}`
    })

</script>

<div class="content-panel" >
    <ControlPanel bind:buttons={buttons} />
</div>


{#if      view === VIEW_DATA}
    <IDE_datapoints bind:application={application} />
{:else if view === VIEW_GRAPH}
    <IDE_graphics   bind:application={application}/>
{:else if view === VIEW_PROG}
    <IDE_logic      bind:application={application} />
{:else if view === LOADING}
    <div>Loading App...</div>
{:else if view === DNE}
    <div>Failed To Load Application {application.name}</div>   
{:else}
    <div>ERROR: VIEW DOES NOT EXIST ({view})...</div>
{/if}


<style></style>

