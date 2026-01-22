<template>
  <div class="px-2 my-4">
    <div class="d-flex justify-space-between align-center">
      <div class="font-weight-bold mb-3 d-flex align-center ga-2">
        <div class="bg-grey-darken-3 bg-opacity-30 text-purple pa-1 rounded d-flex">
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
        클래스 선택
      </div>
      <div class="d-flex align-center justify-space-between">
        <v-btn
          size="x-small"
          variant="text"
          color="purple"
          @click="handleToggleAllClasses"
          title="모든 클래스 선택/해제"
        >
          {{ selectAllClasses ? '모두 해제' : '모두 선택' }}
        </v-btn>
      </div>
    </div>

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
      <div class="classes-list" style="max-height: 150px; overflow-y: auto">
        <v-checkbox
          v-for="(className, index) in availableClasses"
          :key="index"
          :model-value="selectedClasses[className]"
          @update:model-value="updateSelectedClass(className, $event)"
          :label="`${index}: ${className}`"
          hide-details
          density="compact"
          color="purple"
          class="class-checkbox ml-2"
          :title="`YOLO 순서 ${index}: ${className} (프로젝트 저장 시와 동일)`"
        ></v-checkbox>
      </div>
      <v-btn
        block
        class="mt-2"
        variant="tonal"
        @click="$emit('applyClassSelection')"
        :disabled="!(selectAllClasses || Object.values(selectedClasses).some((val) => val))"
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
          class="lucide lucide-check-icon lucide-check"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
        클래스 선택 적용
      </v-btn>

      <!-- 클래스 선택 적용 후 메시지 (버튼 바로 밑에 표시) -->
      <v-alert
        v-if="classSelectionApplied && classSelectionMessage"
        type="success"
        variant="tonal"
        density="compact"
        class="mt-2 mb-2 selected-classes-alert"
        icon="mdi-tag-multiple"
      >
        {{ classSelectionMessage }}
      </v-alert>
    </div>
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
  },
  emits: [
    'update:selectedClasses',
    'update:selectAllClasses',
    'toggleAllClasses',
    'selectAllClassesChanged',
    'checkSelectedClasses',
    'applyClassSelection',
    'dismissClassChangeAlert',
  ],
  methods: {
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
}

.class-checkbox {
  margin-bottom: 4px;
}

.class-change-alert {
  font-size: 12px;
}

.selected-classes-alert {
  font-size: 12px;
}

:deep(.v-checkbox .v-selection-control__input) {
  color: #4f9cf5;
}

:deep(.v-checkbox .v-label) {
  color: #e0e0e0;
  font-size: 14px;
}
</style>
