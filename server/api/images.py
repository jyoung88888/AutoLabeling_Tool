"""
이미지 관련 API 엔드포인트
"""
import logging
import os
from pathlib import Path
from typing import List, TYPE_CHECKING, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

if TYPE_CHECKING:
    from managers.image_utils import ImageManager

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()

# 전역 변수들 (main.py에서 설정됨)
image_manager: Optional['ImageManager'] = None  # main.py에서 설정


def set_dependencies(img_manager: 'ImageManager'):
    """main.py에서 의존성을 설정하는 함수"""
    global image_manager
    image_manager = img_manager


@router.get("/api/images", tags=["Images"])
async def list_images():
    """이미지 목록 조회"""
    if image_manager is None:
        raise HTTPException(status_code=500, detail="이미지 매니저가 초기화되지 않았습니다.")
    return image_manager.list_images()


@router.get("/refresh", tags=["Images"]) 
async def refresh_images():
    """이미지 목록 새로고침"""
    if image_manager is None:
        raise HTTPException(status_code=500, detail="이미지 매니저가 초기화되지 않았습니다.")
    return image_manager.refresh_images()


@router.get("/image/{filename:path}", tags=["Images"])
async def get_image(filename: str):
    """
    파일 경로로부터 이미지를 가져옵니다.
    상대 경로나 파일명으로 접근 가능합니다.
    """
    try:
        if image_manager is None:
            raise HTTPException(status_code=500, detail="이미지 매니저가 초기화되지 않았습니다.")
        
        # 이미지 경로 찾기
        image_path = image_manager.find_image_path(filename)
        
        if not image_path:
            raise HTTPException(status_code=404, detail=f"이미지를 찾을 수 없습니다: {filename}")
            
        return FileResponse(image_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 로드 오류: {str(e)}")


@router.post("/upload/", tags=["Images"])
async def upload_files(
    files: List[UploadFile] = File(...), 
    project: str = Form(...)
):
    """이미지 파일 업로드"""
    if image_manager is None:
        raise HTTPException(status_code=500, detail="이미지 매니저가 초기화되지 않았습니다.")
    return await image_manager.upload_files(files, project)


@router.delete("/api/delete-image/{filename}", tags=["Images"])
async def delete_image_and_label(filename: str, project_path: str):
    """
    이미지 파일과 해당 라벨 파일을 삭제합니다.
    
    Args:
        filename: 삭제할 이미지 파일명
        project_path: 프로젝트 경로
    """
    try:
        project_dir = Path(project_path)
        
        # 프로젝트 경로 유효성 확인
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="프로젝트 경로를 찾을 수 없습니다.")
        
        # 이미지 파일 경로
        images_dir = project_dir / "images"
        image_path = images_dir / filename
        
        # 라벨 파일 경로 (확장자를 .txt로 변경)
        labels_dir = project_dir / "labels"
        label_filename = Path(filename).stem + ".txt"
        label_path = labels_dir / label_filename
        
        deleted_files = []
        errors = []
        
        # 이미지 파일 삭제
        if image_path.exists():
            try:
                os.remove(image_path)
                deleted_files.append(f"이미지: {filename}")
                logger.info(f"이미지 파일 삭제 성공: {image_path}")
            except Exception as e:
                errors.append(f"이미지 파일 삭제 실패: {str(e)}")
                logger.error(f"이미지 파일 삭제 실패: {image_path}, 오류: {str(e)}")
        else:
            errors.append(f"이미지 파일을 찾을 수 없습니다: {filename}")
        
        # 라벨 파일 삭제
        if label_path.exists():
            try:
                os.remove(label_path)
                deleted_files.append(f"라벨: {label_filename}")
                logger.info(f"라벨 파일 삭제 성공: {label_path}")
            except Exception as e:
                errors.append(f"라벨 파일 삭제 실패: {str(e)}")
                logger.error(f"라벨 파일 삭제 실패: {label_path}, 오류: {str(e)}")
        else:
            # 라벨 파일이 없는 것은 정상적인 상황일 수 있음
            logger.info(f"라벨 파일이 존재하지 않음: {label_path}")
        
        # 결과 처리
        if len(deleted_files) == 0:
            raise HTTPException(status_code=404, detail="삭제할 파일을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": f"파일 삭제 완료: {', '.join(deleted_files)}",
            "deleted_files": deleted_files,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 삭제 오류: {str(e)}") 