<script  lang="ts">
    import { onMount, onDestroy }      from 'svelte'
    import { browser_params, user, async_get, async_post, get_cookie_value, initialize_user, popup_add, sleep, datapoints_to_tree } from '../../state.svelte.ts'
    import { build_app, run_app, stop_app, DATAPOINTS_PROPERTIES, UNITS_LIST} from '../../../lib/app_engine.ts'

    import {
        Add,
        TrashCan,
        Save,
        ExpandAll  ,
        CollapseAll,
        Edit,
        QqPlot,
        Boolean,
        StringText,
        CharacterDecimal,
        CharacterWholeNumber,
        ConnectionSignal,
    } from "carbon-icons-svelte"
    

    import DataTableEdit from "../../adp_kit/components/DataTableEdit.svelte"
    import Modal         from "../../adp_kit/components/Modal.svelte"
    import ButtonR       from "../../adp_kit/components/ButtonR.svelte"
    import DataDisplay   from '../../adp_kit/components/DataDisplay.svelte'
    import FlexDataEdit  from '../../adp_kit/layout/FlexDataEdit.svelte'

    
    let {
        application = $bindable(),    
    } = $props()

    let datatable = $state()
    let data = $state({
        header: "DATAPOINTS",
        colums: [
          //{name: "ID",           key: "id",           row_style: "", }, 
            {name: "",             key: "panel",        row_style: "width: 96px;"}, 
            {name: "NAME",         key: "name",         row_style: "", },             
          //{name: "WRITABLE",     key: "writable",     row_style: "", },
          //{name: "DATATYPE",     key: "datatype",     row_style: "width: 48px;", },
            {name: "VALUE",        key: "value",        row_style: "", },
            {name: "UNITS",        key: "units",        row_style: "width: 48px;", },   
            {name: "DESCRIPTION",  key: "description",  row_style: "", },     
          //{name: "MEMALLOC",      row_style: "", },
        ],
        groups: [ {name: 'No Group', value: 'No Group',  expand: true} ],        
        data: [],
    })

    let write_dp_modal = $state()
    let save_modal     = $state()

    let selected_datapoints = $state([])
    let editmode_datapoints = $state([])
    let interval_datapoints = $state(-1)

    let buttons = $derived([{
        text                : 'Collapse All',
        color               : 'normal',
        icon                : CollapseAll,
        onclick             : (e: any) => { datatable?.collapse_all() }
    }, {
        text                : 'Expand All',
        color               : 'normal',
        icon                : ExpandAll,
        onclick             : (e: any) => {  datatable?.expand_all() }
    }, {
        text                : 'Add Datapoint',
        color               : 'normal',
        icon                : Add,
        disabled            : false,
        rendered            : !application.status,
        onclick             : async (e: any) => { await new_datapoint() }
    }, {
        text                : 'Edit Datapoint',
        color               : 'normal',
        icon                : Edit ,
        disabled            : selected_datapoints.length === 0,
        onclick             : async (e: any) => { await edit_datapoints() }
    }, {
        text                : 'Delete Datapoint',
        color               : 'red',
        icon                : TrashCan,
        disabled            : selected_datapoints.length === 0,
        rendered            : !application.status,
        with_confirmation   : true,
        conf_title          : 'DELETE DATAPOINTS',  
        conf_description    : (selected_datapoints.length > 0) ? `Are you sure you want to delete: ${get_point_list(selected_datapoints)}?`: '', 
        conf_btn_accept_txt : 'DELETE',
        onclick             : async (e: any) => { await delete_datapoints() }
    }, ])

    let edit_modal_flex = $state([
        { type: 'InputLabel'   , group: "TAGS", label: "Name",         bind_name: 'name', visible: true, args: {
            minlength: 2, maxlength: 16, readonly: false
        }},
        
        { type: 'InputLabel'   , group: "TAGS", label: "Description", bind_name: 'description', visible: true, args: {
            minlength: 4, maxlength: 128, readonly: false
        }}, 
        
        { type: 'InputDropList', group: "TAGS", label: "Group",       bind_name: 'group', visible: true, args: {
            item_list: data.groups,
            readonly: false,  minlength: 0,  maxlength: 16 
        }},         
        /*{ type: 'InputSelector', group: "VALUE", label: "Writable", bind_name: "writable", visible: true, args: {
            item_list: READ_WRITE,
            readonly: false, not_equal: false //Used at multiselection for editing multiple objects
        }},   */
        { type: 'InputSwitch'  , group: "VALUE", label: "Writable", bind_name: "writable", visible: true, args: {
            readonly: false
        }},                     
        { type: 'DataDisplayPropEdit'  , group: "VALUE", label: "Present Value", bind_name: "value" , visible: true, args: {
            readonly: false,  show_properties: true,
        }},
        { type: 'InputDropList', group: "VALUE", label: "Units",       bind_name: 'units', visible: true, args: {
            item_list: UNITS_LIST,
            readonly: false,  minlength: 0,  maxlength: 16 
        }}, 
//Trend            
        { type: 'TrendEdit'  , group: "TREND", label: "Enable Trend", bind_name: "trend" , visible: true, args: {
            readonly: false, 
        }},
//Protocol Integration
        { type: 'ProtocolEdit'  , group: "NET", label: "Integration", bind_name: "protocol", visible: true, args: {
            readonly: false
        }},  
    ])

    async function new_datapoint(){
        let attachtogroup = "No Group"
        if (selected_datapoints.length > 0) attachtogroup = selected_datapoints[0].group

        const new_dp = {
            name         : 'Point ' + (data.data.length + 1),
            description  : '',
            group        : attachtogroup,  

            datatype     : "float",
            value        : "0.1",  
            units        : '',
            writable     : false,

            properties   : DATAPOINTS_PROPERTIES.float,
            protocol     : {
                connector_id     :"", 
                //src              :"none", 
                //net              :"none", 

                //device_id        : "", 
                //object_id        : "", 

                //device_name      : "", 
                //object_name      : "",
                
                bac_read_enable  : false,
                bac_property     : "presentValue",
                bac_read_refresh : 10,   
            },
            trend        : {enable: false, refresh: 300},

            newpoint     : true
        } 

        editmode_datapoints = [ JSON.parse( JSON.stringify(new_dp) ) ]
        save_modal?.open(120, 120) 
    }


    async function edit_datapoints(){
        if (selected_datapoints.length === 0) return
        
        editmode_datapoints = JSON.parse(JSON.stringify(selected_datapoints))
        editmode_datapoints[0].newpoint = false

        if (application.status)
            write_dp_modal?.open(120, 120)
        else
            save_modal?.open(120, 120) 
    }    


    function get_point_list(points:any){
        let list: string = ""
        points.forEach((el:any) => { list += `${el.name}, ` } ) 
        list = list.substring(0, list.length - 2)
        return list
    }

    async function write_live_data() {
        if (editmode_datapoints.length < 1) return

        let dps_ids: any = []
        let value_to_write: any = editmode_datapoints[0].value       

        editmode_datapoints.forEach((el:any) => {
            dps_ids.push({'data_id': `${application.group}_${application.name}_${el.group}_${el.name}`, 'value': value_to_write})
        })

        const run_data = await async_post( 'app_view', 'set_datapoints',  { data_ids : dps_ids } )
    }    


    async function delete_datapoints(){
        if (selected_datapoints.length > 0){
            let el_set:any = []
            selected_datapoints.forEach(async (el: any) =>  { el_set.push({ id: el.id}) })
            data.data = await async_post( 'app_ide_datapoints', 'delete_datapoints', { app_id: application.id, datapoints: el_set } )
        }

        selected_datapoints = []
        update_data()
    }

    async function live_data(){
        let dps_ids: any = []
        data.data.forEach((el:any) => {
            dps_ids.push(`${application.group}_${application.name}_${el.group}_${el.name}`) 
        })

        interval_datapoints = setInterval(async () => {      
            if (data.data.length === 0) return

            const run_data:any = await async_post( 'app_view', 'get_datapoints', { data_ids : dps_ids } )

            if (run_data[0] === "APP_STOPPED"){
                clearInterval(interval_datapoints)
                interval_datapoints = -1
                await update_data() 
                return //App is stopped, nothing to read anymore
            }

            data.data.forEach((el: any, indx: number) => { el.value = run_data[indx] })
            data.data = data.data
        }, 1000)
    }    


    async function update_data(){
        data.data = await async_post( 'app_ide_datapoints', 'update', { app_id: application.id, app_status: application.status } )
        user.active_tree = datapoints_to_tree(data.data)

        data.data.forEach((el: any) => {
            el.panel = []

            switch (el.datatype) {
                case "int":
                    el.panel.push({ icon: CharacterWholeNumber,  color: "blue", text: 'Integer'})
                    break;
                case "float":
                    el.panel.push({ icon: CharacterDecimal,      color: "blue", text: 'Float Number'})
                    break;
                case "bool":
                    el.panel.push({ icon: Boolean,               color: "blue", text: 'Boolean'})
                    break;
                case "str":
                    el.panel.push({ icon: StringText,            color: "blue", text: 'String'})
                    break;                                        
                default: el.panel.push({ icon: Error,    color: "red", text: 'Unknown Datatype'})
            }
        
            if (el.writable)        el.panel.push({ icon: Edit,    color: "green", text: 'Datapoint Writable'})
            else                    el.panel.push({ icon: Edit,    color: "off"  , text: 'Datapoint Read Only'}) 
            if (el.trend.enable)    el.panel.push({ icon: QqPlot,  color: "green", text: `Trend Refresh ${el.trend.refresh}sec.`})
            else                    el.panel.push({ icon: QqPlot,  color: "off"  , text: 'Trend Disabled'})        
            if (el.protocol.connector_id !== '') el.panel.push({ icon: ConnectionSignal, color: "green", text: 'Protocol Integration Enabled'})
            else                                 el.panel.push({ icon: ConnectionSignal, color: "off"  , text: 'Protocol Integration Disabled'})
        });

        datatable?.update_groups()        
    }


    $effect(() => { (async () => {
        await update_data()
        if ( (application.status === true) && (interval_datapoints === -1) ) live_data()
    })() })    

    //onMount(async () => {  })
    onDestroy(async () => { clearInterval(interval_datapoints)  })  
