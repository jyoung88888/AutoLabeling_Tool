"""
자동 라벨링 서버 유틸리티 함수
"""
import logging
from pathlib import Path

from .config import IMAGES_DIR_NAME, LABELS_DIR_NAME, INFO_FILE_SUFFIX
from .path_utils import scan_image_files

# 로거 설정
logger = logging.getLogger(__name__)

def cleanup_memory_images_info():
    """
    메모리 기반 시스템으로 변경됨에 따른 정보 함수.
    이제 temp 폴더 대신 메모리에서 이미지를 관리합니다.
    
    메모리 이미지 정리는 다음 시점에 자동으로 수행됩니다:
    - 프로젝트 저장 완료 후
    - 서버 재시작 시 (메모리 초기화)
    - ImageManager.clear_memory_images() 호출 시
    
    Returns:
        정보성 메시지 (실제 정리 작업은 ImageManager에서 수행)
    """
    return "메모리 기반 시스템 사용 중 - temp 폴더 정리 불필요"

def get_handle_positions(x, y, width, height, handle_size=1):
    """
    바운딩 박스 편집 핸들 위치를 계산합니다.
    
    Args:
        x: 바운딩 박스 x 좌표
        y: 바운딩 박스 y 좌표
        width: 바운딩 박스 너비
        height: 바운딩 박스 높이
        handle_size: 핸들 크기
        
    Returns:
        핸들 위치 정보
    """
    return {
        "nw": {"x": x - handle_size, "y": y - handle_size, "type": "nw", "color": "#4CAF50"},
        "n": {"x": x + width / 2 - handle_size, "y": y - handle_size, "type": "n", "color": "#2196F3"},
        "ne": {"x": x + width - handle_size, "y": y - handle_size, "type": "ne", "color": "#4CAF50"},
        "w": {"x": x - handle_size, "y": y + height / 2 - handle_size, "type": "w", "color": "#2196F3"},
        "e": {"x": x + width - handle_size, "y": y + height / 2 - handle_size, "type": "e", "color": "#2196F3"},
        "sw": {"x": x - handle_size, "y": y + height - handle_size, "type": "sw", "color": "#4CAF50"},
        "s": {"x": x + width / 2 - handle_size, "y": y + height - handle_size, "type": "s", "color": "#2196F3"},
        "se": {"x": x + width - handle_size, "y": y + height - handle_size, "type": "se", "color": "#4CAF50"},
        "move": {"x": x + width / 2 - handle_size, "y": y + height / 2 - handle_size, "type": "move", "color": "#FF9800"}
    }

def is_valid_project_structure(project_dir: Path) -> bool:
    """
    유효한 프로젝트 구조인지 검증합니다.
    
    유효한 프로젝트 구조:
    - {프로젝트 폴더}/
      - images/ 폴더 (.jpg 또는 .png 파일만 포함)
      - labels/ 폴더 (.txt 파일만 포함)
      - {프로젝트명}_info.json 파일
    
    Args:
        project_dir: 프로젝트 디렉토리 경로
        
    Returns:
        유효한 프로젝트 구조이면 True, 아니면 False
    """
    try:
        # 1. images 폴더 존재 확인
        images_dir = project_dir / IMAGES_DIR_NAME
        if not images_dir.exists() or not images_dir.is_dir():
            logger.debug(f"프로젝트 구조 검증 실패: {project_dir} - {IMAGES_DIR_NAME} 폴더 없음")
            return False
            
        # 2. labels 폴더 존재 확인
        labels_dir = project_dir / LABELS_DIR_NAME
        if not labels_dir.exists() or not labels_dir.is_dir():
            logger.debug(f"프로젝트 구조 검증 실패: {project_dir} - {LABELS_DIR_NAME} 폴더 없음")
            return False
            
        # 3. {프로젝트명}_info.json 파일 존재 확인
        info_file = project_dir / f"{project_dir.name}{INFO_FILE_SUFFIX}"
        if not info_file.exists() or not info_file.is_file():
            logger.debug(f"프로젝트 구조 검증 실패: {project_dir} - {project_dir.name}{INFO_FILE_SUFFIX} 파일 없음")
            return False
            
        # 이미지 파일 개수 계산
        from .config import IMAGE_EXTENSIONS, LABEL_EXTENSIONS
        image_count = len([f for f in images_dir.glob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS])
        # 라벨 파일 개수 계산
        label_count = len([f for f in labels_dir.glob("*.txt") if f.is_file()])
        
        logger.debug(f"프로젝트 구조 검증 성공: {project_dir} - 이미지 {image_count}개, 라벨 {label_count}개")
            
        # 모든 조건 만족
        return True
    except Exception as e:
        logger.error(f"프로젝트 구조 검증 오류: {str(e)}")
        return False

# is_upload_dir_restricted_path 함수는 path_utils.py로 이동됨

def safe_mkdir(path, upload_dir):
    """
    UPLOAD_DIR 제한을 고려한 안전한 폴더 생성
    
    Args:
        path: 생성할 폴더 경로
        upload_dir: UPLOAD_DIR 경로
        
    Returns:
        생성 성공 여부
    """
    from .path_utils import is_upload_dir_restricted_path
    
    if is_upload_dir_restricted_path(Path(path), Path(upload_dir)):
        logger.warning(f"UPLOAD_DIR 내 제한된 경로에 폴더 생성 시도 차단: {path}")
        return False
        
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"폴더 생성 오류: {str(e)}")
        return False

def safe_file_write(file_path, content, upload_dir):
    """
    UPLOAD_DIR 제한을 고려한 안전한 파일 쓰기
    
    Args:
        file_path: 파일 경로
        content: 파일 내용
        upload_dir: UPLOAD_DIR 경로
        
    Returns:
        쓰기 성공 여부
    """
    from .path_utils import is_upload_dir_restricted_path
    
    if is_upload_dir_restricted_path(Path(file_path), Path(upload_dir)):
        logger.warning(f"UPLOAD_DIR 내 제한된 경로에 파일 생성 시도 차단: {file_path}")
        return False
        
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"파일 쓰기 오류: {str(e)}")
        return False 