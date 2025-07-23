import axios from 'axios'
import { API_SERVER } from '../utils/config.js';

// API 호출 시 타임아웃 설정 - 대용량 프로젝트를 위해 증가
const apiClient = axios.create({
  baseURL: API_SERVER,
  timeout: 120000, // 120초로 증가 (큰 프로젝트를 위해)
  headers: {
    'Content-Type': 'application/json'
  }
});

// 응답 인터셉터 설정
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API 요청 오류:', error);
    throw error;
  }
);

// 좌표 유효성 검사 함수
function isValidCoord(coord) {
  return typeof coord === 'number' && !isNaN(coord) && coord >= 0 && coord <= 1;
}

/**
 * 프로젝트 결과를 내보냅니다.
 * @param {Object} exportInfo - 내보내기 정보
 * @param {string} exportInfo.projectName - 프로젝트 이름
 * @param {string} exportInfo.exportPath - 내보내기 경로
 * @param {Array} exportInfo.results - 내보낼 결과 데이터
 * @param {Array} exportInfo.classes - 클래스 목록
 * @param {boolean} exportInfo.includeClassFile - 클래스 파일 포함 여부
 * @returns {Promise<Object>} 내보내기 결과 정보
 */
export async function exportResults(exportInfo) {
  try {
    const response = await apiClient.post('/api/export-results', exportInfo);
    return response.data;
  } catch (error) {
    console.error('결과 내보내기 중 오류 발생:', error);
    const errorMessage = error.response ? `서버 오류: ${error.response.status} ${error.response.statusText}` : error.message;
    throw new Error(errorMessage);
  }
}

/**
 * YOLO 형식으로 라벨링 결과를 내보내는 함수 (새로운 구현)
 * @param {string} exportPath - 내보낼 경로
 * @param {Array} results - 라벨링 결과 배열
 * @param {Array} classes - 클래스 목록
 * @param {Object} modelClasses - 모델 클래스 정보 (예: {0: 'person', 1: 'helmet', ...})
 * @param {Array} lowConfidenceImages - 저신뢰도 이미지 정보 (옵션)
 * @param {Function} progressCallback - 진행률을 업데이트할 콜백 함수 (옵션)
 * @returns {Promise<string>} 저장된 경로
 */
