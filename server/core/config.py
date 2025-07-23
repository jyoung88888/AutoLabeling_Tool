"""
서버 설정 및 상수 관리
"""
import os
import logging
from pathlib import Path

# 파일 확장자 정의
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp')
LABEL_EXTENSIONS = ('.txt',)
TEXT_FILE_EXTENSIONS = ('.txt', '.json', '.yaml', '.yml', '.md')

# 디렉토리 이름
IMAGES_DIR_NAME = "images"
LABELS_DIR_NAME = "labels"


# 프로젝트 구조 관련
INFO_FILE_SUFFIX = "_info.json"
DEFAULT_PROJECT_NAME = "default"



# 업로드 제한
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_UPLOAD_EXTENSIONS = IMAGE_EXTENSIONS

# 경로 설정 함수
def get_base_dir():
    """기본 디렉토리 경로를 환경 변수 또는 기본값으로 반환"""
    base_dir_env = os.getenv('AUTOLABELING_BASE_DIR')
    if base_dir_env:
        return Path(base_dir_env).resolve()
    return Path(__file__).parent.parent.resolve()  # server 디렉토리로 변경

def get_upload_dir():
    """업로드 디렉토리 경로를 환경 변수 또는 기본값으로 반환"""
    logger = logging.getLogger(__name__)
    
    # 현재 환경 변수 상태 로깅
    data_dir_env = os.getenv('AUTOLABELING_DATA_DIR')
    upload_dir_env = os.getenv('AUTOLABELING_UPLOAD_DIR')
    mode_env = os.getenv('AUTOLABELING_MODE', 'production')
    
    logger.info(f"=== 업로드 디렉토리 설정 확인 ===")
    logger.info(f"AUTOLABELING_DATA_DIR: {data_dir_env}")
    logger.info(f"AUTOLABELING_UPLOAD_DIR: {upload_dir_env}")
    logger.info(f"AUTOLABELING_MODE: {mode_env}")
    
    # 1. AUTOLABELING_UPLOAD_DIR 환경 변수 우선 확인 (명시적 경로 설정)
    if upload_dir_env:
        logger.info(f"✅ AUTOLABELING_UPLOAD_DIR 환경 변수 사용: {upload_dir_env}")
        result_path = Path(upload_dir_env).resolve()
        logger.info(f"📁 최종 경로: {result_path}")
        return result_path
    
    # 2. AUTOLABELING_DATA_DIR 환경 변수 확인 (run.py에서 설정하는 임시 변수)
    if data_dir_env:
        logger.info(f"✅ AUTOLABELING_DATA_DIR 환경 변수 사용: {data_dir_env}")
        # 상대 경로인 경우 프로젝트 루트 기준으로 해석
        if not os.path.isabs(data_dir_env):
            result_path = get_base_dir().parent / data_dir_env
            logger.info(f"📁 최종 경로 (상대 -> 절대): {result_path}")
            return result_path
        result_path = Path(data_dir_env).resolve()
        logger.info(f"📁 최종 경로 (절대): {result_path}")
        return result_path
    
    # 3. 기본값: server/uploaded_images 디렉토리 사용 (모드에 관계없이 통일)
    logger.info(f"🔧 환경 변수 없음 - 기본값 사용 (모드: {mode_env})")
    logger.info("📁 모든 모드에서 동일한 디렉토리 사용: server/uploaded_images")
    
    # 기본값: server 디렉토리 하위의 uploaded_images
    result_path = get_base_dir() / "uploaded_images"
    logger.info(f"📁 기본 업로드 디렉토리: {result_path}")
    logger.info(f"   ℹ️  개발/운영 구분 없이 통일된 디렉토리 사용")
    return result_path

def get_model_dir():
    """모델 디렉토리 경로 반환"""
    return get_base_dir() / "models"



def get_vue_dist_dir():
    """Vue 빌드 파일 디렉토리 경로 반환"""
    return get_base_dir().parent / "dist"

# 안전하지 않은 경로 접두사
UNSAFE_PATH_PREFIXES = ['/etc', '/bin', '/sbin', '/var', '/dev', '/boot']

# API 태그 메타데이터
API_TAGS_METADATA = [
    {
        "name": "Root",
        "description": "Root and static file operations."
    },
    {
        "name": "Models",
        "description": "Operations with models: list, details, load."
    },
    {
        "name": "Images", 
        "description": "Operations with images: upload, download, list, predict."
    },
    {
        "name": "Labeling",
        "description": "Operations for automatic labeling."
    },
    {
        "name": "Files",
        "description": "Operations for file management."
    },
    {
        "name": "Projects",
        "description": "Operations for project management."
    }
] 