
<script lang="ts">
    import { onMount }          from 'svelte'
    import { user, async_post } from '../../state.svelte.ts';
    import { USER_PROFILES, } from "../../../lib/app_engine.ts";

    import {
        Add,
        TrashCan,
        Edit,
    } from "carbon-icons-svelte"

    import DataTable        from "../../adp_kit/components/DataTable.svelte"
    import ControlPanel     from "../../adp_kit/components/ControlPanel.svelte"
    
    import ButtonR          from "../../adp_kit/components/ButtonR.svelte"    
    import Modal            from "../../adp_kit/components/Modal.svelte"
    import InputLabel       from "../../adp_kit/components/InputLabel.svelte"
    import InputPassword    from "../../adp_kit/components/InputPassword.svelte"    
    import InputSelector    from "../../adp_kit/components/InputSelector.svelte"    


    let data = $state({
        header: "",
        colums: [
            {name: "USER NAME",    key: "name"        , row_style: ""}, 
            {name: "PROFILE",      key: "profile"     , row_style: ""},
            {name: "DESCRIPTION",  key: "description" , row_style: ""},
        ],
        data: [],
    })

    let user_selected = $state(undefined)

    let buttons = $derived([
        {
            text                : 'Add New User',
            color               : 'normal',
            icon                : Add,
            disabled            : false,
            with_confirmation   : false,
            onclick             : async (e: any) => { 
                new_user_mode = true
                edit_user = JSON.parse( JSON.stringify( new_user_temp ) )
                user_edit_modal?.open(e.clientX, e.clientY) 
            }
        }, {
            text                : 'Edit User',
            color               : 'normal',
            icon                : Edit,
            disabled            : user_selected === undefined,
            with_confirmation   : false, 
            onclick             : async (e: any) => { 
                await on_user_edit(e) 
            }
        }, {
            text                : 'Delete User',
            color               : 'red',
            icon                : TrashCan,
            disabled            : user_selected === undefined,
            with_confirmation   : true,
            conf_title          : 'DELETE USER',
            conf_description    : `Are you sure you want to delete user: ${user_selected?.name}?`, 
            conf_btn_accept_txt : 'DELETE',
            onclick             : async (e: any) => { 
                if (user_selected === undefined) return
                await async_post( 'user', 'delete_user', { name: user_selected?.name } )   
                user_selected = undefined
                await update_data()
            }
        },
    ])


    let user_edit_modal = $state()
    const new_user_temp = {
        name: 'New User',
        description: '',
        profile:     'developer',
        password:    '',
        password2:   '',
        homepage:    '',
    }
    let new_user_mode = $state(false)
    let edit_user:any = $state(JSON.parse( JSON.stringify( new_user_temp ) ))
  
    async function on_user_edit(e: any){
        new_user_mode = false
        user_edit_modal?.open(e.clientX, e.clientY) 
        get_user()
    }
    
    async function get_user(){
        const rec = await async_post( 'user', 'get_user', {name: user_selected?.name} )  
        edit_user = JSON.parse( JSON.stringify( rec ) )
        edit_user.password2 = rec.password
    }


    async function update_data(){ data.data = await async_post( 'user', 'user_list' ) }

    onMount(async () => { 
        user.active_header = 'USER MANAGMENT'
        update_data() 
    })

</script>

<div class="content-panel">
    <ControlPanel bind:buttons={buttons} />
</div>

<div class="content-panel" >
   <DataTable bind:data={data} selectable_rows  context_btns={buttons}
        bind:selected_row={user_selected}
        ondblclick={ async (e: any) => { await on_user_edit(e) }}
   />
</div>


<Modal bind:this={user_edit_modal} title="{ new_user_mode ? 'Add New User' : 'Edit User'} " >
    <div class="flex " >
        <div class="flex-col ">
           <div class="flex-item"><InputLabel       label="NEW USER"        bind:value={edit_user.name}        maxlength={12} readonly={!new_user_mode}  /></div>
            <div class="flex-item"><InputLabel      label="DESCRIPTION"     bind:value={edit_user.description} maxlength={64}   /></div>

            <div class="flex-item"><InputPassword   label="PASSWORD"        bind:value={edit_user.password}    maxlength={16}   /></div>
            <div class="flex-item"><InputPassword   label="PASSWORD REPEAT" bind:value={edit_user.password2}   maxlength={16}   /></div>
            <div class="flex-item"><InputSelector   label="ACCESS PROFILE"  bind:value={edit_user.profile}     item_list={USER_PROFILES} /></div>

            <div class="flex-item">
                <ButtonR   text="Add" color="green"  
                    disabled={ !((edit_user.password === edit_user.password2) && (edit_user.name.length > 3)) }
                    onclick={async (e: any) => {  
                        if (new_user_mode) await async_post( 'user', 'add_user',  edit_user )
                        else               await async_post( 'user', 'save_user', edit_user )  

                        await update_data()
                        user_edit_modal?.close(e)
                    }}
                ><Add class="round-btn-svg" /></ButtonR>
            </div>
        </div>
    </div>
</Modal>


<style>

</style>