<template>
  <div class="class-legend-container" v-if="classInfo && classInfo.length > 0">
    <div class="legend-header">
      <v-icon icon="mdi-format-list-numbered" size="small" class="mr-2"></v-icon>
      <span class="legend-title">클래스 범례</span>
    </div>
    <div class="legend-content">
      <div
        v-for="classItem in classInfo"
        :key="classItem.id"
        class="legend-item"
        :style="{ borderColor: getClassColor(classItem.name) }"
      >
        <div class="class-id">{{ classItem.id }}</div>
        <div class="class-name">{{ classItem.name }}</div>
        <div
          class="class-color-indicator"
          :style="{ backgroundColor: getClassColor(classItem.name) }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script>
import { getClassColor } from '@/utils/colorUtils.js'

export default {
  name: 'ClassLegend',
  props: {
    classInfo: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    getClassColor(className) {
      return getClassColor(className, {})
    }
  }
}
</script>

<style scoped>
.class-legend-container {
  background: rgba(30, 30, 30, 0.95);
  border: 1px solid #333;
  border-radius: 8px;
  padding: 12px;
  margin: 8px;
  max-width: 300px;
  backdrop-filter: blur(8px);
}

.legend-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #444;
}

.legend-title {
  color: #e0e0e0;
  font-size: 14px;
  font-weight: 600;
}

.legend-content {
  max-height: 200px;
  overflow-y: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  margin: 2px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  border-left: 3px solid;
  transition: all 0.2s ease;
}

.legend-item:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(2px);
}

.class-id {
  color: #4f9cf5;
  font-weight: bold;
  font-size: 12px;
  min-width: 24px;
  text-align: center;
  background: rgba(79, 156, 245, 0.2);
  border-radius: 4px;
  padding: 2px 4px;
  margin-right: 8px;
}

.class-name {
  color: #e0e0e0;
  font-size: 12px;
  flex: 1;
  margin-right: 8px;
}

.class-color-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

/* 스크롤바 스타일 */
.legend-content::-webkit-scrollbar {
  width: 4px;
}

.legend-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.legend-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.legend-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
