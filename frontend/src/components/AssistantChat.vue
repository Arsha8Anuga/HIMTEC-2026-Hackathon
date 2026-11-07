<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { api, ApiError } from "../lib/api";

// Kontrak v0.8: semua kalimat jawaban datang dari backend; komponen ini hanya menampilkan.
type Turn = { role: "user" | "assistant"; content: string; grounded?: boolean };
const props = defineProps<{ childId: string; childName?: string }>();
const enabled = ref(false),
  turns = ref<Turn[]>([]),
  draft = ref(""),
  waiting = ref(false),
  note = ref(""),
  list = ref<HTMLElement>();
const suggestions = [
  "Jelaskan status anak saya",
  "Apa yang perlu saya lakukan sekarang?",
  "Apa saran makan dari panduan untuk anak saya?",
];

async function check() {
  try {
    enabled.value = !!(await api<{ enabled: boolean }>("/assistant"))?.enabled;
  } catch {
    enabled.value = false; // F-14: bila asisten tidak ada, bagian ini tidak muncul
  }
}
watch(
  () => props.childId,
  () => {
    turns.value = [];
    note.value = "";
    check();
  },
  { immediate: true },
);

async function send(text = draft.value) {
  const message = text.trim();
  if (!message || waiting.value) return;
  const history = turns.value
    .slice(-10)
    .map(({ role, content }) => ({ role, content }));
  turns.value.push({ role: "user", content: message });
  draft.value = "";
  note.value = "";
  waiting.value = true;
  await scroll();
  try {
    const data = await api<{ reply: string; grounded: boolean }>(
      `/children/${props.childId}/assistant`,
      "POST",
      { message, history },
      120000,
    );
    turns.value.push({ role: "assistant", content: data.reply, grounded: data.grounded });
  } catch (error) {
    turns.value.pop();
    draft.value = message;
    note.value =
      error instanceof ApiError && error.status === 503
        ? "Asisten sementara tidak tersedia. Coba lagi nanti."
        : error instanceof Error
          ? error.message
          : "Pertanyaan belum terkirim.";
  } finally {
    waiting.value = false;
    await scroll();
  }
}
async function scroll() {
  await nextTick();
  list.value?.scrollTo({ top: list.value.scrollHeight });
}
function onKey(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}
</script>

<template>
  <section v-if="enabled" class="card assistant" aria-labelledby="assistant-title">
    <h2 id="assistant-title">Tanya asisten</h2>
    <p class="muted assistant-note">
      Jawaban disusun otomatis oleh model bahasa dari data
      {{ childName || "anak" }} di aplikasi ini. Bukan nasihat medis;
      konfirmasikan ke petugas Posyandu atau Puskesmas.
    </p>
    <div ref="list" class="assistant-log" aria-live="polite">
      <p
        v-for="(t, i) in turns"
        :key="i"
        :class="['bubble', t.role, { unverified: t.grounded === false }]"
      >
        <span class="sr-only">{{ t.role === "user" ? "Anda: " : "Asisten: " }}</span
        >{{ t.content }}</p
      >
      <p v-if="waiting" class="bubble assistant muted" role="status">Asisten sedang menyusun jawaban…</p>
    </div>
    <div v-if="!turns.length" class="assistant-suggestions">
      <button
        v-for="s in suggestions"
        :key="s"
        type="button"
        class="secondary"
        :disabled="waiting"
        @click="send(s)"
      >
        {{ s }}
      </button>
    </div>
    <form class="assistant-form" @submit.prevent="send()">
      <label for="assistant-input" class="sr-only">Pertanyaan untuk asisten</label>
      <textarea
        id="assistant-input"
        v-model="draft"
        rows="2"
        maxlength="500"
        placeholder="Tulis pertanyaan tentang data anak ini…"
        :disabled="waiting"
        @keydown="onKey"
      />
      <button type="submit" :disabled="waiting || !draft.trim()">Kirim</button>
    </form>
    <p v-if="note" class="muted" role="status">{{ note }}</p>
  </section>
</template>

<style scoped>
.assistant-note {
  font-size: 0.9rem;
}
.assistant-log {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
  margin: 12px 0;
}
.bubble {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  max-width: 88%;
  white-space: pre-wrap;
  line-height: 1.5;
}
.bubble.user {
  align-self: flex-end;
  background: var(--brand);
  color: #fff;
}
.bubble.assistant {
  align-self: flex-start;
  background: #f1f4f1;
  border: 1px solid var(--border);
}
.bubble.unverified {
  border-style: dashed;
}
.assistant-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.assistant-form {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.assistant-form textarea {
  flex: 1;
  font-size: 16px;
  min-height: 44px;
  resize: vertical;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
</style>
