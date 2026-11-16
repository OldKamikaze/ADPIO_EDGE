<script  lang="ts">
    import { onMount } from 'svelte'

    import {
        DATAPOINTS_PROPERTIES,
        DATA_TYPES,
        PROTOCOL_LIST,
        CE_SRC
    } from "../../../lib/app_engine.ts"

    import { 
        PRIORITY_ARRAY_LIST, 
        OBJECT_PROPERTIES 
    } from '../../../lib/bacnet_lists.ts'
 
    import { async_post } from '../../state.svelte.ts';

    import InputDropList from "../components/InputDropList.svelte"
    import InputLabel    from "../components/InputLabel.svelte"
    import InputNumber   from "../components/InputNumber.svelte"
    import InputSelector from '../components/InputSelector.svelte'
    import InputSwitch   from "../components/InputSwitch.svelte"
    import DataDisplay   from '../components/DataDisplay.svelte'
    

    let {
        data_list  = $bindable(),
        widget_list = $bindable([ //Bind name is a name of the field inside value_ibjec //use bind_sub_name for add on
            { type: 'InputLabel'   , group: "GROUP 1", label: "Test", bind_name: "field", visible: true, args: {
                minlength: 0, maxlength: 24, readonly: false
            }},

            { type: 'InputNumber'  , group: "GROUP 1", label: "Test", bind_name: "field", visible: true, args: {
                type: "int", //Float or Integer
                readonly: false, minvalue: 0, maxvalue: 100, step:1
            }},

            { type: 'InputSelector', group: "GROUP 2", label: "Test", bind_name: "field", visible: true, args: {
                item_list: [ {name: "Item 1", value: "Value1"}, ],
                readonly: false, not_equal: false //Used at multiselection for editing multiple objects
            }},

            { type: 'InputDropList', group: "GROUP 2", label: "Test", bind_name: "field", visible: true, args: {
                item_list: [ {name: "Item 1", value: "Value1"}, ],
                readonly: false,  minlength: 0,  maxlength: 24 
            }},
            
            { type: 'InputSwitch'  , group: "GROUP 3", label: "Test", bind_name: "field" , visible: true, args: {
                readonly: false
            }}, 

            { type: 'DataDisplayPropEdit'  , group: "GROUP 3", label: "Test", bind_name: "field" , visible: true, args: {
                readonly: false,  show_properties: false, label: ''
            }},

            { type: 'ProtocolEdit'  , group: "GROUP 3", label: "Test", bind_name: "protocol" , visible: true, args: {
                readonly: false, 
            }},

            { type: 'TrendEdit'  , group: "GROUP 3", label: "Test", bind_name: "protocol" , visible: true, args: {
                readonly: false, 
            }},

            { type: 'Label'  , group: "GROUP 3", label: "Test", bind_name: "field" , visible: true, args: {}},        
        ])
    } = $props()

    let widget_ready       = $state(false)
    let groups             = $state(['ALL'])
    let grp_selected       = $state('ALL')
    let connectors_list    = $state([])
    let bac_property_list  = $state([]) //Used for list of bac props


    let rendered_data = $state({})

    function on_value_change( wg:any, sub_filed?: any ){
        if (sub_filed === undefined) {
            data_list.forEach((ds:any) => {            
                ds[wg.bind_name] = rendered_data[wg.bind_name]
            }) 
        } else {            
            data_list.forEach((ds:any) => {      
                ds[wg.bind_name][sub_filed]  = wg.bind[sub_filed]
            })  
        }
    }


    function on_datatype_change(wg: any){        
        let passed = true //Detect if type was changed
        switch (wg.bind.datatype) {
            case "bool":
                wg.bind.value = false
                if (wg.bind.properties.type !== 'bool') wg.bind.properties = DATAPOINTS_PROPERTIES.bool
                break
            case "int":
                wg.bind.value = 0
                if (wg.bind.properties.type !== 'int')  wg.bind.properties = DATAPOINTS_PROPERTIES.int
                break
            case "float":
                wg.bind.value = 0.1
                if (wg.bind.properties.type !== 'float') wg.bind.properties = DATAPOINTS_PROPERTIES.float
                break
            case "str":
                wg.bind.value = "Text"
                if (wg.bind.properties.type !== 'str')   wg.bind.properties = DATAPOINTS_PROPERTIES.str
                break     
            default:
                passed = false
                console.log("Incorrect Data Type: " + wg.bind.datatype)
        }

        if (passed){
            on_datapoint_change(wg, 'datatype')
            on_datapoint_change(wg, 'value')        
            on_datapoint_change(wg, 'properties')
            wg.not_equal_type = false
        }
    }   
    
    
    function on_datapoint_change(wg: any, field:string){
        data_list.forEach((el:any) => { 
            el[field] = wg.bind[field]
        })         
    }

    function onpropertychange(wg: any, property: string){
        data_list.forEach((el:any) => { 
            el.properties[property] = wg.bind.properties[property]
        })  
    }    


	async function update_data(){
        if (data_list.length > 0) 
            rendered_data = JSON.parse( JSON.stringify( data_list[0] )) 
        else 
            return //some oopsie happened, empty data set
            
        widget_list.forEach((wg: any) => {
            if (!groups.includes(wg.group)) //Make group list
                groups.push(wg.group)    
                
            if (wg.type === 'DataDisplayPropEdit' || wg.type === 'TrendEdit' ) { wg['not_equal_type'] = false }
                
            if (data_list.length > 1)
                for (const ds of data_list){
                    if (rendered_data[wg.bind_name] !== ds[wg.bind_name]) {
                        rendered_data[wg.bind_name]  = '≠'
                        if (wg.type === 'DataDisplayPropEdit') wg['not_equal_type'] = true 

                        break
                    } 
                }

            //Fork Values
            if (wg.type === 'DataDisplayPropEdit') {
                wg['bind']  = JSON.parse( JSON.stringify( data_list[0] ))
            } else if (
                (wg.type === 'ProtocolEdit') ||
                (wg.type === 'TrendEdit')
            ){
                wg['bind']  = JSON.parse( JSON.stringify( data_list[0][wg.bind_name] ))
            } else 
                wg['bind'] = data_list[0][wg.bind_name]     

        })     

        widget_ready = true
    }


    onMount(async () => {
        await update_data()
    })

