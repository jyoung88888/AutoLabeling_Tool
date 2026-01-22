<template>
  <v-app :theme="darkTheme ? 'dark' : 'light'">
    <!-- 사이드바 -->
    <LabelingSidebar
      :sidebar-visible="sidebarVisible"
      :sidebar-rail="sidebarRail"
      :sidebar-width="sidebarWidth"
      :models="models"
      :selected-model-type="selectedModelType"
      :model-details="modelDetails"
      :selected-model="selectedModel"
      :model-status-message="modelStatusMessage"
      :model-status-success="modelStatusSuccess"
      :is-loading-model="isLoadingModel"
      :device-info="deviceInfo"
      :model-loaded="modelLoaded"
      :supports-text-prompt="supportsTextPrompt"
      :uploaded-images="uploadedImages"
      :image-status-message="imageStatusMessage"
      :image-status-success="imageStatusSuccess"
      :available-classes="availableClasses"
      :selected-classes="selectedClasses"
      :select-all-classes="selectAllClasses"
      :all-classes-selected="allClassesSelected"
      :show-class-change-alert="showClassChangeAlert"
      :class-change-message="classChangeMessage"
      :selected-classes-info="selectedClassesInfo"
      :class-selection-applied="classSelectionApplied"
      :can-start-labeling="canStartLabeling"
      :is-processing="isProcessing"
      :progress-percent="progressPercent"
      :current-file="currentFile"
      :time-info="timeInfo"
      :low-confidence-images="lowConfidenceImages"
      :can-save-project="labelingComplete"
      :has-results="results.length > 0"
      :results="results"
      :project-path="projectPath"
      :model-classes="modelClasses"
      :confidence-threshold="confidenceThreshold"
      :text-prompt="textPrompt"
      :box-threshold="boxThreshold"
      :text-threshold="textThreshold"
      :prompt-applied="promptApplied"
      @update:sidebar-visible="sidebarVisible = $event"
      @update:confidence-threshold="confidenceThreshold = $event"
      @update:text-prompt="textPrompt = $event"
      @update:box-threshold="boxThreshold = $event"
      @update:text-threshold="textThreshold = $event"
      @update:selected-model-type="selectedModelType = $event"
      @update:selected-model="selectedModel = $event"
      @update:selected-classes="selectedClasses = $event"
      @update:select-all-classes="selectAllClasses = $event"
      @refresh-models="refreshModels"
      @load-model="loadModel"
      @fetch-model-details="fetchModelDetails"
      @file-upload="handleFileUpload"
      @clear-files="clearUploadedFiles"
      @toggle-all-classes="toggleAllClasses"
      @select-all-classes-changed="selectAllClassesChanged"
      @check-selected-classes="checkSelectedClasses"
      @apply-class-selection="applyClassSelection"
      @apply-prompt="handleApplyPrompt"
      @dismiss-class-change-alert="dismissClassChangeAlert"
      @open-load-project="openLoadProjectDialog"
      @start-labeling="startLabeling"
      @stop-labeling="stopLabeling"
      @go-to-image="goToImage"
      @project-save-complete="handleProjectSaveComplete"
      @expand-sidebar="sidebarRail = false"
      @collapse-sidebar="sidebarRail = true"
    />

    <v-main class="main-area">
      <div class="responsive-layout">
        <!-- 상단 이미지 네비게이터 -->
        <TopImageNavigator
          v-if="results.length > 0"
          :current-index="currentImageIndex"
          :total-images="results.length"
          :status-message="currentStatusMessage"
          :status-type="statusMessageType"
          :status-icon="statusMessageIcon"
          @prev="prevImage"
          @next="nextImage"
          @goto="goToImage"
          @clear-status-message="clearStatusMessage"
        />

        <!-- 메인 이미지 뷰어 영역 -->
        <div class="image-viewer-container">
          <ImageViewer
            ref="imageViewer"
            :key="`image-viewer-${currentImageIndex}-${results.length}`"
            :current-result="currentResult"
            :canvas-ref="canvasRef"
            :current-image-index="currentImageIndex"
            :total-images="results.length"
            :results="results"
            :available-classes-from-parent="availableClasses"
            :low-confidence-images="lowConfidenceImages"
            :project-path="projectPath"
            :is-loading-project="isLoadingProject"
            :is-loading-images="isLoadingImages"
            :loading-image-progress="loadingImageProgress"
            :project-class-info="projectClassInfo"
            :copied-box="copiedBox"
            :thick-box-mode="thickBoxMode"
            @prev="prevImage"
            @next="nextImage"
            @bbox-edit="handleBboxEdit"
            @bbox-change="onBboxChange"
            @delete-box="handleDeleteBox"
            @status-message="handleStatusMessage"
            @open-load-project="openLoadProjectDialog"
            @show-help="showHelpDialog = true"
            @update-copied-box="copiedBox = $event"
            @update-thick-box-mode="thickBoxMode = $event"
          />
        </div>
      </div>
    </v-main>

    <!-- 프로젝트 불러오기 다이얼로그 -->
    <ProjectLoadDialog
      v-model="showLoadProjectDialog"
      :is-loading="isLoadingProject"
      :project-list="projectList"
      :project-path="projectPath"
      :project-path-error="projectPathError"
      :load-project-success="loadProjectSuccess"
      :load-project-error="loadProjectError"
      :loading-image-progress="loadingImageProgress"
      @load-project="handleLoadSelectedProject"
      @close="closeLoadProjectDialog"
    />

    <!-- 단축키 도움말 다이얼로그 -->
    <KeyboardShortcutsDialog v-model="showHelpDialog" />

    <!-- 파일 삭제 확인 다이얼로그 -->
    <DeleteConfirmDialog
      v-model="showDeleteConfirmDialog"
      :filename="currentFilename"
      :is-deleting="isDeletingFile"
      @confirm-delete="handleDeleteConfirm"
      @cancel-delete="handleDeleteCancel"
    />

    <!-- 저장 확인 다이얼로그 -->
    <v-dialog
      v-model="showSaveConfirmDialog"
      max-width="500"
      persistent
      class="save-confirm-dialog"
    >
      <v-card color="#1e1e1e" class="text-white">
        <v-card-title class="text-h6 py-4">
          <v-icon icon="mdi-content-save-alert" class="mr-2" color="orange"></v-icon>
          변경사항 저장
        </v-card-title>
        <v-card-text class="py-4">
          <div class="text-body-1 mb-2">현재 이미지에 저장되지 않은 변경사항이 있습니다.</div>
          <div class="text-body-2 text-grey-lighten-1">
            이미지를 이동하기 전에 변경사항을 저장하시겠습니까?
          </div>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="handleSaveConfirmNo"> 아니오 </v-btn>
          <v-btn color="primary" variant="elevated" @click="handleSaveConfirmYes" class="ml-2">
            예, 저장
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 편집 모드 알림창 -->
    <v-snackbar
      v-model="showEditModeSnackbar"
      :key="editModeSnackbarKey"
      :timeout="2000"
      location="top center"
      color="primary"
      class="modern-snackbar edit-mode-snackbar"
      elevation="16"
      eager
      transition="fade-transition"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          :icon="editModeIcon"
          :color="editModeColor"
          size="28"
          class="mr-4 notification-icon"
        ></v-icon>
        <div>
          <div class="text-subtitle-1 font-weight-bold notification-title">
            {{ editModeTitle }}
          </div>
          <div class="text-caption notification-message">
            {{ editModeMessage }}
          </div>
        </div>
      </div>

      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showEditModeSnackbar = false"
          size="small"
          class="notification-close-btn"
        >
          닫기
        </v-btn>
      </template>
    </v-snackbar>

    <!-- 저장 제한 알림창 -->
    <v-snackbar
      v-model="showSaveRestrictionSnackbar"
      :key="saveRestrictionSnackbarKey"
      :timeout="4000"
      location="top center"
      color="warning"
      class="modern-snackbar save-restriction-snackbar"
      elevation="16"
      eager
      transition="fade-transition"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          icon="mdi-lock-alert"
          color="amber-lighten-1"
          size="28"
          class="mr-4 notification-icon"
        ></v-icon>
        <div>
          <div class="text-subtitle-1 font-weight-bold notification-title">
            편집모드에서는 저장할 수 없습니다
          </div>
          <div class="text-caption notification-message">
            R키를 눌러 편집모드를 해제한 후 T키로 저장하세요
          </div>
        </div>
      </div>

      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showSaveRestrictionSnackbar = false"
          size="small"
          class="notification-close-btn"
        >
          닫기
        </v-btn>
      </template>
    </v-snackbar>

    <!-- 바운딩 박스 그리기 모드 알림창 -->
    <v-snackbar
      v-model="showDrawingModeSnackbar"
      :key="drawingModeSnackbarKey"
      :timeout="3000"
      location="top center"
      color="success"
      class="modern-snackbar drawing-mode-snackbar"
      elevation="16"
      eager
      transition="fade-transition"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          icon="mdi-plus-box"
          color="green-lighten-1"
          size="28"
          class="mr-4 notification-icon"
        ></v-icon>
        <div>
          <div class="text-subtitle-1 font-weight-bold notification-title">
            바운딩 박스 그리기 모드
          </div>
          <div class="text-caption notification-message">드래그하여 새 바운딩 박스를 그리세요</div>
        </div>
      </div>

      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showDrawingModeSnackbar = false"
          size="small"
          class="notification-close-btn"
        >
          닫기
        </v-btn>
      </template>
    </v-snackbar>

    <!-- 이미 저장 완료 알림창 -->
    <v-snackbar
      v-model="showAlreadySavedSnackbar"
      :key="alreadySavedSnackbarKey"
      :timeout="3000"
      location="top center"
      color="info"
      class="modern-snackbar already-saved-snackbar"
      elevation="16"
      eager
      transition="fade-transition"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          icon="mdi-check-circle-outline"
          color="light-blue-lighten-1"
          size="28"
          class="mr-4 notification-icon"
        ></v-icon>
        <div>
          <div class="text-subtitle-1 font-weight-bold notification-title">
            이미 저장이 완료되었습니다
          </div>
          <div class="text-caption notification-message">
            변경사항이 없어 저장할 내용이 없습니다
          </div>
        </div>
      </div>

      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showAlreadySavedSnackbar = false"
          size="small"
          class="notification-close-btn"
        >
          닫기
        </v-btn>
      </template>
    </v-snackbar>

    <!-- 전체 복사 알림창 -->
    <v-snackbar
      v-model="showCopyAllSnackbar"
      :key="copyAllSnackbarKey"
      :timeout="2500"
      location="top center"
      color="success"
      class="modern-snackbar copy-all-snackbar"
      elevation="16"
      eager
      transition="fade-transition"
    >
      <div class="d-flex align-center notification-content">
        <v-icon
          icon="mdi-content-copy"
          color="green-lighten-1"
          size="28"
          class="mr-4 notification-icon"
        ></v-icon>
        <div>
          <div class="text-subtitle-1 font-weight-bold notification-title">전체 복사 완료</div>
          <div class="text-caption notification-message">
            {{ copyAllMessage }}
          </div>
        </div>
      </div>

      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showCopyAllSnackbar = false"
          size="small"
          class="notification-close-btn"
        >
          닫기
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import LabelingSidebar from '@/components/sidebar/LabelingSidebar.vue'
import TopImageNavigator from '@/components/images/TopImageNavigator.vue'
import ImageViewer from '@/components/images/ImageViewer.vue'
import ProjectLoadDialog from '@/components/dialogs/ProjectLoadDialog.vue'
import KeyboardShortcutsDialog from '@/components/dialogs/KeyboardShortcutsDialog.vue'
import DeleteConfirmDialog from '@/components/dialogs/DeleteConfirmDialog.vue'
import { useImageManagement } from '@/composables/useImageManagement'
import { useProjectManagement } from '@/composables/useProjectManagement'
import { useModelManagement } from '@/composables/useModelManagement'
import { useLowConfidenceImages } from '@/composables/useLowConfidenceImages'
import { AutoLabelingService } from '@/services/labeling/AutoLabelingService'
import { clearColorCache } from '@/utils/colorUtils.js'

