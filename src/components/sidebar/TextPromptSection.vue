<template>
  <div class="px-2">
    <v-list-subheader
      class="text-subtitle-1 font-weight-bold text-wrap pa-0"
      style="color: #e0e0e0"
    >
      <div class="mb-2 mt-4 d-flex align-center ga-2">
        <div class="bg-grey-darken-3 bg-opacity-30 text-cyan pa-1 rounded d-flex">
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
          >
            <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
          </svg>
        </div>
        텍스트 프롬프트
      </div>
    </v-list-subheader>

    <v-list-item>
      <div class="text-prompt-section">
        <v-alert type="info" variant="tonal" density="compact" class="mb-3" border="start">
          탐지할 객체를 텍스트로 입력하세요. (예: person. helmet. car.)
        </v-alert>

        <v-textarea
          v-model="localTextPrompt"
          label="텍스트 프롬프트"
          placeholder="person. helmet. car. dog."
          rows="3"
          density="compact"
          variant="outlined"
          color="#4f9cf5"
          class="mb-2"
          hide-details
          hint="여러 객체는 마침표(.)로 구분하세요"
          persistent-hint
          @keydown.stop
        ></v-textarea>

        <v-btn
          block
          variant="tonal"
          class="mt-3"
          @click="applyPrompt"
          :disabled="!localTextPrompt || localTextPrompt.trim() === ''"
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
            class="lucide lucide-check-icon lucide-check mr-2"
          >
            <path d="M20 6 9 17l-5-5" />
          </svg>
          프롬프트 적용
        </v-btn>

        <!-- 프롬프트 적용 후 메시지 -->
        <v-alert
          v-if="promptApplied && appliedPrompt"
          type="success"
          variant="tonal"
          density="compact"
          class="mt-2"
          icon="mdi-text-box-check"
        >
          적용된 프롬프트: {{ appliedPrompt }}
        </v-alert>

        <!-- Box Threshold 설정 -->
        <div class="mt-4">
          <v-subheader class="text-caption px-0" style="color: #b0b0b0">
            박스 신뢰도 임계값: {{ boxThreshold }}
          </v-subheader>
          <v-slider
            v-model="localBoxThreshold"
            :min="0.1"
            :max="1.0"
            :step="0.05"
            color="#4f9cf5"
            track-color="#333"
            thumb-label
            density="compact"
            @update:model-value="updateBoxThreshold"
          ></v-slider>
        </div>

        <!-- Text Threshold 설정 -->
        <div class="mt-2">
          <v-subheader class="text-caption px-0" style="color: #b0b0b0">
            텍스트 신뢰도 임계값: {{ textThreshold }}
          </v-subheader>
          <v-slider
            v-model="localTextThreshold"
            :min="0.1"
            :max="1.0"
            :step="0.05"
            color="#4f9cf5"
            track-color="#333"
            thumb-label
            density="compact"
            @update:model-value="updateTextThreshold"
          ></v-slider>
        </div>
      </div>
    </v-list-item>
  </div>
</template>

<script>
export default {
  name: 'TextPromptSection',
  props: {
    textPrompt: {
      type: String,
      default: '',
    },
    boxThreshold: {
      type: Number,
      default: 0.3,
    },
    textThreshold: {
      type: Number,
      default: 0.25,
    },
    promptApplied: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:textPrompt', 'update:boxThreshold', 'update:textThreshold', 'applyPrompt'],
  data() {
    return {
      localTextPrompt: this.textPrompt,
      localBoxThreshold: this.boxThreshold,
      localTextThreshold: this.textThreshold,
      appliedPrompt: '',
    }
  },
  watch: {
    textPrompt(newVal) {
      this.localTextPrompt = newVal
    },
    boxThreshold(newVal) {
      this.localBoxThreshold = newVal
    },
    textThreshold(newVal) {
      this.localTextThreshold = newVal
    },
  },
  methods: {
    applyPrompt() {
      if (this.localTextPrompt && this.localTextPrompt.trim() !== '') {
        this.appliedPrompt = this.localTextPrompt
        this.$emit('update:textPrompt', this.localTextPrompt)
        this.$emit('applyPrompt')
      }
    },
    updateBoxThreshold(value) {
      this.$emit('update:boxThreshold', value)
    },
    updateTextThreshold(value) {
      this.$emit('update:textThreshold', value)
    },
  },
}
</script>

<style scoped>
.text-prompt-section {
  width: 100%;
}

:deep(.v-textarea .v-field) {
  background: rgba(255, 255, 255, 0.02);
  border-color: #333;
}

:deep(.v-textarea .v-field__input) {
  color: #e0e0e0;
  font-size: 14px;
}

:deep(.v-slider .v-slider-thumb) {
  background: #4f9cf5;
}

:deep(.v-slider .v-slider-track__fill) {
  background: #4f9cf5;
}
</style>
