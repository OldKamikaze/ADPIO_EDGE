<script  lang="ts">
    import { onMount, onDestroy }      from 'svelte'
    import { browser_params, user, async_get, async_post, get_cookie_value, initialize_user, popup_add, sleep, blocks_to_tree, datapoints_to_tree } from '../../state.svelte.ts'
    import { build_app, run_app, stop_app, DATAPOINTS_PROPERTIES, UNITS_LIST} from '../../../lib/app_engine.ts'
    import { version, dev } from '$app/env'

    import {
        Add,
        TrashCan,
        Save,
        Edit,    
    } from "carbon-icons-svelte"

    import ContextMenu        from "../../adp_kit/components/ContextMenu.svelte" 
    import Modal              from "../../adp_kit/components/Modal.svelte"
    import InputLabel         from "../../adp_kit/components/InputLabel.svelte"
    import ButtonR            from "../../adp_kit/components/ButtonR.svelte"

    import LENBlock           from "../../adp_kit/logic_engine/LENBlock.svelte"
    import LENSelectionBox    from "../../adp_kit/logic_engine/LENSelectionBox.svelte"
    import LENBind            from "../../adp_kit/logic_engine/LENBind.svelte"
    import LENIO              from "../../adp_kit/logic_engine/LENIO.svelte"
    import LENConnPath        from "../../adp_kit/logic_engine/LENConnPath.svelte"

    const blk_width  = 160
    const blk_height = 40
    const canvas     = { width: 3200, height: 6400 }

    let {
        application = $bindable(),    
    } = $props()       

    let interval_live       = $state(-1)

    let content             = $state([])
    let selected            = $state([])
    let selected_binds      = $state([])
    let datapoints          = $state([])

    let box_mode            = $state() 
    let drag_event          = $state(false) //drage elements normally
    let drop_element_event  = $state({ enabled: false, x: 0, y: 0, buffer: {} }) //Drag from left menu
    let path_connect        = $state({ enabled: false, x0: 0, x1: 0, y0: 0, y1: 0, bind0_block: {}, bind1_block: {}, bind0_io: {}, bind1_io: {}, })

    let context_menu = $state()
    let buttons = $derived([{
        text                : 'Disconnect Bind',
        color               : 'red',
        icon                : TrashCan,
        disabled            : selected_binds.length === 0,
        with_confirmation   : true,
        conf_title          : (selected_binds.length > 0) ? `Are you sure you want to disconnect binds?`: '',  
        conf_description    : '',
        conf_btn_accept_txt : 'DELETE',
        onclick             : async (e: any) => { 
            let disconn:any = []
            selected_binds.forEach((el: any) => { disconn.push({ target_id: el.bind.this_blk_id, target_io_index: el.bind.this_io_index }) });
            content = await async_post( 'app_ide_logic', 'delete_binds', { 
                app_id          : application.id, 
                app_status      : application.status,
                elements        : disconn
            } )
            selected_binds = []
            await update_data(false)
        }
    },{
        text                : 'Delete Elements',
        color               : 'red',
        icon                : TrashCan,
        disabled            : selected.length === 0,
        with_confirmation   : true,
        conf_title          : "DELETE ELEMENTS",  
        conf_description    : (selected.length > 0) ? `Are you sure you want to delete selected elements?`: '',  
        conf_btn_accept_txt : 'DELETE',
        onclick             : async (e: any) => { 
            content = await async_post( 'app_ide_logic', 'delete_elements', { 
                app_id          : application.id, 
                app_status      : application.status,
                elements        : selected
            } )
            selected = []
            await update_data(false)
        }
    }, ])

    let edit_block_modal = $state()
    let edit_block       = $state()

    async function add_element(element: any, pos_x: number, pos_y: number){
        if (application.status) return
        const new_el = { type: element.type, id: element.el_id, name: element.el_name, group: element.el_group, x: pos_x, y: pos_y }

        content = await async_post( 'app_ide_logic', 'add_element', { 
            app_id          : application.id, 
            app_status      : application.status,
            element         : new_el
        } )

        await update_data(false)
    }


    async function on_edit_block(block: any){
        if (block.type !== "constant") return
        edit_block = JSON.parse( JSON.stringify(block) )
        edit_block_modal.open(120, 120)
    }


    async function move_event() {
        if (selected.length === 0) return

        selected.forEach((el: any) => { 
            const res = pos_to_grid(el.x, el.y)
            el.x = res[0]
            el.y = res[1]
        })

        const result: any = await async_post( 'app_ide_logic', 'move_elements', { 
            app_id          : application.id, 
            app_status      : application.status,
            elements        : selected
        } )

        if (result['result'] === 'ok')
            content = content
        else   
            update_data(true)
    }


    function pos_to_grid(x: number, y: number){
        let res = [x, y]

        if (x < 20)                          x = 20      //Check Boundries
        if (y < 20)                          y = 20
        if (x > (canvas.width  - blk_width)) x = canvas.width - blk_width
        if (y > canvas.height)               y = canvas.height - 40

        res[0] = Math.round(x / 20) * 20 //Stick to grid
        res[1] = Math.round(y / 20) * 20

        return res
    }    


    async function bind_elements(){
        if (path_connect.bind0_io.type === path_connect.bind1_io.type)
            return

        if (path_connect.bind0_io.type === path_connect.bind1_io.type){
            popup_add("ILLIGAL BIND", "Output Can Be Binded Only With Input")
            return 
        } 
        
        let trg_blk           : number = -1
        let trg_io            : string = ""
        let trg_io_indx       : number = -1
        
        let new_bind_blk      : number = -1
        let new_bind_io       : string = ""       
        let new_bind_io_indx  : number = -1 

        if (path_connect.bind0_io.type === "input") {
            trg_blk            = path_connect.bind0_block.id
            trg_io             = path_connect.bind0_io.id
            trg_io_indx        = path_connect.bind0_io_index
            
            new_bind_blk       = path_connect.bind1_block.id
            new_bind_io        = path_connect.bind1_io.id
            new_bind_io_indx   = path_connect.bind1_io_index
        } else if (path_connect.bind1_io.type === "input") {
            trg_blk            = path_connect.bind1_block.id
            trg_io             = path_connect.bind1_io.id
            trg_io_indx        = path_connect.bind1_io_index

            new_bind_blk       = path_connect.bind0_block.id
            new_bind_io        = path_connect.bind0_io.id
            new_bind_io_indx   = path_connect.bind0_io_index
        } else return //Just In Case, should never happen

        content = await async_post( 'app_ide_logic', 'bind_elements', { 
            app_id          : application.id, 
            app_status      : application.status,
            elements        : { 
                target_blk: trg_blk      , target_io:  trg_io,   target_io_indx : trg_io_indx,
                bind_blk:   new_bind_blk , bind_io: new_bind_io, bind_io_indx   : new_bind_io_indx,
            }
        } )

        update_data(false)
    }


    async function on_flip_datapoint(block: any){        
        content = await async_post( 'app_ide_logic', 'datapointsetget', { 
            app_id          : application.id, 
            app_status      : application.status,
            element         : block,
        })

        update_data(false)
    }  


    async function live_data(){
        let binds    : any = [] //finds all binds {block index, io inex, bind_name_, value}
        let bnds_ids : any = []
        
        content.forEach((blk:any, blk_index: number) => { //Find bind pointers
            blk.io.forEach((io:any, io_index: number) => {
                if (( io.type === 'input' ) && ( io.bind.bind_id !== undefined )){
                    const bind_name = `bind_${io.bind.bind_id}_${io.bind.bind_io_index}`
                    binds.push({block_index: blk_index, io_index: io_index, bind_name: bind_name, value: ''})
                    bnds_ids.push(`#${application.group}_${application.name}_${bind_name}#`) 
                }
            })
        })

        interval_live = setInterval(async () => { 
            if (bnds_ids.length === 0) return

            const run_data:any = await async_post( 'app_view', 'get_datapoints', { data_ids : bnds_ids } )

            if (run_data[0] === "APP_STOPPED"){
                clearInterval(interval_live)
                interval_live = -1
                await update_data(true) 
                return //App is stopped, nothing to read anymore
            }
            
            binds.forEach((bnd:any, bnd_index: number) => { 
                content[bnd.block_index].io[bnd.io_index].debug_value = run_data[bnd_index]
            })

            content = content
        }, 2000);   
    }

    
    async function update_data(upd_content = true){
        if (upd_content){
            content = await async_post( 'app_ide_logic', 'update', { 
                app_id          : application.id, 
                app_status      : application.status,
            } )
        }

        content.forEach((blk:any) => { //Find bind pointers
            blk.io.forEach((io:any, io_index: number) => {
                if (( io.type === 'input' ) && ( io.bind.bind_id !== undefined )){
                    io.bind.pointer_blk_index = content.findIndex((el: any) => el.id === io.bind.bind_id) //Target Blk
                    io.bind.pointer_io_index  = content[io.bind.pointer_blk_index].io.findIndex((el: any) => el.id === io.bind.bind_io)
                    io.bind.this_blk_id       = blk.id    //This Blk
                    io.bind.this_io_index     = io_index
                }
            })
        })


        const dps  = datapoints_to_tree(await async_post( 'app_ide_datapoints', 'update', { app_id: application.id, }))
        const blks = blocks_to_tree    (await async_post( 'system_tools', 'update_logic_grouped'))
        
        let new_active_tree : any = [...dps, ...blks]

        new_active_tree.forEach((gr_el:any) => {
            gr_el.submenu.forEach((el:any) => {
                el.ondropevent = async (e:any) => { 
                    const res = pos_to_grid(drop_element_event.x, drop_element_event.y)
                    await add_element(drop_element_event.buffer, res[0], res[1])
                    drop_element_event.enabled = false
                }

                el.ondragevent = async (e:any) => {
                    drop_element_event.buffer = {type: el.type, el_name: el.el_name, el_group: el.el_group, el_id: el.el_id}
                    drop_element_event.enabled = true
                }
            })
        })

        user.active_tree = new_active_tree
    }


    $effect(() => { (async () => {
        await update_data()
        if ( (application.status === true) && ( interval_live === -1) ) live_data()
    })() })  


    onMount(async () => {})
    onDestroy(async () => { clearInterval(interval_live) })  
