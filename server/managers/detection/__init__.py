"""
Detection models package
객체 탐지 모델 패키지
"""
from .yolo_manager import YOLOManager

try:
    from .grounding_dino_manager import GroundingDINOManager
except ImportError:
    GroundingDINOManager = None

__all__ = ['YOLOManager', 'GroundingDINOManager']
