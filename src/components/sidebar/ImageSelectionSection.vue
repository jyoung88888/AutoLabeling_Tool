<template>
  <div class="px-2 my-4">
    <div class="font-weight-bold mb-3 d-flex align-center ga-2">
      <div class="bg-grey-darken-3 bg-opacity-30 text-light-green pa-1 rounded d-flex">
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
          class="lucide lucide-image-icon lucide-image"
        >
          <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
          <circle cx="9" cy="9" r="2" />
          <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
        </svg>
      </div>
      이미지 선택 및 라벨링 시작
    </div>
    <ImageUploader
      :uploaded-files="uploadedImages"
      @file-upload="$emit('fileUpload', $event)"
      @clear-files="$emit('clearFiles')"
      class="my-2"
    />

    <template v-if="imageStatusMessage && !isClassSelectionMessage">
      <v-alert
        :type="imageStatusSuccess ? 'success' : 'error'"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        {{ imageStatusMessage }}
      </v-alert>
    </template>
  </div>
</template>

<script>
import ImageUploader from '../images/ImageUploader.vue'

export default {
  name: 'ImageSelectionSection',
  components: {
    ImageUploader,
  },
  props: {
    uploadedImages: {
      type: Array,
      default: () => [],
    },
    imageStatusMessage: {
      type: String,
      default: '',
    },
    imageStatusSuccess: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    isClassSelectionMessage() {
      // 클래스 선택과 관련된 메시지인지 확인
      return (
        this.imageStatusMessage &&
        (this.imageStatusMessage.includes('클래스가 선택되었습니다') ||
          (this.imageStatusMessage.includes('클래스(') &&
            this.imageStatusMessage.includes('개)가 선택되었습니다')))
      )
    },
  },
  emits: ['fileUpload', 'clearFiles'],
}
</script>
