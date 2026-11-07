<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import FieldError from "./FieldError.vue";
import { api, ApiError, type VerifiedSession } from "../lib/api";

const props = defineProps<{ notice: string }>();
const emit = defineEmits<{ verified: [session: VerifiedSession] }>();
const register = ref(false);
const email = ref("");
const name = ref("");
const challenge = ref("");
const heading = ref<HTMLHeadingElement>();
const codeInput = ref<HTMLInputElement>();
const busy = ref(false);
const message = ref(props.notice);
const fields = ref<Record<string, string>>({});
const deadlines = ref(new Map<string, number>());
const now = ref(Date.now());
const address = computed(() => email.value.trim().toLowerCase());
const remaining = computed(() => Math.max(0, Math.ceil(((deadlines.value.get(address.value) || 0) - now.value) / 1000)));
let timer: number;
onMounted(() => {
  heading.value?.focus();
  timer = window.setInterval(() => { now.value = Date.now(); }, 500);
});
onUnmounted(() => clearInterval(timer));

function resetErrors() {
  message.value = "";
  fields.value = {};
}
function cooldown() {
  now.value = Date.now();
  deadlines.value.set(address.value, now.value + 60000);
}
async function changeStep() {
  resetErrors();
  if (challenge.value) challenge.value = "";
  else register.value = !register.value;
  await nextTick();
  heading.value?.focus();
}
function handleError(error: unknown, verifying: boolean) {
  if (error instanceof ApiError) {
    if (error.status === 429) {
      if (!verifying) cooldown();
      message.value = "Terlalu banyak permintaan. Tunggu sebentar sebelum mencoba lagi. Jika sudah meminta lima kode, coba lagi dalam satu jam.";
      return;
    }
    if (error.status === 401) {
      if (verifying) fields.value.code = "Kode salah atau sudah kedaluwarsa. Periksa kode atau minta kode baru.";
      else fields.value.email = "Belum bisa masuk dengan email ini. Periksa alamatnya atau pilih Daftar.";
      return;
    }
    if (error.status === 422) {
      if (verifying) fields.value.code = "Kode belum diterima. Periksa enam angka yang diisikan atau minta kode baru.";
      else {
        for (const key of ["email", "name"]) {
          if (error.fields?.[key]) fields.value[key] = error.fields[key];
        }
        if (!Object.keys(fields.value).length) message.value = "Periksa kembali isian formulir.";
      }
      return;
    }
  }
  message.value = "Permintaan belum berhasil. Periksa koneksi lalu coba lagi.";
}
async function sendCode() {
  if (busy.value || remaining.value) return;
  busy.value = true;
  resetErrors();
  try {
    const payload = register.value ? { email: address.value, name: name.value.trim() } : { email: address.value };
    const response = await api<{ challenge_id: string }>(register.value ? "/auth/register" : "/auth/login", "POST", payload);
    challenge.value = response.challenge_id;
    if (codeInput.value) codeInput.value.value = "";
    cooldown();
    await nextTick();
    heading.value?.focus();
  } catch (e) {
    handleError(e, false);
  } finally {
    busy.value = false;
  }
}
async function verify() {
  if (busy.value || !codeInput.value) return;
  busy.value = true;
  resetErrors();
  try {
    const pending = api<VerifiedSession>("/auth/verify", "POST", {
      challenge_id: challenge.value, code: codeInput.value.value,
    });
    codeInput.value.value = "";
    emit("verified", await pending);
  } catch (e) {
    handleError(e, true);
  } finally {
    busy.value = false;
    if (fields.value.code || message.value) {
      await nextTick();
      codeInput.value?.focus();
    }
  }
}
</script>

<template>
  <h1 ref="heading" tabindex="-1">{{ challenge ? "Masukkan kode" : register ? "Daftar" : "Masuk" }}</h1>
  <p class="muted">{{ challenge ? "Masukkan enam angka yang dikirim ke " + address + "." : "Gunakan alamat email untuk menerima kode masuk." }}</p>
  <p v-if="message" role="alert" class="message">{{ message }}</p>
  <form v-if="!challenge" class="auth-form" @submit.prevent="sendCode">
    <label v-if="register" for="auth-name">Nama
      <input id="auth-name" v-model.trim="name" autocomplete="name" required :disabled="busy"
        :aria-invalid="!!fields.name" :aria-describedby="fields.name ? 'name-error' : undefined" />
      <FieldError field="name" :fields="fields" />
    </label>
    <label for="auth-email">Email
      <input id="auth-email" v-model="email" type="email" autocomplete="email" required :disabled="busy"
        :aria-invalid="!!fields.email" :aria-describedby="fields.email ? 'email-error' : undefined" />
      <FieldError field="email" :fields="fields" />
    </label>
    <button :disabled="busy || remaining > 0">Kirim kode{{ remaining ? ' (' + remaining + ' detik)' : '' }}</button>
    <button type="button" class="secondary" :disabled="busy" @click="changeStep">{{ register ? "Kembali ke masuk" : "Daftar" }}</button>
  </form>
  <form v-else class="auth-form" @submit.prevent="verify">
    <label for="auth-code">Kode 6 angka
      <input ref="codeInput" id="auth-code" type="password" inputmode="numeric" autocomplete="one-time-code"
        pattern="[0-9]{6}" minlength="6" maxlength="6" required :disabled="busy"
        :aria-invalid="!!fields.code" :aria-describedby="fields.code ? 'code-error' : undefined" />
      <FieldError field="code" :fields="fields" />
    </label>
    <button :disabled="busy">Masuk</button>
    <button type="button" class="secondary" :disabled="busy || remaining > 0" @click="sendCode">
      Kirim ulang kode{{ remaining ? ' (' + remaining + ' detik)' : '' }}
    </button>
    <button type="button" class="secondary" :disabled="busy" @click="changeStep">Ubah email</button>
  </form>
</template>
