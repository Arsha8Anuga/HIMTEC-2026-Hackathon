<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from "vue";
import * as echarts from "echarts/core";
import { LineChart, ScatterChart, CustomChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { dateLabel } from "../lib/api";
import { referenceKeys, type GrowthData } from "../lib/growth";

echarts.use([
  LineChart,
  ScatterChart,
  CustomChart,
  GridComponent,
  TooltipComponent,
  SVGRenderer,
]);
const emit = defineEmits<{ ready: []; unavailable: [] }>();
const props = defineProps<{ data: GrowthData }>();
const root = ref<HTMLElement>();
const labels = ["−3 SD", "−2 SD", "Median", "+2 SD", "+3 SD", "Pengukuran"];
const colors = [
  "#9a514b",
  "#89601c",
  "#23695b",
  "#486998",
  "#806595",
  "#203e53",
];
const shown = ref(labels.map(() => true));
const hasData = computed(
  () => props.data.reference.x.length > 0 || props.data.points.length > 0,
);
let chart: echarts.ECharts | undefined;
let observer: ResizeObserver | undefined;
function render() {
  if (!root.value || !hasData.value) {
    emit("unavailable");
    return;
  }
  chart ||= echarts.init(root.value, undefined, { renderer: "svg" });
  const d = props.data,
    r = d.reference;
  const x = (v: number) => (d.x_unit === "days" ? v / 30.4375 : v);
  // Each polygon follows only adjacent reference values supplied by the API.
  const bands = referenceKeys.slice(1).map((key, i) => ({
    type: "custom" as const,
    silent: true,
    clip: true,
    tooltip: { show: false },
    encode: { x: 0, y: 1 },
    data: r.x.length ? [[x(r.x[0]!), r[key][0]]] : [],
    renderItem: (
      _params: unknown,
      api: { coord: (point: number[]) => number[] },
    ) => ({
      type: "polygon",
      shape: {
        points: [
          ...r.x.map((v, j) => api.coord([x(v), r[key][j]!])),
          ...r.x
            .map((v, j) => api.coord([x(v), r[referenceKeys[i]!][j]!]))
            .reverse(),
        ],
      },
      style: {
        fill: ["#efe4dc", "#e8efe4", "#e8efe4", "#e2e7f0"][i],
        opacity: 0.7,
      },
    }),
  }));
  chart.setOption(
    {
      animation: false,
      tooltip: {
        trigger: "axis",
        valueFormatter: (value: unknown) =>
          typeof value === "number"
            ? value.toLocaleString("id-ID", { maximumFractionDigits: 2 })
            : String(value),
      },
      grid: { left: 50, right: 20, top: 30, bottom: 55 },
      xAxis: {
        type: "value",
        scale: d.x_unit === "cm", // sumbu cm mulai dari data, bukan 0 cm
        name: d.x_unit === "days" ? "Umur (bulan)" : "Panjang / tinggi (cm)",
        nameLocation: "middle",
        nameGap: 30,
        axisLabel: {
          formatter: (v: number) =>
            v.toLocaleString("id-ID", { maximumFractionDigits: 1 }),
        },
      },
      yAxis: {
        type: "value",
        scale: true,
        name: ["wfa", "wfl_wfh"].includes(d.indicator) ? "kg" : "cm",
      },
      series: [
        ...bands,
        ...referenceKeys.map((key, i) => ({
          name: labels[i],
          type: "line" as const,
          showSymbol: false,
          lineStyle: {
            width: i === 2 ? 2 : 1.5,
            type: i === 2 ? ("solid" as const) : ("dashed" as const),
          },
          color: colors[i],
          data: shown.value[i] ? r.x.map((v, j) => [x(v), r[key][j]]) : [],
        })),
        {
          name: "Pengukuran",
          type: "scatter",
          symbolSize: 12,
          color: colors[5],
          data: shown.value[5]
            ? d.points.map((p) => ({
                value: [x(p.x), p.value],
                symbol: p.flagged ? "diamond" : "circle",
              }))
            : [],
        },
      ],
    },
    true,
  );
  emit("ready");
}
function resize() {
  chart?.resize();
}
onMounted(() => {
  render();
  observer = new ResizeObserver(resize);
  if (root.value) observer.observe(root.value);
  window.addEventListener("beforeprint", resize);
  window.addEventListener("afterprint", resize);
});
watch(() => props.data, render);
watch(shown, render, { deep: true });
onBeforeUnmount(() => {
  observer?.disconnect();
  chart?.dispose();
  window.removeEventListener("beforeprint", resize);
  window.removeEventListener("afterprint", resize);
});
</script>
<template>
  <div
    ref="root"
    v-show="hasData"
    class="chart"
    role="img"
    aria-label="Kurva pertumbuhan dari API. Gunakan legenda dan tabel di bawah untuk membaca data."
  />
  <p v-if="!hasData" class="muted">Belum ada data kurva.</p>
  <p v-else-if="!data.reference.x.length" class="muted">
    Garis acuan belum tersedia dari layanan.
  </p>
  <fieldset v-if="hasData" class="chart-legend">
    <legend>Garis dan titik yang ditampilkan</legend>
    <label v-for="(label, i) in labels" :key="label" class="check"
      ><input type="checkbox" v-model="shown[i]" /><span
        class="legend-swatch"
        :style="{ background: colors[i] }"
        aria-hidden="true"
      />{{ label }}</label
    >
  </fieldset>
  <p class="muted">
    Titik berlian menandai pengukuran dengan flag dari layanan.
  </p>
  <details>
    <summary>Data pengukuran pada kurva ({{ data.points.length }})</summary>
    <p v-if="!data.points.length" class="muted">Belum ada titik pengukuran.</p>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Tanggal</th>
            <th>
              {{
                ["wfa", "wfl_wfh"].includes(data.indicator)
                  ? "Berat (kg)"
                  : "Ukuran (cm)"
              }}
            </th>
            <th>Z-score</th>
            <th>Flag</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in data.points" :key="p.measurement_id">
            <td>{{ dateLabel(p.measured_at) }}</td>
            <td>{{ p.value.toLocaleString("id-ID") }}</td>
            <td>{{ p.z ?? "—" }}</td>
            <td>{{ p.flagged ? "Ya" : "Tidak" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </details>
</template>
