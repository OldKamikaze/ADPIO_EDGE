<script  lang="ts">
	let { 
        label       = "Select Date Range",
        start_date  = $bindable(new Date().toISOString().slice(0, 10)),
        end_date    = $bindable(new Date().toISOString().slice(0, 10)),
    } = $props();
</script>

<div>
<div>{label}</div>
    <input type="date" name="start_date" bind:value="{start_date}"  max="{end_date}"   />
    <input type="date" name="end_date"   bind:value="{end_date}"    min="{start_date}" />
</div>

<style></style>