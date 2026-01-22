<template>
  <div class="px-2">
    <div class="font-weight-bold mb-2 mt-4 d-flex align-center ga-2">
      <div class="bg-grey-darken-3 bg-opacity-30 text-light-blue pa-1 rounded d-flex">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="lucide lucide-file-cog-icon lucide-file-cog"
        >
          <path
            d="M13.85 22H18a2 2 0 0 0 2-2V8a2 2 0 0 0-.586-1.414l-4-4A2 2 0 0 0 14 2H6a2 2 0 0 0-2 2v6.6"
          />
          <path d="M14 2v5a1 1 0 0 0 1 1h5" />
          <path d="m3.305 19.53.923-.382" />
          <path d="m4.228 16.852-.924-.383" />
          <path d="m5.852 15.228-.383-.923" />
          <path d="m5.852 20.772-.383.924" />
          <path d="m8.148 15.228.383-.923" />
          <path d="m8.53 21.696-.382-.924" />
          <path d="m9.773 16.852.922-.383" />
          <path d="m9.773 19.148.922.383" />
          <circle cx="7" cy="18" r="3" />
        </svg>
      </div>
      모델 설정
    </div>

    <!-- 모델 업로드 컴포넌트 -->
    <ModelUploader
      ref="modelUploader"
      @upload-success="$emit('uploadSuccess', $event)"
      class="mb-3"
    />

    <v-card class="model-upload-card mb-4" color="#2a2a2a" elevation="0">
      <v-card-title
        class="text-subtitle-1 font-weight-bold pa-3 d-flex align-center justify-space-between"
        style="color: #e0e0e0"
      >
        <div class="d-flex align-center ga-2">
          <div class="bg-grey-darken-3 bg-opacity-30 text-light-blue pa-1 rounded d-flex">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="lucide lucide-file-check-icon lucide-file-check"
            >
              <path
                d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"
              />
              <path d="M14 2v5a1 1 0 0 0 1 1h5" />
              <path d="m9 15 2 2 4-4" />
            </svg>
          </div>
          모델 선택
        </div>
        <v-btn
          @click="$emit('refreshModels')"
          color="light-blue"
          size="small"
          variant="tonal"
          icon
          density="comfortable"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="lucide lucide-refresh-ccw-icon lucide-refresh-ccw"
          >
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
            <path d="M3 3v5h5" />
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
            <path d="M16 16h5v5" />
          </svg>
        </v-btn>
      </v-card-title>
      <v-card-text class="model-selection-container px-3 pb-3">
        <v-select
          ref="modelSelect"
          :model-value="selectedModelType"
          @update:model-value="handleModelTypeUpdate"
          :items="models"
          placeholder="모델 선택"
          variant="outlined"
          density="compact"
          hide-details
          :menu-props="{ maxHeight: '400px', maxWidth: '500px', minWidth: '100%' }"
          item-title="text"
          item-value="value"
          return-object
          style="width: 100%"
          class="mb-2 model-select dark-select"
          prepend-inner-icon="mdi-database"
          base-color="#e0e0e0"
        ></v-select>

        <div v-if="modelDetails.length > 0" style="width: 100%; padding: 0 8px">
          <v-select
            ref="detailModelSelect"
            :model-value="selectedModel"
            @update:model-value="$emit('update:selectedModel', $event)"
            :items="modelDetails"
            placeholder="세부 모델 선택"
            variant="outlined"
            density="compact"
            hide-details
            :menu-props="{ maxHeight: '400px', maxWidth: '500px', minWidth: '100%' }"
            item-title="text"
            item-value="value"
            return-object
            style="width: 100%"
            class="mb-2 model-select dark-select"
            prepend-inner-icon="mdi-cube"
            base-color="#e0e0e0"
          ></v-select>
        </div>

        <!-- 모델 상세 정보가 없을 때 알림 -->
        <div
          v-else-if="selectedModelType && modelDetails.length === 0"
          style="width: 100%; padding: 0 8px"
        >
          <v-alert density="compact" type="warning" variant="tonal" class="mb-2">
            선택된 모델 타입에 사용 가능한 모델이 없습니다.
          </v-alert>
        </div>

        <!-- 모델 선택 버튼 -->
        <v-btn
          block
          @click="$emit('loadModel')"
          color="white"
          variant="tonal"
          :disabled="!selectedModel"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="lucide lucide-check-icon lucide-check mr-2"
          >
            <path d="M20 6 9 17l-5-5" />
          </svg>
          모델 선택
        </v-btn>

        <template v-if="modelStatusMessage">
          <v-alert :type="alertType" variant="tonal" density="compact">
            <template v-if="isLoadingModel" #prepend>
              <v-progress-circular
                indeterminate
                size="18"
                width="2"
                color="info"
              ></v-progress-circular>
            </template>
            {{ modelStatusMessage }}
          </v-alert>
        </template>

        <template v-if="deviceInfo.length && deviceInfo[0] !== '알 수 없음'">
          <div class="device-info-section">
            <div class="section-title mb-2">
              <v-icon icon="mdi-chip" size="small" color="#4f9cf5" class="mr-2"></v-icon>
              <span>디바이스 정보</span>
            </div>
            <v-divider color="#333" class="mb-2"></v-divider>
            <div class="device-info-list">
              <div class="device-info-item" v-for="(info, index) in deviceInfo" :key="index">
                <v-icon
                  :icon="getDeviceInfoIcon(index)"
                  size="x-small"
                  color="#8f9bb3"
                  class="mr-2"
                ></v-icon>
                <span class="device-info-text">{{ info }}</span>
              </div>
            </div>
          </div>
        </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import ModelUploader from '../models/ModelUploader.vue'

