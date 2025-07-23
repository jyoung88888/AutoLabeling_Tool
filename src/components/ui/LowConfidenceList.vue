<template>
  <div class="low-confidence-list-container">
    <div class="low-confidence-header pa-2">
      <v-icon icon="mdi-alert-triangle" color="#f0ad4e" size="small" class="mr-1"></v-icon>
      <span class="text-subtitle-2">저신뢰도 이미지 목록</span>
    </div>
    <div v-if="lowConfidenceImages.length > 0" class="low-confidence-list">
      <v-list density="compact" bg-color="#242424" color="#e0e0e0" class="pa-0">
        <v-list-item
          v-for="(image, index) in lowConfidenceImages"
          :key="index"
          @click="handleImageClick(image.index)"
          class="low-confidence-item pa-2"
          density="compact"
          :active="false"
          :hover="true"
          rounded="0"
        >
          <template v-slot:prepend>
            <v-avatar
              size="22"
              color="#f0ad4e"
              class="mr-2 confidence-count-avatar"
            >
              <span class="text-caption font-weight-bold">{{ image.count }}</span>
            </v-avatar>
          </template>

          <v-list-item-title class="text-body-2">
            {{ image.filename }}
          </v-list-item-title>

          <v-list-item-subtitle class="text-caption">
            <span class="low-confidence-details">{{ image.details || '신뢰도 정보 없음' }}</span>
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </div>
    <div v-else class="no-low-confidence">
      저신뢰도 이미지가 없습니다.
    </div>
  </div>
</template>

<script>
export default {
  props: {
    lowConfidenceImages: {
      type: Array,
      required: true
    }
  },
  methods: {
    unformattedDetails(details) {
      // HTML 태그 제거하고 일반 텍스트로 변환
      return details ? details.replace(/<br>/g, ', ') : '';
    },
    handleImageClick(index) {
      console.log('=== 저신뢰도 이미지 클릭 ===');
      console.log('클릭된 인덱스:', index);
      console.log('타입 확인:', typeof index, 'isNaN:', isNaN(index));

      // 유효한 인덱스인지 확인
      if (typeof index !== 'number' || isNaN(index) || index <= 0) {
        console.error('유효하지 않은 이미지 인덱스:', index);
        return;
      }

      // 클릭된 이미지 정보 찾기
      const clickedImage = this.lowConfidenceImages.find(img => img.index === index);
      if (clickedImage) {
        console.log('클릭된 이미지 정보:');
        console.log(`  파일명: "${clickedImage.filename}"`);
        console.log(`  인덱스: ${clickedImage.index}`);
        console.log(`  저신뢰도 객체 수: ${clickedImage.count}`);
        console.log(`  세부정보: ${clickedImage.details}`);
      } else {
        console.error('클릭된 인덱스에 해당하는 이미지 정보를 찾을 수 없음:', index);
        console.error('현재 저신뢰도 이미지 목록:');
        this.lowConfidenceImages.forEach((img, i) => {
          console.error(`  [${i}]: "${img.filename}" => 인덱스 ${img.index}`);
        });
      }

      // 이벤트 전파 차단을 최소화하고, 즉시 부모 컴포넌트에 이벤트 전달
      console.log('부모 컴포넌트에 go-to-image 이벤트 전달:', index);
      this.$emit('go-to-image', index);
    }
  }
};
</script>

<style scoped>
.low-confidence-list-container {
  width: 100%;
  background-color: #242424;
  border: 1px solid #333;
  border-radius: 4px;
  overflow: hidden;
}

.low-confidence-header {
  display: flex;
  align-items: center;
  background-color: #333;
  border-bottom: 1px solid #444;
  color: #e0e0e0;
}

.low-confidence-list {
  width: 100%;
  max-height: 250px;
  overflow-y: auto;
}

.low-confidence-item {
  border-bottom: 1px solid #333;
  transition: background-color 0.2s ease;
}

.low-confidence-item:hover {
  background-color: rgba(240, 173, 78, 0.1) !important;
  cursor: pointer;
}

.low-confidence-item:last-child {
  border-bottom: none;
}

.confidence-count-avatar {
  color: #333 !important;
  font-size: 12px !important;
}

.no-low-confidence {
  padding: 16px;
  text-align: center;
  color: #a0a0a0;
  font-style: italic;
}

:deep(.v-list-item-subtitle) {
  opacity: 0.8;
  color: #aaa !important;
  font-size: 0.8rem !important;
  margin-top: 2px;
}

.low-confidence-details {
  color: #aaa;
}
</style>
