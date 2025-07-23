<template>
  <v-dialog
    v-model="dialogVisible"
    max-width="600"
    class="delete-confirm-dialog"
    @keydown.esc="cancelDelete"
    persistent
  >
    <v-card>
      <v-card-title class="text-h6 d-flex align-center">
        <v-icon start color="red" size="28">mdi-delete-alert</v-icon>
        파일 삭제 확인
      </v-card-title>

      <v-card-text>
        <div class="mb-4">
          <p class="text-body-1 mb-3">
            다음 파일을 삭제하시겠습니까?
          </p>

          <div class="file-info-card mb-3">
            <div class="file-item">
              <div class="d-flex align-center mb-2">
                <v-icon color="blue" class="mr-2">mdi-image</v-icon>
                <span class="file-type-label">이미지 파일:</span>
              </div>
              <v-tooltip :text="filename" location="top">
                <template v-slot:activator="{ props }">
                  <div
                    class="file-name-container"
                    v-bind="props"
                  >
                    <span class="file-name">{{ filename }}</span>
                  </div>
                </template>
              </v-tooltip>
            </div>

            <v-divider class="my-3 border-opacity-25"></v-divider>

            <div class="file-item">
              <div class="d-flex align-center mb-2">
                <v-icon color="orange" class="mr-2">mdi-label</v-icon>
                <span class="file-type-label">라벨 파일:</span>
              </div>
              <v-tooltip :text="labelFilename" location="top">
                <template v-slot:activator="{ props }">
                  <div
                    class="file-name-container"
                    v-bind="props"
                  >
                    <span class="file-name">{{ labelFilename }}</span>
                  </div>
                </template>
              </v-tooltip>
            </div>
          </div>

          <v-alert
            type="warning"
            variant="tonal"
            class="mb-3"
            :icon="false"
          >
            <div class="d-flex align-center">
              <v-icon color="orange" class="mr-2">mdi-alert-circle</v-icon>
              <span class="text-body-2">
                이 작업은 되돌릴 수 없습니다. 신중하게 선택하세요.
              </span>
            </div>
          </v-alert>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          color="grey"
          variant="text"
          @click="cancelDelete"
          :disabled="isDeleting"
        >
          취소
        </v-btn>
        <v-btn
          color="red"
          variant="elevated"
          @click="confirmDelete"
          :loading="isDeleting"
          :disabled="isDeleting"
        >
          <v-icon start>mdi-delete</v-icon>
          삭제
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'DeleteConfirmDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    filename: {
      type: String,
      default: ''
    },
    isDeleting: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'confirm-delete', 'cancel-delete'],
  computed: {
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    },
    labelFilename() {
      if (!this.filename) return '';
      // 이미지 파일 확장자를 .txt로 변경
      const baseName = this.filename.substring(0, this.filename.lastIndexOf('.'));
      return `${baseName}.txt`;
    }
  },
  methods: {
    confirmDelete() {
      this.$emit('confirm-delete');
    },
    cancelDelete() {
      this.$emit('cancel-delete');
    }
  }
};
</script>

<style scoped>
:deep(.delete-confirm-dialog .v-card) {
  background-color: #1e1e1e;
  color: #e0e0e0;
  border: 1px solid #333;
}

:deep(.delete-confirm-dialog .v-card-title) {
  color: #fff;
  border-bottom: 1px solid #333;
  font-size: 18px;
  font-weight: 600;
}

:deep(.delete-confirm-dialog .v-card-text) {
  color: #e0e0e0;
}

.file-info-card {
  background-color: #2d2d2d;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #404040;
}

.file-item {
  position: relative;
}

.file-type-label {
  font-size: 14px;
  color: #b0b0b0;
  font-weight: 500;
}

.file-name-container {
  background-color: #383838;
  border-radius: 6px;
  padding: 10px 12px;
  border: 1px solid #505050;
  cursor: help;
  transition: all 0.2s ease;
  max-width: 100%;
}

.file-name-container:hover {
  background-color: #404040;
  border-color: #606060;
}

.file-name {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #fff;
  font-weight: 500;
  word-break: break-all;
  overflow-wrap: break-word;
  line-height: 1.4;
  display: block;
}

:deep(.v-alert) {
  background-color: rgba(255, 152, 0, 0.1) !important;
  border: 1px solid rgba(255, 152, 0, 0.3) !important;
}

:deep(.v-alert .v-alert__content) {
  color: #e0e0e0 !important;
}

:deep(.v-btn) {
  text-transform: none;
  font-weight: 500;
}

:deep(.v-btn--variant-elevated) {
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

:deep(.v-btn--variant-elevated:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
}

:deep(.v-divider) {
  border-color: #505050 !important;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  :deep(.delete-confirm-dialog .v-dialog) {
    margin: 16px;
  }

  .file-name {
    font-size: 12px;
  }

  .file-info-card {
    padding: 16px;
  }
}
</style>
