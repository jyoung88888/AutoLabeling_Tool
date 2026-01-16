"""
Model Factory for creating model instances
모델 인스턴스를 생성하는 팩토리 클래스
"""
from typing import Dict, Type, List, Optional
from .base_model import BaseModel, ModelType
import logging

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    모델 생성 팩토리

    새로운 모델 타입을 쉽게 등록하고 생성할 수 있는 팩토리 패턴 구현
    """

    # 모델 타입별 매니저 매핑 (lazy loading)
    _model_registry: Dict[str, Type[BaseModel]] = {}
    _initialized = False

    @classmethod
    def _initialize_registry(cls):
        """
        모델 레지스트리 초기화 (lazy initialization)
        """
        if cls._initialized:
            return

        try:
            # Detection 모델들
            from .detection.yolo_manager import YOLOManager
            cls._model_registry["yolo"] = YOLOManager
            logger.info("✅ YOLO 모델 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ YOLO 모델 등록 실패: {e}")

        try:
            from .detection.grounding_dino_manager import GroundingDINOManager
            cls._model_registry["grounding_dino"] = GroundingDINOManager
            logger.info("✅ Grounding DINO 모델 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ Grounding DINO 모델 등록 실패: {e}")

        try:
            # Keypoint 모델들
            from .keypoint.yolo_pose_manager import YOLOPoseManager
            cls._model_registry["yolo_pose"] = YOLOPoseManager
            logger.info("✅ YOLO Pose 모델 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ YOLO Pose 모델 등록 실패: {e}")

        try:
            # OCR 모델들
            from .ocr.easyocr_manager import EasyOCRManager
            cls._model_registry["easyocr"] = EasyOCRManager
            logger.info("✅ EasyOCR 모델 등록 완료")
        except ImportError as e:
            logger.warning(f"⚠️ EasyOCR 모델 등록 실패: {e}")

        cls._initialized = True
        logger.info(f"🎉 모델 팩토리 초기화 완료: {len(cls._model_registry)}개 모델 등록")

    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> BaseModel:
        """
        모델 인스턴스 생성

        Args:
            model_name (str): 모델 이름 (예: "yolo", "grounding_dino")
            **kwargs: 모델 초기화 파라미터

        Returns:
            BaseModel: 생성된 모델 인스턴스

        Raises:
            ValueError: 지원하지 않는 모델인 경우
        """
        cls._initialize_registry()

        manager_class = cls._model_registry.get(model_name)

        if manager_class is None:
            available = ", ".join(cls._model_registry.keys())
            raise ValueError(
                f"지원하지 않는 모델: {model_name}. "
                f"사용 가능한 모델: {available}"
            )

        logger.info(f"🏗️ {model_name} 모델 인스턴스 생성")
        return manager_class(**kwargs)

    @classmethod
    def register_model(cls, model_name: str, manager_class: Type[BaseModel]):
        """
        새 모델 타입 등록 (확장용)

        Args:
            model_name (str): 모델 식별자
            manager_class (Type[BaseModel]): 모델 매니저 클래스
        """
        cls._initialize_registry()
        cls._model_registry[model_name] = manager_class
        logger.info(f"➕ 새 모델 등록: {model_name}")

    @classmethod
    def get_available_models(cls) -> Dict[str, List[str]]:
        """
        사용 가능한 모델 목록 반환

        Returns:
            Dict[str, List[str]]: 카테고리별 모델 목록
        """
        cls._initialize_registry()

        categorized = {
            "detection": [],
            "keypoint": [],
            "ocr": [],
            "segmentation": []
        }

        for model_name in cls._model_registry.keys():
            if "yolo" in model_name and "pose" not in model_name:
                categorized["detection"].append(model_name)
            elif "dino" in model_name:
                categorized["detection"].append(model_name)
            elif "pose" in model_name or "keypoint" in model_name:
                categorized["keypoint"].append(model_name)
            elif "ocr" in model_name:
                categorized["ocr"].append(model_name)
            elif "sam" in model_name or "segment" in model_name:
                categorized["segmentation"].append(model_name)

        return categorized

    @classmethod
    def get_registered_models(cls) -> List[str]:
        """
        등록된 모든 모델 이름 목록

        Returns:
            List[str]: 모델 이름 목록
        """
        cls._initialize_registry()
        return list(cls._model_registry.keys())

    @classmethod
    def is_model_available(cls, model_name: str) -> bool:
        """
        특정 모델이 사용 가능한지 확인

        Args:
            model_name (str): 모델 이름

        Returns:
            bool: 사용 가능 여부
        """
        cls._initialize_registry()
        return model_name in cls._model_registry
