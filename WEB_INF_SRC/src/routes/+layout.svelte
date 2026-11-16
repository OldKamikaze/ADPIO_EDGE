<script lang="ts">
    import { onMount }      from 'svelte';

    import { browser_params, user, async_get, async_post, get_cookie_value, initialize_user, set_navigation } from './state.svelte.ts';

    import Navigation from './adp_kit/layout/Navigation.svelte';
    import Header     from './adp_kit/layout/Header.svelte';
    import Popups     from './adp_kit/layout/Popups.svelte';

    let { children }      = $props();
    let main_layout_ready = $state(false); //Fix for on mount child->parent exec order

    onMount(async () => { 
    //Load auth cookie
        let ssk = get_cookie_value('sessionkey') 
        let usr_chck: any = undefined

        if (ssk !== undefined && ssk !== "undefined"){
          usr_chck = await async_post("login", "sessionkey", {'key': ssk})
          user.user_auth = usr_chck.auth
        }

        if (user.user_auth === false)
          set_navigation("/login")
        else{
          await initialize_user(usr_chck)
        }    

    //Set Browser
        if     ( navigator.userAgent.indexOf("Chrome")  != -1 )  browser_params.client = "chrome";
        else if( navigator.userAgent.indexOf("Opera")   != -1 )  browser_params.client = "opera";
        else if( navigator.userAgent.indexOf("MSIE")    != -1 )  browser_params.client = "ie";
        else if( navigator.userAgent.indexOf("Firefox") != -1 )  browser_params.client = "firefox";
        else browser_params.client = "unknown";

        main_layout_ready = true
    })

</script>

<svelte:head>
	<title>{user.active_header}</title>
</svelte:head>


<svelte:window 
  bind:innerWidth= {browser_params.outerWidth } bind:outerWidth= {browser_params.innerWidth } 
	bind:innerHeight={browser_params.outerHeight} bind:outerHeight={browser_params.innerHeight}
/>


<div class="app-left {user.tree_visible? "app-left-visible":"" }" >
	<Navigation />
</div>
	
<div class="app-right {user.tree_visible? "app-right-visible":"" }">
    <Header  />
    
    <main>
      {#if main_layout_ready}
        {@render children()}
      {:else}
        <span>LOADING...</span>
      {/if}
		  
    </main>
</div>

<Popups />