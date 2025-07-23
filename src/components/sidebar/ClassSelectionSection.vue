<template>
  <div>
    <v-list-subheader class="text-subtitle-1 font-weight-bold text-wrap pa-0" style="color: #e0e0e0;">
      <div class="mb-2 mt-4 px-2">🏷️ 클래스 선택</div>
    </v-list-subheader>

    <v-list-item>
      <div class="class-selection-section">
        <div class="d-flex align-center justify-space-between mb-2">
          <v-btn
            size="x-small"
            variant="text"
            density="compact"
            color="#4f9cf5"
            @click="handleToggleAllClasses"
            title="모든 클래스 선택/해제"
          >
            {{ selectAllClasses ? '모두 해제' : '모두 선택' }}
          </v-btn>
        </div>
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
        <div class="classes-list" style="max-height: 150px; overflow-y: auto;">
          <v-checkbox
            :model-value="selectAllClasses"
            @update:model-value="handleSelectAllChange"
            label="모든 클래스"
            color="#4f9cf5"
            hide-details
            density="compact"
            class="class-checkbox"
          ></v-checkbox>
          <v-checkbox
            v-for="(className, index) in availableClasses"
            :key="index"
            :model-value="selectedClasses[className]"
            @update:model-value="updateSelectedClass(className, $event)"
            :label="`${index}: ${className}`"
            color="#4f9cf5"
            hide-details
            density="compact"
            class="class-checkbox ml-2"
            :title="`YOLO 순서 ${index}: ${className} (프로젝트 저장 시와 동일)`"
          ></v-checkbox>
        </div>
        <v-btn
          size="small"
          block
          color="#4f9cf5"
          class="mt-2"
          prepend-icon="mdi-check"
          @click="$emit('applyClassSelection')"
          :disabled="!(selectAllClasses || Object.values(selectedClasses).some(val => val))"
        >
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
    </v-list-item>
  </div>
</template>

<script>
export default {
  name: 'ClassSelectionSection',
  props: {
    availableClasses: {
      type: Array,
      default: () => []
    },
    selectedClasses: {
      type: Object,
      default: () => ({})
    },
    selectAllClasses: {
      type: Boolean,
      default: false
    },
    allClassesSelected: {
      type: Boolean,
      default: false
    },
    showClassChangeAlert: {
      type: Boolean,
      default: false
    },
    classChangeMessage: {
      type: String,
      default: ''
    },
    selectedClassesInfo: {
      type: String,
      default: ''
    },
    classSelectionApplied: {
      type: Boolean,
      default: false
    },
    classSelectionMessage: {
      type: String,
      default: ''
    }
  },
  emits: [
    'update:selectedClasses',
    'update:selectAllClasses',
    'toggleAllClasses',
    'selectAllClassesChanged',
    'checkSelectedClasses',
    'applyClassSelection',
    'dismissClassChangeAlert'
  ],
  methods: {
    updateSelectedClass(className, value) {
      const newSelectedClasses = { ...this.selectedClasses };
      newSelectedClasses[className] = value;
      this.$emit('update:selectedClasses', newSelectedClasses);

      // 개별 클래스 선택/해제 후 checkSelectedClasses 호출
      this.$emit('checkSelectedClasses');
    },
        handleSelectAllChange(value) {
      // 모든 클래스 체크박스 변경

      // 먼저 selectAllClasses 상태 업데이트
      this.$emit('update:selectAllClasses', value);

      // 그 다음 모든 개별 클래스들의 선택 상태 업데이트
      const newSelectedClasses = {};
      this.availableClasses.forEach(className => {
        newSelectedClasses[className] = value;
      });
      this.$emit('update:selectedClasses', newSelectedClasses);

      // selectAllClassesChanged 이벤트 발생
      this.$emit('selectAllClassesChanged', value);
    },
    handleToggleAllClasses() {
      console.log('모든 클래스 토글 버튼 클릭');
      const newValue = !this.selectAllClasses;
      this.handleSelectAllChange(newValue);
    }
  }
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