export default {
  name: 'MainView',
  components: {
    LabelingSidebar,
    TopImageNavigator,
    ImageViewer,
    ProjectLoadDialog,
    KeyboardShortcutsDialog,
    DeleteConfirmDialog,
  },
  setup() {
    // Reactive state
    const darkTheme = ref(true)
    const sidebarVisible = ref(true)
    const sidebarRail = ref(false)
    const sidebarWidth = ref(360)
    const canvasRef = ref(null)
    const imageViewer = ref(null)

    // Navigation state
    const currentImageIndex = ref(1)
    const results = ref([])
    const labelingComplete = ref(false)

    // Status messages
    const currentStatusMessage = ref('')
    const statusMessageType = ref('info')
    const statusMessageIcon = ref('mdi-information')
    const lastStatusMessage = ref('') // 중복 메시지 방지용

    // Dialog state
    const showLoadProjectDialog = ref(false)
    const showHelpDialog = ref(false)
    const showSaveConfirmDialog = ref(false)
    const pendingNavigationAction = ref(null)
    const showDeleteConfirmDialog = ref(false)
    const isDeletingFile = ref(false)

    // Edit mode notification state
    const showEditModeSnackbar = ref(false)
    const editModeSnackbarKey = ref(0)
    const editModeTitle = ref('')
    const editModeMessage = ref('')
    const editModeIcon = ref('mdi-pencil')
    const editModeColor = ref('orange')

    // Save restriction notification state
    const showSaveRestrictionSnackbar = ref(false)
    const saveRestrictionSnackbarKey = ref(0)

    // Drawing mode notification state
    const showDrawingModeSnackbar = ref(false)
    const drawingModeSnackbarKey = ref(0)

    // Already saved notification state
    const showAlreadySavedSnackbar = ref(false)
    const alreadySavedSnackbarKey = ref(0)

    // Copy all notification state
    const showCopyAllSnackbar = ref(false)
    const copyAllSnackbarKey = ref(0)
    const copyAllMessage = ref('')

    // 복사된 바운딩 박스 상태 (이미지 변경 시에도 유지)
    const copiedBox = ref(null)

    // 바운딩 박스 굵기 모드 (이미지 변경 시에도 유지)
    const thickBoxMode = ref(false)

    // 신뢰도 임계값 (0-1 범위)
    const confidenceThreshold = ref(0.5)

    // Grounding DINO 텍스트 프롬프트 관련
    const textPrompt = ref('')
    const boxThreshold = ref(0.3)
    const textThreshold = ref(0.25)
    const promptApplied = ref(false)

    // Project state
    const projectPath = ref('')
    const projectList = ref([])
    const projectPathError = ref(false)
    const loadProjectSuccess = ref(false)
    const loadProjectError = ref(null)
    const isLoadingProject = ref(false)
    const isLoadingImages = ref(false)
    const loadingImageProgress = ref(0)
    // 프로젝트의 class_info 저장 - 라벨 수정 시 정확한 ID 매핑을 위해
    const projectClassInfo = ref([])

    // Composables
    const {
      models,
      selectedModelType,
      selectedModel,
      modelDetails,
      modelLoaded,
      modelStatusMessage,
      modelStatusSuccess,
      deviceInfo,
      modelClasses,
      supportsTextPrompt,
      isLoadingModel,
      refreshModels,
      loadModel,
      fetchModelDetails,
      loadModelClasses,
    } = useModelManagement()

    const {
      uploadedImages,
      imageStatusMessage,
      imageStatusSuccess,
      availableClasses,
      selectedClasses,
      selectAllClasses,
      allClassesSelected,
      showClassChangeAlert,
      classChangeMessage,
      selectedClassesInfo,
      classSelectionApplied,
      canStartLabeling: canStartLabelingYOLO, // YOLO 전용 조건
      handleFileUpload,
      clearUploadedFiles,
      toggleAllClasses,
      selectAllClassesChanged,
      checkSelectedClasses,
      applyClassSelection,
      dismissClassChangeAlert,
      updateAvailableClassesFromModel,
    } = useImageManagement()

    // 모델 타입에 따른 자동 라벨링 시작 가능 여부
    const canStartLabeling = computed(() => {
      const hasImages = uploadedImages.value.length > 0

      if (supportsTextPrompt.value) {
        // Grounding DINO: 이미지 + 프롬프트 적용
        return hasImages && promptApplied.value
      } else {
        // YOLO: 이미지 + 클래스 선택 적용
        return canStartLabelingYOLO.value
      }
    })

    const { loadSelectedProject, handleProjectSaveComplete: baseHandleProjectSaveComplete } =
      useProjectManagement()

    const {
      lowConfidenceImages,
      rebuildLowConfidenceImages,
      setLowConfidenceImagesFromProject,
      clearLowConfidenceImages,
    } = useLowConfidenceImages()

    // 화면 초기화 함수
    const resetScreen = () => {
      console.log('화면 초기화 시작')

      // 라벨링 관련 상태 초기화
      results.value = []
      labelingComplete.value = false
      currentImageIndex.value = 1

      // 프로젝트 관련 상태 초기화
      projectPath.value = ''
      projectClassInfo.value = []

      // 업로드된 이미지 초기화
      clearUploadedFiles()

      // 상태 메시지 초기화
      currentStatusMessage.value = ''
      lastStatusMessage.value = ''

      // 저신뢰도 이미지 초기화
      clearLowConfidenceImages()

      // 색상 캐시 초기화
      clearColorCache()

      console.log('화면 초기화 완료')
    }

    // 프로젝트 저장 완료 처리
    const handleProjectSaveComplete = (saveResult) => {
      console.log('프로젝트 저장 완료 처리:', saveResult)

      // 기본 처리
      const result = baseHandleProjectSaveComplete(saveResult)

      if (result.shouldReset && saveResult.success) {
        // 저장 완료 메시지 표시
        handleStatusMessage({
          message: result.message,
          type: 'success',
          icon: 'mdi-check-circle',
        })

        // 짧은 지연 후 화면 초기화 (메시지를 사용자가 볼 수 있도록)
        setTimeout(() => {
          resetScreen()

          // 초기화 완료 메시지
          handleStatusMessage({
            message: '새로운 프로젝트를 시작할 수 있습니다.',
            type: 'info',
            icon: 'mdi-information',
          })
        }, 1500)
      }
    }

    // Auto labeling service
    const autoLabelingService = ref(null)
    const isProcessing = ref(false)
    const progressPercent = ref(0)
    const currentFile = ref('')
    const timeInfo = ref({ elapsed: '', eta: '' })

    // Computed
    const currentResult = computed(() => {
      if (results.value.length === 0 || currentImageIndex.value < 1) return null
      const index = currentImageIndex.value - 1
      if (index >= results.value.length) return null
      return results.value[index]
    })

    const currentFilename = computed(() => {
      return currentResult.value?.filename || ''
    })

    // Methods
    const startLabeling = async () => {
      if (!autoLabelingService.value) {
        autoLabelingService.value = new AutoLabelingService()
      }

      try {
        // 자동 라벨링 시작 시 색상 캐시 초기화하여 새로운 랜덤 색상 배정
        clearColorCache()

        const selectedClassList = Object.keys(selectedClasses.value).filter(
          (key) => selectedClasses.value[key],
        )

        isProcessing.value = true
        labelingComplete.value = false

        const labelingResults = await autoLabelingService.value.processImages({
          files: uploadedImages.value,
          selectedClasses: selectedClassList,
          confidenceThreshold: confidenceThreshold.value,
          // Grounding DINO 텍스트 프롬프트 지원
          supportsTextPrompt: supportsTextPrompt.value,
          textPrompt: textPrompt.value,
          boxThreshold: boxThreshold.value,
          textThreshold: textThreshold.value,
          onProgress: (progress) => {
            progressPercent.value = progress.percent
            currentFile.value = progress.currentFile
            timeInfo.value = progress.timeInfo
          },
        })

        results.value = labelingResults
        labelingComplete.value = true
        currentImageIndex.value = 1

        // 리사이즈 통계 수집 및 사용자 피드백
        const resizedImages = labelingResults.filter((result) => result && result.wasResized)
        const veryLowResImages = labelingResults.filter(
          (result) => result && result.veryLowResolution,
        )

        if (veryLowResImages.length > 0) {
          const veryLowCount = veryLowResImages.length
          const totalCount = labelingResults.length
          const veryLowImageNames = veryLowResImages.map((img) => img.filename).join(', ')

          console.log(
            `🔧 [자동라벨링 완료] 총 ${totalCount}개 이미지 중 ${veryLowCount}개 매우 낮은 해상도 이미지가 고품질 letterbox 리사이즈되었습니다`,
          )
          console.log(`고품질 리사이즈된 이미지: ${veryLowImageNames}`)

          // 매우 낮은 해상도 이미지 전용 알림
          handleStatusMessage({
            message: `자동라벨링 완료! 매우 낮은 해상도 이미지 ${veryLowCount}개에 고품질 letterbox 리사이즈가 적용되어 검출 성능이 크게 향상되었습니다.`,
            type: 'success',
            icon: 'mdi-image-filter-hdr',
          })
        } else if (resizedImages.length > 0) {
          const resizedCount = resizedImages.length
          const totalCount = labelingResults.length
          const resizedImageNames = resizedImages.map((img) => img.filename).join(', ')

          console.log(
            `🔄 [자동라벨링 완료] 총 ${totalCount}개 이미지 중 ${resizedCount}개 이미지가 자동 리사이즈되었습니다`,
          )
          console.log(`리사이즈된 이미지: ${resizedImageNames}`)

          // 사용자에게 리사이즈 정보 알림
          handleStatusMessage({
            message: `자동라벨링 완료! 낮은 해상도 이미지 ${resizedCount}개가 성능 향상을 위해 자동 리사이즈되었습니다.`,
            type: 'info',
            icon: 'mdi-image-size-select-actual',
          })
        } else {
          console.log(`✅ [자동라벨링 완료] 모든 이미지가 충분한 해상도를 가지고 있습니다`)

          // 일반 완료 메시지
          handleStatusMessage({
            message: `자동라벨링 완료! 총 ${labelingResults.length}개 이미지가 처리되었습니다.`,
            type: 'success',
            icon: 'mdi-check-circle',
          })
        }

        // Rebuild low confidence images
        rebuildLowConfidenceImages(results.value)
      } catch (error) {
        console.error('자동 라벨링 오류:', error)
      } finally {
        isProcessing.value = false
      }
    }

    const stopLabeling = () => {
      if (autoLabelingService.value) {
        autoLabelingService.value.stop()
      }
      isProcessing.value = false
      labelingComplete.value = false
    }

    // 변경사항 체크 후 이미지 이동 처리
    const checkChangesAndNavigate = (navigationAction) => {
      // 변경사항이 있는지 확인
      if (imageViewer.value?.hasChanges) {
        // 대기 중인 네비게이션 액션 저장
        pendingNavigationAction.value = navigationAction
        // 저장 확인 다이얼로그 표시
        showSaveConfirmDialog.value = true
        return
      }

      // 변경사항이 없으면 바로 실행
      navigationAction()
    }

    const prevImage = () => {
      if (currentImageIndex.value > 1) {
        checkChangesAndNavigate(() => {
          // 편집모드에서 이미지 이동 시 자동으로 편집모드 해제
          if (imageViewer.value?.editMode === 'edit') {
            imageViewer.value.exitEditMode()
            handleStatusMessage({
              message: '이미지 이동으로 인해 편집 모드가 자동 해제되었습니다',
              type: 'info',
              icon: 'mdi-arrow-left-circle',
            })
          }
          currentImageIndex.value--
        })
      }
    }

    const nextImage = () => {
      if (currentImageIndex.value < results.value.length) {
        checkChangesAndNavigate(() => {
          // 편집모드에서 이미지 이동 시 자동으로 편집모드 해제
          if (imageViewer.value?.editMode === 'edit') {
            imageViewer.value.exitEditMode()
            handleStatusMessage({
              message: '이미지 이동으로 인해 편집 모드가 자동 해제되었습니다',
              type: 'info',
              icon: 'mdi-arrow-right-circle',
            })
          }
          currentImageIndex.value++
        })
      }
    }

    const goToImage = (index) => {
      if (index >= 1 && index <= results.value.length) {
        checkChangesAndNavigate(() => {
          // 편집모드에서 이미지 이동 시 자동으로 편집모드 해제
          if (imageViewer.value?.editMode === 'edit') {
            imageViewer.value.exitEditMode()
            handleStatusMessage({
              message: '이미지 이동으로 인해 편집 모드가 자동 해제되었습니다',
              type: 'info',
              icon: 'mdi-skip-next-circle',
            })
          }
          currentImageIndex.value = index
        })
      }
    }

    const handleBboxEdit = (editData) => {
      console.log('Bbox edit:', editData)
    }

    const onBboxChange = (changes) => {
      console.log('Bbox change:', changes)

      // 현재 이미지 결과 업데이트
      if (currentResult.value && results.value.length > 0) {
        const currentIndex = currentImageIndex.value - 1
        if (currentIndex >= 0 && currentIndex < results.value.length) {
          // 현재 이미지의 results에서 boxes 배열 업데이트
          const currentImageResult = results.value[currentIndex]

          if (changes.action === 'delete') {
            // 삭제된 박스를 results에서도 제거
            if (currentImageResult.boxes && Array.isArray(currentImageResult.boxes)) {
              // 삭제할 박스를 찾아서 제거 (인덱스로 찾기, 다중 삭제시 역순 처리됨)
              if (changes.index >= 0 && changes.index < currentImageResult.boxes.length) {
                const removedBox = currentImageResult.boxes.splice(changes.index, 1)[0]
                console.log(
                  `박스 삭제 완료: 인덱스 ${changes.index}, 삭제된 박스:`,
                  removedBox?.class_name || removedBox?.label,
                  `남은 박스 수: ${currentImageResult.boxes.length}`,
                )
              }
            }
          } else if (changes.action === 'add') {
            // 새로운 박스 추가
            if (!currentImageResult.boxes) {
              currentImageResult.boxes = []
            }
            currentImageResult.boxes.push(changes.box)
            console.log(`박스 추가 완료: 총 박스 수: ${currentImageResult.boxes.length}`)
          } else if (
            changes.action === 'modify' ||
            changes.action === 'resize' ||
            changes.action === 'move'
          ) {
            // 기존 박스 수정/리사이즈/이동
            if (
              currentImageResult.boxes &&
              changes.index >= 0 &&
              changes.index < currentImageResult.boxes.length
            ) {
              currentImageResult.boxes[changes.index] = { ...changes.box }
              console.log(`박스 ${changes.action} 완료: 인덱스 ${changes.index}`)
            }
          }

          // results 배열 업데이트 (반응성 유지)
          results.value = [...results.value]
        }
      }
    }

    const handleDeleteBox = (boxIndex) => {
      console.log('Delete box:', boxIndex)
    }

    const handleStatusMessage = (statusData) => {
      console.log('전체 상태 메시지 수신:', statusData) // 디버깅용

      // 중복 메시지 방지 - 같은 메시지가 연속으로 오면 무시
      if (lastStatusMessage.value === statusData.message) {
        console.log('중복 메시지 무시:', statusData.message)
        return
      }
      lastStatusMessage.value = statusData.message

      // 전체 복사 관련 메시지인지 확인 (더 포괄적으로)
      if (
        (statusData.message.includes('개의 바운딩 박스가 복사되었습니다') ||
          statusData.message.includes('복사할 바운딩 박스가 없습니다')) &&
        (statusData.type === 'success' || statusData.type === 'info')
      ) {
        console.log('전체 복사 관련 메시지 감지:', statusData.message)

        // 기존 알림이 있으면 즉시 닫기
        if (showCopyAllSnackbar.value) {
          showCopyAllSnackbar.value = false
        }

        // 복사 메시지 설정
        copyAllMessage.value = statusData.message

        // 전체 복사 스낵바 표시
        copyAllSnackbarKey.value = Date.now()
        showCopyAllSnackbar.value = true
        console.log('전체 복사 스낵바 표시:', showCopyAllSnackbar.value)
        return
      }

      // 이미 저장 완료 메시지인지 확인
      if (statusData.message.includes('이미 저장이 완료되었습니다')) {
        console.log('이미 저장 완료 메시지 수신:', statusData.message)

        // 기존 알림이 있으면 즉시 닫기
        if (showAlreadySavedSnackbar.value) {
          showAlreadySavedSnackbar.value = false
        }

        // 이미 저장 완료 스낵바 표시
        alreadySavedSnackbarKey.value = Date.now()
        showAlreadySavedSnackbar.value = true
        return
      }

      // 편집 모드 관련 메시지인지 확인
      if (statusData.message.includes('편집 모드')) {
        console.log('편집 모드 메시지 수신:', statusData.message) // 디버깅용

        // 더 정확한 활성화/비활성화 구분
        const isActivation = statusData.message === '편집 모드 활성화'
        const isDeactivation = statusData.message === '편집 모드 비활성화'

        // 기존 알림이 있으면 즉시 닫기
        if (showEditModeSnackbar.value) {
          showEditModeSnackbar.value = false
        }

        // 즉시 데이터 설정 및 표시
        if (isActivation) {
          editModeTitle.value = '편집 모드 활성화'
          editModeMessage.value = 'E키로 활성화됨 · R키를 눌러 편집모드를 해제할 수 있습니다'
          editModeIcon.value = 'mdi-pencil'
          editModeColor.value = 'orange'
        } else if (isDeactivation) {
          editModeTitle.value = '편집 모드 비활성화'
          editModeMessage.value = '바운딩 박스를 안전하게 확인할 수 있습니다'
          editModeIcon.value = 'mdi-eye'
          editModeColor.value = 'blue'
        } else {
          // 기본 설정 (다른 편집 모드 관련 메시지)
          editModeTitle.value = statusData.message
          editModeMessage.value = ''
          editModeIcon.value = 'mdi-information'
          editModeColor.value = 'primary'
        }

        editModeSnackbarKey.value = Date.now() // 고유 키 생성
        showEditModeSnackbar.value = true
      } else {
        // 기존 상태 메시지 처리
        currentStatusMessage.value = statusData.message
        statusMessageType.value = statusData.type
        statusMessageIcon.value = statusData.icon
      }
    }

    const clearStatusMessage = () => {
      currentStatusMessage.value = ''
      lastStatusMessage.value = '' // 중복 메시지 방지용 초기화
    }

    const openLoadProjectDialog = () => {
      showLoadProjectDialog.value = true
    }

    const closeLoadProjectDialog = () => {
      showLoadProjectDialog.value = false
    }

    // 저장 확인 다이얼로그 핸들러들
    const handleSaveConfirmYes = async () => {
      // 먼저 저장 시도
      if (imageViewer.value?.saveBoundingBoxes) {
        try {
          await imageViewer.value.saveBoundingBoxes()
          // 저장 성공 후 대기 중인 네비게이션 실행
          if (pendingNavigationAction.value) {
            pendingNavigationAction.value()
          }
        } catch (error) {
          console.error('저장 실패:', error)
          handleStatusMessage({
            message: '저장에 실패했습니다. 다시 시도해주세요.',
            type: 'error',
            icon: 'mdi-alert-circle',
          })
        }
      }

      // 다이얼로그 닫기 및 상태 초기화
      showSaveConfirmDialog.value = false
      pendingNavigationAction.value = null
    }

    const handleSaveConfirmNo = () => {
      // 저장하지 않고 바로 대기 중인 네비게이션 실행
      if (pendingNavigationAction.value) {
        pendingNavigationAction.value()
      }

      // 다이얼로그 닫기 및 상태 초기화
      showSaveConfirmDialog.value = false
      pendingNavigationAction.value = null
    }

    // 파일 삭제 확인 다이얼로그 핸들러들
    const handleDeleteConfirm = async () => {
      console.log('🗑️ 파일 삭제 확인 시작')
      console.log('현재 결과:', currentResult.value)
      console.log('프로젝트 경로:', projectPath.value)

      if (!currentResult.value || !projectPath.value) {
        console.error('❌ 삭제 조건 불만족:', {
          currentResult: currentResult.value,
          projectPath: projectPath.value,
        })
        handleStatusMessage({
          message: '삭제할 파일을 찾을 수 없습니다.',
          type: 'error',
          icon: 'mdi-alert-circle',
        })
        showDeleteConfirmDialog.value = false
        return
      }

      isDeletingFile.value = true
      console.log('🔄 삭제 중 상태로 변경')

      try {
        // API 호출을 위해 import 추가
        const { deleteImageAndLabel } = await import('@/api/imageApi.js')

        console.log('📡 API 호출 시작:', {
          filename: currentResult.value.filename,
          projectPath: projectPath.value,
        })

        const response = await deleteImageAndLabel(currentResult.value.filename, projectPath.value)
        console.log('📡 API 응답:', response)

        if (response.success) {
          console.log('✅ 파일 삭제 성공')

          handleStatusMessage({
            message: response.message,
            type: 'success',
            icon: 'mdi-delete',
          })

          // 현재 이미지를 results에서 제거
          const currentIndex = currentImageIndex.value - 1
          console.log('🔄 UI 업데이트 시작:', {
            currentIndex,
            totalImages: results.value.length,
            currentImageIndex: currentImageIndex.value,
          })

          // 삭제 전 상태 로깅
          console.log('삭제 전 results 길이:', results.value.length)
          console.log('삭제할 이미지 인덱스:', currentIndex)
          console.log('삭제할 이미지 정보:', results.value[currentIndex])

          // Vue 반응성을 위해 새로운 배열 생성
          const newResults = [...results.value]
          newResults.splice(currentIndex, 1)
          results.value = newResults
          console.log('삭제 후 results 길이:', results.value.length)

          // 이미지 인덱스 조정
          if (results.value.length === 0) {
            // 모든 이미지가 삭제된 경우
            console.log('📭 모든 이미지 삭제됨')
            currentImageIndex.value = 1
          } else if (currentIndex >= results.value.length) {
            // 마지막 이미지를 삭제한 경우
            console.log('📄 마지막 이미지 삭제됨, 이전 이미지로 이동')
            currentImageIndex.value = results.value.length
          } else {
            console.log('📄 중간 이미지 삭제됨, 인덱스 유지')
          }

          console.log('조정된 이미지 인덱스:', currentImageIndex.value)

          // 현재 결과 강제 업데이트 (반응성 보장)
          console.log('📸 현재 결과 업데이트:', currentResult.value)

          // Vue.nextTick을 사용하여 DOM 업데이트 보장
          await nextTick()

          // ImageViewer 컴포넌트에 현재 결과 변경 알림
          if (imageViewer.value && imageViewer.value.updateCurrentImage) {
            imageViewer.value.updateCurrentImage(currentResult.value)
          }

          // 저신뢰도 이미지 목록 재구성
          rebuildLowConfidenceImages(results.value)

          console.log('✅ UI 업데이트 완료')
        } else {
          console.error('❌ 파일 삭제 실패:', response.message)
          handleStatusMessage({
            message: response.message || '파일 삭제에 실패했습니다.',
            type: 'error',
            icon: 'mdi-alert-circle',
          })
        }
      } catch (error) {
        console.error('❌ 파일 삭제 오류:', error)
        console.error('오류 상세:', error.response?.data || error.message)
        handleStatusMessage({
          message: '파일 삭제 중 오류가 발생했습니다.',
          type: 'error',
          icon: 'mdi-alert-circle',
        })
      } finally {
        isDeletingFile.value = false
        showDeleteConfirmDialog.value = false
        console.log('🔄 삭제 완료, 상태 초기화')
      }
    }

    const handleDeleteCancel = () => {
      showDeleteConfirmDialog.value = false
    }

    // 프로젝트 로드 처리
    const handleLoadSelectedProject = async (projectName) => {
      try {
        isLoadingProject.value = true
        loadProjectError.value = null
        loadingImageProgress.value = 0

        // 프로젝트 로드 시 색상 캐시 초기화하여 새로운 랜덤 색상 배정
        clearColorCache()

        console.log('프로젝트 로드 시작:', projectName)

        // 프로젝트 데이터 로드
        const projectData = await loadSelectedProject(projectName)

        if (projectData.success) {
          // 프로젝트 정보 설정
          projectPath.value = projectData.projectPath

          // 🎯 class_info 기반 클래스 정보 업데이트
          console.log('=== 프로젝트 로드: 클래스 정보 처리 시작 ===')
          console.log('서버에서 받은 projectData:', projectData)

          let projectClasses = null

          // 1. class_info 우선 확인 (서버에서 전달)
          if (
            projectData.class_info &&
            Array.isArray(projectData.class_info) &&
            projectData.class_info.length > 0
          ) {
            console.log('✅ 프로젝트 파일에서 class_info 발견:', projectData.class_info)

            // class_info를 클래스 매핑 객체로 변환: [{"id": 0, "name": "person"}, ...] -> {0: "person", 1: "helmet", ...}
            const classMapping = {}
            projectData.class_info.forEach((classInfo) => {
              if (classInfo.id !== undefined && classInfo.name) {
                classMapping[classInfo.id] = classInfo.name
              }
            })

            console.log('✅ class_info를 클래스 매핑으로 변환:', classMapping)
            console.log('🎯 프로젝트 저장 시와 동일한 클래스 정보 사용')

            projectClasses = classMapping
          } else if (projectData.classes && projectData.classes.length > 0) {
            // 2. 기존 classes 배열 사용 (하위 호환성)
            console.log('⚠️ class_info가 없어서 기존 classes 배열 사용:', projectData.classes)

            const classMapping = {}
            projectData.classes.forEach((className, index) => {
              classMapping[index] = className
            })

            projectClasses = classMapping
          } else {
            // 3. 현재 로드된 모델의 클래스 정보 사용
            console.log('📡 프로젝트에 클래스 정보가 없어서 현재 모델의 클래스 정보 사용')

            if (modelClasses.value && Object.keys(modelClasses.value).length > 0) {
              projectClasses = modelClasses.value
              console.log('✅ 현재 모델의 클래스 정보 사용:', projectClasses)
            } else {
              console.warn('❌ 현재 모델의 클래스 정보도 없음')
            }
          }

          // 클래스 정보 업데이트
          if (projectClasses && Object.keys(projectClasses).length > 0) {
            console.log('🔄 사이드바 클래스 선택 UI 업데이트 시작')
            updateAvailableClassesFromModel(projectClasses)
            console.log('✅ 사이드바 클래스 선택 UI 업데이트 완료')

            // 🎯 프로젝트 class_info를 ImageViewer에서 사용할 수 있도록 저장
            if (projectData.class_info && Array.isArray(projectData.class_info)) {
              projectClassInfo.value = projectData.class_info
              console.log('✅ 프로젝트 class_info 저장 완료:', projectClassInfo.value)
            } else {
              // class_info가 없는 경우 projectClasses를 class_info 형태로 변환
              const convertedClassInfo = Object.entries(projectClasses)
                .map(([id, name]) => ({
                  id: parseInt(id),
                  name: name,
                }))
                .sort((a, b) => a.id - b.id)

              projectClassInfo.value = convertedClassInfo
              console.log('✅ 변환된 class_info 저장 완료:', projectClassInfo.value)
            }
          } else {
            console.warn('⚠️ 업데이트할 클래스 정보가 없음')
            projectClassInfo.value = [] // 클래스 정보가 없으면 빈 배열로 설정
          }

          // 결과 데이터 설정
          results.value = projectData.results || []
          labelingComplete.value = true
          currentImageIndex.value = 1

          // 저신뢰도 이미지 정보 설정 (서버에서 받은 정보 직접 사용)
          setLowConfidenceImagesFromProject(projectData.lowConfidenceImages, results.value)

          // 편집모드 자동 해제
          if (imageViewer.value?.exitEditMode) {
            imageViewer.value.exitEditMode()
          }

          // 다이얼로그 닫기
          showLoadProjectDialog.value = false
          loadProjectSuccess.value = true

          console.log('프로젝트 로드 완료:', {
            projectName: projectData.projectName,
            totalImages: projectData.totalImages,
            classCount: projectClasses ? Object.keys(projectClasses).length : 0,
            hasClassInfo: projectData.class_info ? true : false,
          })

          // 성공 메시지 표시
          handleStatusMessage({
            message: `프로젝트 "${projectName}"를 성공적으로 불러왔습니다.`,
            type: 'success',
            icon: 'mdi-check-circle',
          })
        }
      } catch (error) {
        console.error('프로젝트 로드 오류:', error)
        loadProjectError.value = error.message || '프로젝트를 불러올 수 없습니다.'

        // 오류 메시지 표시
        handleStatusMessage({
          message: `프로젝트 로드 실패: ${error.message}`,
          type: 'error',
          icon: 'mdi-alert-circle',
        })
      } finally {
        isLoadingProject.value = false
        loadingImageProgress.value = 0
      }
    }

    // Keyboard shortcuts
    const handleKeyDown = (event) => {
      // 다이얼로그나 입력 필드가 활성화된 경우 단축키 비활성화
      const target = event.target
      if (
        target &&
        (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)
      ) {
        return
      }

      // 다이얼로그가 열려있는 경우 단축키 비활성화
      if (
        showLoadProjectDialog.value ||
        showHelpDialog.value ||
        showClassChangeAlert.value ||
        showDeleteConfirmDialog.value
      ) {
        return
      }

      const key = event.key.toLowerCase()

      // 다른 단축키들의 preventDefault 처리
      const shouldPreventDefault =
        [
          'e',
          'r',
          'b',
          'd',
          'a',
          'p',
          's',
          'f',
          'h',
          'g',
          'n',
          't',
          'm',
          '`',
          'home',
          'end',
          'arrowleft',
          'arrowright',
          'delete',
        ].includes(key) || /^[0-9]$/.test(key)

      if (shouldPreventDefault) {
        event.preventDefault()
        event.stopPropagation()
      }

      switch (key) {
        case 'p':
          openLoadProjectDialog()
          break
        case '`':
          showHelpDialog.value = !showHelpDialog.value
          break
        case 's':
        case 'arrowleft':
          prevImage()
          break
        case 'f':
        case 'arrowright':
          nextImage()
          break
        case 'home':
          goToImage(1)
          break
        case 'end':
          goToImage(results.value.length)
          break

        case 'm':
          // 이미지 중앙 정렬
          if (imageViewer.value?.resetZoom) {
            imageViewer.value.resetZoom()
          }
          break
        case 'e':
          // 편집 모드 활성화 (해제는 R키로만 가능)
          if (imageViewer.value?.toggleEditMode) {
            imageViewer.value.toggleEditMode()
          }
          break
        case 'r':
          // 편집 모드 해제
          if (imageViewer.value?.exitEditMode) {
            imageViewer.value.exitEditMode()
          }
          break
        case 'b':
          // 바운딩 박스 그리기 모드
          if (imageViewer.value?.startDrawingMode) {
            // 편집 모드가 아니면 그리기 모드로 진입되지 않으므로
            // 알림창은 실제로 그리기 모드가 활성화될 때만 표시
            const wasInEditMode = imageViewer.value?.editMode === 'edit'
            imageViewer.value.startDrawingMode()

            // 편집 모드였을 때만 그리기 모드 알림창 표시
            if (wasInEditMode) {
              drawingModeSnackbarKey.value = Date.now()
              showDrawingModeSnackbar.value = true
            }
          }
          break
        case 'd':
          // 선택된 바운딩 박스 삭제 - 편집모드에서만 가능
          if (imageViewer.value?.editMode !== 'edit') {
            // 편집모드가 아닐 때는 삭제 불가 알림
            handleStatusMessage({
              message: '편집 모드에서만 바운딩 박스를 삭제할 수 있습니다 (E키로 편집모드 활성화)',
              type: 'warning',
              icon: 'mdi-lock',
            })
          } else if (imageViewer.value?.deleteSelectedBox) {
            // 편집모드일 때만 삭제
            imageViewer.value.deleteSelectedBox()
          }
          break
        case 'a':
          // 모든 바운딩 박스 복사
          if (imageViewer.value?.copyAllBoxes) {
            imageViewer.value.copyAllBoxes()
          }
          break
        case 'h':
          // 바운딩 박스 숨기기/보이기 - 편집모드에서만 가능
          if (imageViewer.value?.editMode !== 'edit') {
            // 편집모드가 아닐 때는 숨기기/보이기 불가 알림
            handleStatusMessage({
              message:
                '편집 모드에서만 바운딩 박스를 숨기거나 표시할 수 있습니다 (E키로 편집모드 활성화)',
              type: 'warning',
              icon: 'mdi-lock',
            })
          } else if (imageViewer.value?.toggleBoxVisibility) {
            // 편집모드일 때만 숨기기/보이기
            imageViewer.value.toggleBoxVisibility()
          }
          break
        case 'g':
          // 숨겨진 바운딩 박스 모두 보이기 - 편집모드에서만 가능
          if (imageViewer.value?.editMode !== 'edit') {
            // 편집모드가 아닐 때는 기능 불가 알림
            handleStatusMessage({
              message:
                '편집 모드에서만 숨겨진 바운딩 박스를 표시할 수 있습니다 (E키로 편집모드 활성화)',
              type: 'warning',
              icon: 'mdi-lock',
            })
          } else if (imageViewer.value?.showAllHiddenBoxes) {
            // 편집모드일 때만 실행
            imageViewer.value.showAllHiddenBoxes()
          }
          break
        case 't':
          // 바운딩 박스 저장 - 편집모드 체크
          if (imageViewer.value?.editMode === 'edit') {
            // 편집모드에서는 저장 불가 알림 (상태 메시지 + 스낵바)
            handleStatusMessage({
              message: '편집모드 해제 후 저장할 수 있습니다 (R키로 편집모드 해제)',
              type: 'warning',
              icon: 'mdi-lock',
            })

            // 추가 스낵바 표시
            saveRestrictionSnackbarKey.value = Date.now()
            showSaveRestrictionSnackbar.value = true
          } else if (imageViewer.value?.saveBoundingBoxes) {
            // 편집모드가 아닐 때만 저장
            imageViewer.value.saveBoundingBoxes()
          }
          break
        case 'w':
          // 단계적 확대 (마우스 커서 중심)
          if (imageViewer.value?.stepZoomIn) {
            // 마우스 위치를 전달
            const mousePos = getMousePosition()
            imageViewer.value.stepZoomIn(mousePos)
          }
          break
        case 'q':
          // 단계적 축소 (마우스 커서 중심)
          if (imageViewer.value?.stepZoomOut) {
            // 마우스 위치를 전달
            const mousePos = getMousePosition()
            imageViewer.value.stepZoomOut(mousePos)
          }
          break
        case 'n':
          // 바운딩 박스 굵기 토글
          if (imageViewer.value?.toggleBoxThickness) {
            imageViewer.value.toggleBoxThickness()
          }
          break

        case 'delete':
          // 파일 삭제 - 프로젝트가 로드되어 있고 현재 이미지가 있을 때만 가능
          if (!projectPath.value || !currentResult.value) {
            handleStatusMessage({
              message: '프로젝트가 로드되어 있고 이미지가 있을 때만 파일을 삭제할 수 있습니다.',
              type: 'warning',
              icon: 'mdi-alert',
            })
          } else {
            showDeleteConfirmDialog.value = true
          }
          break

        default:
          // 숫자 키 (0-9) - 클래스 선택
          if (/^[0-9]$/.test(event.key)) {
            const classIndex = parseInt(event.key)
            if (imageViewer.value?.selectClass) {
              imageViewer.value.selectClass(classIndex)
            }
          }
          break
      }

      // Ctrl 조합 키 처리
      if (event.ctrlKey || event.metaKey) {
        switch (key) {
          case 'c':
            // Ctrl+C: 선택된 바운딩 박스 복사
            event.preventDefault()
            if (imageViewer.value?.copySelectedBox) {
              imageViewer.value.copySelectedBox()
            }
            break
          case 'v':
            // Ctrl+V: 복사된 바운딩 박스 붙여넣기
            event.preventDefault()
            if (imageViewer.value?.pasteBox) {
              imageViewer.value.pasteBox()
            }
            break
          case 'z':
            // Ctrl+Z: 작업 되돌리기
            event.preventDefault()
            if (imageViewer.value?.undoLastAction) {
              imageViewer.value.undoLastAction()
            }
            break
        }
      }
    }

    // Space 키 해제 처리
    // 마우스 위치 상태
    const mousePosition = ref({ x: window.innerWidth / 2, y: window.innerHeight / 2 })

    // 마우스 위치를 가져오는 함수
    const getMousePosition = () => {
      return mousePosition.value
    }

    // 마우스 위치 추적
    const updateMousePosition = (event) => {
      mousePosition.value = {
        x: event.clientX,
        y: event.clientY,
      }
    }

    const handleKeyUp = (event) => {
      // 다이얼로그나 입력 필드가 활성화된 경우 단축키 비활성화
      const target = event.target
      if (
        target &&
        (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)
      ) {
        return
      }

      // 다이얼로그가 열려있는 경우 단축키 비활성화
      if (
        showLoadProjectDialog.value ||
        showHelpDialog.value ||
        showClassChangeAlert.value ||
        showDeleteConfirmDialog.value
      ) {
        return
      }
    }

    // Lifecycle
    onMounted(() => {
      document.documentElement.style.setProperty(
        '--sidebar-width',
        sidebarRail.value ? '60px' : '360px',
      )
      // 키보드 이벤트를 즉각적으로 처리하기 위해 capture 옵션 사용
      window.addEventListener('keydown', handleKeyDown, { capture: true, passive: false })
      window.addEventListener('keyup', handleKeyUp, { capture: true, passive: false })
      // 마우스 위치 추적
      window.addEventListener('mousemove', updateMousePosition)
      refreshModels()
    })

    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeyDown, { capture: true, passive: false })
      window.removeEventListener('keyup', handleKeyUp, { capture: true, passive: false })
      window.removeEventListener('mousemove', updateMousePosition)
    })

    // Watchers
    watch(sidebarRail, (newVal) => {
      document.documentElement.style.setProperty('--sidebar-width', newVal ? '60px' : '360px')
      document.documentElement.classList.toggle('sidebar-rail', newVal)
      window.dispatchEvent(new Event('resize'))
    })

    // 모델 클래스가 변경될 때 availableClasses 업데이트
    watch(
      modelClasses,
      (newModelClasses) => {
        console.log('🔄 MainView: YOLO 모델 클래스 변화 감지됨')
        console.log('새로운 모델 클래스 (YOLO ID 순서):', newModelClasses)

        if (newModelClasses && Object.keys(newModelClasses).length > 0) {
          console.log('✅ 유효한 YOLO 모델 클래스 감지 - 사이드바 클래스 선택 UI 업데이트 시작')
          console.log('🎯 이 클래스 순서는 프로젝트 저장 시와 완전히 동일합니다')
          updateAvailableClassesFromModel(newModelClasses)
        } else {
          console.log('❌ 모델 클래스가 비어있음 - UI 업데이트 생략')
        }
      },
      { deep: true },
    )

    // 텍스트 프롬프트 적용 핸들러 (Grounding DINO용)
    const handleApplyPrompt = () => {
      console.log('💬 텍스트 프롬프트 적용:', textPrompt.value)
      promptApplied.value = true
    }

    return {
      // Refs
      darkTheme,
      sidebarVisible,
      sidebarRail,
      sidebarWidth,
      canvasRef,
      imageViewer,
      currentImageIndex,
      results,
      labelingComplete,
      currentStatusMessage,
      statusMessageType,
      statusMessageIcon,
      showLoadProjectDialog,
      showHelpDialog,
      showSaveConfirmDialog,
      pendingNavigationAction,
      showEditModeSnackbar,
      editModeSnackbarKey,
      editModeTitle,
      editModeMessage,
      editModeIcon,
      editModeColor,
      showSaveRestrictionSnackbar,
      saveRestrictionSnackbarKey,
      showDrawingModeSnackbar,
      drawingModeSnackbarKey,
      showAlreadySavedSnackbar,
      alreadySavedSnackbarKey,
      showCopyAllSnackbar,
      copyAllSnackbarKey,
      copyAllMessage,
      projectPath,
      projectList,
      projectPathError,
      loadProjectSuccess,
      loadProjectError,
      isLoadingProject,
      isLoadingImages,
      loadingImageProgress,
      isProcessing,
      progressPercent,
      currentFile,
      timeInfo,
      projectClassInfo,

      // From composables
      models,
      selectedModelType,
      selectedModel,
      modelDetails,
      modelLoaded,
      modelStatusMessage,
      modelStatusSuccess,
      isLoadingModel,
      deviceInfo,
      modelClasses,
      supportsTextPrompt,
      uploadedImages,
      imageStatusMessage,
      imageStatusSuccess,
      availableClasses,
      selectedClasses,
      selectAllClasses,
      allClassesSelected,
      showClassChangeAlert,
      classChangeMessage,
      selectedClassesInfo,
      classSelectionApplied,
      canStartLabeling,
      lowConfidenceImages,
      confidenceThreshold,
      textPrompt,
      boxThreshold,
      textThreshold,
      promptApplied,

      // Computed
      currentResult,
      currentFilename,

      // Methods
      refreshModels,
      loadModel,
      loadModelClasses,
      fetchModelDetails,
      handleApplyPrompt,
      handleFileUpload,
      clearUploadedFiles,
      toggleAllClasses,
      selectAllClassesChanged,
      checkSelectedClasses,
      applyClassSelection,
      dismissClassChangeAlert,
      loadSelectedProject,
      handleProjectSaveComplete,
      startLabeling,
      stopLabeling,
      prevImage,
      nextImage,
      goToImage,
      handleBboxEdit,
      onBboxChange,
      handleDeleteBox,
      handleStatusMessage,
      clearStatusMessage,
      openLoadProjectDialog,
      handleLoadSelectedProject,
      closeLoadProjectDialog,
      handleSaveConfirmYes,
      handleSaveConfirmNo,
      handleDeleteConfirm,
      handleDeleteCancel,

      // Dialog states
      showDeleteConfirmDialog,
      isDeletingFile,

      // Copied box state
      copiedBox,

      // Thick box mode
      thickBoxMode,

      // Confidence threshold
      confidenceThreshold,
    }
  },
}
</script>

