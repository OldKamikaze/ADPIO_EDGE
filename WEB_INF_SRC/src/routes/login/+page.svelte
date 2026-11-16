
<script lang="ts">
    

    import { onMount } from "svelte"

    import { browser_params, initialize_user, async_post, set_navigation, user } from '../state.svelte.ts'


    import {
        Login
    } from "carbon-icons-svelte"

    import ButtonR          from "../adp_kit/components/ButtonR.svelte"
    import InputLabel       from "../adp_kit/components/InputLabel.svelte"
    import InputPassword    from "../adp_kit/components/InputPassword.svelte"
    

    let fields = $state({ login: "", password: "" })
    let login_field    = $state()
    let password_field = $state()

    async function login(){
        const usr_chck:any = await async_post( 'login', 'login', { key : btoa(fields.login + ':' + fields.password) } )
        if (usr_chck.auth === true){
            await initialize_user(usr_chck)
        }
    }

    onMount(async () => { 
        setTimeout(() => {
            login_field.set_focus()
            //clearInterval(interval)
		}, 50)
    })
</script>


<div class="content-panel">
    <div class="flex " >
        <div class="flex-col ">
            <div class="flex-item">
                <InputLabel bind:this={login_field} label="USER NAME"  bind:value={fields.login}    maxlength={12}
                    onkeydown={(e:any) => { 
                        if ((e.keyCode === 13) && fields.login !== '') 
                            if (fields.password !== '')  login() //Autocomplete, probably, login right away
                            else                         password_field.set_focus() //or jump to pass field
                    }}
                />
            </div>
            
            <div class="flex-item">
                <InputPassword bind:this={password_field} label="PASSWORD" bind:value={fields.password} maxlength={16} 
                    onkeydown={(e:any) => { 
                        if ((e.keyCode === 13) && fields.login !== '') login()
                    }}
                />
            </div>
            
            <div class="flex-item">
                <ButtonR 
                    text="Login" color="green" 
                    disabled={ fields.login === '' } onclick={() => { login() }} 
                ><Login class="round-btn-svg"/></ButtonR>
            </div>
        </div>
    </div>
</div>
