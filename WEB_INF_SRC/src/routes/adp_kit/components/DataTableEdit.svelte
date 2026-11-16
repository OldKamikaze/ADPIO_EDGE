<script  lang="ts">
    //import { 
    //  update_data_groups
    //} from "../../stores" 

    import ContextMenu      from "./ContextMenu.svelte"
    import SignalPanel      from "./SignalPanel.svelte"

    import { ChevronUp } from 'carbon-icons-svelte';


    let {
        data = $bindable( {
            header: "Name Of the Table",
            colums: [
                {name: "",            key: "panel", row_style: ""},
                {name: "User",        key: "user",  row_style: ""},
                {name: "Profile",     key: "prof",  row_style: ""},
                {name: "Description", key: "desc",  row_style: ""}
            ],
            groups: [ {name: 'No Group', expand: true} ],        
            data: [ {
                user_name_value  :   "name",
                profile_value    :   "profile",
                description_value:   "description",
            }],
        }),

        selected_rows   = $bindable(),
        group           = "",
        selectable_rows = true,
        fill_height     = true,

        onselect        = (e: any) => {},
        ondblclick      = (e: any) => {},
        oncontextmenu   = (e: any) => {},

        context_btns          = [],
        context_btns_disabled = false        
    } = $props()
    
    let context:any = $state()

    export function update_groups(){
        var lst:any = []
        data.data.forEach((el:any) => {
          if (!lst.includes(el[group]) && (el[group] !== "")){ lst.push(el[group]) }
        })
    
        let groups: any = []
        lst.forEach((el:any) => { groups.push( { name: el, value: el, expand: true } ) })
    
        data.groups = groups
    }

    export function collapse_all(){ data.groups.forEach( (el:any) => { el.expand = false } ) }
    export function expand_all()  { data.groups.forEach( (el:any) => { el.expand = true } ) }
</script>


{#if context_btns.length > 0}
    <ContextMenu buttons={context_btns} bind:this={context}   /> 
{/if}


<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div class="datatable  {fill_height? 'auto_height' : 'auto_height_auto'}" 
    oncontextmenu="{(e: any) => {
        if (( context_btns.length === 0 ) || (context_btns_disabled)) return
        oncontextmenu(e)
        if ( context_btns.length > 0 ) {
            context.open_context(e.clientX, e.clientY)
            e.preventDefault()
        } 
    }}"

    onmousedown={(e: any) => {
        selected_rows = []
        onselect(e)
    }}    
>

    {#if data.header !== ''}
        <div class="content-panel-header">{data.header}</div>
    {/if}

    <table>
        <thead>
            <tr>
                {#each data.colums as col}
                    <th style="{col.row_style}"><span>{col.name}</span></th>
                {/each}
            </tr>
        </thead>

        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <tbody>
            {#each data.groups as gr}
                <tr class="row_group" >
                    <td colspan="{data.colums.length}"
                        onclick={() => { gr.expand = !gr.expand }}
                    >
                        <span class="row_group_icon {gr.expand ? 'row_group_icon_180' : '' } ">
                            <ChevronUp/>
                        </span>

                        <span>{gr.name}</span>
                    </td>
                </tr>  


                {#each data.data as row}            
                {#if gr.name === row[group] &&  gr.expand === true}
                    <tr class="{ selected_rows?.includes(row)? 'row_selected' : '' }">
                        {#each data.colums as col}
                            <td 
                                ondblclick="{(e: any) =>{ 
                                    selected_rows = []
                                    if (!selectable_rows) return
                                    selected_rows?.push( row ) 
                                    ondblclick(e) 
                                    e.preventDefault()
                                }}"

                                onmousedown="{(e: any) => {
                                    if (!selectable_rows) return  
                                    e.stopPropagation()
                                }}" 

                                onmouseup="{(e:any) => {
                                    if (!selectable_rows) return
                                    if (!e.ctrlKey) selected_rows = [] //Ctrl Key Clicked, clear item list

                                    if (selected_rows?.includes( row )) {
                                        if ((e.button === 0) && (e.ctrlKey)) //Delete element only on left btn click
                                            selected_rows?.splice( selected_rows.indexOf(row), 1 )
                                        data = data
                                    } else {
                                        selected_rows?.push( row )
                                        data = data
                                    }
                                    onselect(e)
                                    e.preventDefault()
                                }}"                                
                            >   
                                {#if col.key === 'panel'}
                                    <SignalPanel dash={row[col.key]} />
                                {:else}
                                    <span>{row[col.key]}</span>
                                {/if}
                            </td>                    
                        {/each}
                    </tr>
                {/if}    
                {/each}

            {/each}
        </tbody>
    </table> 
</div>


<style>

</style>