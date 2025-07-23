<template>
  <div>
    <v-subheader class="text-subtitle-1 font-weight-bold">모델 설정</v-subheader>

    <v-btn
      @click="refreshModels"
      block
      size="small"
      color="#6c757d"
      class="mb-2">
      모델 목록 새로고침
    </v-btn>

    <v-select
      v-model="selectedModel"
      :items="models"
      label="모델 선택"
      dense
      outlined
      class="mb-2"
    ></v-select>

    <v-btn
      @click="loadModel"
      block
      size="small"
      color="primary"
      class="mb-3"
      :disabled="!selectedModel || isLoading"
      :loading="isLoading">
      {{ isLoading ? '모델 로드 중...' : '모델 로드' }}
    </v-btn>

    <v-card-text class="pa-0">
      <strong>디바이스:</strong>
      <span>{{ deviceInfo }}</span>
    </v-card-text>

    <!-- 에러 메시지 표시 -->
    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      density="compact"
      class="mt-2"
      closable
      @click:close="errorMessage = ''"
    >
      {{ errorMessage }}
    </v-alert>

    <!-- 모델 클래스 정보 표시 -->
    <div v-if="modelClasses && Object.keys(modelClasses).length > 0" class="mt-3">
      <v-divider class="my-2"></v-divider>
      <v-card-text class="pa-0">
        <strong>모델 클래스 ({{ Object.keys(modelClasses).length }}개):</strong>
        <v-chip-group column class="mt-2">
          <v-chip
            v-for="(className, classId) in modelClasses"
            :key="classId"
            size="small"
            color="success"
            variant="outlined"
            class="ma-1"
          >
            {{ classId }}: {{ className }}
          </v-chip>
        </v-chip-group>
      </v-card-text>
    </div>

    <!-- 모델 로드 상태 표시 -->
    <div v-else-if="selectedModel" class="mt-3">
      <v-divider class="my-2"></v-divider>
      <v-card-text class="pa-0">
        <v-alert
          type="info"
          variant="tonal"
          density="compact"
          text="모델을 로드하면 클래스 정보가 표시됩니다."
        ></v-alert>
      </v-card-text>
    </div>
  </div>
</template>

<script>
import { API_SERVER } from '@/utils/config.js'

export default {
  data() {
    return {
      selectedModel: '',
      models: [],
      deviceInfo: '알 수 없음',
      modelClasses: {},
      isLoading: false,
      errorMessage: ''
    }
  },
  methods: {
    async refreshModels() {
      try {
        const response = await fetch(`${API_SERVER}/models/`);
        if (!response.ok) throw new Error('모델 목록 조회 실패');
        const data = await response.json();
        this.models = data.models;
      } catch (error) {
        console.error('모델 목록 새로고침 오류:', error);
      }
    },
    async loadModel() {
      if (!this.selectedModel) return;

      this.isLoading = true;
      this.modelClasses = {}; // 로딩 시작 시 기존 클래스 정보 초기화
      this.errorMessage = ''; // 에러 메시지 초기화

      try {
        const response = await fetch(`${API_SERVER}/model/load/${this.selectedModel}`, {
          method: 'POST'
        });
        if (!response.ok) throw new Error('모델 로드 실패');

        // 디바이스 정보 업데이트
        const deviceResponse = await fetch(`${API_SERVER}/device/info`);
        if (deviceResponse.ok) {
          const deviceData = await deviceResponse.json();
          this.deviceInfo = deviceData.device || '알 수 없음';
        }

        // 모델 클래스 정보 가져오기
        await this.loadModelClasses();

        // 모델 로드 성공
      } catch (error) {
        console.error('모델 로드 오류:', error);
        // 모델 로드 실패 시 클래스 정보 초기화
        this.modelClasses = {};
        this.errorMessage = '모델 로드에 실패했습니다: ' + error.message;
      } finally {
        this.isLoading = false;
      }
    },
    async loadModelClasses() {
      try {
        const response = await fetch(`${API_SERVER}/model/classes`);
        if (response.ok) {
          const data = await response.json();
          this.modelClasses = data.classes || {};
          // 모델 클래스 정보 로드 완료
        } else {
          console.warn('모델 클래스 정보를 가져올 수 없습니다.');
          this.modelClasses = {};
        }
      } catch (error) {
        console.error('모델 클래스 정보 로드 오류:', error);
        this.modelClasses = {};
      }
    }
  },
  mounted() {
    this.refreshModels();
  }
}
</script>

<style scoped>
strong {
  font-weight: 600;
}
</style>