export async function exportToYOLO(exportPath, results, classes, modelClasses = null, lowConfidenceImages = null) {
  // 진행률 추적 완전히 비활성화
  const tracker = null;

  try {
    // === 1단계: 초기화 ===
    if (tracker) {
      tracker.startStep(0, '프로젝트 데이터 초기화 중...');
    }

    // 경로에서 프로젝트명 추출
    const pathParts = exportPath.split('/');
    const projectName = pathParts[pathParts.length - 1] || `project_${Date.now()}`;

    // 입력 데이터 유효성 검사
    if (!results || !Array.isArray(results)) {
      throw new Error('유효하지 않은 결과 데이터');
    }
    if (!classes || !Array.isArray(classes)) {
      throw new Error('유효하지 않은 클래스 데이터');
    }

    if (tracker) {
      tracker.completeStep('초기화 완료');
    }

    // === 2단계: 데이터 검증 ===
    if (tracker) {
      tracker.startStep(1, '이미지 및 라벨 데이터 검증 중...');
    }

    const validResults = results.filter(result => result && result.filename);
    console.log(`유효한 결과: ${validResults.length}개`);

    // 클래스 매핑 생성
    const classMapping = {};
    classes.forEach((className, index) => {
      classMapping[className] = index;
    });

    if (tracker) {
      tracker.updateStepProgress(50, `${validResults.length}개 이미지 검증 중...`);
    }

    // 실제 데이터 검증 작업
    let validImages = 0;
    let validBoxes = 0;
    for (let i = 0; i < validResults.length; i++) {
      const result = validResults[i];
      if (result.boxes && Array.isArray(result.boxes)) {
        validImages++;
        validBoxes += result.boxes.length;
      }

      // 검증 진행률 업데이트
      const checkProgress = 50 + ((i + 1) / validResults.length) * 50;
      if (tracker) {
        tracker.updateStepProgress(checkProgress, `검증 중: ${i + 1}/${validResults.length} 이미지`);
      }
    }

    console.log(`검증 완료: ${validImages}개 이미지, ${validBoxes}개 바운딩 박스`);
    if (tracker) {
      tracker.completeStep(`데이터 검증 완료 (${validImages}개 이미지, ${validBoxes}개 박스)`);
    }

    // === 3단계: 파일 변환 ===
    if (tracker) {
      tracker.startStep(2, 'YOLO 형식 라벨 데이터 변환 중...');
    }

    // 이미지 결과 변환 (실제 작업 기반)
    const processedImages = [];
    const totalImages = validResults.length;

    if (totalImages === 0) {
      if (tracker) {
        tracker.completeStep('변환할 이미지가 없음');
      }
    } else {
      let totalProcessedBoxes = 0;

      for (let i = 0; i < totalImages; i++) {
        try {
          const result = validResults[i];

          // 실제 변환 작업 진행률 업데이트
          const stepProgress = ((i + 1) / totalImages) * 100;
          if (tracker) {
            tracker.updateStepProgress(stepProgress, `YOLO 라벨 변환: ${i + 1}/${totalImages} - ${result.filename}`);
          }

          // 안전한 결과 검증
          if (!result || !result.filename) {
            continue; // 건너뛰기
          }

          // YOLO 형식의 라벨 데이터 생성
          let labelData = '';
          const boxes = result.boxes || [];
          let processedBoxCount = 0;

          for (const box of boxes) {
            if (!box || !box.class_name) continue;

            const classIdx = classMapping[box.class_name];
            if (classIdx === undefined) continue;

            try {
              // 정규화된 좌표 사용
              if (box.normalized_coords && Array.isArray(box.normalized_coords) && box.normalized_coords.length === 4) {
                const [x_center, y_center, width, height] = box.normalized_coords;
                if (isValidCoord(x_center) && isValidCoord(y_center) &&
                    isValidCoord(width) && isValidCoord(height)) {
                  labelData += `${classIdx} ${x_center.toFixed(6)} ${y_center.toFixed(6)} ${width.toFixed(6)} ${height.toFixed(6)}\n`;
                  processedBoxCount++;
                }
              }
              // bbox 좌표로부터 정규화된 좌표 계산
              else if (box.bbox && Array.isArray(box.bbox) && box.bbox.length === 4 &&
                       result.width && result.height && result.width > 0 && result.height > 0) {
                const [x, y, w, h] = box.bbox;
                const x_center = (x + w / 2) / result.width;
                const y_center = (y + h / 2) / result.height;
                const norm_width = w / result.width;
                const norm_height = h / result.height;

                if (isValidCoord(x_center) && isValidCoord(y_center) &&
                    isValidCoord(norm_width) && isValidCoord(norm_height)) {
                  labelData += `${classIdx} ${x_center.toFixed(6)} ${y_center.toFixed(6)} ${norm_width.toFixed(6)} ${norm_height.toFixed(6)}\n`;
                  processedBoxCount++;
                }
              }
            } catch (boxError) {
              console.warn(`박스 처리 중 오류 (${result.filename}):`, boxError);
              continue; // 해당 박스만 건너뛰기
            }
          }

          totalProcessedBoxes += processedBoxCount;

          processedImages.push({
            filename: result.filename,
            labelData: labelData,
            imageData: result.imageData || null,
            width: result.width || 0,
            height: result.height || 0,
            boxCount: processedBoxCount
          });

        } catch (imageError) {
          console.warn(`이미지 처리 중 오류 (인덱스 ${i}):`, imageError);
          // 개별 이미지 오류는 전체 프로세스를 중단하지 않음
          continue;
        }
      }

      if (tracker) {
        tracker.completeStep(`YOLO 변환 완료 (${processedImages.length}개 이미지, ${totalProcessedBoxes}개 박스)`);
      }
    }

    // === 4단계: 서버 전송 ===
    if (tracker) {
      tracker.startStep(3, '서버로 데이터 전송 중...');
    }

    // modelClasses를 class_info 형태로 변환
    let classInfo = null;
    if (modelClasses && typeof modelClasses === 'object') {
      try {
        // {0: 'person', 1: 'helmet', ...} 형태를 [{"id": 0, "name": "person"}, ...] 형태로 변환
        classInfo = Object.entries(modelClasses)
          .map(([id, name]) => ({
            id: parseInt(id),
            name: name
          }))
          .sort((a, b) => a.id - b.id); // ID 순서대로 정렬

        console.log('YOLO 내보내기 - 변환된 class_info:', classInfo);
      } catch (error) {
        console.warn('YOLO 내보내기 - modelClasses 변환 중 오류:', error);
        classInfo = null;
      }
    }

         // 요청 데이터 구성 (백엔드 API와 호환되도록)
     // classes 키 제거 - 서버에서 현재 모델로부터 동적으로 가져옴
     const requestData = {
       projectName,
       basePath: pathParts.slice(0, -1).join('/'),  // 백엔드가 기대하는 basePath 필드명 사용
       createDirs: true,  // 디렉토리 생성 허용
       images: processedImages,
       // classes 키 제거 - 프로젝트 저장 시 JSON에 포함되지 않도록 함
       customLowConfidenceImages: lowConfidenceImages || [],  // 백엔드가 기대하는 필드명
       confidenceData: {},  // 빈 객체로 초기화
       metadata: {
         totalImages: processedImages.length,
         exportTime: new Date().toISOString(),
         format: 'YOLO'
       },
       class_info: classInfo
     };

    if (tracker) {
      tracker.updateStepProgress(15, 'API 요청 준비 중...');
      console.log(`YOLO 내보내기 - 요청 데이터 크기: ${JSON.stringify(requestData).length} 바이트`);
    }

    // API 호출 with 타임아웃 및 재시도 메커니즘
    let response;
    let retryCount = 0;
    const maxRetries = 3; // 재시도 횟수 증가

    while (retryCount <= maxRetries) {
      try {
        const progressBase = 25 + (retryCount * 15);
        if (tracker) {
          tracker.updateStepProgress(progressBase, `서버 요청 중... (시도 ${retryCount + 1}/${maxRetries + 1})`);
        }

        console.log(`YOLO API 요청 시작: /api/project/save-local (시도 ${retryCount + 1})`);

        response = await apiClient.post('/api/project/save-local', requestData, {
          timeout: 90000, // 90초
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const uploadPercent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
              const currentProgress = progressBase + (uploadPercent * 0.5); // 50% 범위 내에서 업로드 진행률 반영
              if (tracker) {
                tracker.updateStepProgress(currentProgress, `YOLO 데이터 전송 중... ${uploadPercent}%`);
              }
            }
          }
        });

        console.log('YOLO API 요청 성공');
        break; // 성공시 루프 탈출

      } catch (apiError) {
        retryCount++;
        console.error(`YOLO API 요청 실패 (시도 ${retryCount}):`, apiError.message);

        if (retryCount > maxRetries) {
          // 최대 재시도 횟수 초과
          console.error('YOLO 내보내기 최대 재시도 횟수 초과');
          if (tracker) {
            tracker.onError(apiError);
          }
          throw createApiError(apiError);
        }

        // 재시도 대기
        const waitTime = Math.min(1000 * retryCount, 3000);
        if (tracker) {
          tracker.updateStepProgress(20 + (retryCount * 10),
            `재시도 대기 중... (${retryCount}/${maxRetries}, ${waitTime/1000}초 후)`);
        }
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    // 서버 응답 검증
    if (!response || !response.data) {
      throw new Error('서버로부터 유효하지 않은 응답을 받았습니다.');
    }

    if (tracker) {
      tracker.updateStepProgress(95, '서버 응답 처리 완료');
      tracker.completeStep('서버 전송 완료');
    }

    // === 5단계: 저장 완료 ===
    if (tracker) {
      tracker.startStep(4, '최종 저장 확인 중...');
    }

    // 저장 경로 확인
    const savedPath = response.data.path || exportPath;
    console.log(`YOLO 내보내기 성공: ${savedPath}`);

    if (tracker) {
      tracker.complete('YOLO 내보내기 완료!');
    }

    return savedPath;

  } catch (error) {
    console.error('YOLO 내보내기 중 오류:', error);
    if (tracker) {
      tracker.onError(error);
    }
    throw error;
  }
}

