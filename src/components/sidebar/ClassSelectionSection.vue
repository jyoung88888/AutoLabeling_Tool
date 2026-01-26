<template>
  <div class="px-2 my-4">
    <v-card class="model-upload-card" color="#2a2a2a" elevation="0">
      <v-card-title
        class="text-subtitle-1 font-weight-bold pa-3 d-flex align-center justify-space-between"
      >
        <div class="font-weight-bold d-flex align-center ga-2">
          <div class="bg-grey-darken-3 bg-opacity-30 text-light-blue-lighten-2 pa-1 rounded d-flex">
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
              class="lucide lucide-component-icon lucide-component"
            >
              <path
                d="M15.536 11.293a1 1 0 0 0 0 1.414l2.376 2.377a1 1 0 0 0 1.414 0l2.377-2.377a1 1 0 0 0 0-1.414l-2.377-2.377a1 1 0 0 0-1.414 0z"
              />
              <path
                d="M2.297 11.293a1 1 0 0 0 0 1.414l2.377 2.377a1 1 0 0 0 1.414 0l2.377-2.377a1 1 0 0 0 0-1.414L6.088 8.916a1 1 0 0 0-1.414 0z"
              />
              <path
                d="M8.916 17.912a1 1 0 0 0 0 1.415l2.377 2.376a1 1 0 0 0 1.414 0l2.377-2.376a1 1 0 0 0 0-1.415l-2.377-2.376a1 1 0 0 0-1.414 0z"
              />
              <path
                d="M8.916 4.674a1 1 0 0 0 0 1.414l2.377 2.376a1 1 0 0 0 1.414 0l2.377-2.376a1 1 0 0 0 0-1.414l-2.377-2.377a1 1 0 0 0-1.414 0z"
              />
            </svg>
          </div>
          클래스 및 신뢰도 설정
        </div>
        <v-btn
          size="x-small"
          variant="text"
          color="light-blue-lighten-2"
          @click="handleToggleAllClasses"
          title="모든 클래스 선택/해제"
        >
          <svg
            v-if="selectAllClasses"
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-1"
          >
            <rect width="18" height="18" x="3" y="3" rx="2" />
          </svg>
          <svg
            v-else
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="mr-1"
          >
            <rect width="18" height="18" x="3" y="3" rx="2" />
            <path d="m9 12 2 2 4-4" />
          </svg>
          {{ selectAllClasses ? '모두 해제' : '모두 선택' }}
        </v-btn>
      </v-card-title>
      <v-card-text>
        <div class="class-selection-section">
          <v-alert
            v-if="showClassChangeAlert"
            density="compact"
            type="info"
            variant="tonal"
            class="mb-2 class-change-alert"
            border="start"
            closable
            @click:close="$emit('dismissClassChangeAlert')"
          >
            {{ classChangeMessage }}
          </v-alert>
          <div class="classes-list">
            <div
              v-for="(className, index) in availableClasses"
              :key="index"
              class="custom-checkbox"
              @click="updateSelectedClass(className, !selectedClasses[className])"
              :title="`YOLO 순서 ${index}: ${className} (프로젝트 저장 시와 동일)`"
            >
              <svg
                v-if="selectedClasses[className]"
                class="checkbox-icon checked"
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <rect width="18" height="18" x="3" y="3" rx="2" />
                <path d="m9 12 2 2 4-4" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="checkbox-icon unchecked"
              >
                <rect width="18" height="18" x="3" y="3" rx="2" />
              </svg>
              <span class="checkbox-label">{{ index }}: {{ className }}</span>
            </div>
          </div>
          <v-btn
            block
            class="mt-2"
            variant="tonal"
            @click="handleApplyClassSelection"
            :disabled="
              !(selectAllClasses || Object.values(selectedClasses).some((val) => val)) ||
              classSelectionApplied
            "
          >
            <svg
              v-if="classSelectionApplied"
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
            {{
              classSelectionApplied ? `클래스 적용 완료 (${selectedClassCount}개)` : '클래스 적용'
            }}
          </v-btn>

          <!-- 신뢰도 설정 -->
          <div class="mt-3">
            <v-subheader class="text-caption px-0" style="color: #b0b0b0">
              최소 신뢰도 임계값: {{ confidenceThreshold }}
            </v-subheader>
            <v-slider
              :model-value="confidenceThreshold"
              @update:model-value="$emit('update:confidenceThreshold', $event)"
              :min="0"
              :max="1"
              :step="0.01"
              color="light-blue-lighten-2"
              thumb-label
              hide-details
              density="compact"
            ></v-slider>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'ClassSelectionSection',
  props: {
    availableClasses: {
      type: Array,
      default: () => [],
    },
    selectedClasses: {
      type: Object,
      default: () => ({}),
    },
    selectAllClasses: {
      type: Boolean,
      default: false,
    },
    allClassesSelected: {
      type: Boolean,
      default: false,
    },
    showClassChangeAlert: {
      type: Boolean,
      default: false,
    },
    classChangeMessage: {
      type: String,
      default: '',
    },
    selectedClassesInfo: {
      type: String,
      default: '',
    },
    classSelectionApplied: {
      type: Boolean,
      default: false,
    },
    classSelectionMessage: {
      type: String,
      default: '',
    },
    confidenceThreshold: {
      type: Number,
      default: 0.5,
    },
  },
  emits: [
    'update:selectedClasses',
    'update:selectAllClasses',
    'update:confidenceThreshold',
    'toggleAllClasses',
    'selectAllClassesChanged',
    'checkSelectedClasses',
    'applyClassSelection',
    'dismissClassChangeAlert',
    'selectionChanged',
  ],
  data() {
    return {
      lastAppliedSelection: null,
    }
  },
  computed: {
    selectedClassCount() {
      if (this.selectAllClasses) {
        return this.availableClasses.length
      }
      return Object.values(this.selectedClasses).filter((val) => val).length
    },
  },
  watch: {
    selectedClasses: {
      deep: true,
      handler() {
        // 선택이 변경되면 적용 상태를 확인
        if (this.classSelectionApplied && this.hasSelectionChanged()) {
          console.log('🔄 selectedClasses 변경 감지 - selectionChanged 이벤트 발생')
          this.$emit('selectionChanged')
        }
      },
    },
    selectAllClasses() {
      // selectAll 토글 시에도 확인
      if (this.classSelectionApplied && this.hasSelectionChanged()) {
        console.log('🔄 selectAllClasses 변경 감지 - selectionChanged 이벤트 발생')
        this.$emit('selectionChanged')
      }
    },
    classSelectionApplied(newVal) {
      console.log('📊 classSelectionApplied 상태 변경:', newVal)
    },
  },
  methods: {
    hasSelectionChanged() {
      if (!this.lastAppliedSelection) return false

      // 현재 선택과 마지막 적용된 선택을 비교
      const currentSelection = JSON.stringify({
        selectAll: this.selectAllClasses,
        selected: this.selectedClasses,
      })
      return currentSelection !== this.lastAppliedSelection
    },
    saveCurrentSelection() {
      // 현재 선택 상태를 저장
      this.lastAppliedSelection = JSON.stringify({
        selectAll: this.selectAllClasses,
        selected: this.selectedClasses,
      })
    },
    updateSelectedClass(className, value) {
      const newSelectedClasses = { ...this.selectedClasses }
      newSelectedClasses[className] = value
      this.$emit('update:selectedClasses', newSelectedClasses)

      // 개별 클래스 선택/해제 후 checkSelectedClasses 호출
      this.$emit('checkSelectedClasses')
    },
    handleSelectAllChange(value) {
      // 모든 클래스 체크박스 변경

      // 먼저 selectAllClasses 상태 업데이트
      this.$emit('update:selectAllClasses', value)

      // 그 다음 모든 개별 클래스들의 선택 상태 업데이트
      const newSelectedClasses = {}
      this.availableClasses.forEach((className) => {
        newSelectedClasses[className] = value
      })
      this.$emit('update:selectedClasses', newSelectedClasses)

      // selectAllClassesChanged 이벤트 발생
      this.$emit('selectAllClassesChanged', value)
    },
    handleToggleAllClasses() {
      console.log('모든 클래스 토글 버튼 클릭')
      const newValue = !this.selectAllClasses
      this.handleSelectAllChange(newValue)
    },
    handleApplyClassSelection() {
      console.log('✅ handleApplyClassSelection 실행')
      console.log('현재 상태:', {
        selectAllClasses: this.selectAllClasses,
        selectedCount: this.selectedClassCount,
        classSelectionApplied: this.classSelectionApplied,
      })
      // 현재 선택 상태 저장
      this.saveCurrentSelection()
      console.log('저장된 선택 상태:', this.lastAppliedSelection)
      // 적용 이벤트 발생
      this.$emit('applyClassSelection')
    },
  },
}
</script>

<style scoped>
.class-selection-section {
  width: 100%;
}

.classes-list {
  border: 1px solid #333;
  border-radius: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.02);
  max-height: 200px;
  overflow-y: auto;
}

.custom-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
  user-select: none;
}

.custom-checkbox:hover {
  background: rgba(255, 255, 255, 0.05);
}

.checkbox-icon {
  flex-shrink: 0;
  transition: all 0.2s;
}

.checkbox-icon.checked {
  color: #81d4fa;
}

.checkbox-icon.unchecked {
  color: #666;
}

.custom-checkbox:hover .checkbox-icon.unchecked {
  color: #999;
}

.checkbox-label {
  color: #e0e0e0;
  font-size: 14px;
  line-height: 1.2;
}

.class-change-alert {
  font-size: 12px;
}

.selected-classes-alert {
  font-size: 12px;
}
</style>
