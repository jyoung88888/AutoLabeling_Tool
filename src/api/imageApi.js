/**
 * 이미지 관련 API 함수들
 */
import axios from 'axios';
import { API_SERVER } from '../utils/config.js';

/**
 * 이미지 파일을 서버에 업로드합니다.
 * @param {File[]} files - 업로드할 이미지 파일 배열
 * @param {string} projectName - 업로드할 프로젝트명 (기본값: "default")
 * @returns {Promise<Object>} - 업로드 결과
 */
export const uploadImages = async (files, projectName = "default") => {
  try {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    // 프로젝트명 추가
    formData.append('project', projectName);

    const response = await axios.post(`${API_SERVER}/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('이미지 업로드 실패:', error);
    throw error;
  }
};

/**
 * 업로드된 이미지 목록을 가져옵니다.
 * @returns {Promise<Object>} - 이미지 목록
 */
export const getImages = async () => {
  try {
    const response = await axios.get(`${API_SERVER}/images/`);
    return response.data;
  } catch (error) {
    console.error('이미지 목록 가져오기 실패:', error);
    throw error;
  }
};

/**
 * 이미지 파일과 라벨 파일을 삭제합니다.
 * @param {string} filename - 삭제할 이미지 파일명
 * @param {string} projectPath - 프로젝트 경로
 * @returns {Promise<Object>} - 삭제 결과
 */
export const deleteImageAndLabel = async (filename, projectPath) => {
  try {
    const response = await axios.delete(`${API_SERVER}/api/delete-image/${encodeURIComponent(filename)}`, {
      params: {
        project_path: projectPath
      }
    });
    return response.data;
  } catch (error) {
    console.error('파일 삭제 실패:', error);
    throw error;
  }
};

/**
 * 이미지 URL을 생성합니다.
 * @param {string} imagePath - 이미지 경로 (날짜/프로젝트/images/파일명 or 파일명만)
 * @returns {string} 이미지 URL
 */
export function getImageUrl(imagePath) {
  if (!imagePath) {
    console.error('이미지 경로가 비어 있습니다.');
    return `${API_SERVER}/error-image.jpg`;
  }

  try {
    // 상대 경로로 변환 (images/ 디렉토리가 빠진 경우 처리)
    let processedPath = imagePath;

    // 날짜/프로젝트/파일명 형식이고 images가 없는 경우 추가
    if (imagePath.includes('/') && !imagePath.includes('/images/')) {
      const parts = imagePath.split('/');
      if (parts.length >= 3) {
        // 마지막 부분은 파일명으로 가정
        const fileName = parts.pop();
        // images 디렉토리 추가
        processedPath = [...parts, 'images', fileName].join('/');
        console.log(`경로 수정됨: ${imagePath} -> ${processedPath}`);
      }
    }

    // 각 경로 세그먼트를 개별적으로 인코딩하되 / 구분자는 유지
    const pathParts = processedPath.split('/');
    const encodedParts = pathParts.map(part => encodeURIComponent(part));
    const encodedImagePath = encodedParts.join('/');

    console.log(`이미지 URL 생성: 원본=${processedPath}, 인코딩=${encodedImagePath}`);

    // 서버 이미지 URL 반환
    return `${API_SERVER}/image/${encodedImagePath}`;
  } catch (err) {
    console.error('이미지 URL 생성 오류:', err);
    return `${API_SERVER}/error-image.jpg`;
  }
}
