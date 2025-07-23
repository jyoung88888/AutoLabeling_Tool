/**
 * 모델 관련 API 함수들
 */
import axios from 'axios';
import { API_SERVER } from '../utils/config.js';

/**
 * 사용 가능한 모델 목록을 가져옵니다.
 * @returns {Promise<Object>} - 모델 목록 (새로운 형식: { models: { "yolo": ["model1.pt"], "custom": ["model2.pt"] } })
 */
export const getModels = async () => {
  try {
    const response = await axios.get(`${API_SERVER}/models/`);
    return response.data;
  } catch (error) {
    console.error('모델 목록 가져오기 실패:', error);
    throw error;
  }
};

/**
 * 사용 가능한 모델 타입 목록을 가져옵니다.
 * @returns {Promise<Object>} - 모델 타입 목록
 */
export const getModelTypes = async () => {
  try {
    const response = await axios.get(`${API_SERVER}/models/types`);
    return response.data;
  } catch (error) {
    console.error('모델 타입 목록 가져오기 실패:', error);
    throw error;
  }
};

/**
 * 로컬에서 모델 파일을 업로드합니다.
 * @param {File} file - 업로드할 모델 파일
 * @param {string} modelType - 모델 타입 (예: yolo)
 * @param {string} modelName - 모델 이름 (확장자 제외)
 * @returns {Promise<Object>} - 업로드 결과
 */
export const uploadModel = async (file, modelType, modelName) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_type', modelType);
    formData.append('model_name', modelName);

    const response = await axios.post(`${API_SERVER}/models/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('모델 업로드 실패:', error);
    throw error;
  }
};

/**
 * 업로드된 모델을 삭제합니다.
 * @param {string} modelType - 모델 타입
 * @param {string} modelName - 모델 파일명
 * @returns {Promise<Object>} - 삭제 결과
 */
export const deleteModel = async (modelType, modelName) => {
  try {
    const response = await axios.delete(`${API_SERVER}/models/${modelType}/${modelName}`);
    return response.data;
  } catch (error) {
    console.error('모델 삭제 실패:', error);
    throw error;
  }
};

/**
 * 선택한 모델을 로드합니다.
 * @param {string} modelPath - 모델 경로 (모델타입/모델명)
 * @returns {Promise<Object>} - 로드 결과
 */
export const loadModel = async (modelPath) => {
  try {
    const response = await axios.post(`${API_SERVER}/models/load/${modelPath}`, {}, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('모델 로드 실패:', error);
    throw error;
  }
};

/**
 * 현재 로드된 모델의 클래스 목록을 가져옵니다.
 * @param {string} project - 프로젝트 이름 (선택 사항)
 * @returns {Promise<Object>} - 클래스 목록
 */
export const getModelClasses = async (project = null) => {
  try {
    // 프로젝트 파라미터가 있으면 쿼리 파라미터로 추가
    const url = project
      ? `${API_SERVER}/model/classes?project=${encodeURIComponent(project)}`
      : `${API_SERVER}/model/classes`;

    const response = await axios.get(url);

    // 응답 데이터 처리
    const data = response.data;
    let classes = [];

    if (data.classes) {
      if (Array.isArray(data.classes)) {
        classes = data.classes;
      } else if (typeof data.classes === 'object') {
        // 객체인 경우 값들을 배열로 변환
        classes = Object.values(data.classes).filter(val => val && typeof val === 'string');
      }
    }

    // 클래스가 없는 경우 오류 발생
    if (!classes || classes.length === 0) {
      throw new Error('클래스 정보가 없습니다. 프로젝트 JSON 파일을 확인해주세요.');
    }

    return { classes };
  } catch (error) {
    console.error('모델 클래스 가져오기 실패:', error);
    // 오류 발생시키기
    throw new Error('클래스 정보를 불러올 수 없습니다: ' + error.message);
  }
};
