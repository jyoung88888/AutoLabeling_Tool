<template>
  <v-dialog
    v-model="dialogVisible"
    max-width="500"
    class="keyboard-shortcuts-dialog"
    @keydown.esc="closeDialog"
  >
    <v-card>
      <v-card-title class="text-h6">
        <v-icon start color="#3982d4">mdi-keyboard</v-icon>
        바운딩 박스 모드 단축키
      </v-card-title>
      <v-card-text>
        <div class="shortcuts-grid">
          <div class="shortcut-group">
            <div class="shortcut-title">이미지 탐색</div>
            <div class="shortcut-item">
              <div class="shortcut-key">←</div>
              <div class="shortcut-key">S</div>
              <div class="shortcut-desc">이전 이미지</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">→</div>
              <div class="shortcut-key">F</div>
              <div class="shortcut-desc">다음 이미지</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Home</div>
              <div class="shortcut-desc">첫 번째 이미지로 이동</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">End</div>
              <div class="shortcut-desc">마지막 이미지로 이동</div>
            </div>
          </div>

          <div class="shortcut-group">
            <div class="shortcut-title">이미지 조작</div>
            <div class="shortcut-item">
              <div class="shortcut-key">M</div>
              <div class="shortcut-desc">이미지 중앙 정렬</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Ctrl</div>
              <div class="shortcut-key">+</div>
              <div class="shortcut-key">마우스 휠</div>
              <div class="shortcut-desc">마우스 커서 중심 확대/축소 </div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Space</div>
              <div class="shortcut-key">+</div>
              <div class="shortcut-key">드래그</div>
              <div class="shortcut-desc">이미지 이동</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">W</div>
              <div class="shortcut-desc">단계적 확대 (25%-400% 순환)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Q</div>
              <div class="shortcut-desc">단계적 축소 (400%-25% 순환)</div>
            </div>
          </div>
          <div class="shortcut-group">
            <div class="shortcut-title">바운딩 박스 편집</div>
            <div class="shortcut-item">
              <div class="shortcut-key">E</div>
              <div class="shortcut-desc">편집 모드 활성화</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">R</div>
              <div class="shortcut-desc">편집 모드 해제 (저장하지 않음)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">B</div>
              <div class="shortcut-desc">바운딩 박스 그리기 (편집 모드 전용)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">D</div>
              <div class="shortcut-desc">바운딩 박스 삭제 (편집 모드 전용)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">T</div>
              <div class="shortcut-desc">바운딩 박스 변경사항 저장 (편집모드에서는 저장 불가)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">0-9</div>
              <div class="shortcut-desc">클래스 선택</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Ctrl</div>
              <div class="shortcut-key">+</div>
              <div class="shortcut-key">C</div>
              <div class="shortcut-desc">선택된 바운딩 박스 복사</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Ctrl</div>
              <div class="shortcut-key">+</div>
              <div class="shortcut-key">V</div>
              <div class="shortcut-desc">복사된 바운딩 박스 붙여넣기</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Ctrl</div>
              <div class="shortcut-key">+</div>
              <div class="shortcut-key">Z</div>
              <div class="shortcut-desc">작업 되돌리기 (최대 10단계)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">A</div>
              <div class="shortcut-desc">모든 바운딩 박스 복사 (편집 모드 전용)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">H</div>
              <div class="shortcut-desc">선택된 바운딩 박스와 라벨 숨기기/보이기 (편집 모드 전용)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">G</div>
              <div class="shortcut-desc">숨겨진 바운딩 박스 모두 보이기 (편집 모드 전용)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">N</div>
              <div class="shortcut-desc">바운딩 박스 굵기 굵게/얇게 토글 (편집 모드 전용)</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Shift</div>
              <div class="shortcut-key">+</div>
              <div class="shortcut-key">클릭</div>
              <div class="shortcut-desc">바운딩 박스 다중 선택/해제 (편집 모드 전용)</div>
            </div>

          </div>

          <div class="shortcut-group">
            <div class="shortcut-title">기타</div>
            <div class="shortcut-item">
              <div class="shortcut-key">`</div>
              <div class="shortcut-desc">단축키 도움말</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">P</div>
              <div class="shortcut-desc">프로젝트 불러오기</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Delete</div>
              <div class="shortcut-desc">현재 이미지 파일 및 라벨 파일 삭제</div>
            </div>
            <div class="shortcut-item">
              <div class="shortcut-key">Esc</div>
              <div class="shortcut-desc">다이얼로그 닫기</div>
            </div>
          </div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" text @click="closeDialog">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'KeyboardShortcutsDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  computed: {
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  },
  methods: {
    closeDialog() {
      this.dialogVisible = false;
    }
  }
};
</script>

<style scoped>
:deep(.keyboard-shortcuts-dialog .v-card) {
  background-color: #1e1e1e;
  color: #e0e0e0;
  border: 1px solid #333;
}

:deep(.keyboard-shortcuts-dialog .v-card-title) {
  color: #fff;
  border-bottom: 1px solid #333;
  font-size: 16px;
}

.shortcuts-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.shortcut-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-title {
  font-weight: 600;
  color: #3982d4;
  margin-bottom: 4px;
  font-size: 14px;
}

.shortcut-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.shortcut-key {
  background-color: #333;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  min-width: 24px;
  text-align: center;
  font-family: monospace;
  display: inline-block;
}

.shortcut-desc {
  font-size: 13px;
  color: #bbb;
  flex: 1;
}
</style>
