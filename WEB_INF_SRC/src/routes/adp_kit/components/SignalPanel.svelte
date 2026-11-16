<script  lang="ts">
    import { ArrowDown, ArrowUp } from 'carbon-icons-svelte'

    import Tooltip from './Tooltip.svelte'

    let { 
        dash = [
            { icon: ArrowDown, color: "normal", text: 'text1'}, //normal green red blue off
            { icon: ArrowUp,   color: "red"   , text: 'text2'}
        ]
    } = $props();

    let hover_index = $state(-1)
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<span> 
    {#each dash as d, indx }
        <span  class="panel-icon signals-{d.color}"  onmouseenter="{() => { hover_index = indx }}" onmouseleave="{() => { hover_index = -1 }}"    >
            {#if d.text !== "" }<Tooltip text={d.text} show={hover_index === indx} x="-16px" y="-42px" />{/if}
            <d.icon class="panel-icon-svg" />
        </span>
    {/each} 
</span>

<style>
    .panel-icon { 
        display: inline-block;
        height: 24px;
        width:  24px;
        text-align: center;
        text-decoration: none;       
    }

    .panel-icon-svg {
        scale: 1.2; 
        vertical-align: top; 
        padding-top: 3px;
    }
</style>