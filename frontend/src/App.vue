<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Activity,
  House,
  BookOpen,
  Plus,
  ArrowUpRight,
  ClipboardList,
  ChartNoAxesCombined,
  Heart,
  AlertCircle,
  Printer,
  Trash2,
} from "lucide-vue-next";
import { api, ApiError, today, dateLabel } from "./lib/api";
import { childBody, measurementBody, foodBody } from "./lib/forms";
const GrowthChart = defineAsyncComponent(
  () => import("./components/GrowthChart.vue"),
);
const route = useRoute(),
  router = useRouter();
const children = ref<any[]>([]),
  child = ref<any>(null),
  status = ref<any>(null),
  measurements = ref<any[]>([]),
  results = ref<any[]>([]),
  foods = ref<any[]>([]),
  guides = ref<any[]>([]),
  questionnaire = ref<any>(null),
  growth = ref<any>(null);
const busy = ref(false),
  saving = ref(false),
  error = ref(""),
  notice = ref(""),
  fields = ref<Record<string, string>>({}),
  indicator = ref("lhfa"),
  step = ref(0),
  answers = ref<Record<number, boolean>>({}),
  deleteId = ref(""),
  reportWarning = ref(""),
  relatedGuides = ref<any[]>([]),
  guideCategory = ref(""),
  guideAge = ref("");
const form = ref<Record<string, any>>({});
const parts = computed(() => route.path.split("/").filter(Boolean)),
  id = computed(() => (parts.value[0] === "children" ? parts.value[1] : "")),
  page = computed(() =>
    id.value ? parts.value[2] || "status" : parts.value[0] || "home",
  );
const links = [
  { path: "", label: "Ringkasan", icon: Activity },
  { path: "growth", label: "Kurva", icon: ChartNoAxesCombined },
  { path: "history", label: "Riwayat", icon: ClipboardList },
  { path: "kpsp", label: "Perkembangan", icon: Heart },
  { path: "food", label: "Catatan makan", icon: BookOpen },
];
function trapDialog(event: KeyboardEvent) {
  if (event.key !== "Tab") return;
  const nodes = document.querySelectorAll<HTMLButtonElement>(
    ".dialog button:not(:disabled)",
  );
  if (event.shiftKey && document.activeElement === nodes[0]) {
    event.preventDefault();
    nodes[nodes.length - 1]?.focus();
  } else if (
    !event.shiftKey &&
    document.activeElement === nodes[nodes.length - 1]
  ) {
    event.preventDefault();
    nodes[0]?.focus();
  }
}
let previousFocus: HTMLElement | null = null;
watch(deleteId, async (value) => {
  if (value) {
    previousFocus = document.activeElement as HTMLElement;
    await nextTick();
    document.querySelector<HTMLButtonElement>(".dialog button")?.focus();
  } else {
    await nextTick();
    previousFocus?.focus();
  }
});
const reportReady = ref(false);
const focusMain = () => document.getElementById("main")?.focus();
const printReport = () => window.print();
const validPage = computed(() =>
  [
    "home",
    "new",
    "guides",
    "status",
    "measurement",
    "growth",
    "history",
    "kpsp",
    "food",
    "report",
  ].includes(page.value),
);
let loadVersion = 0,
  growthVersion = 0;
class StaleLoad extends Error {}
const heading = computed(
  () =>
    ({
      home: "Langkah kecil, tumbuh bersama.",
      new: "Tambahkan profil anak",
      guides: "Panduan untuk keseharian",
      status: "Ringkasan anak",
      measurement: "Catat pengukuran",
      growth: "Kurva pertumbuhan",
      history: "Riwayat pengukuran",
      kpsp: "Skrining perkembangan",
      food: "Catatan makan kemarin",
      report: "Laporan untuk Posyandu",
    })[page.value] || "Pantau",
);
const age = (c: any) =>
  Math.max(
    0,
    (Date.now() - new Date(c.birth_date).getTime()) / 86400000 / 30.4375,
  ).toFixed(1);
const go = (p = "") =>
  router.push(id.value ? `/children/${id.value}/${p}` : "/");
