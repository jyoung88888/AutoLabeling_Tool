<template>
  <div class="image-info-panel horizontal" v-if="currentResult">
    <!-- 파일 정보 섹션 -->
    <div class="info-section file-info">
      <span class="info-item">
        <span class="info-label">파일명:</span>
        <span class="info-value">{{ currentResult.filename }}</span>
      </span>
      <span class="info-item">
        <span class="info-label">해상도:</span>
        <span class="info-value">{{ currentResult.width }} × {{ currentResult.height }}</span>
      </span>
      <span class="info-item">
        <span class="info-label">객체 수:</span>
        <span class="info-value">{{ currentResult.boxes.length }}</span>
      </span>
      <span class="info-item" v-if="hiddenBoxes.size > 0">
        <span class="info-label">숨겨짐:</span>
        <span class="info-value hidden-count-label">{{ hiddenBoxes.size }}개</span>
      </span>
      <span class="info-item" v-if="isLowConfidenceImage">
        <span class="info-label">신뢰도:</span>
        <span class="info-value low-confidence-label">저신뢰도</span>
      </span>
    </div>

    <!-- 선택된 박스 정보 섹션 (별도 섹션으로 분리) -->
    <div v-if="selectedBoxIndex !== -1 && getSelectedBoxPosition" class="info-section selected-box-info">
      <span class="info-item">
        <span class="info-label">선택된 박스:</span>
        <span class="info-value position-value">
          <span class="box-label-badge" :style="{ backgroundColor: getClassColor(getSelectedBoxPosition.label || 'Unknown') }">
            {{ getSelectedBoxPosition.label || 'Unknown' }}
          </span>
          <span class="coordinate-group">
            <span class="coordinate-item position">X: {{ Math.round(getSelectedBoxPosition.x || 0) }}</span>
            <span class="coordinate-item position">Y: {{ Math.round(getSelectedBoxPosition.y || 0) }}</span>
            <span class="coordinate-item size">W: {{ Math.round(getSelectedBoxPosition.width || 0) }}</span>
            <span class="coordinate-item size">H: {{ Math.round(getSelectedBoxPosition.height || 0) }}</span>
          </span>
          <span class="coordinate-group center-coords">
            <span class="coordinate-item center">중심 X: {{ Math.round((getSelectedBoxPosition.x || 0) + (getSelectedBoxPosition.width || 0)/2) }}</span>
            <span class="coordinate-item center">중심 Y: {{ Math.round((getSelectedBoxPosition.y || 0) + (getSelectedBoxPosition.height || 0)/2) }}</span>
          </span>
          <span v-if="editMode === 'edit'" class="edit-mode-badge">편집중</span>
        </span>
      </span>
    </div>

    <!-- 편집모드 안내 섹션 -->
    <div v-else-if="currentResult && currentResult.boxes && currentResult.boxes.length > 0" class="info-section edit-mode-guide">
      <span class="info-item">
        <span class="info-label">바운딩 박스 편집:</span>
        <span class="info-value guide-value">
          <span class="guide-badge">E키</span>
          <span class="guide-text">편집모드 활성화</span>
          <span class="guide-separator">→</span>
          <span class="guide-text">박스 클릭</span>
          <span class="guide-separator">→</span>
          <span class="guide-text">좌표 정보 표시</span>
        </span>
      </span>
    </div>

    <!-- 라벨링 타입 섹션 -->
    <div class="info-section labeling-section">
      <span class="info-item">
        <span class="info-label">라벨링:</span>
        <span class="info-value">바운딩 박스</span>
      </span>
    </div>

    <!-- 라벨 정보 섹션 -->
    <div class="info-section label-section">
      <div class="label-list-horizontal">
        <div
          v-for="(boxGroup, className) in groupedBoxes"
          :key="className"
          class="label-item-inline"
        >
          <div class="color-dot" :style="{ backgroundColor: getClassColor(className) }"></div>
          <span class="label-name-inline">{{ className }}</span>
          <span class="label-count-inline">{{ boxGroup.length }}</span>
        </div>
      </div>
    </div>


  </div>
</template>

<script>
import { getClassColor as utilGetClassColor, UI_COLORS } from '@/utils/colorUtils.js';