</script>


{#if widget_ready}

{#if groups.length > 2}
    <div class="filter">
        {#each groups as grp}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="{(grp_selected === grp)? 'selected_grp' : ''}"
                onpointerdown={() => { grp_selected = grp }}
            >{grp}</div>
        {/each}
    </div>
{/if}


<div class="data_edit_flex">
{#each widget_list as wg}
    {#if ((wg.visible) && ('bind' in wg) && ( (wg.group === grp_selected || grp_selected === 'ALL') ))}

<!-- BASIC TYPES -->
        {#if wg.type      === 'InputLabel'}
            <div class="data_edit_flex_left">{wg.label}</div>
            <div class="data_edit_flex_right">
                <InputLabel    label=""  bind:value={ rendered_data[wg.bind_name] } minlength={wg.args.minlength} maxlength={wg.args.maxlength} readonly={wg.args.readonly}
                    oninput={()=>{ on_value_change( wg ) }}
                />
            </div>
        {:else if wg.type === 'InputNumber'}
            <div class="data_edit_flex_left">{wg.label}</div>
            <div class="data_edit_flex_right">
                <InputNumber   label=""  bind:value={ rendered_data[wg.bind_name] } type={wg.args.type} readonly={wg.args.readonly} minvalue={wg.args.minvalue} maxvalue={wg.args.maxvalue} step={wg.args.step} 
                    onchange={()=>{ 
                        on_value_change( wg ) 
                    }}
                />
            </div>
        {:else if wg.type === 'InputSelector'}
            <div class="data_edit_flex_left">{wg.label}</div>
            <div class="data_edit_flex_right">
                <InputSelector label=""  bind:value={ rendered_data[wg.bind_name] } item_list={wg.args.item_list} readonly={wg.args.readonly}  
                    onchange={()=>{ on_value_change( wg ) }}
                />
            </div>
        {:else if wg.type === 'InputDropList'}
            <div class="data_edit_flex_left">{wg.label}</div>
            <div class="data_edit_flex_right">
                <InputDropList label=""  bind:value={ rendered_data[wg.bind_name] } item_list={wg.args.item_list} readonly={wg.args.readonly}  minlength={wg.args.minlength}  maxlength={wg.args.maxlength} 
                    onchange={()=>{ on_value_change( wg ) }}
                />
            </div>
        {:else if wg.type === 'InputSwitch'}
            <div class="data_edit_flex_left">{wg.label}</div>
            <div class="data_edit_flex_right">
                <InputSwitch   label=""  bind:value={ rendered_data[wg.bind_name] } readonly={wg.args.readonly} 
                    onchange={()=>{ on_value_change( wg ) }}
                />
            </div>
        {:else if wg.type === 'Label'}
            <div class="data_edit_flex_left"> {wg.label}</div>
            <div class="data_edit_flex_right">{rendered_data[wg.bind_name]}</div>            

    <!-- COMLEX TYPES -->
        {:else if wg.type === 'DataDisplayPropEdit'}
            <div class="data_edit_flex_left">Data Type</div>
            <div class="data_edit_flex_right">
                <InputSelector label=""  bind:value={ wg.bind.datatype } item_list={DATA_TYPES} readonly={false}  
                    onchange={()=>{ on_datatype_change( wg ) }}
                />
            </div>

<!-- Present Values-->
        {#if !wg.not_equal_type} 
            <div class="data_edit_flex_left">{wg.label}</div>
            <div class="data_edit_flex_right">
                <DataDisplay bind:datapoint={ wg.bind } readonly={wg.args.readonly} label={wg.args.label}
                    onchange={()=>{ on_datapoint_change( wg, 'value' ) }}
                />
            </div>
                
            <!--props-->      
            {#if ('show_properties' in wg.args) && (wg.args.show_properties)}                    
                {#if  wg.bind.datatype === 'bool'}
                    <div class="data_edit_flex_left">Disabled Text</div>
                    <div class="data_edit_flex_right"><InputLabel label="" bind:value={wg.bind.properties.text_false}
                        oninput={()=>{onpropertychange(wg, 'text_false') }}
                    /></div>
                        
                    <div class="data_edit_flex_left">Enabled Text</div>
                    <div class="data_edit_flex_right"><InputLabel label="" bind:value={wg.bind.properties.text_true}
                        oninput={()=>{onpropertychange(wg, 'text_true') }}
                    /></div>
                        
                {:else if  wg.bind.datatype === 'int'}
                    <div class="data_edit_flex_left">Minimum Value</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.min}  step={1} minvalue={-999999999999999} maxvalue={999999999999999}
                       onchange={()=>{ onpropertychange(wg, 'min') }}
                    /></div>
                        
                    <div class="data_edit_flex_left">Maximum Value</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.max}  step={1} minvalue={-999999999999999} maxvalue={999999999999999}
                        onchange={()=>{ onpropertychange(wg, 'max') }}
                    /></div>
                        
                    <div class="data_edit_flex_left">Steps</div> 
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.step} step={1} minvalue={0}  maxvalue={1000}
                        onchange={()=>{ onpropertychange(wg, 'step') }}
                    /></div>
                        
                {:else if  wg.bind.datatype === 'float'}
                    <div class="data_edit_flex_left">Minimum Value</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.min} minvalue={-999999999999999} maxvalue={999999999999999}
                        onchange={()=>{ onpropertychange(wg, 'min') }}
                    /></div>    
                        
                    <div class="data_edit_flex_left">Maximum Value</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.max}  minvalue={-999999999999999} maxvalue={999999999999999}
                        onchange={()=>{ onpropertychange(wg, 'max') }} 
                    /></div>    
                        
                    <div class="data_edit_flex_left">Decimal Places</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.decimals} step={1} minvalue={0} maxvalue={64}
                       onchange={()=>{ onpropertychange(wg, 'decimals') }}
                    /></div>    
                        
                    <div class="data_edit_flex_left">Step</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value={wg.bind.properties.step} type="float"  step={0.1} minvalue={0} maxvalue={1000}
                        onchange={()=>{ onpropertychange(wg, 'step') }}
                    /></div>                        
                        
                {:else if  wg.bind.datatype === 'str'}
                    <div class="data_edit_flex_left">Text Max Length</div>
                    <div class="data_edit_flex_right"><InputNumber label="" bind:value="{wg.bind.properties.length}"  minvalue={1} maxvalue={1024}
                        onchange={()=>{ onpropertychange(wg, 'length') }}
                    /></div>
                {/if}   
            {/if}      
        {:else} 
            <div class="data_edit_flex_left"></div> 
            <div class="data_edit_flex_right" style="color:crimson">Different Data Types</div>
        {/if}


<!-- Protocols -->
        {:else if wg.type === 'ProtocolEdit'}
            <div class="data_edit_flex_left">Connectors</div>
            <div class="data_edit_flex_right">
                <InputDropList label=""  bind:value={ wg.bind.connector_id } item_list={connectors_list} readonly={wg.args.readonly}  minlength={1}  maxlength={32} 
                    onfocus={async (e:any) => { 
                        connectors_list = await async_post( 'connectors', 'connectors_list' ) 
                    } }

                    onchange={async (e:any, item: any) => { 
//                        if (item !== undefined){
//                            wg.bind.src = item.item.src
//                            wg.bind.net = item.item.net
//
//                            wg.bind.device_id   = item.item.device_id
//                            wg.bind.device_name = item.item.device_name
//
//                            wg.bind.object_id   = item.item.object_id
//                            wg.bind.object_name = item.item.object_name
//                        } else {
//                            wg.bind.device_name = 'Not Found'
//                            wg.bind.object_name = 'Not Found'
//                        }
//                        
                        on_value_change( wg, 'connector_id' )
                    } }
                />                        
            </div>

<!-- BACnet Specific -->
            {#if wg.bind.connector_id.includes( CE_SRC.BACnet_IP )}
                <div class="data_edit_flex_left">Property</div>
                <div class="data_edit_flex_right">
                    <InputDropList label=""  bind:value={ wg.bind.bac_property } item_list={bac_property_list} readonly={wg.args.readonly}  minlength={1}  maxlength={24} 
                        onchange={()=>{ on_value_change( wg, 'bac_property' ) }}
                        onfocus={async (e:any) => { 
                            const splt = wg.bind.connector_id.split('::')
                            if (splt.length !== 3) return
                            const obj = splt[2].split(',')[0]

                            if (OBJECT_PROPERTIES[obj] !== undefined) 
                                OBJECT_PROPERTIES[obj].forEach((el: string) => { bac_property_list.push({"name": el, "value": el}) })
                        }}                                    
                    />
                </div>

                <div class="data_edit_flex_left">Read Enable</div>
                <div class="data_edit_flex_right">
                    <InputSwitch   label=""  bind:value={ wg.bind.bac_read_enable } readonly={wg.args.readonly} 
                        onchange={()=>{ on_value_change( wg, 'bac_read_enable' ) }}
                    />
                </div>

                {#if wg.bind.bac_read_enable}
                    <div class="data_edit_flex_left">Read Refresh</div>
                    <div class="data_edit_flex_right">
                        <InputNumber label="" bind:value={wg.bind.bac_read_refresh} step={1} minvalue={0}  maxvalue={9999}
                            onchange={()=>{ on_value_change( wg, 'bac_read_refresh' ) }}
                        />
                    </div>
                {/if}                            
            {/if}


<!-- Temporary Disabled
            <div class="data_edit_flex_left">Protocol</div>
            <div class="data_edit_flex_right">
                <InputSelector label=""  bind:value={ wg.bind.src } item_list={PROTOCOL_LIST} readonly={wg.args.readonly}  
                    onchange={()=>{ 
                        console.log('broken')
                        wg.bind.connector_id = `${wg.bind.src}[${wg.bind.net}]:${wg.bind.object_id}`
                        if (wg.bind.src === 'none') wg.bind.connector_id = ""
                        on_value_change( wg, 'src' )                             
                    }}
                />
            </div>

            <div class="data_edit_flex_left">Network:</div>
            <div class="data_edit_flex_right">
                <InputLabel label=""  bind:value={ wg.bind.net } readonly={wg.args.readonly}  minlength={1}  maxlength={32} 
                    oninput={()=>{ 
                        console.log('broken')
                        wg.bind.connector_id = `${wg.bind.src}:${wg.bind.device_id}-${wg.bind.object_id}`
                        on_value_change( wg, 'net' )  
                    }}
                /> 
            </div>                    

            {#if wg.bind.src  !== CE_SRC.None}
                <div class="data_edit_flex_left">Device: { wg.bind.device_name }</div>
                <div class="data_edit_flex_right"> ID: { wg.bind.device_id }</div>
                   
                <div class="data_edit_flex_left">Object: { wg.bind.object_name }</div>
                <div class="data_edit_flex_right">
                    <InputLabel label=""  bind:value={ wg.bind.object_id } readonly={wg.args.readonly}  minlength={1}  maxlength={32} 
                        oninput={()=>{ 
                            console.log('broken')
                            wg.bind.connector_id = `${wg.bind.src}:${wg.bind.device_id}-${wg.bind.object_id}`
                            on_value_change( wg, 'object_id' )  
                        }}
                    />    {/if}

                </div> 
-->


<!-- Trend Edit -->
        {:else if wg.type === 'TrendEdit'}
            <div class="data_edit_flex_left">Trend Enable</div>
            <div class="data_edit_flex_right">
                <InputSwitch   label=""  bind:value={ wg.bind.enable } readonly={wg.args.readonly} 
                    onchange={()=>{ on_value_change(wg, 'enable') }}
                />
            </div> 

            {#if wg.bind.enable}
                <div class="data_edit_flex_left">Refresh Rate</div>
                <div class="data_edit_flex_right">
                    <InputNumber label="" bind:value={wg.bind.refresh} step={1} minvalue={0}  maxvalue={9999}
                        onchange={()=>{ on_value_change(wg, 'refresh') }}
                    />
                </div>
            {/if}

        {:else}
            <div class="data_edit_flex_left">Unknown type: {wg.bind_name}</div>
            <div class="data_edit_flex_right"></div>
        {/if}  
    
    {/if}
{/each}
</div>

{:else}
    <div>Loading...</div>
{/if}


<style>
    .filter{
        display: flex; /* or inline-flex */
        flex-wrap: wrap;
        justify-content: flex-start;
    }

    .filter > div {
        margin-right: 16px;
        /*background-color: rgb(158, 255, 179);*/
        padding: 0.4em 1.2em;
        vertical-align: middle;
        text-align: center;

        cursor: pointer;
    }

    .selected_grp{
        /*background-color: rgba(83, 179, 252, 0.8);*/
        border-bottom: 2px solid #ff9800;
    }

    .data_edit_flex { 
        display: flex;   
        flex-wrap: wrap;
        width: 100%;
    }
    
    .data_edit_flex > div {
        padding: 4px 0;
        vertical-align: middle;
    }

    .data_edit_flex_left {
        flex: 1 1 calc(35% - 12px);
        /*background-color: rgb(255, 224, 224);*/
    }

    .data_edit_flex_right {
        flex: 1 1 calc(65% - 12px);
        /*background-color: rgb(236, 255, 209);*/
    }
    
</style>
