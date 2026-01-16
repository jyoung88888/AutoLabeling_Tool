"""
Base model abstract class for all AI models
모든 AI 모델의 추상 베이스 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """모델 타입 열거형"""
    DETECTION = "detection"      # Object Detection (YOLO, Grounding DINO)
    KEYPOINT = "keypoint"        # Keypoint/Pose Estimation
    OCR = "ocr"                  # Text Recognition
    SEGMENTATION = "segmentation" # Instance/Semantic Segmentation


class TaskType(Enum):
    """작업 타입 열거형"""
    BBOX = "bbox"                # Bounding Box
    KEYPOINT = "keypoint"        # Keypoint
    TEXT = "text"                # Text
    MASK = "mask"                # Mask
    POLYGON = "polygon"          # Polygon


class BaseModel(ABC):
    """
    모든 모델의 추상 베이스 클래스

    모든 모델 매니저는 이 클래스를 상속받아 구현해야 합니다.
    """

    def __init__(self):
        """베이스 모델 초기화"""
        self.model = None
        self.model_type: Optional[ModelType] = None
        self.task_type: Optional[TaskType] = None
        self.is_loaded = False
        self.model_name = self.__class__.__name__
        logger.info(f"🔧 {self.model_name} 초기화")

    @abstractmethod
    def load_model(self, model_path: str, **kwargs):
        """
        모델 로딩

        Args:
            model_path (str): 모델 파일 경로
            **kwargs: 추가 설정 파라미터
        """
        pass

    @abstractmethod
    def predict(self, image, **kwargs) -> Dict[str, Any]:
        """
        추론 실행

        Args:
            image: 입력 이미지 (PIL Image, numpy array, 등)
            **kwargs: 추가 추론 파라미터

        Returns:
            Dict[str, Any]: 추론 결과
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 반환

        Returns:
            Dict[str, Any]: 모델 메타데이터
        """
        pass

    def validate_model(self) -> bool:
        """
        모델 검증

        Returns:
            bool: 모델이 정상적으로 로드되었는지 여부
        """
        is_valid = self.is_loaded and self.model is not None
        if not is_valid:
            logger.warning(f"⚠️ {self.model_name} 모델이 로드되지 않았습니다")
        return is_valid

    def unload_model(self):
        """모델 언로드 및 메모리 해제"""
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info(f"🗑️ {self.model_name} 언로드 완료")

    def __str__(self):
        """문자열 표현"""
        return f"{self.model_name}(type={self.model_type}, task={self.task_type}, loaded={self.is_loaded})"

    def __repr__(self):
        """객체 표현"""
        return self.__str__()
