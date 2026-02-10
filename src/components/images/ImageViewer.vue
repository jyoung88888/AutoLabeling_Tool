<template>
  <v-card
    v-if="currentResult"
    class="flex-grow-1 image-viewer-card"
    elevation="0"
    rounded="0"
    color="transparent"
  >
    <!-- 메인 이미지 뷰어 영역 -->
    <div class="image-viewer" ref="imageViewer">
      <div class="image-container" ref="imageContainer" @wheel="handleWheel">
        <div class="konva-container" ref="konvaContainer" @pointermove="handleNativePointerMove">
          <v-stage
            ref="stage"
            :config="stageConfig"
            @wheel="handleWheel"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @touchstart="handleMouseDown"
            @dragstart="handleStageDragStart"
            @dragmove="handleStageDragMove"
            @dragend="handleStageDragEnd"
          >
            <v-layer ref="imageLayer">
              <!-- 이미지 레이어 -->
              <v-image
                v-if="imageNode"
                :config="imageConfig"
              />
            </v-layer>
            <v-layer ref="boxLayer">
              <!-- 바운딩 박스 레이어 -->
              <!-- 우선순위에 따라 정렬된 박스들 렌더링 (숨겨진 박스 < 보이는 박스) -->
              <v-group
                v-for="{ box, index } in sortedBoxesForRendering"
                :key="`box-${index}`"
                @click="handleBoxClick(index, $event)"
                @tap="handleBoxClick(index, $event)"
                @mouseover="() => handleBoxMouseOver(index)"
                @mouseout="() => handleBoxMouseOut(index)"
              >
                <!-- 바운딩 박스 -->
                <v-rect
                  :config="{
                    x: box.x,
                    y: box.y,
                    width: box.width,
                    height: box.height,
                    stroke: box.color || '#00ff00',
                    strokeWidth: getBoxStrokeWidth(index),
                    dash: hiddenBoxes.has(index) ? [4, 4] : (box.isLowConfidence ? [8, 8] : (selectedBoxIndices.has(index) && selectedBoxIndices.size > 1 ? [6, 6] : [])),
                    listening: !hiddenBoxes.has(index),
                    id: `box-rect-${index}`,
                    opacity: hiddenBoxes.has(index) ? 0.05 : 1.0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)',
                    shadowBlur: 3,
                    shadowOffset: { x: 1, y: 1 },
                    cursor: editMode === 'edit' && selectedBoxIndex === index ? 'move' : 'pointer',
                    draggable: editMode === 'edit' && selectedBoxIndex === index
                  }"
                  @dragmove="editMode === 'edit' && selectedBoxIndex === index ? handleBoxMove($event, index) : null"
                  @dragend="editMode === 'edit' && selectedBoxIndex === index ? handleBoxMoveEnd($event, index) : null"
                />
                <!-- 라벨 텍스트 -->
                <v-text
                  :config="{
                    x: box.x + 2,
                    y: box.y - getLabelFontSize(selectedBoxIndex === index ? 14 : 13) - 4,
                    text: box.label + (box.confidenceText ? ` (${box.confidenceText})` : ''),
                    fontSize: getLabelFontSize(selectedBoxIndex === index ? 14 : 13),
                    fontFamily: 'Arial, sans-serif',
                    fill: box.color || '#00ff00',
                    fontStyle: box.isLowConfidence ? 'italic' : 'normal',
                    fontWeight: selectedBoxIndex === index ? 'bold' : 'normal',
                    opacity: hiddenBoxes.has(index) ? 0.05 : 1.0,
                    listening: false,
                    align: 'left'
                  }"
                />
              </v-group>

              <!-- 선택된 박스를 마지막에 렌더링하여 최상위에 표시 -->
              <v-group
                v-if="selectedBoxIndex >= 0 && selectedBoxIndex < boundingBoxes.length"
                :key="`selected-box-${selectedBoxIndex}`"
                @click="handleBoxClick(selectedBoxIndex, $event)"
                @tap="handleBoxClick(selectedBoxIndex, $event)"
                @mouseover="() => handleBoxMouseOver(selectedBoxIndex)"
                @mouseout="() => handleBoxMouseOut(selectedBoxIndex)"
              >
                <!-- 바운딩 박스 -->
                <v-rect
                  :config="{
                    x: boundingBoxes[selectedBoxIndex].x,
                    y: boundingBoxes[selectedBoxIndex].y,
                    width: boundingBoxes[selectedBoxIndex].width,
                    height: boundingBoxes[selectedBoxIndex].height,
                    stroke: boundingBoxes[selectedBoxIndex].color || '#00ff00',
                    strokeWidth: getBoxStrokeWidth(selectedBoxIndex),
                    dash: hiddenBoxes.has(selectedBoxIndex) ? [4, 4] : (boundingBoxes[selectedBoxIndex].isLowConfidence ? [8, 8] : (selectedBoxIndices.has(selectedBoxIndex) && selectedBoxIndices.size > 1 ? [6, 6] : [])),
                    listening: !hiddenBoxes.has(selectedBoxIndex),
                    id: `box-rect-${selectedBoxIndex}`,
                    opacity: hiddenBoxes.has(selectedBoxIndex) ? 0.05 : 1.0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)',
                    shadowBlur: 3,
                    shadowOffset: { x: 1, y: 1 },
                    cursor: editMode === 'edit' ? 'move' : 'pointer',
                    draggable: editMode === 'edit'
                  }"
                  @dragmove="editMode === 'edit' ? handleBoxMove($event, selectedBoxIndex) : null"
                  @dragend="editMode === 'edit' ? handleBoxMoveEnd($event, selectedBoxIndex) : null"
                />
                <!-- 라벨 텍스트 -->
                <v-text
                  :config="{
                    x: boundingBoxes[selectedBoxIndex].x + 2,
                    y: boundingBoxes[selectedBoxIndex].y - getLabelFontSize(14) - 4,
                    text: boundingBoxes[selectedBoxIndex].label + (boundingBoxes[selectedBoxIndex].confidenceText ? ` (${boundingBoxes[selectedBoxIndex].confidenceText})` : ''),
                    fontSize: getLabelFontSize(14),
                    fontFamily: 'Arial, sans-serif',
                    fill: boundingBoxes[selectedBoxIndex].color || '#00ff00',
                    fontStyle: boundingBoxes[selectedBoxIndex].isLowConfidence ? 'italic' : 'normal',
                    fontWeight: 'bold',
                    opacity: hiddenBoxes.has(selectedBoxIndex) ? 0.05 : 1.0,
                    listening: false,
                    align: 'left'
                  }"
                />
                <!-- 편집 핸들들 (편집 모드에서만 표시, 숨겨지지 않은 박스만) -->
                <v-group v-if="editMode === 'edit' && !hiddenBoxes.has(selectedBoxIndex)">
                  <!-- 리사이즈 핸들들 -->
                  <v-circle
                    v-for="(handle, handleType) in currentResizeHandles"
                    :key="`handle-${selectedBoxIndex}-${handleType}`"
                    :config="{
                      x: handle.x,
                      y: handle.y,
                      radius: getSmallHandleRadius(),
                      fill: handle.color,
                      stroke: '#ffffff',
                      strokeWidth: 0.5,
                      listening: true,
                      draggable: true,
                      id: `handle-${selectedBoxIndex}-${handleType}`,
                      cursor: handle.cursor,
                      opacity: 0.8,
                      shadowColor: 'rgba(0, 0, 0, 0.3)',
                      shadowBlur: 0.5,
                      shadowOffset: { x: 0.5, y: 0.5 }
                    }"
                    @dragmove="handleResize($event, selectedBoxIndex, handleType)"
                    @dragend="handleResizeEnd($event, selectedBoxIndex)"
                    @mouseover="($event) => handleMouseOver($event, handle.cursor)"
                    @mouseout="handleMouseOut"
                  />
                  <!-- 이동 핸들 제거 - 바운딩 박스 자체에서 이동 처리 -->
                </v-group>
              </v-group>

              <!-- 새 박스 그리기 시 임시 박스 -->
              <v-rect
                v-if="isDrawing && tempBox"
                :config="{
                  x: tempBox.x,
                  y: tempBox.y,
                  width: tempBox.width,
                  height: tempBox.height,
                  stroke: selectedClassColor,
                  strokeWidth: 3,
                  dash: [3, 3],
                  listening: false,
                  opacity: 0.8,
                  shadowColor: 'rgba(0, 0, 0, 0.3)',
                  shadowBlur: 2,
                  shadowOffset: { x: 1, y: 1 }
                }"
              />
            </v-layer>

            <!-- 마우스 십자선 가이드 레이어 -->
            <v-layer :config="{ listening: false, hitGraphEnabled: false }">
              <!-- 수직선 -->
              <v-line
                v-if="currentMousePos.x > 0 && currentMousePos.y > 0"
                :config="{
                  points: [currentMousePos.x, 0, currentMousePos.x, imageHeight],
                  stroke: 'red',
                  strokeWidth: 1,
                  opacity: 0.8,
                  listening: false,
                  perfectDrawEnabled: false
                }"
              />
              <!-- 수평선 -->
              <v-line
                v-if="currentMousePos.x > 0 && currentMousePos.y > 0"
                :config="{
                  points: [0, currentMousePos.y, imageWidth, currentMousePos.y],
                  stroke: 'red',
                  strokeWidth: 1,
                  opacity: 0.8,
                  listening: false,
                  perfectDrawEnabled: false
                }"
              />
            </v-layer>
          </v-stage>
        </div>

        <!-- 클래스 범례 -->
        <div class="class-legend-wrapper">
          <ClassLegend
            :class-info="projectClassInfo"
          />
        </div>
      </div>

      <!-- 이미지 정보 패널 -->
      <div class="info-panel-container">
        <ImageInfoPanel
          :current-result="currentResult"
          :is-low-confidence-image="isLowConfidenceImage"
          :selected-box-index="selectedBoxIndex"
          :get-selected-box-position="getSelectedBoxPosition"
          :grouped-boxes="groupedBoxes"
          :edit-mode="editMode"
          :class-colors="classColors"
          :project-path="projectPath"
          :hidden-boxes="hiddenBoxes"
          @show-help="$emit('show-help')"
          @reset-zoom="resetZoom"
          @open-load-project="$emit('open-load-project')"
        />
      </div>

      <!-- 편집 모드 인디케이터 -->
      <div v-if="editMode === 'edit'" class="edit-mode-indicator">
        <v-chip color="orange" size="small" prepend-icon="mdi-pencil">
          편집 모드 - R키로 해제
        </v-chip>
      </div>

      <!-- 그리기 모드 인디케이터 -->
      <div v-if="editMode === 'draw'" class="draw-mode-indicator">
        <v-chip color="green" size="small" prepend-icon="mdi-plus-box">
          그리기 모드 - 드래그로 박스 생성
        </v-chip>
      </div>
    </div>
  </v-card>
  <v-card v-else-if="isLoadingProject || isLoadingImages" elevation="0" rounded="lg" class="pa-4 no-image-card" color="#151a24">
    <v-card-text class="text-center text-body-1 text-grey">
      <v-progress-circular indeterminate color="primary" class="mb-3"></v-progress-circular>
      <div>프로젝트 이미지를 불러오는 중입니다...</div>
      <div class="mt-2 text-body-2">이미지 {{loadingImageProgress ? loadingImageProgress + '% 완료' : '로드 중'}}</div>
    </v-card-text>
  </v-card>
  <v-card v-else elevation="0" rounded="lg" class="pa-4 no-image-card" color="#000000">
    <v-card-text class="text-center text-body-1" style="color: #ffffff !important;">
      <v-icon icon="mdi-image-outline" size="large" class="mb-2" color="grey-lighten-1"></v-icon>
      <div>아직 라벨링된 이미지가 없습니다.</div>
      <div class="mt-2 text-body-2">자동 라벨링을 시작하면 이곳에 이미지가 표시됩니다.</div>
    </v-card-text>
    </v-card>

    <!-- 복사 및 선택 알림창 -->
    <v-snackbar
      v-model="showMultiSelectSnackbar"
      :timeout="2500"
      location="top center"
      color="success"
      class="modern-snackbar copy-notification-snackbar"
      elevation="20"
      rounded="lg"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          :icon="multiSelectIcon"
          color="green-lighten-1"
          size="28"
          class="mr-4 notification-icon"
        ></v-icon>
        <div>
          <div class="text-subtitle-1 font-weight-bold notification-title">
            {{ multiSelectIcon === 'mdi-content-copy' ? '복사 완료' : '선택 완료' }}
          </div>
          <div class="text-caption notification-message">
            {{ multiSelectMessage }}
          </div>
        </div>
      </div>
    </v-snackbar>

    <!-- 저장 상태 알림창 -->
    <v-snackbar
      v-model="showSaveSnackbar"
      :timeout="3000"
      location="top center"
      :color="saveMessageType === 'success' ? 'success' : 'error'"
      class="modern-snackbar save-snackbar"
      elevation="16"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          :icon="saveIcon"
          color="white"
          size="24"
          class="mr-3 notification-icon"
        ></v-icon>
        <span class="text-body-2 notification-message">{{ saveMessage }}</span>
      </div>
    </v-snackbar>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import ImageInfoPanel from '@/components/images/ImageInfoPanel.vue'
import ClassLegend from '@/components/images/ClassLegend.vue'
import { getClassColor } from '@/utils/colorUtils.js'
import { API_SERVER } from '@/utils/config.js'

