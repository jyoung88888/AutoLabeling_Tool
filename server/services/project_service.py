"""프로젝트 저장 관련 서비스 모듈"""

import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ProjectService:
    """프로젝트 저장 및 관리를 담당하는 서비스 클래스"""
    
    def __init__(self, upload_dir: Path, image_manager, model_manager=None):
        self.upload_dir = upload_dir
        self.image_manager = image_manager
        self.model_manager = model_manager
    
    def save_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트를 저장합니다.

        Args:
            data: 프로젝트 저장 데이터

        Returns:
            저장 결과 정보
        """
        try:
            # 데이터 검증
            self._validate_project_data(data)

            # 모델 상태 사전 검증
            self._validate_model_state()

            project_name = data["projectName"]
            images = data["images"]
            base_path = data.get("basePath", "")

            # 프로젝트 경로 설정
            project_dir = self._create_project_directory(project_name, base_path)

            # 이미지 및 라벨 저장 (data 전달하여 class_info 사용 가능하게 함)
            save_results = self._save_images_and_labels(project_dir, images, data)

            # 프로젝트 정보 파일 저장
            self._save_project_info(project_dir, project_name, save_results, data)

            # 메모리 정리
            self._cleanup_memory_images()

            logger.info(f"프로젝트 저장 완료: {project_dir}")

            return {
                "success": True,
                "message": "프로젝트가 성공적으로 저장되었습니다.",
                "path": str(project_dir),
                "savedImages": save_results["saved_images"],
                "savedLabels": save_results["saved_labels"],
                "totalImages": len(images)
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"프로젝트 저장 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"프로젝트 저장 중 오류가 발생했습니다: {str(e)}")
    
    def save_class_file(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        클래스 파일을 저장합니다.
        
        Args:
            data: 클래스 파일 저장 데이터
            
        Returns:
            저장 결과 정보
        """
        try:
            project_path = data.get("projectPath")
            filename = data.get("filename")
            file_content = data.get("fileContent")
            
            if not project_path or not filename or file_content is None:
                raise HTTPException(status_code=400, detail="필수 데이터가 누락되었습니다.")
            
            file_path = Path(project_path) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            
            logger.info(f"클래스 파일 저장 완료: {file_path}")
            
            return {
                "success": True,
                "message": "클래스 파일이 성공적으로 저장되었습니다.",
                "path": str(file_path)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"클래스 파일 저장 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"클래스 파일 저장 중 오류가 발생했습니다: {str(e)}")
    
    def save_label_file(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        개별 라벨 파일을 저장합니다.
        
        Args:
            data: 라벨 파일 저장 데이터
            
        Returns:
            저장 결과 정보
        """
        try:
            project_path = data.get("projectPath")
            filename = data.get("filename")
            file_content = data.get("fileContent", "")
            
            if not project_path or not filename:
                raise HTTPException(status_code=400, detail="프로젝트 경로와 파일명이 필요합니다.")
            
            file_path = Path(project_path) / filename
            
            # 보안 검사
            if not self._is_safe_path(file_path):
                raise HTTPException(status_code=400, detail="잘못된 파일 경로입니다.")
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            
            logger.info(f"라벨 파일 저장 완료: {file_path}")
            
            return {
                "success": True,
                "message": "라벨 파일이 성공적으로 저장되었습니다.",
                "path": str(file_path),
                "filename": filename,
                "contentLength": len(file_content)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"라벨 파일 저장 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"라벨 파일 저장 중 오류가 발생했습니다: {str(e)}")
    
    def _validate_project_data(self, data: Dict[str, Any]) -> None:
        """프로젝트 데이터 유효성 검증"""
        if not data.get("projectName"):
            raise HTTPException(status_code=400, detail="프로젝트 이름이 필요합니다.")
        
        if not data.get("images") or not isinstance(data["images"], list):
            raise HTTPException(status_code=400, detail="유효하지 않은 이미지 데이터입니다.")
    
    def _validate_model_state(self) -> None:
        """모델 상태 검증 - Grounding DINO 지원"""
        logger.info("=== 모델 상태 사전 검증 ===")

        # model_manager가 없거나 YOLO 모델이 없는 경우 (Grounding DINO 등)
        if not self.model_manager or not hasattr(self.model_manager, 'model') or self.model_manager.model is None:
            logger.warning("⚠️ YOLO 모델 매니저가 없음 - Grounding DINO 등 다른 모델 사용 중일 수 있음")
            logger.info("📡 프론트엔드에서 전달된 class_info를 사용할 예정")
            # 프론트엔드에서 class_info를 전달받을 예정이므로 검증 통과
            return

        # YOLO 모델이 있는 경우 클래스 정보 확인
        try:
            logger.info("🔍 YOLO 모델 클래스 정보 사전 검증 시작...")
            model_classes_response = self.model_manager.get_model_classes()
            logger.info(f"📋 모델 클래스 응답: {model_classes_response}")

            if not model_classes_response:
                logger.error("❌ 모델 클래스 응답이 None입니다!")
                raise HTTPException(status_code=400, detail="모델 클래스 정보를 가져올 수 없습니다. 모델을 다시 로드해주세요.")

            if "classes" not in model_classes_response:
                logger.error(f"❌ 모델 클래스 응답에 'classes' 키가 없습니다: {model_classes_response}")
                raise HTTPException(status_code=400, detail="모델 클래스 정보를 가져올 수 없습니다. 모델을 다시 로드해주세요.")

            model_classes = model_classes_response.get("classes", {})
            logger.info(f"🎯 추출된 모델 클래스 (타입: {type(model_classes)}, 길이: {len(model_classes) if hasattr(model_classes, '__len__') else 'N/A'})")

            if not model_classes:
                logger.error("❌ 모델 클래스 정보가 비어있습니다!")
                raise HTTPException(status_code=400, detail="모델에 클래스 정보가 없습니다. 올바른 YOLO 모델을 로드해주세요.")

            if isinstance(model_classes, dict) and len(model_classes) == 0:
                logger.error("❌ 모델 클래스 딕셔너리가 비어있습니다!")
                raise HTTPException(status_code=400, detail="모델에 클래스 정보가 없습니다. 올바른 YOLO 모델을 로드해주세요.")
            elif isinstance(model_classes, list) and len(model_classes) == 0:
                logger.error("❌ 모델 클래스 리스트가 비어있습니다!")
                raise HTTPException(status_code=400, detail="모델에 클래스 정보가 없습니다. 올바른 YOLO 모델을 로드해주세요.")

            class_count = len(model_classes)
            logger.info(f"✅ YOLO 모델 상태 검증 완료: {class_count}개 클래스 확인")

            # 처음 10개 클래스만 로깅
            if isinstance(model_classes, dict):
                sorted_items = sorted(model_classes.items(), key=lambda x: int(x[0]))
                sample_classes = sorted_items[:10]
                logger.info(f"📋 모델 클래스 샘플 (딕셔너리): {sample_classes}")
                if len(sorted_items) > 10:
                    logger.info(f"   ... 및 {len(sorted_items) - 10}개 더")
            elif isinstance(model_classes, list):
                sample_classes = model_classes[:10]
                logger.info(f"📋 모델 클래스 샘플 (리스트): {sample_classes}")
                if len(model_classes) > 10:
                    logger.info(f"   ... 및 {len(model_classes) - 10}개 더")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 모델 상태 검증 중 오류: {str(e)}")
            import traceback
            logger.error(f"🔍 오류 상세: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"모델 상태 검증 실패: {str(e)}")
    
    def _create_project_directory(self, project_name: str, base_path: str) -> Path:
        """프로젝트 디렉토리 생성"""
        if base_path:
            project_dir = Path(base_path) / project_name
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
            project_dir = self.upload_dir / current_date / project_name
        
        project_dir.mkdir(parents=True, exist_ok=True)
        images_dir = project_dir / "images"
        labels_dir = project_dir / "labels"
        images_dir.mkdir(exist_ok=True)
        labels_dir.mkdir(exist_ok=True)
        
        return project_dir
    
    def _save_images_and_labels(self, project_dir: Path, images: List[Dict], data: Dict[str, Any]) -> Dict[str, int]:
        """이미지와 라벨 파일들을 저장"""
        images_dir = project_dir / "images"
        labels_dir = project_dir / "labels"

        # 프론트엔드에서 전달받은 class_info 우선 사용 (Grounding DINO 등)
        received_class_info = data.get("class_info")

        if received_class_info and isinstance(received_class_info, list) and len(received_class_info) > 0:
            logger.info("✅ 프론트엔드에서 전달받은 class_info 사용 (Grounding DINO 등)")
            classes_with_ids = sorted(received_class_info, key=lambda x: x.get("id", 0))
            model_classes = [cls["name"] for cls in classes_with_ids]
        else:
            # YOLO 모델에서 클래스 정보 가져오기
            logger.info("📡 YOLO 모델에서 클래스 정보 가져오기")
            classes_with_ids = self._get_current_model_classes()
            model_classes = [cls["name"] for cls in classes_with_ids]

        logger.info(f"라벨 저장에 사용할 클래스 순서: {model_classes}")

        saved_images = 0
        saved_labels = 0

        for image in images:
            try:
                # 이미지 파일 저장
                if self._save_single_image(image, images_dir):
                    saved_images += 1

                    # 라벨 파일 저장 (모델 클래스 순서 사용)
                    if self._save_single_label(image, labels_dir, model_classes):
                        saved_labels += 1

            except Exception as e:
                logger.warning(f"이미지 {image.get('filename', 'unknown')} 저장 중 오류: {str(e)}")
                continue

        return {"saved_images": saved_images, "saved_labels": saved_labels}
    
    def _save_single_image(self, image: Dict, images_dir: Path) -> bool:
        """단일 이미지 파일 저장"""
        filename = image.get("filename")
        if not filename:
            return False
        
        source_path = self.image_manager.find_image_path(filename)
        dest_path = images_dir / filename
        
        # 메모리 이미지인 경우
        if source_path and str(source_path).startswith("memory://"):
            memory_filename = str(source_path).replace("memory://", "")
            memory_data = self.image_manager.get_memory_image(memory_filename)
            
            if memory_data:
                with open(dest_path, "wb") as f:
                    f.write(memory_data)
                logger.info(f"[SAVE] 메모리 이미지를 디스크에 저장: {memory_filename}")
                self.image_manager.remove_memory_image(memory_filename)
                return True
        
        # 파일 시스템 이미지인 경우
        elif source_path and Path(source_path).exists():
            shutil.copy2(source_path, dest_path)
            logger.info(f"[SAVE] 파일 시스템 이미지 복사: {source_path}")
            return True
        
        return False
    
    def _save_single_label(self, image: Dict, labels_dir: Path, classes: List[str]) -> bool:
        """단일 라벨 파일 저장"""
        filename = image.get("filename")
        if not filename:
            return False
        
        label_filename = Path(filename).stem + ".txt"
        label_path = labels_dir / label_filename
        
        # 라벨 내용 생성
        label_content = self._generate_yolo_label_content(image, classes)
        
        with open(label_path, "w", encoding="utf-8") as f:
            f.write(label_content)
        
        return True
    
    def _generate_yolo_label_content(self, image: Dict, classes: List[str]) -> str:
        """YOLO 형식의 라벨 내용 생성"""
        content_lines = []
        boxes = image.get("boxes", [])
        
        if not boxes:
            return ""  # 빈 라벨 파일
        
        img_width = image.get("width", 1)
        img_height = image.get("height", 1)
        
        if img_width <= 0 or img_height <= 0:
            return ""
        
        for box in boxes:
            try:
                # 클래스 정보 처리
                class_name = box.get("class_name") or box.get("label", "unknown")
                class_id = self._get_class_id(class_name, classes)
                
                # 정규화된 좌표가 있으면 우선 사용 (서버에서 이미 계산됨)
                normalized_coords = box.get("normalized_coords")
                if normalized_coords and len(normalized_coords) == 4:
                    x_center, y_center, width, height = normalized_coords
                    # 유효성 검사
                    if 0 <= x_center <= 1 and 0 <= y_center <= 1 and width > 0 and height > 0:
                        yolo_coords = f"{x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                        content_lines.append(f"{class_id} {yolo_coords}")
                        logger.info(f"정규화된 좌표 직접 사용: {yolo_coords}")
                        continue
                
                # 정규화된 좌표가 없으면 bbox로부터 변환
                bbox = box.get("bbox", [])
                if len(bbox) >= 4:
                    yolo_coords = self._convert_to_yolo_format(bbox, img_width, img_height)
                    if yolo_coords:  # 빈 문자열이 아닌 경우
                        content_lines.append(f"{class_id} {yolo_coords}")
                        logger.info(f"bbox 변환 사용: {yolo_coords}")
                else:
                    logger.warning(f"유효하지 않은 박스 데이터: {box}")
                    
            except Exception as e:
                logger.warning(f"박스 처리 중 오류: {str(e)}")
                continue
        
        return "\n".join(content_lines)

    def _get_current_model_classes(self) -> List[Dict[str, Any]]:
        """현재 로드된 YOLO 모델의 클래스 정보를 정확히 가져옵니다."""
        logger.info("=== 현재 로드된 모델의 클래스 정보 가져오기 (MODEL MANAGER 사용) ===")
        
        try:
            if not self.model_manager:
                logger.error("❌ 모델 매니저가 없음")
                return []
                
            if not hasattr(self.model_manager, 'model') or self.model_manager.model is None:
                logger.error("❌ YOLO 모델이 로드되지 않음")
                return []
                
            # ModelManager의 get_model_classes 메서드를 직접 사용
            logger.info("📡 ModelManager.get_model_classes() 직접 호출...")
            
            try:
                model_classes_response = self.model_manager.get_model_classes()
                logger.info(f"📋 ModelManager 응답: {model_classes_response}")
                
                if not model_classes_response or "classes" not in model_classes_response:
                    logger.error("❌ ModelManager에서 유효한 클래스 정보를 받지 못함")
                    return []
                
                model_classes = model_classes_response["classes"]
                logger.info(f"🎯 ModelManager에서 받은 클래스 딕셔너리: {model_classes}")
                logger.info(f"🔍 타입: {type(model_classes)}, 길이: {len(model_classes) if hasattr(model_classes, '__len__') else 'N/A'}")
                
            except Exception as e:
                logger.error(f"❌ ModelManager.get_model_classes() 호출 실패: {str(e)}")
                return []
            
            classes_with_ids = []
            
            if isinstance(model_classes, dict) and len(model_classes) > 0:
                # ModelManager에서 이미 정렬된 딕셔너리를 받음: {0: 'person', 1: 'helmet', ...}
                logger.info("🔢 ModelManager에서 받은 딕셔너리 클래스 정보 처리 중...")
                logger.info(f"📊 ModelManager 클래스 딕셔너리: {model_classes}")
                
                # ModelManager에서 이미 정렬되어 오므로 그대로 사용
                for class_id, class_name in model_classes.items():
                    if class_name and isinstance(class_name, str) and class_name.strip():
                        classes_with_ids.append({
                            "id": int(class_id),
                            "name": class_name.strip()
                        })
                        logger.info(f"  ✅ ModelManager 클래스 추가 - ID {class_id}: '{class_name}'")
                    else:
                        logger.warning(f"  ⚠️ 건너뜀 - ID {class_id}: 빈 클래스명 '{class_name}'")
                        
                logger.info(f"✅ ModelManager 딕셔너리 클래스 처리 완료: {len(classes_with_ids)}개")
                
            else:
                logger.error(f"❌ ModelManager에서 받은 클래스 정보가 딕셔너리가 아니거나 비어있음")
                logger.error(f"❌ 타입: {type(model_classes)}, 내용: {model_classes}")
                return []
            
            # 결과 검증
            if not classes_with_ids:
                logger.error("❌ 처리된 클래스가 없습니다!")
                return []
            
            # 최종 결과 로깅 (ID 순서로 정렬하여 출력)
            classes_with_ids.sort(key=lambda x: x["id"])
            logger.info(f"🎉 ModelManager에서 클래스 정보 성공적으로 추출: {len(classes_with_ids)}개")
            logger.info("=== ModelManager에서 받은 최종 클래스 정보 (ID 순서) ===")
            for class_info in classes_with_ids:
                logger.info(f"  ID {class_info['id']}: '{class_info['name']}'")
                
            return classes_with_ids
            
        except Exception as e:
            logger.error(f"❌ ModelManager 클래스 정보 가져오기 실패: {str(e)}")
            import traceback
            logger.error(f"🔍 오류 상세: {traceback.format_exc()}")
            return []

    def _get_class_id(self, class_name: str, classes: List[str]) -> int:
        """클래스 이름으로부터 YOLO 모델의 정확한 ID 찾기"""
        logger.debug(f"=== 클래스 '{class_name}'의 ID 찾기 시작 ===")
        
        if class_name == "unknown":
            logger.debug(f"알 수 없는 클래스 '{class_name}', ID 0 사용")
            return 0
        
        # 현재 로드된 모델에서 직접 클래스 매핑 가져오기
        try:
            if not self.model_manager or not hasattr(self.model_manager, 'model') or self.model_manager.model is None:
                logger.warning("모델이 로드되지 않음. fallback 사용")
                return self._fallback_class_id(class_name, classes)
            
            # 모델에서 직접 클래스 정보 가져오기
            if hasattr(self.model_manager.model, 'names') and self.model_manager.model.names:
                model_classes = self.model_manager.model.names
                logger.debug(f"모델 names 속성: {model_classes}")
                
                if isinstance(model_classes, dict):
                    # 클래스 이름으로 ID 찾기
                    for class_id, class_name_in_model in model_classes.items():
                        if class_name_in_model == class_name:
                            logger.info(f"✅ 모델에서 클래스 '{class_name}' 찾음: ID {class_id}")
                            return int(class_id)
                    
                    logger.warning(f"모델에서 클래스 '{class_name}'를 찾지 못함. 모델 클래스: {list(model_classes.values())}")
                    return self._fallback_class_id(class_name, classes)
                    
                elif isinstance(model_classes, list):
                    try:
                        class_id = model_classes.index(class_name)
                        logger.info(f"✅ 리스트 모델에서 클래스 '{class_name}' 찾음: ID {class_id}")
                        return class_id
                    except ValueError:
                        logger.warning(f"리스트 모델에서 클래스 '{class_name}'를 찾지 못함. 모델 클래스: {model_classes}")
                        return self._fallback_class_id(class_name, classes)
                        
                else:
                    logger.warning(f"지원하지 않는 모델 클래스 형식: {type(model_classes)}")
                    return self._fallback_class_id(class_name, classes)
            else:
                logger.warning("모델에 names 속성이 없음")
                return self._fallback_class_id(class_name, classes)
                
        except Exception as e:
            logger.error(f"모델에서 클래스 ID 찾기 실패: {str(e)}")
            return self._fallback_class_id(class_name, classes)
    
    def _fallback_class_id(self, class_name: str, classes: List[str]) -> int:
        """fallback: 순서 기반 클래스 ID"""
        if classes and len(classes) > 0:
            try:
                class_id = classes.index(class_name)
                logger.warning(f"Fallback: 클래스 '{class_name}' 순서 기반 ID 사용: {class_id}")
                return class_id
            except ValueError:
                logger.warning(f"Fallback: 클래스 '{class_name}'를 찾을 수 없음. 사용 가능한 클래스: {classes}")
                return 0
        
        logger.warning(f"Fallback: 모델 정보 없음. 클래스 '{class_name}'를 ID 0으로 처리")
        return 0
    
    def _convert_to_yolo_format(self, bbox: List[float], img_width: int, img_height: int) -> str:
        """바운딩박스를 YOLO 형식으로 변환 (표준 x, y, width, height 형식)"""
        try:
            if len(bbox) != 4:
                logger.warning(f"잘못된 bbox 길이: {len(bbox)}")
                return ""
            
            # 표준 bbox 형식: [x, y, width, height] (좌상단 기준)
            x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
            
            logger.info(f"좌표 변환 입력: bbox=[{x}, {y}, {w}, {h}], 이미지크기={img_width}x{img_height}")
            
            # 박스 크기 유효성 검사
            if w <= 0 or h <= 0:
                logger.warning(f"유효하지 않은 박스 크기: width={w}, height={h}")
                return ""
            
            # YOLO 정규화 좌표로 변환 (중심점 기준)
            x_center = (x + w / 2) / img_width
            y_center = (y + h / 2) / img_height
            norm_width = w / img_width
            norm_height = h / img_height
            
            logger.info(f"박스 좌표 변환: [{x}, {y}, {w}, {h}] -> 정규화 좌표: [{x_center:.6f}, {y_center:.6f}, {norm_width:.6f}, {norm_height:.6f}]")
            
            # 좌표 유효성 검사
            if 0 <= x_center <= 1 and 0 <= y_center <= 1 and norm_width > 0 and norm_height <= 1 and norm_height > 0 and norm_width <= 1:
                result = f"{x_center:.6f} {y_center:.6f} {norm_width:.6f} {norm_height:.6f}"
                logger.info(f"변환 성공: {result}")
                return result
            else:
                logger.warning(f"유효하지 않은 정규화 좌표: center=({x_center:.3f}, {y_center:.3f}), size=({norm_width:.3f}, {norm_height:.3f})")
                return ""
                
        except (IndexError, ValueError) as e:
            logger.warning(f"좌표 변환 오류: {e}")
            return ""
    
    def _save_project_info(self, project_dir: Path, project_name: str, save_results: Dict, data: Dict) -> None:
        """프로젝트 정보 파일 저장 - 프론트엔드에서 전달받은 class_info를 우선 사용"""
        
        logger.info("=== 프로젝트 정보 저장 시작 ===")
        logger.info(f"모델 매니저 존재 여부: {self.model_manager is not None}")
        
        # 프론트엔드에서 전달받은 class_info 확인
        received_class_info = data.get("class_info")
        logger.info(f"프론트엔드에서 전달받은 class_info: {received_class_info}")
        
        classes_with_ids = []
        
        if received_class_info and isinstance(received_class_info, list) and len(received_class_info) > 0:
            # 프론트엔드에서 전달받은 class_info 사용
            logger.info("✅ 프론트엔드에서 전달받은 class_info 사용")
            
            try:
                # class_info 검증 및 정렬
                classes_with_ids = sorted(received_class_info, key=lambda x: x.get("id", 0))
                
                logger.info(f"✅ 프론트엔드에서 받은 {len(classes_with_ids)}개 클래스 정보 확인")
                logger.info("=== 프론트엔드에서 받은 클래스 정보 (ID 순서) ===")
                for class_info in classes_with_ids:
                    logger.info(f"  ID {class_info.get('id')}: '{class_info.get('name')}'")
                    
            except Exception as e:
                logger.error(f"❌ 프론트엔드 class_info 처리 오류: {str(e)}")
                classes_with_ids = []
        
        # 프론트엔드에서 class_info가 없거나 유효하지 않은 경우 모델에서 가져오기
        if not classes_with_ids:
            logger.info("📡 프론트엔드 class_info가 없음 - 현재 로드된 모델에서 클래스 정보 가져오기")
            
            classes_with_ids = self._get_current_model_classes()
            
            if not classes_with_ids:
                logger.error("❌ 현재 로드된 모델에서 클래스 정보를 가져오지 못했습니다!")
                logger.error("프로젝트 저장을 위해서는 반드시 YOLO 모델이 로드되어 있어야 합니다.")
                
                raise HTTPException(
                    status_code=400, 
                    detail="YOLO 모델이 로드되지 않았거나 클래스 정보를 가져올 수 없습니다. 먼저 모델을 로드한 후 프로젝트를 저장해주세요."
                )
            
            logger.info(f"✅ 모델에서 {len(classes_with_ids)}개 클래스 정보 확인")
            logger.info("=== 모델에서 가져온 클래스 정보 (정확한 YOLO ID 순서) ===")
            for class_info in classes_with_ids:
                logger.info(f"  ID {class_info.get('id')}: '{class_info.get('name')}'")

        project_info = {
            "projectName": project_name,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "totalImages": save_results["saved_images"],
            "savedImages": save_results["saved_images"],
            "savedLabels": save_results["saved_labels"],
            # class_info 키 추가 - 사이드바의 모델 클래스 선택 정보와 동일한 형태로 저장
            "class_info": classes_with_ids,
            "lowConfidenceImages": data.get("customLowConfidenceImages", [])
        }
        
        info_file = project_dir / f"{project_name}_info.json"
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump(project_info, f, ensure_ascii=False, indent=2)
            
        logger.info(f"프로젝트 정보 파일 저장 완료: {info_file}")
        logger.info("✅ JSON 파일에 class_info 키로 클래스 정보 저장됨 (사이드바와 동일한 형태)")
        logger.info("✅ 라벨 파일(.txt)에는 YOLO 모델의 정확한 ID 사용됨")
        logger.info("✅ 프로젝트 로드 시 class_info를 통해 클래스 번호와 이름 매칭")
        logger.info("=== 프로젝트 정보 저장 완료 ===")
    
    def _cleanup_memory_images(self) -> None:
        """메모리 이미지 정리"""
        remaining_memory_images = len(self.image_manager.memory_images)
        if remaining_memory_images > 0:
            logger.info(f"[SAVE] 프로젝트 저장 후 남은 메모리 이미지 {remaining_memory_images}개 정리")
            self.image_manager.clear_memory_images()
    
    def _is_safe_path(self, path: Path) -> bool:
        """경로가 안전한지 확인"""
        try:
            resolved_path = path.resolve()
            base_path = self.upload_dir.resolve()
            return str(resolved_path).startswith(str(base_path))
        except (OSError, ValueError):
            return False


 