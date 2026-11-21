<script  lang="ts">
    import '/static/graphics.css'

    import { onMount, onDestroy }      from 'svelte'
    import { user, async_post, datapoints_to_tree } from '../../state.svelte.ts'

    import {
        Add,
        TrashCan,
        Save,
        Edit,
    } from "carbon-icons-svelte"

    import ContextMenu      from "../../adp_kit/components/ContextMenu.svelte"
    import InputSelector    from "../../adp_kit/components/InputSelector.svelte" 
    import ButtonR          from "../../adp_kit/components/ButtonR.svelte"
    import Modal            from "../../adp_kit/components/Modal.svelte"
    import InputLabel       from "../../adp_kit/components/InputLabel.svelte"
    import DataDisplay      from "../../adp_kit/components/DataDisplay.svelte"
    
    let {
        application = $bindable(),
    } = $props()       

    let interval_datapoints = $state(-1)
    let datapoints          = $state([])

    let content             = $state([])
    let selected_elements   = $state([])
    
    let el_move_tracker     = $state({element: {id: -1}, side: -1, gap: -1})

    let view_editor_modal   = $state()
    let write_dp_modal      = $state()
    let new_view            = $state("New View")

    let context_menu        = $state()
    let buttons             = $derived([
    {
        text                : 'Delete Element',
        color               : 'red',
        icon                : TrashCan,
        disabled            : selected_elements.length === 0,
        with_confirmation   : true,
        conf_title          : 'DELETE ELEMENTS',  
        conf_description    : (selected_elements.length > 0) ? `Are you sure you want to delete: ${get_point_list(selected_elements)}?`: '',  
        conf_btn_accept_txt : 'DELETE',
        onclick             : async (e: any) => { await delete_element() }
    }, 
    ])

    function get_point_list(points:any){
        let list: string = ""
        points.forEach((el:any) => { list += `${el.name}, ` } ) 
        list = list.substring(0, list.length - 2)
        return list
    }

    async function handler_move_el_drag(el_move_tracker: any){  
        if (selected_elements.length > 0){
            let el_set:any = []
            selected_elements.forEach(async (el: any) =>  {
                const this_el_index  = content.indexOf(el)
                if ((this_el_index === el_move_tracker.gap) || (this_el_index + 1 === el_move_tracker.gap)) return
                el.place =  el_move_tracker.gap //New Place
                el_set.push(el) 
            })

            content = await async_post( 'app_ide_graphics', 'move_element', { 
                app_id          : application.id, 
                view            : application.selected_view,
                elements        : el_set
            } ) 
        }    
        
        update_data(false)
    }
    
    function calc_gap(index1: number, index2: number){
        if (content.length === 0)           return 0
        if (content.length === 1)           return 0
        if ((index1 === 0) && (index2 === -1))                                 return (content[index1].order - 1)
        if ((index1  === content.length - 1) && (index2  === content.length))  return (content[index1].order + 1)

        return ((content[index1].order + content[index2].order) / 2)
    }


    async function add_element(id: number, name: string){
        const new_el = {
            //"name"          : name, 
            //"description"   : "description ", 
            "order"         : el_move_tracker.gap,
            "view"          : application.selected_view,
            "datapoint_bind": id
        } 
        
        content = await async_post( 'app_ide_graphics', 'add_element', { 
            app_id          : application.id, 
            view            : application.selected_view,
            element         : new_el 
        } )   

        await update_data(false) 
    }


    async function delete_element() {
        if (selected_elements.length > 0){
            let el_set:any = []
            selected_elements.forEach(async (el: any) =>  { el_set.push({ app_id: application.id, id: el.id}) })
            content = await async_post( 'app_ide_graphics', 'delete_element', { 
                app_id          : application.id, 
                view            : application.selected_view,
                elements        : el_set 
            } )
        }

        await update_data(false)
        selected_elements = []
    }


    async function write_modal(){
        if (selected_elements.length === 0) return
        
        let edit_list = []
        if (selected_elements.length === 1)
            edit_list.push(selected_elements[0])
        else {
            edit_list.push(JSON.parse(JSON.stringify(selected_elements[0])))

            selected_elements.forEach( (el: any) => {
                if (selected_elements[0].datapoint.datatype    !== el.datapoint.datatype)  edit_list[0].datapoint.datatype    = '≠'
                if (selected_elements[0].datapoint.value       !== el.datapoint.value   )  edit_list[0].datapoint.value       = '≠'
                if (selected_elements[0].datapoint.writable    !== el.datapoint.writable)  edit_list[0].datapoint.writable    = '≠'       

                edit_list.push(el)
            } )
        }
        
        selected_elements = JSON.parse(JSON.stringify(edit_list))
        if (application.status) write_dp_modal.open(120, 120)     
    }    

    async function write_live_value(){
        if (selected_elements.length < 1){
            selected_elements.slice(1, selected_elements.length).forEach((el:any) => {
                if (selected_elements[0].datapoint.value       !== '≠') el.datapoint.value       = selected_elements[0].datapoint.value   
            })
            selected_elements = JSON.parse(JSON.stringify( selected_elements.slice(1, selected_elements.length) ))    
        }   

        let write_dps:any = []
        selected_elements.forEach((el:any) => {
            write_dps.push({'data_id': `${application.group}_${application.name}_${el.datapoint.group}_${el.datapoint.name}`, 'value': el.datapoint.value})
        })

        const run_data = await async_post( 'app_view', 'set_datapoints',  { data_ids : write_dps } )        
    }    


    async function live_data(){
        let dps_ids: any = []
        datapoints.forEach((el:any) => {
            dps_ids.push(`${application.group}_${application.name}_${el.group}_${el.name}`) 
        })        

        interval_datapoints = setInterval(async () => {             
            if (datapoints.length === 0) return
            const run_data:any = await async_post( 'app_view', 'get_datapoints', { data_ids : dps_ids } )

            if (run_data[0] === "APP_STOPPED"){
                clearInterval(interval_datapoints)
                interval_datapoints = -1
                await update_data() 
                return //App is stopped, nothing to read anymore
            }

            datapoints.forEach((el: any, indx: number) => { el.value = run_data[indx] })
            update_data(false)
        }, 1000);   
    }


    async function update_data(upd_content = true){
        if (upd_content){
            content = await async_post( 'app_ide_graphics', 'update', { 
                app_id          : application.id, 
                app_status      : application.status,
                view            : application.selected_view,
            } )
            datapoints = await async_post( 'app_ide_datapoints', 'update', { app_id: application.id, })

            let new_active_tree = datapoints_to_tree(datapoints)
            new_active_tree.forEach((gr_el:any) => {
                gr_el.submenu.forEach((el:any) => {
                    el.ondropevent = async (e: any) => { add_element(el.el_id, el.el_name) } //Set navi drag events
                    el.ondragevent = async (e: any) => {  }
                })
            })  
            
            user.active_tree = new_active_tree
        }

        content.forEach((c_el: any) =>  {            
            c_el.error = true                           //Error If name was changed
            datapoints.forEach((d_el: any) =>  {
                if (c_el.datapoint_bind === d_el.id){
                    c_el.datapoint = d_el
                    c_el.error = false
                }               
            })
        })
    }


    $effect(() => { (async () => {
        await update_data()
        if ( (application.status === true) && (interval_datapoints === -1) ) live_data()
    })() })  

    //onMount(async () => { }) 
    onDestroy(async () => { clearInterval(interval_datapoints) })  
