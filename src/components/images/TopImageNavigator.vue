<template>
  <div class="top-image-navigator">
    <div class="navigator-container">
      <!-- 왼쪽 영역: 이미지 네비게이션 -->
      <div class="nav-section">
        <v-btn
          icon="mdi-chevron-left"
          variant="text"
          color="#3982d4"
          @click="$emit('prev')"
          :disabled="currentIndex <= 1"
          size="small"
          class="nav-btn"
        ></v-btn>

        <div class="image-counter-section">
          <div class="image-counter-display">
            <span
              v-if="!isEditing"
              class="index-display clickable"
              @click="startEditing"
              :title="'클릭하여 이미지 번호 입력'"
            >{{ currentIndex }}</span>
            <input
              v-else
              ref="indexInput"
              v-model="editingValue"
              @blur="finishEditing"
              @keydown.enter="finishEditing"
              @keydown.esc="cancelEditing"
              class="index-input"
              type="number"
              :min="1"
              :max="totalImages"
            />
            <span class="separator">/</span>
            <span class="total-count">{{ totalImages }}</span>
          </div>
        </div>

        <v-btn
          icon="mdi-chevron-right"
          variant="text"
          color="#3982d4"
          @click="$emit('next')"
          :disabled="currentIndex >= totalImages"
          size="small"
          class="nav-btn"
        ></v-btn>
      </div>

      <!-- 중앙 영역: 진행 바 -->
      <div class="center-section">
        <div class="progress-bar-container">
          <div
            class="progress-bar"
            @click="handleProgressBarClick"
            @mousedown="handleProgressBarMouseDown"
            ref="progressBar"
          >
            <div
              class="progress-fill"
              :style="{ width: progressPercentage + '%' }"
            ></div>
            <!-- 현재 위치 표시 마커 -->
            <div
              class="progress-marker"
              :class="{ 'dragging': isDragging }"
              :style="{ left: progressPercentage + '%' }"
              @mousedown="handleMarkerMouseDown"
            >
              <span class="marker-tooltip">{{ currentIndex }}</span>
            </div>
          </div>
          <div class="progress-text">{{ Math.round(progressPercentage) }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TopImageNavigator',
  data() {
    return {
      isEditing: false,
      editingValue: '',
      isDragging: false,
      dragStartX: 0
    };
  },
  props: {
    currentIndex: {
      type: Number,
      required: true,
      validator(value) {
        const isValid = value >= 1;
        if (!isValid) {
          console.error('TopImageNavigator: currentIndex는 1 이상이어야 합니다:', value);
        }
        return isValid;
      }
    },
    totalImages: {
      type: Number,
      required: true,
      validator(value) {
        const isValid = value >= 0;
        if (!isValid) {
          console.error('TopImageNavigator: totalImages는 0 이상이어야 합니다:', value);
        }
        return isValid;
      }
    }
  },
  computed: {
    progressPercentage() {
      if (this.totalImages === 0) {
        return 0;
      }

      // 정확한 진행률 계산: 현재 인덱스 기준으로 100% 달성이 가능하도록
      const percentage = Math.min((this.currentIndex / this.totalImages) * 100, 100);

      // 마지막 이미지일 때 100% 보장
      if (this.currentIndex === this.totalImages) {
        return 100;
      }

      return Math.round(percentage * 10) / 10; // 소수점 1자리까지 정확하게
    }
  },
  methods: {
    // 기본 네비게이션 이벤트만 전달
    prevImage() {
      if (this.currentIndex > 1) {
        this.$emit('prev');
      }
    },
    nextImage() {
      if (this.currentIndex < this.totalImages) {
        this.$emit('next');
      }
    },
    // 편집 모드 시작
    startEditing() {
      this.isEditing = true;
      this.editingValue = this.currentIndex.toString();
      this.$nextTick(() => {
        if (this.$refs.indexInput) {
          this.$refs.indexInput.focus();
          this.$refs.indexInput.select();
        }
      });
    },
    // 편집 완료
    finishEditing() {
      const newIndex = parseInt(this.editingValue, 10);

      if (isNaN(newIndex)) {
        this.cancelEditing();
        return;
      }

      if (newIndex >= 1 && newIndex <= this.totalImages) {
        if (newIndex !== this.currentIndex) {
          this.$emit('goto', newIndex);
        }
      } else {
        // 유효하지 않은 범위인 경우 경고 메시지
        alert(`유효한 범위는 1부터 ${this.totalImages}까지입니다.`);
      }

      this.isEditing = false;
      this.editingValue = '';
    },
    // 편집 취소
    cancelEditing() {
      this.isEditing = false;
      this.editingValue = '';
    },
    // 프로그레스 바 클릭 처리
    handleProgressBarClick(event) {
      // 드래그 중이 아닐 때만 클릭 처리
      if (!this.isDragging) {
        this.calculateAndGoToImage(event);
      }
    },
    // 프로그레스 바 마우스 다운 처리
    handleProgressBarMouseDown(event) {
      this.isDragging = true;
      this.dragStartX = event.clientX;

      // 전역 마우스 이벤트 리스너 등록
      document.addEventListener('mousemove', this.handleMouseMove);
      document.addEventListener('mouseup', this.handleMouseUp);

      // 초기 위치로 이동
      this.calculateAndGoToImage(event);
    },
    // 마커 마우스 다운 처리
    handleMarkerMouseDown(event) {
      event.preventDefault();
      this.isDragging = true;
      this.dragStartX = event.clientX;

      // 전역 마우스 이벤트 리스너 등록
      document.addEventListener('mousemove', this.handleMouseMove);
      document.addEventListener('mouseup', this.handleMouseUp);
    },
    // 마우스 이동 처리
    handleMouseMove(event) {
      if (this.isDragging) {
        this.calculateAndGoToImage(event);
      }
    },
    // 마우스 업 처리
    handleMouseUp() {
      this.isDragging = false;
      this.dragStartX = 0;

      // 전역 마우스 이벤트 리스너 제거
      document.removeEventListener('mousemove', this.handleMouseMove);
      document.removeEventListener('mouseup', this.handleMouseUp);
    },
    // 위치 계산 및 이미지 이동
    calculateAndGoToImage(event) {
      if (!this.$refs.progressBar) return;

      const rect = this.$refs.progressBar.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const percentage = Math.max(0, Math.min(100, (clickX / rect.width) * 100));

      // 퍼센트를 이미지 인덱스로 변환 (1부터 시작)
      const targetIndex = Math.max(1, Math.min(this.totalImages, Math.round((percentage / 100) * this.totalImages)));

      // 현재 인덱스와 다른 경우에만 이동
      if (targetIndex !== this.currentIndex) {
        this.$emit('goto', targetIndex);
      }
    }
  },
  watch: {
    currentIndex: {
      handler(newVal, oldVal) {
        console.log(`TopImageNavigator: currentIndex 변경 ${oldVal} → ${newVal}`);
        if (newVal < 1 || newVal > this.totalImages) {
          console.warn(`TopImageNavigator: currentIndex가 유효 범위를 벗어남: ${newVal} (유효 범위: 1-${this.totalImages})`);
        }
      },
      immediate: true
    },
    totalImages: {
      handler(newVal, oldVal) {
        console.log(`TopImageNavigator: totalImages 변경 ${oldVal} → ${newVal}`);
        if (this.currentIndex > newVal && newVal > 0) {
          console.warn(`TopImageNavigator: currentIndex(${this.currentIndex})가 totalImages(${newVal})보다 큼`);
        }
      },
      immediate: true
    },
  },
  emits: ['prev', 'next', 'goto'],
};
</script>

