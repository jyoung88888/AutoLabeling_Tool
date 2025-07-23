<template>
  <div>
    <!-- 사이드바가 접혔을 때 표시할 미니 사이드바 -->
    <v-navigation-drawer
      v-if="sidebarRail"
      permanent
      rail
      width="60"
      elevation="3"
      color="#1e1e1e"
      border
      class="sidebar-mini"
    >
      <!-- 상단 헤더 -->
      <v-list class="pa-0" bg-color="#1e1e1e">
        <v-list-item
          class="mt-2 mb-1"
          color="#e0e0e0"
        >
          <template #prepend>
            <v-img
              src="/img/auto-labeling-icon.svg"
              width="32"
              height="32"
              class="ml-1"
            ></v-img>
          </template>
        </v-list-item>
      </v-list>

      <!-- 상단 사이드바 펼치기 버튼 -->
      <div class="expand-btn-container">
        <v-btn
          variant="text"
          icon="mdi-chevron-right"
          @click.stop="handleExpandSidebar"
          color="#4f9cf5"
          size="small"
          class="expand-icon"
          elevation="2"
        ></v-btn>
      </div>
    </v-navigation-drawer>

    <!-- 메인 사이드바 -->
    <v-navigation-drawer
      v-else
      :model-value="sidebarVisible"
      @update:model-value="$emit('update:sidebarVisible', $event)"
      permanent
      :width="sidebarWidth"
      class="sidebar"
      elevation="3"
      color="#1e1e1e"
      border
    >
      <v-list-item
        class="mt-2 mb-3 py-5 px-4"
      >
        <template #prepend>
          <v-img
            src="/img/auto-labeling-icon.svg"
            width="36"
            height="36"
            class="mr-2"
          ></v-img>
        </template>
        <template #title>
          <div class="text-h5 font-weight-bold primary--text text-no-wrap" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #e0e0e0;">
            이미지 자동 라벨링
          </div>
        </template>
        <template v-slot:append>
          <v-btn
            variant="text"
            icon="mdi-chevron-left"
            @click.stop="handleCollapseSidebar"
            color="#4f9cf5"
          ></v-btn>
        </template>
      </v-list-item>

      <v-divider color="#333"></v-divider>

      <v-list density="compact" nav class="py-2 px-2" bg-color="#252525">
        <!-- 모델 설정 섹션 -->
        <ModelSettingsSection
          :models="models"
          :selected-model-type="selectedModelType"
          :model-details="modelDetails"
          :selected-model="selectedModel"
          :model-status-message="modelStatusMessage"
          :model-status-success="modelStatusSuccess"
          :device-info="deviceInfo"
          @update:selected-model-type="$emit('update:selectedModelType', $event)"
          @update:selected-model="$emit('update:selectedModel', $event)"
          @refresh-models="$emit('refreshModels')"
          @load-model="$emit('loadModel')"
          @fetch-model-details="$emit('fetchModelDetails', $event)"
        />

        <!-- 이미지 선택 섹션 -->
        <ImageSelectionSection
          :uploaded-images="uploadedImages"
          :image-status-message="imageStatusMessage"
          :image-status-success="imageStatusSuccess"
          @file-upload="$emit('fileUpload', $event)"
          @clear-files="$emit('clearFiles')"
        />

        <!-- 클래스 선택 섹션 -->
        <ClassSelectionSection
          v-if="modelLoaded"
          :available-classes="availableClasses"
          :selected-classes="selectedClasses"
          :select-all-classes="selectAllClasses"
          :all-classes-selected="allClassesSelected"
          :show-class-change-alert="showClassChangeAlert"
          :class-change-message="classChangeMessage"
          :selected-classes-info="selectedClassesInfo"
          :class-selection-applied="classSelectionApplied"
          :class-selection-message="imageStatusMessage"
          @update:selected-classes="$emit('update:selectedClasses', $event)"
          @update:select-all-classes="$emit('update:selectAllClasses', $event)"
          @toggle-all-classes="$emit('toggleAllClasses')"
          @select-all-classes-changed="$emit('selectAllClassesChanged', $event)"
          @check-selected-classes="$emit('checkSelectedClasses')"
          @apply-class-selection="$emit('applyClassSelection')"
          @dismiss-class-change-alert="$emit('dismissClassChangeAlert')"
        />

        <!-- 신뢰도 설정 섹션 -->
        <ConfidenceSettingsSection
          v-if="modelLoaded"
          :confidence-threshold="confidenceThreshold"
          @update:confidence-threshold="$emit('update:confidenceThreshold', $event)"
        />

        <!-- 자동 라벨링 시작 버튼 -->
        <v-list-item v-if="modelLoaded">
          <v-btn
            block
            @click="$emit('startLabeling')"
            color="#4caf50"
            size="small"
            :disabled="!canStartLabeling || !classSelectionApplied"
            class="mb-2"
            prepend-icon="mdi-play"
            style="color: #fff;"
          >
            자동 라벨링 시작
          </v-btn>
        </v-list-item>

        <!-- 자동 라벨링 진행 상태 표시 (버튼 바로 밑에) -->
        <v-list-item v-if="modelLoaded && isProcessing">
          <v-card
            class="processing-progress-card pa-3 mb-2"
            variant="outlined"
            color="#252525"
            border
          >
            <v-card-title class="pb-1 px-1 text-subtitle-2 font-weight-bold d-flex align-center justify-space-between" style="color: #e0e0e0;">
              <div class="d-flex align-center">
                <v-icon icon="mdi-cog-play" class="mr-1" color="#4f9cf5" size="small"></v-icon>
                라벨링 처리중...
              </div>
              <v-btn
                color="#f44336"
                size="x-small"
                icon="mdi-stop"
                variant="text"
                @click="$emit('stopLabeling')"
                class="ml-2"
              ></v-btn>
            </v-card-title>
            <v-divider color="#333" class="mb-2"></v-divider>
            <LabelingProgress
              :progress-percent="progressPercent"
              :current-file="currentFile"
              :time-info="timeInfo"
            />
          </v-card>
        </v-list-item>

        <!-- 프로젝트 로더 섹션 -->
        <ProjectLoader
          :project-path="projectPath"
          :total-images="results ? results.length : 0"
          @open-load-project="$emit('openLoadProject')"
        />

        <!-- 프로젝트 저장 섹션 -->
        <ProjectSaver
          ref="projectSaver"
          v-show="modelLoaded"
          :can-save-project="canSaveProject"
          :has-results="hasResults"
          :low-confidence-images="lowConfidenceImages"
          :available-classes="availableClasses"
          :model-classes="modelClasses"
          :results="results"
          @save-complete="$emit('projectSaveComplete', $event)"
        />

        <!-- 저신뢰도 이미지 목록 섹션 -->
        <LowConfidenceSection
          :low-confidence-images="lowConfidenceImages"
          @go-to-image="$emit('goToImage', $event)"
        />
      </v-list>
    </v-navigation-drawer>
  </div>
