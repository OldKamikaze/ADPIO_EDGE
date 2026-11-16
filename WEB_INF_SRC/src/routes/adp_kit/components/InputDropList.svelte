<script  lang="ts">
    import {
        DataAdd
    } from "carbon-icons-svelte"    

	let { 
        label = "",
        value = $bindable(),
        item_list = [
            {name: "Item 1", value: "Value1"},
        ],

        readonly = false,

        minlength = 0,
        maxlength = 48,
        width     = 240,

        onchange = function(e: any, item_selected: any = undefined){},
        onfocus  = function(e: any){},
    } = $props();

    const r_id:string = $props.id()
    let   this_el = $state()
    let   old_val = $state('')

</script>


<div style="width: {width}px;">
    <span class="input-container {readonly? 'input-container-readonly' : ''}">
        {#if readonly}
            {#each item_list as item}
                {#if value === item.value}
                    <span>{item.name} </span> 
                {/if}
            {/each}
        {:else}
            <input bind:this={this_el}  id="dropdown_{r_id}" list="dropdown_{r_id}_list" name="dropdown_{r_id}"  required
                bind:value="{value}" 

                minlength  = {minlength}
                maxlength  = {maxlength}

                onfocus    = {(e:any) => { onfocus(e) }}

                onblur  = {(e:any) => {//In Case nothing was selected from dropdown after btn pust
                    if (value === '' && old_val !== '') value = old_val
                    old_val = ''
                }}
                oninput = {(e:any) => { 
                    let item: any = undefined
                    item = item_list.find((el: any) => el.value === value)
                    
                    onchange( e, item ) 
                }}
            />            

            <datalist id="dropdown_{r_id}_list" 
                onselect={(e:any) => { onchange(e) }}
            >
                {#each item_list as item}
                    <option  value="{item.value}" >
                        {item.name}
                    </option>
                {/each}
            </datalist>   

            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="picker" onclick={()=>{
                old_val = value
                value = ''
                this_el.focus()
                this_el.showPicker()
            }}><DataAdd /></div>
        {/if}

        <label for="input-text-{r_id}" class="input-label">{label}</label>
        <span  class="input-underline"></span>
    </span>
</div>

<style>
    .picker{
        position: absolute;
        top: 4px;
        right: -18px;
        cursor: pointer;
        &:hover {
            color: #ff9800; 
            transition: all 0.3s ease;     
        }
    }

   
</style>