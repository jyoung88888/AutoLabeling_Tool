"""
Grounding DINO Detection Model Manager
Grounding DINO 텍스트 프롬프트 기반 객체 탐지 모델 관리자
Hugging Face Transformers 라이브러리 사용
"""
import torch
import logging
import numpy as np
from typing import Dict, Any, Optional, List
from PIL import Image
from fastapi import HTTPException

from ..base_model import BaseModel, ModelType, TaskType

logger = logging.getLogger(__name__)


class GroundingDINOManager(BaseModel):
    """
    Grounding DINO 객체 탐지 모델 관리자
    텍스트 프롬프트를 사용한 zero-shot 객체 탐지
    Hugging Face Hub에서 모델 자동 다운로드
    """

    def __init__(self):
        """Grounding DINO 매니저 초기화"""
        super().__init__()
        self.model_type = ModelType.DETECTION
        self.task_type = TaskType.BBOX
        self.processor = None
        self.model_id = None

    def load_model(self, model_path: str = None, **kwargs):
        """
        Grounding DINO 모델 로딩 (Hugging Face Hub)

        Args:
            model_path (str, optional): Hugging Face model ID
                (기본값: "IDEA-Research/grounding-dino-tiny")
            **kwargs:
                - model_id (str): 모델 ID (model_path 대신 사용 가능)
        """
        try:
            # Transformers 라이브러리 임포트
            try:
                from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
            except ImportError:
                raise ImportError(
                    "transformers 라이브러리가 설치되지 않았습니다. "
                    "다음 명령어로 설치하세요: pip install transformers"
                )

            # 모델 ID 결정 (우선순위: kwargs['model_id'] > model_path > 기본값)
            self.model_id = kwargs.get('model_id') or model_path or "IDEA-Research/grounding-dino-tiny"

            logger.info(f"🔄 Grounding DINO 모델 로딩 시작")
            logger.info(f"  - Model ID: {self.model_id}")
            logger.info(f"  - Source: Hugging Face Hub")

            # 디바이스 설정
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"  - Device: {device}")

            # Processor와 모델 로드
            logger.info(f"📥 Processor 다운로드 중...")
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            logger.info(f"📥 모델 다운로드 중...")
            self.model = AutoModelForZeroShotObjectDetection.from_pretrained(self.model_id)

            # GPU로 이동
            self.model.to(device)

            if device == "cuda":
                logger.info(f"✅ Grounding DINO 모델을 GPU로 로드")
            else:
                logger.info(f"✅ Grounding DINO 모델을 CPU로 로드")

            self.is_loaded = True
            logger.info(f"✅ Grounding DINO 모델 로딩 완료")

            return {
                "success": True,
                "message": f"Grounding DINO model loaded successfully from Hugging Face",
                "model_id": self.model_id,
                "supports_text_prompt": True,
                "device": device
            }

        except Exception as e:
            logger.error(f"❌ Grounding DINO 모델 로딩 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"모델 로딩 실패: {str(e)}")

    def predict(self, image, **kwargs) -> Dict[str, Any]:
        """
        Grounding DINO 객체 탐지 추론 (Transformers API)

        Args:
            image: PIL Image 또는 numpy array
            **kwargs:
                - text_prompt (str): 탐지할 객체 텍스트 프롬프트 (예: "person. car. dog.")
                - box_threshold (float): 박스 신뢰도 임계값 (기본값: 0.3)
                - text_threshold (float): 텍스트 신뢰도 임계값 (기본값: 0.25)

        Returns:
            Dict[str, Any]: 탐지 결과
        """
        if not self.validate_model():
            raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다")

        try:
            # 필수 파라미터 확인
            text_prompt = kwargs.get('text_prompt')
            if not text_prompt:
                raise ValueError("text_prompt가 필요합니다 (예: 'person. car. dog.')")

            box_threshold = kwargs.get('box_threshold', 0.3)
            text_threshold = kwargs.get('text_threshold', 0.25)

            logger.info(f"🔍 Grounding DINO 추론 시작")
            logger.info(f"  - 프롬프트: {text_prompt}")
            logger.info(f"  - Box threshold: {box_threshold}")
            logger.info(f"  - Text threshold: {text_threshold}")

            # 이미지 전처리
            if not isinstance(image, Image.Image):
                if isinstance(image, np.ndarray):
                    image = Image.fromarray(image)
                else:
                    raise ValueError("이미지는 PIL Image 또는 numpy array여야 합니다")

            # RGB 변환
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Processor로 입력 전처리
            device = next(self.model.parameters()).device

            # Transformers 버전 확인
            import transformers
            logger.info(f"🔍 Transformers 버전: {transformers.__version__}")

            inputs = self.processor(
                images=image,
                text=text_prompt,
                return_tensors="pt"
            ).to(device)

            # 추론
            with torch.no_grad():
                outputs = self.model(**inputs)

            # 후처리 (Transformers API)
            # 버전에 따라 threshold 파라미터 지원 여부가 다를 수 있음

            # API 시그니처 확인
            import inspect
            sig = inspect.signature(self.processor.post_process_grounded_object_detection)
            logger.info(f"🔍 post_process_grounded_object_detection 파라미터: {list(sig.parameters.keys())}")

            try:
                # 최신 버전: box_threshold, text_threshold 지원
                logger.info(f"🔄 최신 버전 API 시도 중 (box_threshold={box_threshold}, text_threshold={text_threshold})")
                results = self.processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    box_threshold=box_threshold,
                    text_threshold=text_threshold,
                    target_sizes=[image.size[::-1]]
                )[0]

                logger.info("✅ 최신 버전 API 성공")

                # 결과 변환
                detections = self._postprocess_results(
                    boxes=results["boxes"],
                    scores=results["scores"],
                    labels=results["labels"],
                    image_size=image.size
                )

            except TypeError as e:
                # 구버전: threshold 파라미터 미지원 - 수동 필터링
                logger.warning(f"Threshold 파라미터 미지원 - 수동 필터링 사용: {e}")

                results = self.processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    target_sizes=[image.size[::-1]]
                )[0]

                # threshold 수동 적용
                filtered_boxes = []
                filtered_scores = []
                filtered_labels = []

                for box, score, label in zip(results["boxes"], results["scores"], results["labels"]):
                    if float(score) >= box_threshold:
                        filtered_boxes.append(box)
                        filtered_scores.append(score)
                        filtered_labels.append(label)

                # 결과 변환
                if len(filtered_boxes) > 0:
                    detections = self._postprocess_results(
                        boxes=torch.stack(filtered_boxes),
                        scores=torch.stack(filtered_scores),
                        labels=filtered_labels,
                        image_size=image.size
                    )
                else:
                    detections = []

            logger.info(f"✅ Grounding DINO 추론 완료 - 탐지된 객체: {len(detections)}개")

            return {
                "boxes": detections,
                "num_detections": len(detections),
                "task_type": "bbox",
                "model_type": "grounding_dino",
                "text_prompt": text_prompt
            }

        except Exception as e:
            logger.error(f"❌ Grounding DINO 추론 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"추론 실패: {str(e)}")

    def _postprocess_results(
        self,
        boxes: torch.Tensor,
        scores: torch.Tensor,
        labels: List[str],
        image_size: tuple
    ) -> List[Dict]:
        """
        Grounding DINO 결과 후처리 (Transformers API)

        Args:
            boxes: 탐지된 박스 (픽셀 좌표 xyxy format)
            scores: 신뢰도 점수
            labels: 탐지된 텍스트 레이블
            image_size: 원본 이미지 크기 (width, height)

        Returns:
            List[Dict]: 박스 정보 리스트
        """
        detections = []
        img_width, img_height = image_size

        # Tensor를 numpy로 변환
        if isinstance(boxes, torch.Tensor):
            boxes = boxes.cpu().numpy()
        if isinstance(scores, torch.Tensor):
            scores = scores.cpu().numpy()

        for box, confidence, label in zip(boxes, scores, labels):
            # 픽셀 좌표 xyxy format
            x_min, y_min, x_max, y_max = box

            # xywh 형식으로 변환
            width = x_max - x_min
            height = y_max - y_min

            # 정규화된 좌표 계산
            x_center_norm = ((x_min + x_max) / 2) / img_width
            y_center_norm = ((y_min + y_max) / 2) / img_height
            width_norm = width / img_width
            height_norm = height / img_height

            detection = {
                "class_id": -1,  # Grounding DINO는 class ID가 없음
                "class_name": label.strip(),
                "confidence": float(confidence),
                "bbox": [float(x_min), float(y_min), float(width), float(height)],
                "normalized_coords": [
                    float(x_center_norm),
                    float(y_center_norm),
                    float(width_norm),
                    float(height_norm)
                ]
            }

            detections.append(detection)

        return detections

    def get_model_info(self) -> Dict[str, Any]:
        """
        Grounding DINO 모델 정보 반환

        Returns:
            Dict[str, Any]: 모델 메타데이터
        """
        return {
            "model_type": "grounding_dino",
            "task": "detection",
            "framework": "transformers",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "is_loaded": self.is_loaded,
            "supports_text_prompt": True,
            "zero_shot": True,
            "model_id": self.model_id,
            "source": "Hugging Face Hub"
        }
