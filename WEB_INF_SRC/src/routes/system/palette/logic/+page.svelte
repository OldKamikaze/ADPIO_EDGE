
<script lang="ts">
    import { onMount }          from 'svelte'
    import { user, async_post } from '../../../state.svelte.ts';

    import DataTableEdit from "../../../adp_kit/components/DataTableEdit.svelte"
    import Modal         from "../../../adp_kit/components/Modal.svelte"
    import ControlPanel  from "../../../adp_kit/components/ControlPanel.svelte"
    
    import {
        ExpandAll  ,
        CollapseAll,
        BuildImage,
        Information
    } from "carbon-icons-svelte"  


    let datatable = $state()
    let data      = $state({
        header: "",
        colums: [
            {name: "ID",           key: "id"   ,        row_style: ""}, 
            {name: "NAME",         key: "name"     ,    row_style: ""},
            {name: "DESCRIPTION",  key: "description" , row_style: ""},
        ],
        groups: [
            {name: 'No Group', expand: true}
        ],        
        data: [],
    })
    let selected_el = $state()

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
            text                : "Show Element's Info",
            color               : 'normal',
            icon                : Information,
            disabled            : selected_el?.length === 0,
            onclick             : (e: any) => { info_modal?.open(120, 120) }
        }, {
            text                : 'Rebuild Database',
            color               : 'red',
            icon                : BuildImage,
            with_confirmation   : true,
            conf_title          : "Are you sure you want to rebuild database?",  
            conf_description    : 'Some data may be lost during this action.',
            conf_btn_accept_txt : 'RERBUILD',
            onclick             : async (e: any) => { 
                data.data = await async_post( 'system_tools', 'rebuild_logic_db' )  
            }
        },         
    ])

    let info_modal = $state()

    async function update_data(){
        data.data = await async_post( 'system_tools', 'update_logic' )
        datatable?.update_groups()
    }

    onMount(async () => { 
        user.active_header = 'LOGIC PALETTE'
        update_data() 
    }) 
</script>



<div class="content-panel">
    <ControlPanel buttons={buttons} />
</div>

<div class="content-panel">
    <DataTableEdit bind:this={datatable} bind:selected_rows={selected_el} bind:data={data} context_btns={buttons} group="group" 
        ondblclick={() => { info_modal?.open(120, 120) }}
    />
</div>


<Modal bind:this={info_modal} title="Info: {selected_el?.at(0).name}" > 
    <div>
        <div class="flex-item">Type:        {selected_el?.at(0).type}         </div>
        <div class="flex-item">Description: {selected_el?.at(0).description}  </div>
        <div class="flex-item">Function:    {selected_el?.at(0).function}     </div>
        <div class="flex-item">Lib Import:  {selected_el?.at(0).libimport}    </div>
        <div class="flex-item">IO:          </div>

        {#each selected_el?.at(0).io as rec}
            <div class="flex-item">{JSON.stringify(rec)} </div>
        {/each}
    </div>
</Modal>


<style>
</style>