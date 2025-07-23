"""
바운딩 박스 관련 유틸리티 함수
"""
import logging
from pathlib import Path
from fastapi import HTTPException
from PIL import Image
from typing import Dict, Any, List

try:
    # 상대 임포트 시도
    from ..core.utils import get_handle_positions
except ImportError:
    # 상대 임포트 실패 시 절대 임포트 시도
    try:
        from core.utils import get_handle_positions
    except ImportError:
        # 그래도 실패하면 기본 함수 정의
        def get_handle_positions(x, y, width, height):
            """기본 핸들 위치 함수"""
            return {
                "top_left": {"x": x, "y": y},
                "top_right": {"x": x + width, "y": y},
                "bottom_left": {"x": x, "y": y + height},
                "bottom_right": {"x": x + width, "y": y + height},
                "center": {"x": x + width/2, "y": y + height/2}
            }

# 로거 설정
logger = logging.getLogger(__name__)

class BboxManager:
    def __init__(self, upload_dir):
        self.upload_dir = upload_dir
        self.bbox_edits = {}  # 메모리에 바운딩 박스 정보를 저장할 딕셔너리
        
    def edit_bounding_box(self, data: Dict[str, Any], image_files: List[str]):
        """
        바운딩 박스를 편집합니다.
        
        Args:
            data: 바운딩 박스 편집 데이터
            image_files: 이미지 파일 목록
            
        Returns:
            편집된 바운딩 박스 정보
        """
        try:
            image_id = data.get("image_id")
            box_index = data.get("box_index")
            action = data.get("action")
            new_coords = data.get("new_coords", {})
            edit_mode = data.get("edit_mode", "active")
            
            if action == "toggle_edit":
                edit_status = edit_mode == "active"
                return {
                    "success": True,
                    "edit_mode": "active" if edit_status else "inactive",
                    "message": "바운딩 박스 편집 모드가 " + ("활성화" if edit_status else "비활성화") + "되었습니다."
                }
            
            if not image_id or box_index is None or not isinstance(box_index, int) or not action or not new_coords:
                raise HTTPException(
                    status_code=400,
                    detail="필수 파라미터가 누락되었습니다: image_id, box_index, action, new_coords"
                )
            
            image_path = None
            if image_id in image_files:
                image_path = self.upload_dir / image_id
            
            if not image_path or not image_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"이미지를 찾을 수 없습니다: {image_id}"
                )
            
            with Image.open(image_path) as img:
                img_width, img_height = img.size
            
            x = new_coords.get("x", 0)
            y = new_coords.get("y", 0)
            width = new_coords.get("width", 0)
            height = new_coords.get("height", 0)
            
            if width <= 0 or height <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="유효하지 않은 바운딩 박스 크기입니다."
                )
            
            # 이미지 경계 체크 및 보정
            if x < 0:
                width += x
                x = 0
            if y < 0:
                height += y
                y = 0
            if x + width > img_width:
                width = img_width - x
            if y + height > img_height:
                height = img_height - y
            
            # 최소 크기 보장
            if width < 10: width = 10
            if height < 10: height = 10
            
            # YOLO 형식 좌표 계산
            center_x = (x + width / 2) / img_width
            center_y = (y + height / 2) / img_height
            rel_width = width / img_width
            rel_height = height / img_height
            
            original_coords = [x, y, x + width, y + height]
            
            # 편집된 바운딩 박스 정보를 bbox_edits에 임시 저장
            if image_id not in self.bbox_edits:
                self.bbox_edits[image_id] = {"boxes": []}
            
            # 이전에 처리된 바운딩 박스 데이터가 있으면 해당 박스만 업데이트
            if image_id in self.bbox_edits and "boxes" in self.bbox_edits[image_id]:
                boxes = self.bbox_edits[image_id]["boxes"]
                if boxes is not None and isinstance(boxes, list) and box_index < len(boxes):
                    self.bbox_edits[image_id]["boxes"][box_index]["bbox"] = [x, y, width, height]
                    logger.info(f"바운딩 박스 업데이트: 이미지 {image_id}, 박스 {box_index}")
            
            response_data = {
                "box_index": box_index,
                "coords": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "textX": x + 2,
                    "textY": y - 5
                },
                "original_coords": original_coords,
                "yolo_coords": [center_x, center_y, rel_width, rel_height],
                "handle_positions": get_handle_positions(x, y, width, height)
            }
            
            return response_data
        except Exception as e:
            error_msg = f"바운딩 박스 편집 오류: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
    def save_bounding_boxes(self, data: Dict[str, Any], image_files: List[str]):
        """
        바운딩 박스 정보를 저장합니다.
        
        Args:
            data: 바운딩 박스 데이터
            image_files: 이미지 파일 목록
            
        Returns:
            저장 결과 정보
        """
        try:
            image_id = data.get("image_id")
            boxes = data.get("boxes", [])
            
            # 디버깅을 위한 로그 추가
            logger.info(f"바운딩 박스 저장 요청: 이미지 ID={image_id}, 박스 개수={len(boxes)}")
            if boxes:
                logger.info(f"첫 번째 박스 샘플: {boxes[0]}")
            else:
                logger.warning("저장할 바운딩 박스가 없습니다. 모든 기존 바운딩 박스를 삭제합니다.")
            
            if not image_id:  # boxes는 빈 배열일 수 있음 (모든 박스 삭제)
                logger.warning("이미지 ID가 누락되었습니다.")
                return {
                    "success": True,
                    "message": "바운딩 박스 저장 완료 (이미지 ID 없음)",
                    "image_id": "unknown",
                    "box_count": 0,
                    "boxes": []
                }
            
            # 이미지 ID에서 경로 부분 제거 (파일명만 사용)
            if '/' in image_id:
                image_id = image_id.split('/')[-1]
                logger.info(f"이미지 ID 정규화: {image_id}")
            
            image_path = None
            # 이미지 파일 목록에서 이미지 찾기 (파일 이름으로 완전 일치하지 않으면 포함 여부 확인)
            if image_id in image_files:
                image_path = self.upload_dir / image_id
            else:
                # 부분 일치 시도
                for img_file in image_files:
                    if image_id in img_file:
                        image_path = self.upload_dir / img_file
                        logger.info(f"부분 일치로 이미지 찾음: {img_file}")
                        break
            
            # 이미지를 찾지 못해도 바운딩 박스는 저장 (경고만 표시)
            if not image_path or not image_path.exists():
                logger.warning(f"이미지를 찾을 수 없습니다: {image_id} (바운딩 박스는 저장됨)")
            
            # 바운딩 박스가 없는 경우 빈 배열로 설정하고 저장
            if boxes is None:
                boxes = []
                logger.info(f"바운딩 박스가 None입니다. 빈 배열로 초기화합니다.")
                
            # 바운딩 박스 검증 (모든 필드가 존재하는지 확인)
            valid_boxes = []
            for i, box in enumerate(boxes):
                # 원래 필수 필드가 모두 있는지 확인
                has_required_fields = all(k in box for k in ["bbox", "conf", "class_name"])
                
                if not has_required_fields:
                    logger.warning(f"유효하지 않은 박스 데이터(인덱스 {i}): bbox, conf, class_name 필요")
                    # originalCoords가 있는 경우 bbox로 사용
                    if "originalCoords" in box and box["originalCoords"]:
                        box["bbox"] = box["originalCoords"]
                        logger.info(f"originalCoords를 bbox로 사용: {box['bbox']}")
                    
                    # 필수 데이터가 없는 경우 기본값으로 채움
                    box = {
                        "bbox": box.get("bbox", box.get("originalCoords", [0, 0, 10, 10])),
                        "conf": box.get("conf", box.get("confidence", 1.0)),
                        "class_name": box.get("class_name", box.get("label", "unknown"))
                    }
                valid_boxes.append(box)
            
            # 유효한 박스가 있는지 확인 - 빈 배열도 유효한 값으로 처리
            if not valid_boxes:
                logger.info("유효한 바운딩 박스가 없습니다. 모든 바운딩 박스가 삭제됩니다.")
            
            # 메모리에 편집된 박스 정보 저장 (빈 배열이라도 저장)
            self.bbox_edits[image_id] = {"boxes": valid_boxes}
            
            logger.info(f"바운딩 박스 저장 완료: 이미지 {image_id}, {len(valid_boxes)}개 박스")
            
            # 저장된 바운딩 박스 정보 로그 출력
            for i, box in enumerate(valid_boxes):
                bbox = box["bbox"]
                cls_name = box["class_name"]
                conf = box.get("conf", box.get("confidence", 1.0))
                logger.info(f"  [{i}] 클래스: {cls_name}, 신뢰도: {conf:.4f}, 좌표: {bbox}")
            
            return {
                "success": True,
                "message": f"{len(valid_boxes)}개의 바운딩 박스가 저장되었습니다.",
                "image_id": image_id,
                "box_count": len(valid_boxes),
                "boxes": valid_boxes  # 저장된 박스 데이터 반환
            }
        except Exception as e:
            error_msg = f"바운딩 박스 저장 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            # 예외가 발생하면 실패 상태로 처리
            return {
                "success": False,
                "message": f"바운딩 박스 저장 실패: {str(e)}",
                "error_info": str(e),
                "image_id": data.get("image_id", "unknown"),
                "box_count": 0,
                "boxes": []
            }
    
    def toggle_edit_mode(self, data: Dict[str, Any]):
        """
        바운딩 박스 편집 모드를 전환합니다.
        
        Args:
            data: 편집 모드 데이터
            
        Returns:
            편집 모드 정보
        """
        try:
            image_id = data.get("image_id")
            edit_mode = data.get("edit_mode", "active")
            
            if not image_id:
                raise HTTPException(
                    status_code=400,
                    detail="필수 파라미터가 누락되었습니다: image_id"
                )
            
            edit_status = edit_mode == "active"
            return {
                "success": True,
                "edit_mode": "active" if edit_status else "inactive",
                "message": "바운딩 박스 편집 모드가 " + ("활성화" if edit_status else "비활성화") + "되었습니다."
            }
        except Exception as e:
            error_msg = f"바운딩 박스 편집 모드 전환 오류: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def add_edit_handles(self, data: Dict[str, Any]):
        """
        바운딩 박스에 편집 핸들을 추가합니다.
        
        Args:
            data: 바운딩 박스 데이터
            
        Returns:
            핸들 위치 정보
        """
        try:
            image_id = data.get("image_id")
            box_index = data.get("box_index")
            
            if not all([image_id, isinstance(box_index, int)]):
                raise HTTPException(
                    status_code=400,
                    detail="필수 파라미터가 누락되었습니다: image_id, box_index"
                )
            
            coords = data.get("coords")
            if coords is None:
                raise HTTPException(
                    status_code=400,
                    detail="좌표 정보가 누락되었습니다."
                )
                
            x = coords.get("x", 0)
            y = coords.get("y", 0)
            width = coords.get("width", 0)
            height = coords.get("height", 0)
            
            handle_positions = get_handle_positions(x, y, width, height)
            
            return {
                "success": True,
                "box_index": box_index,
                "handle_positions": handle_positions
            }
        except Exception as e:
            error_msg = f"편집 핸들 추가 오류: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def start_editing(self, data: Dict[str, Any]):
        """
        바운딩 박스 편집을 시작합니다.
        
        Args:
            data: 편집 시작 데이터
            
        Returns:
            편집 모드 정보
        """
        try:
            image_id = data.get("image_id")
            edit_mode = data.get("edit_mode", "edit")
            
            if not image_id:
                raise HTTPException(
                    status_code=400,
                    detail="필수 파라미터가 누락되었습니다: image_id"
                )
            
            mode_messages = {
                "edit": "바운딩 박스 편집 모드 활성화 - 이동 및 크기 조절이 가능합니다.",
                "move": "바운딩 박스 이동 모드 활성화",
                "resize": "바운딩 박스 크기 조절 모드 활성화",
                "delete": "바운딩 박스 삭제 모드 활성화",
                "create": "바운딩 박스 생성 모드 활성화",
                "": "바운딩 박스 편집 모드 비활성화"
            }
            
            return {
                "success": True,
                "edit_mode": edit_mode,
                "message": mode_messages.get(edit_mode, "알 수 없는 편집 모드")
            }
        except Exception as e:
            error_msg = f"바운딩 박스 편집 시작 오류: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
    def get_boxes_for_image(self, image_id: str):
        """
        이미지에 대한 바운딩 박스 정보를 반환합니다.
        
        Args:
            image_id: 이미지 ID
            
        Returns:
            바운딩 박스 목록
        """
        if image_id in self.bbox_edits and 'boxes' in self.bbox_edits[image_id]:
            return self.bbox_edits[image_id]['boxes']
        return [] 