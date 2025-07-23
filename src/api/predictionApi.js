/**
 * 예측(라벨링) 관련 API 함수들
 */
import axios from 'axios';
import { API_SERVER } from '../utils/config.js';

/**
 * 업로드된 이미지에 대한 예측(라벨링)을 수행합니다.
 * @param {string} filename - 이미지 파일명
 * @param {string[]} selectedClasses - 선택된 클래스 목록 (빈 배열이면 모든 클래스 사용)
 * @returns {Promise<Object>} - 예측 결과
 */
export const predictImage = async (filename, selectedClasses = []) => {
  try {
    const response = await axios.post(`${API_SERVER}/model/predict/${filename}`, {
      selected_classes: selectedClasses
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('이미지 예측 실패:', error);
    throw error;
  }
};
