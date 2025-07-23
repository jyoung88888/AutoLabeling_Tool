<template>
  <v-dialog
    v-model="show"
    max-width="400"
    @keydown.esc="$emit('cancel')"
    @click:outside="$emit('cancel')"
  >
    <v-card>
      <v-card-title class="text-h6">
        <v-icon start color="#3982d4" class="mr-2">mdi-shape</v-icon>
        클래스 선택
      </v-card-title>
      <v-card-text>
        <v-select
          v-model="selectedClass"
          :items="availableClasses"
          label="클래스"
          variant="outlined"
          class="dark-select"
          hide-details
          @keydown.stop
          :loading="availableClasses.length === 0"
          :disabled="availableClasses.length === 0"
        >
          <template v-slot:selection="{ item }">
            <v-chip
              :color="getClassColor(item.value)"
              label
              size="small"
              class="mr-2"
              text-color="white"
            >
              {{ item.value }}
            </v-chip>
          </template>
          <template v-slot:item="{ item, props }">
            <v-list-item v-bind="props">
              <template v-slot:prepend>
                <v-chip
                  :color="getClassColor(item.value)"
                  size="small"
                  class="mr-2"
                  text-color="white"
                >
                  {{ item.value }}
                </v-chip>
              </template>
            </v-list-item>
          </template>
        </v-select>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" text @click="$emit('cancel')">취소</v-btn>
        <v-btn
          color="primary"
          text
          @click="$emit('confirm', selectedClass)"
          :disabled="!selectedClass || availableClasses.length === 0 || (availableClasses.length === 1 && availableClasses[0] === 'unknown')"
        >
          확인
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { getClassColor as utilGetClassColor } from '@/utils/colorUtils.js';

export default {
  name: 'ClassSelectionDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    availableClasses: {
      type: Array,
      default: () => []
    },
    initialClass: {
      type: String,
      default: ''
    },
    classColors: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'confirm', 'cancel'],
  data() {
    return {
      selectedClass: ''
    }
  },
  computed: {
    show: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        this.selectedClass = this.initialClass || (this.availableClasses.length > 0 ? this.availableClasses[0] : '')
      }
    },
    initialClass(newVal) {
      this.selectedClass = newVal
    }
  },
  methods: {
    getClassColor(className) {
      // 통합 색상 유틸리티 사용
      return utilGetClassColor(className, this.classColors);
    }
  }
}
</script>

<style scoped>
.dark-select {
  color: white;
}

.v-card {
  background-color: #2a2a2a;
  color: white;
}

.v-card-title {
  background-color: #1976d2;
  color: white;
  margin-bottom: 0;
}

.v-card-text {
  padding: 20px;
}

.v-card-actions {
  padding: 16px 20px;
  background-color: #333;
}

:deep(.v-select .v-field) {
  background-color: #424242;
}

:deep(.v-select .v-field__input) {
  color: white;
}

:deep(.v-list) {
  background-color: #424242;
}

:deep(.v-list-item) {
  color: white;
}

:deep(.v-list-item:hover) {
  background-color: #555;
}
</style>
