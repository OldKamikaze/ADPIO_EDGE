<script  lang="ts">
	let { 
        content,
        block, 
        io,

        selected       = $bindable(), 
        selected_binds = $bindable(), 

        blk_width ,
        blk_height,
        is_live  = $bindable(),
    } = $props();
    
    let bind_render = $state({ x: 0, y: 0 })
    let path_d      = $state('')

    function path( block: any, io: any ){
        let pointer_blk = content[io.bind.pointer_blk_index]
        const  blk_height_offst = (block.type !== 'block'       ? -20 : 0)
        const  pnt_height_offst = (pointer_blk.type !== 'block' ? -20 : 0)        

        bind_render = { 
            x: (pointer_blk.x + blk_width + 6), 
            y: (pointer_blk.y + blk_height + io.bind.pointer_io_index * 20 - 6 + pnt_height_offst)
        }
        
        return `M ${(pointer_blk.x + blk_width + 3)}, ${(pointer_blk.y + blk_height + io.bind.pointer_io_index * 20 + 1 + pnt_height_offst)} C 
                ${((block.x - 3) - (pointer_blk.x + blk_width + 3))/2 + 15 + (pointer_blk.x + blk_width + 3)}, ${(pointer_blk.y + blk_height + io.bind.pointer_io_index * 20 + 1 + pnt_height_offst)}
                ${((block.x - 3) - (pointer_blk.x + blk_width + 3))/2 - 15 + (pointer_blk.x + blk_width + 3)}, ${(block.y       + blk_height + io.bind.this_io_index * 20    + 1 + blk_height_offst)}
                ${(block.x - 3)}, ${(block.y + blk_height + io.bind.this_io_index * 20 + 1 + blk_height_offst)}
            `  
    }    

    $effect(() => { path_d = path( block, io ) })
</script>

<path class="path-normal" d={path_d} />

<!-- svelte-ignore a11y_no_static_element_interactions -->
<path class="{ selected_binds.includes( io ) ? 'path-selected' : 'path-area' }" 
    onpointerdown="{(e:any) => { 
        if (!e.ctrlKey) { 
            selected        = []
            selected_binds  = []
        }
        selected_binds.push(io) 
        e.stopImmediatePropagation()
    }}"

    d="{ path_d }" 
/>

{#if is_live && ('debug_value' in io)} 
    <text text-anchor="start"   class="bind-value "  x="{bind_render.x}"  y="{bind_render.y}" >
        = {io.debug_value}
    </text>
{/if}


<style>
    /* Paths */
    .path-normal            { stroke-width: 3; stroke: rgb(60, 60, 60); stroke-opacity: 1; fill-opacity:   0; filter: drop-shadow(2px 2px 2px rgba(0, 0, 0, 0.4));}

    .path-area              { stroke-width: 8; fill: none; stroke: red;  stroke-opacity: 0.0; }
    .path-area:hover        { stroke-width: 8; fill: none; stroke: rgb(172, 172, 172);  stroke-opacity: 1; cursor: grab;  }
    
    .path-selected          { stroke-width: 6; fill: none; stroke: deepskyblue }    

    .bind-value             {  font: inherit; font-size: 0.92em; }
</style>