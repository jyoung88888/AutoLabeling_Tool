"""
YOLO Detection Model Manager
YOLO 객체 탐지 모델 관리자
"""
import torch
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from io import BytesIO
from PIL import Image
from fastapi import HTTPException

from ..base_model import BaseModel, ModelType, TaskType

logger = logging.getLogger(__name__)


class YOLOManager(BaseModel):
    """
    YOLO 객체 탐지 모델 관리자
    Ultralytics YOLO (v8/v11) 모델을 관리합니다.
    """

    def __init__(self):
        """YOLO 매니저 초기화"""
        super().__init__()
        self.model_type = ModelType.DETECTION
        self.task_type = TaskType.BBOX
        self.classes = None

    def load_model(self, model_path: str, **kwargs):
        """
        YOLO 모델 로딩

        Args:
            model_path (str): 모델 파일 경로 (.pt, .pth)
            **kwargs: 추가 설정
        """
        try:
            from ultralytics import YOLO

            model_path = Path(model_path)
            if not model_path.is_file():
                raise HTTPException(status_code=404, detail=f"모델 파일을 찾을 수 없습니다: {model_path}")

            logger.info(f"🔄 YOLO 모델 로딩 시작: {model_path}")
            self.model = YOLO(str(model_path))

            # GPU 사용 가능 시 GPU로 이동
            if torch.cuda.is_available():
                torch.cuda.set_device(0)
                self.model.to('cuda:0')
                logger.info(f"✅ YOLO 모델을 GPU(cuda:0)로 로드")
            else:
                logger.info(f"✅ YOLO 모델을 CPU로 로드")

            # 클래스 정보 저장
            self.classes = self.model.names
            self.is_loaded = True

            logger.info(f"✅ YOLO 모델 로딩 완료: {len(self.classes)}개 클래스")
            return {
                "success": True,
                "message": f"Model {model_path.name} loaded successfully",
                "num_classes": len(self.classes)
            }

        except Exception as e:
            logger.error(f"❌ YOLO 모델 로딩 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"모델 로딩 실패: {str(e)}")

    def predict(self, image, **kwargs) -> Dict[str, Any]:
        """
        YOLO 객체 탐지 추론

        Args:
            image: PIL Image, numpy array, 또는 BytesIO
            **kwargs:
                - confidence_threshold (float): 신뢰도 임계값 (기본값: 0.5)
                - selected_classes (List[str]): 필터링할 클래스 목록
                - imgsz (int): 추론 이미지 크기 (기본값: 640)

        Returns:
            Dict[str, Any]: 탐지 결과
        """
        if not self.validate_model():
            raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다")

        try:
            # 파라미터 추출
            confidence_threshold = kwargs.get('confidence_threshold', 0.5)
            selected_classes = kwargs.get('selected_classes', None)
            imgsz = kwargs.get('imgsz', 640)

            logger.info(f"🔍 YOLO 추론 시작 - 신뢰도: {confidence_threshold}")

            # 이미지 전처리
            processed_image = self._preprocess_image(image)

            # YOLO 추론 실행
            results = self.model.predict(
                processed_image,
                imgsz=imgsz,
                conf=confidence_threshold,
                iou=0.5,
                max_det=300,
                augment=False,
                agnostic_nms=False,
                classes=None,
                half=False,
                device=None,
                verbose=False,
                save=False,
                retina_masks=False,
                rect=True,
                batch=1
            )

            # 결과 후처리
            boxes = self._postprocess_results(results[0], selected_classes)

            logger.info(f"✅ YOLO 추론 완료 - 탐지된 객체: {len(boxes)}개")

            return {
                "boxes": boxes,
                "num_detections": len(boxes),
                "task_type": "bbox",
                "model_type": "yolo"
            }

        except Exception as e:
            logger.error(f"❌ YOLO 추론 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"추론 실패: {str(e)}")

    def _preprocess_image(self, image_input):
        """
        이미지 전처리

        Args:
            image_input: BytesIO, PIL Image, numpy array 등

        Returns:
            PIL Image: 전처리된 이미지
        """
        if isinstance(image_input, BytesIO):
            try:
                image_input.seek(0)
                pil_image = Image.open(image_input)

                # 색상 모드 변환
                if pil_image.mode in ('RGBA', 'LA'):
                    rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                    if pil_image.mode == 'RGBA':
                        rgb_image.paste(pil_image, mask=pil_image.split()[-1])
                    else:
                        rgb_image.paste(pil_image.convert('L'))
                    pil_image = rgb_image
                elif pil_image.mode not in ('RGB', 'L'):
                    pil_image = pil_image.convert('RGB')

                logger.info(f"BytesIO → PIL Image 변환: {pil_image.mode}, {pil_image.size}")
                return pil_image

            except Exception as e:
                logger.error(f"이미지 전처리 실패: {str(e)}")
                raise HTTPException(status_code=400, detail=f"이미지 처리 실패: {str(e)}")

        return image_input

    def _postprocess_results(self, result, selected_classes: Optional[List[str]] = None) -> List[Dict]:
        """
        YOLO 결과 후처리

        Args:
            result: YOLO 결과 객체
            selected_classes: 필터링할 클래스 목록

        Returns:
            List[Dict]: 박스 정보 리스트
        """
        boxes = []

        if result.boxes is None or len(result.boxes) == 0:
            logger.info("탐지된 객체가 없습니다")
            return boxes

        logger.info(f"탐지된 박스 수: {len(result.boxes)}")

        for box in result.boxes:
            try:
                # 클래스 정보
                class_id = int(box.cls.item())
                class_name = self.classes.get(class_id, f"class_{class_id}")

                # 선택된 클래스 필터링
                if selected_classes and len(selected_classes) > 0:
                    if class_name not in selected_classes:
                        continue

                # 신뢰도
                confidence = float(box.conf.item())

                # 정규화된 좌표 (YOLO 포맷: x_center, y_center, width, height)
                xywhn = box.xywhn[0]
                x_center_norm = float(xywhn[0])
                y_center_norm = float(xywhn[1])
                width_norm = float(xywhn[2])
                height_norm = float(xywhn[3])

                # 픽셀 좌표
                xywh = box.xywh[0]
                x_center = float(xywh[0])
                y_center = float(xywh[1])
                width = float(xywh[2])
                height = float(xywh[3])

                # 좌상단 좌표
                x = x_center - width / 2
                y = y_center - height / 2

                box_info = {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [float(x), float(y), float(width), float(height)],
                    "normalized_coords": [x_center_norm, y_center_norm, width_norm, height_norm]
                }

                boxes.append(box_info)

            except Exception as e:
                logger.error(f"박스 처리 오류: {str(e)}")
                continue

        return boxes

    def get_model_info(self) -> Dict[str, Any]:
        """
        YOLO 모델 정보 반환

        Returns:
            Dict[str, Any]: 모델 메타데이터
        """
        info = {
            "model_type": "yolo",
            "task": "detection",
            "framework": "ultralytics",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "is_loaded": self.is_loaded
        }

        if self.is_loaded and self.classes:
            info["num_classes"] = len(self.classes)
            info["class_names"] = list(self.classes.values()) if isinstance(self.classes, dict) else self.classes

        return info

    def get_model_classes(self) -> Dict[str, Any]:
        """
        모델 클래스 정보 반환 (기존 호환성 유지)

        Returns:
            Dict[str, Any]: 클래스 정보
        """
        if not self.validate_model():
            raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다")

        if isinstance(self.classes, dict):
            sorted_classes = dict(sorted(self.classes.items()))
            return {
                "success": True,
                "classes": sorted_classes,
                "total_classes": len(sorted_classes)
            }

        return {
            "success": True,
            "classes": self.classes,
            "total_classes": len(self.classes) if self.classes else 0
        }

    def get_device_info(self) -> Dict[str, Any]:
        """
        디바이스 정보 반환

        Returns:
            Dict[str, Any]: GPU/CPU 정보
        """
        gpu_info = {
            "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "없음",
            "count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "cuda_available": torch.cuda.is_available()
        }
        return {"gpu_info": gpu_info}