export default {
  name: 'ImageViewer',
  components: {
    ImageInfoPanel,
    ClassLegend
  },
  props: {
    currentResult: {
      type: Object,
      default: null
    },
    canvasRef: {
      type: Object,
      default: null
    },
    currentImageIndex: {
      type: Number,
      default: 1
    },
    totalImages: {
      type: Number,
      default: 0
    },
    results: {
      type: Array,
      default: () => []
    },
    availableClassesFromParent: {
      type: Array,
      default: () => []
    },
    lowConfidenceImages: {
      type: Array,
      default: () => []
    },
    projectPath: {
      type: String,
      default: ''
    },
    isLoadingProject: {
      type: Boolean,
      default: false
    },
    isLoadingImages: {
      type: Boolean,
      default: false
    },
    loadingImageProgress: {
      type: Number,
      default: 0
    },
    projectClassInfo: {
      type: Array,
      default: () => []
    },
    copiedBox: {
      type: Object,
      default: null
    },
    thickBoxMode: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'prev',
    'next',
    'bbox-edit',
    'bbox-change',
    'delete-box',
    'status-message',
    'open-load-project',
    'show-help',
    'update-copied-box',
    'update-thick-box-mode'
  ],
  setup(props, { emit }) {
    // Refs
    const imageViewer = ref(null)
    const imageContainer = ref(null)
    const konvaContainer = ref(null)
    const stage = ref(null)
    const imageLayer = ref(null)
    const boxLayer = ref(null)

    // State
    const selectedBoxIndex = ref(-1)
    const selectedBoxIndices = ref(new Set()) // 다중 선택된 박스들의 인덱스
    const editMode = ref('view') // 'view', 'edit', 'draw'
    const imageNode = ref(null)
    const boundingBoxes = ref([])
    const classColors = ref({})
    const selectedClassIndex = ref(0)
    const hiddenBoxes = ref(new Set()) // 숨겨진 박스들의 인덱스를 저장
    const hoveredBoxIndex = ref(-1) // 마우스가 올라간 박스의 인덱스
    const currentMousePos = ref({ x: 0, y: 0 }) // 현재 마우스 위치 (이미지 좌표계)
    const hasChanges = ref(false) // 편집모드에서 변경사항이 있는지 추적

    // 다중 선택 알림창 관련
    const showMultiSelectSnackbar = ref(false)
    const multiSelectMessage = ref('')
    const multiSelectIcon = ref('mdi-selection-multiple')

    // 저장 상태 알림창 관련
    const showSaveSnackbar = ref(false)
    const saveMessage = ref('')
    const saveMessageType = ref('success')
    const saveIcon = ref('mdi-content-save')

    // Drawing state
    const isDrawing = ref(false)
    const startPoint = ref(null)
    const tempBox = ref(null)

    // Stage dragging state (for Space+drag in edit mode)
    const isDraggingStage = ref(false)
    const dragStartPos = ref(null)
    const dragStartStagePos = ref(null)
    const isSpacePressed = ref(false)
    const isDragStarted = ref(false)

    // Undo/Redo history management
    const historyStack = ref([])
    const maxHistorySize = 10

    // Step zoom levels - 저해상도 이미지를 위해 높은 확대 범위 추가
    const zoomLevels = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0]
    const currentZoomIndex = ref(4) // 기본값은 100% (index 4)

    // Display settings
    const containerWidth = ref(800)
    const containerHeight = ref(600)
    const displayScale = ref(1)
    const stageScale = ref(1) // 실제 stage 확대/축소 scale (마우스 휠 등)
    const stageX = ref(0)
    const stageY = ref(0)
    const imageWidth = ref(0)
    const imageHeight = ref(0)

    // Computed
    const stageConfig = computed(() => ({
      width: containerWidth.value,
      height: containerHeight.value,
      x: stageX.value,
      y: stageY.value,
      scaleX: displayScale.value,
      scaleY: displayScale.value,
      draggable: false // 수동 드래그 처리를 위해 비활성화
    }))

    const imageConfig = computed(() => ({
      image: imageNode.value,
      x: 0,
      y: 0,
      width: imageWidth.value,
      height: imageHeight.value
    }))

    const isLowConfidenceImage = computed(() => {
      if (!props.currentResult) return false
      return props.lowConfidenceImages.some(img => img.filename === props.currentResult.filename)
    })

    const groupedBoxes = computed(() => {
      if (!boundingBoxes.value.length) return {}

      const grouped = {}
      boundingBoxes.value.forEach((box, index) => {
        const className = box.label || 'unknown'
        if (!grouped[className]) {
          grouped[className] = []
        }
        grouped[className].push({ ...box, index })
      })

      return grouped
    })

    const selectedClassColor = computed(() => {
      const availableClasses = props.availableClassesFromParent
      if (availableClasses.length > 0 && selectedClassIndex.value < availableClasses.length) {
        const className = availableClasses[selectedClassIndex.value]
        return getClassColor(className, classColors.value)
      }
      return '#00ff00'
    })

    // 클릭 우선순위에 따라 정렬된 박스 목록 (숨겨진 박스 < 보이는 박스 < 선택된 박스)
    const sortedBoxesForRendering = computed(() => {
      if (!boundingBoxes.value.length) return []

      return boundingBoxes.value
        .map((box, index) => ({ box, index }))
        .filter(({ index }) => selectedBoxIndex.value !== index) // 선택된 박스는 제외 (별도 렌더링)
        .sort((a, b) => {
          // 숨겨진 박스가 먼저, 보이는 박스가 나중에 (나중에 렌더링될수록 위에 표시됨)
          const aHidden = hiddenBoxes.value.has(a.index)
          const bHidden = hiddenBoxes.value.has(b.index)

          if (aHidden && !bHidden) return -1 // a가 숨겨짐, b가 보임 -> a를 먼저
          if (!aHidden && bHidden) return 1  // a가 보임, b가 숨겨짐 -> b를 먼저
          return 0 // 둘 다 같은 상태면 원래 순서 유지
        })
    })

    // Undo/Redo 히스토리 관리 함수들
    const saveToHistory = () => {
      // 편집 모드가 아닐 때는 히스토리 저장하지 않음
      if (editMode.value !== 'edit') {
        return
      }

      // 현재 바운딩 박스 상태를 깊은 복사로 저장
      const currentState = {
        boundingBoxes: JSON.parse(JSON.stringify(boundingBoxes.value)),
        selectedBoxIndex: selectedBoxIndex.value,
        selectedBoxIndices: new Set(selectedBoxIndices.value),
        timestamp: Date.now()
      }

      // 스택에 추가
      historyStack.value.push(currentState)

      // 최대 크기 초과 시 가장 오래된 항목 제거
      if (historyStack.value.length > maxHistorySize) {
        historyStack.value.shift()
      }

      console.log(`히스토리 저장: ${historyStack.value.length}/${maxHistorySize}개 상태 보관 중`)
    }

    // 히스토리 스택 초기화 함수
    const clearHistory = () => {
      const previousHistoryCount = historyStack.value.length
      historyStack.value = []

      if (previousHistoryCount > 0) {
        console.log(`히스토리 스택 초기화: ${previousHistoryCount}개 상태가 제거됨`)
      }
    }

    const undoLastAction = () => {
      if (historyStack.value.length === 0) {
        emit('status-message', {
          message: '되돌릴 작업이 없습니다',
          type: 'info',
          icon: 'mdi-information'
        })
        return false
      }

      // 편집 모드가 아닐 때는 되돌리기 불가
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 작업을 되돌릴 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return false
      }

      // 마지막 상태 복원
      const lastState = historyStack.value.pop()

      boundingBoxes.value = JSON.parse(JSON.stringify(lastState.boundingBoxes))
      selectedBoxIndex.value = lastState.selectedBoxIndex
      selectedBoxIndices.value = new Set(lastState.selectedBoxIndices)

      // 변경사항 표시
      hasChanges.value = true

      console.log(`작업 복원: ${historyStack.value.length}개 상태 남음`)

      emit('status-message', {
        message: `작업을 되돌렸습니다 (${historyStack.value.length}/${maxHistorySize}단계 남음)`,
        type: 'success',
        icon: 'mdi-undo'
      })

      // 복원된 상태에 대한 이벤트 발생
      emit('bbox-change', {
        action: 'undo',
        boxes: boundingBoxes.value,
        selectedIndex: selectedBoxIndex.value
      })

      return true
    }

    // 이미지가 화면에 맞게 전체가 보이도록 스케일링하는 함수
    const calculateDisplaySize = () => {
      if (!imageContainer.value) return

      const containerRect = imageContainer.value.getBoundingClientRect()

      // 컨테이너의 사용 가능한 크기 (적절한 패딩 고려)
      const availableWidth = Math.max(300, containerRect.width - 20)
      const availableHeight = Math.max(200, containerRect.height - 20)

      // Stage 크기를 컨테이너에 맞게 설정
      containerWidth.value = availableWidth
      containerHeight.value = availableHeight

      // 이미지가 있는 경우 스케일과 위치 계산
      if (imageWidth.value > 0 && imageHeight.value > 0) {
        // 이미지가 컨테이너에 완전히 들어가도록 스케일 계산
        const scaleX = availableWidth / imageWidth.value
        const scaleY = availableHeight / imageHeight.value

        // 더 작은 스케일을 사용해서 이미지 전체가 보이도록 함
        const fitScale = Math.min(scaleX, scaleY)

        // 최대 스케일 제한 (너무 크게 확대되지 않도록)
        displayScale.value = Math.min(fitScale, 1.0)
        stageScale.value = displayScale.value // 초기 stage scale 설정

        // 실제 표시될 이미지 크기 계산
        const scaledImageWidth = imageWidth.value * displayScale.value
        const scaledImageHeight = imageHeight.value * displayScale.value

        // 이미지를 중앙에 배치
        stageX.value = (availableWidth - scaledImageWidth) / 2
        stageY.value = (availableHeight - scaledImageHeight) / 2
      } else {
        // 이미지가 없는 경우 기본값
        displayScale.value = 1
        stageScale.value = 1 // 초기 stage scale 설정
        stageX.value = 0
        stageY.value = 0
      }
    }

    // Methods
    const getImageSource = () => {
      if (!props.currentResult) return ''
      const imagePath = props.currentResult.image_path || props.currentResult.filename

      if (!imagePath || imagePath.trim() === '') {
        console.warn('빈 이미지 경로로 인한 요청 방지:', props.currentResult)
        return ''
      }

      if (props.projectPath) {
        return `${API_SERVER}/files/${props.projectPath}/images/${imagePath}`
      }

      return `${API_SERVER}/files/${imagePath}`
    }

    const loadImage = async () => {
      const imageSrc = getImageSource()
      if (!imageSrc) return

      const img = new Image()
      img.crossOrigin = 'anonymous'

      img.onload = () => {
        imageNode.value = img
        imageWidth.value = img.naturalWidth
        imageHeight.value = img.naturalHeight

        // DOM 업데이트 후 크기 재계산
        nextTick(async () => {
          calculateDisplaySize()
          await processResults()
        })
      }

      img.onerror = () => {
        console.error('이미지 로드 실패:', imageSrc)
        handleImageError()
      }

      img.src = imageSrc
    }

    const processResults = async () => {
      console.log('processResults 시작:', {
        currentResult: props.currentResult,
        imageWidth: imageWidth.value,
        imageHeight: imageHeight.value,
        hasCurrentResult: !!props.currentResult,
        resultFilename: props.currentResult?.filename
      })

      if (!props.currentResult) {
        boundingBoxes.value = []
        console.log('currentResult가 없어서 바운딩박스 초기화')
        return
      }

      // 이미지 크기 정보 검증
      if (!imageWidth.value || !imageHeight.value || imageWidth.value <= 0 || imageHeight.value <= 0) {
        console.warn('이미지 크기 정보가 올바르지 않음:', {
          imageWidth: imageWidth.value,
          imageHeight: imageHeight.value
        })
        // 결과에서 크기 정보 가져오기 시도
        if (props.currentResult.width && props.currentResult.height) {
          console.log('결과에서 이미지 크기 정보 사용:', {
            width: props.currentResult.width,
            height: props.currentResult.height
          })
        } else {
          console.error('이미지 크기 정보를 찾을 수 없음')
          return
        }
      }

      // 먼저 저장된 라벨 파일이 있는지 확인하고 로드
      const savedBoxes = await loadSavedLabels()

      if (savedBoxes && savedBoxes.length > 0) {
        // 저장된 라벨이 있으면 우선적으로 사용
        boundingBoxes.value = savedBoxes
        console.log(`저장된 라벨 파일에서 ${savedBoxes.length}개의 바운딩 박스를 로드했습니다.`)
      } else {
                        // 저장된 라벨이 없으면 자동 라벨링 결과 사용
        const result = props.currentResult
        const boxes = []

        // 원본 이미지 크기 정보 (백엔드에서 제공, YOLO 예측에 사용된 크기)
        const originalWidth = result.width || 0
        const originalHeight = result.height || 0

        console.log('자동 라벨링 결과 처리:', {
          hasBoxes: !!result.boxes,
          boxesLength: result.boxes?.length,
          resultKeys: Object.keys(result),
          originalImageSize: { originalWidth, originalHeight },
          displayImageSize: { width: imageWidth.value, height: imageHeight.value },
          fullResult: result
        })

        // 원본 이미지 크기 확인
        if (!originalWidth || !originalHeight || originalWidth <= 0 || originalHeight <= 0) {
          console.error('원본 이미지 크기 정보가 없거나 유효하지 않음:', {
            originalWidth,
            originalHeight,
            result
          })
          return
        }

        if (result.boxes && Array.isArray(result.boxes)) {
          console.log(`result.boxes 처리 시작: ${result.boxes.length}개`)
          console.log('첫 번째 박스 샘플:', result.boxes[0])

          result.boxes.forEach((detection, index) => {
            console.log(`박스 ${index} 처리:`, detection)
            const box = processDetectionBox(detection, originalWidth, originalHeight)
            if (box) {
              box.color = getClassColor(box.label, classColors.value)
              boxes.push(box)
              console.log(`박스 ${index} 성공적으로 추가:`, box)
            } else {
              console.warn(`박스 ${index} 처리 실패`)
            }
          })
        } else {
          console.warn('자동 라벨링 결과에 boxes가 없음')
          console.log('result 전체 구조:', result)
        }

        boundingBoxes.value = boxes
        console.log(`자동 라벨링 결과에서 ${boxes.length}개의 바운딩 박스를 로드했습니다.`)
        console.log('최종 boundingBoxes:', boundingBoxes.value)
      }

      selectedBoxIndex.value = -1
      hasChanges.value = false // 새 이미지 로드 시 변경사항 초기화
    }

    const processDetectionBox = (detection, originalWidth, originalHeight) => {
      console.log('processDetectionBox 입력:', {
        detection,
        originalWidth,
        originalHeight,
        displayImageSize: { width: imageWidth.value, height: imageHeight.value }
      })

      // 원본 이미지 크기 검증
      if (!originalWidth || !originalHeight || originalWidth <= 0 || originalHeight <= 0) {
        console.warn('유효하지 않은 원본 이미지 크기:', { originalWidth, originalHeight })
        return null
      }

      // 화면 표시 이미지 크기 검증
      if (!imageWidth.value || !imageHeight.value || imageWidth.value <= 0 || imageHeight.value <= 0) {
        console.warn('유효하지 않은 표시 이미지 크기:', {
          imageWidth: imageWidth.value,
          imageHeight: imageHeight.value
        })
        return null
      }

      const conf = detection.confidence || detection.conf
      const className = detection.class_name || detection.label || 'unknown'

      let displayX, displayY, displayWidth, displayHeight, originalX, originalY, originalWidth_px, originalHeight_px

      // 🎯 우선순위 1: 정규화된 좌표 사용 (가장 정확함)
      if (detection.normalized_coords && Array.isArray(detection.normalized_coords) && detection.normalized_coords.length === 4) {
        const [xCenterNorm, yCenterNorm, widthNorm, heightNorm] = detection.normalized_coords

        console.log('정규화된 좌표 사용:', {
          normalized: { xCenterNorm, yCenterNorm, widthNorm, heightNorm },
          originalSize: { originalWidth, originalHeight },
          displaySize: { width: imageWidth.value, height: imageHeight.value }
        })

        // 정규화된 좌표 유효성 검사
        if (xCenterNorm < 0 || xCenterNorm > 1 || yCenterNorm < 0 || yCenterNorm > 1 ||
            widthNorm <= 0 || widthNorm > 1 || heightNorm <= 0 || heightNorm > 1) {
          console.warn('유효하지 않은 정규화된 좌표:', { xCenterNorm, yCenterNorm, widthNorm, heightNorm })
          return null
        }

        // 정규화된 좌표 → 원본 크기 기준 픽셀 좌표
        const xCenterOriginal = xCenterNorm * originalWidth
        const yCenterOriginal = yCenterNorm * originalHeight
        const boxWidthOriginal = widthNorm * originalWidth
        const boxHeightOriginal = heightNorm * originalHeight

        // 원본 좌상단 좌표
        originalX = xCenterOriginal - boxWidthOriginal / 2
        originalY = yCenterOriginal - boxHeightOriginal / 2
        originalWidth_px = boxWidthOriginal
        originalHeight_px = boxHeightOriginal

        // 원본 크기 → 화면 표시 크기로 변환
        displayX = (originalX / originalWidth) * imageWidth.value
        displayY = (originalY / originalHeight) * imageHeight.value
        displayWidth = (originalWidth_px / originalWidth) * imageWidth.value
        displayHeight = (originalHeight_px / originalHeight) * imageHeight.value

        console.log('정규화된 좌표 변환:', {
          normalized: { xCenterNorm, yCenterNorm, widthNorm, heightNorm },
          originalPixel: { xCenterOriginal, yCenterOriginal, boxWidthOriginal, boxHeightOriginal },
          originalCoords: { originalX, originalY, originalWidth_px, originalHeight_px },
          displayCoords: { displayX, displayY, displayWidth, displayHeight }
        })

      } else if (detection.bbox && Array.isArray(detection.bbox) && detection.bbox.length === 4) {
        // 🎯 우선순위 2: 절대좌표 사용 (백업)
        const [x, y, w, h] = detection.bbox

        console.log('절대좌표 사용 (백업):', {
          bbox: detection.bbox,
          x, y, w, h,
          originalSize: { originalWidth, originalHeight },
          displaySize: { width: imageWidth.value, height: imageHeight.value }
        })

        // 좌표 유효성 검사
        if (typeof x !== 'number' || typeof y !== 'number' ||
            typeof w !== 'number' || typeof h !== 'number' ||
            isNaN(x) || isNaN(y) || isNaN(w) || isNaN(h)) {
          console.warn('유효하지 않은 절대좌표:', { x, y, w, h })
          return null
        }

        // 박스 크기 유효성 검사
        if (w <= 0 || h <= 0) {
          console.warn('유효하지 않은 박스 크기:', { w, h })
          return null
        }

        // 원본 좌표 정보 저장
        originalX = x
        originalY = y
        originalWidth_px = w
        originalHeight_px = h

        // 원본 크기에서 화면 표시 크기로 스케일링
        const scaleX = imageWidth.value / originalWidth
        const scaleY = imageHeight.value / originalHeight

        displayX = x * scaleX
        displayY = y * scaleY
        displayWidth = w * scaleX
        displayHeight = h * scaleY

        console.log('절대좌표 스케일링:', {
          scaleFactors: { scaleX: scaleX.toFixed(4), scaleY: scaleY.toFixed(4) },
          originalCoords: { x, y, w, h },
          displayCoords: { displayX, displayY, displayWidth, displayHeight }
        })

      } else {
        console.warn('좌표 정보가 없음:', detection)
        return null
      }

      // 화면 표시 이미지 경계 내로 제한
      const finalX = Math.max(0, Math.min(displayX, imageWidth.value - displayWidth))
      const finalY = Math.max(0, Math.min(displayY, imageHeight.value - displayHeight))
      const finalWidth = Math.min(displayWidth, imageWidth.value - finalX)
      const finalHeight = Math.min(displayHeight, imageHeight.value - finalY)

      console.log('최종 표시 좌표:', {
        beforeClamp: { displayX, displayY, displayWidth, displayHeight },
        afterClamp: { finalX, finalY, finalWidth, finalHeight }
      })

      // 최종 크기 검사
      if (finalWidth <= 0 || finalHeight <= 0) {
        console.warn('표시할 수 없는 박스 크기:', { finalWidth, finalHeight })
        return null
      }

      const box = {
        x: finalX,
        y: finalY,
        width: finalWidth,
        height: finalHeight,
        label: className,
        isLowConfidence: conf !== undefined && conf < 0.5,
        // 정규화된 좌표 저장 (우선순위: 서버 제공 > 계산된 값)
        normalized_coords: detection.normalized_coords || [
          (originalX + originalWidth_px / 2) / originalWidth,  // x_center_norm
          (originalY + originalHeight_px / 2) / originalHeight, // y_center_norm
          originalWidth_px / originalWidth,   // width_norm
          originalHeight_px / originalHeight  // height_norm
        ],
        // 원본 좌표 정보도 저장 (나중에 저장할 때 사용)
        originalBbox: [originalX, originalY, originalWidth_px, originalHeight_px]
      }

      // 신뢰도가 있는 경우에만 신뢰도 정보 추가
      if (conf !== undefined) {
        box.confidence = conf
        box.confidenceText = `${Math.round(conf * 100)}%`
      }

      console.log('생성된 박스:', box)
      return box
    }

    // 저장된 라벨 파일을 읽어오는 함수
    const loadSavedLabels = async () => {
      if (!props.currentResult || !props.projectPath) return null

      const baseFilename = props.currentResult.filename.replace(/\.[^/.]+$/, "")
      const labelFilename = `${baseFilename}.txt`
      const labelFilePath = `${props.projectPath}/labels/${labelFilename}`

      try {
        // 라벨 파일이 존재하는지 확인하고 읽어오기
        const response = await fetch(`${API_SERVER}/api/read-label-file`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            labelFilePath: labelFilePath
          })
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success && data.content) {
            // YOLO 형식 라벨 파일을 파싱하여 바운딩 박스로 변환
            // 원본 이미지 크기를 사용 (라벨 파일은 항상 원본 크기 기준으로 정규화됨)
            const originalWidth = props.currentResult?.width || imageWidth.value
            const originalHeight = props.currentResult?.height || imageHeight.value
            return parseYoloLabels(data.content, originalWidth, originalHeight)
          }
        } else if (response.status === 404) {
          // 라벨 파일이 없는 경우 - 정상적인 상황
          console.log('저장된 라벨 파일이 없습니다. 자동 라벨링 결과만 표시합니다.')
        } else {
          console.warn('라벨 파일 읽기 실패:', response.status)
        }
      } catch (error) {
        console.warn('라벨 파일 읽기 중 오류:', error.message)
      }

      return null
    }

    // YOLO 형식 라벨을 바운딩 박스로 변환하는 함수
    const parseYoloLabels = (labelContent, originalWidth, originalHeight) => {
      const lines = labelContent.trim().split('\n').filter(line => line.trim())
      const boxes = []

      // 현재 프로젝트에서 사용 중인 클래스를 정렬하여 사용
      const availableClasses = props.availableClassesFromParent || []
      console.log('파싱에 사용할 클래스 순서:', availableClasses)

      // 화면 표시 이미지 크기 검증
      if (!imageWidth.value || !imageHeight.value || imageWidth.value <= 0 || imageHeight.value <= 0) {
        console.warn('유효하지 않은 표시 이미지 크기:', {
          imageWidth: imageWidth.value,
          imageHeight: imageHeight.value
        })
        return boxes
      }

      // 좌표 스케일링 팩터 계산
      const scaleX = imageWidth.value / originalWidth
      const scaleY = imageHeight.value / originalHeight

      console.log('라벨 파싱 스케일링 정보:', {
        originalSize: { originalWidth, originalHeight },
        displaySize: { width: imageWidth.value, height: imageHeight.value },
        scaleFactors: { scaleX: scaleX.toFixed(4), scaleY: scaleY.toFixed(4) }
      })

      lines.forEach(line => {
        const parts = line.trim().split(/\s+/)
        if (parts.length < 5) return

        try {
          const classIndex = parseInt(parts[0])
          const xCenterNorm = parseFloat(parts[1])
          const yCenterNorm = parseFloat(parts[2])
          const widthNorm = parseFloat(parts[3])
          const heightNorm = parseFloat(parts[4])

          // 정규화된 좌표를 원본 이미지 크기 기준 픽셀 좌표로 변환
          const xCenterOriginal = xCenterNorm * originalWidth
          const yCenterOriginal = yCenterNorm * originalHeight
          const boxWidthOriginal = widthNorm * originalWidth
          const boxHeightOriginal = heightNorm * originalHeight

          // 원본 좌상단 좌표 계산
          const xOriginal = xCenterOriginal - boxWidthOriginal / 2
          const yOriginal = yCenterOriginal - boxHeightOriginal / 2

          // 화면 표시 크기로 스케일링
          const xScaled = xOriginal * scaleX
          const yScaled = yOriginal * scaleY
          const widthScaled = boxWidthOriginal * scaleX
          const heightScaled = boxHeightOriginal * scaleY

          // 화면 표시 이미지 경계 내로 제한
          const x = Math.max(0, Math.min(xScaled, imageWidth.value - widthScaled))
          const y = Math.max(0, Math.min(yScaled, imageHeight.value - heightScaled))
          const width = Math.min(widthScaled, imageWidth.value - x)
          const height = Math.min(heightScaled, imageHeight.value - y)

          console.log('YOLO 라벨 파싱:', {
            line: line,
            normalized: { xCenterNorm, yCenterNorm, widthNorm, heightNorm },
            originalPixel: { xCenterOriginal, yCenterOriginal, boxWidthOriginal, boxHeightOriginal },
            originalCoords: { xOriginal, yOriginal },
            scaledCoords: { xScaled, yScaled, widthScaled, heightScaled },
            final: { x, y, width, height }
          })

          // 클래스 이름 결정 - 정확한 인덱스 매핑
          let className = 'unknown'
          if (classIndex >= 0 && classIndex < availableClasses.length) {
            className = availableClasses[classIndex]
          } else {
            console.warn(`잘못된 클래스 인덱스 ${classIndex}. 사용 가능한 클래스 수: ${availableClasses.length}, 클래스: ${availableClasses}`)
            // 잘못된 인덱스인 경우 'unknown'으로 처리하되 첫 번째 클래스가 있으면 사용
            if (availableClasses.length > 0) {
              className = availableClasses[0]
            }
          }

          const box = {
            x: x,
            y: y,
            width: width,
            height: height,
            label: className,
            // 프로젝트 로드 시에는 신뢰도 정보를 포함하지 않음
            isLowConfidence: false,
            color: getClassColor(className, classColors.value),
            // 원본 좌표 정보도 저장 (편집 후 저장할 때 사용)
            originalBbox: [xOriginal, yOriginal, boxWidthOriginal, boxHeightOriginal]
          }

          boxes.push(box)
        } catch (error) {
          console.warn('라벨 라인 파싱 오류:', line, error)
        }
      })

      return boxes
    }

    // 리사이즈 핸들 위치 계
                const getResizeHandles = (box) => {
      if (!box) return {}

      // 바운딩 박스 변경을 감지하기 위해 리액티브 참조 추가
      const currentBox = boundingBoxes.value[selectedBoxIndex.value]
      if (currentBox && (currentBox.x !== box.x || currentBox.y !== box.y ||
                         currentBox.width !== box.width || currentBox.height !== box.height)) {
        box = currentBox
      }

      return {
        'nw': { x: box.x, y: box.y, color: '#4CAF50', cursor: 'nw-resize' },
        'n': { x: box.x + box.width / 2, y: box.y, color: '#2196F3', cursor: 'n-resize' },
        'ne': { x: box.x + box.width, y: box.y, color: '#4CAF50', cursor: 'ne-resize' },
        'w': { x: box.x, y: box.y + box.height / 2, color: '#2196F3', cursor: 'w-resize' },
        'e': { x: box.x + box.width, y: box.y + box.height / 2, color: '#2196F3', cursor: 'e-resize' },
        'sw': { x: box.x, y: box.y + box.height, color: '#4CAF50', cursor: 'sw-resize' },
        's': { x: box.x + box.width / 2, y: box.y + box.height, color: '#2196F3', cursor: 's-resize' },
        'se': { x: box.x + box.width, y: box.y + box.height, color: '#4CAF50', cursor: 'se-resize' }
      }
        }

    // 선택된 박스의 리사이즈 핸들을 리액티브하게 계산
    const currentResizeHandles = computed(() => {
      if (selectedBoxIndex.value < 0 || !boundingBoxes.value[selectedBoxIndex.value]) {
        return {}
      }
      return getResizeHandles(boundingBoxes.value[selectedBoxIndex.value])
    })

        // 이동 핸들 위치 계산
    const getMoveHandlePosition = (box) => {
      return {
        x: box.x + box.width / 2,
        y: box.y + box.height / 2
      }
    }

        // 박스 테두리 두께 계산
    const getBoxStrokeWidth = (index) => {
      // 숨겨진 박스는 더 두껍게 표시하여 잘 보이도록 함
      if (hiddenBoxes.value.has(index)) {
        return 2 // 숨겨진 박스는 기본 두께보다 두껍게
      }

      if (props.thickBoxMode) {
        // 굵은 모드 - 기존의 얇은 상태 두께 사용
        if (selectedBoxIndex.value === index) {
          return 5 // 주요 선택된 박스는 가장 두껍게
        } else if (selectedBoxIndices.value.has(index)) {
          return 4 // 다중 선택된 박스는 중간 두께
        } else {
          return 3 // 일반 박스는 기본 두께
        }
      } else {
        // 얇은 모드 - 모든 박스를 1로 설정
        return 1
      }
    }

            // 이미지 해상도 기반 스케일 팩터 계산
    const getResolutionScaleFactor = () => {
      if (!imageWidth.value || !imageHeight.value) return 1

      // 이미지 해상도를 기준으로 한 기본 스케일 계산
      const imageArea = imageWidth.value * imageHeight.value
      const referenceArea = 1920 * 1080 // 기준 해상도 FHD
      const lowResThreshold = 640 * 480 // 저해상도 임계값

      // 면적 비율의 제곱근으로 스케일 팩터 계산
      const areRatio = imageArea / referenceArea
      let resolutionFactor = Math.sqrt(areRatio)

      // 640×480 미만일 때는 강제로 작은 값 적용
      if (imageArea < lowResThreshold) {
        resolutionFactor = Math.min(0.4, resolutionFactor)
      }

      // FHD에서 더 크게 보이도록 기본 스케일을 1.2배로 조정
      resolutionFactor = resolutionFactor * 1.2

      // 표시 스케일은 역방향으로 적용 (확대하면 UI 요소는 상대적으로 작게)
      // Stage의 실제 scale을 사용 (마우스 휠 확대/축소 반영)
      const displayFactor = 1 / stageScale.value

      // 최종 스케일 팩터: 해상도가 클수록 큰 값, 표시 스케일이 클수록 작은 값
      return Math.max(0.25, Math.min(3.5, resolutionFactor * displayFactor))
    }

        // 편집점 크기 계산 (이미지 해상도와 표시 스케일 모두 고려)
    const getHandleRadius = (baseRadius) => {
      const imageArea = imageWidth.value * imageHeight.value
      const imageWidth = imageWidth.value
      const imageHeight = imageHeight.value

      // 해상도별 임계값 정의
      const lowResThreshold = 640 * 480
      const hdThreshold = 1280 * 720
      const fhdThreshold = 1920 * 1080
      const qhdThreshold = 2560 * 1440
      const uhdThreshold = 3840 * 2160

                  // 해상도별 편집점 크기 조정 (전체적으로 1.5배 더 크게)
      let handleScale = 1.0

      if (imageArea <= lowResThreshold) {
        // 640×480 이하: 최소 크기 (1.5배 증가)
        handleScale = 0.675
      } else if (imageArea <= hdThreshold) {
        // HD (1280×720) 이하: 작은 크기 (1.5배 증가)
        handleScale = 1.35
      } else if (imageArea <= fhdThreshold) {
        // FHD (1920×1080) 이하: 중간 크기 (2배 증가)
        handleScale = 4.5
      } else if (imageArea <= qhdThreshold) {
        // QHD (2560×1440) 이하: 큰 크기 (1.5배 증가)
        handleScale = 3.3
      } else if (imageArea <= uhdThreshold) {
        // UHD (3840×2160) 이하: 매우 큰 크기 (1.5배 증가)
        handleScale = 4.5
      } else {
        // UHD 이상: 최대 크기 (1.5배 증가)
        handleScale = 5.4
      }

      // 표시 스케일도 고려하여 최종 크기 계산
      // 이미지 확대 시 핸들을 더 작게 (0.15배까지 축소)
      // Stage의 실제 scale을 사용 (마우스 휠 확대/축소 반영)
      const displayFactor = 1 / stageScale.value
      const finalScale = handleScale * Math.max(0.15, Math.min(2.5, displayFactor))

      const scaledRadius = baseRadius * finalScale
      return Math.max(3.0, Math.min(30, scaledRadius))
    }

    // 작은 편집점 크기 계산 (미세한 객체 라벨링을 위해 더 작게)
    const getSmallHandleRadius = () => {
      const imageArea = imageWidth.value * imageHeight.value

      // 해상도별 임계값 정의
      const lowResThreshold = 640 * 480
      const hdThreshold = 1280 * 720
      const fhdThreshold = 1920 * 1080
      const qhdThreshold = 2560 * 1440
      const uhdThreshold = 3840 * 2160

                  // 해상도별 작은 편집점 크기 조정 (전체적으로 1.5배 더 크게)
      let smallHandleScale = 1.0

      if (imageArea <= lowResThreshold) {
        // 640×480 이하: 매우 작은 크기 (1.5배 증가)
        smallHandleScale = 0.45
      } else if (imageArea <= hdThreshold) {
        // HD (1280×720) 이하: 작은 크기 (1.5배 증가)
        smallHandleScale = 1.05
      } else if (imageArea <= fhdThreshold) {
        // FHD (1920×1080) 이하: 중간 크기 (2배 증가)
        smallHandleScale = 3.0
      } else if (imageArea <= qhdThreshold) {
        // QHD (2560×1440) 이하: 큰 크기 (1.5배 증가)
        smallHandleScale = 2.25
      } else if (imageArea <= uhdThreshold) {
        // UHD (3840×2160) 이하: 매우 큰 크기 (1.5배 증가)
        smallHandleScale = 3.0
      } else {
        // UHD 이상: 최대 크기 (1.5배 증가)
        smallHandleScale = 3.75
      }

      // 표시 스케일도 고려하여 최종 크기 계산
      // 이미지 확대 시 작은 핸들을 더 작게 (0.1배까지 축소)
      // Stage의 실제 scale을 사용 (마우스 휠 확대/축소 반영)
      const displayFactor = 1 / stageScale.value
      const finalScale = smallHandleScale * Math.max(0.1, Math.min(2.0, displayFactor))

      const smallRadius = 1.5 * finalScale
      return Math.max(1.5, Math.min(12, smallRadius))
    }

    // 라벨 텍스트 크기 계산 (이미지 해상도와 표시 스케일 모두 고려)
    const getLabelFontSize = (baseFontSize) => {
      const imageArea = imageWidth.value * imageHeight.value

      // 해상도별 임계값 정의
      const lowResThreshold = 640 * 480
      const hdThreshold = 1280 * 720
      const fhdThreshold = 1920 * 1080
      const qhdThreshold = 2560 * 1440
      const uhdThreshold = 3840 * 2160

      // 해상도별 폰트 크기 조정
      let fontScale = 1.0

      if (imageArea <= lowResThreshold) {
        // 640×480 이하: 최소 폰트 크기
        fontScale = 0.5
      } else if (imageArea <= hdThreshold) {
        // HD (1280×720) 이하: 작은 폰트
        fontScale = 0.8
      } else if (imageArea <= fhdThreshold) {
        // FHD (1920×1080) 이하: 중간 폰트
        fontScale = 1.2
      } else if (imageArea <= qhdThreshold) {
        // QHD (2560×1440) 이하: 큰 폰트
        fontScale = 1.6
      } else if (imageArea <= uhdThreshold) {
        // UHD (3840×2160) 이하: 매우 큰 폰트
        fontScale = 2.0
      } else {
        // UHD 이상: 최대 폰트
        fontScale = 2.5
      }

      // 표시 스케일도 고려하여 최종 크기 계산
      // 이미지 확대 시 라벨 폰트도 작게 (0.3배까지 축소, 가독성 유지)
      // Stage의 실제 scale을 사용 (마우스 휠 확대/축소 반영)
      const displayFactor = 1 / stageScale.value
      const finalScale = fontScale * Math.max(0.3, Math.min(1.8, displayFactor))

      const scaledSize = baseFontSize * finalScale
      return Math.max(6, Math.min(32, scaledSize))
    }

    // 라벨 배경 크기 계산 (텍스트 길이와 폰트 크기에 따라)
    const getLabelBackgroundWidth = (text, fontSize) => {
      const imageArea = imageWidth.value * imageHeight.value

      // 해상도별 임계값 정의
      const lowResThreshold = 640 * 480
      const hdThreshold = 1280 * 720
      const fhdThreshold = 1920 * 1080
      const qhdThreshold = 2560 * 1440
      const uhdThreshold = 3840 * 2160

      // 해상도별 패딩 조정
      let paddingScale = 1.0

      if (imageArea <= lowResThreshold) {
        // 640×480 이하: 최소 패딩
        paddingScale = 0.4
      } else if (imageArea <= hdThreshold) {
        // HD (1280×720) 이하: 작은 패딩
        paddingScale = 0.6
      } else if (imageArea <= fhdThreshold) {
        // FHD (1920×1080) 이하: 중간 패딩
        paddingScale = 0.8
      } else if (imageArea <= qhdThreshold) {
        // QHD (2560×1440) 이하: 큰 패딩
        paddingScale = 1.0
      } else if (imageArea <= uhdThreshold) {
        // UHD (3840×2160) 이하: 매우 큰 패딩
        paddingScale = 1.2
      } else {
        // UHD 이상: 최대 패딩
        paddingScale = 1.4
      }

      const padding = Math.max(4, fontSize * paddingScale)
      const charWidth = fontSize * (imageArea <= lowResThreshold ? 0.7 : 0.6)
      return text.length * charWidth + padding
    }



    // 라벨 배경 높이 계산
    const getLabelBackgroundHeight = (fontSize) => {
      const imageArea = imageWidth.value * imageHeight.value

      // 해상도별 임계값 정의
      const lowResThreshold = 640 * 480
      const hdThreshold = 1280 * 720
      const fhdThreshold = 1920 * 1080
      const qhdThreshold = 2560 * 1440
      const uhdThreshold = 3840 * 2160

      // 해상도별 높이 패딩 조정
      let heightPaddingScale = 1.0

      if (imageArea <= lowResThreshold) {
        // 640×480 이하: 최소 높이 패딩
        heightPaddingScale = 0.3
      } else if (imageArea <= hdThreshold) {
        // HD (1280×720) 이하: 작은 높이 패딩
        heightPaddingScale = 0.4
      } else if (imageArea <= fhdThreshold) {
        // FHD (1920×1080) 이하: 중간 높이 패딩
        heightPaddingScale = 0.5
      } else if (imageArea <= qhdThreshold) {
        // QHD (2560×1440) 이하: 큰 높이 패딩
        heightPaddingScale = 0.6
      } else if (imageArea <= uhdThreshold) {
        // UHD (3840×2160) 이하: 매우 큰 높이 패딩
        heightPaddingScale = 0.7
      } else {
        // UHD 이상: 최대 높이 패딩
        heightPaddingScale = 0.8
      }

      const padding = Math.max(3, fontSize * heightPaddingScale)
      return fontSize + padding
    }

    // Event handlers
    const selectBox = (index, event) => {
      // Space 키가 눌린 상태에서는 박스 선택을 무시하고 드래그 우선
      if (isSpacePressed.value) {
        console.log('Space 키 눌린 상태 - 박스 선택 무시하고 드래그 처리')
        return
      }

      if (event && event.cancelBubble !== undefined) {
        event.cancelBubble = true
      }

      // 숨겨진 박스는 hover 상태일 때만 클릭 허용
      if (hiddenBoxes.value.has(index) && hoveredBoxIndex.value !== index) {
        console.log(`숨겨진 박스 ${index} 클릭 차단 (hover 상태 아님)`)
        return
      }

      // 편집모드에서 Shift + 클릭인 경우 다중 선택
      if (editMode.value === 'edit' && event?.evt?.shiftKey) {
        const newSelectedIndices = new Set(selectedBoxIndices.value)

        if (newSelectedIndices.has(index)) {
          // 이미 선택된 박스면 선택 해제
          newSelectedIndices.delete(index)
          if (selectedBoxIndex.value === index) {
            // 주요 선택 박스가 해제되면 다른 박스를 주요 선택으로 설정
            selectedBoxIndex.value = newSelectedIndices.size > 0 ? [...newSelectedIndices][0] : -1
          }
        } else {
          // 새로운 박스 선택
          newSelectedIndices.add(index)
          selectedBoxIndex.value = index // 마지막 선택된 박스를 주요 선택으로 설정
        }

                selectedBoxIndices.value = newSelectedIndices

        // 다중 선택 상태 메시지 및 알림창 (2개 이상 선택 시에만 표시)
        if (newSelectedIndices.size > 1) {
          const message = `${newSelectedIndices.size}개의 바운딩 박스가 선택되었습니다`
          emit('status-message', {
            message: message,
            type: 'info',
            icon: 'mdi-selection-multiple'
          })
          // 다중 선택 알림창 표시
          multiSelectMessage.value = message
          multiSelectIcon.value = 'mdi-selection-multiple'
          showMultiSelectSnackbar.value = true
        }
      } else {
        // 일반 단일 선택
        selectedBoxIndex.value = index
        selectedBoxIndices.value = new Set([index]) // 단일 선택도 다중 선택 상태에 포함
      }

      emit('bbox-edit', { index, box: boundingBoxes.value[index] })
    }

    const handleMouseDown = (event) => {
      const stage = event.target.getStage()
      const pos = stage.getPointerPosition()

      console.log('마우스 다운:', {
        isSpacePressed: isSpacePressed.value,
        targetIsStage: event.target === stage,
        targetType: event.target.getClassName?.() || 'unknown'
      })

      // Space 키가 눌린 상태에서는 이미지 영역 내외 관계없이 드래그 시작
      if (isSpacePressed.value) {
        isDraggingStage.value = true
        isDragStarted.value = true
        dragStartPos.value = { x: pos.x, y: pos.y }
        dragStartStagePos.value = { x: stageX.value, y: stageY.value }

        console.log('Space+드래그 시작:', {
          startPos: dragStartPos.value,
          stagePos: dragStartStagePos.value,
          target: event.target.getClassName?.() || 'unknown'
        })

        // Space+드래그 시에는 다른 모든 이벤트를 차단
        event.stopPropagation()
        return
      }

      if (editMode.value === 'draw') {
        // 그리기 모드에서 새 박스 그리기 시작
        isDrawing.value = true

        // Stage의 실제 변환 상태를 사용하여 정확한 이미지 좌표 계산
        const stageScale = stage.scaleX() || 1
        const stageOffsetX = stage.x() || 0
        const stageOffsetY = stage.y() || 0

        startPoint.value = {
          x: (pos.x - stageOffsetX) / stageScale,
          y: (pos.y - stageOffsetY) / stageScale
        }
        tempBox.value = {
          x: startPoint.value.x,
          y: startPoint.value.y,
          width: 0,
          height: 0
        }
      } else if (event.target === stage) {
        // 배경 클릭 시 선택 해제
        selectedBoxIndex.value = -1
        selectedBoxIndices.value = new Set()
      }
    }

        const handleMouseMove = (event) => {
      const stage = event.target.getStage()
      const pos = stage.getPointerPosition()

      // Space+드래그로 스테이지 이동 (최우선 처리)
      if (isDraggingStage.value && dragStartPos.value && dragStartStagePos.value) {
        const deltaX = pos.x - dragStartPos.value.x
        const deltaY = pos.y - dragStartPos.value.y
        const newX = dragStartStagePos.value.x + deltaX
        const newY = dragStartStagePos.value.y + deltaY

        // Stage 위치 업데이트
        stageX.value = newX
        stageY.value = newY

        // Konva Stage에 직접 위치 적용
        const stageRef = stage.value?.getStage()
        if (stageRef) {
          stageRef.position({ x: newX, y: newY })
        }

        console.log('드래그 중:', { newX, newY, deltaX, deltaY })

        // Space 드래그 중에는 다른 처리를 하지 않음
        event.stopPropagation()
        return
      }

      // Stage의 실제 변환 상태를 사용하여 정확한 좌표 계산
      const stageScale = stage.scaleX() || 1
      const stageOffsetX = stage.x() || 0
      const stageOffsetY = stage.y() || 0

      // 항상 현재 마우스 위치를 이미지 좌표계로 변환하여 저장
      const imageX = (pos.x - stageOffsetX) / stageScale
      const imageY = (pos.y - stageOffsetY) / stageScale

      // 이미지 영역 내에서만 마우스 위치 업데이트
      if (imageX >= 0 && imageX <= imageWidth.value && imageY >= 0 && imageY <= imageHeight.value) {
        currentMousePos.value = { x: imageX, y: imageY }
      }

      // 그리기 모드에서 임시 박스 업데이트
      if (!isDrawing.value || !startPoint.value) return

      const currentPoint = {
        x: imageX,
        y: imageY
      }

      const x = Math.min(startPoint.value.x, currentPoint.x)
      const y = Math.min(startPoint.value.y, currentPoint.y)
      const width = Math.abs(currentPoint.x - startPoint.value.x)
      const height = Math.abs(currentPoint.y - startPoint.value.y)

      tempBox.value = { x, y, width, height }
    }

    // Native DOM pointermove - 드래그 중에도 크로스헤어 업데이트 보장
    const handleNativePointerMove = (event) => {
      const stageNode = stage.value?.getStage()
      if (!stageNode) return

      const container = stageNode.container()
      if (!container) return

      const rect = container.getBoundingClientRect()
      const scaleX = stageNode.scaleX() || 1
      const offsetX = stageNode.x() || 0
      const offsetY = stageNode.y() || 0

      const pointerX = event.clientX - rect.left
      const pointerY = event.clientY - rect.top

      const imageX = (pointerX - offsetX) / scaleX
      const imageY = (pointerY - offsetY) / scaleX

      if (imageX >= 0 && imageX <= imageWidth.value && imageY >= 0 && imageY <= imageHeight.value) {
        currentMousePos.value = { x: imageX, y: imageY }
      }
    }

    const handleMouseUp = async (event) => {
      // Space+드래그 종료 (최우선 처리)
      if (isDraggingStage.value) {
        isDraggingStage.value = false
        dragStartPos.value = null
        dragStartStagePos.value = null
        console.log('Space+드래그 종료')
        event?.stopPropagation()
        return
      }

      if (!isDrawing.value || !tempBox.value) return

      // 최소 크기 제한을 제거하고 모든 크기의 박스를 허용
      if (tempBox.value.width > 0 && tempBox.value.height > 0) {
        // 작업 전 상태 저장
        saveToHistory()

        // 새 박스 추가
        const availableClasses = props.availableClassesFromParent
        const className = availableClasses.length > 0 ? availableClasses[selectedClassIndex.value] : 'unknown'

        const newBox = {
          x: tempBox.value.x,
          y: tempBox.value.y,
          width: tempBox.value.width,
          height: tempBox.value.height,
          label: className,
          // 새로 그린 박스에는 신뢰도 정보를 포함하지 않음
          isLowConfidence: false,
          color: getClassColor(className, classColors.value)
        }

        boundingBoxes.value.push(newBox)
        selectedBoxIndex.value = boundingBoxes.value.length - 1
        hasChanges.value = true // 변경사항 표시

        emit('bbox-change', {
          action: 'add',
          box: newBox,
          index: selectedBoxIndex.value
        })

        emit('status-message', {
          message: `새 바운딩 박스가 추가되었습니다 (클래스: ${className}). T키로 저장하세요`,
          type: 'success',
          icon: 'mdi-plus-box'
        })
      }

            // 그리기 상태 초기화
      isDrawing.value = false
      startPoint.value = null
      tempBox.value = null
      editMode.value = 'edit' // 그리기 완료 후 편집 모드로 전환
    }

    const handleResize = (event, boxIndex, handleType) => {
      const box = boundingBoxes.value[boxIndex]
      if (!box) return

      // 처음 리사이즈 시작할 때만 히스토리 저장 (여러 번 저장 방지)
      if (!event.target.attrs.isResizing) {
        saveToHistory()
        event.target.attrs.isResizing = true
      }

      // 현재 마우스 포인터 위치를 가져옴
      const stage = event.target.getStage()
      const pointerPos = stage.getPointerPosition()

      // Stage의 실제 변환 상태를 사용하여 이미지 좌표 계산
      const stageScale = stage.scaleX() || 1
      const stageOffsetX = stage.x() || 0
      const stageOffsetY = stage.y() || 0

      const realX = (pointerPos.x - stageOffsetX) / stageScale
      const realY = (pointerPos.y - stageOffsetY) / stageScale

      // 박스 변경 전 상태 저장
      const originalBox = { ...box }

      // 핸들 타입에 따라 박스 크기 조정
      switch (handleType) {
        case 'nw':
          box.width = originalBox.width + (originalBox.x - realX)
          box.height = originalBox.height + (originalBox.y - realY)
          box.x = realX
          box.y = realY
          break
        case 'n':
          box.height = originalBox.height + (originalBox.y - realY)
          box.y = realY
          break
        case 'ne':
          box.width = realX - originalBox.x
          box.height = originalBox.height + (originalBox.y - realY)
          box.y = realY
          break
        case 'w':
          box.width = originalBox.width + (originalBox.x - realX)
          box.x = realX
          break
        case 'e':
          box.width = realX - originalBox.x
          break
        case 'sw':
          box.width = originalBox.width + (originalBox.x - realX)
          box.x = realX
          box.height = realY - originalBox.y
          break
        case 's':
          box.height = realY - originalBox.y
          break
        case 'se':
          box.width = realX - originalBox.x
          box.height = realY - originalBox.y
          break
      }

      // 최소 크기 제한 - 음수가 되지 않도록만 제한
      if (box.width < 0) box.width = 0
      if (box.height < 0) box.height = 0

      // 편집된 박스의 기존 좌표 정보 제거 (현재 화면 좌표를 사용하도록)
      delete box.normalized_coords
      delete box.originalBbox

      hasChanges.value = true // 변경사항 표시

      // 박스 변경을 즉시 반영하여 핸들 위치가 업데이트되도록 함
      nextTick(() => {
        emit('bbox-change', {
          action: 'resize',
          box: box,
          index: boxIndex
        })
      })
    }

    const handleResizeEnd = async (event, boxIndex) => {
      const box = boundingBoxes.value[boxIndex]
      if (!box) return

      // 리사이즈 플래그 초기화
      if (event.target.attrs) {
        event.target.attrs.isResizing = false
      }

        emit('status-message', {
          message: `바운딩 박스 크기가 조정되었습니다. T키로 저장하세요`,
          type: 'success',
          icon: 'mdi-resize'
        })
    }

    const handleMove = (event, boxIndex) => {
      const box = boundingBoxes.value[boxIndex]
      if (!box) return

      // 처음 이동 시작할 때만 히스토리 저장 (여러 번 저장 방지)
      if (!event.target.attrs.isMoving) {
        saveToHistory()
        event.target.attrs.isMoving = true
      }

      // 현재 마우스 포인터 위치를 가져옴
      const stage = event.target.getStage()
      const pointerPos = stage.getPointerPosition()

      // Stage의 실제 변환 상태를 사용하여 이미지 좌표 계산
      const stageScale = stage.scaleX() || 1
      const stageOffsetX = stage.x() || 0
      const stageOffsetY = stage.y() || 0

      const realCenterX = (pointerPos.x - stageOffsetX) / stageScale
      const realCenterY = (pointerPos.y - stageOffsetY) / stageScale

      // 박스의 중심을 기준으로 새 위치 계산
      box.x = realCenterX - box.width / 2
      box.y = realCenterY - box.height / 2

      // 이미지 경계 내로 제한
      box.x = Math.max(0, Math.min(box.x, imageWidth.value - box.width))
      box.y = Math.max(0, Math.min(box.y, imageHeight.value - box.height))

      // 편집된 박스의 기존 좌표 정보 제거 (현재 화면 좌표를 사용하도록)
      delete box.normalized_coords
      delete box.originalBbox

      hasChanges.value = true // 변경사항 표시

      emit('bbox-change', {
        action: 'move',
        box: box,
        index: boxIndex
      })
    }

    const handleMoveEnd = async (event, boxIndex) => {
      const box = boundingBoxes.value[boxIndex]
      if (!box) return

      // 이동 플래그 초기화
      if (event.target.attrs) {
        event.target.attrs.isMoving = false
      }

      emit('status-message', {
        message: `바운딩 박스가 이동되었습니다. T키로 저장하세요`,
        type: 'success',
        icon: 'mdi-cursor-move'
      })
    }

    // 바운딩 박스 자체를 드래그하여 이동하는 함수
    const handleBoxMove = (event, boxIndex) => {
      const box = boundingBoxes.value[boxIndex]
      if (!box) return

      // 처음 이동 시작할 때만 히스토리 저장 (여러 번 저장 방지)
      if (!event.target.attrs.isBoxMoving) {
        saveToHistory()
        event.target.attrs.isBoxMoving = true
        // 초기 오프셋 저장 (마우스 위치와 박스 좌상단 모서리의 차이)
        const stage = event.target.getStage()
        const pointerPos = stage.getPointerPosition()
        const stageScale = stage.scaleX() || 1
        const stageOffsetX = stage.x() || 0
        const stageOffsetY = stage.y() || 0
        const realX = (pointerPos.x - stageOffsetX) / stageScale
        const realY = (pointerPos.y - stageOffsetY) / stageScale

        event.target.attrs.moveOffsetX = realX - box.x
        event.target.attrs.moveOffsetY = realY - box.y
      }

      // 현재 마우스 포인터 위치를 가져옴
      const stage = event.target.getStage()
      const pointerPos = stage.getPointerPosition()

      // Stage의 실제 변환 상태를 사용하여 이미지 좌표 계산
      const stageScale = stage.scaleX() || 1
      const stageOffsetX = stage.x() || 0
      const stageOffsetY = stage.y() || 0

      const realX = (pointerPos.x - stageOffsetX) / stageScale
      const realY = (pointerPos.y - stageOffsetY) / stageScale

      // 초기 오프셋을 고려하여 박스 위치 계산
      const offsetX = event.target.attrs.moveOffsetX || box.width / 2
      const offsetY = event.target.attrs.moveOffsetY || box.height / 2

      box.x = realX - offsetX
      box.y = realY - offsetY

      // 이미지 경계 내로 제한
      box.x = Math.max(0, Math.min(box.x, imageWidth.value - box.width))
      box.y = Math.max(0, Math.min(box.y, imageHeight.value - box.height))

      // 편집된 박스의 기존 좌표 정보 제거 (현재 화면 좌표를 사용하도록)
      delete box.normalized_coords
      delete box.originalBbox

      hasChanges.value = true // 변경사항 표시

      // 박스 변경을 즉시 반영하여 핸들 위치가 업데이트되도록 함
      nextTick(() => {
        emit('bbox-change', {
          action: 'move',
          box: box,
          index: boxIndex
        })
      })
    }

    // 바운딩 박스 이동 완료 처리
    const handleBoxMoveEnd = async (event, boxIndex) => {
      const box = boundingBoxes.value[boxIndex]
      if (!box) return

      // 이동 플래그 및 오프셋 초기화
      if (event.target.attrs) {
        event.target.attrs.moveOffsetX = null
        event.target.attrs.moveOffsetY = null
        event.target.attrs.isBoxMoving = false
      }

      emit('status-message', {
        message: `바운딩 박스가 이동되었습니다. T키로 저장하세요`,
        type: 'success',
        icon: 'mdi-cursor-move'
      })
    }

    const handleWheel = (event) => {
      // Ctrl 키가 눌렸을 때만 확대/축소 동작
      if (!event.evt.ctrlKey) {
        return
      }

      event.evt.preventDefault()

      const scaleBy = 1.1
      const stageRef = stage.value?.getStage()
      if (!stageRef) return

      const oldScale = stageRef.scaleX()
      const pointer = stageRef.getPointerPosition()

      const mousePointTo = {
        x: (pointer.x - stageRef.x()) / oldScale,
        y: (pointer.y - stageRef.y()) / oldScale,
      }

      // 휠 방향을 반대로 변경: 위쪽 휠(음수 deltaY)은 확대, 아래쪽 휠(양수 deltaY)은 축소
      const newScale = event.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy

      // 줌 범위 제한 - 저해상도 이미지를 위해 최대 확대 범위 증가
      const clampedScale = Math.max(0.05, Math.min(20, newScale))

      stageRef.scale({ x: clampedScale, y: clampedScale })
      stageScale.value = clampedScale // reactive 변수 업데이트

      const newPos = {
        x: pointer.x - mousePointTo.x * clampedScale,
        y: pointer.y - mousePointTo.y * clampedScale,
      }
      stageRef.position(newPos)
    }

    const handleMouseOver = (event, cursor) => {
      const container = konvaContainer.value
      if (container) {
        container.style.cursor = cursor
      }
    }

    const handleMouseOut = () => {
      const container = konvaContainer.value
      if (container) {
        container.style.cursor = 'crosshair'
      }
    }

    const resetZoom = () => {
      const stageRef = stage.value?.getStage()
      if (!stageRef) return

      calculateDisplaySize()
      stageRef.scale({ x: displayScale.value, y: displayScale.value })
      stageRef.position({ x: stageX.value, y: stageY.value })
      stageScale.value = displayScale.value // reactive 변수 업데이트

      // 줌 인덱스를 기본값(100%)으로 재설정
      currentZoomIndex.value = 4
    }

    const stepZoomIn = (mousePos = null) => {
      const stageRef = stage.value?.getStage()
      if (!stageRef) return

      // 다음 확대 단계로 이동 (순환)
      currentZoomIndex.value = (currentZoomIndex.value + 1) % zoomLevels.length
      const newScale = zoomLevels[currentZoomIndex.value]

      // 마우스 위치 또는 화면 중앙을 기준으로 확대
      const centerX = mousePos ? mousePos.x : containerWidth.value / 2
      const centerY = mousePos ? mousePos.y : containerHeight.value / 2

      const currentScale = stageRef.scaleX()
      const scaleRatio = newScale / currentScale

      // 마우스 위치 기준 확대를 위한 위치 계산
      const currentPos = stageRef.position()
      const newX = centerX - (centerX - currentPos.x) * scaleRatio
      const newY = centerY - (centerY - currentPos.y) * scaleRatio

      stageRef.scale({ x: newScale, y: newScale })
      stageRef.position({ x: newX, y: newY })
      stageScale.value = newScale // reactive 변수 업데이트

      // 확대 레벨 피드백
      const percentage = Math.round(newScale * 100)
      emit('status-message', {
        message: `확대: ${percentage}% (${currentZoomIndex.value + 1}/${zoomLevels.length} 단계)`,
        type: 'info',
        icon: 'mdi-magnify-plus'
      })

      console.log(`단계적 확대: ${percentage}% (${currentZoomIndex.value + 1}/${zoomLevels.length})`)
    }

    const stepZoomOut = (mousePos = null) => {
      const stageRef = stage.value?.getStage()
      if (!stageRef) return

      // 이전 축소 단계로 이동 (순환)
      currentZoomIndex.value = currentZoomIndex.value === 0 ? zoomLevels.length - 1 : currentZoomIndex.value - 1
      const newScale = zoomLevels[currentZoomIndex.value]

      // 마우스 위치 또는 화면 중앙을 기준으로 축소
      const centerX = mousePos ? mousePos.x : containerWidth.value / 2
      const centerY = mousePos ? mousePos.y : containerHeight.value / 2

      const currentScale = stageRef.scaleX()
      const scaleRatio = newScale / currentScale

      // 마우스 위치 기준 축소를 위한 위치 계산
      const currentPos = stageRef.position()
      const newX = centerX - (centerX - currentPos.x) * scaleRatio
      const newY = centerY - (centerY - currentPos.y) * scaleRatio

      stageRef.scale({ x: newScale, y: newScale })
      stageRef.position({ x: newX, y: newY })
      stageScale.value = newScale // reactive 변수 업데이트

      // 축소 레벨 피드백
      const percentage = Math.round(newScale * 100)
      emit('status-message', {
        message: `축소: ${percentage}% (${currentZoomIndex.value + 1}/${zoomLevels.length} 단계)`,
        type: 'info',
        icon: 'mdi-magnify-minus'
      })

      console.log(`단계적 축소: ${percentage}% (${currentZoomIndex.value + 1}/${zoomLevels.length})`)
    }

    const handleImageError = () => {
      console.error('이미지 로드 실패:', getImageSource())
    }

    // 박스 클릭 처리 함수 - 숨겨진 박스는 완전히 클릭 무시
    const handleBoxClick = (clickedIndex, event) => {
      // 숨겨진 박스는 클릭 무시 (listening이 false이므로 여기까지 오지 않지만 안전장치)
      if (hiddenBoxes.value.has(clickedIndex)) {
        return
      }

      // 보이는 박스만 클릭 처리
      selectBox(clickedIndex, event)
    }

    const getSelectedBoxPosition = computed(() => {
      if (selectedBoxIndex.value === -1 || !boundingBoxes.value[selectedBoxIndex.value]) {
        return { x: 0, y: 0, width: 0, height: 0, label: 'Unknown' }
      }
      return boundingBoxes.value[selectedBoxIndex.value]
    })

    const handleWindowResize = () => {
      calculateDisplaySize()
    }

    // 공개 메소들 (MainView에서 호출)
    const toggleEditMode = () => {
      // 편집 모드가 아닐 때만 활성화 가능 (R키로만 해제 가능)
      if (editMode.value !== 'edit') {
        editMode.value = 'edit'
        hasChanges.value = false // 편집모드 진입 시 변경사항 초기화

        // 편집모드 진입 시 바운딩박스가 있으면 첫 번째 박스를 자동 선택하여 편집점 활성화
        if (boundingBoxes.value.length > 0) {
          selectedBoxIndex.value = 0
          emit('bbox-edit', { index: 0, box: boundingBoxes.value[0] })
        }

        // 즉시 emit으로 빠른 알림 표시
        emit('status-message', {
          message: '편집 모드 활성화',
          type: 'info',
          icon: 'mdi-pencil'
        })
      }
    }

        const startDrawingMode = () => {
      // 편집모드가 아닐 때는 그리기 불가
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 바운딩 박스를 그릴 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      editMode.value = 'draw'
      selectedBoxIndex.value = -1
      emit('status-message', {
        message: '박스 그리기 모드 - 드래그하여 새 박스를 그리세요',
        type: 'info',
        icon: 'mdi-plus-box'
      })
    }

    const deleteSelectedBox = async () => {
      // 작업 전 상태 저장
      saveToHistory()

      if (selectedBoxIndices.value.size > 0) {
        // 다중 선택된 박스들을 인덱스 역순으로 정렬하여 삭제 (인덱스 변경 방지)
        const indicesToDelete = [...selectedBoxIndices.value].sort((a, b) => b - a)
        const deletedBoxes = []

        indicesToDelete.forEach(index => {
          if (boundingBoxes.value[index]) {
            // 삭제 전에 박스 정보를 저장
            const boxToDelete = boundingBoxes.value[index]
            deletedBoxes.push(boxToDelete)
            boundingBoxes.value.splice(index, 1)

            emit('bbox-change', {
              action: 'delete',
              box: boxToDelete,  // 삭제된 박스가 아닌 원본 박스 정보 전달
              index: index
            })
          }
        })

        selectedBoxIndex.value = -1
        selectedBoxIndices.value = new Set()
        hasChanges.value = true // 변경사항 표시

        emit('status-message', {
          message: `${deletedBoxes.length}개의 바운딩 박스가 삭제되었습니다. T키로 저장하세요`,
          type: 'success',
          icon: 'mdi-delete'
        })
      } else if (selectedBoxIndex.value !== -1 && boundingBoxes.value[selectedBoxIndex.value]) {
        // 단일 선택 삭제 (기존 로직)
        const deletedBox = boundingBoxes.value[selectedBoxIndex.value]
        const deleteIndex = selectedBoxIndex.value
        boundingBoxes.value.splice(selectedBoxIndex.value, 1)

        emit('bbox-change', {
          action: 'delete',
          box: deletedBox,
          index: deleteIndex
        })

        selectedBoxIndex.value = -1
        selectedBoxIndices.value = new Set()
        hasChanges.value = true // 변경사항 표시

        emit('status-message', {
          message: '바운딩 박스가 삭제되었습니다. T키로 저장하세요',
          type: 'success',
          icon: 'mdi-delete'
        })
      }
    }

            const copySelectedBox = () => {
      // 편집모드가 아닐 때는 복사 불가
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 바운딩 박스를 복사할 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      if (selectedBoxIndices.value.size > 0) {
        // 다중 선택된 박스들 복사
        const selectedBoxes = [...selectedBoxIndices.value].map(index => ({ ...boundingBoxes.value[index] }))

        // 복사 타입과 데이터를 함께 저장
        const newCopiedBox = {
          type: selectedBoxes.length > 1 ? 'multiple' : 'single',
          data: selectedBoxes,
          count: selectedBoxes.length
        }

        // MainView의 copiedBox 상태 업데이트
        emit('update-copied-box', newCopiedBox)

        // 전용 복사 알림창 표시
        multiSelectMessage.value = `${selectedBoxes.length}개의 바운딩 박스가 복사되었습니다`
        multiSelectIcon.value = 'mdi-content-copy'
        showMultiSelectSnackbar.value = true

        emit('status-message', {
          message: `${selectedBoxes.length}개의 바운딩 박스가 복사되었습니다`,
          type: 'success',
          icon: 'mdi-content-copy'
        })
      } else if (selectedBoxIndex.value !== -1 && boundingBoxes.value[selectedBoxIndex.value]) {
        // 단일 선택 복사 (기존 로직)
        const newCopiedBox = {
          type: 'single',
          data: [{ ...boundingBoxes.value[selectedBoxIndex.value] }],
          count: 1
        }

        // MainView의 copiedBox 상태 업데이트
        emit('update-copied-box', newCopiedBox)

        // 전용 복사 알림창 표시
        multiSelectMessage.value = '1개의 바운딩 박스가 복사되었습니다'
        multiSelectIcon.value = 'mdi-content-copy'
        showMultiSelectSnackbar.value = true

        emit('status-message', {
          message: '바운딩 박스가 복사되었습니다',
          type: 'success',
          icon: 'mdi-content-copy'
        })
      }
    }

    const exitEditMode = async () => {
      if (editMode.value === 'edit') {
        console.log('편집모드 해제 - 변경사항 상태:', hasChanges.value)
        console.log('현재 바운딩 박스 개수:', boundingBoxes.value.length)

        let saveMessage = '편집 모드 비활성화'

        // 변경사항 상태에 따른 메시지 설정
        if (hasChanges.value) {
          saveMessage = '편집 모드 비활성화 - 변경사항이 있습니다. T키로 저장하세요'
        } else {
          saveMessage = '편집 모드 비활성화 - 변경사항이 없습니다'
        }

        editMode.value = 'view'
        selectedBoxIndex.value = -1
        selectedBoxIndices.value = new Set()

        // 즉시 emit으로 빠른 알림 표시
        emit('status-message', {
          message: saveMessage,
          type: 'success',
          icon: 'mdi-eye'
        })
      }
    }

        // 수동 저장 기능 (N키로 호출)
    const saveBoundingBoxes = async () => {
      try {
        console.log('저장 시도 - 변경사항 상태:', hasChanges.value)
        console.log('현재 바운딩 박스 개수:', boundingBoxes.value.length)
        console.log('현재 편집모드:', editMode.value)

        if (!props.currentResult || !props.currentResult.filename) {
          emit('status-message', {
            message: '현재 이미지 정보가 없어 저장할 수 없습니다',
            type: 'warning',
            icon: 'mdi-alert'
          })
          return
        }

        if (!hasChanges.value) {
          // 저장 상태 메시지 설정
          saveMessage.value = '이미 저장이 완료되었습니다. 변경사항이 없습니다'
          saveMessageType.value = 'info'
          saveIcon.value = 'mdi-check-circle-outline'
          showSaveSnackbar.value = true

          // 저장 완료된 상태임을 명확히 알림
          emit('status-message', {
            message: '이미 저장이 완료되었습니다. 변경사항이 없습니다',
            type: 'info',
            icon: 'mdi-check-circle-outline'
          })
          return
        }

        // YOLO 형식으로 변환
        const yoloLines = []
        const originalWidth = props.currentResult.width || imageWidth.value
        const originalHeight = props.currentResult.height || imageHeight.value

         if (!originalWidth || !originalHeight) {
           console.warn('원본 이미지 크기 정보가 없어 저장할 수 없습니다.')
           return
         }

         // 화면 표시 크기에서 원본 크기로 변환하기 위한 스케일링 팩터
         const scaleToOriginalX = originalWidth / (imageWidth.value || 1)
         const scaleToOriginalY = originalHeight / (imageHeight.value || 1)

         console.log('저장 시 좌표 변환 정보:', {
           originalSize: { originalWidth, originalHeight },
           displaySize: { width: imageWidth.value, height: imageHeight.value },
           scaleToOriginal: { scaleToOriginalX: scaleToOriginalX.toFixed(4), scaleToOriginalY: scaleToOriginalY.toFixed(4) }
         })

         // 바운딩박스가 있는 경우에만 변환
         if (boundingBoxes.value.length > 0) {

           // 🎯 프로젝트의 class_info를 사용하여 클래스 ID 매핑 생성
           const classIdMapping = {}

           console.log('=== 프로젝트 클래스 ID 매핑 생성 시작 ===')
           console.log('프로젝트 class_info:', props.projectClassInfo)

           if (props.projectClassInfo && Array.isArray(props.projectClassInfo) && props.projectClassInfo.length > 0) {
             // class_info가 있는 경우 - 프로젝트 저장 시와 동일한 ID 매핑 사용
             props.projectClassInfo.forEach(classInfo => {
               if (classInfo.id !== undefined && classInfo.name) {
                 classIdMapping[classInfo.name] = classInfo.id
               }
             })
             console.log('✅ 프로젝트 class_info 기반 ID 매핑:', classIdMapping)
           } else {
             // class_info가 없는 경우 - 사용 중인 클래스들을 정렬하여 연속된 ID 할당 (기존 방식)
             console.log('⚠️ 프로젝트 class_info가 없어서 기존 방식 사용')
             const usedClasses = new Set()
             boundingBoxes.value.forEach(box => {
               if (box.label && box.label !== 'unknown') {
                 usedClasses.add(box.label)
               }
             })
             const sortedClasses = Array.from(usedClasses).sort()
             console.log('정렬된 클래스 목록:', sortedClasses)

             sortedClasses.forEach((className, index) => {
               classIdMapping[className] = index
             })
             console.log('✅ 정렬 기반 ID 매핑:', classIdMapping)
           }

           boundingBoxes.value.forEach(box => {
             if (!box.label) return

             // 클래스 ID 매핑에서 ID 찾기
             const classIndex = classIdMapping[box.label]

             // 클래스를 찾을 수 없는 경우 경고 출력 후 건너뛰기
             if (classIndex === undefined) {
               console.warn(`클래스 '${box.label}'의 ID를 찾을 수 없습니다. ID 매핑:`, classIdMapping)
               return
             }

             console.log(`클래스 '${box.label}' -> ID ${classIndex}`)

             let centerX, centerY, normalizedWidth, normalizedHeight

             // 항상 현재 화면 표시 좌표를 사용 (편집된 내용이 정확히 반영됨)
             // 화면 표시 좌표를 원본 크기로 변환 후 정규화
             const xOriginal = box.x * scaleToOriginalX
             const yOriginal = box.y * scaleToOriginalY
             const widthOriginal = box.width * scaleToOriginalX
             const heightOriginal = box.height * scaleToOriginalY

             centerX = (xOriginal + widthOriginal / 2) / originalWidth
             centerY = (yOriginal + heightOriginal / 2) / originalHeight
             normalizedWidth = widthOriginal / originalWidth
             normalizedHeight = heightOriginal / originalHeight

             console.log('현재 화면 좌표로 정규화 계산:', {
               displayBox: { x: box.x, y: box.y, width: box.width, height: box.height },
               originalBox: { xOriginal, yOriginal, widthOriginal, heightOriginal },
               normalized: { centerX, centerY, normalizedWidth, normalizedHeight }
             })

             // 좌표 유효성 검사
             if (centerX >= 0 && centerX <= 1 && centerY >= 0 && centerY <= 1 &&
                 normalizedWidth > 0 && normalizedWidth <= 1 && normalizedHeight > 0 && normalizedHeight <= 1) {
               yoloLines.push(`${classIndex} ${centerX.toFixed(6)} ${centerY.toFixed(6)} ${normalizedWidth.toFixed(6)} ${normalizedHeight.toFixed(6)}`)
             } else {
               console.warn('유효하지 않은 정규화 좌표, 저장 스킵:', { centerX, centerY, normalizedWidth, normalizedHeight })
             }
           })
         }

         // 바운딩박스가 모두 삭제된 경우 빈 내용으로 저장
         const yoloContent = yoloLines.join('\n')

         // 프로젝트 라벨링 폴더에 저장
         if (props.projectPath) {
           const baseFilename = props.currentResult.filename.replace(/\.[^/.]+$/, "")
           const labelFilename = `${baseFilename}.txt`
           const labelsFolderPath = `${props.projectPath}/labels`

           console.log('저장 정보:', {
             projectPath: props.projectPath,
             labelsFolderPath: labelsFolderPath,
             filename: labelFilename,
             contentLength: yoloContent.length,
             boundingBoxCount: boundingBoxes.value.length
           })

           // 저장 API 호출 (새로운 라벨 파일 저장 API 사용)
           const saveResponse = await fetch(`${API_SERVER}/api/save-label-file`, {
             method: 'POST',
             headers: {
               'Content-Type': 'application/json',
             },
             body: JSON.stringify({
               projectPath: labelsFolderPath,
               filename: labelFilename,
               fileContent: yoloContent
             })
           })

           if (!saveResponse.ok) {
             const errorText = await saveResponse.text()
             console.error('저장 실패 응답:', errorText)
             throw new Error(`저장 실패: ${saveResponse.status} - ${errorText}`)
           }

           const responseData = await saveResponse.json()
           console.log('저장 성공 응답:', responseData)

           // 저장 성공 시 변경사항 초기화
           hasChanges.value = false

           // 저장 상태 메시지 설정
           saveMessage.value = `라벨 파일이 저장되었습니다: ${labelFilename} (${boundingBoxes.value.length}개 박스)`
           saveMessageType.value = 'success'
           saveIcon.value = 'mdi-content-save'
           showSaveSnackbar.value = true

           // 저장 성공 알림 MainView로 전달
           emit('status-message', {
             message: `라벨 파일이 저장되었습니다: ${labelFilename} (${boundingBoxes.value.length}개 박스)`,
             type: 'success',
             icon: 'mdi-content-save'
           })
         } else {
           throw new Error('프로젝트 경로가 설정되지 않았습니다')
         }
       } catch (error) {
         console.error('저장 오류:', error)

         // 저장 상태 메시지 설정
         saveMessage.value = `저장 중 오류: ${error.message}`
         saveMessageType.value = 'error'
         saveIcon.value = 'mdi-alert'
         showSaveSnackbar.value = true

         // 저장 실패 알림 MainView로 전달
         emit('status-message', {
           message: `저장 중 오류: ${error.message}`,
           type: 'error',
           icon: 'mdi-alert'
         })
       }
     }

    const copyAllBoxes = () => {
      // 편집모드가 아닐 때는 복사 불가
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 바운딩 박스를 복사할 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      if (boundingBoxes.value.length > 0) {
        // 전체 복사 타입과 데이터를 함께 저장
        const newCopiedBox = {
          type: 'all',
          data: [...boundingBoxes.value],
          count: boundingBoxes.value.length
        }

        // MainView의 copiedBox 상태 업데이트
        emit('update-copied-box', newCopiedBox)

        // 전체 복사 알림 MainView로 전달
        emit('status-message', {
          message: `${boundingBoxes.value.length}개의 바운딩 박스가 복사되었습니다`,
          type: 'success',
          icon: 'mdi-content-copy'
        })
      } else {
        // 복사할 박스가 없을 때 알림창 표시
        emit('status-message', {
          message: '복사할 바운딩 박스가 없습니다',
          type: 'info',
          icon: 'mdi-information'
        })
      }
    }
    const pasteBox = () => {
      // 편집모드가 아닐 때는 붙여넣기 불가
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 바운딩 박스를 붙여넣을 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      // 복사된 박스가 없을 때 알림 메시지 추가
      if (!props.copiedBox || !props.copiedBox.data || props.copiedBox.data.length === 0) {
        emit('status-message', {
          message: '붙여넣을 바운딩 박스가 없습니다. 먼저 Ctrl+C로 바운딩 박스를 복사하세요',
          type: 'warning',
          icon: 'mdi-content-copy'
        })
        return
      }

      // 작업 전 상태 저장
      saveToHistory()

      const copyType = props.copiedBox.type
      const copyData = props.copiedBox.data
      const copyCount = props.copiedBox.count

      if (copyType === 'single') {
        // 단일 박스 붙여넣기 (마우스 커서 위치에 왼쪽 상단 배치)
        const originalBox = copyData[0]

        // 박스 크기가 이미지 크기를 초과하는 경우 크기 조정
        const adjustedWidth = Math.min(originalBox.width, imageWidth.value)
        const adjustedHeight = Math.min(originalBox.height, imageHeight.value)

        // 마우스 위치가 유효한지 확인하고 기본 위치 설정
        let targetX, targetY

        if (currentMousePos.value.x >= 0 && currentMousePos.value.x <= imageWidth.value &&
            currentMousePos.value.y >= 0 && currentMousePos.value.y <= imageHeight.value) {
          // 마우스 위치가 이미지 내부에 있는 경우
          targetX = currentMousePos.value.x
          targetY = currentMousePos.value.y
        } else {
          // 마우스 위치가 유효하지 않은 경우, 이미지 중앙에서 조금 오프셋을 준 위치
          targetX = Math.max(10, imageWidth.value / 2 - adjustedWidth / 2)
          targetY = Math.max(10, imageHeight.value / 2 - adjustedHeight / 2)
        }

        const newBox = {
          ...originalBox,
          width: adjustedWidth,
          height: adjustedHeight,
          x: Math.max(0, Math.min(targetX, imageWidth.value - adjustedWidth)),
          y: Math.max(0, Math.min(targetY, imageHeight.value - adjustedHeight))
        }

        boundingBoxes.value.push(newBox)
        selectedBoxIndex.value = boundingBoxes.value.length - 1
        selectedBoxIndices.value = new Set([selectedBoxIndex.value])

        // 변경사항 표시 및 이벤트 emit
        hasChanges.value = true

        emit('bbox-change', {
          action: 'add',
          box: newBox,
          index: selectedBoxIndex.value
        })

        // 크기가 조정되었는지 확인
        const wasResized = originalBox.width > imageWidth.value || originalBox.height > imageHeight.value

        emit('status-message', {
          message: `바운딩 박스가 마우스 위치에 붙여넣기되었습니다${wasResized ? ' (박스 크기 조정됨)' : ''}. T키로 저장하세요`,
          type: 'success',
          icon: 'mdi-content-paste'
        })
      } else if (copyType === 'multiple' || copyType === 'all') {
        // 다중/전체 박스 붙여넣기 (원래 좌표 그대로 유지)
        const pastedBoxes = copyData.map(box => {
          // 박스 크기가 이미지 크기를 초과하는 경우 크기 조정
          const adjustedWidth = Math.min(box.width, imageWidth.value)
          const adjustedHeight = Math.min(box.height, imageHeight.value)

          return {
            ...box,
            width: adjustedWidth,
            height: adjustedHeight,
            // 이미지 경계 내로 제한하되 원래 좌표 최대한 유지
            x: Math.max(0, Math.min(box.x, imageWidth.value - adjustedWidth)),
            y: Math.max(0, Math.min(box.y, imageHeight.value - adjustedHeight))
          }
        })

        // 기존 박스들에 추가 (덮어쓰지 않음)
        boundingBoxes.value.push(...pastedBoxes)

        // 붙여넣은 박스들을 다중 선택 상태로 설정
        const startIndex = boundingBoxes.value.length - pastedBoxes.length
        const newSelectedIndices = new Set()
        for (let i = 0; i < pastedBoxes.length; i++) {
          newSelectedIndices.add(startIndex + i)
        }
        selectedBoxIndices.value = newSelectedIndices
        selectedBoxIndex.value = startIndex + pastedBoxes.length - 1 // 마지막 박스를 주요 선택으로

        // 변경사항 표시 및 이벤트 emit
        hasChanges.value = true

        console.log(`${copyType} 박스 붙여넣기 완료 - 변경사항 상태:`, hasChanges.value)
        console.log('붙여넣은 박스 수:', pastedBoxes.length)
        console.log('총 박스 수:', boundingBoxes.value.length)

        // 각 붙여넣은 박스에 대해 이벤트 emit
        pastedBoxes.forEach((box, index) => {
          emit('bbox-change', {
            action: 'add',
            box: box,
            index: startIndex + index
          })
        })

        // 크기가 조정된 박스가 있는지 확인
        const hasResizedBoxes = copyData.some(box =>
          box.width > imageWidth.value || box.height > imageHeight.value
        )

        const copyTypeText = copyType === 'all' ? '전체' : '다중 선택된'
        emit('status-message', {
          message: `${copyCount}개의 ${copyTypeText} 바운딩 박스가 원래 위치에 붙여넣기되었습니다${hasResizedBoxes ? ' (일부 박스 크기 조정됨)' : ''}. T키로 저장하세요`,
          type: 'success',
          icon: 'mdi-content-paste'
        })
      }
    }

    const selectClass = async (classIndex) => {
      const availableClasses = props.availableClassesFromParent
      if (classIndex < availableClasses.length) {
        selectedClassIndex.value = classIndex
        const className = availableClasses[classIndex]

        // 선택된 박스의 클래스 변경
        if (selectedBoxIndex.value !== -1 && boundingBoxes.value[selectedBoxIndex.value]) {
          const oldLabel = boundingBoxes.value[selectedBoxIndex.value].label

          // 클래스가 실제로 변경되는 경우에만 히스토리 저장
          if (oldLabel !== className) {
            saveToHistory()
          }

          boundingBoxes.value[selectedBoxIndex.value].label = className
          boundingBoxes.value[selectedBoxIndex.value].color = getClassColor(className, classColors.value)
          hasChanges.value = true // 변경사항 표시

          // 클래스 변경 이벤트 emit
          emit('bbox-change', {
            action: 'modify',
            box: boundingBoxes.value[selectedBoxIndex.value],
            index: selectedBoxIndex.value
          })

        emit('status-message', {
          message: `클래스가 "${oldLabel}"에서 "${className}"로 변경되었습니다. T키로 저장하세요`,
          type: 'success',
          icon: 'mdi-tag'
        })
        } else {
          emit('status-message', {
            message: `클래스 "${className}" 선택됨`,
            type: 'info',
            icon: 'mdi-tag'
          })
        }
      }
    }

                const toggleBoxVisibility = () => {
      // 편집모드가 아니면 실행하지 않음 (이미 MainView에서 체크하지만 이중 보안)
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 바운딩 박스를 숨기거나 표시할 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      // 선택된 박스가 있으면 처리
      if (selectedBoxIndex.value !== -1) {
        const index = selectedBoxIndex.value
        const newHiddenBoxes = new Set(hiddenBoxes.value)
        const boxLabel = boundingBoxes.value[index]?.label || '박스'

        if (newHiddenBoxes.has(index)) {
          // 현재 숨겨진 상태면 보이게 함
          newHiddenBoxes.delete(index)
          const hiddenCount = newHiddenBoxes.size
          emit('status-message', {
            message: `${boxLabel} 바운딩 박스가 표시되었습니다 ${hiddenCount > 0 ? `(숨겨진 박스: ${hiddenCount}개)` : ''}`,
            type: 'success',
            icon: 'mdi-eye'
          })
        } else {
          // 현재 보이는 상태면 완전히 숨김
          newHiddenBoxes.add(index)

          const hiddenCount = newHiddenBoxes.size
          emit('status-message', {
            message: `${boxLabel} 바운딩 박스가 숨겨졌습니다 (숨겨진 박스: ${hiddenCount}개) - 편집모드에서 H키로 복구`,
            type: 'success',
            icon: 'mdi-eye-off'
          })
        }

        hiddenBoxes.value = newHiddenBoxes
      } else {
        emit('status-message', {
          message: '바운딩 박스를 먼저 선택해주세요',
          type: 'warning',
          icon: 'mdi-cursor-pointer'
        })
      }
    }

    const toggleBoxThickness = () => {
      // 편집모드에서만 굵기 토글 가능
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 바운딩 박스 굵기를 변경할 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      // MainView의 thickBoxMode 상태 업데이트
      const newThickBoxMode = !props.thickBoxMode
      emit('update-thick-box-mode', newThickBoxMode)

      emit('status-message', {
        message: `바운딩 박스 굵기: ${newThickBoxMode ? '굵게' : '얇게'}`,
        type: 'info',
        icon: newThickBoxMode ? 'mdi-border-style' : 'mdi-border-all'
      })
    }

    const showAllHiddenBoxes = () => {
      // 편집모드가 아니면 실행하지 않음
      if (editMode.value !== 'edit') {
        emit('status-message', {
          message: '편집 모드에서만 숨겨진 바운딩 박스를 표시할 수 있습니다 (E키로 편집모드 활성화)',
          type: 'warning',
          icon: 'mdi-lock'
        })
        return
      }

      const hiddenCount = hiddenBoxes.value.size

      if (hiddenCount === 0) {
        emit('status-message', {
          message: '숨겨진 바운딩 박스가 없습니다',
          type: 'info',
          icon: 'mdi-eye'
        })
        return
      }

      // 모든 숨겨진 박스를 보이게 함
      hiddenBoxes.value = new Set()

      emit('status-message', {
        message: `숨겨진 바운딩 박스 ${hiddenCount}개를 모두 표시했습니다`,
        type: 'success',
        icon: 'mdi-eye-check'
      })
    }

    // 박스 마우스 오버 핸들러 - 숨겨진 박스는 호버 무시
    const handleBoxMouseOver = (index) => {
      // 숨겨진 박스는 호버 이벤트 무시 (listening이 false이므로 여기까지 오지 않지만 안전장치)
      if (hiddenBoxes.value.has(index)) {
        return
      }

      hoveredBoxIndex.value = index
    }

    // 박스 마우스 아웃 핸들러 - 숨겨진 박스는 호버 무시
    const handleBoxMouseOut = (index) => {
      // 숨겨진 박스는 호버 이벤트 무시 (listening이 false이므로 여기까지 오지 않지만 안전장치)
      if (hiddenBoxes.value.has(index)) {
        return
      }

      hoveredBoxIndex.value = -1
    }



    // Stage drag handlers (빈 핸들러들로 이벤트만 처리)
    const handleStageDragStart = () => {
      // 기본 드래그는 사용하지 않고 마우스 이벤트로 처리
    }

    const handleStageDragMove = () => {
      // 기본 드래그는 사용하지 않고 마우스 이벤트로 처리
    }

    const handleStageDragEnd = () => {
      // 기본 드래그는 사용하지 않고 마우스 이벤트로 처리
    }

    // 키보드 이벤트 핸들러
    const handleKeyDown = (event) => {
      if (event.code === 'Space') {
        event.preventDefault() // Space 키의 기본 동작 방지
        isSpacePressed.value = true
        isDragStarted.value = false
        console.log('Space 키 눌림 - 드래그 대기 상태', { isSpacePressed: isSpacePressed.value })
      }
    }

    const handleKeyUp = (event) => {
      if (event.code === 'Space') {
        isSpacePressed.value = false
        isDragStarted.value = false

        // Space 키를 뗄 때 드래그 상태도 해제
        if (isDraggingStage.value) {
          isDraggingStage.value = false
          dragStartPos.value = null
          dragStartStagePos.value = null
        }
      }
    }

    // Lifecycle
    onMounted(() => {
      window.addEventListener('resize', handleWindowResize)
      window.addEventListener('keydown', handleKeyDown)
      window.addEventListener('keyup', handleKeyUp)
      nextTick(() => {
        calculateDisplaySize()
        if (props.currentResult) {
          loadImage()
        }
      })
    })

        onBeforeUnmount(() => {
      window.removeEventListener('resize', handleWindowResize)
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    })

    // Watchers
    watch(() => props.currentResult, () => {
      selectedBoxIndex.value = -1
      selectedBoxIndices.value = new Set() // 다중 선택 초기화
      hiddenBoxes.value = new Set() // 이미지 변경 시 숨김 상태 초기화
      clearHistory() // 이미지 변경 시 히스토리 스택 초기화
      hasChanges.value = false // 변경사항 초기화
      // 편집모드는 R키로만 해제 가능하므로 이미지 변경시에도 유지
      if (props.currentResult) {
        loadImage()
      }
    })

    watch(() => props.availableClassesFromParent, async (newClasses) => {
      if (newClasses && newClasses.length > 0) {
        const colors = {}
        newClasses.forEach(className => {
          colors[className] = getClassColor(className, colors)
        })
        classColors.value = colors
        await processResults()
      }
    }, { immediate: true })

    return {
      // Refs
      imageViewer,
      imageContainer,
      konvaContainer,
      stage,
      imageLayer,
      boxLayer,

      // State
      selectedBoxIndex,
      selectedBoxIndices,
      editMode,
      imageNode,
      boundingBoxes,
      classColors,
      isDrawing,
      tempBox,
      hiddenBoxes,
      hoveredBoxIndex,
      currentMousePos,
      hasChanges,
      showMultiSelectSnackbar,
      multiSelectMessage,
      multiSelectIcon,
      showSaveSnackbar,
      saveMessage,
      saveMessageType,
      saveIcon,
      isSpacePressed,

      // Computed
      stageConfig,
      imageConfig,
      isLowConfidenceImage,
      groupedBoxes,
      displayScale,
      selectedClassColor,
      sortedBoxesForRendering,
      currentResizeHandles,

      // Methods
      selectBox,
      handleMouseDown,
      handleMouseMove,
      handleNativePointerMove,
      handleMouseUp,
      handleResize,
      handleResizeEnd,
      handleMove,
      handleMoveEnd,
      handleBoxMove,
      handleBoxMoveEnd,
      handleWheel,
      handleMouseOver,
      handleMouseOut,
      handleBoxMouseOver,
      handleBoxMouseOut,
      handleBoxClick,
      handleStageDragStart,
      handleStageDragMove,
      handleStageDragEnd,
      resetZoom,
      getSelectedBoxPosition,
      getResizeHandles,
      getMoveHandlePosition,
      getBoxStrokeWidth,
      getResolutionScaleFactor,
      getHandleRadius,
      getSmallHandleRadius,
      getLabelFontSize,
      getLabelBackgroundWidth,
      getLabelBackgroundHeight,

      // Public methods (called from MainView)
      toggleEditMode,
      exitEditMode,
      saveBoundingBoxes,
      startDrawingMode,
      deleteSelectedBox,
      copySelectedBox,
      copyAllBoxes,
      pasteBox,
      selectClass,
      toggleBoxVisibility,
      toggleBoxThickness,
      showAllHiddenBoxes,
      undoLastAction,
      clearHistory,
      stepZoomIn,
      stepZoomOut,

      // Crosshair guide
      imageWidth,
      imageHeight
    }
  }
}
</script>

