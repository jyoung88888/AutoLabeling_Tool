<template>
  <div class="project-loader">
    <!-- 프로젝트 불러오기 UI -->
    <div class="project-section">
      <v-list-subheader class="text-subtitle-1 font-weight-bold text-wrap pa-0" style="color: #e0e0e0;">
        <div class="mb-2 mt-4 px-2">📂 프로젝트 불러오기</div>
      </v-list-subheader>

      <!-- 프로젝트 불러오기 버튼 -->
      <v-list-item>
        <v-btn
          block
          color="#4CAF50"
          size="small"
          class="mb-2"
          prepend-icon="mdi-folder-open"
          @click="openLoadProjectDialog"
          style="color: #fff;"
        >
          프로젝트 불러오기
        </v-btn>
      </v-list-item>

      <!-- 현재 프로젝트 상태 표시 -->
      <v-list-item v-if="projectPath">
        <v-alert
          density="compact"
          type="success"
          variant="tonal"
          class="mb-2"
        >
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
      </v-list-item>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProjectLoader',
  props: {
    projectPath: {
      type: String,
      default: ''
    },
    totalImages: {
      type: Number,
      default: 0
    }
  },
  emits: ['open-load-project'],
  computed: {
    displayProjectPath() {
      if (!this.projectPath) return '';

      // 경로가 너무 긴 경우 마지막 부분만 표시
      const pathParts = this.projectPath.split('/');
      if (pathParts.length > 3) {
        // 처음 부분과 마지막 2-3개 부분만 보이게 함
        const start = pathParts[0] || pathParts[1];
        const end = pathParts.slice(-2).join('/');
        return `${start}/...//${end}`;
      }

      return this.projectPath;
    }
  },
  methods: {
    // MainView의 프로젝트 불러오기 다이얼로그를 열도록 이벤트 발생
    openLoadProjectDialog() {
      this.$emit('open-load-project');
    }
  }
};
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
  color: #4CAF50;
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
  color: #81C784;
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
