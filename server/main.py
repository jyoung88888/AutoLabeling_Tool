# FastAPI 관련 임포트
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

# 표준 라이브러리 임포트
import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# 서드파티 라이브러리 임포트
from PIL import Image

# 로컬 모듈 임포트
from managers import model_utils, image_utils
from managers.pipeline_manager import PipelineManager
from managers.model_factory import ModelFactory
from core.config import (
    API_TAGS_METADATA, get_upload_dir, get_model_dir,
    get_vue_dist_dir
)

# 라우터 임포트
from api.images import router as images_router

# 서비스 임포트
from services.project_service import ProjectService

# 필요한 클래스 가져오기
ModelManager = model_utils.ModelManager
ImageManager = image_utils.ImageManager

# 로거 객체 생성
logger = logging.getLogger(__name__)

# 전역 설정 변수
UPLOAD_DIR = get_upload_dir()
VUE_DIST_DIR = get_vue_dist_dir()
MODEL_DIR = get_model_dir()

def ensure_directories():
    """필요한 디렉토리들을 생성합니다."""
    
    # 현재 환경 변수 상태 로깅
    mode = os.getenv('AUTOLABELING_MODE', 'production')
    data_dir = os.getenv('AUTOLABELING_DATA_DIR')
    upload_dir = os.getenv('AUTOLABELING_UPLOAD_DIR')
    
    logger.info("=== 서버 디렉토리 설정 정보 ===")
    logger.info(f"🔧 모드: {mode}")
    logger.info(f"📂 데이터 디렉토리 환경변수: {data_dir or 'None'}")
    logger.info(f"📂 업로드 디렉토리 환경변수: {upload_dir or 'None'}")
    logger.info(f"📁 최종 업로드 디렉토리: {UPLOAD_DIR}")
    logger.info("=" * 35)
    
    directories = [UPLOAD_DIR]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"디렉토리 생성: {directory}")
        else:
            logger.info(f"디렉토리 확인: {directory}")

# 디렉토리 초기화
ensure_directories()

