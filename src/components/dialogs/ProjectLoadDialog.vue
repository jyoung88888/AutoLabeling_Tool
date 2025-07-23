<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="700"
    persistent
    @keydown.esc="handleClose"
  >
    <v-card theme="dark">
      <v-card-title class="headline d-flex align-center">
        <v-icon icon="mdi-folder-open" class="mr-2" color="primary"></v-icon>
        프로젝트 선택
        <v-spacer></v-spacer>
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="handleClose"
          :disabled="isLoading"
        ></v-btn>
      </v-card-title>

      <v-card-text>
        <!-- 경로 정보 -->
        <v-alert
          density="compact"
          type="info"
          variant="tonal"
          border="start"
          class="mb-3"
        >
          <p><strong>프로젝트 경로:</strong> uploaded_images/</p>
          <p><strong>유효한 프로젝트 구조:</strong></p>
          <ul class="ml-4 mt-1">
            <li><code>{날짜}/</code> (예: 2025-06-10)</li>
            <li class="ml-4"><code>{프로젝트명}/</code></li>
            <li class="ml-6"><code>images/</code> (이미지 파일)</li>
            <li class="ml-6"><code>labels/</code> (라벨 파일)</li>
            <li class="ml-6"><code>{프로젝트명}_info.json</code></li>
          </ul>
        </v-alert>

        <!-- 프로젝트 목록 -->
        <div v-if="!isLoadingProjects && internalProjectList.length > 0" class="project-list">
          <v-list density="compact" bg-color="#252525" rounded>
                          <v-list-item
                v-for="project in internalProjectList"
                :key="project.name"
              :title="project.projectFolder || project.name"
              :subtitle="`이미지: ${project.imageCount}개, 라벨: ${project.labelCount}개`"
              @click="selectProject(project)"
              :active="selectedProject?.name === project.name"
              class="project-item"
            >
              <template v-slot:prepend>
                <v-icon
                  icon="mdi-folder-multiple"
                  color="#4CAF50"
                ></v-icon>
              </template>
              <template v-slot:append>
                <div class="d-flex align-center">
                  <v-chip
                    size="small"
                    color="primary"
                    variant="tonal"
                  >
                    {{ formatDate(project.createdTime) }}
                  </v-chip>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </div>

        <!-- 로딩 상태 -->
        <div v-else-if="isLoadingProjects" class="d-flex justify-center align-center pa-4">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <span class="ml-3">프로젝트 목록 로딩 중...</span>
        </div>

        <!-- 빈 목록 -->
        <div v-else class="text-center pa-4">
          <v-icon icon="mdi-folder-remove" color="error" size="large" class="mb-2"></v-icon>
          <div>사용 가능한 프로젝트가 없습니다.</div>
        </div>

        <!-- 선택된 프로젝트 정보 -->
        <v-text-field
          v-if="selectedProject"
          :model-value="selectedProject.projectFolder || selectedProject.name"
          label="선택된 프로젝트"
          variant="outlined"
          density="compact"
          readonly
          prepend-inner-icon="mdi-folder"
          class="mt-3"
        />

        <!-- 프로젝트 로딩 진행 상태 -->
        <div v-if="isLoading" class="mt-4">
          <v-progress-linear
            :model-value="loadingImageProgress"
            color="primary"
            height="10"
            class="mb-2"
          ></v-progress-linear>
          <div class="text-center">프로젝트 이미지 로딩 중... {{ loadingImageProgress }}%</div>
        </div>

        <!-- 오류 메시지 -->
        <v-alert
          v-if="loadProjectError"
          type="error"
          variant="tonal"
          class="mt-3"
          closable
          @click:close="$emit('clear-error')"
        >
          {{ loadProjectError }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="handleClose"
          :disabled="isLoading"
          prepend-icon="mdi-close"
        >
          취소
        </v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          @click="loadProject"
          :disabled="!selectedProject || isLoading"
          :loading="isLoading"
          prepend-icon="mdi-download"
        >
          불러오기
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { API_SERVER } from '@/utils/config.js'

export default {
  name: 'ProjectLoadDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    projectList: {
      type: Array,
      default: () => []
    },
    projectPath: {
      type: String,
      default: ''
    },
    projectPathError: {
      type: Boolean,
      default: false
    },
    loadProjectSuccess: {
      type: Boolean,
      default: false
    },
    loadProjectError: {
      type: String,
      default: null
    },
    loadingImageProgress: {
      type: Number,
      default: 0
    }
  },
  emits: ['update:modelValue', 'load-project', 'close', 'clear-error'],
  data() {
    return {
      selectedProject: null,
      isLoadingProjects: false,
      internalProjectList: []
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        this.loadProjectList()
        // 다이얼로그가 열릴 때 ESC 키 리스너 추가
        this.addKeyboardListener()
      } else {
        // 다이얼로그가 닫힐 때 ESC 키 리스너 제거
        this.removeKeyboardListener()
      }
    }
  },
  beforeUnmount() {
    this.removeKeyboardListener()
  },
  methods: {
    async loadProjectList() {
      this.isLoadingProjects = true
      try {
        console.log('프로젝트 목록 로드 시작', `${API_SERVER}/api/list-projects`)
        const response = await fetch(`${API_SERVER}/api/list-projects`)

        if (!response.ok) {
          console.error('프로젝트 목록 API 응답 오류:', response.status, response.statusText)
          throw new Error(`프로젝트 목록 로드 실패: ${response.status}`)
        }

        const data = await response.json()
        console.log('프로젝트 목록 응답 데이터:', data)

        if (data.success && data.projects) {
          console.log(`프로젝트 ${data.projects.length}개 발견`)
          // 내부 상태에 프로젝트 목록 저장
          this.internalProjectList = data.projects
          // 부모 컴포넌트로도 전달 (호환성)
          this.$emit('update-project-list', data.projects)
        } else {
          console.warn('프로젝트 목록이 비어있거나 응답 형식이 올바르지 않습니다:', data)
          this.internalProjectList = []
          this.$emit('update-project-list', [])
        }
      } catch (error) {
        console.error('프로젝트 목록 로드 오류:', error)
        this.$emit('load-error', '프로젝트 목록을 불러올 수 없습니다.')
      } finally {
        this.isLoadingProjects = false
      }
    },

    selectProject(project) {
      this.selectedProject = project
    },

    loadProject() {
      if (this.selectedProject) {
        this.$emit('load-project', this.selectedProject.name)
      }
    },

    handleClose() {
      if (!this.isLoading) {
        this.selectedProject = null
        this.$emit('close')
      }
    },

    handleKeydown(event) {
      if (event.key === 'Escape') {
        this.handleClose()
      }
    },

    addKeyboardListener() {
      document.addEventListener('keydown', this.handleKeydown)
    },

    removeKeyboardListener() {
      document.removeEventListener('keydown', this.handleKeydown)
    },

    formatDate(timestamp) {
      return new Date(timestamp * 1000).toLocaleDateString()
    }
  }
}
</script>

<style scoped>
.project-list {
  max-height: 400px;
  overflow-y: auto;
}

.project-item {
  transition: background-color 0.2s;
}

.project-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.v-progress-linear {
  border-radius: 4px;
}
</style>
