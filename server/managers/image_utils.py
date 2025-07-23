"""
이미지 관련 유틸리티 함수
"""
import os
import logging
import time
import json
from pathlib import Path
from fastapi import HTTPException
from PIL import Image
import base64

try:
    # 상대 임포트 시도
    from ..core.path_utils import find_image_paths, scan_image_files
except ImportError:
    # 상대 임포트 실패 시 절대 임포트 시도
    try:
        from core.path_utils import find_image_paths, scan_image_files
    except ImportError:
        # 기본 함수 정의
        def find_image_paths(upload_dir, filename):
            """기본 이미지 경로 찾기 함수"""
            if isinstance(upload_dir, str):
                upload_dir = Path(upload_dir)
            
            # 단순한 파일 찾기
            for root, dirs, files in os.walk(upload_dir):
                if filename in files:
                    return Path(root) / filename
            return None
        
        def scan_image_files(upload_dir, exclude_temp=True):
            """기본 이미지 파일 스캔 함수"""
            image_files = []
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
            
            if isinstance(upload_dir, str):
                upload_dir = Path(upload_dir)
            
            if not upload_dir.exists():
                return image_files
            
            for root, dirs, files in os.walk(upload_dir):
                for file in files:
                    if file.lower().endswith(extensions):
                        if exclude_temp and 'temp' in file.lower():
                            continue
                        rel_path = Path(root).relative_to(upload_dir) / file
                        image_files.append(str(rel_path))
            
            return image_files

def get_project_dir(upload_dir, project_path):
    """
    프로젝트 디렉터리 경로를 반환합니다.
    
    Args:
        upload_dir: 업로드 기본 디렉터리
        project_path: 프로젝트 경로 (상대 또는 절대)
        
    Returns:
        Path: 프로젝트 디렉터리 경로
    """
    if isinstance(upload_dir, str):
        upload_dir = Path(upload_dir)
    
    if isinstance(project_path, str):
        project_path = Path(project_path)
    
    # 절대 경로인 경우
    if project_path.is_absolute():
        return project_path
    
    # 상대 경로인 경우 upload_dir과 결합
    return upload_dir / project_path

# 로거 설정
logger = logging.getLogger(__name__)

