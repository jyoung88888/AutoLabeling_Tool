<template>
  <div class="labeling-progress">
    <v-card flat class="progress-card">
      <div class="progress-bar-wrapper pa-3">
        <v-progress-linear
          :model-value="progressPercent"
          color="#4f9cf5"
          height="10"
          bg-color="#444"
          class="mb-1"
        ></v-progress-linear>
        <div class="progress-percent text-body-2 text-center">{{ Math.round(progressPercent) }}%</div>
      </div>
      
      <v-divider></v-divider>
      
      <div class="current-file-info pa-3">
        <div class="text-subtitle-2 mb-1">현재 처리 중:</div>
        <div class="text-body-2">{{ currentFile }}</div>
      </div>
      
      <v-divider></v-divider>
      
      <v-row class="time-info-row ma-0">
        <v-col cols="6" class="pa-3 time-info-col">
          <div class="text-subtitle-2 mb-1">진행 시간:</div>
          <div class="text-body-2">{{ timeInfo.elapsed }}</div>
        </v-col>
        <v-divider vertical></v-divider>
        <v-col cols="6" class="pa-3 time-info-col">
          <div class="text-subtitle-2 mb-1">예상 남은 시간:</div>
          <div class="text-body-2">{{ timeInfo.eta }}</div>
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>

<script>
export default {
  props: {
    progressPercent: {
      type: Number,
      default: 0
    },
    currentFile: {
      type: String,
      default: ''
    },
    timeInfo: {
      type: Object,
      default: () => ({
        elapsed: '0초',
        eta: '계산 중...'
      })
    }
  }
}
</script>

<style scoped>
.labeling-progress {
  width: 100%;
}

.progress-card {
  background-color: #242424 !important;
  border-radius: 4px;
  border: 1px solid #333 !important;
  overflow: hidden;
}

.progress-bar-wrapper {
  position: relative;
}

.progress-percent {
  margin-top: 4px;
  color: #e0e0e0;
}

.current-file-info {
  background-color: #242424;
  color: #e0e0e0;
}

.time-info-row {
  background-color: #242424;
}

.time-info-col {
  color: #e0e0e0;
}

:deep(.v-divider) {
  border-color: #333 !important;
  opacity: 1;
}
</style> 