<style scoped>
.image-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  min-height: 0; /* Flexbox에서 중요한 설정 */
}

.image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  min-height: 0;
  background: #000;
  overflow: hidden;
  position: relative;
}

.konva-container {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  background: #000;
  cursor: crosshair;
}

.info-panel-container {
  border-top: 1px solid #333;
  background: #1e1e1e;
}

.edit-mode-indicator,
.draw-mode-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.class-legend-wrapper {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 9;
  pointer-events: none;
}

.class-legend-wrapper .class-legend-container {
  pointer-events: auto;
}

.image-viewer-col {
  height: 100%;
  flex-direction: column;
}

.image-viewer-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.no-image-card {
  height: 100%;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #000000 !important;
}

.modern-snackbar {
  font-weight: 500;
}

:deep(.modern-snackbar .v-snackbar__wrapper) {
  margin-top: 60px; /* 상단 네비게이터와 겹치지 않도록 조정 */
  border-radius: 16px !important;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.2) !important;
  backdrop-filter: blur(16px) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  min-width: 380px !important;
}

:deep(.modern-snackbar .v-snackbar__content) {
  padding: 18px 22px !important;
}

:deep(.modern-snackbar .notification-content) {
  align-items: center !important;
}

:deep(.modern-snackbar .notification-icon) {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) !important;
}

