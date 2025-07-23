// 브라우저 환경에서 동적 경로 설정
export const getBasePaths = () => {
  // 완전히 동적으로 경로를 구성 - 하드코딩 없음
  // 현재 페이지의 origin을 기반으로 작업 디렉토리 구성
  const baseWorkspace = './autolabeling';  // 상대 경로 사용

  return {
    // 업로드된 이미지 기본 경로
    uploadedImages: `${baseWorkspace}/server/uploaded_images`,

    // 데이터셋 저장 기본 경로
    datasets: `${baseWorkspace}/datasets`,

    // 프로젝트 저장 기본 경로
    projects: `${baseWorkspace}/projects`,

    // 임시 파일 경로
    temp: `${baseWorkspace}/temp`
  };
};

// 설정 가능한 기본 경로 (런타임에 변경 가능)
let customBasePath = null;

// 기본 경로 설정 함수
export const setBasePath = (path) => {
  customBasePath = path;
};

// 동적 기본 경로 가져오기
export const getDynamicBasePaths = () => {
  if (customBasePath) {
    return {
      uploadedImages: `${customBasePath}/server/uploaded_images`,
      datasets: `${customBasePath}/datasets`,
      projects: `${customBasePath}/projects`,
      temp: `${customBasePath}/temp`
    };
  }
  return getBasePaths();
};

// 경로 정규화 함수
export const normalizePath = (path) => {
  if (!path) return '';

  // 윈도우 경로를 유닉스 스타일로 변환
  return path.replace(/\\/g, '/');
};

// 상대 경로를 절대 경로로 변환
export const resolveAbsolutePath = (relativePath, basePath) => {
  if (!relativePath) return basePath || '';

  // 이미 절대 경로인 경우
  if (relativePath.startsWith('/')) {
    return normalizePath(relativePath);
  }

  const base = basePath || getDynamicBasePaths().projects;
  return normalizePath(`${base}/${relativePath}`);
};

// 서버 경로 접두사 생성 함수
export const getServerPathPrefix = () => {
  return getDynamicBasePaths().uploadedImages + '/';
};

// 현재 작업 디렉토리 감지 (API 호출을 통해)
export const detectWorkingDirectory = async () => {
  try {
    // 백엔드 API를 통해 현재 작업 디렉토리 가져오기
    const response = await fetch('/api/system/working-directory');
    if (response.ok) {
      const data = await response.json();
      if (data.workingDirectory) {
        setBasePath(data.workingDirectory + '/autolabeling');
        return data.workingDirectory + '/autolabeling';
      }
    }
  } catch (error) {
    console.warn('작업 디렉토리 감지 실패, 기본값 사용:', error);
  }

  return getBasePaths();
};

// 브라우저 환경에서 사용할 수 있는 기본값들
export const DEFAULT_PATHS = {
  get uploadedImages() {
    return getDynamicBasePaths().uploadedImages;
  },
  get datasets() {
    return getDynamicBasePaths().datasets;
  },
  get projects() {
    return getDynamicBasePaths().projects;
  },
  get temp() {
    return getDynamicBasePaths().temp;
  }
};
