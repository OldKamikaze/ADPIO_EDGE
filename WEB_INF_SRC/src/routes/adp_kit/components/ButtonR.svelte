<script  lang="ts">
  import Tooltip   from "./Tooltip.svelte"
  import ConfModal from "./ConfModal.svelte";
  
  let {

    color         = "normal", //red, blue, orange, green
    onclick       = function(e: any){},
    //icon,
    text          = "",
    with_confirmation = false,

  //For Confirmation Dialog
    conf_title       = "No Title",
    conf_description = "No Description",

    conf_btn_accept_txt  = "DELETE",
    conf_btn_decline_txt = "CANCEL",

    disabled = false,
    rendered = true,

    children
  } = $props()


  let modal_view: boolean = $state(false)
  let hover     : boolean = $state(false)
  
  export function open_conf(){ modal_view = true }
</script>

{#if rendered }
  <button class="round-btn round-btn-{disabled ? 'disabled': color}" 
    onclick={(e: any) => { 
      if (!disabled){
        if (with_confirmation) {
          modal_view = true
        } else {
          onclick(e)
        }
      }
    }} 

    onmouseenter="{() => {hover = true}}" onmouseleave="{() => {hover = false}}"   
  >
    {#if text !== ""}
      <Tooltip text={text} show={hover} x="-15px" y="-50px" />
    {/if}

      <!--svelte:component style="width: 22px; height:24px; vertical-align: top; " this={icon} /--> 
      {@render children()}
  </button>

  {#if with_confirmation}
    <ConfModal 
      title={conf_title} description={conf_description} 
      btn_accept_txt={conf_btn_accept_txt} btn_decline_txt={conf_btn_decline_txt}
      bind:visible={modal_view} on_accept={(e: any) => { onclick(e)} } 
    />  
  {/if}
{/if}  

<style>

</style>