# 전역 파이프라인 매니저
pipeline_manager = PipelineManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시와 종료 시 실행되는 이벤트 핸들러"""
    # 서버 시작 시 실행되는 코드
    logger.info("서버 시작됨")
    logger.info("메모리 기반 이미지 시스템 사용 중")
    logger.info("🚀 멀티모델 파이프라인 시스템 초기화 완료")

    yield  # 서버 실행 중

    # 서버 종료 시 실행되는 코드
    logger.info("🗑️ 파이프라인 매니저 정리 중...")
    pipeline_manager.clear_all_models()
    logger.info("서버 종료됨")

app = FastAPI(
    title="Iljoo AutoLabeling",
    description="API for Iljoo AutoLabeling",
    version="1.0.0",
    openapi_tags=API_TAGS_METADATA,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 캐시 제어를 위한 커스텀 StaticFiles 클래스
class NoCacheStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        try:
            response = super().file_response(full_path, stat_result, scope, status_code)
            # 개발 환경에서 캐시 비활성화
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            # CORS 헤더 추가
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        except Exception as e:
            logger.error(f"정적 파일 응답 생성 오류: {e}")
            raise

def setup_static_files():
    """정적 파일 서빙을 설정합니다."""
    try:
        # Vue dist 디렉토리와 assets 폴더 존재 확인
        assets_dir = VUE_DIST_DIR / "assets"
        
        logger.info(f"정적 파일 설정 확인 중: VUE_DIST_DIR={VUE_DIST_DIR}")
        logger.debug(f"assets 디렉토리: {assets_dir}, 존재여부: {assets_dir.exists()}")
        
        if VUE_DIST_DIR.exists() and assets_dir.exists():
            # assets 폴더 내 파일 목록 확인
            asset_files = list(assets_dir.glob("*"))
            logger.debug(f"assets 폴더 파일 개수: {len(asset_files)}")
            
            if asset_files:
                # 동적 속성 설정 방식으로 중복 마운트 방지
                if not hasattr(setup_static_files, '_assets_mounted'):
                    app.mount("/assets", NoCacheStaticFiles(directory=str(assets_dir)), name="assets")
                    setup_static_files._assets_mounted = True
                    logger.info(f"Vue assets 디렉토리 마운트 완료: {assets_dir}")
                
                # img 폴더도 마운트 (있는 경우)
                img_dir = VUE_DIST_DIR / "img"
                if img_dir.exists() and not hasattr(setup_static_files, '_img_mounted'):
                    app.mount("/img", NoCacheStaticFiles(directory=str(img_dir)), name="img")
                    setup_static_files._img_mounted = True
                    logger.info(f"Vue img 디렉토리 마운트 완료: {img_dir}")
            else:
                logger.warning(f"assets 폴더가 비어있습니다: {assets_dir}")
        else:
            logger.warning(f"Vue 빌드 파일을 찾을 수 없습니다. VUE_DIST_DIR={VUE_DIST_DIR}, assets 존재={assets_dir.exists()}")
            
    except Exception as e:
        logger.error(f"정적 파일 설정 오류: {e}")
        raise

# 초기 정적 파일 설정
setup_static_files()

app.mount("/static", StaticFiles(directory=str(UPLOAD_DIR), html=True), name="static")

# 매니저 객체 생성
model_manager = ModelManager()
image_manager = ImageManager(UPLOAD_DIR)

# 서비스 객체 생성
project_service = ProjectService(UPLOAD_DIR, image_manager, model_manager)

# 초기화 작업
image_manager.load_existing_images()

# 라우터에 의존성 설정은 images 모듈이 필요한 경우에만 사용
# images.set_dependencies(image_manager)  # 제거: 사용되지 않음

# 라우터 포함 - 이미지 관련 엔드포인트들을 별도 라우터로 분리
app.include_router(images_router, prefix="")

# API 엔드포인트 정의
@app.get("/", tags=["Root"])
async def root():
    """Vue 앱의 index.html 파일을 반환합니다."""
    vue_index = VUE_DIST_DIR / "index.html"
    if vue_index.exists():
        response = FileResponse(str(vue_index))
        # 캐시 비활성화 헤더 추가
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return {"message": "Welcome to the Iljoo AutoLabeling API"}

@app.get("/models/", tags=["Models"])
async def get_models():
    """사용 가능한 모델 목록을 반환합니다."""
    try:
        models = {}
        
        # 모델 디렉토리가 존재하지 않으면 생성
        if not MODEL_DIR.exists():
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        # 각 모델 타입 폴더 확인
        for model_type_dir in MODEL_DIR.iterdir():
            if model_type_dir.is_dir():
                model_type = model_type_dir.name
                model_files = []
                
                # 해당 타입 폴더 내의 모델 파일들 확인
                for model_file in model_type_dir.iterdir():
                    if model_file.is_file() and model_file.suffix.lower() in ['.pt', '.pth', '.onnx', '.engine']:
                        model_files.append(model_file.name)
                
                models[model_type] = model_files
        
        # 기본 yolo 폴더가 없으면 생성
        if 'yolo' not in models:
            yolo_dir = MODEL_DIR / 'yolo'
            yolo_dir.mkdir(exist_ok=True)
            models['yolo'] = []
        
        return {"models": models}
    except Exception as e:
        logger.error(f"모델 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/upload", tags=["Models"])
async def upload_model(
    file: UploadFile = File(...),
    model_type: str = Form(...),
    model_name: str = Form(...)
):
    """로컬에서 모델 파일을 업로드합니다."""
    try:
        # 파일명 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 필요합니다.")
            
        # 파일 확장자 확인
        if not file.filename.endswith(('.pt', '.pth', '.onnx', '.engine')):
            raise HTTPException(status_code=400, detail="지원되지 않는 파일 형식입니다. (.pt, .pth, .onnx, .engine만 지원)")
        
        # 모델 타입 디렉토리 생성
        model_type_dir = MODEL_DIR / model_type
        model_type_dir.mkdir(exist_ok=True)
        
        # 파일 확장자 추출
        file_extension = Path(file.filename).suffix
        
        # 저장할 파일 경로 생성
        save_filename = f"{model_name}{file_extension}"
        save_path = model_type_dir / save_filename
        
        # 파일이 이미 존재하는지 확인
        if save_path.exists():
            raise HTTPException(status_code=409, detail=f"모델 파일이 이미 존재합니다: {model_type}/{save_filename}")
        
        # 파일 저장
        with open(save_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"모델 파일 업로드 완료: {save_path}")
        
        return {
            "success": True,
            "message": f"모델 파일이 성공적으로 업로드되었습니다.",
            "model_type": model_type,
            "model_name": save_filename,
            "file_path": str(save_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 업로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 업로드 실패: {str(e)}")

@app.get("/models/types", tags=["Models"])
async def get_model_types():
    """사용 가능한 모델 타입 목록을 반환합니다."""
    try:
        # 기본 모델 타입들
        default_types = ["yolo"]
        
        # 실제 존재하는 모델 타입 디렉토리들
        existing_types = [d.name for d in MODEL_DIR.iterdir() if d.is_dir()]
        
        # 기본 타입과 기존 타입을 합치고 중복 제거
        all_types = list(set(default_types + existing_types))
        all_types.sort()
        
        return {"model_types": all_types}
        
    except Exception as e:
        logger.error(f"모델 타입 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/load/{model_path:path}", tags=["Models"])
async def load_model(model_path: str):
    """모델을 로드합니다. (로컬 모델 및 Hugging Face 모델 지원)"""
    try:
        logger.info(f"🔄 모델 로드 요청: {model_path}")

        # Hugging Face 모델인지 확인 (grounding_dino/IDEA-Research/... 형태)
        path_parts = model_path.split('/')

        if len(path_parts) >= 2 and path_parts[0] == "grounding_dino":
            # Grounding DINO 모델 (Hugging Face)
            model_id = "/".join(path_parts[1:])  # "IDEA-Research/grounding-dino-tiny"
            logger.info(f"📦 Hugging Face 모델 감지: {model_id}")

            # 파이프라인 매니저를 통해 로드
            result = pipeline_manager.add_model(
                task_name="detection",
                model_name="grounding_dino",
                model_path=model_id
            )

            # 모델 로드 결과에 추가 정보 병합
            if result:
                result["model_type"] = "grounding_dino"
                result["model_id"] = model_id
                result["source"] = "huggingface"
                return result
            else:
                return {
                    "success": True,
                    "message": f"Grounding DINO model loaded successfully",
                    "model_type": "grounding_dino",
                    "model_id": model_id,
                    "source": "huggingface",
                    "supports_text_prompt": True
                }

        # 기존 로컬 모델 파일 로드
        model_full_path = MODEL_DIR / model_path
        if not model_full_path.is_file():
            raise HTTPException(status_code=404, detail="Model file not found")

        result = model_manager.load_model(model_full_path)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 모델 로드 오류: {str(e)}")
        import traceback
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{model_type}", tags=["Models"])
async def get_model_details(model_type: str):
    """모델 타입의 상세 정보를 반환합니다."""
    try:
        # Hugging Face에서 자동 다운로드하는 모델들의 경우 가상 모델 목록 반환
        huggingface_models = {
            "grounding_dino": [
                "IDEA-Research/grounding-dino-tiny",
                "IDEA-Research/grounding-dino-base"
            ],
            "easyocr": [
                "easyocr (auto-download)"
            ]
        }

        # Hugging Face 모델인 경우
        if model_type in huggingface_models:
            logger.info(f"Hugging Face 모델 타입 '{model_type}' - 사용 가능한 모델: {huggingface_models[model_type]}")
            return {
                "details": huggingface_models[model_type],
                "source": "huggingface",
                "auto_download": True
            }

        # 로컬 모델 파일 검색
        model_path = MODEL_DIR / model_type

        if not model_path.exists():
            logger.warning(f"모델 타입 디렉토리가 존재하지 않습니다: {model_path}")
            # 디렉토리가 없으면 생성
            model_path.mkdir(parents=True, exist_ok=True)
            return {"details": [], "source": "local", "auto_download": False}

        if not model_path.is_dir():
            raise HTTPException(status_code=404, detail=f"'{model_type}'는 유효한 모델 타입이 아닙니다.")

        # 모델 파일들 찾기 (지원되는 확장자만)
        details = []
        for file_path in model_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pt', '.pth', '.onnx', '.engine']:
                details.append(file_path.name)

        logger.info(f"모델 타입 '{model_type}'에서 {len(details)}개의 모델 파일 발견: {details}")

        return {
            "details": details,
            "source": "local",
            "auto_download": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 상세 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 상세 정보 조회 오류: {str(e)}")

@app.delete("/models/{model_type}/{model_name}", tags=["Models"])
async def delete_model(model_type: str, model_name: str):
    """업로드된 모델을 삭제합니다."""
    try:
        model_path = MODEL_DIR / model_type / model_name
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="모델 파일을 찾을 수 없습니다.")
        
        # 파일 삭제
        model_path.unlink()
        
        logger.info(f"모델 파일 삭제 완료: {model_path}")
        
        return {
            "success": True,
            "message": f"모델 파일이 성공적으로 삭제되었습니다: {model_type}/{model_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 삭제 실패: {str(e)}")

@app.delete("/api/delete-image/{filename:path}", tags=["Files"])
async def delete_image_and_label(filename: str, project_path: str = Query(...)):
    """이미지 파일과 연관된 라벨 파일을 삭제합니다."""
    try:
        logger.info(f"🗑️ 파일 삭제 요청: filename={filename}, project_path={project_path}")
        
        if not filename:
            raise HTTPException(status_code=400, detail="파일명이 필요합니다.")
        
        if not project_path:
            raise HTTPException(status_code=400, detail="프로젝트 경로가 필요합니다.")
        
        # 프로젝트 경로 검증
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="프로젝트 경로를 찾을 수 없습니다.")
        
        # 이미지 파일 경로
        image_path = project_dir / "images" / filename
        
        # 라벨 파일 경로 (확장자를 .txt로 변경)
        label_filename = Path(filename).stem + ".txt"
        label_path = project_dir / "labels" / label_filename
        
        # 삭제할 파일들 목록
        files_to_delete = []
        deletion_results = []
        
        # 이미지 파일 확인 및 삭제
        if image_path.exists():
            files_to_delete.append(("이미지", image_path))
        
        # 라벨 파일 확인 및 삭제
        if label_path.exists():
            files_to_delete.append(("라벨", label_path))
        
        if not files_to_delete:
            raise HTTPException(status_code=404, detail="삭제할 파일을 찾을 수 없습니다.")
        
        # 파일 삭제 실행
        for file_type, file_path in files_to_delete:
            try:
                file_path.unlink()
                deletion_results.append(f"{file_type} 파일: {file_path.name}")
                logger.info(f"{file_type} 파일 삭제 완료: {file_path}")
            except Exception as e:
                logger.error(f"{file_type} 파일 삭제 실패 ({file_path}): {str(e)}")
                raise HTTPException(status_code=500, detail=f"{file_type} 파일 삭제 실패: {str(e)}")
        
        return {
            "success": True,
            "message": f"파일이 성공적으로 삭제되었습니다: {', '.join(deletion_results)}",
            "deleted_files": deletion_results,
            "image_file": filename,
            "label_file": label_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}")

@app.get("/device-info/", tags=["Models"])
async def get_device_info():
    """디바이스 정보를 반환합니다."""
    return model_manager.get_device_info()

@app.get("/model/training-info/{model_path:path}", tags=["Models"])
async def get_model_training_info(model_path: str):
    """YOLO 모델의 학습 정보를 반환합니다."""
    try:
        logger.info(f"🔍 모델 학습 정보 요청: {model_path}")
        
        # 모델 경로 검증
        if not model_path:
            raise HTTPException(status_code=400, detail="모델 경로가 필요합니다.")
            
        # 절대 경로로 변환
        full_model_path = Path(model_path)
        
        # 상대 경로인 경우 MODEL_DIR 기준으로 처리
        if not full_model_path.is_absolute():
            full_model_path = MODEL_DIR / model_path
            
        if not full_model_path.exists():
            raise HTTPException(status_code=404, detail=f"모델 파일을 찾을 수 없습니다: {model_path}")
            
        # 파일 확장자 검증
        if not full_model_path.suffix.lower() in ['.pt', '.pth']:
            raise HTTPException(status_code=400, detail="YOLO 모델 파일(.pt, .pth)만 지원됩니다.")
            
        # 모델 학습 정보 추출
        training_info = model_manager.get_model_training_info(full_model_path)
        
        return {
            "success": True,
            "model_path": str(full_model_path),
            "training_info": training_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 모델 학습 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 학습 정보 조회 오류: {str(e)}")

@app.get("/model/classes", tags=["Models"])
async def get_model_classes():
    """현재 로드된 모델의 클래스 정보를 반환합니다."""
    try:
        return model_manager.get_model_classes()
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(f"모델 클래스 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"모델 클래스 정보 조회 오류: {str(e)}")

@app.get("/model/classes-with-ids", tags=["Models"])
async def get_model_classes_with_ids():
    """현재 로드된 모델의 클래스 정보를 ID와 함께 반환합니다 (사이드바용)."""
    try:
        logger.info("🔍 모델 클래스 정보 (ID 포함) 요청 받음")
        
        # project_service의 _get_current_model_classes 함수 사용
        classes_with_ids = project_service._get_current_model_classes()
        
        if not classes_with_ids:
            logger.error("❌ 클래스 정보를 가져오지 못했습니다")
            raise HTTPException(status_code=400, detail="모델이 로드되지 않았거나 클래스 정보를 찾을 수 없습니다. 먼저 YOLO 모델을 로드해주세요.")
        
        logger.info(f"✅ 클래스 정보 반환 성공: {len(classes_with_ids)}개 클래스")
        
        return {
            "success": True,
            "classes": classes_with_ids,
            "total": len(classes_with_ids),
            "message": f"총 {len(classes_with_ids)}개의 클래스가 로드되었습니다 (YOLO ID 순서)"
        }
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(f"❌ 모델 클래스 정보 (ID 포함) 조회 오류: {str(e)}")
        import traceback
        logger.error(f"🔍 오류 상세: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"모델 클래스 정보 조회 오류: {str(e)}")

@app.post("/model/predict/{filename:path}", tags=["Models"])
async def predict_image(filename: str, data: Dict[str, Any] = {}):
    """업로드된 이미지에 대한 예측을 수행합니다."""
    try:
                # 이미지 경로 찾기
        image_path = image_manager.find_image_path(filename)
        if not image_path:
            raise HTTPException(status_code=404, detail=f"이미지 파일을 찾을 수 없습니다: {filename}")
        
        # 선택된 클래스 목록
        selected_classes = data.get("selected_classes", [])
        
        # 이미지 예측 수행
        boxes = model_manager.predict_image(image_path, selected_classes)
        
        return {
            "success": True,
            "filename": os.path.basename(filename),
            "boxes": boxes,
            "total_objects": len(boxes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이미지 예측 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 예측 중 오류가 발생했습니다: {str(e)}")

@app.post("/labeling/process", tags=["Labeling"])
async def process_labeling(
    file: UploadFile = File(...),
    classes: str = Form(...),
    confidence_threshold: float = Form(0.5),
    text_prompt: str = Form(None),
    box_threshold: float = Form(0.3),
    text_threshold: float = Form(0.25)
):
    """자동 라벨링을 위한 이미지 처리 엔드포인트 (YOLO 및 Grounding DINO 지원)"""
    import time

    start_time = time.time()

    try:
        if text_prompt:
            logger.info(f"자동 라벨링 요청 시작 (Grounding DINO) - 파일: {file.filename}, 프롬프트: {text_prompt}, box_threshold: {box_threshold}, text_threshold: {text_threshold}")
        else:
            logger.info(f"자동 라벨링 요청 시작 (YOLO) - 파일: {file.filename}, 신뢰도: {confidence_threshold}")
        
        # 파일 검증
        if not file.content_type or not file.content_type.startswith('image/'):
            logger.error(f"잘못된 파일 형식: {file.content_type}")
            raise HTTPException(status_code=400, detail="이미지 파일만 허용됩니다.")
        
        # 신뢰도 임계값 검증
        if not (0.0 <= confidence_threshold <= 1.0):
            logger.error(f"잘못된 신뢰도 임계값: {confidence_threshold}")
            raise HTTPException(status_code=400, detail="신뢰도 임계값은 0.0과 1.0 사이여야 합니다.")
        
        # 파일 내용 읽기
        try:
            contents = await file.read()
            logger.info(f"파일 읽기 완료 - 크기: {len(contents)} bytes")
        except Exception as e:
            logger.error(f"파일 읽기 실패: {str(e)}")
            raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {str(e)}")
        
        # 선택된 클래스 정보 파싱
        try:
            selected_classes = json.loads(classes)
            logger.info(f"클래스 정보 파싱 완료: {selected_classes}")
            # 자동 라벨링에서는 빈 클래스 배열이면 모든 클래스를 포함하도록 처리
            if not selected_classes or len(selected_classes) == 0:
                selected_classes = None  # None으로 설정하여 모든 클래스 포함
                logger.info("빈 클래스 배열 - 모든 클래스 포함으로 설정")
                
        except json.JSONDecodeError as e:
            logger.error(f"클래스 정보 파싱 실패: {str(e)}, 원본 데이터: {classes}")
            selected_classes = None  # 파싱 실패 시 모든 클래스 포함
        
        # 메모리에서 직접 처리 (임시 파일 저장 제거)
        try:
            # 메모리에 이미지 저장 (자동 라벨링 중에만 사용)
            image_manager.add_memory_image(file.filename, contents, {
                "project": "auto_labeling",
                "size": len(contents)
            })
            logger.info(f"메모리에 이미지 저장 완료: {file.filename}")
            
            # 원본 이미지 크기 정보 추출 (리사이즈 전)
            import cv2
            import numpy as np
            
            # BytesIO에서 원본 이미지 크기 추출
            try:
                image_bytes = np.frombuffer(contents, dtype=np.uint8)
                cv_image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
                if cv_image is None:
                    logger.error("이미지 디코딩 실패 - cv2.imdecode 반환값이 None")
                    raise HTTPException(status_code=400, detail="이미지 디코딩에 실패했습니다.")
                original_height, original_width = cv_image.shape[:2]
                logger.info(f"원본 이미지 크기: {original_width}x{original_height}")
            except Exception as e:
                logger.error(f"이미지 크기 추출 실패: {str(e)}")
                raise HTTPException(status_code=400, detail=f"이미지 크기 추출 실패: {str(e)}")
            
            # 낮은 해상도 체크 (model_utils와 동일한 기준 사용)
            min_dimension = min(original_width, original_height)
            very_low_res = min_dimension < 300
            low_res = min_dimension < 640
            
            # 모델 예측 수행 (BytesIO 사용) - 자동 리사이즈 포함
            try:
                from io import BytesIO
                image_stream = BytesIO(contents)
                
                # Grounding DINO 텍스트 프롬프트 지원
                if text_prompt:
                    logger.info(f"모델 예측 시작 (Grounding DINO) - 프롬프트: {text_prompt}, box_threshold: {box_threshold}, text_threshold: {text_threshold}")

                    # PIL 이미지로 변환 (Image는 파일 상단에서 이미 import됨)
                    image_stream.seek(0)
                    pil_image = Image.open(image_stream)

                    # pipeline_manager를 통해 Grounding DINO 추론
                    result = pipeline_manager.run_single_task(
                        task_name="detection",
                        image=pil_image,
                        text_prompt=text_prompt,
                        box_threshold=box_threshold,
                        text_threshold=text_threshold
                    )

                    # 결과에서 boxes 추출
                    boxes = result.get("boxes", [])
                else:
                    logger.info(f"모델 예측 시작 (YOLO) - 선택된 클래스: {selected_classes}, 신뢰도: {confidence_threshold}")
                    # YOLO용 기본 호출
                    boxes = model_manager.predict_image(image_stream, selected_classes, confidence_threshold)

                logger.info(f"모델 예측 완료 - 감지된 객체 수: {len(boxes)}")
            except Exception as e:
                logger.error(f"모델 예측 실패: {str(e)}")
                raise HTTPException(status_code=500, detail=f"모델 예측 실패: {str(e)}")
            
            # 이미지를 base64로 인코딩하여 반환 (원본 이미지 사용)
            try:
                import base64
                image = Image.open(BytesIO(contents))
                buffer = BytesIO()
                
                # RGBA 모드인 경우 RGB로 변환하여 JPEG 호환성 보장
                if image.mode == 'RGBA':
                    # 흰색 배경으로 RGBA를 RGB로 변환
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[-1])  # 알파 채널을 마스크로 사용
                    image = rgb_image
                elif image.mode == 'LA':
                    # 회색조 + 알파 채널인 경우 RGB로 변환
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    gray_image = image.convert('L')  # 회색조로 변환
                    rgb_image.paste(gray_image)
                    image = rgb_image
                elif image.mode not in ['RGB', 'L']:
                    # 기타 모드인 경우 RGB로 변환
                    image = image.convert('RGB')
                
                image.save(buffer, format="JPEG")
                buffer.seek(0)
                image_data = base64.b64encode(buffer.getvalue()).decode()
                logger.info("이미지 base64 인코딩 완료")
            except Exception as e:
                logger.error(f"이미지 인코딩 실패: {str(e)}")
                raise HTTPException(status_code=500, detail=f"이미지 인코딩 실패: {str(e)}")
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "filename": file.filename,
                "boxes": boxes,
                "imageData": f"data:image/jpeg;base64,{image_data}",
                "width": original_width,
                "height": original_height,
                "confidence": "high",
                "processing_time": round(processing_time, 3),
                "was_resized": low_res,
                "very_low_resolution": very_low_res,
                "original_resolution": f"{original_width}x{original_height}",
                "resize_applied": low_res,
                "resize_method": "letterbox" if very_low_res else "standard" if low_res else "none"
            }
            
            logger.info(f"자동 라벨링 처리 완료 - 처리 시간: {processing_time:.3f}초, 객체 수: {len(boxes)}")
            
            return result
            
        finally:
            # 자동 라벨링용 임시 이미지는 즉시 제거 (저장하지 않는 경우)
            # 실제 업로드된 이미지와 구분하기 위해 조건부 제거
            pass  # 나중에 프로젝트 저장 시 제거하거나 세션 종료 시 정리
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동 라벨링 처리 중 예상치 못한 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"자동 라벨링 처리 중 오류가 발생했습니다: {str(e)}")

@app.post("/labeling/batch-process", tags=["Labeling"])
async def batch_process_labeling(data: Dict[str, Any]):
    """
    배치 자동 라벨링 엔드포인트 (여러 이미지 동시 처리)

    Args:
        data: {
            "filenames": List[str],  # 업로드된 이미지 파일명 리스트
            "text_prompt": str,      # Grounding DINO 텍스트 프롬프트
            "box_threshold": float,  # 박스 임계값 (기본값: 0.3)
            "text_threshold": float, # 텍스트 임계값 (기본값: 0.25)
            "batch_size": int        # 배치 크기 (기본값: 4)
        }

    Returns:
        List[Dict]: 각 이미지별 탐지 결과
    """
    import time
    start_time = time.time()

    try:
        # 파라미터 추출
        filenames = data.get("filenames", [])
        text_prompt = data.get("text_prompt")
        box_threshold = data.get("box_threshold", 0.3)
        text_threshold = data.get("text_threshold", 0.25)
        batch_size = data.get("batch_size", 4)

        # 유효성 검증
        if not filenames or not isinstance(filenames, list):
            raise HTTPException(status_code=400, detail="filenames 리스트가 필요합니다")

        if not text_prompt:
            raise HTTPException(status_code=400, detail="text_prompt가 필요합니다")

        logger.info(f"🔍 배치 자동 라벨링 시작")
        logger.info(f"  - 이미지 수: {len(filenames)}개")
        logger.info(f"  - 배치 크기: {batch_size}")
        logger.info(f"  - 프롬프트: {text_prompt}")
        logger.info(f"  - Box threshold: {box_threshold}")
        logger.info(f"  - Text threshold: {text_threshold}")

        # 이미지 로드
        images = []
        image_infos = []

        for filename in filenames:
            try:
                # 이미지 경로 찾기
                image_path = image_manager.find_image_path(filename)
                if not image_path:
                    logger.warning(f"이미지를 찾을 수 없음: {filename}")
                    continue

                # PIL 이미지 로드
                pil_image = Image.open(image_path)
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')

                images.append(pil_image)
                image_infos.append({
                    "filename": filename,
                    "size": pil_image.size  # (width, height)
                })

            except Exception as e:
                logger.error(f"이미지 로드 실패 ({filename}): {str(e)}")
                continue

        if len(images) == 0:
            raise HTTPException(status_code=404, detail="유효한 이미지를 찾을 수 없습니다")

        logger.info(f"📥 {len(images)}개 이미지 로드 완료")

        # 배치 추론 수행
        try:
            results = pipeline_manager.run_batch_task(
                task_name="detection",
                images=images,
                text_prompt=text_prompt,
                box_threshold=box_threshold,
                text_threshold=text_threshold,
                batch_size=batch_size
            )
        except Exception as e:
            logger.error(f"배치 추론 실패: {str(e)}")
            raise HTTPException(status_code=500, detail=f"배치 추론 실패: {str(e)}")

        # 결과 정리
        processed_results = []
        for idx, result in enumerate(results):
            info = image_infos[idx]
            processed_results.append({
                "success": True,
                "filename": info["filename"],
                "boxes": result.get("boxes", []),
                "num_detections": result.get("num_detections", 0),
                "width": info["size"][0],
                "height": info["size"][1]
            })

        processing_time = time.time() - start_time

        logger.info(f"✅ 배치 자동 라벨링 완료 - 처리 시간: {processing_time:.3f}초, 이미지: {len(processed_results)}개")

        return {
            "success": True,
            "results": processed_results,
            "total_images": len(processed_results),
            "processing_time": round(processing_time, 3)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 자동 라벨링 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"배치 자동 라벨링 실패: {str(e)}")

@app.get("/files/{filename:path}", tags=["Files"])
async def get_file(filename: str):
    """파일 서빙을 위한 엔드포인트 - 기존 이미지 매니저와 통합"""
    try:
        # 빈 파일명 체크
        if not filename or filename.strip() == "":
            raise HTTPException(status_code=400, detail="파일명이 필요합니다.")
        
        # 이미지 매니저의 find_image_path를 사용하여 파일 찾기
        image_path = image_manager.find_image_path(filename)
        
        # 메모리 이미지인 경우
        if image_path and str(image_path).startswith("memory://"):
            memory_filename = str(image_path).replace("memory://", "")
            memory_data = image_manager.get_memory_image(memory_filename)
            
            if memory_data:
                # 이미지 타입 결정
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    media_type = "image/jpeg"
                elif filename.lower().endswith('.png'):
                    media_type = "image/png"
                else:
                    media_type = "application/octet-stream"
                
                return Response(
                    content=memory_data,
                    media_type=media_type,
                    headers={"Content-Disposition": f"inline; filename={filename}"}
                )
            else:
                image_path = None
        
        elif not image_path:
            # 기본 경로에서도 확인
            file_path = UPLOAD_DIR / filename
            
            # 파일 존재 여부 확인
            if file_path.exists() and file_path.is_file():
                image_path = file_path
        
        if not image_path:
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
            
        return FileResponse(
            path=str(image_path),
            filename=Path(image_path).name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FILES] 파일 서빙 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 서빙 오류: {str(e)}")

@app.post("/api/project/save-local", tags=["Projects"])
async def save_project_local(data: Dict[str, Any]):
    """프로젝트를 로컬에 저장합니다."""
    try:
        return project_service.save_project(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로젝트 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 저장 중 오류가 발생했습니다: {str(e)}")

@app.post("/api/save-class-file", tags=["Projects"])
async def save_class_file(data: Dict[str, Any]):
    """클래스 파일을 저장합니다."""
    try:
        return project_service.save_class_file(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"클래스 파일 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"클래스 파일 저장 중 오류가 발생했습니다: {str(e)}")

@app.post("/api/save-label-file", tags=["Projects"])
async def save_label_file(data: Dict[str, Any]):
    """개별 라벨 파일을 저장합니다."""
    try:
        return project_service.save_label_file(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라벨 파일 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"라벨 파일 저장 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/list-projects", tags=["Projects"])
async def list_projects():
    """사용 가능한 프로젝트 목록을 반환합니다."""
    try:
        projects = []
        
        # UPLOAD_DIR이 존재하지 않으면 빈 목록 반환
        if not UPLOAD_DIR.exists():
            return {"success": True, "projects": []}
        
        # 1. 날짜 형식 폴더 내의 프로젝트 검색 (우선순위) - 2025-06-10/project_name 형태
        for date_dir in UPLOAD_DIR.iterdir():
            if date_dir.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', date_dir.name):
                for proj_dir in date_dir.iterdir():
                    if proj_dir.is_dir():
                        project_info = validate_and_extract_project_info(proj_dir, date_prefix=date_dir.name)
                        if project_info:
                            projects.append(project_info)
        
        # 2. 루트 디렉토리의 프로젝트 폴더 검색 (레거시 지원) - 날짜 형식 폴더 제외
        for folder in UPLOAD_DIR.iterdir():
            if folder.is_dir() and not re.match(r'^\d{4}-\d{2}-\d{2}$', folder.name):
                project_info = validate_and_extract_project_info(folder)
                if project_info:
                    projects.append(project_info)
        
        # 프로젝트를 생성 시간 기준으로 내림차순 정렬 (최신 먼저)
        projects.sort(key=lambda x: x.get('createdTime', 0), reverse=True)
        
        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
        
    except Exception as e:
        logger.error(f"프로젝트 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 목록 조회 중 오류가 발생했습니다: {str(e)}")

def validate_and_extract_project_info(project_dir: Path, date_prefix: str = "") -> Optional[Dict[str, Any]]:
    """프로젝트 디렉토리가 유효한지 확인하고 프로젝트 정보를 추출합니다."""
    try:
        # 유효한 프로젝트 구조인지 확인 (images, labels 폴더 존재)
        images_dir = project_dir / "images"
        labels_dir = project_dir / "labels"
        
        if not (images_dir.exists() and labels_dir.exists()):
            return None
        
        # info.json 파일 검색
        info_files = list(project_dir.glob("*_info.json"))
        if not info_files:
            # 일반적인 info.json 파일도 확인
            info_json = project_dir / "info.json"
            if info_json.exists():
                info_files = [info_json]
        
        if not info_files:
            return None
        
        # 프로젝트 이름 결정
        project_name = project_dir.name
        display_name = project_name
        if date_prefix:
            project_name = f"{date_prefix}/{project_name}"
            display_name = f"{project_name} ({date_prefix})"
        
        # 이미지와 라벨 파일 개수 계산
        image_count = len([f for f in images_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']])
        label_count = len([f for f in labels_dir.iterdir() if f.is_file() and f.suffix.lower() == '.txt'])
        
        # 생성 시간 확인 (info.json 파일의 수정 시간 사용)
        created_time = info_files[0].stat().st_mtime
        
        # info.json에서 추가 정보 추출 (선택사항)
        additional_info = {}
        try:
            with open(info_files[0], 'r', encoding='utf-8') as f:
                info_data = json.load(f)
                
                # class_info 우선, 없으면 classes 키 사용 (하위 호환성)
                classes_info = []
                if "class_info" in info_data and info_data["class_info"]:
                    # 새로운 class_info 형태: [{"id": 0, "name": "person"}, ...]
                    class_info = info_data["class_info"]
                    if isinstance(class_info, list):
                        classes_info = [cls.get("name", f"class_{cls.get('id', 0)}") for cls in class_info if isinstance(cls, dict)]
                elif "classes" in info_data:
                    # 기존 classes 키 사용 (하위 호환성)
                    classes_info = info_data.get('classes', [])
                
                additional_info = {
                    'classes': classes_info,
                    'description': info_data.get('description', ''),
                    'version': info_data.get('version', '1.0')
                }
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"info.json 파일 읽기 실패 ({project_dir}): {e}")
        
        project_info = {
            "name": project_name,  # API에서 사용할 전체 경로
            "displayName": display_name,  # UI에서 표시할 이름
            "path": str(project_dir),
            "dateFolder": date_prefix if date_prefix else None,
            "projectFolder": project_dir.name,
            "imageCount": image_count,
            "labelCount": label_count,
            "createdTime": created_time,
            **additional_info
        }
        
        return project_info
        
    except Exception as e:
        logger.warning(f"프로젝트 정보 추출 실패 ({project_dir}): {e}")
        return None

@app.post("/api/load-project", tags=["Projects"])
async def load_project(data: Dict[str, Any]):
    """지정된 프로젝트를 불러옵니다."""
    try:
        project_name = data.get("projectName")
        if not project_name:
            raise HTTPException(status_code=400, detail="프로젝트 이름이 제공되지 않았습니다.")
        
        # 프로젝트 경로 구성
        project_path = UPLOAD_DIR / project_name
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_name}")
        
        # 프로젝트 구조 검증
        images_dir = project_path / "images"
        labels_dir = project_path / "labels"
        
        if not images_dir.exists():
            raise HTTPException(status_code=404, detail="이미지 폴더를 찾을 수 없습니다.")
        
        if not labels_dir.exists():
            raise HTTPException(status_code=404, detail="라벨 폴더를 찾을 수 없습니다.")
        
        # info.json 파일 찾기
        info_files = list(project_path.glob("*_info.json"))
        if not info_files:
            info_json = project_path / "info.json"
            if info_json.exists():
                info_files = [info_json]
        
        if not info_files:
            raise HTTPException(status_code=404, detail="프로젝트 정보 파일(info.json)을 찾을 수 없습니다.")
        
        # 프로젝트 정보 로드
        project_info = {}
        try:
            with open(info_files[0], 'r', encoding='utf-8') as f:
                project_info = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"프로젝트 정보 파일 파싱 오류: {e}")
            raise HTTPException(status_code=400, detail="프로젝트 정보 파일 형식이 올바르지 않습니다.")
        
        # 클래스 정보 처리: class_info를 우선적으로 사용
        logger.info("=== 프로젝트 로드: 클래스 정보 처리 시작 ===")
        
        processed_classes = []
        
        # 1. 먼저 project_info에서 class_info 확인
        if "class_info" in project_info and project_info["class_info"]:
            class_info = project_info["class_info"]
            logger.info(f"✅ 프로젝트 파일에서 class_info 발견: {class_info}")
            
            if isinstance(class_info, list) and len(class_info) > 0:
                # class_info가 [{"id": 0, "name": "person"}, {"id": 1, "name": "helmet"}, ...] 형태인 경우
                try:
                    # ID 순서대로 정렬하여 클래스명 추출
                    sorted_class_info = sorted(class_info, key=lambda x: x.get("id", 0))
                    processed_classes = [cls.get("name", f"class_{cls.get('id', 0)}") for cls in sorted_class_info]
                    
                    logger.info("✅ 프로젝트 저장 시 class_info 사용:")
                    for cls_info in sorted_class_info:
                        logger.info(f"  ID {cls_info.get('id')}: '{cls_info.get('name')}'")
                    
                    logger.info(f"🎯 프로젝트 로드에 사용할 클래스 정보 (class_info): {processed_classes}")
                    
                except Exception as e:
                    logger.error(f"❌ class_info 파싱 오류: {str(e)}")
                    processed_classes = []
            else:
                logger.warning("⚠️ class_info가 리스트가 아니거나 비어있음")
        
        # 2. class_info가 없거나 유효하지 않은 경우 현재 모델에서 동적으로 가져오기
        if not processed_classes:
            logger.info("📡 class_info가 없거나 유효하지 않음 - 현재 모델에서 클래스 정보 동적 로드")
            
            try:
                # 현재 로드된 모델에서 클래스 정보 가져오기
                model_classes_response = model_manager.get_model_classes()
                
                if model_classes_response and "classes" in model_classes_response:
                    model_classes_dict = model_classes_response["classes"]
                    logger.info(f"모델에서 가져온 클래스 딕셔너리: {model_classes_dict}")
                    
                    # 딕셔너리를 ID 순서대로 정렬하여 리스트로 변환
                    if isinstance(model_classes_dict, dict):
                        # ID 순서대로 정렬: {0: 'person', 1: 'helmet', ...} -> ['person', 'helmet', ...]
                        processed_classes = [model_classes_dict[str(i)] for i in sorted([int(k) for k in model_classes_dict.keys()])]
                        logger.info(f"현재 모델의 클래스 정보 (ID 순서): {processed_classes}")
                    else:
                        logger.error("모델 클래스 정보가 딕셔너리 형태가 아닙니다.")
                        raise HTTPException(status_code=400, detail="현재 로드된 모델의 클래스 정보를 가져올 수 없습니다.")
                else:
                    logger.error("모델에서 클래스 정보를 가져오지 못했습니다.")
                    raise HTTPException(status_code=400, detail="모델이 로드되지 않았거나 클래스 정보를 가져올 수 없습니다. 먼저 모델을 로드해주세요.")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"모델 클래스 정보 가져오기 실패: {str(e)}")
                raise HTTPException(status_code=500, detail="현재 로드된 모델에서 클래스 정보를 가져오는 중 오류가 발생했습니다.")
        
        logger.info(f"🎯 최종 프로젝트 로드에 사용할 클래스 정보: {processed_classes}")
        project_info["processed_classes"] = processed_classes
        
        # class_info도 응답에 포함 (프론트엔드에서 사용할 수 있도록)
        if "class_info" in project_info and project_info["class_info"]:
            logger.info("✅ 프로젝트 응답에 class_info 포함")
        else:
            logger.info("📡 프로젝트 응답에 class_info가 없어서 processed_classes 기반으로 생성")
            # processed_classes를 class_info 형태로 변환
            class_info_for_response = []
            for index, class_name in enumerate(processed_classes):
                class_info_for_response.append({
                    "id": index,
                    "name": class_name
                })
            project_info["class_info"] = class_info_for_response
        
        # 이미지 파일 목록 수집
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
        image_files = []
        
        for img_file in images_dir.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                image_files.append(img_file)
        
        # 이미지 파일 정렬
        image_files.sort(key=lambda x: x.name)
        
        # 각 이미지에 대한 결과 데이터 구성
        results = []
        
        for img_file in image_files:
            try:
                
                # 해당 이미지의 라벨 파일 찾기
                label_file = labels_dir / f"{img_file.stem}.txt"
                
                # 이미지 메타데이터 수집
                image_info = {
                    "filename": img_file.name,
                    "image_path": f"images/{img_file.name}",
                    "boxes": []
                }
                
                # 이미지 크기 정보 가져오기
                try:
                    with Image.open(img_file) as pil_img:
                        image_info["width"], image_info["height"] = pil_img.size
                except Exception as e:
                    logger.warning(f"이미지 크기 정보 추출 실패 ({img_file.name}): {e}")
                    image_info["width"] = 640  # 기본값
                    image_info["height"] = 640
                
                # 라벨 파일이 존재하면 바운딩 박스 정보 로드
                if label_file.exists():
                    try:
                        # 변환된 클래스 정보 사용
                        boxes = parse_yolo_label_file(label_file, image_info["width"], image_info["height"], processed_classes)
                        image_info["boxes"] = boxes
                    except Exception as e:
                        logger.warning(f"라벨 파일 파싱 실패 ({label_file.name}): {e}")
                
                results.append(image_info)
                
            except Exception as e:
                logger.error(f"이미지 처리 오류 ({img_file.name}): {e}")
                continue
        
        return {
            "success": True,
            "projectName": project_name,
            "projectPath": str(project_path),
            "results": results,
            "classes": processed_classes,  # 변환된 클래스 정보 사용
            "totalImages": len(results),
            "lowConfidenceImages": project_info.get("lowConfidenceImages", []),
            "projectInfo": project_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"프로젝트 로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 로드 중 오류가 발생했습니다: {str(e)}")

def parse_yolo_label_file(label_file: Path, img_width: int, img_height: int, classes: List[str]) -> List[Dict[str, Any]]:
    """
    YOLO 형식의 라벨 파일을 파싱하여 바운딩 박스 정보를 반환합니다.
    프로젝트 저장 시 class_info로 저장된 클래스 정보를 우선 사용하고,
    없을 경우 현재 로드된 모델의 클래스 정보를 사용합니다.
    """
    boxes = []
    
    try:
        with open(label_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 5:
                logger.warning(f"라벨 파일 {label_file.name} 라인 {line_num}: 형식이 올바르지 않음")
                continue
            
            try:
                class_id = int(parts[0])
                x_center_norm = float(parts[1])
                y_center_norm = float(parts[2])
                width_norm = float(parts[3])
                height_norm = float(parts[4])
                
                # 정규화된 좌표를 픽셀 좌표로 변환
                x_center = x_center_norm * img_width
                y_center = y_center_norm * img_height
                box_width = width_norm * img_width
                box_height = height_norm * img_height
                
                # 좌상단 좌표 계산
                x = x_center - box_width / 2
                y = y_center - box_height / 2
                
                # 현재 모델의 클래스 정보를 사용하여 클래스 이름 결정
                class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"
                
                box_info = {
                    "bbox": [x, y, box_width, box_height],
                    "class_name": class_name,
                    # 프로젝트 로드 시에는 신뢰도를 표시하지 않음 (confidence 필드 제거)
                    "normalized_coords": [x_center_norm, y_center_norm, width_norm, height_norm]
                }
                
                boxes.append(box_info)
                
            except (ValueError, IndexError) as e:
                logger.warning(f"라벨 파일 {label_file.name} 라인 {line_num} 파싱 오류: {e}")
                continue
    
    except Exception as e:
        logger.error(f"라벨 파일 읽기 오류 ({label_file}): {e}")
        raise
    
    return boxes

@app.get("/project/classes", tags=["Projects"])
async def get_project_classes(project: Optional[str] = None):
    """프로젝트의 클래스 정보를 반환합니다."""
    try:
        # 사용할 프로젝트 결정 (파라미터 또는 자동 검색)
        target_project = project
        
        # 특정 프로젝트 파라미터가 제공되지 않은 경우 자동으로 프로젝트 찾기
        if not target_project:
            logger.info("프로젝트 파라미터가 제공되지 않았습니다. 사용 가능한 프로젝트를 검색합니다.")
            
            # 모든 프로젝트 폴더 검색
            available_projects = []
            
            # 1. 루트 디렉토리의 프로젝트 폴더 검색
            for folder in UPLOAD_DIR.iterdir():
                if folder.is_dir():
                    # 유효한 프로젝트 구조인지 확인 (images, labels 폴더와 *_info.json 파일 존재)
                    if (folder / "images").exists() and (folder / "labels").exists():
                        # info.json 파일 검색
                        info_files = list(folder.glob("*_info.json"))
                        if info_files:
                            available_projects.append(folder.name)
                            logger.info(f"사용 가능한 프로젝트 발견: {folder.name}")
            
            # 2. 날짜 형식 폴더 내의 프로젝트 검색
            for date_dir in UPLOAD_DIR.iterdir():
                if date_dir.is_dir() and date_dir.name.startswith('20'):  # 2023-01-01 형식
                    for proj_dir in date_dir.iterdir():
                        if proj_dir.is_dir():
                            # 유효한 프로젝트 구조인지 확인
                            if (proj_dir / "images").exists() and (proj_dir / "labels").exists():
                                # info.json 파일 검색
                                info_files = list(proj_dir.glob("*_info.json"))
                                if info_files:
                                    available_projects.append(f"{date_dir.name}/{proj_dir.name}")
                                    logger.info(f"사용 가능한 프로젝트 발견: {date_dir.name}/{proj_dir.name}")
            
            # 사용 가능한 프로젝트가 없으면 오류 반환
            if not available_projects:
                logger.error("사용 가능한 프로젝트를 찾을 수 없습니다.")
                raise HTTPException(status_code=404, detail="사용 가능한 프로젝트를 찾을 수 없습니다.")
            
            # 첫 번째 프로젝트 선택
            target_project = available_projects[0]
            logger.info(f"자동으로 프로젝트 선택됨: {target_project}")
        
        # 프로젝트 경로 정규화
        project_path = UPLOAD_DIR / target_project
        
        # 프로젝트 경로 존재 여부 확인
        if not project_path.is_dir():
            logger.error(f"지정된 프로젝트 경로를 찾을 수 없습니다: {project_path}")
            raise HTTPException(status_code=404, detail=f"프로젝트 경로를 찾을 수 없습니다: {target_project}")
        
        # 프로젝트 이름 추출 (경로의 마지막 부분)
        project_name = os.path.basename(target_project.rstrip('/'))
        
        # 프로젝트 폴더 내에서 info.json 파일 검색
        info_files = []
        info_file_pattern = re.compile(f"{project_name}_info.json$")
        
        for file in os.listdir(project_path):
            if info_file_pattern.match(file) or file == 'info.json':
                info_file_path = project_path / file
                if info_file_path.is_file():
                    info_files.append(info_file_path)
        
        # info.json 파일이 없으면 오류 반환
        if not info_files:
            logger.error("info.json 파일을 찾을 수 없습니다.")
            raise HTTPException(status_code=404, detail=f"프로젝트 {target_project}에서 info.json 파일을 찾을 수 없습니다.")
        
        # 첫 번째 info.json 파일 로드
        try:
            with open(info_files[0], 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # 클래스 정보 추출
            classes = []
            
            if "classes" in content and content["classes"]:
                if isinstance(content["classes"], list):
                    # 새 형식: [{"id": 0, "name": "person"}, ...] 또는 기존 형식: ["person", ...]
                    for cls in content["classes"]:
                        if isinstance(cls, dict) and "name" in cls:
                            # 새 형식: {"id": 0, "name": "person"}
                            classes.append(cls["name"])
                        elif isinstance(cls, str):
                            # 기존 형식: "person"
                            classes.append(cls)
                elif isinstance(content["classes"], dict):
                    # 클래스 사전 형식 (ID: 이름)
                    classes = list(content["classes"].values())
            
            if not classes:
                logger.error("info.json 파일에서 클래스 정보를 찾을 수 없습니다.")
                raise HTTPException(status_code=404, detail="클래스 정보가 없습니다.")
            
            logger.info(f"프로젝트 파일에서 클래스 정보 로드 성공: {classes}")
            return {"classes": classes}
            
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON 파싱 오류: {str(json_err)}")
            raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {str(json_err)}")
        except Exception as load_err:
            logger.error(f"info.json 파일 로드 중 오류: {str(load_err)}")
            raise HTTPException(status_code=500, detail=f"정보 파일 로드 오류: {str(load_err)}")
                
    except HTTPException as http_e:
        # 기존 HTTPException은 그대로 전달
        raise http_e
    except Exception as e:
        logger.error(f"프로젝트 클래스 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 클래스 정보 조회 오류: {str(e)}")

@app.post("/api/read-label-file", tags=["Projects"])
async def read_label_file(data: Dict[str, Any]):
    """저장된 라벨 파일을 읽어옵니다."""
    try:
        label_file_path = data.get('labelFilePath', '')
        if not label_file_path:
            raise HTTPException(status_code=400, detail="라벨 파일 경로가 필요합니다.")
        
        # 경로 보안 검증
        full_path = Path(label_file_path)
        
        # 프로젝트 경로에서 파일 존재 확인
        if not full_path.exists():
            return {"success": False, "message": "라벨 파일을 찾을 수 없습니다.", "content": ""}
        
        # 파일 읽기
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True, 
                "content": content,
                "message": f"라벨 파일을 성공적으로 읽었습니다: {full_path.name}"
            }
        except Exception as read_error:
            logger.error(f"라벨 파일 읽기 오류: {read_error}")
            return {"success": False, "message": f"라벨 파일 읽기 실패: {str(read_error)}", "content": ""}
            
    except Exception as e:
        logger.error(f"라벨 파일 읽기 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"라벨 파일 읽기 중 오류가 발생했습니다: {str(e)}")


# ============================================================================
# 멀티모델 파이프라인 API 엔드포인트
# ============================================================================

@app.get("/pipeline/info", tags=["Pipeline"])
async def get_pipeline_info():
    """현재 로드된 파이프라인 정보를 반환합니다."""
    try:
        info = pipeline_manager.get_pipeline_info()
        return {
            "success": True,
            "pipeline_info": info
        }
    except Exception as e:
        logger.error(f"파이프라인 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/load-model", tags=["Pipeline"])
async def load_pipeline_model(
    task_name: str = Form(...),
    model_name: str = Form(...),
    model_path: Optional[str] = Form(None),
    config: Optional[str] = Form(None)
):
    """파이프라인에 모델을 로드합니다."""
    try:
        logger.info(f"모델 로드 요청: {task_name} -> {model_name}")

        # 추가 설정 파싱
        kwargs = {}
        if config:
            kwargs = json.loads(config)

        # 모델 추가
        pipeline_manager.add_model(
            task_name=task_name,
            model_name=model_name,
            model_path=model_path,
            **kwargs
        )

        return {
            "success": True,
            "message": f"{model_name} 모델이 {task_name}에 로드되었습니다",
            "pipeline_info": pipeline_manager.get_pipeline_info()
        }

    except Exception as e:
        logger.error(f"모델 로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/process-multi", tags=["Pipeline"])
async def process_multi_task(
    file: UploadFile = File(...),
    tasks: str = Form(...),
    detection_config: Optional[str] = Form(None),
    keypoint_config: Optional[str] = Form(None),
    ocr_config: Optional[str] = Form(None)
):
    """
    멀티태스크 파이프라인 실행
    여러 모델을 동시에 실행합니다 (detection, keypoint, ocr 등)
    """
    import time
    from io import BytesIO

    start_time = time.time()

    try:
        logger.info(f"🚀 멀티태스크 파이프라인 요청 - 파일: {file.filename}")

        # 파일 검증
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="이미지 파일만 허용됩니다")

        # 태스크 파싱
        tasks_list = json.loads(tasks)
        logger.info(f"실행할 태스크: {tasks_list}")

        # 각 태스크별 설정 파싱
        configs = {}
        if detection_config:
            configs["detection"] = json.loads(detection_config)
        if keypoint_config:
            configs["keypoint"] = json.loads(keypoint_config)
        if ocr_config:
            configs["ocr"] = json.loads(ocr_config)

        # 이미지 읽기
        contents = await file.read()
        image_bytes = BytesIO(contents)
        pil_image = Image.open(image_bytes)

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

        logger.info(f"이미지 로드 완료: {pil_image.size}, {pil_image.mode}")

        # 파이프라인 실행
        results = pipeline_manager.run_pipeline(
            image=pil_image,
            tasks=tasks_list,
            **configs
        )

        # 이미지 인코딩 (결과 표시용)
        import base64
        import io
        buffered = io.BytesIO()
        pil_image.save(buffered, format="JPEG", quality=95)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ 파이프라인 실행 완료 - 소요시간: {elapsed_time:.2f}초")

        return {
            "success": True,
            "results": results,
            "image": f"data:image/jpeg;base64,{img_base64}",
            "image_size": {
                "width": pil_image.width,
                "height": pil_image.height
            },
            "processing_time": round(elapsed_time, 3),
            "pipeline_info": pipeline_manager.get_pipeline_info()
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 파이프라인 실행 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/available", tags=["Pipeline"])
async def get_available_models():
    """사용 가능한 모델 목록을 반환합니다."""
    try:
        models = ModelFactory.get_available_models()
        return {
            "success": True,
            "models": models,
            "total_models": sum(len(v) for v in models.values())
        }
    except Exception as e:
        logger.error(f"모델 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 여기서는 주요 엔드포인트들만 포함하고, 나머지는 별도 모듈로 분리하는 것을 권장
# 실제 구현에서는 이 파일을 여러 모듈로 분리하여 유지보수성을 높여야 합니다.

if __name__ == "__main__":
    logger.info("🚀 Iljoo AutoLabeling 서버 시작 중...")
    
    # Vue 빌드 파일 존재 여부 확인
    vue_index = VUE_DIST_DIR / "index.html"
    
    if vue_index.exists():
        logger.info(f"🌐 웹 인터페이스: http://localhost:8000")
        logger.info(f"📚 API 문서: http://localhost:8000/docs")
    else:
        logger.warning("Vue 빌드 파일을 찾을 수 없습니다!")
        logger.info("cd autolabeling && npm run build")
        logger.info(f"🌐 API만 실행: http://localhost:8000")
        logger.info(f"📚 API 문서: http://localhost:8000/docs") 