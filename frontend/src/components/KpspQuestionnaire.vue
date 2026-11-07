<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
type Answer = { item_no: number; answer: boolean };
type Item = { item_no: number; question: string; aspect: string };
const props = defineProps<{ questionnaire: any; saving: boolean }>();
const emit = defineEmits<{ submit: [answers: Answer[]] }>();
const step = ref(0),
  answers = ref<Record<number, boolean>>({}),
  heading = ref<HTMLElement>();
const items = computed<Item[]>(() =>
  Array.isArray(props.questionnaire?.items) ? props.questionnaire.items : [],
);
const valid = computed(
  () =>
    items.value.length === 10 &&
    items.value.every(
      (i) =>
        i !== null &&
        typeof i === "object" &&
        Number.isInteger(i.item_no) &&
        i.item_no >= 1 &&
        i.item_no <= 10 &&
        typeof i.question === "string" &&
        i.question.trim().length > 0,
    ) &&
    new Set(items.value.map((i) => i.item_no)).size === 10,
);
const current = computed(() => items.value[step.value]);
const complete = computed(
  () =>
    valid.value &&
    items.value.every((i) => typeof answers.value[i.item_no] === "boolean"),
);
async function move(by: number) {
  step.value += by;
  await nextTick();
  heading.value?.focus();
}
function send() {
  if (complete.value && !props.saving)
    emit(
      "submit",
      items.value.map((i) => ({
        item_no: i.item_no,
        answer: answers.value[i.item_no]!,
      })),
    );
}
watch(
  () => props.questionnaire,
  () => {
    step.value = 0;
    answers.value = {};
  },
);
</script>
<template>
  <section class="card form-card">
    <h2>Kuesioner {{ questionnaire.questionnaire_age_months }} bulan</h2>
    <p>{{ questionnaire.due ? "Jatuh tempo" : "Belum jatuh tempo" }}</p>
    <p>Pra-skrining yang perlu dikonfirmasi di Posyandu.</p>
    <template v-if="questionnaire.due && valid">
      <p aria-live="polite">Butir {{ step + 1 }} dari 10</p>
      <progress
        :value="Object.keys(answers).length"
        max="10"
        aria-label="Jumlah jawaban terisi"
      />
      <h3 ref="heading" tabindex="-1">{{ current.question }}</h3>
      <div class="actions" role="group" aria-label="Jawaban pertanyaan">
        <button
          v-for="answer in [true, false]"
          :key="String(answer)"
          :disabled="saving"
          :class="{ secondary: answers[current.item_no] !== answer }"
          :aria-pressed="answers[current.item_no] === answer"
          @click="answers[current.item_no] = answer"
        >
          {{ answer ? "Ya" : "Tidak" }}
        </button>
      </div>
      <div class="actions">
        <button
          class="secondary"
          :disabled="step === 0 || saving"
          @click="move(-1)"
        >
          Sebelumnya
        </button>
        <button
          v-if="step < 9"
          :disabled="answers[current.item_no] === undefined || saving"
          @click="move(1)"
        >
          Berikutnya
        </button>
        <button v-else :disabled="!complete || saving" @click="send">
          {{ saving ? "Menyimpan…" : "Simpan jawaban" }}
        </button>
      </div>
    </template>
    <p v-else-if="questionnaire.due" role="status">
      Butir kuesioner dari layanan belum lengkap. Jawaban belum dapat dikirim.
    </p>
  </section>
</template>
