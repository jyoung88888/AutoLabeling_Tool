<template>
  <div id="app" class="d-flex">
    <MainView />
  </div>
</template>

<script>
import MainView from './views/MainView.vue';

export default {
  components: { MainView }
};
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  background-color: #000000 !important;
}

/* 하단에 불필요한 요소 숨김 */
.v-application {
  height: 100% !important;
  background-color: #000000 !important;
}

.v-application__wrap {
  min-height: 100% !important;
  padding-bottom: 0 !important;
  background-color: #000000 !important;
}

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #000000 !important;
}
</style>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: 300px;
  padding: 20px;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
  overflow-y: auto;
}

.main-content {
  margin-left: 300px;
  padding: 20px;
  box-sizing: border-box;
  width: calc(100% - 300px);
}

h5, h6 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #333;
  border-bottom: 2px solid #dee2e6;
  padding-bottom: 5px;
}

button {
  margin-top: 10px;
  margin-bottom: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #0056b3;
}

.form-check-label, .form-select, .form-control {
  margin-bottom: 10px;
}

.list-group-item {
  margin-bottom: 5px;
}

.list-group-item:hover {
  background-color: #e9ecef;
  cursor: pointer;
}

.list-group-item small {
  font-size: 0.8rem;
}
</style>
