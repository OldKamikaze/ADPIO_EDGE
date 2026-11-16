<script  lang="ts">
	let { 
        label     = "",
        value     = $bindable()   ,
        type      = "int", //Float or Integer

        readonly  = false,

        minvalue  = 0,
        maxvalue  = 100,
        step      = 1,
        limits    = true,
        decimals  = 2,

        onchange = function(e: any){    },

        width = 240,
    } = $props();


    const r_id:string = $props.id()
    let focused = $state(false)
    //let inpt    = $state(undefined)

    function check_pattern(e: any){
        var numberRegex: any = /^\d+$/; //Numbers only
        
        if (e)
            switch (e.keyCode) {
                case 37: //'ArrowLeft':
                case 39: //'ArrowRight':
                case 8 : //'Backspace':
                case 46: //'Delete':
                case 36: //'Home':
                case 35: //'End':
                    return true

                case 67:  //CTRL C 
                case 86:  //CTRL V
                case 65:  //CTRL A
                    if (e.ctrlKey) return true
            }

        if ((type !== "int") && (e.keyCode === 190)) return true 
        if ((minvalue < 0) && (e.key === '-'))   return true

        //Test Key First
        if (numberRegex.test(e.key) !== true) e.preventDefault()

        return false
    }

    function check_limits(v: any){
        if (typeof v !== 'number') v = Number(v)
        
        if (limits) { //Enforse Limits ?
            if (v < minvalue) v = minvalue
            if (v > maxvalue) v = maxvalue
        }
    
        if (type === 'float')
            v = parseFloat( v.toFixed(decimals) )

        return v
    }


</script>

<div style="width: {width}px;">
    <span class="input-container {readonly? 'input-container-readonly' : ''}"  >
        {#if readonly}
            <input inputmode="{type === "int" ? "numeric" : "decimal"}" id="input-text-{r_id}" required
                onkeydown="{(e: any) => { e.preventDefault() }}"
                bind:value={value} 
            >
        {:else}
            <input inputmode="{type === "int" ? "numeric" : "decimal"}" id="input-text-{r_id}" required
                min  = {minvalue}
                max  = {maxvalue}
                step = {step}
                                
                bind:value={value}
                
                onwheel   = {(e:any) => {
                    if (!focused) return
                    e.preventDefault()

                    let val: number = Number(e.target.value)

                    if (e.deltaY < 0)
                        val += step   // Increase
                    else if (e.deltaY > 0) 
                        val -= step   // Decrease

                    value = check_limits(val)
                    onchange(e)
                }}


                onkeydown = {(e:any) => { check_pattern(e) }}
                oninput   = {(e:any) => { onchange(e) }}

                onfocus = {() => { focused = true  }}
                onblur  = {(e: any) => { 
                    focused = false 
                    value = check_limits(value)
                    onchange(e)
                }}
            >
        {/if}

        <label for="input-text-{r_id}" class="input-label">{label}</label>
        <span  class="input-underline"></span>
    </span>
</div>

<style>

</style>