export default {
  name: 'ModelSettingsSection',
  components: {
    ModelUploader,
  },
  props: {
    models: {
      type: Array,
      default: () => [],
    },
    selectedModelType: {
      type: Object,
      default: null,
    },
    modelDetails: {
      type: Array,
      default: () => [],
    },
    selectedModel: {
      type: Object,
      default: null,
    },
    modelStatusMessage: {
      type: String,
      default: '',
    },
    modelStatusSuccess: {
      type: Boolean,
      default: false,
    },
    isLoadingModel: {
      type: Boolean,
      default: false,
    },
    deviceInfo: {
      type: Array,
      default: () => ['알 수 없음'],
    },
  },
  computed: {
    alertType() {
      if (this.isLoadingModel) return 'info'
      return this.modelStatusSuccess ? 'success' : 'error'
    },
  },
  emits: [
    'update:selectedModelType',
    'update:selectedModel',
    'refreshModels',
    'loadModel',
    'fetchModelDetails',
    'uploadSuccess',
  ],
  methods: {
    getDeviceInfoIcon(index) {
      const icons = ['mdi-memory', 'mdi-chip', 'mdi-harddisk', 'mdi-speedometer']
      return icons[index] || 'mdi-information'
    },
    handleModelTypeUpdate(value) {
      this.$emit('update:selectedModelType', value)
      this.$emit('fetchModelDetails', value)
    },
  },
}
</script>

<style scoped>
.device-info-section {
  width: 100%;
  padding: 8px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
  border: 1px solid #333;
}

.section-title {
  display: flex;
  align-items: center;
  color: #e0e0e0;
  font-size: 14px;
  font-weight: 500;
}

.device-info-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-info-item {
  display: flex;
  align-items: center;
  color: #b0b0b0;
  font-size: 12px;
}

.device-info-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 모델 선택 컨테이너 */
.model-selection-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 모델 타입 리스트 */
.model-type-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 모델 타입 박스 */
.model-type-box {
  padding: 12px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
}

.model-type-box:hover {
  background: #252525;
  border-color: #4f9cf5;
}

.model-type-box.active {
  background: #1a2332;
  border-color: #4f9cf5;
}

.model-type-content {
  gap: 8px;
}

.model-type-icon {
  width: 32px;
  height: 32px;
  background: #2a2a2a;
  border-radius: 6px;
  color: #4f9cf5;
}

.model-info {
  gap: 2px;
}

.model-type-text {
  font-size: 14px;
  font-weight: 600;
  color: #e0e0e0;
}

.model-count-text {
  font-size: 11px;
  color: #888;
}

.chevron-icon {
  color: #666;
  transition: transform 200ms ease;
}

.chevron-icon.rotated {
  transform: rotate(90deg);
}

/* 모델 상세 리스트 */
.model-detail-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 모델 상세 박스 */
.model-detail-box {
  padding: 12px;
  background: #252525;
  border: 1px solid #333;
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
  margin-left: 20px;
}

.model-detail-box:hover {
  background: #2a2a2a;
  border-color: #4f9cf5;
}

.model-detail-box.active {
  background: #1a2332;
  border-color: #4f9cf5;
}

.model-detail-content {
  gap: 8px;
}

.model-detail-icon {
  width: 24px;
  height: 24px;
  background: #2a2a2a;
  border-radius: 4px;
  color: #4f9cf5;
}

.model-detail-text {
  font-size: 13px;
  color: #e0e0e0;
}

.check-icon {
  color: #4f9cf5;
}

.divider-line {
  height: 1px;
  background: linear-gradient(to right, transparent, #333, transparent);
  margin: 4px 0;
}
</style>
