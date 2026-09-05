<template>
  <div class="dashboard">
    <a-row :gutter="16">
      <a-col :span="6" v-for="card in statCards" :key="card.title">
        <StatCard
          :title="card.title"
          :value="card.value"
          :icon="card.icon"
          :color="card.color"
          :sub-title="card.subTitle"
        />
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="16">
        <PageCard title="文章生成趋势（近7天）">
          <v-chart class="chart" :option="trendOption" autoresize />
        </PageCard>
      </a-col>
      <a-col :span="8">
        <PageCard title="平台账号分布">
          <v-chart class="chart" :option="platformOption" autoresize />
        </PageCard>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <PageCard title="热门标题 TOP5（按阅读量）">
          <a-list :bordered="false" size="small">
            <a-list-item v-for="(item, idx) in topTitles" :key="idx">
              <a-list-item-meta>
                <template #title>
                  <a-tag :color="idx < 3 ? 'red' : 'blue'" size="small">{{ idx + 1 }}</a-tag>
                  <span style="margin-left:8px">{{ item.title }}</span>
                </template>
                <template #description>
                  阅读量: <strong :style="{ color: '#f53f3f' }">{{ formatRead(item.read) }}</strong>
                  · 评论: {{ item.comment }} · 点赞: {{ item.praise }}
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </PageCard>
      </a-col>
      <a-col :span="12">
        <PageCard title="文章状态分布">
          <v-chart class="chart" :option="statusOption" autoresize />
        </PageCard>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="24">
        <PageCard title="快捷操作">
          <a-space wrap>
            <a-button type="primary" @click="$router.push('/article')">
              <template #icon><icon-file /></template>文章管理
            </a-button>
            <a-button status="success" @click="$router.push('/title-spider')">
              <template #icon><icon-search /></template>标题采集
            </a-button>
            <a-button status="warning" @click="$router.push('/article/batch-import')">
              <template #icon><icon-upload /></template>批量导入
            </a-button>
            <a-button status="danger" @click="startSpider">
              <template #icon><icon-play-circle /></template>启动爬虫
            </a-button>
            <a-button @click="$router.push('/settings/format')">
              <template #icon><icon-settings /></template>排版设置
            </a-button>
            <a-button @click="$router.push('/command')">
              <template #icon><icon-command /></template>指令队列
            </a-button>
          </a-space>
        </PageCard>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DataZoomComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { Message } from '@arco-design/web-vue'
import {
  IconFile, IconSearch, IconUser, IconCommand,
  IconUpload, IconPlayCircle, IconSettings
} from '@arco-design/web-vue/es/icon'
import StatCard from '@/components/common/StatCard.vue'
import PageCard from '@/components/common/PageCard.vue'

use([
  CanvasRenderer, LineChart, PieChart, BarChart,
  TitleComponent, TooltipComponent, LegendComponent,
  GridComponent, DataZoomComponent
])

const statCards = ref([
  { title: '文章总数', value: '128', icon: IconFile, color: '#165dff', subTitle: '较昨日 +12' },
  { title: '今日生成', value: '12', icon: IconCommand, color: '#00b42a', subTitle: '成功 10 / 失败 2' },
  { title: '采集标题', value: '356', icon: IconSearch, color: '#ff7d00', subTitle: '今日新增 28' },
  { title: '在线账号', value: '8', icon: IconUser, color: '#f53f3f', subTitle: '5平台 · 6运行中' }
])

const topTitles = ref([
  { title: '我扮穷去相亲被嫌弃，女方说：你配不上我，我走了，第二天她来公司面试', read: 56800, comment: 678, praise: 3450 },
  { title: '女领导绩效表上给我打0分，害我丢了42万奖金，我秒递辞职信，她凌晨来电', read: 45200, comment: 512, praise: 2340 },
  { title: '我把工资全交岳母整整8年，老婆一直不吭声；我突发脑梗急等手术费找她', read: 41200, comment: 567, praise: 2100 },
  { title: '妹妹不肯借我16万给妻子做手术，转头花112万给外甥买豪车，半年后她钱周转不开', read: 32100, comment: 445, praise: 1890 },
  { title: '婆婆住我家，承担了全部家务和生活开销，我妈来了她便回老家，半个月后面对8600元账单', read: 18900, comment: 256, praise: 890 }
])

const formatRead = (n) => n >= 10000 ? (n / 10000).toFixed(1) + '万' : n

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['生成文章', '生成图片', '存草稿'], bottom: 0 },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
  xAxis: { type: 'category', data: ['08-29', '08-30', '08-31', '09-01', '09-02', '09-03', '09-04'] },
  yAxis: { type: 'value' },
  series: [
    { name: '生成文章', type: 'line', smooth: true, data: [8, 15, 12, 18, 14, 20, 12], itemStyle: { color: '#165dff' }, areaStyle: { opacity: 0.1 } },
    { name: '生成图片', type: 'line', smooth: true, data: [6, 12, 10, 15, 11, 18, 10], itemStyle: { color: '#00b42a' } },
    { name: '存草稿', type: 'line', smooth: true, data: [5, 10, 8, 12, 9, 15, 8], itemStyle: { color: '#ff7d00' } }
  ]
}))

const platformOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
    label: { show: false },
    emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
    data: [
      { value: 3, name: '百家号', itemStyle: { color: '#165dff' } },
      { value: 2, name: '豆包', itemStyle: { color: '#00b42a' } },
      { value: 2, name: '仰度AI', itemStyle: { color: '#ff7d00' } },
      { value: 1, name: '智谱AI', itemStyle: { color: '#722ed1' } },
      { value: 1, name: '元宝', itemStyle: { color: '#14c9c9' } }
    ]
  }]
}))

const statusOption = computed(() => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: ['待生成', '生成中', '成功', '失败', '草稿中', '已导出'] },
  yAxis: { type: 'value' },
  series: [{
    type: 'bar',
    data: [
      { value: 15, itemStyle: { color: '#ff7d00' } },
      { value: 8, itemStyle: { color: '#165dff' } },
      { value: 68, itemStyle: { color: '#00b42a' } },
      { value: 5, itemStyle: { color: '#f53f3f' } },
      { value: 22, itemStyle: { color: '#14c9c9' } },
      { value: 10, itemStyle: { color: '#86909c' } }
    ],
    barWidth: '50%',
    itemStyle: { borderRadius: [4, 4, 0, 0] }
  }]
}))

const startSpider = () => {
  Message.success('爬虫启动指令已发送')
}
</script>

<style scoped>
.chart {
  height: 280px;
  width: 100%;
}
</style>