<style scoped>
.main-area {
  transition: margin-left 0.2s;
  background-color: #000000 !important;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 반응형 레이아웃 컨테이너 */
.responsive-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  background-color: #000000 !important;
}

/* 이미지 뷰어 컨테이너 */
.image-viewer-container {
  flex: 1;
  min-height: 0; /* Flexbox에서 중요한 설정 */
  display: flex;
  background-color: #000000 !important;
  position: relative;
}

/* 이미지 뷰어 카드 */
.image-viewer-card {
  flex: 1;
  background: transparent !important;
  display: flex;
  flex-direction: column;
}

.no-image-card {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  background-color: #000000 !important;
  color: #ffffff !important;
}

:deep(.no-image-card .v-card-text) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
}

:deep(.v-main) {
  --v-layout-left: var(--sidebar-width);
  background-color: #000000 !important;
}

:deep(.v-container) {
  background-color: #000000 !important;
}

/* 텍스트 가독성 향상 */
:deep(.v-card-text) {
  color: #ffffff !important;
}

/* :deep(.v-btn) {
  color: #ffffff !important;
  font-weight: 500 !important;
} */

:deep(.v-list-item-title) {
  color: #ffffff !important;
  font-weight: 500 !important;
}

:deep(.v-list-item-subtitle) {
  color: #e0e0e0 !important;
}

