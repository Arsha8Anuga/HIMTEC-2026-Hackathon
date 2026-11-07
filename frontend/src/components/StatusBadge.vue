<script setup lang="ts">
import { AlertCircle, CheckCircle2, CircleHelp, Info } from "lucide-vue-next";
defineProps<{ level?: string; label?: string }>();
const icons = {
  green: CheckCircle2,
  yellow: AlertCircle,
  red: AlertCircle,
  info: Info,
};
</script>

<template>
  <span class="badge" :class="level">
    <component
      :is="icons[level as keyof typeof icons] || CircleHelp"
      :size="16"
      aria-hidden="true"
    />
    {{ label || "Status belum tersedia" }}
  </span>
</template>
