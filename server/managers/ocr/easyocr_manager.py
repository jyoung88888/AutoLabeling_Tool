"""
EasyOCR Text Recognition Model Manager
EasyOCR 텍스트 인식 모델 관리자
"""
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image
from fastapi import HTTPException

from ..base_model import BaseModel, ModelType, TaskType

logger = logging.getLogger(__name__)


class EasyOCRManager(BaseModel):
    """
    EasyOCR 텍스트 인식 모델 관리자
    다국어 OCR을 지원합니다.
    """

    def __init__(self):
        """EasyOCR 매니저 초기화"""
        super().__init__()
        self.model_type = ModelType.OCR
        self.task_type = TaskType.TEXT
        self.languages = []

    def load_model(self, model_path: str = None, **kwargs):
        """
        EasyOCR 모델 로딩

        Args:
            model_path (str): 모델 경로 (EasyOCR은 자동 다운로드하므로 선택사항)
            **kwargs:
                - languages (List[str]): 인식할 언어 목록 (기본값: ['en', 'ko'])
                - gpu (bool): GPU 사용 여부 (기본값: True)
        """
        try:
            # EasyOCR 라이브러리 임포트
            try:
                import easyocr
            except ImportError:
                raise ImportError(
                    "easyocr 라이브러리가 설치되지 않았습니다. "
                    "다음 명령어로 설치하세요: pip install easyocr"
                )

            # 언어 설정
            self.languages = kwargs.get('languages', ['en', 'ko'])
            use_gpu = kwargs.get('gpu', True)

            logger.info(f"🔄 EasyOCR 모델 로딩 시작")
            logger.info(f"  - 언어: {self.languages}")
            logger.info(f"  - GPU 사용: {use_gpu}")

            # EasyOCR Reader 생성
            self.model = easyocr.Reader(
                self.languages,
                gpu=use_gpu,
                verbose=False
            )

            self.is_loaded = True
            logger.info(f"✅ EasyOCR 모델 로딩 완료")

            return {
                "success": True,
                "message": f"EasyOCR model loaded successfully",
                "languages": self.languages,
                "gpu": use_gpu
            }

        except Exception as e:
            logger.error(f"❌ EasyOCR 모델 로딩 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"모델 로딩 실패: {str(e)}")

    def predict(self, image, **kwargs) -> Dict[str, Any]:
        """
        EasyOCR 텍스트 인식 추론

        Args:
            image: PIL Image, numpy array, 또는 이미지 경로
            **kwargs:
                - detail (int): 탐지 세부 수준 (0: 간단, 1: 상세, 기본값: 1)
                - paragraph (bool): 단락으로 그룹화 (기본값: False)
                - min_size (int): 최소 텍스트 크기 (기본값: 10)
                - text_threshold (float): 텍스트 신뢰도 임계값 (기본값: 0.7)
                - low_text (float): 낮은 텍스트 임계값 (기본값: 0.4)
                - link_threshold (float): 링크 임계값 (기본값: 0.4)
                - width_ths (float): 박스 너비 임계값 (기본값: 0.5)
                - height_ths (float): 박스 높이 임계값 (기본값: 0.5)

        Returns:
            Dict[str, Any]: OCR 인식 결과
        """
        if not self.validate_model():
            raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다")

        try:
            # 파라미터 추출
            detail = kwargs.get('detail', 1)
            paragraph = kwargs.get('paragraph', False)
            min_size = kwargs.get('min_size', 10)
            text_threshold = kwargs.get('text_threshold', 0.7)
            low_text = kwargs.get('low_text', 0.4)
            link_threshold = kwargs.get('link_threshold', 0.4)
            width_ths = kwargs.get('width_ths', 0.5)
            height_ths = kwargs.get('height_ths', 0.5)

            logger.info(f"🔍 EasyOCR 추론 시작")
            logger.info(f"  - Text threshold: {text_threshold}")

            # 이미지 전처리
            processed_image = self._preprocess_image(image)

            # EasyOCR 추론 실행
            results = self.model.readtext(
                processed_image,
                detail=detail,
                paragraph=paragraph,
                min_size=min_size,
                text_threshold=text_threshold,
                low_text=low_text,
                link_threshold=link_threshold,
                width_ths=width_ths,
                height_ths=height_ths
            )

            # 결과 후처리
            texts_data = self._postprocess_results(results, processed_image)

            logger.info(f"✅ EasyOCR 추론 완료 - 인식된 텍스트: {len(texts_data)}개")

            return {
                "texts": texts_data,
                "num_texts": len(texts_data),
                "task_type": "text",
                "model_type": "easyocr",
                "languages": self.languages
            }

        except Exception as e:
            logger.error(f"❌ EasyOCR 추론 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"추론 실패: {str(e)}")

    def _preprocess_image(self, image_input):
        """
        이미지 전처리

        Args:
            image_input: PIL Image, numpy array, 또는 이미지 경로

        Returns:
            numpy array: 전처리된 이미지
        """
        if isinstance(image_input, Image.Image):
            # PIL Image → numpy array
            return np.array(image_input)
        elif isinstance(image_input, (str, Path)):
            # 파일 경로는 그대로 반환 (EasyOCR이 처리)
            return str(image_input)
        elif isinstance(image_input, np.ndarray):
            # numpy array는 그대로 사용
            return image_input
        else:
            raise ValueError(
                f"지원하지 않는 이미지 타입: {type(image_input)}"
            )

    def _postprocess_results(self, results: List, image) -> List[Dict]:
        """
        EasyOCR 결과 후처리

        Args:
            results: EasyOCR 결과 리스트
            image: 원본 이미지 (크기 정보용)

        Returns:
            List[Dict]: 텍스트 정보 리스트
        """
        texts_data = []

        # 이미지 크기 가져오기
        if isinstance(image, np.ndarray):
            img_height, img_width = image.shape[:2]
        elif isinstance(image, Image.Image):
            img_width, img_height = image.size
        else:
            img_width, img_height = None, None

        for result in results:
            if len(result) == 3:
                bbox, text, confidence = result
            elif len(result) == 2:
                bbox, text = result
                confidence = 1.0
            else:
                logger.warning(f"예상치 못한 결과 형식: {result}")
                continue

            # Bounding box 처리 (4개의 꼭짓점)
            bbox_points = [[float(x), float(y)] for x, y in bbox]

            # Bounding box → xywh 변환 (좌상단 기준)
            x_coords = [pt[0] for pt in bbox_points]
            y_coords = [pt[1] for pt in bbox_points]
            x_min = min(x_coords)
            y_min = min(y_coords)
            x_max = max(x_coords)
            y_max = max(y_coords)
            width = x_max - x_min
            height = y_max - y_min

            text_info = {
                "text": text,
                "confidence": float(confidence),
                "bbox": [x_min, y_min, width, height],
                "bbox_points": bbox_points  # 원래 4점 좌표도 보존
            }

            # 정규화된 좌표 추가 (이미지 크기를 알 경우)
            if img_width and img_height:
                x_center = (x_min + x_max) / 2
                y_center = (y_min + y_max) / 2
                text_info["normalized_coords"] = [
                    float(x_center / img_width),
                    float(y_center / img_height),
                    float(width / img_width),
                    float(height / img_height)
                ]

            texts_data.append(text_info)

        return texts_data

    def get_model_info(self) -> Dict[str, Any]:
        """
        EasyOCR 모델 정보 반환

        Returns:
            Dict[str, Any]: 모델 메타데이터
        """
        return {
            "model_type": "easyocr",
            "task": "ocr",
            "framework": "easyocr",
            "is_loaded": self.is_loaded,
            "languages": self.languages,
            "supports_multilingual": True
        }

    def get_supported_languages(self) -> List[str]:
        """
        지원하는 언어 목록 반환

        Returns:
            List[str]: 언어 코드 목록
        """
        # EasyOCR이 지원하는 주요 언어들
        return [
            'en', 'ko', 'ja', 'zh', 'zh_tra',  # 영어, 한국어, 일본어, 중국어(간체/번체)
            'th', 'vi', 'ar', 'ru', 'es', 'fr',  # 태국어, 베트남어, 아랍어, 러시아어, 스페인어, 프랑스어
            'de', 'pt', 'it', 'tr', 'pl', 'nl',  # 독일어, 포르투갈어, 이탈리아어, 터키어, 폴란드어, 네덜란드어
            # 더 많은 언어 지원 가능
        ]
