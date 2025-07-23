"""
경로 관련 유틸리티 함수
"""
import os
import re
import logging
from pathlib import Path
from typing import Optional, Union, List

from .config import (
    IMAGE_EXTENSIONS, UNSAFE_PATH_PREFIXES,
    IMAGES_DIR_NAME, LABELS_DIR_NAME, DEFAULT_PROJECT_NAME
)

logger = logging.getLogger(__name__)

def is_safe_path(path: Path) -> bool:
    """
    경로가 안전한지 확인합니다.
    
    Args:
        path: 검사할 경로
        
    Returns:
        안전한 경로인지 여부
    """
    try:
        path = path.resolve()
        
        for prefix in UNSAFE_PATH_PREFIXES:
            if str(path).startswith(prefix):
                return False
        
        return True
    except Exception:
        return False

def normalize_project_path(path_str: str) -> str:
    """
    프로젝트 경로에서 upload_images/ 또는 upload_images/projects/ 접두사를 제거합니다.
    
    Args:
        path_str: 원본 경로 문자열
        
    Returns:
        정규화된 경로 문자열
    """
    if isinstance(path_str, str):
        if path_str.startswith("upload_images/"):
            return path_str[len("upload_images/"):]
    
    return path_str

def get_project_dir(upload_dir: Path, project_path: str) -> Path:
    """
    프로젝트 경로로부터 실제 디렉토리 경로를 구성합니다.
    
    Args:
        upload_dir: 업로드 기본 디렉토리 (projects 디렉토리)
        project_path: 프로젝트 경로
        
    Returns:
        프로젝트 디렉토리 경로
    """
    # upload_images/ 또는 upload_images/projects/ 접두사 제거
    normalized_path = normalize_project_path(project_path)
    
    # 정규화된 경로를 Path 객체로 변환
    if isinstance(normalized_path, str):
        # 전체 상대 경로를 유지 (날짜/프로젝트명 형식 지원)
        return Path(upload_dir) / normalized_path
    
    # 기본값
    return Path(upload_dir) / DEFAULT_PROJECT_NAME

def find_image_paths(
    upload_dir: Path, 
    filename: str, 
) -> Optional[Path]:
    """
    파일명에 해당하는 이미지 경로를 찾습니다. (메모리 기반 시스템용)
    
    Args:
        upload_dir: 업로드 디렉토리
        temp_dir: 임시 디렉토리 (사용 안함 - 호환성용)
        filename: 이미지 파일명 또는 상대 경로
        temp_images: 임시 이미지 딕셔너리 (사용 안함 - 호환성용)
        
    Returns:
        이미지 파일 경로
    """
    logger.debug(f"이미지 검색 시작 (메모리 기반): {filename}")
    base_name = os.path.basename(filename)
    
    # temp 관련 검색은 제거됨 - 메모리 기반 시스템 사용
        
    # 3. 상대 경로 처리 (다양한 패턴 지원)
    if '/' in filename:
        # 3.1 정확한 상대 경로로 찾기
        try_path = upload_dir / filename
        if try_path.exists() and try_path.is_file():
            logger.debug(f"상대 경로 이미지 찾음: {try_path}")
            return try_path
            
        # 3.2 경로가 날짜 형식으로 시작하는 경우 (YYYY-MM-DD/...)
        parts = filename.split('/')
        if len(parts) >= 2 and re.match(r'\d{4}-\d{2}-\d{2}', parts[0]):
            # images 디렉토리가 없는 경우 추가해보기
            if IMAGES_DIR_NAME not in parts and len(parts) >= 3:
                revised_path = f"{parts[0]}/{parts[1]}/{IMAGES_DIR_NAME}/{parts[-1]}"
                try_path = upload_dir / revised_path
                if try_path.exists() and try_path.is_file():
                    logger.debug(f"images 디렉토리 추가하여 이미지 찾음: {try_path}")
                    return try_path
    
            # 4. 전체 폴더 검색 (파일 이름으로)
    for root, _, files in os.walk(upload_dir):
        for file in files:
            # 완전 일치
            if file == base_name:
                found_path = Path(os.path.join(root, file))
                logger.debug(f"전체 검색으로 이미지 찾음: {found_path}")
                return found_path
    
    # 5. 부분 일치로 검색
    for root, _, files in os.walk(upload_dir):
        for file in files:
            if base_name in file and file.lower().endswith(IMAGE_EXTENSIONS):
                found_path = Path(os.path.join(root, file))
                logger.debug(f"부분 일치 검색으로 이미지 찾음: {found_path}")
                return found_path
    
    # 이미지를 찾지 못함
    logger.error(f"이미지를 찾을 수 없음: {filename}")
    return None

