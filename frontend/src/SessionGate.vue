<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import App from "./App.vue";
import AuthForm from "./components/AuthForm.vue";
import { api, ApiError, sessionExpired, setToken, type AuthUser, type VerifiedSession } from "./lib/api";

const router = useRouter();
const mode = ref<"loading" | "demo" | "login" | "signed" | "error">("loading");
const user = ref<AuthUser>();
const message = ref("");
const loggingOut = ref(false);

function showLogin(reason = "") {
  setToken("");
  user.value = undefined;
  message.value = reason;
  mode.value = "login";
  void router.replace("/masuk");
}
function expired() {
  if (loggingOut.value) return;
  showLogin("Sesi telah berakhir. Silakan masuk kembali.");
}
async function detect() {
  mode.value = "loading";
  await router.isReady();
  try {
    user.value = await api<AuthUser>("/auth/me");
    if (router.currentRoute.value.path === "/masuk") await router.replace("/");
    mode.value = "signed";
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) {
      setToken("");
      if (router.currentRoute.value.path === "/masuk") await router.replace("/");
      mode.value = "demo";
    } else if (e instanceof ApiError && e.status === 401) showLogin();
    else mode.value = "error";
  }
}
async function enter(session: VerifiedSession) {
  setToken(session.access_token);
  user.value = session.user;
  await router.replace("/");
  mode.value = "signed";
}
async function logout() {
  if (loggingOut.value) return;
  loggingOut.value = true;
  try {
    await api("/auth/logout", "POST");
  } catch {
    // Always end the local session, including when the service is offline.
  } finally {
    showLogin();
    loggingOut.value = false;
  }
}
onMounted(() => {
  sessionExpired.addEventListener("expired", expired);
  void detect();
});
onUnmounted(() => sessionExpired.removeEventListener("expired", expired));
</script>

<template>
  <App v-if="mode === 'signed' || mode === 'demo'" :user-name="user?.name" :logging-out="loggingOut" @logout="logout" />
  <main v-else class="auth-page">
    <section class="card auth-card">
      <div class="header-brand">Pantau</div>
      <AuthForm v-if="mode === 'login'" :notice="message" @verified="enter" />
      <template v-else-if="mode === 'error'">
        <h1>Belum dapat memeriksa sesi</h1>
        <p role="alert">Periksa koneksi ke layanan lalu coba lagi.</p>
        <button @click="detect">Coba lagi</button>
      </template>
      <p v-else role="status">Memeriksa sesi…</p>
    </section>
  </main>
</template>
