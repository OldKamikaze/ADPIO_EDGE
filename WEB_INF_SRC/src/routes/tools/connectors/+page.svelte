
<script lang="ts">
    import { onMount, onDestroy }      from 'svelte'
    import { browser_params, user, async_get, async_post, get_cookie_value, initialize_user } from '../../state.svelte.ts';

    import { CE_SRC } from "../../../lib/app_engine.ts";
    import { PRIORITY_ARRAY_LIST, OBJECT_PROPERTIES } from "../../../lib/bacnet_lists.ts"    

    import DataTableEdit    from "../../adp_kit/components/DataTableEdit.svelte"
    import DataTable        from "../../adp_kit/components/DataTable.svelte"
    import Modal            from "../../adp_kit/components/Modal.svelte"
    import ControlPanel     from "../../adp_kit/components/ControlPanel.svelte"
    
    import {
        ExpandAll  ,
        CollapseAll,        
        Edit,
        ConnectionSignal,
        DataQualityDefinition,
        FolderParent,
        Run,
        SearchLocateMirror,
        DataBackup
    } from "carbon-icons-svelte"

    let datatable         = $state()
    let data = $state({
        header: "",
        colums: [
            //{name: "",              key: "panel",          row_style: "width: 28px;"}, 
            //{name: "id",            key: "id",             row_style: "", }, 

            {name: "src",           key: "src",            row_style: "", }, 
            {name: "net",           key: "net",            row_style: "", }, 

            {name: "device_id",     key: "device_id",      row_style: "", },   
            {name: "device_name",   key: "device_name",    row_style: "", }, 

            {name: "object_id",     key: "object_id",      row_style: "", }, 
            {name: "object_name",   key: "object_name",    row_style: "", },     
            
            {name: "value",         key: "value",          row_style: "", },  

            {name: "online",        key: "online",         row_style: "", }, 
            //{name: "last_updated",  key: "last_updated",   row_style: "", },           
            //{name: "binds",         key: "binds",          row_style: "", },         
        ],       
        data  : [],
        groups: [],          
    })

    let selected_records  = $state([])
    let interval_update = $state(-1)    
    let view_properties_modal = $state()

    let buttons = $derived([
        {
            text                : 'Collapse All',
            color               : 'normal',
            icon                : CollapseAll,
            onclick             : (e: any) => { datatable?.collapse_all() }
        }, {
            text                : 'Expand All',
            color               : 'normal',
            icon                : ExpandAll,
            onclick             : (e: any) => { datatable?.expand_all() }
        }, {
            text                : 'Read Object List',
            color               : 'normal',
            icon                : DataBackup,
            disabled            : selected_records.length > 0 && selected_records[0].src !== CE_SRC.BACnet_IP,
            onclick             : async (e: any) => { await async_post('connectors', 'add_task', [{ 'src': CE_SRC.BACnet_IP, 'cmd': 'read_device_list', 'params': { 'net': selected_records[0].net } }]) }
        }, {
            text                : 'Who Is? Lookup',
            color               : 'green',
            icon                : SearchLocateMirror ,
            disabled            : false,
            onclick             : async (e: any) => { await async_post('connectors', 'add_task', [{ 'src': CE_SRC.BACnet_IP, 'cmd': 'who_is', 'params': {} }]) }
        },

            /*{
                text                : 'Show Device Data',
                color               : 'normal',
                icon                : FolderParent ,
                disabled            : selected_device === undefined,

                onclick             : async (e: any) => { await show_data_modal() }
            }/*/
    ])

    async function  update() {
        data.data = await async_post( 'connectors', 'update' )
        datatable?.update_groups()
    }

    onMount(async () => { 
        user.active_header = 'CONNECTORS BROWSER'
        await update()
        interval_update = setInterval(async () => { await update() }, 2000)
    })

    onDestroy(async () => { clearInterval(interval_update) }) 
</script>

<div class="content-panel">
    <ControlPanel bind:buttons={buttons} />

    <div id="l_count">Lines: {data.data.length}</div>
</div>

<div class="content-panel"> 
    <DataTableEdit bind:this={datatable} bind:data={data}  bind:selected_rows={ selected_records } context_btns={buttons} selectable_rows={true}
        group="net"

        onselect={async (e: any) => { 
            if (selected_records.length === 0) return
            if ( selected_records[0].src !== CE_SRC.BACnet_IP ) return

            let props = ['object-name']
            const obj = selected_records[0].object_id.split(',')[0]
            if (OBJECT_PROPERTIES[obj].includes('present-value')) props.push('present-value')

            await async_post('connectors', 'add_task', [{ 'src': CE_SRC.BACnet_IP, 'cmd': 'read_properties_db', 'params': {
                id: selected_records[0].id, requests: props
            }}])
        }}
        
        ondblclick={async (e: any) => {
            if (selected_records.length === 0) return
            if ( selected_records[0].src !== CE_SRC.BACnet_IP ) return

            await async_post('connectors', 'add_task', [{ 'src': CE_SRC.BACnet_IP, 'cmd': 'read_properties_db', 'params': {
                id: selected_records[0].id, requests: ['all']
            }}])
            view_properties_modal?.open(120, 120)
        }}
    />
</div>

{#if (selected_records.length > 0)}
    <Modal bind:this={view_properties_modal} title="{selected_records[0].device_name}: {selected_records[0].object_name} [{selected_records[0].object_id}]" >
        {#each Object.keys(selected_records[0].properties) as key}
            <div>{key} = {selected_records[0].properties[key]}</div>
        {/each}
    </Modal>
{/if}


<style>
    #l_count { float: right;  }
</style>