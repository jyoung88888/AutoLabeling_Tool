<template>
  <div>
    <v-list-subheader
      class="text-subtitle-1 font-weight-bold text-wrap pa-0"
      style="color: #e0e0e0"
    >
      <div class="mb-2 mt-2 px-2">
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
          class="lucide lucide-settings-icon lucide-settings"
        >
          <path
            d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"
          />
          <circle cx="12" cy="12" r="3" />
        </svg>
        모델 설정
      </div>
    </v-list-subheader>

    <!-- 모델 업로드 컴포넌트 -->
    <v-list-item>
      <ModelUploader
        ref="modelUploader"
        @upload-success="$emit('uploadSuccess', $event)"
        class="mb-3"
      />
    </v-list-item>

    <v-list-item>
      <v-btn
        block
        @click="$emit('refreshModels')"
        color="#4f9cf5"
        size="small"
        class="mb-2"
        style="color: #fff"
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
        모델 목록 새로고침
      </v-btn>
    </v-list-item>

    <v-list-item style="width: 100%; padding: 0 8px">
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
    </v-list-item>

    <v-list-item v-if="modelDetails.length > 0" style="width: 100%; padding: 0 8px">
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
    </v-list-item>

    <!-- 모델 상세 정보가 없을 때 알림 -->
    <v-list-item
      v-else-if="selectedModelType && modelDetails.length === 0"
      style="width: 100%; padding: 0 8px"
    >
      <v-alert density="compact" type="warning" variant="tonal" class="mb-2">
        선택된 모델 타입에 사용 가능한 모델이 없습니다.
      </v-alert>
    </v-list-item>

    <v-list-item>
      <v-btn
        block
        @click="$emit('loadModel')"
        color="#4f9cf5"
        size="small"
        :disabled="!selectedModel"
        class="mb-2"
        prepend-icon="mdi-upload"
        style="color: #fff"
      >
        모델 로드
      </v-btn>
    </v-list-item>

    <v-list-item v-if="modelStatusMessage">
      <v-alert
        :type="modelStatusSuccess ? 'success' : 'error'"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        {{ modelStatusMessage }}
      </v-alert>
    </v-list-item>

    <v-list-item v-if="deviceInfo.length && deviceInfo[0] !== '알 수 없음'">
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
    </v-list-item>
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
    deviceInfo: {
      type: Array,
      default: () => ['알 수 없음'],
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
      // 디바이스 정보 아이콘 매핑
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

:deep(.model-select .v-field) {
  background-color: #2a2a2a !important;
}

:deep(.model-select .v-field__input) {
  color: #e0e0e0 !important;
}
</style>
