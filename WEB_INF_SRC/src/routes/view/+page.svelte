
<script lang="ts">
    import '/static/graphics.css'

    import { onMount, onDestroy }   from 'svelte'
    import { page }                 from '$app/state'
    import { user, async_post }     from '../state.svelte.ts'
    
    import {
        Edit,
    } from "carbon-icons-svelte"


    import InputSelector    from "../adp_kit/components/InputSelector.svelte" 
    import ButtonR          from "../adp_kit/components/ButtonR.svelte"
    import Modal            from "../adp_kit/components/Modal.svelte"
    import DataDisplay      from "../adp_kit/components/DataDisplay.svelte"


    let application = $state({group: "nogroup", id: "noid", name: "Loading App...", status: false, selected_view: '', view_list: []})
    let content     = $state([])
    let datapoints  = $state([])
    let interval_datapoints = $state(-1)

    let write_dp_modal    = $state()
    let selected_elements = $state([])

    let app_id = $derived(page.url.searchParams.get('app') || '')

    async function write_live_value(){
        let write_dps:any = []
        selected_elements.forEach((el:any) => {
            write_dps.push({'data_id': `${application.group}_${application.name}_${el.datapoint.group}_${el.datapoint.name}`, 'value': el.datapoint.value})
        })

        const run_data = await async_post( 'app_view', 'set_datapoints',  { data_ids : write_dps } )   
    }   


    async function update_datapoints(content: any, dp_ids: any){
        const run_data:any = await async_post( 'app_view', 'get_datapoints', { data_ids : dp_ids } )

        datapoints.forEach((el: any, indx: number) => { el.value = run_data[indx] })
        content.forEach((c_el: any) =>  {            
            c_el.error = true                           //Error If name was changed/offline
            datapoints.forEach((d_el: any) =>  {
                if (c_el.datapoint_bind === d_el.id){
                    c_el.datapoint = d_el
                    c_el.error = !application.status
                }               
            })
        })   

        return content
    }


    async function update_content(){      
        clearInterval(interval_datapoints) 
        datapoints = await async_post( 'app_ide_datapoints', 'update', { app_id: application.id, })
        content    = await async_post( 'app_ide_graphics',   'update', { 
            app_id          : application.id, 
            app_status      : application.status,
            view            : application.selected_view,
        } )

        if (datapoints.length === 0) return
        content.forEach((c_el: any) =>  {            
            c_el.error = true                           //Error If name was changed/offline
            datapoints.forEach((d_el: any) =>  {
                if (c_el.datapoint_bind === d_el.id) c_el.datapoint = d_el
            })
        })          

        if (!application.status)  return //Quit if offline

        let refresh_dps_ids: any = []
        datapoints.forEach((el:any) => { refresh_dps_ids.push(`${application.group}_${application.name}_${el.group}_${el.name}`) })
        content = await update_datapoints(content, refresh_dps_ids) 
        interval_datapoints = setInterval(async () => {
            content = await update_datapoints(content, refresh_dps_ids) 
        }, 1000);   
    }
        

    async function get_app(appid: string){
        application = await async_post( 'app_ide', 'get_app', {id: appid} )
        user.active_header = application.name    
    }


    $effect(() => { (async () => {
        await get_app(app_id)

        if ((application.id  !== "err") && (application.status == true)) 
            await update_content()
    })() })

    //onMount(async () => { })
    onDestroy(async () => { clearInterval(interval_datapoints) })  
</script>


{#if      application.id === "noid"}
    <div>Loading Application...</div>
{:else if application.id === "err"}
    <div>Failed To Load Application...</div>
{:else}
    <div class="content-panel">
        <span id="view_select" ><InputSelector label="Views" item_list={application.view_list}  bind:value={application.selected_view} onchange={async () =>  {
            await update_content()
        }} /></span>
    </div>

<!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="content-panel flex flex-gap-tile"  >
        {#each content as el, index}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <div class="tile tile-basic flex-tile"
                onpointerdown="{(e: any) => { 
                    selected_elements = [ JSON.parse(JSON.stringify(el)) ]
                    if ((el.datapoint !== undefined) && (el.datapoint.writable))
                        write_dp_modal?.open(120, 120) 
                }}"
            >
                {#if el.error || el.datapoint === undefined}
                    <div class="tile-basic-value">...</div>
                {:else}
                    <div class="tile-basic-group">{el.datapoint.group}</div>
                    <div class="tile-basic-name" >{el.datapoint.name}</div>
                    <div class="tile-basic-value {el.datapoint.writable ? 'tile-editable': ''}">
                        <DataDisplay readonly={true} label=''  bind:datapoint={el.datapoint}  />                    
                        {el.datapoint.units}
                    </div>
                {/if}
            </div>
        {/each}
    </div>  
    

    <Modal bind:this={write_dp_modal} title="Write Values" > 
        <div>
            <p><DataDisplay readonly={false} bind:datapoint="{selected_elements[0].datapoint}" /></p>
        </div>

        <ButtonR text="Write Value" onclick={async (e:any) =>  {
            write_dp_modal?.close(e)
            await write_live_value()
        }} > <Edit class="round-btn-svg"/> </ButtonR>  
    </Modal>


{/if}

