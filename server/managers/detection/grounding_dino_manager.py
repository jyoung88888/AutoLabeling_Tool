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
                - enable_compile (bool): torch.compile() 사용 여부 (기본값: False)
                  → Windows에서는 Triton 미지원으로 기본 비활성화
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

            # torch.compile()로 모델 최적화 (PyTorch 2.0+)
            # Windows 환경에서는 Triton 미지원으로 기본 비활성화
            enable_compile = kwargs.get('enable_compile', False)  # 기본값: False (안정성 우선)

            if device == "cuda" and enable_compile:
                try:
                    logger.info(f"🔧 torch.compile()로 모델 최적화 중...")

                    # GPU 환경에 최적화된 설정
                    compile_options = {
                        "mode": "max-autotune",  # GPU 최대 성능
                        "fullgraph": False,  # 호환성 향상
                    }

                    self.model = torch.compile(self.model, **compile_options)
                    logger.info(f"✅ torch.compile() 적용 완료 (첫 추론 시 컴파일됨)")

                except Exception as compile_error:
                    logger.warning(f"⚠️ torch.compile() 적용 실패: {str(compile_error)}")
                    logger.info(f"   기본 모델로 실행합니다")
            else:
                if device == "cpu":
                    logger.info(f"ℹ️ CPU 모드에서는 torch.compile() 건너뜀")
                elif not enable_compile:
                    logger.info(f"ℹ️ torch.compile() 비활성화됨 (안정성 우선)")
                    logger.info(f"   💡 활성화하려면: load_model(enable_compile=True)")

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

            # 프롬프트에서 클래스 순서 추출 (예: "person. helmet." → ["person", "helmet"])
            prompt_classes = [cls.strip() for cls in text_prompt.split('.') if cls.strip()]

            logger.info(f"🔍 Grounding DINO 추론 시작")
            logger.info(f"  - 프롬프트: {text_prompt}")
            logger.info(f"  - 프롬프트 클래스 순서: {prompt_classes}")
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

            # 원본 이미지 크기 저장
            original_size = image.size  # (width, height)
            logger.info(f"  - 원본 이미지 크기: {original_size[0]}x{original_size[1]}")

            # 추론 속도 향상을 위한 이미지 리사이징 (긴 축을 800px로 제한)
            max_size = 800
            width, height = image.size

            if max(width, height) > max_size:
                # 비율을 유지하면서 리사이징
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))

                image = image.resize((new_width, new_height), Image.LANCZOS)
                logger.info(f"  - 리사이징된 크기: {new_width}x{new_height} (속도 최적화)")
            else:
                logger.info(f"  - 리사이징 불필요 (이미 {max_size}px 이하)")

            # Processor로 입력 전처리
            device = next(self.model.parameters()).device

            # Transformers 버전 확인
            import transformers

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

            try:
                # 최신 버전: box_threshold, text_threshold 지원
                results = self.processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    box_threshold=box_threshold,
                    text_threshold=text_threshold,
                    target_sizes=[image.size[::-1]]
                )[0]

                # 결과 변환 (내장 threshold 필터링 사용)
                detections = self._postprocess_results(
                    boxes=results["boxes"],
                    scores=results["scores"],
                    labels=results["labels"],
                    image_size=image.size,
                    prompt_classes=prompt_classes,
                    original_size=original_size
                )

            except TypeError as e:
                # 구버전: threshold 파라미터 미지원 - 수동 필터링 (결과는 동일)
                logger.info(f"ℹ️ Transformers {transformers.__version__} - threshold 파라미터 미지원, 수동 필터링 사용 (결과 동일)")

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
                        image_size=image.size,
                        prompt_classes=prompt_classes,
                        original_size=original_size
                    )
                else:
                    detections = []

            logger.info(f"✅ Grounding DINO 추론 완료 - 탐지된 객체: {len(detections)}개")

            return {
                "boxes": detections,
                "num_detections": len(detections),
                "task_type": "bbox",
                "model_type": "grounding_dino",
                "text_prompt": text_prompt,
                "prompt_classes": prompt_classes  # 프롬프트 순서 정보 추가
            }

        except Exception as e:
            logger.error(f"❌ Grounding DINO 추론 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"추론 실패: {str(e)}")

    def _postprocess_results(
        self,
        boxes: torch.Tensor,
        scores: torch.Tensor,
        labels: List[str],
        image_size: tuple,
        prompt_classes: List[str] = None,
        original_size: tuple = None
    ) -> List[Dict]:
        """
        Grounding DINO 결과 후처리 (Transformers API)

        Args:
            boxes: 탐지된 박스 (픽셀 좌표 xyxy format)
            scores: 신뢰도 점수
            labels: 탐지된 텍스트 레이블
            image_size: 추론에 사용된 이미지 크기 (width, height)
            prompt_classes: 프롬프트 클래스 순서 (예: ["person", "helmet"])
            original_size: 원본 이미지 크기 (width, height) - 리사이징 시 필요

        Returns:
            List[Dict]: 박스 정보 리스트
        """
        detections = []
        img_width, img_height = image_size

        # 좌표 스케일 팩터 계산 (리사이징된 경우)
        if original_size and original_size != image_size:
            scale_x = original_size[0] / img_width
            scale_y = original_size[1] / img_height
            logger.info(f"  - 좌표 스케일업: {scale_x:.2f}x (가로), {scale_y:.2f}x (세로)")
        else:
            scale_x = 1.0
            scale_y = 1.0

        # 정규화 계산은 원본 크기 기준
        norm_width = original_size[0] if original_size else img_width
        norm_height = original_size[1] if original_size else img_height

        # 프롬프트 클래스 순서로 class_id 매핑 생성
        class_id_mapping = {}
        if prompt_classes:
            for idx, cls_name in enumerate(prompt_classes):
                class_id_mapping[cls_name.lower()] = idx
            logger.info(f"📋 클래스 ID 매핑 (프롬프트 순서): {class_id_mapping}")

        # Tensor를 numpy로 변환
        if isinstance(boxes, torch.Tensor):
            boxes = boxes.cpu().numpy()
        if isinstance(scores, torch.Tensor):
            scores = scores.cpu().numpy()

        for box, confidence, label in zip(boxes, scores, labels):
            # 픽셀 좌표 xyxy format
            x_min, y_min, x_max, y_max = box

            # 원본 크기로 스케일업 (리사이징된 경우)
            x_min = x_min * scale_x
            y_min = y_min * scale_y
            x_max = x_max * scale_x
            y_max = y_max * scale_y

            # xywh 형식으로 변환
            width = x_max - x_min
            height = y_max - y_min

            # 정규화된 좌표 계산 (원본 크기 기준)
            x_center_norm = ((x_min + x_max) / 2) / norm_width
            y_center_norm = ((y_min + y_max) / 2) / norm_height
            width_norm = width / norm_width
            height_norm = height / norm_height

            # 프롬프트 순서에 따라 class_id 할당
            label_clean = label.strip().lower()
            class_id = class_id_mapping.get(label_clean, -1) if prompt_classes else -1

            detection = {
                "class_id": class_id,  # 프롬프트 순서에 따른 class ID
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

    def predict_batch(self, images: List, **kwargs) -> List[Dict[str, Any]]:
        """
        Grounding DINO 배치 추론 (여러 이미지 동시 처리)

        Args:
            images: PIL Image 또는 numpy array 리스트
            **kwargs:
                - text_prompt (str): 탐지할 객체 텍스트 프롬프트 (예: "person. car. dog.")
                - box_threshold (float): 박스 신뢰도 임계값 (기본값: 0.3)
                - text_threshold (float): 텍스트 신뢰도 임계값 (기본값: 0.25)
                - batch_size (int): 배치 크기 (기본값: 4)

        Returns:
            List[Dict[str, Any]]: 각 이미지별 탐지 결과 리스트
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
            batch_size = kwargs.get('batch_size', 4)

            # 프롬프트에서 클래스 순서 추출
            prompt_classes = [cls.strip() for cls in text_prompt.split('.') if cls.strip()]

            logger.info(f"🔍 Grounding DINO 배치 추론 시작")
            logger.info(f"  - 총 이미지 수: {len(images)}개")
            logger.info(f"  - 배치 크기: {batch_size}")
            logger.info(f"  - 프롬프트: {text_prompt}")
            logger.info(f"  - Box threshold: {box_threshold}")
            logger.info(f"  - Text threshold: {text_threshold}")

            all_results = []

            # 이미지를 배치 단위로 처리
            for batch_idx in range(0, len(images), batch_size):
                batch_images = images[batch_idx:batch_idx + batch_size]
                batch_num = batch_idx // batch_size + 1
                total_batches = (len(images) + batch_size - 1) // batch_size

                logger.info(f"📦 배치 {batch_num}/{total_batches} 처리 중 ({len(batch_images)}개 이미지)")

                # 배치 이미지 전처리
                processed_images = []
                original_sizes = []

                for img in batch_images:
                    # PIL Image 변환
                    if not isinstance(img, Image.Image):
                        if isinstance(img, np.ndarray):
                            img = Image.fromarray(img)
                        else:
                            raise ValueError("이미지는 PIL Image 또는 numpy array여야 합니다")

                    # RGB 변환
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # 원본 크기 저장
                    original_sizes.append(img.size)

                    # 이미지 리사이징 (속도 최적화)
                    max_size = 800
                    width, height = img.size

                    if max(width, height) > max_size:
                        if width > height:
                            new_width = max_size
                            new_height = int(height * (max_size / width))
                        else:
                            new_height = max_size
                            new_width = int(width * (max_size / height))
                        img = img.resize((new_width, new_height), Image.LANCZOS)

                    processed_images.append(img)

                # Processor로 배치 입력 전처리
                device = next(self.model.parameters()).device

                inputs = self.processor(
                    images=processed_images,
                    text=[text_prompt] * len(processed_images),  # 각 이미지에 동일한 프롬프트
                    return_tensors="pt"
                ).to(device)

                # 배치 추론
                with torch.no_grad():
                    outputs = self.model(**inputs)

                # 배치 후처리
                try:
                    # 최신 버전: box_threshold, text_threshold 지원
                    results = self.processor.post_process_grounded_object_detection(
                        outputs,
                        inputs.input_ids,
                        box_threshold=box_threshold,
                        text_threshold=text_threshold,
                        target_sizes=[img.size[::-1] for img in processed_images]
                    )
                except TypeError:
                    # 구버전: threshold 파라미터 미지원
                    results = self.processor.post_process_grounded_object_detection(
                        outputs,
                        inputs.input_ids,
                        target_sizes=[img.size[::-1] for img in processed_images]
                    )

                    # threshold 수동 적용
                    filtered_results = []
                    for result in results:
                        filtered_boxes = []
                        filtered_scores = []
                        filtered_labels = []

                        for box, score, label in zip(result["boxes"], result["scores"], result["labels"]):
                            if float(score) >= box_threshold:
                                filtered_boxes.append(box)
                                filtered_scores.append(score)
                                filtered_labels.append(label)

                        if len(filtered_boxes) > 0:
                            filtered_results.append({
                                "boxes": torch.stack(filtered_boxes),
                                "scores": torch.stack(filtered_scores),
                                "labels": filtered_labels
                            })
                        else:
                            filtered_results.append({
                                "boxes": torch.tensor([]),
                                "scores": torch.tensor([]),
                                "labels": []
                            })
                    results = filtered_results

                # 각 이미지별로 결과 변환
                for idx, result in enumerate(results):
                    if len(result["boxes"]) > 0:
                        detections = self._postprocess_results(
                            boxes=result["boxes"],
                            scores=result["scores"],
                            labels=result["labels"],
                            image_size=processed_images[idx].size,
                            prompt_classes=prompt_classes,
                            original_size=original_sizes[idx]
                        )
                    else:
                        detections = []

                    all_results.append({
                        "boxes": detections,
                        "num_detections": len(detections),
                        "task_type": "bbox",
                        "model_type": "grounding_dino",
                        "text_prompt": text_prompt,
                        "prompt_classes": prompt_classes
                    })

                logger.info(f"✅ 배치 {batch_num}/{total_batches} 완료")

            logger.info(f"✅ 전체 배치 추론 완료 - 총 {len(all_results)}개 이미지 처리")

            return all_results

        except Exception as e:
            logger.error(f"❌ Grounding DINO 배치 추론 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"배치 추론 실패: {str(e)}")

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
            "supports_batch_inference": True,
            "zero_shot": True,
            "model_id": self.model_id,
            "source": "Hugging Face Hub"
        }
