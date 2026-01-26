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
          class="lucide lucide-settings2-icon lucide-settings-2"
        >
          <path d="M14 17H5" />
          <path d="M19 7h-9" />
          <circle cx="17" cy="17" r="3" />
          <circle cx="7" cy="7" r="3" />
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

    <v-card class="model-upload-card mb-3" color="#2a2a2a" elevation="0">
      <v-card-title
        class="text-subtitle-1 font-weight-bold pa-3 d-flex align-center justify-space-between"
        style="color: #e0e0e0"
      >
        <div class="d-flex align-center ga-2">
          <div class="bg-grey-darken-3 bg-opacity-30 text-light-blue-lighten-3 pa-1 rounded d-flex">
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
          color="light-blue-lighten-3"
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
        <!-- Accordion 형태의 모델 선택 -->
        <v-expansion-panels v-model="expandedPanel" variant="accordion">
          <v-expansion-panel
            v-for="modelType in models"
            :key="modelType.value"
            :value="modelType.value"
          >
            <v-expansion-panel-title @click="handlePanelClick(modelType)" class="px-3 py-2">
              <div class="d-flex align-center justify-space-between">
                <span class="text-grey-lighten-5 d-flex align-center ga-2">
                  <div
                    class="bg-grey-darken-3 bg-opacity-30 text-light-blue-lighten-3 pa-1 rounded d-flex"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      class="lucide lucide-layers-icon lucide-layers"
                    >
                      <path
                        d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"
                      />
                      <path
                        d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"
                      />
                      <path
                        d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"
                      />
                    </svg>
                  </div>
                  {{ modelType.value }}
                </span>
                <span class="model-count">{{ getModelCount(modelType) }}</span>
              </div>
            </v-expansion-panel-title>

            <v-expansion-panel-text>
              <v-radio-group
                v-if="getCachedDetails(modelType).length > 0"
                :model-value="selectedModel"
                @update:model-value="handleModelUpdate"
                hide-details
              >
                <v-radio
                  v-for="detail in getCachedDetails(modelType)"
                  :key="detail.value"
                  :label="detail.text"
                  :value="detail"
                  color="light-blue-lighten-3"
                  density="compact"
                  class="mb-1 radio-small"
                >
                  <template v-slot:label>
                    <div class="text-caption text-grey-lighten-4">{{ detail.text }}</div>
                  </template>
                </v-radio>
              </v-radio-group>

              <p
                v-else-if="
                  modelDetailsCache[modelType.value] !== undefined &&
                  getCachedDetails(modelType).length === 0
                "
                class="text-caption text-grey-lighten-1"
              >
                사용 가능한 모델이 없습니다.
              </p>

              <div v-else class="d-flex align-center justify-center pa-3">
                <v-progress-circular indeterminate size="24" width="2"></v-progress-circular>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <!-- 모델 선택 버튼 -->
        <v-btn
          block
          @click="$emit('loadModel')"
          variant="tonal"
          :disabled="!selectedModel || isLoadingModel || modelStatusSuccess"
          :loading="isLoadingModel"
        >
          <template v-if="!isLoadingModel">
            <svg
              v-if="modelStatusSuccess"
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="lucide lucide-check-circle mr-2"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <path d="m9 11 3 3L22 4" />
            </svg>
            <svg
              v-else
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
          </template>
          {{ buttonText }}
        </v-btn>

        <!-- 에러 alert만 표시 -->
        <template v-if="modelStatusMessage && !isLoadingModel && !modelStatusSuccess">
          <v-alert type="error" variant="tonal" density="compact" class="mb-2">
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
  data() {
    return {
      expandedPanel: null,
      modelDetailsCache: {}, // 타입별 세부 모델 캐시
    }
  },
  computed: {
    alertType() {
      if (this.isLoadingModel) return 'info'
      return this.modelStatusSuccess ? 'success' : 'error'
    },
    buttonText() {
      if (this.isLoadingModel) return '모델 불러오는 중...'
      if (this.modelStatusSuccess) return '모델 선택 완료'
      return '모델 선택'
    },
  },
  emits: [
    'update:selectedModelType',
    'update:selectedModel',
    'refreshModels',
    'loadModel',
    'fetchModelDetails',
    'uploadSuccess',
    'resetModelStatus',
  ],
  watch: {
    selectedModel(newVal, oldVal) {
      // 실제 모델 값이 변경되었을 때만 버튼 상태 초기화
      const newValue = newVal?.value
      const oldValue = oldVal?.value

      if (newValue !== oldValue && newValue && oldValue && this.modelStatusSuccess) {
        this.$emit('resetModelStatus')
      }
    },
    modelDetails(newDetails) {
      // modelDetails가 변경되면 현재 선택된 타입의 캐시에 저장
      if (this.selectedModelType) {
        this.modelDetailsCache[this.selectedModelType.value] = newDetails
      }
    },
  },
  methods: {
    getDeviceInfoIcon(index) {
      const icons = ['mdi-memory', 'mdi-chip', 'mdi-harddisk', 'mdi-speedometer']
      return icons[index] || 'mdi-information'
    },
    handlePanelClick(modelType) {
      // 항상 selectedModelType 업데이트
      this.$emit('update:selectedModelType', modelType)

      // 캐시에 없으면 fetchModelDetails 호출
      if (this.modelDetailsCache[modelType.value] === undefined) {
        this.$emit('fetchModelDetails', modelType)
      }
      // 아코디언 클릭 시에는 resetModelStatus 호출 안함
    },
    handleModelUpdate(value) {
      this.$emit('update:selectedModel', value)
      // 라디오 버튼 변경 시에만 리셋 (watch에서 처리)
    },
    getCachedDetails(modelType) {
      return this.modelDetailsCache[modelType.value] || []
    },
    getModelCount(modelType) {
      // 캐시에 있으면 캐시된 개수 표시
      const cached = this.modelDetailsCache[modelType.value]
      if (cached && cached.length > 0) {
        return `(${cached.length}개 모델)`
      }
      // 초기 count 표시
      if (modelType.count > 0) {
        return `(${modelType.count}개 모델)`
      }
      return ''
    },
  },
}
</script>

<style scoped>
/* Accordion 패널 스타일 */

/* v-expansion-panel-text wrapper padding */
:deep(.v-expansion-panel-text__wrapper) {
  padding: 4px 12px 8px !important;
}

/* 라디오 버튼 크기 조정 - 체크 부분만 */
.radio-small :deep(.v-selection-control__input) {
  transform: scale(0.75);
}

.radio-small :deep(.v-selection-control__input .v-icon) {
  font-size: 18px;
}

.model-count {
  font-size: 12px;
  color: #888;
  margin-left: 8px;
}

.model-radio:last-child {
  margin-bottom: 0;
}

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

.divider-line {
  height: 1px;
  background: linear-gradient(to right, transparent, #333, transparent);
  margin: 4px 0;
}
</style>
