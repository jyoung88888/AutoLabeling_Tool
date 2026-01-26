<template>
  <div>
    <v-btn block variant="tonal" @click="triggerFileInput">
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
        class="lucide lucide-file-image-icon lucide-file-image mr-2"
      >
        <path
          d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"
        />
        <path d="M14 2v5a1 1 0 0 0 1 1h5" />
        <circle cx="10" cy="12" r="2" />
        <path d="m20 17-1.296-1.296a2.41 2.41 0 0 0-3.408 0L9 22" />
      </svg>
      파일 선택 (JPG, PNG)
    </v-btn>
    <input
      ref="fileInput"
      type="file"
      accept=".jpg,.jpeg,.png"
      multiple
      @change="handleFileInput"
      style="display: none"
    />

    <div v-if="uploadedFiles.length > 0" class="uploaded-files my-2">
      <div class="file-header d-flex align-center justify-space-between">
        <div class="text-subtitle-2" style="color: #e0e0e0">
          업로드된 파일 ({{ uploadedFiles.length }}개)
        </div>
        <v-btn
          icon="mdi-close"
          size="x-small"
          variant="text"
          color="#e0e0e0"
          @click="$emit('clear-files')"
        ></v-btn>
      </div>
      <div class="file-list-container">
        <v-list dense class="file-list" bg-color="#333" color="#e0e0e0">
          <v-list-item
            v-for="file in uploadedFiles"
            :key="file.name"
            class="file-item pa-1"
            density="compact"
          >
            <template v-slot:prepend>
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
                class="lucide lucide-image-icon lucide-image"
              >
                <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
                <circle cx="9" cy="9" r="2" />
                <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
              </svg>
            </template>
            <v-list-item-title class="text-body-2">{{ file.name }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    uploadedFiles: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['file-upload', 'clear-files'],
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click()
    },

    handleFileInput(event) {
      if (event.target.files) {
        this.$emit('file-upload', event)
      }
    },
  },
}
</script>

<style scoped>
.file-header {
  padding: 8px;
  border-bottom: 1px solid #444;
}

.file-list-container {
  max-height: 150px;
  overflow-y: auto;
  border-radius: 0 0 4px 4px;
}

.file-list {
  width: 100%;
  padding: 0;
}

.file-item {
  border-bottom: 1px solid #444;
}

.file-item:last-child {
  border-bottom: none;
}

/* 다크모드에서 항목 텍스트 색상 수정 */
:deep(.v-list-item-title) {
  color: #e0e0e0 !important;
}

:deep(.v-field__input) {
  color: #e0e0e0 !important;
}

:deep(.v-field__prepend-inner) .v-icon {
  color: #e0e0e0 !important;
}

:deep(.v-field__append-inner) {
  color: #e0e0e0 !important;
}

:deep(.v-field) {
  color: #e0e0e0 !important;
}

.uploaded-files {
  background-color: #333;
  border-radius: 4px;
  border: 1px solid #444;
}
</style>
