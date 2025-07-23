// API 서버 설정
const getApiServer = () => {
  // 환경변수에서 API 서버 주소 가져오기
  if (import.meta.env.VITE_API_SERVER) {
    return import.meta.env.VITE_API_SERVER;
  }

  // 개발 환경에서는 현재 호스트의 8000 포트 사용
  if (import.meta.env.DEV) {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:8000`;
  }

  // 프로덕션 환경에서는 현재 호스트 사용 (Python 서버에서 Vue 앱 서빙 시)
  return `${window.location.protocol}//${window.location.host}`;
};

// 프로젝트 기본 경로 설정
const getProjectBasePath = () => {
  // 환경변수에서 프로젝트 기본 경로 가져오기
  if (import.meta.env.VITE_PROJECT_BASE_PATH) {
    return import.meta.env.VITE_PROJECT_BASE_PATH;
  }

  // 기본값: 현재 사용자의 홈 디렉토리 기반으로 동적 생성
  const currentUser = import.meta.env.VITE_CURRENT_USER || 'thub';
  return `/home/${currentUser}/supark/autolabeling/server/uploaded_images`;
};

// 사용되지 않는 함수들 제거 (WORKSPACE_PATH, NODE_MODULES_PATH)

export const API_SERVER = getApiServer();
export const PROJECT_BASE_PATH = getProjectBasePath();

// 설정 정보 (필요시 개발자 도구에서 확인 가능)