def scan_image_files(upload_dir: Path, exclude_temp: bool = True) -> List[str]:
    """
    디렉토리에서 이미지 파일 목록을 스캔합니다.
    
    Args:
        upload_dir: 스캔할 디렉토리
        exclude_temp: temp 디렉토리 제외 여부
        
    Returns:
        이미지 파일의 상대 경로 목록
    """
    image_files = []
    
    try:
        logger.info("이미지 파일 스캔 중...")
        
        # 모든 하위 디렉토리에서 이미지 파일 검색
        for root, _, files in os.walk(upload_dir):
            for file in files:
                if file.lower().endswith(IMAGE_EXTENSIONS):
                    # temp 디렉토리는 건너뛰기 (옵션) - 메모리 기반으로 변경됨
                    if exclude_temp and "temp" in root:
                        continue
                        
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, upload_dir)
                    image_files.append(rel_path)
        
        logger.info(f"이미지 파일 스캔 완료: {len(image_files)}개")
    except Exception as e:
        logger.error(f"이미지 파일 스캔 오류: {str(e)}")
        
    return image_files

def clean_url_path(url_path: str) -> str:
    """
    URL 경로를 정리합니다.
    
    Args:
        url_path: 정리할 URL 경로
        
    Returns:
        정리된 경로
    """
    # 중복된 upload_images/ 접두사 제거
    while url_path.startswith("upload_images/upload_images/"):
        url_path = url_path.replace("upload_images/upload_images/", "upload_images/")
        
    # upload_images/ 접두사 제거
    if url_path.startswith("upload_images/"):
        url_path = url_path[len("upload_images/"):]
        
    # server-image 접두사 제거  
    if url_path.startswith("/server-image/"):
        url_path = url_path[len("/server-image/"):]
        
    return url_path

def resolve_image_path_from_url(upload_dir: Path, temp_dir: Path, url_path: str) -> Optional[Path]:
    """
    URL 경로로부터 실제 이미지 파일 경로를 찾습니다.
    
    Args:
        upload_dir: 업로드 디렉토리
        temp_dir: 임시 디렉토리  
        url_path: URL 경로
        
    Returns:
        실제 이미지 파일 경로
    """
    # URL 경로 정리
    clean_path = clean_url_path(url_path)
    
    # 1. 임시 폴더 경로 확인 (temp/temp_id/filename 패턴)
    if clean_path.startswith("temp/"):
        parts = Path(clean_path).parts
        if len(parts) >= 3:
            temp_id = parts[1]
            file_name = parts[2]
            temp_path = temp_dir / temp_id / file_name
            
            if temp_path.exists():
                logger.debug(f"임시 폴더에서 이미지 찾음: {temp_path}")
                return temp_path

    # 2. 업로드 디렉토리에서 찾기
    try_path = upload_dir / clean_path
    if try_path.exists():
        logger.debug(f"업로드 디렉토리에서 이미지 찾음: {try_path}")
        return try_path
        
    # 3. 확장자 추가하여 시도
    for ext in IMAGE_EXTENSIONS:
        if not clean_path.endswith(ext):
            test_with_ext = f"{clean_path}{ext}"
            test_path = upload_dir / test_with_ext
            if test_path.exists():
                logger.debug(f"확장자 추가하여 이미지 찾음: {test_path}")
                return test_path
    
    # 4. 일반적인 이미지 검색 사용
    return find_image_paths(upload_dir, clean_path)

def is_upload_dir_restricted_path(path: Path, upload_dir: Path) -> bool:
    """
    UPLOAD_DIR 경로에서 프로젝트 폴더를 제외한 모든 폴더/파일 생성을 막습니다.
    단, 이미지 파일과 라벨 파일은 허용합니다.
    
    Args:
        path: 생성하려는 경로
        upload_dir: UPLOAD_DIR 경로
        
    Returns:
        제한된 경로이면 True, 허용된 경로이면 False
    """
    try:
        path = path.resolve()
        upload_dir = upload_dir.resolve()
        
        # UPLOAD_DIR 내부가 아니면 허용
        if upload_dir not in path.parents and path != upload_dir:
            return False
            
        # UPLOAD_DIR 자체는 허용
        if path == upload_dir:
            return False
            
        # UPLOAD_DIR의 직접 하위 폴더 (프로젝트 폴더)는 허용
        relative_path = path.relative_to(upload_dir)
        path_parts = relative_path.parts
        
        # 프로젝트 폴더 (1단계 깊이)는 허용
        if len(path_parts) == 1:
            return False
            
        # 이미지 파일과 라벨 파일은 허용
        if path.is_file() or not path.exists():
            # 파일 확장자 확인
            file_ext = path.suffix.lower()
            if file_ext in IMAGE_EXTENSIONS or file_ext in ('.txt',):
                return False
                
        # images, labels 폴더는 허용
        if len(path_parts) >= 2:
            folder_name = path_parts[1]  # 프로젝트 폴더 다음 폴더
            if folder_name in [IMAGES_DIR_NAME, LABELS_DIR_NAME]:
                return False
            
        # 그 외 모든 경우는 제한 (json 파일 등)
        return True
        
    except Exception as e:
        logger.error(f"경로 제한 검사 오류: {str(e)}")
        return True  # 오류 시 제한 