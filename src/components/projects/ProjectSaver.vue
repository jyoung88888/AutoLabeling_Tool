<template>
  <div class="project-saver">
    <!-- 프로젝트 저장 섹션 헤더 -->
    <v-list-subheader
      class="text-subtitle-1 font-weight-bold text-wrap pa-0"
      style="color: #e0e0e0"
    >
      <div class="mb-2 mt-4 px-2">
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
          class="lucide lucide-save-icon lucide-save"
        >
          <path
            d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"
          />
          <path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7" />
          <path d="M7 3v4a1 1 0 0 0 1 1h7" />
        </svg>
        프로젝트 저장
      </div>
    </v-list-subheader>

    <!-- 프로젝트 저장 버튼 -->
    <v-list-item>
      <v-btn
        block
        variant="tonal"
        class="mb-2"
        @click="openSaveProjectDialog"
        :disabled="!canSaveProject || !hasResults"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="lucide lucide-save-icon lucide-save mr-2"
        >
          <path
            d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"
          />
          <path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7" />
          <path d="M7 3v4a1 1 0 0 0 1 1h7" />
        </svg>
        프로젝트 저장
      </v-btn>
    </v-list-item>

    <!-- 저장 조건 안내 -->
    <v-list-item v-if="!canSaveProject || !hasResults">
      <v-alert density="compact" type="info" variant="tonal" class="mb-2">
        <div class="text-body-2">자동라벨링 완료 후 저장 가능합니다.</div>
      </v-alert>
    </v-list-item>

    <!-- 저장 가능 안내 -->
    <v-list-item v-if="canSaveProject && hasResults">
      <v-alert density="compact" type="success" variant="tonal" class="mb-2">
        <div class="text-body-2">프로젝트 저장이 가능합니다! 위 버튼을 클릭하세요.</div>
      </v-alert>
    </v-list-item>

    <!-- 프로젝트 저장 다이얼로그 -->
    <v-dialog v-model="showSaveProjectDialog" max-width="600" persistent>
      <v-card theme="dark">
        <v-card-title class="headline d-flex align-center">
          <v-icon icon="mdi-content-save" class="mr-2" color="primary"></v-icon>
          프로젝트 저장
        </v-card-title>

        <v-card-text>
          <v-alert density="compact" type="info" variant="tonal" border="start" class="mb-3">
            <p><strong>저장 내용:</strong></p>
            <ul class="ml-4 mt-1">
              <li>이미지 파일 ({{ results.length }}개)</li>
              <li>라벨링 결과 (.txt 파일)</li>
              <li>프로젝트 정보 파일 (.json)</li>
              <li v-if="availableClasses.length > 0">
                클래스 정보 ({{ availableClasses.length }}개 클래스)
              </li>
              <li v-else>클래스 정보 (박스에서 자동 추출)</li>
            </ul>
          </v-alert>

          <v-text-field
            v-model="projectName"
            label="프로젝트 이름"
            variant="outlined"
            density="compact"
            :error-messages="projectNameError ? ['프로젝트 이름을 입력해주세요'] : []"
            prepend-inner-icon="mdi-folder-edit"
            class="mb-3"
            placeholder="예: my_labeling_project"
          />

          <!-- 저장 진행 상태 -->
          <div v-if="isSavingProject" class="mt-4">
            <v-card flat class="progress-card">
              <div class="progress-bar-wrapper pa-3">
                <v-progress-linear
                  :model-value="Math.min(savingProgress, 100)"
                  color="#2196F3"
                  height="12"
                  bg-color="#444"
                  class="mb-2"
                  striped
                  stream
                ></v-progress-linear>
                <div class="progress-percent text-body-2 text-center font-weight-bold">
                  {{ Math.round(Math.min(savingProgress, 100)) }}%
                </div>
              </div>

              <v-divider></v-divider>

              <div class="current-file-info pa-3">
                <div class="text-subtitle-2 mb-1">
                  <v-icon
                    icon="mdi-database-export"
                    size="small"
                    class="mr-1"
                    color="#2196F3"
                  ></v-icon>
                  현재 진행:
                </div>
                <div class="text-body-2">
                  <v-icon icon="mdi-file-export" class="mr-1" size="small" color="#2196F3"></v-icon>
                  {{ currentSavingFile || '프로젝트 데이터 저장 중...' }}
                </div>
              </div>
            </v-card>
          </div>

          <v-alert
            v-if="saveProjectSuccess"
            density="compact"
            type="success"
            variant="tonal"
            border="start"
            class="mt-3"
          >
            프로젝트가 성공적으로 저장되었습니다!
          </v-alert>

          <v-alert
            v-if="saveProjectError"
            density="compact"
            type="error"
            variant="tonal"
            border="start"
            class="mt-3"
          >
            {{ saveProjectError }}
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeSaveProjectDialog" :disabled="isSavingProject">
            취소
          </v-btn>
          <v-btn
            color="primary"
            @click="saveProject"
            :disabled="!projectName || isSavingProject"
            :loading="isSavingProject"
            prepend-icon="mdi-content-save"
          >
            저장
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  name: 'ProjectSaver',
  props: {
    // 저장 가능 여부
    canSaveProject: {
      type: Boolean,
      default: false,
    },
    // 결과 데이터 존재 여부
    hasResults: {
      type: Boolean,
      default: false,
    },
    // 저신뢰도 이미지 데이터
    lowConfidenceImages: {
      type: Array,
      default: () => [],
    },
    // 클래스 정보
    availableClasses: {
      type: Array,
      default: () => [],
    },
    // 라벨링 결과 데이터
    results: {
      type: Array,
      default: () => [],
    },
    // 모델 클래스 정보
    modelClasses: {
      type: Object,
      default: () => ({}),
    },
    // Grounding DINO 프롬프트 클래스 정보
    promptClassInfo: {
      type: Array,
      default: () => null,
    },
  },
  data() {
    return {
      // 프로젝트 저장 다이얼로그 상태
      showSaveProjectDialog: false,
      projectName: '',
      projectNameError: false,

      // 프로젝트 저장 상태
      isSavingProject: false,
      savingProgress: 0,
      currentSavingFile: '',
      saveProjectSuccess: false,
      saveProjectError: null,
    }
  },
  methods: {
    // 프로젝트 저장 다이얼로그 열기
    openSaveProjectDialog() {
      console.log('프로젝트 저장 다이얼로그 열기 시도')
      console.log('저장 조건 확인:', {
        canSaveProject: this.canSaveProject,
        hasResults: this.hasResults,
        resultsLength: this.results?.length || 0,
        availableClassesLength: this.availableClasses?.length || 0,
      })

      // 저장 조건 확인
      if (!this.canSaveProject) {
        console.error('저장 불가: canSaveProject가 false입니다.')
        return
      }

      if (!this.hasResults || !this.results || this.results.length === 0) {
        console.error('저장 불가: 라벨링 결과가 없습니다.')
        return
      }

      console.log('조건 확인 완료 - 프로젝트 저장 다이얼로그 열기')
      this.showSaveProjectDialog = true
      this.resetSaveDialogState()
    },

    // 프로젝트 저장 다이얼로그 닫기
    closeSaveProjectDialog() {
      if (!this.isSavingProject) {
        this.showSaveProjectDialog = false
        this.resetSaveDialogState()
      }
    },

    // 저장 다이얼로그 상태 초기화
    resetSaveDialogState() {
      this.projectName = ''
      this.projectNameError = false
      this.savingProgress = 0
      this.currentSavingFile = ''
      this.saveProjectSuccess = false
      this.saveProjectError = null
    },

    // 프로젝트 저장 실행
    async saveProject() {
      // 프로젝트 이름 검증
      if (!this.projectName || this.projectName.trim() === '') {
        this.projectNameError = true
        return
      }

      this.projectNameError = false
      this.isSavingProject = true
      this.savingProgress = 0
      this.currentSavingFile = '프로젝트 저장 준비 중...'
      this.saveProjectError = null

      try {
        // exportApi의 saveProjectLocal 함수 사용
        const { saveProjectLocal } = await import('@/api/exportApi')

        // 이미지 데이터를 올바른 형식으로 변환
        const images = this.results.map((result) => ({
          filename: result.filename,
          boxes: result.boxes || [],
          width: result.width || 0,
          height: result.height || 0,
        }))

        // 프로젝트 저장 데이터 구성
        const projectData = {
          projectName: this.projectName.trim(),
          images: images,
          lowConfidenceImages: this.lowConfidenceImages,
          modelClasses: this.modelClasses,
          promptClassInfo: this.promptClassInfo, // Grounding DINO 프롬프트 클래스 정보
        }

        console.log('프로젝트 저장 데이터:', {
          projectName: projectData.projectName,
          imageCount: projectData.images.length,
          lowConfidenceImagesCount: this.lowConfidenceImages.length,
          lowConfidenceImagesSample: this.lowConfidenceImages.slice(0, 3),
          promptClassInfo: projectData.promptClassInfo, // 디버깅용 로그 추가
        })

        this.currentSavingFile = '프로젝트 저장 중...'
        this.savingProgress = 50

        // 프로젝트 저장 API 호출
        const result = await saveProjectLocal(projectData)

        if (result.success) {
          this.savingProgress = 100
          this.currentSavingFile = '저장 완료!'
          this.saveProjectSuccess = true

          console.log('프로젝트 저장 성공:', result)

          // 성공 메시지 표시 및 다이얼로그 자동 닫기
          setTimeout(() => {
            this.showSaveProjectDialog = false
            this.$emit('save-complete', {
              success: true,
              projectPath: result.path,
              message: `프로젝트 '${this.projectName}'이(가) 성공적으로 저장되었습니다.`,
            })
          }, 2000)
        } else {
          throw new Error('프로젝트 저장에 실패했습니다.')
        }
      } catch (error) {
        console.error('프로젝트 저장 오류:', error)
        this.saveProjectError = `프로젝트 저장 실패: ${error.message}`
        this.savingProgress = 0
        this.currentSavingFile = ''

        // 실패 이벤트 발생
        this.$emit('save-complete', {
          success: false,
          message: `프로젝트 저장 실패: ${error.message}`,
        })
      } finally {
        this.isSavingProject = false
      }
    },

    // 저장 진행 상태 업데이트 (외부에서 호출 가능)
    updateSavingProgress(progress, currentFile) {
      this.savingProgress = progress
      this.currentSavingFile = currentFile
    },
  },
}
</script>

<style scoped>
.project-saver {
  width: 100%;
}

.progress-card {
  background-color: rgba(30, 30, 30, 0.8);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  padding: 10px;
  margin-bottom: 10px;
}

.progress-bar-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.progress-percent {
  font-size: 14px;
  font-weight: 600;
  color: #e0e0e0;
}

.current-file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-subtitle-2 {
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
}

.text-body-2 {
  font-size: 12px;
  font-weight: 400;
  color: #e0e0e0;
}
</style>
