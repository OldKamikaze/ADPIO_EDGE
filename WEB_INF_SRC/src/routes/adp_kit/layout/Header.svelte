<script  lang="ts">
    import {
        Terminal,
		Code,
        View,
        Menu,
        Logout,
        Login
    } from "carbon-icons-svelte"

    import { logout_user, set_navigation, user, switch_gui_mode } from "../../state.svelte.ts"

    import ConfModal    from "../components/ConfModal.svelte"
    import SysTerminal  from "../components/Terminal.svelte"

    let terminal_modal = $state()
    let logout_conf    = $state(false)

    let { } = $props();
</script>


<SysTerminal bind:this={terminal_modal} />

<div id="toolbar">
    <div>
        <button class="toolbar-menu-btns" onclick={()=>{ 
            user.tree_visible = !user.tree_visible
        }}>
        <Menu /></button>
        <span class="toolbar-separator"></span>

        <div>{user.active_header}</div>
    </div>
       
    <div>      
        {#if user.gui_edit_btn_ena }  
            {#if user.gui_edit_mode}
                <button class="toolbar-menu-btns" onclick={()=>{ switch_gui_mode(false) }} >
                    <Code />
                    <span>Edit Mode</span>
                </button>
            {:else}
                <button  class="toolbar-menu-btns" onclick={()=>{ switch_gui_mode(true) }} >
                    <View />
                    <span>View Mode</span>
                </button>
            {/if}

            <button  class="toolbar-menu-btns" onclick={async (e: any)=>{ await terminal_modal.open(e) }} >
                <Terminal />
                <span>Terminal</span>
            </button>              
        {/if}

        {#if user.user_auth}
            <button  class="toolbar-menu-btns" onclick={()=>{ logout_conf = true }}  >
                <Logout />
                <span>Logout, {user.user_name}</span>
            </button>  
        {:else}   
            <button  class="toolbar-menu-btns" onclick={()=>{ set_navigation('/login') }} >
                <Login />
                <span>Login</span>
            </button>                    
        {/if}
       
    </div>
</div>


<ConfModal 
    title="LOGOUT CONFIRMATION" description="Are you sure?"
    btn_accept_txt="LOGOUT?" btn_decline_txt="CANCEL"
    bind:visible={logout_conf} on_accept={(e:any) => { logout_user() } } 
/>  


<style>

</style>