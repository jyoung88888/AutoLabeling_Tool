"""
YOLO Pose Keypoint Detection Model Manager
YOLO Pose 키포인트 탐지 모델 관리자
"""
import torch
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
from io import BytesIO
from PIL import Image
from fastapi import HTTPException

from ..base_model import BaseModel, ModelType, TaskType

logger = logging.getLogger(__name__)


class YOLOPoseManager(BaseModel):
    """
    YOLO Pose 키포인트 탐지 모델 관리자
    사람의 포즈(키포인트)를 탐지합니다. (COCO 17 keypoints)
    """

    def __init__(self):
        """YOLO Pose 매니저 초기화"""
        super().__init__()
        self.model_type = ModelType.KEYPOINT
        self.task_type = TaskType.KEYPOINT
        self.num_keypoints = 17  # COCO format

        # COCO 17 keypoints 정의
        self.keypoint_names = [
            "nose",           # 0
            "left_eye",       # 1
            "right_eye",      # 2
            "left_ear",       # 3
            "right_ear",      # 4
            "left_shoulder",  # 5
            "right_shoulder", # 6
            "left_elbow",     # 7
            "right_elbow",    # 8
            "left_wrist",     # 9
            "right_wrist",    # 10
            "left_hip",       # 11
            "right_hip",      # 12
            "left_knee",      # 13
            "right_knee",     # 14
            "left_ankle",     # 15
            "right_ankle"     # 16
        ]

    def load_model(self, model_path: str, **kwargs):
        """
        YOLO Pose 모델 로딩

        Args:
            model_path (str): 모델 파일 경로 (yolov8n-pose.pt 등)
            **kwargs: 추가 설정
        """
        try:
            from ultralytics import YOLO

            model_path = Path(model_path)
            if not model_path.is_file():
                raise HTTPException(
                    status_code=404,
                    detail=f"모델 파일을 찾을 수 없습니다: {model_path}"
                )

            logger.info(f"🔄 YOLO Pose 모델 로딩 시작: {model_path}")
            self.model = YOLO(str(model_path))

            # GPU 사용 가능 시 GPU로 이동
            if torch.cuda.is_available():
                torch.cuda.set_device(0)
                self.model.to('cuda:0')
                logger.info(f"✅ YOLO Pose 모델을 GPU(cuda:0)로 로드")
            else:
                logger.info(f"✅ YOLO Pose 모델을 CPU로 로드")

            self.is_loaded = True
            logger.info(f"✅ YOLO Pose 모델 로딩 완료")

            return {
                "success": True,
                "message": f"YOLO Pose model {model_path.name} loaded successfully",
                "num_keypoints": self.num_keypoints
            }

        except Exception as e:
            logger.error(f"❌ YOLO Pose 모델 로딩 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"모델 로딩 실패: {str(e)}")

    def predict(self, image, **kwargs) -> Dict[str, Any]:
        """
        YOLO Pose 키포인트 탐지 추론

        Args:
            image: PIL Image, numpy array, 또는 BytesIO
            **kwargs:
                - confidence_threshold (float): 신뢰도 임계값 (기본값: 0.5)
                - imgsz (int): 추론 이미지 크기 (기본값: 640)

        Returns:
            Dict[str, Any]: 키포인트 탐지 결과
        """
        if not self.validate_model():
            raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다")

        try:
            # 파라미터 추출
            confidence_threshold = kwargs.get('confidence_threshold', 0.5)
            imgsz = kwargs.get('imgsz', 640)

            logger.info(f"🔍 YOLO Pose 추론 시작 - 신뢰도: {confidence_threshold}")

            # 이미지 전처리
            processed_image = self._preprocess_image(image)

            # YOLO Pose 추론 실행
            results = self.model.predict(
                processed_image,
                imgsz=imgsz,
                conf=confidence_threshold,
                iou=0.5,
                max_det=300,
                verbose=False,
                save=False,
                device=None
            )

            # 결과 후처리
            keypoints_data = self._postprocess_results(results[0])

            logger.info(f"✅ YOLO Pose 추론 완료 - 탐지된 사람: {len(keypoints_data)}명")

            return {
                "keypoints": keypoints_data,
                "num_persons": len(keypoints_data),
                "task_type": "keypoint",
                "model_type": "yolo_pose",
                "keypoint_format": "coco_17"
            }

        except Exception as e:
            logger.error(f"❌ YOLO Pose 추론 실패: {str(e)}")
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

    def _postprocess_results(self, result) -> List[Dict]:
        """
        YOLO Pose 결과 후처리

        Args:
            result: YOLO 결과 객체

        Returns:
            List[Dict]: 키포인트 정보 리스트
        """
        keypoints_data = []

        if not hasattr(result, 'keypoints') or result.keypoints is None:
            logger.info("탐지된 키포인트가 없습니다")
            return keypoints_data

        if len(result.keypoints) == 0:
            logger.info("탐지된 사람이 없습니다")
            return keypoints_data

        logger.info(f"탐지된 사람 수: {len(result.keypoints)}")

        # 키포인트 데이터 추출
        kpts_xy = result.keypoints.xy.cpu().numpy()  # (N, 17, 2) - 픽셀 좌표
        kpts_conf = result.keypoints.conf.cpu().numpy()  # (N, 17) - 신뢰도

        # 이미지 크기 (정규화용)
        img_height, img_width = result.orig_shape

        for person_idx, (person_kpts, person_conf) in enumerate(zip(kpts_xy, kpts_conf)):
            # 각 사람의 키포인트 정보
            keypoints_list = []

            for kpt_idx, (xy, conf) in enumerate(zip(person_kpts, person_conf)):
                x, y = xy
                keypoint_info = {
                    "name": self.keypoint_names[kpt_idx],
                    "x": float(x),
                    "y": float(y),
                    "confidence": float(conf),
                    "normalized_x": float(x / img_width),
                    "normalized_y": float(y / img_height),
                    "visible": conf > 0.5  # 신뢰도 0.5 이상이면 보임
                }
                keypoints_list.append(keypoint_info)

            # 바운딩 박스 정보 (있으면)
            bbox = None
            if hasattr(result, 'boxes') and result.boxes is not None:
                if len(result.boxes) > person_idx:
                    box = result.boxes[person_idx]
                    xywh = box.xywh[0].cpu().numpy()
                    x_center, y_center, width, height = xywh
                    x = x_center - width / 2
                    y = y_center - height / 2
                    bbox = [float(x), float(y), float(width), float(height)]

            person_data = {
                "person_id": person_idx,
                "keypoints": keypoints_list,
                "num_keypoints": self.num_keypoints,
                "bbox": bbox,
                "avg_confidence": float(np.mean(person_conf))
            }

            keypoints_data.append(person_data)

        return keypoints_data

    def get_model_info(self) -> Dict[str, Any]:
        """
        YOLO Pose 모델 정보 반환

        Returns:
            Dict[str, Any]: 모델 메타데이터
        """
        return {
            "model_type": "yolo_pose",
            "task": "keypoint",
            "framework": "ultralytics",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "is_loaded": self.is_loaded,
            "num_keypoints": self.num_keypoints,
            "keypoint_format": "coco_17",
            "keypoint_names": self.keypoint_names
        }
