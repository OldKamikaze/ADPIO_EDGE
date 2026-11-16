<script  lang="ts">
	let { 
        label     = "",
        item_list = [
            {name: "Item 1", value: "Value1"},
        ],

        value = $bindable(),

        width    = 240,
        readonly = false,

        onchange = (e: any) => {},
    } = $props();

    const r_id:string = $props.id()
</script>

<div style="width: {width}px;">
    {#if label !== "" }
        <label for="dropdown_{r_id}" class="dropdown-label">{label}</label>    
    {/if}

    {#if readonly}
        {#each item_list as item}
            {#if value === item.value}
                <span>{item.name} </span> 
            {/if}
        {/each}
    {:else}

        <select id="dropdown_{r_id}" class="dropdown-input"   bind:value="{value}" 
            onchange={(e:any) => { onchange(e) }}
        >
            {#each item_list as item}
                <option selected={value === item.value? true : false} value="{item.value}">
                    {item.name}
                </option>
            {/each}
        </select>    
    {/if}


</div>

<style>

</style>