</script>

<div class="content-panel" >
    <DataTableEdit 
        bind:this={datatable} bind:data={data} context_btns={buttons} group="group" 
        bind:selected_rows={selected_datapoints}
    
        onselect={(e: any) => { }}        
        ondblclick={(e: any) => {
            edit_datapoints() //In edit and live mode
        }}
    />

</div>

<Modal bind:this={save_modal} title="Edit Datapoints" >
    <div  class="edit_data_mod">
        <FlexDataEdit bind:data_list={editmode_datapoints} bind:widget_list={edit_modal_flex} />
    </div>
    
    <ButtonR text="Save" color="green" onclick={async (e:any) =>  {
        if (editmode_datapoints[0].newpoint){ 
            data.data = await async_post( 'app_ide_datapoints', 'add_datapoints', { 
                app_id: application.id, 
                datapoints: editmode_datapoints,
            } ) 
        } else {
            data.data = await async_post( 'app_ide_datapoints', 'save_datapoints', { 
                app_id    : application.id, 
                datapoints: editmode_datapoints,
            } )
        }
        
        save_modal?.close(e)
        await update_data()
    }} ><Save class="round-btn-svg" /></ButtonR> 
</Modal>     

<Modal bind:this={write_dp_modal} title="Write Values" > 
    {#if editmode_datapoints.length > 0}
        {#if editmode_datapoints[0].datatype      === '≠'}
            <div class="flex-item">Simultaneous Editing Is Impossible, Different Datatypes</div>
        {:else if editmode_datapoints[0].writable !== true}
            <div class="flex-item">Simultaneous Editing Is Impossible, Some Datapoints Read Only</div>            
        {:else}
            <div class="flex-item">
                <DataDisplay readonly={false} bind:datapoint="{editmode_datapoints[0]}" />
            </div>

            <ButtonR text="Write Value" color="green" onclick={async (e:any, ) =>  {
                write_dp_modal.close(e)
                await write_live_data()
            }} > <Edit class="round-btn-svg"/> </ButtonR>
        {/if}
    {:else}    
        <div>LOADING...</div>
    {/if}
</Modal>


<style>

</style>