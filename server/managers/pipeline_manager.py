"""
Pipeline Manager for Multi-Model Integration
멀티모델 통합 파이프라인 관리자
"""
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

from .model_factory import ModelFactory
from .base_model import BaseModel, TaskType

logger = logging.getLogger(__name__)


class PipelineManager:
    """
    멀티모델 파이프라인 관리자

    여러 AI 모델을 통합하여 실행하고 결과를 관리합니다.
    """

    def __init__(self):
        """파이프라인 매니저 초기화"""
        self.models: Dict[str, BaseModel] = {}
        self.pipeline_config = {
            "detection": None,
            "keypoint": None,
            "ocr": None,
            "segmentation": None
        }
        logger.info("🔧 PipelineManager 초기화")

    def add_model(
        self,
        task_name: str,
        model_name: str,
        model_path: Optional[str] = None,
        **kwargs
    ):
        """
        파이프라인에 모델 추가

        Args:
            task_name (str): 작업 이름 ("detection", "keypoint", "ocr" 등)
            model_name (str): 모델 타입 ("yolo", "grounding_dino", "yolo_pose", "easyocr")
            model_path (str): 모델 파일 경로 (선택사항)
            **kwargs: 모델별 추가 설정

        Returns:
            dict: 모델 로드 결과 (supports_text_prompt 등 포함)
        """
        try:
            logger.info(f"➕ 파이프라인에 모델 추가: {task_name} -> {model_name}")

            # 모델 인스턴스 생성
            model = ModelFactory.create_model(model_name)

            # 모델 로드
            # EasyOCR, Grounding DINO는 Hugging Face에서 자동 다운로드 가능
            auto_download_models = ["easyocr", "grounding_dino"]

            load_result = None
            if model_path or model_name not in auto_download_models:
                # 로컬 모델 파일이 필요한 경우
                if model_path:
                    load_result = model.load_model(model_path, **kwargs)
                else:
                    raise ValueError(f"{model_name} 모델은 model_path가 필요합니다")
            else:
                # Hugging Face 등에서 자동 다운로드하는 모델
                load_result = model.load_model(**kwargs)

            # 파이프라인에 등록
            self.models[task_name] = model
            self.pipeline_config[task_name] = model_name

            logger.info(f"✅ 모델 추가 성공: {task_name} -> {model_name}")

            return load_result or {"success": True}

        except Exception as e:
            logger.error(f"❌ 모델 추가 실패 ({task_name}/{model_name}): {str(e)}")
            raise

    def remove_model(self, task_name: str):
        """
        파이프라인에서 모델 제거

        Args:
            task_name (str): 제거할 작업 이름
        """
        if task_name in self.models:
            model = self.models[task_name]
            model.unload_model()
            del self.models[task_name]
            self.pipeline_config[task_name] = None
            logger.info(f"🗑️ 모델 제거: {task_name}")
        else:
            logger.warning(f"⚠️ 모델이 존재하지 않습니다: {task_name}")

    def run_pipeline(
        self,
        image,
        tasks: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """
        멀티태스크 파이프라인 실행

        Args:
            image: 입력 이미지
            tasks (List[str]): 실행할 작업 목록 (예: ["detection", "keypoint", "ocr"])
            **kwargs: 각 작업별 설정
                - detection: detection 관련 파라미터
                - keypoint: keypoint 관련 파라미터
                - ocr: ocr 관련 파라미터

        Returns:
            Dict[str, Any]: 각 작업별 결과
        """
        logger.info(f"🚀 파이프라인 실행 시작 - 작업: {tasks}")
        results = {}

        for task in tasks:
            if task not in self.models:
                logger.warning(f"⚠️ {task} 모델이 로드되지 않음 - 스킵")
                results[task] = {
                    "error": f"{task} 모델이 로드되지 않았습니다",
                    "loaded": False
                }
                continue

            try:
                model = self.models[task]
                task_kwargs = kwargs.get(task, {})

                logger.info(f"🔄 {task} 실행 중...")
                task_result = model.predict(image, **task_kwargs)
                results[task] = task_result
                logger.info(f"✅ {task} 완료")

            except Exception as e:
                logger.error(f"❌ {task} 실패: {str(e)}")
                results[task] = {
                    "error": str(e),
                    "success": False
                }

        logger.info(f"✅ 파이프라인 실행 완료")
        return results

    def run_single_task(
        self,
        task_name: str,
        image,
        **kwargs
    ) -> Dict[str, Any]:
        """
        단일 작업 실행

        Args:
            task_name (str): 실행할 작업 이름
            image: 입력 이미지
            **kwargs: 작업별 설정

        Returns:
            Dict[str, Any]: 작업 결과
        """
        if task_name not in self.models:
            raise ValueError(f"{task_name} 모델이 로드되지 않았습니다")

        logger.info(f"🔄 단일 작업 실행: {task_name}")
        model = self.models[task_name]
        result = model.predict(image, **kwargs)
        logger.info(f"✅ 작업 완료: {task_name}")

        return result

    def run_batch_task(
        self,
        task_name: str,
        images: List,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        배치 작업 실행 (여러 이미지 동시 처리)

        Args:
            task_name (str): 실행할 작업 이름
            images (List): 입력 이미지 리스트
            **kwargs: 작업별 설정 (batch_size 포함)

        Returns:
            List[Dict[str, Any]]: 각 이미지별 작업 결과 리스트
        """
        if task_name not in self.models:
            raise ValueError(f"{task_name} 모델이 로드되지 않았습니다")

        logger.info(f"🔄 배치 작업 실행: {task_name} (이미지 {len(images)}개)")
        model = self.models[task_name]

        # 모델이 배치 추론을 지원하는지 확인
        if hasattr(model, 'predict_batch'):
            # 배치 추론 메서드 사용
            results = model.predict_batch(images, **kwargs)
        else:
            # 배치 추론을 지원하지 않으면 순차 처리
            logger.warning(f"⚠️ {task_name} 모델이 배치 추론을 지원하지 않습니다. 순차 처리로 대체합니다.")
            results = []
            for img in images:
                result = model.predict(img, **kwargs)
                results.append(result)

        logger.info(f"✅ 배치 작업 완료: {task_name} (처리된 이미지: {len(results)}개)")

        return results

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        파이프라인 정보 반환

        Returns:
            Dict[str, Any]: 파이프라인 상태 정보
        """
        return {
            "loaded_models": list(self.models.keys()),
            "config": self.pipeline_config,
            "model_info": {
                name: model.get_model_info()
                for name, model in self.models.items()
            },
            "num_loaded_models": len(self.models)
        }

    def is_task_loaded(self, task_name: str) -> bool:
        """
        특정 작업의 모델이 로드되었는지 확인

        Args:
            task_name (str): 확인할 작업 이름

        Returns:
            bool: 로드 여부
        """
        return task_name in self.models and self.models[task_name].is_loaded

    def clear_all_models(self):
        """
        모든 모델 언로드 및 정리
        """
        logger.info("🗑️ 모든 모델 정리 중...")
        for task_name in list(self.models.keys()):
            self.remove_model(task_name)
        logger.info("✅ 모든 모델 정리 완료")

    def __str__(self):
        """문자열 표현"""
        loaded = [f"{k}({v})" for k, v in self.pipeline_config.items() if v]
        return f"PipelineManager(loaded={loaded})"

    def __repr__(self):
        """객체 표현"""
        return self.__str__()


class PipelinePresets:
    """
    사전 정의된 파이프라인 프리셋
    """

    @staticmethod
    def safety_inspection_pipeline() -> List[str]:
        """
        안전 점검용 파이프라인
        (헬멧, 안전복, 사람 탐지 + 포즈)
        """
        return ["detection", "keypoint"]

    @staticmethod
    def document_processing_pipeline() -> List[str]:
        """
        문서 처리용 파이프라인
        (객체 탐지 + OCR)
        """
        return ["detection", "ocr"]

    @staticmethod
    def full_analysis_pipeline() -> List[str]:
        """
        전체 분석 파이프라인
        (모든 작업)
        """
        return ["detection", "keypoint", "ocr"]

    @staticmethod
    def get_preset(preset_name: str) -> List[str]:
        """
        프리셋 이름으로 파이프라인 가져오기

        Args:
            preset_name (str): 프리셋 이름

        Returns:
            List[str]: 작업 목록
        """
        presets = {
            "safety": PipelinePresets.safety_inspection_pipeline(),
            "document": PipelinePresets.document_processing_pipeline(),
            "full": PipelinePresets.full_analysis_pipeline()
        }
        return presets.get(preset_name, ["detection"])
