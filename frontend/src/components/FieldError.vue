<script setup lang="ts">
defineProps<{ field: string; fields: Record<string, string> }>();
</script>
<template>
  <small v-if="fields[field]" :id="field + '-error'" class="field-error">{{
    fields[field]
  }}</small>
</template>
