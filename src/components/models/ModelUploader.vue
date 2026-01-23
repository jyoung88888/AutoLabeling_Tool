<template>
  <div class="model-uploader">
    <v-card class="model-upload-card" color="#2a2a2a" elevation="0">
      <v-card-title class="text-subtitle-1 font-weight-bold pa-3 d-flex align-center ga-2">
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
            class="lucide lucide-file-up-icon lucide-file-up"
          >
            <path
              d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"
            />
            <path d="M14 2v5a1 1 0 0 0 1 1h5" />
            <path d="M12 12v6" />
            <path d="m15 15-3-3-3 3" />
          </svg>
        </div>

        모델 추가
      </v-card-title>

      <v-card-text class="pb-3 px-3 d-flex flex-column ga-2">
        <!-- 파일 선택 -->
        <!-- <v-file-input
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
        ></v-file-input> -->
        <v-file-upload
          v-model="selectedFile"
          accept=".pt,.pth,.onnx,.engine"
          label="모델 추가"
          class="dark-select"
          rounded="lg"
          density="compact"
          variant="compact"
          show-size
        >
          <template v-slot:icon>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="lucide lucide-file-up-icon lucide-file-up"
            >
              <path
                d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"
              />
              <path d="M14 2v5a1 1 0 0 0 1 1h5" />
              <path d="M12 12v6" />
              <path d="m15 15-3-3-3 3" />
            </svg>
          </template>
          <template v-slot:title>
            <div class="d-flex flex-column">
              <span class="text-body-2 text-left">
                <strong>드래그 앤 드롭</strong> 또는<br />
                <strong>클릭</strong>하여 모델 추가
              </span>
              <span class="text-caption text-grey">(.pt,.pth,.onnx,.engine)</span>
            </div>
          </template>
          <template v-slot:default>
            <v-file-item
              v-if="selectedFile"
              :file="selectedFile"
              :show-size="true"
              clearable
            ></v-file-item>
          </template>
        </v-file-upload>

        <!-- 업로드 버튼 -->
        <v-btn
          color="white"
          variant="tonal"
          :disabled="!canUpload"
          :loading="isUploading"
          @click="uploadModel"
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
            class="lucide lucide-plus-icon lucide-plus mr-2"
          >
            <path d="M5 12h14" />
            <path d="M12 5v14" />
          </svg>
          <span>{{ isUploading ? '모델 추가 중...' : '모델 추가' }}</span>
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
import { uploadModel } from '@/api/modelApi.js'

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
        (value) => {
          if (!value || !value.length) return true
          const file = Array.isArray(value) ? value[0] : value
          const allowedExtensions = ['.pt', '.pth', '.onnx', '.engine']
          const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
          return (
            allowedExtensions.includes(fileExtension) ||
            '지원되는 파일 형식: .pt, .pth, .onnx, .engine'
          )
        },
      ],
    }
  },
  computed: {
    canUpload() {
      return this.selectedFile && !this.isUploading
    },
    finalModelName() {
      // 업로드한 파일의 원본 파일명 사용 (확장자 제거)
      if (this.selectedFile) {
        const file = Array.isArray(this.selectedFile) ? this.selectedFile[0] : this.selectedFile
        return file.name.replace(/\.[^/.]+$/, '')
      }
      return ''
    },
  },
  methods: {
    async uploadModel() {
      if (!this.canUpload) return

      this.isUploading = true
      this.statusMessage = ''
      this.uploadSuccess = false

      try {
        const file = Array.isArray(this.selectedFile) ? this.selectedFile[0] : this.selectedFile

        // 기본 모델 타입을 'yolo'로 설정
        const result = await uploadModel(
          file,
          'yolo', // 기본 모델 타입
          this.finalModelName,
        )

        this.statusMessage = result.message || '모델이 성공적으로 업로드되었습니다.'
        this.uploadSuccess = true

        // 폼 초기화
        this.selectedFile = null

        // 부모 컴포넌트에 업로드 성공 알림
        this.$emit('upload-success', {
          modelType: 'yolo',
          modelName: result.model_name,
          filePath: result.file_path,
        })
      } catch (error) {
        console.error('모델 업로드 실패:', error)
        this.statusMessage =
          error.response?.data?.detail || error.message || '모델 업로드에 실패했습니다.'
        this.uploadSuccess = false
      } finally {
        this.isUploading = false
      }
    },

    clearStatus() {
      this.statusMessage = ''
      this.uploadSuccess = false
    },
  },
}
</script>

<style scoped>
.model-uploader {
  width: 100%;
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

.dark-select :deep(.v-file-item .v-file-item__name) {
  font-weight: 700 !important;
}

/* 파일 아이템 영역 내부의 title 숨김 */
.dark-select :deep(.v-file-upload__files .v-file-upload__title) {
  display: none !important;
}

.dark-select :deep(.v-file-upload__files .text-body-2) {
  display: none !important;
}

.dark-select :deep(.v-file-upload__files .text-caption) {
  display: none !important;
}
</style>