</script>


<div class="content-panel">
    <span id="view_select" ><InputSelector label="Views" item_list={application.view_list}  bind:value={application.selected_view} onchange={async () =>  {
        await update_data()
    }} /></span>

    <ButtonR text='Add View' onclick={() => { 
        view_editor_modal?.open(120, 120)
    }} > <Add class="round-btn-svg"/> </ButtonR>

    <ButtonR text='Delete View' color="red" 
        with_confirmation   = {true}
        conf_title          = 'Delete View'
        conf_description    = 'Are you sure you want to delete current view and all corresponding elements?'
        conf_btn_accept_txt = 'DELETE'

        disabled={(application.view_list.length === 1)}
        
        onclick={async () => { 
            const res = await async_post( 'app_ide_graphics', 'clear_view_elements', {
                app_id: application.id,
                view  : application.selected_view,
            } ) 

            if ( ('result' in res) && (res.result === 'error') ) return

            application = await async_post( 'app_ide', 'delete_view', {
                id    : application.id,
                view  : application.selected_view,
            } ) 

            update_data()
    }} > <TrashCan class="round-btn-svg"/> </ButtonR>
</div>


<ContextMenu buttons={buttons} bind:this={context_menu}   /> 

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="content-panel flex flex-gap-tile" 
    oncontextmenu="{(e: any) => {
        if (application.status) return

        context_menu.open_context(e.clientX, e.clientY)
        e.preventDefault()
    }}"