export default {
  name: 'ImageInfoPanel',
  props: {
    currentResult: {
      type: Object,
      default: null
    },
    isLowConfidenceImage: {
      type: Boolean,
      default: false
    },
    selectedBoxIndex: {
      type: Number,
      default: -1
    },
    getSelectedBoxPosition: {
      type: Object,
      default: () => ({ x: 0, y: 0, width: 0, height: 0, label: 'Unknown' })
    },
    groupedBoxes: {
      type: Object,
      default: () => ({})
    },
    editMode: {
      type: String,
      default: 'edit'
    },
    classColors: {
      type: Object,
      default: () => ({})
    },
    projectPath: {
      type: String,
      default: ''
    },
    hiddenBoxes: {
      type: Set,
      default: () => new Set()
    }
  },
  emits: [],
  computed: {
    uiColors() {
      return UI_COLORS;
    }
  },
  methods: {
    getClassColor(className) {
      // 통합 색상 유틸리티 사용
      return utilGetClassColor(className, this.classColors);
    }
  }
}
</script>

<style scoped>
.image-info-panel {
  background: linear-gradient(135deg, #1e1e1e 80%, #232a3a 100%);
  border-radius: 12px;
  padding: 12px 20px;
  color: #e0e0e0;
  font-size: 13px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.35);
  border: 1px solid rgba(79, 156, 245, 0.13);
  backdrop-filter: blur(10px);
  width: 100%;
}

.image-info-panel.horizontal {
  display: flex;
  align-items: center;
  gap: 20px;
  height: 54px;
  flex-wrap: wrap;
  flex-shrink: 0; /* 고정 높이 유지 */
}

.info-section {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(44, 49, 66, 0.18);
  transition: all 0.3s ease;
}

.file-info {
  flex: 0 0 auto;
  background: rgba(79, 156, 245, 0.10);
  border-color: rgba(79, 156, 245, 0.25);
}

.file-info:hover {
  background: rgba(79, 156, 245, 0.18);
  border-color: rgba(79, 156, 245, 0.4);
}

.labeling-section {
  flex: 0 0 auto;
  background: rgba(76, 175, 80, 0.10);
  border-color: rgba(76, 175, 80, 0.25);
}

.labeling-section:hover {
  background: rgba(76, 175, 80, 0.18);
  border-color: rgba(76, 175, 80, 0.4);
}

.selected-box-info {
  flex: 0 0 auto;
  background: rgba(255, 193, 7, 0.10);
  border-color: rgba(255, 193, 7, 0.25);
  border: 2px solid rgba(255, 193, 7, 0.3);
}

.selected-box-info:hover {
  background: rgba(255, 193, 7, 0.18);
  border-color: rgba(255, 193, 7, 0.4);
}

.edit-mode-guide {
  flex: 0 0 auto;
  background: rgba(103, 58, 183, 0.10);
  border-color: rgba(103, 58, 183, 0.25);
  border: 1px solid rgba(103, 58, 183, 0.3);
}

.edit-mode-guide:hover {
  background: rgba(103, 58, 183, 0.18);
  border-color: rgba(103, 58, 183, 0.4);
}

.guide-value {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9c7ddb;
  font-weight: 600;
}