const childFields = [
  { key: "name", label: "Nama anak", type: "text", required: true },
  { key: "birth_date", label: "Tanggal lahir", type: "date", required: true },
  {
    key: "birth_weight_kg",
    label: "Berat lahir (kg)",
    type: "number",
    min: 0.5,
    max: 6,
    step: 0.01,
  },
  {
    key: "birth_length_cm",
    label: "Panjang lahir (cm)",
    type: "number",
    min: 30,
    max: 60,
    step: 0.1,
  },
];
const measureFields = [
  {
    key: "measured_at",
    label: "Tanggal pengukuran",
    type: "date",
    required: true,
  },
  {
    key: "weight_kg",
    label: "Berat badan (kg)",
    type: "number",
    required: true,
    min: 0.5,
    max: 40,
    step: 0.01,
  },
  {
    key: "length_height_cm",
    label: "Panjang / tinggi badan (cm)",
    type: "number",
    min: 40,
    max: 130,
    step: 0.1,
  },
  {
    key: "head_circumference_cm",
    label: "Lingkar kepala (cm)",
    type: "number",
    min: 30,
    max: 60,
    step: 0.1,
  },
];
const groups = [
  { key: "grains_roots_tubers", label: "Serealia & umbi" },
  { key: "pulses_nuts_seeds", label: "Kacang & biji" },
  { key: "dairy", label: "Susu & olahannya" },
  { key: "flesh_foods", label: "Daging, ikan & unggas" },
  { key: "eggs", label: "Telur" },
  { key: "vita_fruits_veg", label: "Buah & sayur kaya vitamin A" },
  { key: "other_fruits_veg", label: "Buah & sayur lainnya" },
];
async function load() {
  const version = ++loadVersion;
  const request = async (path: string) => {
    const result = await api(path);
    if (version !== loadVersion) throw new StaleLoad();
    return result;
  };
  reportWarning.value = "";
  relatedGuides.value = [];
  reportReady.value = false;
  growthVersion++;
  busy.value = true;
  error.value = "";
  notice.value = "";
  fields.value = {};
  child.value = null;
  status.value = null;
  growth.value = null;
  questionnaire.value = null;
  measurements.value = [];
  results.value = [];
  foods.value = [];
  step.value = 0;
  answers.value = {};
  form.value = {
    measured_at: today(),
    source: "posyandu",
    position: "recumbent",
    sex: "female",
    is_preterm: false,
    recall_date: today(),
    breastfed: true,
    food_groups: [],
    meal_count: 0,
    milk_feed_count: null,
  };
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  form.value.recall_date = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, "0")}-${String(yesterday.getDate()).padStart(2, "0")}`;
  try {
    if (id.value) {
      child.value = await request(`/children/${id.value}`);
      form.value.position =
        Number(age(child.value)) < 24 ? "recumbent" : "standing";
      if (["status", "report"].includes(page.value)) {
        const r = await Promise.allSettled([
          request(`/children/${id.value}/status`),
          request(`/children/${id.value}/measurements`),
          request(`/children/${id.value}/kpsp`),
        ]);
        if (version !== loadVersion) throw new StaleLoad();
        status.value = r[0].status === "fulfilled" ? r[0].value : null;
        measurements.value = r[1].status === "fulfilled" ? r[1].value : [];
        results.value = r[2].status === "fulfilled" ? r[2].value : [];
        const failed = r.find((x) => x.status === "rejected");
        if (version !== loadVersion) throw new StaleLoad();
        if (failed?.status === "rejected") error.value = failed.reason.message;
      }
      if (page.value === "growth" || page.value === "report")
        await loadGrowth();
      if (version !== loadVersion) throw new StaleLoad();
      if (page.value === "status" && status.value?.reasons?.length) {
        const cards = await request(
          `/guides?age_months=${Math.floor(Number(age(child.value)))}`,
        );
        relatedGuides.value = cards.filter((g: any) =>
          g.related_codes?.some((code: string) =>
            status.value.reasons.some((r: any) => r.code === code),
          ),
        );
      }
      if (page.value === "history")
        measurements.value = await request(
          `/children/${id.value}/measurements`,
        );
      if (page.value === "kpsp") {
        results.value = await request(`/children/${id.value}/kpsp`);
        questionnaire.value = await request(`/children/${id.value}/kpsp/next`);
      }
      if (page.value === "food")
        foods.value = await request(`/children/${id.value}/food-recalls`);
    } else if (page.value === "home") {
      children.value = await request("/children");
      await Promise.all(
        children.value.map(async (c) => {
          try {
            c.status = await request(`/children/${c.id}/status`);
          } catch {
            c.unavailable = true;
          }
        }),
      );
    } else if (page.value === "guides")
      guides.value = await request("/guides" + guideQuery.value);
  } catch (e) {
    if (version === loadVersion && !(e instanceof StaleLoad))
      error.value = (e as Error).message;
  } finally {
    if (version === loadVersion) {
      busy.value = false;
      await nextTick();
      document.querySelector<HTMLElement>("h1")?.focus();
    }
  }
}
async function loadGrowth() {
  const version = ++growthVersion,
    owner = route.path;
  growth.value = null;
  reportReady.value = false;
  const selected = page.value === "report" ? "lhfa" : indicator.value;
  try {
    const data = await api(
      `/children/${id.value}/growth?indicator=${selected}`,
    );
    if (version === growthVersion && owner === route.path) growth.value = data;
  } catch (e) {
    if (version === growthVersion && owner === route.path) {
      if (page.value === "report") reportWarning.value = (e as Error).message;
      else error.value = (e as Error).message;
    }
  }
}
const guideQuery = computed(() => {
  const params = new URLSearchParams();
  if (guideCategory.value) params.set("category", guideCategory.value);
  if (guideAge.value !== "") params.set("age_months", guideAge.value);
  return params.size ? "?" + params : "";
});
watch(() => route.path, load, { immediate: true });
watch(indicator, () => {
  if (page.value === "growth") {
    error.value = "";
    loadGrowth();
  }
});
async function submit(kind: string) {
  saving.value = true;
  error.value = "";
  fields.value = {};
  try {
    let body: any,
      path = "";
    if (kind === "new") {
      body = childBody(form.value);
      path = "/children";
    } else if (kind === "measurement") {
      body = measurementBody(form.value);
      path = `/children/${id.value}/measurements`;
    } else if (kind === "food") {
      body = foodBody(form.value);
      path = `/children/${id.value}/food-recalls`;
    } else {
      body = {
        questionnaire_age_months: questionnaire.value.questionnaire_age_months,
        answered_at: today(),
        answers: Object.entries(answers.value).map(([item_no, answer]) => ({
          item_no: Number(item_no),
          answer,
        })),
      };
      path = `/children/${id.value}/kpsp`;
    }
    const r = await api(path, "POST", body);
    if (kind === "new") await router.push(`/children/${r.id}`);
    else await go("");
    notice.value = "Data berhasil disimpan.";
  } catch (e) {
    const x = e as ApiError;
    error.value = x.message;
    fields.value = x.fields || {};
    if (kind === "food") {
      try {
        foods.value = await api(`/children/${id.value}/food-recalls`);
      } catch {
        /* Keep the original save error visible. */
      }
    }
    await nextTick();
    document.querySelector<HTMLElement>('[role="alert"]')?.focus();
  } finally {
    saving.value = false;
  }
}
async function remove() {
  saving.value = true;
  try {
    await api(`/children/${id.value}/measurements/${deleteId.value}`, "DELETE");
    deleteId.value = "";
    await load();
    notice.value = "Pengukuran dihapus.";
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <a href="#main" @click.prevent="focusMain()" class="skip">Lewati ke isi</a>
  <aside class="sidebar">
    <RouterLink to="/" class="brand"
      ><Activity />
      <span>Pantau<small>Tumbuh kembang anak</small></span></RouterLink
    >
    <div class="nav-caption">RUANG KELUARGA</div>
    <nav>
      <RouterLink to="/" :class="{ active: page !== 'guides' }"
        ><House /> Beranda</RouterLink
      ><RouterLink to="/guides"><BookOpen /> Panduan</RouterLink>
    </nav>
    <div class="sidebar-foot">
      <Heart />
      <p>Setiap langkah<br />punya cerita.</p>
      <small>HIMTEC 2026</small>
    </div>
  </aside>
  <div class="workspace">
    <header>
      <span>Pantau tumbuh kembang</span
      ><span class="header-label">Ruang orang tua</span>
    </header>
    <main id="main" tabindex="-1">
      <div class="eyebrow">
        {{
          child
            ? child.name + " · " + age(child) + " bulan"
            : "BERSAMA DI SETIAP TAHAP"
        }}
      </div>
      <div class="title-row">
        <div>
          <h1 tabindex="-1">{{ heading }}</h1>
          <p class="muted">
            {{
              page === "home"
                ? "Catatan tumbuh kembang si kecil, dalam satu tempat."
                : child
                  ? "Lahir " + dateLabel(child.birth_date)
                  : "Informasi yang tersusun, lebih mudah dipahami."
            }}
          </p>
        </div>
        <RouterLink v-if="page === 'home'" to="/new" class="button"
          ><Plus /> Tambah anak</RouterLink
        ><button
          v-if="page === 'report'"
          :disabled="busy || !reportReady"
          @click="printReport()"
        >
          <Printer /> Cetak / simpan PDF
        </button>
      </div>
      <nav v-if="id" class="tabs" aria-label="Halaman anak">
        <RouterLink
          v-for="link in links"
          :key="link.path"
          :to="`/children/${id}/${link.path}`"
          :class="{ selected: page === (link.path || 'status') }"
          ><component :is="link.icon" />{{ link.label }}</RouterLink
        >
      </nav>
      <div v-if="error" role="alert" tabindex="-1" class="message error">
        <AlertCircle />
        <div>
          {{ error }}
          <p v-if="page === 'measurement' || page === 'food'">
            Jika pesan menyebut data sudah tersimpan, periksa riwayat sebelum
            mengirim ulang.
          </p>
          <button v-else @click="load">Coba lagi</button
          ><RouterLink
            v-if="id"
            :to="`/children/${id}/${page === 'food' ? 'food' : 'history'}`"
            >Lihat riwayat</RouterLink
          >
        </div>
      </div>
      <p v-if="notice" role="status" class="message">{{ notice }}</p>
      <div v-if="busy" class="loading" role="status">Memuat catatan…</div>
      <template v-else>
        <section v-if="!validPage" class="card">
          <h2>Halaman tidak ditemukan</h2>
          <RouterLink to="/">Kembali ke beranda</RouterLink>
        </section>
        <template v-if="page === 'home'"
          ><section class="welcome">
            <div>
              <span class="eyebrow">CATATAN HARI INI</span>
              <h2>Kenali perjalanannya,<br />satu catatan setiap waktu.</h2>
              <p>
                Mulai dari profil anak, lalu simpan pengukuran<br
                  class="desktop"
                />
                dari kunjungan Posyandu terakhir.
              </p>
            </div>
            <div class="hero-art" aria-hidden="true">
              <span></span><Activity :size="86" /><i></i>
            </div>
          </section>
          <div class="section-title">
            <h2>Anak dalam pantauan</h2>
            <span>{{ children.length }} profil anak</span>
          </div>
          <div class="cards">
            <RouterLink
              v-for="c in children"
              :key="c.id"
              :to="`/children/${c.id}`"
              class="card child-card"
              ><div class="child-top">
                <span class="avatar">{{ c.name.slice(0, 1) }}</span
                ><ArrowUpRight />
              </div>
              <h2>{{ c.name }}</h2>
              <p class="muted">
                {{ age(c) }} bulan ·
                {{ c.sex === "female" ? "Perempuan" : "Laki-laki" }}
              </p>
              <span class="badge" :class="c.status?.level">{{
                c.status?.level_label || "Status belum tersedia"
              }}</span>
              <div class="card-footer">
                Pengukuran terakhir
                <strong>{{ dateLabel(c.status?.latest?.measured_at) }}</strong>
              </div></RouterLink
            ><RouterLink to="/new" class="card add-card"
              ><Plus />
              <h3>Tambahkan profil anak</h3>
              <p>Mulai catatan tumbuh kembangnya.</p></RouterLink
            >
          </div></template
        >
        <form
          v-if="page === 'new' || page === 'measurement'"
          class="card form-card"
          @submit.prevent="submit(page)"
        >
          <div class="section-title">
            <h2>
              {{ page === "new" ? "Identitas anak" : "Hasil pengukuran" }}
            </h2>
            <span>* Wajib diisi</span>
          </div>
          <div class="form-grid">
            <label
              v-for="f in page === 'new' ? childFields : measureFields"
              :key="f.key"
              :for="f.key"
              >{{ f.label }}{{ f.required ? " *" : ""
              }}<input
                :id="f.key"
                v-model="form[f.key]"
                :type="f.type"
                :required="f.required"
                :maxlength="f.key === 'name' ? 60 : undefined"
                :min="f.min"
                :max="f.type === 'date' ? today() : f.max"
                :step="f.step"
                :inputmode="f.type === 'number' ? 'decimal' : undefined"
                :aria-invalid="!!fields[f.key]"
                :aria-describedby="fields[f.key] ? f.key + '-error' : undefined"
              /><small
                v-if="fields[f.key]"
                :id="f.key + '-error'"
                class="field-error"
                >{{ fields[f.key] }}</small
              ></label
            ><label v-if="page === 'new'"
              >Jenis kelamin<select v-model="form.sex">
                <option value="female">Perempuan</option>
                <option value="male">Laki-laki</option>
              </select></label
            ><template v-else
              ><label
                >Posisi pengukuran<select v-model="form.position">
                  <option value="recumbent">Berbaring</option>
                  <option value="standing">Berdiri</option>
                </select></label
              ><label
                >Sumber pengukuran<select v-model="form.source">
                  <option value="posyandu">Posyandu</option>
                  <option value="puskesmas">Puskesmas</option>
                  <option value="home">Rumah</option>
                </select></label
              ><label
                >Catatan (opsional)<textarea
                  v-model="form.note"
                  maxlength="200"
                /></label
            ></template>
          </div>
          <label v-if="page === 'new'" class="check"
            ><input type="checkbox" v-model="form.is_preterm" /> Anak lahir
            prematur</label
          >
          <p v-for="(message, key) in fields" :key="key" class="field-error">
            {{ key }}: {{ message }}
          </p>
          <div class="actions">
            <button
              type="button"
              class="secondary"
              @click="page === 'new' ? router.push('/') : go()"
            >
              Batal</button
            ><button :disabled="saving">
              {{
                saving
                  ? "Menyimpan…"
                  : "Simpan " + (page === "new" ? "profil" : "pengukuran")
              }}
            </button>
          </div>
        </form>
        <template v-if="page === 'status' || page === 'report'"
          ><div class="detail-grid">
            <section class="card status-card" :class="status?.level">
              <span class="eyebrow">STATUS TERKINI</span>
              <h2>{{ status?.level_label || "Status belum tersedia" }}</h2>
              <p v-if="status?.latest">
                Pengukuran {{ dateLabel(status.latest.measured_at) }}
              </p>
              <p v-else>Catatan pengukuran akan tampil di sini.</p>
              <RouterLink
                v-if="page !== 'report'"
                :to="`/children/${id}/measurement`"
                class="button"
                ><Plus /> Catat pengukuran</RouterLink
              >
            </section>
            <section class="card">
              <h2>Catatan terakhir</h2>
              <div class="metrics">
                <div>
                  <span>Berat badan</span
                  ><strong
                    >{{ status?.latest?.weight_kg ?? "—" }}
                    <small>kg</small></strong
                  >
                </div>
                <div>
                  <span>Panjang / tinggi</span
                  ><strong
                    >{{ status?.latest?.length_height_cm ?? "—" }}
                    <small>cm</small></strong
                  >
                </div>
              </div>
              <RouterLink :to="`/children/${id}/report`"
                >Buka laporan <ArrowUpRight :size="16"
              /></RouterLink>
            </section>
          </div>
          <section class="card">
            <h2>Hal yang perlu diperhatikan</h2>
            <details
              v-for="(reason, index) in status?.reasons || []"
              :key="index"
            >
              <summary>
                {{ reason.title }}
                <span class="badge" :class="reason.level">{{
                  reason.level
                }}</span>
              </summary>
              <p>{{ reason.message }}</p>
              <details>
                <summary>Lihat detail</summary>
                <dl class="evidence">
                  <template v-for="(value, key) in reason.evidence" :key="key"
                    ><dt>{{ key }}</dt>
                    <dd>{{ value }}</dd></template
                  >
                </dl>
              </details>
            </details>
            <p v-if="!status?.reasons?.length" class="muted">
              {{
                status
                  ? "Tidak ada alasan yang ditampilkan oleh layanan."
                  : "Menunggu hasil dari layanan evaluasi."
              }}
            </p>
            <div v-for="g in relatedGuides" :key="g.id" class="related-guide">
              <h3>{{ g.title }}</h3>
              <p class="preserve">{{ g.body }}</p>
              <small>Sumber: {{ g.source }}</small>
            </div>
            <RouterLink to="/guides">Lihat semua panduan</RouterLink>
          </section>
          <section v-if="status?.next_kpsp" class="card">
            <h2>Skrining perkembangan</h2>
            <p>
              Formulir {{ status.next_kpsp.questionnaire_age_months }} bulan ·
              {{
                status.next_kpsp.due ? "Sudah jatuh tempo" : "Belum jatuh tempo"
              }}
            </p>
            <RouterLink :to="`/children/${id}/kpsp`"
              >Lihat skrining <ArrowUpRight :size="16"
            /></RouterLink>
          </section>
          <section v-if="status?.diet" class="card">
            <h2>Catatan makan · {{ dateLabel(status.diet.recall_date) }}</h2>
            <p>{{ status.diet.group_count }} kelompok pangan tercatat</p>
            <dl>
              <template v-for="key in ['mdd', 'mmf', 'eff']" :key="key"
                ><dt>{{ key.toUpperCase() }}</dt>
                <dd>
                  {{ status.diet[key] ? "Terpenuhi" : "Belum terpenuhi" }}
                </dd></template
              >
            </dl>
          </section>
          <template v-if="page === 'report'"
            ><p>Dicetak {{ dateLabel(today()) }}</p>
            <p v-if="reportWarning" role="status" class="message error">
              Kurva belum tersedia: {{ reportWarning }}
            </p>
            <GrowthChart
              v-if="growth"
              :data="growth"
              @ready="reportReady = true"
            /><button v-else class="secondary" @click="reportReady = true">
              Lanjutkan cetak tanpa kurva
            </button></template
          ></template
        >
        <section v-if="page === 'growth'" class="card">
          <div class="section-title">
            <h2>Perjalanan pertumbuhan</h2>
            <select v-model="indicator" aria-label="Indikator kurva">
              <option value="lhfa">Panjang / tinggi menurut umur</option>
              <option value="wfa">Berat menurut umur</option>
              <option value="wfl_wfh">Berat menurut panjang / tinggi</option>
              <option value="hcfa">Lingkar kepala menurut umur</option>
            </select>
          </div>
          <GrowthChart v-if="growth" :data="growth" />
          <p v-else class="muted">Kurva belum tersedia.</p>
        </section>
        <section v-if="page === 'history' || page === 'report'" class="card">
          <h2>Riwayat pengukuran</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Tanggal</th>
                  <th>Berat (kg)</th>
                  <th>PB/TB (cm)</th>
                  <th v-if="page !== 'report'">Tindakan</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in measurements" :key="m.id">
                  <td>{{ dateLabel(m.measured_at) }}</td>
                  <td>{{ m.weight_kg }}</td>
                  <td>{{ m.length_height_cm ?? "—" }}</td>
                  <td v-if="page !== 'report'">
                    <button
                      class="danger secondary"
                      @click="deleteId = m.id"
                      :aria-label="
                        'Hapus pengukuran ' + dateLabel(m.measured_at)
                      "
                    >
                      <Trash2 :size="18" /> Hapus
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="!measurements.length" class="muted">Belum ada pengukuran.</p>
        </section>
        <template v-if="page === 'kpsp'"
          ><section v-if="questionnaire" class="card form-card">
            <h2>
              Kuesioner {{ questionnaire.questionnaire_age_months }} bulan
            </h2>
            <p>{{ questionnaire.due ? "Jatuh tempo" : "Belum jatuh tempo" }}</p>
            <template
              v-if="questionnaire.due && questionnaire.items?.length === 10"
              ><p>Butir {{ step + 1 }} dari 10</p>
              <progress :value="step + 1" max="10" />
              <h2>{{ questionnaire.items[step].question }}</h2>
              <div class="actions">
                <button
                  v-for="answer in [true, false]"
                  :key="String(answer)"
                  :class="{
                    secondary:
                      answers[questionnaire.items[step].item_no] !== answer,
                  }"
                  :aria-pressed="
                    answers[questionnaire.items[step].item_no] === answer
                  "
                  @click="answers[questionnaire.items[step].item_no] = answer"
                >
                  {{ answer ? "Ya" : "Tidak" }}
                </button>
              </div>
              <div class="actions">
                <button
                  class="secondary"
                  :disabled="step === 0"
                  @click="step--"
                >
                  Sebelumnya</button
                ><button
                  v-if="step < 9"
                  :disabled="
                    answers[questionnaire.items[step].item_no] === undefined
                  "
                  @click="step++"
                >
                  Berikutnya</button
                ><button
                  v-else
                  :disabled="Object.keys(answers).length !== 10 || saving"
                  @click="submit('kpsp')"
                >
                  Simpan jawaban
                </button>
              </div></template
            >
          </section>
          <section v-else-if="!error" class="card">
            Kuesioner belum tersedia.
          </section></template
        >
        <section v-if="page === 'kpsp' || page === 'report'" class="card">
          <h2>Riwayat skrining</h2>
          <p v-for="r in results" :key="r.id">
            {{ dateLabel(r.answered_at) }} ·
            {{ r.questionnaire_age_months }} bulan · {{ r.result }}
          </p>
          <p v-if="!results.length" class="muted">Belum ada hasil skrining.</p>
        </section>
        <template v-if="page === 'food'"
          ><form class="card form-card" @submit.prevent="submit('food')">
            <label
              >Tanggal yang dicatat<input
                type="date"
                v-model="form.recall_date"
                :max="today()"
                required /></label
            ><label class="check"
              ><input type="checkbox" v-model="form.breastfed" /> Minum ASI pada
              hari tersebut</label
            >
            <fieldset>
              <legend>Kelompok pangan yang dimakan</legend>
              <div class="food-grid">
                <label v-for="g in groups" :key="g.key" class="check"
                  ><input
                    type="checkbox"
                    v-model="form.food_groups"
                    :value="g.key"
                  />{{ g.label }}</label
                >
              </div>
            </fieldset>
            <div class="form-grid">
              <label
                >Jumlah makan padat / lunak<input
                  type="number"
                  min="0"
                  max="10"
                  step="1"
                  required
                  v-model="form.meal_count" /></label
              ><label
                >Jumlah minum susu selain ASI (opsional)<input
                  type="number"
                  min="0"
                  max="10"
                  step="1"
                  v-model="form.milk_feed_count"
              /></label>
            </div>
            <p v-for="(message, key) in fields" :key="key" class="field-error">
              {{ key }}: {{ message }}
            </p>
            <button :disabled="saving">
              {{ saving ? "Menyimpan…" : "Simpan catatan makan" }}
            </button>
          </form>
          <section class="card">
            <h2>Catatan 14 hari terakhir</h2>
            <p v-for="f in foods" :key="f.id">
              {{ dateLabel(f.recall_date) }} · {{ f.meal_count }} kali makan
            </p>
            <p v-if="!foods.length" class="muted">Belum ada catatan makan.</p>
          </section></template
        >
        <form
          v-if="page === 'guides'"
          class="card guide-filter"
          @submit.prevent="load"
        >
          <label
            >Kategori<select v-model="guideCategory">
              <option value="">Semua panduan</option>
              <option value="mpasi">GiziCerdas</option>
              <option value="stimulasi">Stimulasi Pintar</option>
            </select></label
          ><label
            >Umur (bulan)<input
              v-model="guideAge"
              type="number"
              min="0"
              max="60"
              step="1"
              placeholder="Semua umur" /></label
          ><button>Terapkan</button>
        </form>
        <section v-if="page === 'guides'" class="cards">
          <article v-for="g in guides" :key="g.id" class="card">
            <span class="eyebrow">{{
              g.category === "mpasi" ? "GiziCerdas" : "Stimulasi Pintar"
            }}</span>
            <h2>{{ g.title }}</h2>
            <p class="preserve">{{ g.body }}</p>
            <small>Sumber: {{ g.source }}</small>
          </article>
          <div v-if="!guides.length && !error" class="card">
            <BookOpen />
            <h2>Panduan sedang disiapkan</h2>
            <p>Materi akan tampil setelah tersedia dari layanan.</p>
          </div>
        </section>
      </template>
      <footer>
        Alat skrining, bukan diagnosis. Konfirmasikan hasil skrining di
        Posyandu/Puskesmas.
      </footer>
    </main>
  </div>
  <nav class="mobile-nav">
    <RouterLink to="/"><House />Beranda</RouterLink
    ><RouterLink to="/guides"><BookOpen />Panduan</RouterLink>
  </nav>
  <div
    v-if="deleteId"
    class="modal-backdrop"
    @keydown="trapDialog"
    @keydown.esc="deleteId = ''"
    @click.self="deleteId = ''"
  >
    <section
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="delete-title"
      class="card dialog"
    >
      <h2 id="delete-title">Hapus pengukuran ini?</h2>
      <p>
        Data akan dihapus. Status dan kurva dihitung ulang dari catatan yang
        tersisa.
      </p>
      <div class="actions">
        <button autofocus @click="deleteId = ''">Batal</button
        ><button class="danger" :disabled="saving" @click="remove">
          Hapus pengukuran
        </button>
      </div>
    </section>
  </div>
</template>
