import { createApp } from 'vue';
import App from './App.vue';

// Vuetify
import { createVuetify } from 'vuetify';
import 'vuetify/styles';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { VFileUpload } from 'vuetify/labs/VFileUpload';

// Vue Konva
import VueKonva from 'vue-konva';

// Material Design Icons
import '@mdi/font/css/materialdesignicons.css';

// 사용자 정의 CSS 변수 추가
import './assets/custom-variables.css';

// Vue 애플리케이션 초기화

const vuetify = createVuetify({
  components: {
    ...components,
    VFileUpload,
  },
  directives,
  icons: {
    defaultSet: 'mdi',
    iconfont: 'mdi',
  },
  theme: {
    defaultTheme: 'dark',
    themes: {
      light: {
        colors: {
          primary: '#1867C0',
          secondary: '#5CBBF6',
          accent: '#8c9eff',
          error: '#b71c1c',
          success: '#4CAF50',
          info: '#2196F3',
          warning: '#FB8C00',
        },
      },
      dark: {
        dark: true,
        colors: {
          // 배경색을 검은색 계열로 설정
          background: '#000000',
          surface: '#121212',
          'surface-bright': '#1a1a1a',
          'surface-light': '#262626',
          'surface-variant': '#1a1a1a',
          'on-surface-variant': '#e0e0e0',

          // 메인 컬러들
          primary: '#4CAF50',
          secondary: '#5CBBF6',
          accent: '#8c9eff',
          error: '#FF5252',
          success: '#4CAF50',
          info: '#2196F3',
          warning: '#FF9800',

          // 텍스트 색상 (가독성 향상)
          'on-background': '#ffffff',
          'on-surface': '#ffffff',
          'on-primary': '#000000',
          'on-secondary': '#000000',
          'on-error': '#000000',
          'on-success': '#000000',
          'on-warning': '#000000',
          'on-info': '#000000',
        },
      },
    },
  },
});

const app = createApp(App);
app.use(vuetify);
app.use(VueKonva);
app.mount('#app');