.guide-badge {
  background: linear-gradient(135deg, #673AB7, #512DA8);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(103, 58, 183, 0.4);
}

.guide-text {
  font-size: 11px;
  color: #B39DDB;
}

.guide-separator {
  color: #7E57C2;
  font-weight: bold;
}

.label-section {
  flex: 1 1 auto;
  min-width: 0;
  background: rgba(30, 30, 30, 0.10);
  border-color: rgba(255,255,255,0.08);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.info-label {
  color: #8f9bb3;
  font-weight: 500;
  margin-right: 2px;
}

.info-value {
  color: #e0e0e0;
  font-weight: 600;
}

.low-confidence-label {
  color: #f0ad4e;
  font-weight: bold;
}

.hidden-count-label {
  color: #ff6b6b;
  font-weight: bold;
  background: rgba(255, 107, 107, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 11px;
}

.position-value {
  color: #4f9cf5;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.box-label-badge {
  color: white;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.3);
  min-width: 50px;
  text-align: center;
}

.coordinate-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.coordinate-group.center-coords {
  border-left: 1px solid rgba(79, 156, 245, 0.3);
  padding-left: 8px;
}

.coordinate-item {
  background: rgba(79, 156, 245, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  border: 1px solid rgba(79, 156, 245, 0.3);
  color: #87CEEB;
}

.coordinate-item.position {
  background: rgba(33, 150, 243, 0.2);
  border-color: rgba(33, 150, 243, 0.3);
  color: #81C784;
}

.coordinate-item.size {
  background: rgba(156, 39, 176, 0.2);
  border-color: rgba(156, 39, 176, 0.3);
  color: #CE93D8;
}

.coordinate-item.center {
  background: rgba(255, 152, 0, 0.2);
  border-color: rgba(255, 152, 0, 0.3);
  color: #FFB74D;
}

.edit-mode-badge {
  background: linear-gradient(135deg, #FF8C00, #FF4500);
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  animation: pulse 2s infinite;
  box-shadow: 0 2px 6px rgba(255, 140, 0, 0.4);
}

@keyframes pulse {
  0% {
    box-shadow: 0 2px 6px rgba(255, 140, 0, 0.4);
  }
  50% {
    box-shadow: 0 2px 12px rgba(255, 140, 0, 0.8);
  }
  100% {
    box-shadow: 0 2px 6px rgba(255, 140, 0, 0.4);
  }
}

.label-list-horizontal {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow-x: auto;
  max-width: 100%;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 2px 0;
}

.label-list-horizontal::-webkit-scrollbar {
  display: none;
}

.label-item-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 10px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  cursor: pointer;
}

.label-item-inline:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.label-name-inline {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  font-size: 11px;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.label-count-inline {
  background: linear-gradient(135deg, #3B82F6, #1D4ED8);
  color: white;
  padding: 2px 7px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
}

/* 반응형 처리 */
@media (max-width: 1200px) {
  .image-info-panel.horizontal {
    gap: 16px;
  }
  .info-section {
    gap: 10px;
    padding: 6px 10px;
  }
  .coordinate-group.center-coords {
    display: none; /* 화면이 작을 때 중심 좌표 숨김 */
  }
}

@media (max-width: 768px) {
  .image-info-panel.horizontal {
    gap: 12px;
    padding: 8px 8px;
    height: auto;
    min-height: 50px;
  }
  .info-section {
    gap: 6px;
    padding: 5px 6px;
  }
  .info-item {
    gap: 2px;
  }
  .info-label, .info-value {
    font-size: 11px;
  }
  .coordinate-item {
    font-size: 9px;
    padding: 1px 4px;
  }
  .box-label-badge {
    font-size: 10px;
    padding: 2px 6px;
  }
  .edit-mode-badge {
    font-size: 9px;
    padding: 1px 6px;
  }
}

@media (max-width: 480px) {
  .image-info-panel.horizontal {
    gap: 8px;
    padding: 6px 6px;
    min-height: 45px;
  }
  .info-section {
    gap: 4px;
    padding: 4px 5px;
  }
  .info-item {
    gap: 1px;
  }
  .info-label, .info-value {
    font-size: 10px;
  }
  .coordinate-item {
    font-size: 8px;
    padding: 1px 3px;
  }
  .box-label-badge {
    font-size: 9px;
    padding: 1px 5px;
  }
  .edit-mode-badge {
    font-size: 8px;
    padding: 1px 5px;
  }
  .label-name-inline {
    font-size: 10px;
  }
  .label-count-inline {
    font-size: 9px;
    padding: 1px 6px;
    min-width: 18px;
  }
  .color-dot {
    width: 10px;
    height: 10px;
  }
}

@media (max-width: 320px) {
  .image-info-panel.horizontal {
    gap: 6px;
    padding: 4px 4px;
    min-height: 40px;
  }
  .info-section {
    gap: 3px;
    padding: 3px 4px;
  }
  .info-item {
    gap: 1px;
  }
  .info-label, .info-value {
    font-size: 9px;
  }
  .coordinate-item {
    font-size: 7px;
    padding: 1px 2px;
  }
  .box-label-badge {
    font-size: 8px;
    padding: 1px 4px;
  }
  .edit-mode-badge {
    font-size: 7px;
    padding: 1px 4px;
  }
  .label-name-inline {
    font-size: 9px;
  }
  .label-count-inline {
    font-size: 8px;
    padding: 1px 5px;
    min-width: 16px;
  }
  .color-dot {
    width: 8px;
    height: 8px;
  }
}

/* 애니메이션 효과 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.image-info-panel {
  animation: fadeInUp 0.5s ease-out;
}

.label-item-inline {
  animation: fadeInUp 0.3s ease-out;
}
</style>