class ImageManager:
    def __init__(self, upload_dir):
        self.upload_dir = upload_dir
        self.image_files = []
        self.memory_images = {}  # 메모리에 저장된 임시 이미지들 (파일명: {"data": bytes, "metadata": dict})
        
    def load_existing_images(self):
        """
        서버의 이미지 파일 목록을 메모리에 로드합니다.
        새로운 폴더 구조에 맞게 모든 프로젝트의 이미지를 조회합니다.
        """
        # scan_image_files 함수 사용으로 중복 제거
        self.image_files = scan_image_files(self.upload_dir, exclude_temp=True)
            
    def list_images(self):
        """
        이미지 목록을 반환합니다.
        
        Returns:
            이미지 목록 정보
        """
        try:
            return {
                "success": True,
                "images": sorted(self.image_files),
                "total_count": len(self.image_files)
            }
        except Exception as e:
            logger.error(f"이미지 목록 조회 오류: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="이미지 목록을 가져올 수 없습니다."
            )
            
    def refresh_images(self):
        """
        이미지 목록을 새로고침합니다.
        
        Returns:
            업데이트된 이미지 목록 정보
        """
        try:
            # scan_image_files 함수 사용으로 중복 제거
            self.image_files = scan_image_files(self.upload_dir, exclude_temp=True)
            
            logger.info(f"이미지 목록 새로고침 완료: {len(self.image_files)}개 파일 찾음")
            
            return {
                "success": True,
                "message": f"이미지 목록 새로고침 완료: {len(self.image_files)}개 파일 찾음",
                "images": sorted(self.image_files),
                "total_count": len(self.image_files)
            }
        except Exception as e:
            logger.error(f"이미지 목록 새로고침 오류: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"이미지 목록을 새로고칠 수 없습니다: {str(e)}"
            )
            
    def find_image_path(self, filename):
        """
        파일명에 해당하는 이미지 경로를 찾습니다.
        메모리 이미지, 프로젝트 파일 순으로 검색합니다.
        
        Args:
            filename: 이미지 파일명 또는 상대 경로
            
        Returns:
            이미지 파일 경로 또는 메모리 이미지 식별자
        """
        base_filename = os.path.basename(filename)
        
        # 1. 메모리에 저장된 이미지 먼저 확인
        if base_filename in self.memory_images:
            logger.debug(f"메모리에서 이미지 찾음: {base_filename}")
            return f"memory://{base_filename}"  # 특별한 식별자 반환
        
        # 2. 프로젝트 파일 시스템에서 검색
        found_path = find_image_paths(self.upload_dir, filename)
        
        return found_path
    
    def add_memory_image(self, filename, image_data, metadata=None):
        """
        이미지를 메모리에 저장합니다.
        
        Args:
            filename: 파일명
            image_data: 이미지 바이너리 데이터
            metadata: 추가 메타데이터 (width, height, project 등)
        """
        if metadata is None:
            metadata = {}
            
        self.memory_images[filename] = {
            "data": image_data,
            "metadata": metadata,
            "timestamp": time.time()
        }
        logger.info(f"이미지를 메모리에 저장: {filename} ({len(image_data)} bytes)")
    
    def get_memory_image(self, filename):
        """
        메모리에서 이미지 데이터를 가져옵니다.
        
        Args:
            filename: 파일명
            
        Returns:
            이미지 바이너리 데이터 또는 None
        """
        if filename in self.memory_images:
            return self.memory_images[filename]["data"]
        return None
    
    def remove_memory_image(self, filename):
        """
        메모리에서 이미지를 제거합니다.
        
        Args:
            filename: 파일명
        """
        if filename in self.memory_images:
            del self.memory_images[filename]
            logger.info(f"메모리에서 이미지 제거: {filename}")
    
    def clear_memory_images(self):
        """
        모든 메모리 이미지를 정리합니다.
        """
        count = len(self.memory_images)
        self.memory_images.clear()
        logger.info(f"메모리 이미지 {count}개 정리 완료")
            
    async def upload_files(self, files, project):
        """
        이미지 파일을 메모리에 업로드합니다. (디스크 임시 저장 제거)
        
        Args:
            files: 업로드할 파일 목록
            project: 대상 프로젝트명
            
        Returns:
            업로드 결과 정보
        """
        uploaded_files = []
        
        logger.info(f"[MEMORY] 메모리 기반 이미지 업로드 시작: 프로젝트={project}")
        
        # 각 파일 처리
        for file in files:
            try:
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in ['.jpg', '.jpeg', '.png']:
                    logger.warning(f"지원하지 않는 파일 형식: {file.filename}")
                    continue
                
                # 파일 데이터 읽기
                image_data = await file.read()
                
                # 이미지 파일 유효성 검사
                try:
                    from io import BytesIO
                    
                    # 이미지 검증
                    with Image.open(BytesIO(image_data)) as img:
                        img.verify()
                    
                    # 크기 정보 가져오기 (verify() 후에는 다시 열어야 함)
                    with Image.open(BytesIO(image_data)) as img:
                        width, height = img.size
                        
                    # 메모리에 이미지 저장
                    metadata = {
                        "width": width,
                        "height": height,
                        "project": project,
                        "size": len(image_data)
                    }
                    
                    self.add_memory_image(file.filename, image_data, metadata)
                    
                    # 응답에 이미지 정보 추가
                    uploaded_files.append({
                        "filename": file.filename,
                        "path": f"memory/{file.filename}",  # 메모리 경로 식별자
                        "width": width,
                        "height": height
                    })
                    
                    logger.info(f"[MEMORY] 이미지 메모리 업로드 성공: {file.filename} ({len(image_data)} bytes)")
                    
                except Exception as img_error:
                    logger.error(f"잘못된 이미지 파일 ({file.filename}): {str(img_error)}")
                    continue
                    
            except Exception as e:
                logger.error(f"파일 업로드 오류 ({file.filename}): {str(e)}")
                continue
        
        if not uploaded_files:
            raise HTTPException(status_code=400, detail="유효한 이미지 파일이 없습니다.")
        
        logger.info(f"[MEMORY] 메모리 업로드 완료: {len(uploaded_files)}개 파일, 총 메모리 이미지: {len(self.memory_images)}개")
        
        return {
            "success": True,
            "files": uploaded_files,
            "project": project
        }
        
    def save_yolo_format(self, project_path, filename, label_data, image_data=None, overwrite=False):
        """
        YOLO 형식으로 단일 이미지 결과를 서버에 저장합니다.
        
        Args:
            project_path: 프로젝트 경로
            filename: 파일명
            label_data: 라벨 데이터
            image_data: 이미지 데이터 (base64 인코딩, 선택 사항)
            overwrite: 덮어쓰기 여부
            
        Returns:
            저장 결과 정보
        """
        try:
            # 결과 저장 경로 결정
            project_dir = get_project_dir(self.upload_dir, project_path)
            images_dir = project_dir / "images"
            labels_dir = project_dir / "labels"
            
            logger.info(f"저장 디렉토리 경로: 프로젝트={project_dir}, 이미지={images_dir}, 라벨={labels_dir}")
            
            # 프로젝트 디렉토리 생성 (라벨링 작업을 위해 제한 해제)
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # 라벨링 작업을 위해 images, labels 폴더 생성 허용
            try:
                images_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"이미지 디렉토리 생성: {images_dir}")
            except Exception as e:
                logger.error(f"이미지 디렉토리 생성 실패: {str(e)}")
                
            try:
                labels_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"라벨 디렉토리 생성: {labels_dir}")
            except Exception as e:
                logger.error(f"라벨 디렉토리 생성 실패: {str(e)}")
            
            # 이미지 파일 경로 (프로젝트 내)
            dest_image_path = images_dir / filename
            
            # 덮어쓰기 모드에서는 먼저 이미지 파일이 이미 존재하는지 확인
            existing_image = dest_image_path.exists()
            
            # 이미지 처리 (덮어쓰기 모드가 아닐 때만)
            image_processed = False
            
            if not overwrite:
                # 메모리 이미지 확인
                memory_data = self.get_memory_image(filename)
                if memory_data:
                    # 메모리에서 디스크로 저장
                    with open(dest_image_path, "wb") as f:
                        f.write(memory_data)
                    logger.info(f"메모리 이미지를 디스크에 저장: {filename}")
                    
                    # 전역 이미지 목록에 추가
                    try:
                        # 프로젝트 상대 경로 생성
                        rel_project_path = project_dir.relative_to(self.upload_dir)
                        rel_path = str(rel_project_path / "images" / filename)
                        if rel_path not in self.image_files:
                            self.image_files.append(rel_path)
                    except Exception as e:
                        logger.warning(f"이미지 파일 목록 업데이트 오류: {str(e)}")
                    
                    # 메모리에서 제거
                    self.remove_memory_image(filename)
                    image_processed = True
                
                elif image_data:
                    # base64 이미지 데이터 디코딩 및 저장
                    try:
                        # 데이터 URL인 경우 (data:image/jpeg;base64,...)
                        if image_data.startswith('data:'):
                            image_binary = base64.b64decode(image_data.split(',')[1])
                        else:
                            # 패딩 처리
                            padding_needed = len(image_data) % 4
                            if padding_needed:
                                image_data += '=' * (4 - padding_needed)
                            
                            # base64 문자열인 경우
                            image_binary = base64.b64decode(image_data)
                        
                        # 이미지 저장
                        with open(dest_image_path, "wb") as f:
                            f.write(image_binary)
                        logger.info(f"base64 이미지 데이터로 이미지 저장: {dest_image_path}")
                        image_processed = True
                    except Exception as e:
                        logger.error(f"이미지 저장 오류: {str(e)}")
                        # 이미지 저장 실패해도 라벨은 저장 계속 진행
            
            # 라벨 파일 저장 (파일명의 확장자를 .txt로 변경)
            base_name = os.path.splitext(filename)[0]
            label_file = labels_dir / f"{base_name}.txt"
            
            try:
                with open(label_file, "w", encoding="utf-8") as f:
                    f.write(label_data if label_data is not None else "")
                logger.info(f"라벨 파일 저장 완료: {label_file}")
            except Exception as e:
                logger.error(f"라벨 파일 저장 오류: {str(e)}")
                raise HTTPException(status_code=500, detail=f"라벨 파일 저장 오류: {str(e)}")
            
            # 응답 메시지 구성
            if overwrite:
                if existing_image:
                    message = "라벨 정보가 성공적으로 저장되었습니다."
                else:
                    message = "이미지가 없지만 라벨 정보만 성공적으로 저장되었습니다."
            else:
                message = "YOLO 형식으로 데이터가 저장되었습니다."
            
            return {
                "success": True,
                "message": message,
                "path": str(project_dir),
                "labelPath": str(label_file),
                "image_path": str(dest_image_path) if (not overwrite and image_processed) or (overwrite and existing_image) else None,
                "overwrite": overwrite,
                "imageExists": existing_image
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"YOLO 내보내기 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"내보내기 오류: {str(e)}")

    def save_image_data(self, target_path, image_base64):
        """
        Base64 인코딩된 이미지 데이터를 파일로 저장합니다.
        
        Args:
            target_path: 저장할 대상 경로 (Path 객체)
            image_base64: Base64 인코딩된 이미지 데이터
            
        Returns:
            성공 여부 (Boolean)
        """
        try:
            # Base64 디코딩
            image_bytes = base64.b64decode(image_base64)
            
            # 파일 저장
            with open(target_path, "wb") as f:
                f.write(image_bytes)
                
            return True
        except Exception as e:
            logger.error(f"이미지 데이터 저장 오류: {str(e)}")
            return False 
    
    def save_class_file(self, data):
        """
        클래스 파일을 저장합니다.
        
        Args:
            data: 클래스 파일 저장 요청 데이터
                - projectPath: 프로젝트 경로
                - filename: 파일명
                - fileContent: 파일 내용 (JSON 문자열)
                
        Returns:
            저장 결과 정보
        """
        try:
            project_path = data.get("projectPath", "")
            filename = data.get("filename", "")
            file_content = data.get("fileContent", "")
            
            if not project_path or not filename or not file_content:
                raise HTTPException(status_code=400, detail="프로젝트 경로, 파일명, 파일 내용이 모두 필요합니다.")
            
            # 경로 정규화
            if project_path.startswith('upload_images/'):
                project_path = project_path[len('upload_images/'):]
            
            # 프로젝트 디렉토리 가져오기
            project_dir = get_project_dir(self.upload_dir, project_path)
            
            # 프로젝트 디렉토리 생성
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일 경로 생성
            file_path = project_dir / filename
            
            # JSON 내용 파싱하여 lowConfidenceImages가 true로 설정되지 않도록 수정
            try:
                json_data = json.loads(file_content)
                
                # lowConfidenceImages가 true로 설정된 경우 빈 배열로 변경
                if "lowConfidenceImages" in json_data:
                    if json_data["lowConfidenceImages"] is True or json_data["lowConfidenceImages"] is False:
                        logger.warning(f"lowConfidenceImages가 boolean 값({json_data['lowConfidenceImages']})으로 설정되어 있습니다. 빈 배열로 변경합니다.")
                        json_data["lowConfidenceImages"] = []
                    elif not isinstance(json_data["lowConfidenceImages"], list):
                        logger.warning(f"lowConfidenceImages가 배열이 아닙니다({type(json_data['lowConfidenceImages'])}). 빈 배열로 변경합니다.")
                        json_data["lowConfidenceImages"] = []
                
                # 수정된 JSON을 다시 문자열로 변환
                file_content = json.dumps(json_data, ensure_ascii=False, indent=2)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
                # JSON 파싱 실패 시 원본 내용 그대로 저장
            
            # 파일 저장
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
            raise HTTPException(status_code=500, detail=f"클래스 파일 저장 오류: {str(e)}")
            
    def load_project_results(self, project_path):
        """
        프로젝트의 라벨링 결과를 로드합니다.
        
        Args:
            project_path: 프로젝트 경로 (상대 경로 또는 절대 경로)
            
        Returns:
            라벨링 결과 정보 (이미지 경로, 라벨, 클래스 등)
        """
        try:
            logger.info(f"프로젝트 결과 로드 시작: {project_path}")
            
            # 경로 정규화
            if project_path.startswith('upload_images/'):
                project_path = project_path[len('upload_images/'):]
                
            # 프로젝트 디렉토리 가져오기
            project_dir = get_project_dir(self.upload_dir, project_path)
            logger.info(f"프로젝트 디렉토리: {project_dir}")
            
            # 프로젝트 디렉토리가 존재하는지 확인
            if not project_dir.exists() or not project_dir.is_dir():
                logger.error(f"프로젝트 디렉토리를 찾을 수 없음: {project_dir}")
                raise HTTPException(status_code=404, detail=f"프로젝트 디렉토리를 찾을 수 없습니다: {project_path}")
            
            # 이미지, 라벨 디렉토리 확인
            images_dir = project_dir / "images"
            labels_dir = project_dir / "labels"
            
            if not images_dir.exists() or not images_dir.is_dir():
                logger.error(f"이미지 디렉토리를 찾을 수 없음: {images_dir}")
                raise HTTPException(status_code=404, detail=f"이미지 디렉토리를 찾을 수 없습니다: {project_path}/images")
                
            if not labels_dir.exists() or not labels_dir.is_dir():
                logger.error(f"라벨 디렉토리를 찾을 수 없음: {labels_dir}")
                raise HTTPException(status_code=404, detail=f"라벨 디렉토리를 찾을 수 없습니다: {project_path}/labels")
            
            # 프로젝트 정보 파일 확인 및 로드
            project_name = project_dir.name
            info_file = project_dir / f"{project_name}_info.json"
            
            classes = []
            low_confidence_images = []
            
            # 프로젝트 정보 파일이 있으면 로드
            if info_file.exists() and info_file.is_file():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        project_info = json.load(f)
                        
                    # 클래스 정보 추출 (안전한 처리)
                    if 'classes' in project_info:
                        classes_data = project_info['classes']
                        
                        # None이나 False 값 체크
                        if not classes_data or classes_data is False:
                            logger.debug("클래스 정보가 비어있거나 False입니다.")
                            classes = []
                        # 다양한 클래스 정보 형식 처리
                        elif isinstance(classes_data, list):
                            # 새 형식: [{"id": 0, "name": "person"}, ...] 또는 기존 형식: ["person", "wheelchair", ...]
                            classes = []
                            for cls in classes_data:
                                if isinstance(cls, dict) and 'name' in cls:
                                    # 새 형식: {"id": 0, "name": "person"}
                                    classes.append(cls['name'])
                                elif isinstance(cls, str):
                                    # 기존 형식: "person"
                                    classes.append(cls)
                            # 클래스 정렬하여 일관성 보장
                            classes = sorted(classes)
                        elif isinstance(classes_data, dict):
                            # 클래스 사전 형식 (ID: 이름)
                            classes = sorted(list(classes_data.values()))
                        elif isinstance(classes_data, bool) and classes_data is True:
                            # True인 경우 기본 클래스 사용하지 않고 빈 배열
                            logger.debug("클래스 정보가 True로 설정되어 있습니다. 빈 클래스 목록을 사용합니다.")
                            classes = []
                        elif isinstance(classes_data, (int, float)):
                            # 숫자 값인 경우 무시
                            logger.debug(f"클래스 정보가 숫자입니다: {classes_data}")
                            classes = []
                        else:
                            logger.debug(f"알 수 없는 클래스 정보 형식: {type(classes_data)} - {classes_data}")
                            classes = []
                    
                    # 저신뢰도 이미지 정보 추출 (안전한 처리)
                    if 'lowConfidenceImages' in project_info:
                        low_conf_data = project_info['lowConfidenceImages']
                        if isinstance(low_conf_data, list):
                            low_confidence_images = low_conf_data
                        elif isinstance(low_conf_data, bool):
                            logger.debug(f"저신뢰도 이미지 정보가 boolean입니다: {low_conf_data}")
                            low_confidence_images = []
                        elif isinstance(low_conf_data, (int, float, str)):
                            logger.debug(f"저신뢰도 이미지 정보가 예상치 못한 타입입니다: {type(low_conf_data)} - {low_conf_data}")
                            low_confidence_images = []
                        else:
                            logger.debug(f"알 수 없는 저신뢰도 이미지 정보 형식: {type(low_conf_data)}")
                            low_confidence_images = []
                        
                    # 안전한 길이 계산
                    try:
                        classes_count = len(classes) if classes and hasattr(classes, '__len__') else 0
                        low_conf_count = len(low_confidence_images) if low_confidence_images and hasattr(low_confidence_images, '__len__') else 0
                        logger.info(f"프로젝트 정보 로드 완료: 클래스 {classes_count}개, 저신뢰도 이미지 {low_conf_count}개")
                    except Exception as len_error:
                        logger.error(f"길이 계산 오류: {str(len_error)}")
                        logger.info(f"프로젝트 정보 로드 완료: 클래스 타입={type(classes)}, 저신뢰도 이미지 타입={type(low_confidence_images)}")
                except Exception as e:
                    logger.error(f"프로젝트 정보 파일 파싱 오류: {str(e)}")
                    # 오류가 발생해도 진행 - 클래스 정보만 비어 있게 됨
                    classes = []
                    low_confidence_images = []
            
            # 이미지와 라벨 파일 매칭
            results = []
            image_count = 0  # 이미지 개수 계산용
            label_count = 0  # 라벨 개수 계산용
            
            # 이미지 파일 목록 가져오기
            image_files = [f for f in images_dir.glob("*") if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png')]
            
            for image_file in image_files:
                image_count += 1
                
                # 이미지 정보 구성
                image_info = {
                    "image_id": image_file.name,
                    "image_path": str(image_file.relative_to(self.upload_dir)),
                    "image_url": f"/server-image/{image_file.relative_to(self.upload_dir)}",
                }
                
                try:
                    # 이미지 크기 가져오기
                    with Image.open(image_file) as img:
                        image_info["image_width"] = img.width
                        image_info["image_height"] = img.height
                except Exception as e:
                    logger.warning(f"이미지 크기 확인 오류 ({image_file.name}): {str(e)}")
                    image_info["image_width"] = 0
                    image_info["image_height"] = 0
                
                # 해당 이미지에 대한 라벨 파일 찾기
                base_name = image_file.stem
                label_file = labels_dir / f"{base_name}.txt"
                
                annotations = []
                label_exists = False
                if label_file.exists() and label_file.is_file():
                    label_count += 1
                    try:
                        # YOLO 형식 라벨 파일 읽기 (class_id, x_center, y_center, width, height)
                        with open(label_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split()
                            if len(parts) < 5:
                                continue
                            class_id = int(parts[0])
                            x_center = float(parts[1]) * image_info["image_width"]
                            y_center = float(parts[2]) * image_info["image_height"]
                            width = float(parts[3]) * image_info["image_width"]
                            height = float(parts[4]) * image_info["image_height"]
                            x = x_center - width / 2
                            y = y_center - height / 2
                            class_name = "unknown"
                            if classes and class_id < len(classes):
                                class_name = classes[class_id]
                            annotations.append({
                                "class_id": class_id,
                                "class_name": class_name,
                                "confidence": 0.9,
                                "bbox": [x, y, width, height]
                            })
                        label_exists = len(annotations) > 0
                    except Exception as e:
                        logger.error(f"라벨 파일 파싱 오류 ({label_file.name}): {str(e)}")
                        label_exists = False
                else:
                    logger.warning(f"라벨 파일 없음: {label_file.name}")
                    label_exists = False
                # 라벨이 없는 경우에도 안내용 필드 추가
                image_info["annotations"] = annotations
                image_info["no_label"] = not label_exists
                results.append(image_info)
            
            logger.info(f"프로젝트 결과 로드 완료: 이미지 {image_count}개, 라벨 {label_count}개")
            
            return {
                "success": True,
                "project_path": project_path,
                "classes": classes,
                "results": results,
                "imageCount": image_count,
                "labelCount": label_count,
                "lowConfidenceImages": low_confidence_images
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"프로젝트 결과 로드 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"프로젝트 결과 로드 오류: {str(e)}") 