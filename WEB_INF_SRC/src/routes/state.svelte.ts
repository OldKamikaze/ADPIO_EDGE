import Cookies  from "js-cookie" //install js-cookie and --save-dev @types/js-cookie
import { goto, invalidate, refreshAll, invalidateAll  } from '$app/navigation'
import { page } from '$app/state'


export let browser_params = $state({
	outerWidth  : 0,
	innerWidth  : 0,
	outerHeight : 0,
	innerHeight : 0,

	client:        'unknown',     //Broser
})

export function get_cookie_value(name: string) {     //Just A cookie filter 
  return Cookies.get(name)
}

export function set_cookie(param:string, value: any){
  Cookies.set(param, value, {SameSite: 'Strict', secure: false,  path: '/'}); 
}


//*********** API ************//
let headers_jsn:any = {                                                   //Header For POST Requests
  'Accept': 'application/json',
  'Content-Type': 'application/json; charset=UTF-8',
  //'X-CSRFToken': csrf_token,
  //'Authorization': 'Basic s'
}


export async function async_post(uri: string, cmd: string, jsn_content?: any){  //Async POST Request CMD
  if ((jsn_content === null) ||  (jsn_content === undefined)) jsn_content = {empty: ''}
  
  let jsn: any = { cmd: cmd, content: JSON.stringify(jsn_content) }

  const pst = await fetch(`/api/${uri}`, {
    method: 'POST',
    headers: headers_jsn,
    credentials: 'include',

    body: JSON.stringify(jsn)
  });

  jsn = await pst.json()

  if ( ('result' in jsn) && (jsn.result === 'error') ) popup_add('Error', jsn.error_text)

  return jsn
}

export async function async_get(uri: string){                                          //Async Get Request CMD
  const pst = await fetch(uri)
  return pst
}


/********* Popup Engine *************/
export let popup_list:any = $state([])

export function popup_delete(index: number){
  popup_list.splice(index, 1)
}

export function popup_add(header_msg: string, description_msg: string){
  if (popup_list.length < 32)
    popup_list.push({ header: header_msg, description: description_msg })
}


/********* User MNGment *************/
export let user = $state({     //user params
  user_name:      'Guest',
  user_auth:      false,
  user_profile:  'view',        //Will it even be 

  gui_edit_mode:    false,      //False - View, True - Edit Mode
  gui_edit_btn_ena: false,      //Enables switch over button on top
  tree_visible:     true,       //Expanded or collapsed tree
  filter:           '',         //filter

  view_content:   '/',
  view_tree:      [],
  
  edit_content:   '/',
  edit_tree:      [],

  active_header:  'ADPIO EDGE',
  active_tree:    [],
})


export async function initialize_user(user_check:any){
  set_cookie("sessionkey", user_check.sessionkey )
  headers_jsn["Authorization"]  = user_check.sessionkey

  user.user_name = user_check.user
  user.user_auth = true
  user.user_profile = user_check.profile

  const trees = await async_post("user", "get_tree", { profile: user.user_profile })

  user.view_tree = trees.view_tree
  user.edit_tree = trees.edit_tree  

  if (user.edit_tree.length === 0){
    user.gui_edit_mode    = false
    user.gui_edit_btn_ena = false
    user.active_tree      = user.view_tree 
  } else {
    user.gui_edit_mode    = true
    user.gui_edit_btn_ena = true
    user.active_tree      = user.edit_tree 
  }

  if ((page.url.pathname === '/login') && (user.active_tree.length > 0)) set_navigation(user.active_tree[0].submenu[0].id) 
}

export function switch_gui_mode(editmode: boolean){
  if (editmode){
    user.gui_edit_mode = true
    user.active_tree = user.edit_tree
    if ((user.edit_content === '/') || (user.edit_content === '/login'))
      set_navigation(user.active_tree[0].submenu[0].id) 
    else
      set_navigation(user.edit_content)
  } else {
    user.gui_edit_mode = false
    user.active_tree = user.view_tree
    if ((user.view_content === '/') || (user.view_content === '/login'))
      set_navigation(user.active_tree[0].submenu[0].id) 
    else
      set_navigation(user.view_content)
  }
}

export function logout_user(){ 
  user.user_name        = 'Guest'
  user.user_auth        = false
  user.gui_edit_btn_ena = false

  //set_edit_mode  (false)
  headers_jsn["Authorization"] = "undefined"
  set_cookie("sessionkey", '')

  user.view_tree    =  []
  user.edit_tree    =  []
  user.active_tree  =  []

  set_navigation('/login')
}


export function set_navigation(location: string){
  if (user.gui_edit_mode) {
    user.edit_content = location
  } else {
    user.view_content = location
  }

  goto(location, { replaceState: true, }) // { keepFocus: true, noScroll: true, replaceState: true, invalidateAll: true}
}

/** std functions ***/
export function sleep(ms: number) {  return new Promise(resolve => setTimeout(resolve, ms)) }

/** APPS functions **/
export function datapoints_to_tree(data_db: any){
  let new_active_tree: any = []
    
  let groups: any = []
  data_db.forEach((el:any) => { 
    if (!groups.includes(el.group)) {
      groups.push( el.group ) 
      new_active_tree.push({id: `gr_${el.group}`, name: el.group, visible: true, submenu: []})
    }
  })

  new_active_tree.forEach((el_gr:any) => {
    const fltred = data_db.filter((e: any) => e.group === el_gr.name)

    let submenu = []
    fltred.forEach((el_sub:any) => { submenu.push({
      id: `datapoint_${el_sub.id}`, name: el_sub.name,
      visible: true, draggable: true, 
      type    : 'datapoint', 
      el_name : el_sub.name,   //Datapoint Specific 
      el_group: el_sub.group,  //Datapoint Specific 
      el_id   : el_sub.id      //Datapoint Specific 
    }) })

    el_gr.submenu = submenu
  })

  return new_active_tree
}

export function blocks_to_tree(blks_db: any){
  let new_active_tree: any = []

  blks_db.forEach((blk_grp:any) => {
    let new_grp: any = {id: blk_grp.name, name: blk_grp.name, visible: true, submenu: []}
//Group
    blk_grp.list.forEach((el_d:any) => { 
        new_grp.submenu.push( {
            id: `blocks_${el_d.id}`, name: el_d.name,
            visible: true, draggable: true,                 
            type    : el_d.type, el_name : el_d.name, el_group: el_d.group, el_id   : el_d.id       //Datapoint Specific
        } )
    })

    new_active_tree.push(new_grp)
  })

  return new_active_tree
}