<style scoped>
.top-image-navigator {
  background: linear-gradient(135deg, #1e1e1e 80%, #232a3a 100%);
  border-radius: 12px;
  padding: 12px 20px;
  color: #e0e0e0;
  font-size: 13px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.35);
  border: 1px solid rgba(79, 156, 245, 0.13);
  backdrop-filter: blur(10px);
  width: 100%;
  height: 54px;
  flex-shrink: 0; /* 고정 높이 유지 */
  z-index: 40;
  transition: all 0.3s ease;
}

.navigator-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 100%;
}

.nav-section {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(79, 156, 245, 0.10);
  border: 1px solid rgba(79, 156, 245, 0.25);
  border-radius: 8px;
  padding: 8px 12px;
  transition: all 0.3s ease;
  min-width: 180px;
}

.nav-section:hover {
  background: rgba(79, 156, 245, 0.18);
  border-color: rgba(79, 156, 245, 0.4);
}

.nav-btn {
  background-color: rgba(57, 130, 212, 0.1);
  border-radius: 4px;
  width: 32px;
  height: 32px;
  min-width: 32px;
  transition: background-color 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background-color: rgba(57, 130, 212, 0.2);
}

.nav-btn:disabled {
  opacity: 0.5;
  color: rgba(57, 130, 212, 0.5) !important;
}

.image-counter-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  gap: 6px;
}

.image-counter-display {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  color: #e0e0e0;
}

