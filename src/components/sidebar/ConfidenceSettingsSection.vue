<template>
  <div>
    <v-list-subheader class="text-subtitle-1 font-weight-bold text-wrap pa-0" style="color: #e0e0e0;">
      <div class="mb-2 mt-4 px-2">🎯 신뢰도 설정</div>
    </v-list-subheader>

    <v-list-item>
      <div class="confidence-settings-section">
        <v-card
          class="confidence-card pa-3 mb-2"
          variant="outlined"
          color="#252525"
          border
        >
          <v-card-title class="pb-2 px-0 text-subtitle-2 font-weight-bold d-flex align-center" style="color: #e0e0e0;">
            <v-icon icon="mdi-target" class="mr-2" color="#4f9cf5" size="small"></v-icon>
            최소 신뢰도 임계값
          </v-card-title>
          <v-divider color="#333" class="mb-3"></v-divider>

          <div class="confidence-control-group">
            <div class="confidence-slider-container">
              <v-slider
                :model-value="confidenceThreshold"
                @update:model-value="updateConfidenceThreshold"
                :min="0"
                :max="1"
                :step="0.01"
                color="#4f9cf5"
                track-color="#333"
                thumb-color="#4f9cf5"
                class="confidence-slider small-thumb"
                hide-details
                :thumb-size="12"
              >
                <template v-slot:prepend>
                  <div class="confidence-label">0</div>
                </template>
                <template v-slot:append>
                  <div class="confidence-label">1</div>
                </template>
              </v-slider>
            </div>

            <div class="confidence-input-container mt-2">
              <v-text-field
                :model-value="confidenceThreshold"
                @update:model-value="updateConfidenceThreshold"
                type="number"
                :min="0"
                :max="1"
                :step="0.01"
                variant="outlined"
                density="compact"
                hide-details
                class="confidence-input"
                prepend-inner-icon="mdi-numeric"
                base-color="#e0e0e0"
                :rules="[validateConfidence]"
                label="임계값 (0.0 ~ 1.0)"
              >
                <template v-slot:append-inner>
                  <v-tooltip location="top">
                    <template v-slot:activator="{ props }">
                      <v-icon
                        v-bind="props"
                        icon="mdi-help-circle"
                        size="small"
                        color="#8f9bb3"
                      ></v-icon>
                    </template>
                    이 값보다 낮은 신뢰도의 바운딩박스는 표시되지 않습니다.
                  </v-tooltip>
                </template>
              </v-text-field>
            </div>
          </div>

          <div class="confidence-display mt-3 d-flex align-center justify-space-between">
            <div class="confidence-value">
              <span class="confidence-value-label">현재 설정:</span>
              <span class="confidence-value-number">{{ Math.round(confidenceThreshold * 100) }}%</span>
            </div>
            <v-btn
              size="x-small"
              variant="text"
              color="#4f9cf5"
              @click="resetToDefault"
              prepend-icon="mdi-restore"
            >
              초기화
            </v-btn>
          </div>
        </v-card>
      </div>
    </v-list-item>
  </div>
</template>

<script>
export default {
  name: 'ConfidenceSettingsSection',
  props: {
    confidenceThreshold: {
      type: Number,
      default: 0.5
    }
  },
  emits: [
    'update:confidenceThreshold'
  ],
  methods: {
    updateConfidenceThreshold(value) {
      // 숫자 타입으로 변환하고 범위 제한
      const numValue = parseFloat(value);
      if (isNaN(numValue)) {
        return;
      }

      const clampedValue = Math.max(0, Math.min(1, numValue));
      this.$emit('update:confidenceThreshold', clampedValue);
    },
    validateConfidence(value) {
      const numValue = parseFloat(value);
      if (isNaN(numValue)) {
        return '유효한 숫자를 입력하세요';
      }
      if (numValue < 0 || numValue > 1) {
        return '0과 1 사이의 값을 입력하세요';
      }
      return true;
    },
    resetToDefault() {
      this.$emit('update:confidenceThreshold', 0.5);
    }
  }
}
</script>

<style scoped>
.confidence-settings-section {
  width: 100%;
}

.confidence-card {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid #333 !important;
}

.confidence-control-group {
  width: 100%;
}

.confidence-slider-container {
  width: 100%;
}

.confidence-slider {
  width: 100%;
}

.confidence-label {
  color: #8f9bb3;
  font-size: 12px;
  min-width: 16px;
  text-align: center;
}

.confidence-input-container {
  width: 100%;
}

.confidence-input {
  width: 100%;
}

.confidence-display {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  padding: 8px;
  border: 1px solid #333;
}

.confidence-value-label {
  color: #8f9bb3;
  font-size: 12px;
  margin-right: 8px;
}

.confidence-value-number {
  color: #4f9cf5;
  font-weight: bold;
  font-size: 14px;
}

:deep(.confidence-input .v-field) {
  background-color: #2a2a2a !important;
}

:deep(.confidence-input .v-field__input) {
  color: #e0e0e0 !important;
}

:deep(.confidence-slider .v-slider-track__fill) {
  background-color: #4f9cf5 !important;
}

/* 슬라이더 thumb 크기 조정 */
:deep(.confidence-slider.small-thumb .v-slider-thumb) {
  background-color: #4f9cf5 !important;
  width: 12px !important;
  height: 12px !important;
}

:deep(.confidence-slider.small-thumb .v-slider-thumb__surface) {
  width: 12px !important;
  height: 12px !important;
}

/* 전역 Vuetify 슬라이더 스타일 오버라이드 */
.v-slider-thumb {
  --v-slider-thumb-size: 12px !important;
}

.confidence-slider.small-thumb .v-slider-thumb {
  --v-slider-thumb-size: 12px !important;
}
</style>