>
    {#each content as el, index}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div class="tile tile-basic flex-tile  { selected_elements.includes( el ) ? 'tile-selected': '' }"
            onmousedown="{(e:any) => {
                if (!e.ctrlKey) selected_elements = [] //shiftKey
                
                if (selected_elements.includes( el )) {
                    if ((e.button === 0) && (e.ctrlKey)) //Delete element only on left btn click
                        selected_elements.splice( selected_elements.indexOf(el), 1 )
                    content = content
                } else {
                    selected_elements.push( el )
                    content = content
                }  

                if (application.status) return
            }}"

            draggable="{!application.status}" 
            
            ondblclick="{() => {
                if (application.status) write_modal()
            }}"

            ondragstart={(e:any) => { el_move_tracker = {element: {id: -1}, side: -1, gap: -1} }}
            ondragend  ={(e:any) => {
                if (el_move_tracker.side !== -1) handler_move_el_drag(el_move_tracker)
                el_move_tracker = {element: {id: -1}, side: -1, gap: -1}
            }}
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

            {#if el_move_tracker}
                <div class="tile-drag-overlay-left {((el_move_tracker.element.id === el.id) && (el_move_tracker.side % 2 == 0))  ? 'tile-drag-overlay-left-selected' : ''}"
                    ondragleave={(e:any) => { }}

                    ondragover={(e:any) => { 
                        el_move_tracker = {element: el, side: index * 2, gap: calc_gap(index, index - 1)}
                    }}
                ></div>
                
                <div class="tile-drag-overlay-right  {((el_move_tracker.element.id === el.id) && (el_move_tracker.side % 2 != 0)) ? 'tile-drag-overlay-right-selected' : ''} "
                    ondragleave={(e:any) => {  }}

                    ondragover={(e:any) => { 
                       el_move_tracker = {element: el, side: index * 2 + 1, gap: calc_gap(index, index + 1)}
                    }}
                ></div>
            {/if}
        </div>
    {/each}
</div>



<Modal bind:this={view_editor_modal} title="View Editor" > 
    <div style="padding-top: 20px">
        <InputLabel label="View Name" minlength={1} maxlength={32} bind:value={new_view} />
    </div>
    <div style="padding-top: 20px">
        <ButtonR text="Save" onclick={async (e:any) =>  {
            const res = await async_post( 'app_ide', 'add_view', {
                id   : application.id,
                view : new_view,
            } )    

            if ( ('result' in res) && (res.result === 'error') ) return
            application.view_list = res.view_list

            view_editor_modal.close(e)
        }} > <Save class="round-btn-svg"/> </ButtonR>
    </div>
</Modal>


<Modal bind:this={write_dp_modal} title="Write Values" > 
    {#if selected_elements.length > 0}
        {#if selected_elements[0].datapoint.datatype    === '≠'}
            <p>Simultaneous Editing Is Impossible, Different Datatypes</p>
        {:else if selected_elements[0].datapoint.writable !== true}
            <p>Simultaneous Editing Is Impossible, Some Datapoints Read Only</p>              
        {:else}
            <div>
                <p><DataDisplay readonly={false} bind:datapoint="{selected_elements[0].datapoint}" /></p>
            </div>

            <ButtonR text="Write Value" onclick={async (e:any, ) =>  {
                write_dp_modal.close(e)
                await write_live_value()
            }} > <Edit class="round-btn-svg"/> </ButtonR>
        {/if}
    {:else}    
        <div>LOADING...</div>
    {/if}
</Modal>



<style>
    #view_select{
        display: inline-block;
    }

    .tile-drag-overlay-left{
        position: absolute;

        top:  -12px;
        left: -8px;

        width:  calc(50%  + 8px);   
        height: calc(100% + 22px);     
    }

    .tile-drag-overlay-left-selected{
        border-left: solid black 2px !important;
    }

    .tile-drag-overlay-right{
        position: absolute;

        top:   -12px;
        right: -8px;

        width:  calc(50%  + 8px);   
        height: calc(100% + 22px);        
    } 
    
    .tile-drag-overlay-right-selected{
        border-right: solid black 2px !important;
    }    
</style>