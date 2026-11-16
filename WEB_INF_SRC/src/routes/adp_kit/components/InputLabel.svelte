<script  lang="ts">
	let { 
        label = "",
        value = $bindable(),

        readonly  = false,
        minlength = 0,
        maxlength = 24,
    
        oninput   = function(e: any){},
        onkeydown = function(e: any){},

        width = 240,
    } = $props();

    const r_id = $props.id()

    let this_input: any =  $state()

    export function set_focus(){ this_input.focus() }
</script>

<div style="width: {width}px;">
    <span class="input-container {readonly? 'input-container-readonly' : ''}">
        {#if readonly}
            <input inputmode="text" id="input-text-{r_id}" required
                onkeydown ={(e:any) => { e.preventDefault() }}
                oninput   ={(e:any) => { e.preventDefault() }}

                value={value} 
            >
        {:else}
            <input bind:this={this_input} inputmode="text" id="input-text-{r_id}" required 
                minlength  = {minlength}
                maxlength  = {maxlength}
                
                oninput   = {(e:any) => { oninput(e) }}
                onkeydown = {(e:any) => { onkeydown(e) }}

                bind:value={value}
            >
        {/if}

        <label for="input-text-{r_id}" class="input-label">{label}</label>
        <span  class="input-underline"></span>
    </span>
</div>

<style>

</style>