.index-display {
  min-width: 36px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  text-align: center;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.index-display.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.index-display.clickable:hover {
  background-color: rgba(79, 156, 245, 0.3);
  border-color: rgba(79, 156, 245, 0.5);
  transform: scale(1.05);
}

.index-input {
  min-width: 36px;
  width: 50px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  text-align: center;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: rgba(79, 156, 245, 0.2);
  border: 2px solid rgba(79, 156, 245, 0.6);
  outline: none;
  transition: all 0.2s ease;
}

.index-input:focus {
  background-color: rgba(79, 156, 245, 0.3);
  border-color: #4f9cf5;
  box-shadow: 0 0 0 2px rgba(79, 156, 245, 0.3);
}

/* 숫자 입력 필드의 스핀 버튼 제거 */
.index-input::-webkit-outer-spin-button,
.index-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* 모든 브라우저에서 기본 appearance 제거 */
.index-input {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

.separator {
  margin: 0 6px;
  color: #8f9bb3;
  font-weight: 500;
}

.total-count {
  color: #8f9bb3;
  font-size: 14px;
  font-weight: 500;
}

.center-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 600px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background-color: rgba(79, 156, 245, 0.15);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(79, 156, 245, 0.25);
  cursor: pointer;
  transition: all 0.2s ease;
}

.progress-bar:hover {
  background-color: rgba(79, 156, 245, 0.2);
  border-color: rgba(79, 156, 245, 0.4);
  transform: scaleY(1.1);
}

.progress-bar:active {
  transform: scaleY(1.2);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f9cf5 0%, #3982d4 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
  box-shadow: 0 0 8px rgba(79, 156, 245, 0.4);
  pointer-events: none;
}

.progress-marker {
  position: absolute;
  top: -2px;
  width: 12px;
  height: 12px;
  background-color: #fff;
  border: 2px solid #4f9cf5;
  border-radius: 50%;
  transform: translateX(-50%);
  transition: left 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  cursor: grab;
  z-index: 2;
}

.progress-marker:hover {
  background-color: #f0f8ff;
  border-color: #3982d4;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
  transform: translateX(-50%) scale(1.1);
}

.progress-marker:active {
  cursor: grabbing;
  transform: translateX(-50%) scale(1.2);
}

.progress-marker.dragging {
  cursor: grabbing;
  transform: translateX(-50%) scale(1.2);
  box-shadow: 0 4px 12px rgba(79, 156, 245, 0.6);
}

.marker-tooltip {
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s;
}

.progress-marker:hover .marker-tooltip {
  opacity: 1;
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: #8f9bb3;
  min-width: 40px;
  text-align: center;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 200px;
  justify-content: flex-end;
}

/* 상태 메시지 스타일 */
.status-message {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  max-width: 500px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-message.info {
  background-color: rgba(33, 150, 243, 0.85);
  color: white;
  border-color: rgba(33, 150, 243, 0.3);
}

.status-message.success {
  background-color: rgba(76, 175, 80, 0.85);
  color: white;
  border-color: rgba(76, 175, 80, 0.3);
}

.status-message.warning {
  background-color: rgba(255, 152, 0, 0.85);
  color: white;
  border-color: rgba(255, 152, 0, 0.3);
}

.status-message.error {
  background-color: rgba(244, 67, 54, 0.85);
  color: white;
  border-color: rgba(244, 67, 54, 0.3);
}

/* 사이드바 상태에 따른 위치 조정 */
:global(.app.sidebar-rail) .top-image-navigator {
  left: 68px !important;
}

/* 반응형 처리 */
@media (max-width: 1200px) {
  .navigator-container {
    gap: 16px;
  }
  .nav-section {
    gap: 6px;
    padding: 6px 10px;
    min-width: 160px;
  }
  .progress-bar-container {
    max-width: 400px;
  }
}

@media (max-width: 768px) {
  .top-image-navigator {
    padding: 8px 12px;
    height: auto;
    min-height: 50px;
  }
  .nav-section {
    gap: 4px;
    padding: 5px 8px;
    min-width: 140px;
  }
  .center-section {
    padding: 0 10px;
  }
  .progress-bar-container {
    max-width: 300px;
  }
  .progress-text {
    font-size: 11px;
    min-width: 35px;
  }
  .index-display {
    min-width: 30px;
    font-size: 13px;
    padding: 2px 4px;
  }
}

@media (max-width: 480px) {
  .top-image-navigator {
    padding: 6px 8px;
    min-height: 45px;
  }
  .navigator-container {
    gap: 8px;
  }
  .nav-section {
    gap: 3px;
    padding: 4px 6px;
    min-width: 120px;
  }
  .progress-bar-container {
    max-width: 200px;
  }
  .progress-text {
    font-size: 10px;
    min-width: 30px;
  }
  .index-display {
    min-width: 25px;
    font-size: 12px;
    padding: 1px 3px;
  }
  .nav-btn {
    width: 28px;
    height: 28px;
    min-width: 28px;
  }
}

@media (max-width: 320px) {
  .top-image-navigator {
    padding: 4px 6px;
    min-height: 40px;
  }
  .navigator-container {
    gap: 6px;
  }
  .nav-section {
    gap: 2px;
    padding: 3px 5px;
    min-width: 100px;
  }
  .progress-bar-container {
    max-width: 150px;
  }
  .progress-text {
    font-size: 9px;
    min-width: 25px;
  }
  .index-display {
    min-width: 20px;
    font-size: 11px;
    padding: 1px 2px;
  }
  .nav-btn {
    width: 24px;
    height: 24px;
    min-width: 24px;
  }
}

/* 애니메이션 효과 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.top-image-navigator {
  animation: fadeInDown 0.5s ease-out;
}

</style>
