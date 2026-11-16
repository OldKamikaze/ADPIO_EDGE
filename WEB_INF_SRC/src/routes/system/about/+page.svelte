
<script lang="ts">
    import { browser_params } from '../../state.svelte.ts';
    import { version, dev } from '$app/env';
    import { onMount }      from 'svelte'
    import { user } from '../../state.svelte.ts';    

    onMount(async () => { 
        user.active_header = 'ABOUT'
    })    
</script>


<div class="content-panel">
    <div class="content-panel-header">ADPIO EDGE</div>

    {#if dev}
        <div style="color: red;">Debug Version: {version}</div>
    {:else}
        <div>Build Version: {version}</div>
    {/if}

    <div style="margin-top: 15px;">By Artem Pavlov</div> 
    <div>Vacnouver, BC</div>
    <div>Canada</div>

    <div style="margin-top: 15px;"><a class="email_to" href="mailto:apavlov.adpautomation@gmail.com">Contact Email</a></div>
    <div style="margin-top: 25px;">Client: {browser_params.client}</div>
</div>

<style>
    .email_to {
        color: cornflowerblue !important;
        text-decoration: underline !important;
    }
</style>