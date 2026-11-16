<script  lang="ts">
    //import { elasticInOut } from "svelte/easing";
    import ButtonR    from "./ButtonR.svelte"

    import {
    Branch,
        TildeLarge,
    } from "carbon-icons-svelte"

    //export let buttons:any
    //export let binds: any  = [undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,]

    let {
        buttons = $bindable([ 

            {
                text                : 'Refresh',
                color               : 'normal',
                icon                : TildeLarge,
                disabled            : false,


                with_confirmation   : true,
                conf_title          : 'Conf Event',
                conf_description    : 'Are you sure you want to do something?',
                conf_btn_accept_txt : 'DO',            
    
                onclick             : async (e: any) => { console.log('Button Click Event') }              
            }, 
    
        ]),    
    } = $props()    
    
    //icon, text, color
    //disabled, rendered
    //onclick
    //with_confirmation, conf_title, conf_description, conf_btn_accept_txt

    /*export let hotkeys: boolean = false //Feature For future implementation

    async function onkey_down_call(e: any){
        if (!hotkeys) return
        if ( e.keyCode >= 112 && e.keyCode <= 121 ){ //Navigation with F1-F10
            e.preventDefault()

            let index = e.keyCode - 112 
            if (binds[index] === undefined) return

            const btn = buttons[index]
            const bnd = binds  [index]
        
            const rendered = ('rendered' in btn)?  btn.rendered : true
            const disabled = ('disabled' in btn)?  btn.disabled : false

            if (!disabled && rendered === true){
                if (btn.with_confirmation) bnd.open_conf()
                else btn.onclick(e)                
            }
        }
    }*/

</script>

    <!--svelte:window on:keydown={async (e:any) => { await onkey_down_call(e) }} /--> 
  
    {#each buttons as btn, index }
        <ButtonR 
            //bind:this           = {binds[index]}
            //icon                = {btn.icon}   
            //text                = {hotkeys?  `${btn.text} [F${index + 1}]` : btn.text}  
            text                = {btn.text} 
            color               = {btn.color} 
            disabled            = {('disabled' in btn)?  btn.disabled : false}
            rendered            = {btn.rendered}
            onclick             = {(e: any) => { btn.onclick(e) }}      
            with_confirmation   = {btn.with_confirmation}
            conf_title          = {btn.conf_title}
            conf_description    = {btn.conf_description}
            conf_btn_accept_txt = {btn.conf_btn_accept_txt}                
        >            
            <btn.icon class="round-btn-svg"/>
        </ButtonR>
    {/each}

    <!--<TildeLarge class="round-btn-svg"/>
                    <ButtonR 
                    text="Login" color="green" 
                    disabled={ fields.login === '' } onclick={() => { login() }} 
                ><Login class="round-btn-svg"/></ButtonR>
    -->

<style>

</style>