:deep(.v-chip) {
  font-weight: 500 !important;
}

/* 반응형 미디어 쿼리 */
@media (max-width: 1200px) {
  .responsive-layout {
    padding: 0 8px;
  }

  .image-viewer-container {
    margin: 0 4px;
  }
}

@media (max-width: 768px) {
  .responsive-layout {
    padding: 0 4px;
  }

  .image-viewer-container {
    margin: 0 2px;
  }

  .main-area {
    height: 100vh;
    overflow: hidden;
  }
}

@media (max-width: 480px) {
  .responsive-layout {
    padding: 0 2px;
  }

  .image-viewer-container {
    margin: 0 1px;
  }
}

/* 세로 화면 (모바일 세로 모드) */
@media (max-height: 600px) {
  .responsive-layout {
    height: 100vh;
  }

  .image-viewer-container {
    min-height: 300px; /* 최소 높이 보장 */
  }
}

/* 매우 작은 화면 */
@media (max-width: 320px) {
  .responsive-layout {
    padding: 0;
  }

  .image-viewer-container {
    margin: 0;
  }
}

/* 모던 알림창 스타일 - 통일된 디자인 */
:deep(.modern-snackbar) {
  .v-snackbar__wrapper {
    border-radius: 16px !important;
    box-shadow:
      0 12px 40px rgba(0, 0, 0, 0.4),
      0 4px 16px rgba(0, 0, 0, 0.2) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    min-width: 420px !important;
  }

  .v-snackbar__content {
    padding: 20px 24px !important;
  }

  .notification-content {
    align-items: flex-start !important;
  }

  .notification-icon {
    margin-top: 2px !important;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) !important;
  }

  .notification-title {
    font-size: 1.1rem !important;
    line-height: 1.3 !important;
    margin-bottom: 4px !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
  }

  .notification-message {
    font-size: 0.9rem !important;
    opacity: 0.95 !important;
    line-height: 1.4 !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  }

  .notification-close-btn {
    margin-left: 16px !important;
    color: rgba(255, 255, 255, 0.8) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
  }

  .notification-close-btn:hover {
    background-color: rgba(255, 255, 255, 0.1) !important;
    color: rgba(255, 255, 255, 1) !important;
    transform: scale(1.05) !important;
  }
}

/* 편집 모드 알림창 특별 스타일 */
:deep(.edit-mode-snackbar) {
  .v-snackbar__wrapper {
    background: linear-gradient(
      135deg,
      rgba(33, 150, 243, 0.95),
      rgba(21, 101, 192, 0.95)
    ) !important;
  }
}

/* 저장 제한 알림창 특별 스타일 */
:deep(.save-restriction-snackbar) {
  .v-snackbar__wrapper {
    background: linear-gradient(
      135deg,
      rgba(255, 152, 0, 0.95),
      rgba(245, 124, 0, 0.95)
    ) !important;
  }
}

/* 바운딩 박스 그리기 모드 알림창 특별 스타일 */
:deep(.drawing-mode-snackbar) {
  .v-snackbar__wrapper {
    background: linear-gradient(
      135deg,
      rgba(76, 175, 80, 0.95),
      rgba(56, 142, 60, 0.95)
    ) !important;
  }
}

/* 이미 저장 완료 알림창 특별 스타일 */
:deep(.already-saved-snackbar) {
  .v-snackbar__wrapper {
    background: linear-gradient(
      135deg,
      rgba(3, 169, 244, 0.95),
      rgba(2, 136, 209, 0.95)
    ) !important;
  }
}
</style>