</template>

<script>
import ModelSettingsSection from './ModelSettingsSection.vue'
import ImageSelectionSection from './ImageSelectionSection.vue'
import ClassSelectionSection from './ClassSelectionSection.vue'
import ConfidenceSettingsSection from './ConfidenceSettingsSection.vue'
import LowConfidenceSection from './LowConfidenceSection.vue'
import ProjectLoader from '../projects/ProjectLoader.vue'
import ProjectSaver from '../projects/ProjectSaver.vue'
import LabelingProgress from '../ui/LabelingProgress.vue'

export default {
  name: 'LabelingSidebar',
  components: {
    ModelSettingsSection,
    ImageSelectionSection,
    ClassSelectionSection,
    ConfidenceSettingsSection,
    LowConfidenceSection,
    ProjectLoader,
    ProjectSaver,
    LabelingProgress
  },
  props: {
    sidebarVisible: {
      type: Boolean,
      default: true
    },
    sidebarRail: {
      type: Boolean,
      default: false
    },
    sidebarWidth: {
      type: Number,
      default: 360
    },
    models: {
      type: Array,
      default: () => []
    },
    selectedModelType: {
      type: Object,
      default: null
    },
    modelDetails: {
      type: Array,
      default: () => []
    },
    selectedModel: {
      type: Object,
      default: null
    },
    modelStatusMessage: {
      type: String,
      default: ''
    },
    modelStatusSuccess: {
      type: Boolean,
      default: false
    },
    deviceInfo: {
      type: Array,
      default: () => ['알 수 없음']
    },
    modelLoaded: {
      type: Boolean,
      default: false
    },
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
    },
    availableClasses: {
      type: Array,
      default: () => []
    },
    selectedClasses: {
      type: Object,
      default: () => ({})
    },
    selectAllClasses: {
      type: Boolean,
      default: false
    },
    allClassesSelected: {
      type: Boolean,
      default: false
    },
    showClassChangeAlert: {
      type: Boolean,
      default: false
    },
    classChangeMessage: {
      type: String,
      default: ''
    },
    selectedClassesInfo: {
      type: String,
      default: ''
    },
    classSelectionApplied: {
      type: Boolean,
      default: false
    },
    canStartLabeling: {
      type: Boolean,
      default: false
    },
    isProcessing: {
      type: Boolean,
      default: false
    },
    progressPercent: {
      type: Number,
      default: 0
    },
    currentFile: {
      type: String,
      default: ''
    },
    timeInfo: {
      type: Object,
      default: () => ({
        elapsed: '',
        eta: ''
      })
    },
    lowConfidenceImages: {
      type: Array,
      default: () => []
    },
    // ProjectSaver를 위한 추가 props
    canSaveProject: {
      type: Boolean,
      default: false
    },
    hasResults: {
      type: Boolean,
      default: false
    },
    results: {
      type: Array,
      default: () => []
    },
    // ProjectLoader를 위한 추가 props
    projectPath: {
      type: String,
      default: ''
    },
    // 모델 클래스 정보
    modelClasses: {
      type: Object,
      default: () => ({})
    },
    // 신뢰도 임계값
    confidenceThreshold: {
      type: Number,
      default: 0.5
    }
  },
  emits: [
    'update:selectedModelType',
    'update:selectedModel',
    'update:selectedClasses',
    'update:selectAllClasses',
    'update:confidenceThreshold',
    'refreshModels',
    'loadModel',
    'fetchModelDetails',
    'fileUpload',
    'clearFiles',
    'toggleAllClasses',
    'selectAllClassesChanged',
    'checkSelectedClasses',
    'applyClassSelection',
    'dismissClassChangeAlert',
    'startLabeling',
    'stopLabeling',
    'goToImage',
    'expandSidebar',
    'collapseSidebar',
    'update:sidebarVisible',
    'openLoadProject',
    'projectSaveComplete'
  ],
  methods: {
    handleExpandSidebar() {
      this.$emit('expandSidebar')
    },
    handleCollapseSidebar() {
      this.$emit('collapseSidebar')
    },
    // ProjectSaver 다이얼로그 열기
    openProjectSaverDialog() {
      console.log('LabelingSidebar: ProjectSaver 다이얼로그 열기 요청 수신');
      console.log('현재 상태:', {
        modelLoaded: this.modelLoaded,
        resultsLength: this.results?.length || 0,
        canSaveProject: this.canSaveProject,
        hasResults: this.hasResults
      });

      // ProjectSaver 컴포넌트가 렌더링될 때까지 잠시 대기
      this.$nextTick(() => {
        // ProjectSaver 컴포넌트 참조를 통해 다이얼로그 열기
        const projectSaver = this.$refs.projectSaver;
        if (projectSaver && typeof projectSaver.openSaveProjectDialog === 'function') {
          console.log('ProjectSaver 다이얼로그 열기 실행');
          projectSaver.openSaveProjectDialog();
        } else {
          console.error('ProjectSaver 컴포넌트를 찾을 수 없거나 openSaveProjectDialog 메서드가 없습니다.');
          console.log('ProjectSaver 참조:', projectSaver);

          // 강제로 다시 시도
          setTimeout(() => {
            const retryProjectSaver = this.$refs.projectSaver;
            if (retryProjectSaver && typeof retryProjectSaver.openSaveProjectDialog === 'function') {
              console.log('재시도: ProjectSaver 다이얼로그 열기 실행');
              retryProjectSaver.openSaveProjectDialog();
            } else {
              console.error('재시도 실패: ProjectSaver 컴포넌트를 찾을 수 없습니다.');
            }
          }, 200);
        }
      });
    }
  }
}
</script>

<style scoped>
.expand-btn-container {
  display: flex;
  justify-content: center;
  padding: 8px;
}

.expand-icon {
  background-color: rgba(79, 156, 245, 0.1) !important;
  border-radius: 50% !important;
}

.sidebar-mini {
  z-index: 1002;
}

.sidebar {
  z-index: 1001;
}

.processing-progress-card {
  background: rgba(255, 255, 255, 0.02) !important;
  border: 1px solid #333 !important;
}

:deep(.processing-progress-card .v-card-title) {
  padding: 8px 4px 4px 4px;
}
</style>
