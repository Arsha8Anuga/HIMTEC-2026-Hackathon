<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, ScatterChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([LineChart, ScatterChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])
const props=defineProps<{data:any}>();const root=ref<HTMLElement>();let chart:echarts.ECharts|undefined;let observer:ResizeObserver
function render(){if(!chart)return;const d=props.data,r=d.reference;const colors=['#9a514b','#b17d29','#23695b','#627eb0','#806595'];const keys=['sd_neg3','sd_neg2','median','sd_pos2','sd_pos3'];const labels=['−3 SD','−2 SD','Median','+2 SD','+3 SD'];const x=(v:number)=>d.x_unit==='days'?Number((v/30.4375).toFixed(2)):v
chart.setOption({animation:false,tooltip:{trigger:'axis'},legend:{data:[...labels,'Pengukuran'],bottom:0},grid:{left:50,right:20,top:30,bottom:85},xAxis:{type:'value',name:d.x_unit==='days'?'Umur (bulan)':'Panjang / tinggi (cm)',nameLocation:'middle',nameGap:30},yAxis:{type:'value',scale:true,name:['wfa','wfl_wfh'].includes(d.indicator)?'kg':'cm'},series:[...keys.map((key,i)=>({name:labels[i],type:'line',showSymbol:false,lineStyle:{width:i===2?2:1.5,type:i===2?'solid':'dashed'},color:colors[i],data:r.x.map((v:number,j:number)=>[x(v),r[key][j]])})),{name:'Pengukuran',type:'scatter',symbolSize:12,color:'#203e53',data:d.points.map((p:any)=>({value:[x(p.x),p.value],symbol:p.flagged?'diamond':'circle'}))}]},true)}
onMounted(()=>{chart=echarts.init(root.value);render();observer=new ResizeObserver(()=>chart?.resize());observer.observe(root.value!)});watch(()=>props.data,render);onBeforeUnmount(()=>{observer?.disconnect();chart?.dispose()})
</script>
<template><div ref="root" class="chart" role="img" aria-label="Kurva pertumbuhan dan garis acuan WHO. Data pengukuran tersedia pada tabel di bawah."/><p class="muted">Titik berlian menandai pengukuran dengan flag dari layanan.</p><details><summary>Data pengukuran pada kurva</summary><div class="table-wrap"><table><thead><tr><th>Tanggal</th><th>Nilai</th><th>Flag</th></tr></thead><tbody><tr v-for="p in data.points" :key="p.measurement_id"><td>{{p.measured_at}}</td><td>{{p.value}}</td><td>{{p.flagged?'Ya':'Tidak'}}</td></tr></tbody></table></div></details></template>