/**
 * 프로젝트를 로컬 폴더에 저장합니다 (새로운 구현)
 * @param {Object} projectData - 프로젝트 데이터
 * @param {Function} progressCallback - 진행률을 업데이트할 콜백 함수 (옵션)
 * @returns {Promise<Object>} 저장 결과
 */
export async function saveProjectLocal(projectData) {
  try {
    // 입력 데이터 검증 및 기본값 설정
    if (!projectData || !projectData.projectName) {
      throw new Error('프로젝트 이름이 필요합니다.');
    }

    if (!projectData.images || !Array.isArray(projectData.images)) {
      throw new Error('유효하지 않은 이미지 데이터입니다.');
    }

    // 전달받은 저신뢰도 이미지 데이터 사용 (우선순위)
    let lowConfidenceImages = [];

    if (projectData.lowConfidenceImages && Array.isArray(projectData.lowConfidenceImages)) {
      console.log('전달받은 저신뢰도 이미지 데이터 사용:', projectData.lowConfidenceImages.length, '개');
      // 저신뢰도 이미지 데이터를 올바른 형식으로 변환
      lowConfidenceImages = projectData.lowConfidenceImages.map(img => ({
        filename: img.filename,
        confidence: `${Math.round((img.confidence || 0) * 100)}%`
      }));
    } else {
      console.log('저신뢰도 이미지 데이터가 없어서 자동 계산');
      // 전달받은 데이터가 없는 경우에만 자동 계산
      projectData.images.forEach((image) => {
        if (image.boxes && Array.isArray(image.boxes)) {
          const confidences = image.boxes
            .filter(box => typeof box.confidence === 'number')
            .map(box => box.confidence);

          if (confidences.length > 0) {
            const avgConfidence = confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length;

            // 저신뢰도 이미지 체크 (평균 신뢰도 0.7 미만)
            if (avgConfidence < 0.7) {
              lowConfidenceImages.push({
                filename: image.filename,
                confidence: `${Math.round(avgConfidence * 100)}%`
              });
            }
          }
        }
      });
    }

    // 클래스 정보를 class_info 형태로 변환하여 서버로 전달
    console.log('modelClasses를 class_info 형태로 변환 중...');
    console.log('전달된 modelClasses:', projectData.modelClasses);

    let classInfo = null;

    // modelClasses가 있으면 class_info 형태로 변환
    if (projectData.modelClasses && typeof projectData.modelClasses === 'object') {
      try {
        // {0: 'person', 1: 'helmet', ...} 형태를 [{"id": 0, "name": "person"}, ...] 형태로 변환
        classInfo = Object.entries(projectData.modelClasses)
          .map(([id, name]) => ({
            id: parseInt(id),
            name: name
          }))
          .sort((a, b) => a.id - b.id); // ID 순서대로 정렬

        console.log('변환된 class_info:', classInfo);
        console.log(`✅ ${classInfo.length}개 클래스를 class_info 형태로 변환 완료`);
      } catch (error) {
        console.warn('modelClasses 변환 중 오류:', error);
        classInfo = null;
      }
    } else {
      console.log('modelClasses가 없거나 유효하지 않음 - class_info 없이 저장');
    }

    // 백엔드 API와 호환되는 데이터 구성
    const dataWithConfidence = {
      ...projectData,
      customLowConfidenceImages: lowConfidenceImages,
      createDirs: true,
      // class_info 키 추가 - 사이드바의 모델 클래스 선택 정보와 동일한 형태로 저장
      class_info: classInfo
    };

    // 클래스 파일 저장 처리 제거
    // classes 정보를 JSON에 저장하지 않으므로 별도 클래스 파일도 생성하지 않음
    console.log('클래스 정보는 프로젝트 JSON 파일에 저장하지 않으며, 별도 클래스 파일도 생성하지 않습니다.');
    console.log('클래스 정보는 프로젝트 로드 시 현재 모델에서 동적으로 가져옵니다.');

    // 서버 전송
    const response = await apiClient.post('/api/project/save-local', dataWithConfidence, {
      timeout: 90000, // 90초
    });

    // 응답 검증
    if (!response || !response.data) {
      throw new Error('서버로부터 유효하지 않은 응답을 받았습니다.');
    }

    // 저장 결과 확인
    const savedPath = response.data.path;
    console.log(`프로젝트 저장 성공: ${savedPath}`);

    // 성공 응답 반환
    return {
      success: true,
      path: response.data.path,
      projectName: projectData.projectName,
      imageCount: projectData.images.length,
      classCount: classInfo ? classInfo.length : 0,
      lowConfidenceCount: lowConfidenceImages.length,
      progress: 100
    };

  } catch (error) {
    // 상세한 에러 메시지 생성
    let errorMessage = '프로젝트 저장 중 오류가 발생했습니다.';
    if (error.response) {
      errorMessage = `서버 오류 (${error.response.status}): ${error.response.data?.message || error.response.statusText}`;
    } else if (error.message) {
      errorMessage = error.message;
    }

    throw new Error(errorMessage);
  }
}

