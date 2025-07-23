<template>
  <div class="model-uploader">
    <v-card class="model-upload-card" color="#2a2a2a">
      <v-card-title class="text-subtitle-1 font-weight-bold pa-3" style="color: #e0e0e0;">
        <v-icon icon="mdi-cloud-upload" size="small" color="#4f9cf5" class="mr-2"></v-icon>
        모델 업로드
      </v-card-title>

      <v-card-text class="pa-3">
        <!-- 파일 선택 -->
        <v-file-input
          v-model="selectedFile"
          label="모델 파일 선택"
          variant="outlined"
          density="compact"
          hide-details
          class="mb-3 dark-select"
          prepend-inner-icon="mdi-file"
          base-color="#e0e0e0"
          accept=".pt,.pth,.onnx,.engine"
          :rules="fileRules"
        ></v-file-input>

        <!-- 업로드 버튼 -->
        <v-btn
          block
          color="#4f9cf5"
          size="small"
          :disabled="!canUpload"
          :loading="isUploading"
          @click="uploadModel"
          prepend-icon="mdi-upload"
          style="color: #fff;"
        >
          {{ isUploading ? '업로드 중...' : '모델 업로드' }}
        </v-btn>

        <!-- 상태 메시지 -->
        <v-alert
          v-if="statusMessage"
          :type="uploadSuccess ? 'success' : 'error'"
          variant="tonal"
          density="compact"
          class="mt-3"
          closable
          @click:close="clearStatus"
        >
          {{ statusMessage }}
        </v-alert>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { uploadModel } from '@/api/modelApi.js';

export default {
  name: 'ModelUploader',
  emits: ['upload-success'],
  data() {
    return {
      selectedFile: null,
      isUploading: false,
      statusMessage: '',
      uploadSuccess: false,
      fileRules: [
        value => {
          if (!value || !value.length) return true;
          const file = Array.isArray(value) ? value[0] : value;
          const allowedExtensions = ['.pt', '.pth', '.onnx', '.engine'];
          const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
          return allowedExtensions.includes(fileExtension) || '지원되는 파일 형식: .pt, .pth, .onnx, .engine';
        }
      ]
    };
  },
  computed: {
    canUpload() {
      return this.selectedFile && !this.isUploading;
    },
    finalModelName() {
      // 업로드한 파일의 원본 파일명 사용 (확장자 제거)
      if (this.selectedFile) {
        const file = Array.isArray(this.selectedFile) ? this.selectedFile[0] : this.selectedFile;
        return file.name.replace(/\.[^/.]+$/, '');
      }
      return '';
    }
  },
  methods: {
    async uploadModel() {
      if (!this.canUpload) return;

      this.isUploading = true;
      this.statusMessage = '';
      this.uploadSuccess = false;

      try {
        const file = Array.isArray(this.selectedFile) ? this.selectedFile[0] : this.selectedFile;

        // 기본 모델 타입을 'yolo'로 설정
        const result = await uploadModel(
          file,
          'yolo', // 기본 모델 타입
          this.finalModelName
        );

        this.statusMessage = result.message || '모델이 성공적으로 업로드되었습니다.';
        this.uploadSuccess = true;

        // 폼 초기화
        this.selectedFile = null;

        // 부모 컴포넌트에 업로드 성공 알림
        this.$emit('upload-success', {
          modelType: 'yolo',
          modelName: result.model_name,
          filePath: result.file_path
        });

      } catch (error) {
        console.error('모델 업로드 실패:', error);
        this.statusMessage = error.response?.data?.detail || error.message || '모델 업로드에 실패했습니다.';
        this.uploadSuccess = false;
      } finally {
        this.isUploading = false;
      }
    },

    clearStatus() {
      this.statusMessage = '';
      this.uploadSuccess = false;
    }
  }
};
</script>

<style scoped>
.model-uploader {
  width: 100%;
}

.model-upload-card {
  border: 1px solid #333;
  border-radius: 8px;
}

.dark-select :deep(.v-field) {
  border: none !important;
  background-color: #333 !important;
}

.dark-select :deep(.v-field__outline) {
  color: #555 !important;
  opacity: 1 !important;
}

.dark-select :deep(.v-field__input) {
  color: #e0e0e0 !important;
}

.dark-select :deep(.v-select__selection-text) {
  color: #e0e0e0 !important;
}

.dark-select :deep(.v-field__prepend-inner) {
  color: #4f9cf5 !important;
}

.dark-select :deep(.v-field__append-inner) {
  color: #e0e0e0 !important;
}

.dark-select :deep(.v-label) {
  color: #b0b0b0 !important;
}

.dark-select :deep(.v-field--focused .v-field__outline) {
  color: #4f9cf5 !important;
}
</style>
