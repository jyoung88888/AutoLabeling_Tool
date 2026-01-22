<template>
  <div>
    <div class="mb-2 mt-2 px-2 d-flex align-center">
      <v-icon icon="mdi-alert-circle" size="small" color="#f0ad4e" class="mr-2"></v-icon>
      저신뢰도 이미지 목록
    </div>

    <div class="px-4">
      <v-card
        class="low-confidence-card pa-0 mb-2"
        variant="outlined"
        color="#252525"
        border
        v-if="lowConfidenceImages.length > 0"
      >
        <LowConfidenceList
          :low-confidence-images="lowConfidenceImages"
          @go-to-image="$emit('goToImage', $event)"
        />
      </v-card>
      <v-card
        v-else
        class="low-confidence-empty pa-3 mb-2"
        variant="outlined"
        color="#252525"
        border
      >
        <div class="text-center py-2" style="color: #a0a0a0">
          <v-icon icon="mdi-check-circle" color="#4caf50" class="mb-1"></v-icon>
          <div>저신뢰도 이미지가 없습니다</div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script>
import LowConfidenceList from '../ui/LowConfidenceList.vue'

export default {
  name: 'LowConfidenceSection',
  components: {
    LowConfidenceList,
  },
  props: {
    lowConfidenceImages: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['goToImage'],
}
</script>

<style scoped>
.low-confidence-card {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid #333 !important;
}

.low-confidence-empty {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid #333 !important;
}
</style>
