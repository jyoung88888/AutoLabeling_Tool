<template>
  <div>
    <v-list-subheader class="text-subtitle-1 font-weight-bold text-wrap pa-0" style="color: #e0e0e0;">
      <div class="mb-2 mt-4 px-2">📷 이미지 선택</div>
    </v-list-subheader>

    <v-list-item>
      <ImageUploader
        :uploaded-files="uploadedImages"
        @file-upload="$emit('fileUpload', $event)"
        @clear-files="$emit('clearFiles')"
        class="my-2"
      />
    </v-list-item>

    <v-list-item v-if="imageStatusMessage && !isClassSelectionMessage">
      <v-alert
        :type="imageStatusSuccess ? 'success' : 'error'"
        variant="tonal"
        density="compact"
        class="mb-2"
      >
        {{ imageStatusMessage }}
      </v-alert>
    </v-list-item>
  </div>
</template>

<script>
import ImageUploader from '../images/ImageUploader.vue'

export default {
  name: 'ImageSelectionSection',
  components: {
    ImageUploader
  },
  props: {
    uploadedImages: {
      type: Array,
      default: () => []
    },
    imageStatusMessage: {
      type: String,
      default: ''
    },
    imageStatusSuccess: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    isClassSelectionMessage() {
      // 클래스 선택과 관련된 메시지인지 확인
      return this.imageStatusMessage && (
        this.imageStatusMessage.includes('클래스가 선택되었습니다') ||
        this.imageStatusMessage.includes('클래스(') && this.imageStatusMessage.includes('개)가 선택되었습니다')
      )
    }
  },
  emits: [
    'fileUpload',
    'clearFiles'
  ]
}
</script>