:deep(.modern-snackbar .notification-message) {
  font-size: 0.95rem !important;
  opacity: 0.95 !important;
  line-height: 1.4 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  font-weight: 500 !important;
}

/* 다중 선택 알림창 특별 스타일 */
:deep(.multi-select-snackbar) {
  .v-snackbar__wrapper {
    background: linear-gradient(135deg, rgba(33, 150, 243, 0.95), rgba(21, 101, 192, 0.95)) !important;
  }
}

/* 저장 상태 알림창 특별 스타일 */
:deep(.save-snackbar.modern-snackbar) {
  .v-snackbar__wrapper {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.95), rgba(56, 142, 60, 0.95)) !important;
  }
}

:deep(.save-snackbar.modern-snackbar .v-snackbar__wrapper[style*="error"]) {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.95), rgba(198, 40, 40, 0.95)) !important;
}

/* 반응형 미디어 쿼리 */
@media (max-width: 1200px) {
  .image-container {
    padding: 8px;
  }

  .edit-mode-indicator,
  .draw-mode-indicator {
    top: 15px;
    right: 15px;
  }

  .class-legend-wrapper {
    top: 15px;
    left: 15px;
  }
}

@media (max-width: 768px) {
  .image-container {
    padding: 6px;
  }

  .edit-mode-indicator,
  .draw-mode-indicator {
    top: 10px;
    right: 10px;
  }

  .class-legend-wrapper {
    top: 10px;
    left: 10px;
  }
}

@media (max-width: 480px) {
  .image-container {
    padding: 4px;
  }

  .edit-mode-indicator,
  .draw-mode-indicator {
    top: 8px;
    right: 8px;
  }

  .class-legend-wrapper {
    top: 8px;
    left: 8px;
  }
}

@media (max-width: 320px) {
  .image-container {
    padding: 2px;
  }

  .edit-mode-indicator,
  .draw-mode-indicator {
    top: 5px;
    right: 5px;
  }

  .class-legend-wrapper {
    top: 5px;
    left: 5px;
  }
}
</style>
