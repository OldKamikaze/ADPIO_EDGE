<script  lang="ts">
	let { 
        label = "PASSWORD",
        value = $bindable(),

        minlength = 0,
        maxlength = 16,

        oninput   = function(e: any){},
        onkeydown = function(e: any){},
    
        width = 240,
    } = $props();

    const r_id = $props.id()

    let this_input: any =  $state()

    export function set_focus(){ this_input.focus() }
</script>

<div style="width: {width}px;">
    <span class="input-container">
        <input bind:this={this_input} type="password" id="input-text-password-{r_id}" required
            
            minlength  = {minlength}
            maxlength  = {maxlength}

            oninput   = {(e:any) => { oninput(e) }}
            onkeydown = {(e:any) => { onkeydown(e) }}
            
            bind:value={value}
        >

        <label for="input-text-password-{r_id}" class="input-label">{label}</label>
        <span  class="input-underline"></span>
    </span>
</div>

<style>

</style>