/**
 * API 에러 생성 헬퍼
 */
function createApiError(apiError) {
  console.log('API 에러 상세 정보:', {
    code: apiError.code,
    message: apiError.message,
    response: apiError.response?.status,
    timeout: apiError.timeout
  });

  if (apiError.code === 'ECONNABORTED' || apiError.code === 'ETIMEDOUT') {
    return new Error('서버 응답 시간 초과. 프로젝트가 너무 크거나 서버가 과부하 상태일 수 있습니다. 잠시 후 다시 시도해주세요.');
  } else if (apiError.code === 'ECONNREFUSED') {
    return new Error('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.');
  } else if (apiError.code === 'ENOTFOUND') {
    return new Error('서버 주소를 찾을 수 없습니다. 네트워크 연결을 확인해주세요.');
  } else if (apiError.response) {
    const status = apiError.response.status;
    const message = apiError.response.data?.message || apiError.response.statusText;

    if (status === 413) {
      return new Error('프로젝트 데이터가 너무 큽니다. 이미지 수를 줄이거나 데이터 크기를 확인해주세요.');
    } else if (status === 422) {
      return new Error('프로젝트 데이터 형식이 올바르지 않습니다. 데이터를 확인해주세요.');
    } else if (status >= 500) {
      return new Error(`서버 내부 오류 (${status}): ${message}. 서버 로그를 확인해주세요.`);
    } else {
      return new Error(`서버 오류 (${status}): ${message}`);
    }
  } else if (apiError.request) {
    return new Error('서버로부터 응답을 받을 수 없습니다. 네트워크 연결을 확인해주세요.');
  } else {
    return new Error(`요청 처리 오류: ${apiError.message}`);
  }
}

/**
 * 프로젝트를 서버에 저장합니다 (기존 유지)
 * @param {Object} projectData - 프로젝트 데이터
 * @param {Function} progressCallback - 진행률 콜백 함수
 * @returns {Promise<Object>} 저장 결과
 */
export async function saveProjectServer(projectData) {
  // 서버 저장은 로컬 저장과 동일한 로직 사용 (프로그래스 없이)
  return await saveProjectLocal(projectData);
}