</script>


<ContextMenu buttons={buttons} bind:this={context_menu}   /> 

<!-- svelte-ignore a11y_click_events_have_key_events -->
<div  id="editor" class="content-panel"  >
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <svg id="editor_svg" width="{canvas.width}" height="{canvas.height}" xmlns="http://www.w3.org/2000/svg" 
        oncontextmenu="{(e: any) => {
            context_menu.open_context(e.clientX, e.clientY)
            e.preventDefault()
        }}"    

        onpointerdown    = "{(e: any) => {            
            box_mode.on_start_box(e)

            if (!e.ctrlKey) { 
                selected        = []
                selected_binds  = []
            }            
        }}" 

        onpointerup    = "{(e: any) => {  
            box_mode.on_stop_box(e)
            content  = content
        }}"

        onpointermove  = "{(e: any) => {    
            box_mode.on_move_box(e)
        }}"
    >

<!-- Renderer Block --> 
    {#each content as block}  
        <LENBlock 
            bind:selected={selected} 
            bind:selected_binds={selected_binds}  
            bind:drag_event={drag_event}
            block={block} 
            blk_height={blk_height} blk_width={blk_width}  
            on_flip_datapoint= { async (e:any) => { await on_flip_datapoint(block) } }
            on_dblclick      = { async (e:any) => { await on_edit_block(block)     } }
        />   
    {/each} 
 

<!--  Connection Path -->  
    {#if (path_connect.enabled) } 
        <LENConnPath bind:path_connect={path_connect} is_debug={dev} />  
    {/if} 
  
<!-- Binds-->
    {#each content as block} 
        {#each block.io as io}
            {#if      io.type === "input" && io.bind.bind_id !== undefined }
                <LENBind 
                    bind:selected={selected} 
                    bind:selected_binds={selected_binds} 
                    content={content} 
                    block={block}  io={io}  
                    blk_height={blk_height} blk_width={blk_width} 
                    bind:is_live={application.status}
                />              
            {/if}
        {/each}                                              
    {/each}
      

<!-- IO -->
    {#each content as block} 
        {#each block.io as io, index}
            <LENIO 
                bind:path_connect={path_connect} 
                block={block} io={io} io_index={index} 
                blk_height={blk_height} blk_width={blk_width} 
                on_bind = { async (e:any) => { await bind_elements() }}
            />
        {/each}                                              
    {/each}
   
<!-- Box Selector -->
    <LENSelectionBox bind:this={box_mode} content={content} selection={selected} blk_height={blk_height} blk_width={blk_width} />

<!-- Drag Area -->
    {#if drag_event}
        <rect class="drag_area{dev ? '_debug': ''}"  style="fill: green;" 
            onpointermove  = "{(e: any) => {
                selected.forEach((el: any) => {
                    el.x = e.layerX + el.dX
                    el.y = e.layerY + el.dY
                });

                content  = content      
                e.stopImmediatePropagation()
            }}"

            onpointerup    = "{async (e: any) => {
                drag_event = false
                await move_event()
                e.stopImmediatePropagation()
            }}"
        />
    {/if}

    {#if drop_element_event.enabled}
        <rect class="drag_area{dev ? '_debug': ''}" style="fill: deepskyblue;" 
            ondragover = "{(e: any) => {
                drop_element_event.x = e.layerX
                drop_element_event.y = e.layerY
                e.stopImmediatePropagation()
            }}"
        />    
    {/if}
    
    {#if application.status}
        <rect class="drag_area{dev ? '_debug': ''}" style="fill: orange;"  
            onpointerdown = "{(e: any) => { e.stopImmediatePropagation() }}"
            onpointerup   = "{(e: any) => { e.stopImmediatePropagation() }}"
            onpointermove = "{(e: any) => { e.stopImmediatePropagation() }}"
            onclick       = "{(e: any) => { e.stopImmediatePropagation() }}"
        />    
    {/if}  
    </svg>
</div>


<Modal bind:this={edit_block_modal} title="Edit Block" >
    <div class="flex-item">
        <InputLabel label="Constant Value" bind:value={edit_block.io[0].value} />
    </div>
   

    <ButtonR text="Save" color="green" onclick={async (e:any) =>  {
        const result: any = await async_post( 'app_ide_logic', 'save_elements', { 
            app_id          : application.id, 
            app_status      : application.status,
            elements        : [ edit_block ]
        } )

        //Make raw edit of multiple objects
        edit_block_modal.close(e)
        await update_data(true)
    }} > <Edit class="round-btn-svg"/> </ButtonR>
</Modal>



<style>
    #editor { /*border: 1px solid grey;*/  width: 100%;  height: calc(100vh - 118px);  overflow: auto; }

    #editor_svg{
        position: relative;

        background-image: linear-gradient(#dfdfdf 1px, transparent 1px), linear-gradient(to right, #dfdfdf 1px, transparent 1px);
        background-size: 20px 20px;
        background-color: #ffffff;        
        
        background-position-x: 20px;
        background-position-y: 20px;

        /*
            https://10015.io/tools/css-background-pattern-generator
            fill="{selected_elements.includes(block) ? 'lightblue' : 'white'}"
        */
    }
</style>