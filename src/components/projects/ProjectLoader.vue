<template>
  <div class="project-loader">
    <!-- 프로젝트 불러오기 UI -->
    <div class="project-section">
      <div class="font-weight-bold mb-3 mt-4 px-2 d-flex align-center ga-2">
        <div class="bg-grey-darken-3 bg-opacity-30 text-amber-lighten-1 pa-1 rounded d-flex">
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
            class="lucide lucide-folder-input-icon lucide-folder-input"
          >
            <path
              d="M2 9V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H20a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-1"
            />
            <path d="M2 13h10" />
            <path d="m9 16 3-3-3-3" />
          </svg>
        </div>
        프로젝트 불러오기
      </div>

      <!-- 프로젝트 불러오기 버튼 -->
      <div class="px-2">
        <v-btn block color="white" variant="tonal" @click="openLoadProjectDialog"
          ><svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="lucide lucide-arrow-right-icon lucide-arrow-right mr-2"
          >
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
          프로젝트 불러오기
        </v-btn>
      </div>

      <!-- 현재 프로젝트 상태 표시 -->
      <template v-if="projectPath">
        <v-alert density="compact" type="success" variant="tonal" class="mb-2">
          <div class="project-info">
            <div class="d-flex align-center mb-1">
              <v-icon icon="mdi-folder-multiple" color="success" class="mr-2" size="small"></v-icon>
              <strong class="project-label">현재 프로젝트:</strong>
            </div>
            <div class="project-path" :title="projectPath">
              {{ displayProjectPath }}
            </div>
            <div v-if="totalImages" class="project-stats mt-1">
              <v-icon icon="mdi-image-multiple" size="x-small" class="mr-1"></v-icon>
              <small>{{ totalImages }}개 이미지</small>
            </div>
          </div>
        </v-alert>
      </template>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProjectLoader',
  props: {
    projectPath: {
      type: String,
      default: '',
    },
    totalImages: {
      type: Number,
      default: 0,
    },
  },
  emits: ['open-load-project'],
  computed: {
    displayProjectPath() {
      if (!this.projectPath) return ''

      // 경로가 너무 긴 경우 마지막 부분만 표시
      const pathParts = this.projectPath.split('/')
      if (pathParts.length > 3) {
        // 처음 부분과 마지막 2-3개 부분만 보이게 함
        const start = pathParts[0] || pathParts[1]
        const end = pathParts.slice(-2).join('/')
        return `${start}/...//${end}`
      }

      return this.projectPath
    },
  },
  methods: {
    // MainView의 프로젝트 불러오기 다이얼로그를 열도록 이벤트 발생
    openLoadProjectDialog() {
      this.$emit('open-load-project')
    },
  },
}
</script>

<style scoped>
.project-loader {
  width: 100%;
}

.project-section {
  margin-bottom: 16px;
}

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

.v-alert {
  margin-bottom: 0;
}

/* 프로젝트 정보 스타일링 */
.project-info {
  width: 100%;
  min-width: 0; /* flex 아이템에서 텍스트 오버플로우 방지 */
}

.project-label {
  font-size: 0.85rem;
  color: #4caf50;
}

.project-path {
  font-size: 0.8rem;
  color: #e0e0e0;
  word-break: break-all;
  line-height: 1.3;
  margin: 2px 0;
  padding: 2px 4px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.project-stats {
  color: #81c784;
  font-size: 0.75rem;
}

/* 사이드바가 축소된 상태에서의 스타일 */
:deep(.v-navigation-drawer--rail) .project-path {
  display: none;
}

:deep(.v-navigation-drawer--rail) .project-label {
  font-size: 0.7rem;
}
</style>
