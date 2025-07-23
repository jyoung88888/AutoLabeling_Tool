"""
모델 관련 유틸리티 함수
"""
import torch
import cv2
import numpy as np
import logging
import json
from pathlib import Path
from fastapi import HTTPException
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.model = None
        
    def get_model_training_info(self, model_path):
        """
        YOLO 모델의 학습 정보를 확인합니다.
        
        Args:
            model_path: 모델 파일 경로
            
        Returns:
            모델 학습 정보를 포함한 딕셔너리
        """
        try:
            if isinstance(model_path, str):
                model_path = Path(model_path)
            
            if not model_path.exists():
                raise HTTPException(status_code=404, detail=f"모델 파일을 찾을 수 없습니다: {model_path}")
                
            logger.info(f"🔍 YOLO 모델 학습 정보 분석 시작: {model_path}")
            
            # PyTorch 모델 파일 로드
            try:
                checkpoint = torch.load(str(model_path), map_location='cpu', weights_only=False)
                logger.info(f"✅ 모델 파일 로드 성공: {model_path}")
            except Exception as e:
                logger.error(f"❌ 모델 파일 로드 실패: {str(e)}")
                raise HTTPException(status_code=400, detail=f"모델 파일 로드 실패: {str(e)}")
            
            # 기본 정보 수집
            training_info = {
                "model_file": model_path.name,
                "file_size": f"{model_path.stat().st_size / (1024*1024):.2f} MB",
                "file_path": str(model_path),
                "created_date": datetime.fromtimestamp(model_path.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified_date": datetime.fromtimestamp(model_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 체크포인트 키 확인
            logger.info(f"📊 체크포인트 키들: {list(checkpoint.keys())}")
            
            # 모델 정보 추출
            if 'model' in checkpoint:
                model_info = checkpoint['model']
                if hasattr(model_info, 'yaml') and hasattr(model_info, 'nc'):
                    training_info['num_classes'] = model_info.nc
                    training_info['model_yaml'] = model_info.yaml if hasattr(model_info, 'yaml') else None
                
                # 모델 구조 정보
                training_info['model_structure'] = str(type(model_info))
                
            # 클래스 정보 추출
            if 'names' in checkpoint:
                names = checkpoint['names']
                training_info['classes'] = names
                training_info['num_classes'] = len(names) if isinstance(names, (list, dict)) else 0
                logger.info(f"📋 클래스 정보: {len(names) if isinstance(names, (list, dict)) else 0}개 클래스")
                
                # 클래스별 상세 정보
                if isinstance(names, dict):
                    class_list = []
                    for class_id, class_name in sorted(names.items()):
                        class_list.append({"id": class_id, "name": class_name})
                    training_info['class_details'] = class_list
                elif isinstance(names, list):
                    class_list = []
                    for i, class_name in enumerate(names):
                        class_list.append({"id": i, "name": class_name})
                    training_info['class_details'] = class_list
            
            # 학습 관련 정보 추출
            if 'epoch' in checkpoint:
                training_info['trained_epochs'] = checkpoint['epoch']
                logger.info(f"📈 학습 에포크: {checkpoint['epoch']}")
                
            if 'best_fitness' in checkpoint:
                best_fitness = checkpoint['best_fitness']
                if best_fitness is not None:
                    training_info['best_fitness'] = float(best_fitness)
                    logger.info(f"🏆 최고 적합도: {best_fitness}")
                else:
                    training_info['best_fitness'] = None
                    logger.info("🏆 최고 적합도: 정보 없음")
                
            # 학습 결과 메트릭
            metrics = {}
            for key in ['results', 'metrics', 'val_results']:
                if key in checkpoint:
                    metrics[key] = checkpoint[key]
                    
            if metrics:
                training_info['training_metrics'] = metrics
                logger.info(f"📊 학습 메트릭 발견: {list(metrics.keys())}")
            
            # 하이퍼파라미터 정보
            if 'opt' in checkpoint:
                opt = checkpoint['opt']
                try:
                    if hasattr(opt, '__dict__'):
                        hyperparams = {}
                        for key, value in opt.__dict__.items():
                            if not key.startswith('_'):
                                # 직렬화 가능한 값만 저장
                                try:
                                    json.dumps(value)  # 직렬화 가능성 테스트
                                    hyperparams[key] = value
                                except (TypeError, ValueError):
                                    hyperparams[key] = str(value)  # 문자열로 변환
                        training_info['hyperparameters'] = hyperparams
                        logger.info(f"⚙️ 하이퍼파라미터 정보 추출됨: {len(hyperparams)}개 파라미터")
                    elif isinstance(opt, dict):
                        # 딕셔너리 형태의 하이퍼파라미터 처리
                        safe_hyperparams = {}
                        for key, value in opt.items():
                            try:
                                json.dumps(value)  # 직렬화 가능성 테스트
                                safe_hyperparams[key] = value
                            except (TypeError, ValueError):
                                safe_hyperparams[key] = str(value)  # 문자열로 변환
                        training_info['hyperparameters'] = safe_hyperparams
                        logger.info(f"⚙️ 하이퍼파라미터 정보 추출됨: {len(safe_hyperparams)}개 파라미터")
                except Exception as e:
                    logger.warning(f"⚠️ 하이퍼파라미터 정보 추출 실패: {str(e)}")
                    training_info['hyperparameters'] = {"error": "정보 추출 실패"}
                    
            # 모델 아키텍처 정보
            if 'model' in checkpoint:
                try:
                    model_state = checkpoint['model']
                    if hasattr(model_state, 'yaml'):
                        training_info['model_config'] = model_state.yaml
                    if hasattr(model_state, 'stride'):
                        stride = model_state.stride
                        # stride가 tensor인 경우 리스트로 변환
                        if hasattr(stride, 'tolist'):
                            training_info['model_stride'] = stride.tolist()
                        else:
                            training_info['model_stride'] = stride
                    if hasattr(model_state, 'pt_path'):
                        training_info['pretrained_path'] = model_state.pt_path
                except Exception as e:
                    logger.warning(f"⚠️ 모델 아키텍처 정보 추출 실패: {str(e)}")
            
            # 학습 환경 정보
            training_env = {}
            for key in ['date', 'version', 'license', 'git']:
                if key in checkpoint:
                    value = checkpoint[key]
                    # 직렬화 가능한 값만 저장
                    try:
                        json.dumps(value)
                        training_env[key] = value
                    except (TypeError, ValueError):
                        training_env[key] = str(value)
                    
            if training_env:
                training_info['training_environment'] = training_env
                logger.info(f"🔧 학습 환경 정보: {list(training_env.keys())}")
            
            # 모델 가중치 정보
            if 'model' in checkpoint:
                try:
                    model_state = checkpoint['model']
                    if hasattr(model_state, 'parameters'):
                        total_params = sum(p.numel() for p in model_state.parameters())
                        training_info['total_parameters'] = total_params
                        logger.info(f"🎯 총 파라미터 수: {total_params:,}")
                except Exception as e:
                    logger.warning(f"⚠️ 파라미터 수 계산 실패: {str(e)}")
                    
            # 추가 정보들
            additional_info = {}
            for key in ['ema', 'updates', 'optimizer', 'wandb_id', 'train_args']:
                if key in checkpoint:
                    value = checkpoint[key]
                    # 직렬화 가능한 값만 저장
                    try:
                        json.dumps(value)
                        additional_info[key] = value
                    except (TypeError, ValueError):
                        additional_info[key] = str(value)
                    
            if additional_info:
                training_info['additional_info'] = additional_info
                logger.info(f"📝 추가 정보: {list(additional_info.keys())}")
            
            logger.info(f"✅ 모델 학습 정보 분석 완료: {model_path.name}")
            return training_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 모델 학습 정보 분석 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"모델 학습 정보 분석 오류: {str(e)}")
    

        
    def load_model(self, model_path):
        """
        YOLO 모델을 로드합니다.
        
        Args:
            model_path: 모델 파일 경로
            
        Returns:
            성공 여부 및 메시지를 포함한 딕셔너리
        """
        try:
            from ultralytics import YOLO
            
            if not model_path.is_file():
                raise HTTPException(status_code=404, detail="Model file not found")
            
            self.model = YOLO(str(model_path))
            
            if torch.cuda.is_available():
                torch.cuda.set_device(0)
                self.model.to('cuda:0')
            
            return {
                "success": True,
                "message": f"Model {model_path} loaded successfully"
            }
        except Exception as e:
            logger.error(f"모델 로드 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
            
    def get_device_info(self):
        """
        GPU 관련 정보를 반환합니다.
        
        Returns:
            GPU 정보를 포함한 딕셔너리
        """
        try:
            gpu_info = {
                "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "없음",
                "count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "cuda_available": torch.cuda.is_available()
            }
            return {"gpu_info": gpu_info}
        except Exception as e:
            return {"message": "GPU 정보를 가져올 수 없습니다."}

    def get_model_classes(self):
        """
        모델의 클래스 정보를 반환합니다.
        YOLO 모델의 원래 ID 순서를 보장합니다.
        
        Returns:
            클래스 정보를 포함한 딕셔너리
        """
        try:
            if self.model is None:
                raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다. 먼저 모델을 로드해주세요.")
            
            classes = self.model.names
            logger.info(f"모델에서 가져온 원본 클래스 정보: {classes} (타입: {type(classes)})")
            
            # 클래스가 숫자 인덱스 키를 가진 딕셔너리인 경우 처리
            if isinstance(classes, dict):
                # 숫자 인덱스 키를 정수로 변환하여 정렬 (YOLO 모델의 원래 ID 순서 보장)
                valid_classes = {}
                invalid_entries = []
                
                for k, v in classes.items():
                    try:
                        class_id = int(k)
                        if v and isinstance(v, str) and v.strip():
                            valid_classes[class_id] = v.strip()
                        else:
                            invalid_entries.append(f"ID {k}: 빈 클래스명")
                    except (ValueError, TypeError):
                        invalid_entries.append(f"ID {k}: 잘못된 ID 형식")
                
                if invalid_entries:
                    logger.warning(f"유효하지 않은 클래스 엔트리들: {invalid_entries}")
                
                # ID 순서대로 정렬 (0, 1, 2, 3, ...)
                sorted_classes = dict(sorted(valid_classes.items()))
                
                # 클래스 ID 연속성 확인 및 로깅
                class_ids = list(sorted_classes.keys())
                if class_ids:
                    min_id = min(class_ids)
                    max_id = max(class_ids)
                    missing_ids = []
                    
                    for i in range(min_id, max_id + 1):
                        if i not in class_ids:
                            missing_ids.append(i)
                    
                    logger.info(f"클래스 ID 범위: {min_id} ~ {max_id}")
                    logger.info(f"총 클래스 수: {len(sorted_classes)}개")
                    
                    if missing_ids:
                        logger.warning(f"누락된 클래스 ID들: {missing_ids}")
                        logger.warning("YOLO 모델에서 일부 클래스 ID가 누락되었습니다. 이는 커스텀 모델에서 정상적일 수 있습니다.")
                    else:
                        logger.info("✅ 모든 클래스 ID가 연속적입니다.")
                    
                    # 각 클래스 정보 로깅
                    for class_id, class_name in sorted_classes.items():
                        logger.info(f"  ID {class_id}: '{class_name}'")
                else:
                    logger.error("유효한 클래스가 없습니다.")
                    raise HTTPException(status_code=400, detail="모델에 유효한 클래스가 없습니다.")
                
                logger.info(f"✅ YOLO 모델 클래스 정보 반환 완료: ID 순서 보장됨")
                return {"classes": sorted_classes}
            
            # 클래스가 리스트인 경우 (인덱스가 자동으로 ID가 됨)
            elif isinstance(classes, list):
                # 리스트를 딕셔너리로 변환하여 ID 명시
                class_dict = {}
                for i, class_name in enumerate(classes):
                    if class_name and isinstance(class_name, str) and class_name.strip():
                        class_dict[i] = class_name.strip()
                        logger.info(f"  ID {i}: '{class_name.strip()}'")
                
                logger.info(f"✅ 리스트 형태 클래스 정보를 딕셔너리로 변환 완료: {len(class_dict)}개 클래스")
                return {"classes": class_dict}
            
            # 클래스 정보가 없는 경우 오류 발생
            logger.error("유효한 클래스 정보를 찾을 수 없습니다")
            raise HTTPException(status_code=400, detail="유효한 클래스 정보를 찾을 수 없습니다. 모델을 다시 로드해주세요.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"모델 클래스 정보 조회 오류: {str(e)}")
            # 오류 반환
            raise HTTPException(status_code=500, detail=f"클래스 정보 조회 오류: {str(e)}")
                              
    def predict_image(self, image_input, selected_classes=None, confidence_threshold=0.5):
        """
        이미지에 대한 예측을 수행합니다.
        ultralytics YOLO의 표준 방식을 사용하여 최적의 성능을 보장합니다.
        
        Args:
            image_input: 이미지 파일 경로 (str 또는 Path 객체) 또는 BytesIO 스트림
            selected_classes: 선택된 클래스 목록 (선택 사항)
            confidence_threshold: 신뢰도 임계값 (0.0~1.0, 기본값: 0.5)
            
        Returns:
            예측 결과를 포함한 딕셔너리 (ultralytics 표준 형식)
        """
        try:
            if self.model is None:
                logger.error("모델이 로드되지 않았습니다.")
                raise HTTPException(status_code=400, detail="모델이 로드되지 않았습니다. 먼저 모델을 로드해주세요.")
            
            # 사용자가 설정한 신뢰도 임계값을 그대로 사용
            effective_conf = confidence_threshold
            
            logger.info(f"YOLO 예측 시작 - 신뢰도 임계값: {effective_conf}")
            
            # BytesIO 입력 처리
            from io import BytesIO
            processed_input = image_input
            
            if isinstance(image_input, BytesIO):
                try:
                    # BytesIO를 PIL 이미지로 변환하여 ultralytics에서 처리 가능하도록 함
                    from PIL import Image
                    image_input.seek(0)  # 스트림 포지션을 처음으로 이동
                    pil_image = Image.open(image_input)
                    
                    # RGBA나 LA 모드인 경우 RGB로 변환
                    if pil_image.mode in ('RGBA', 'LA'):
                        # 흰색 배경으로 변환
                        rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'RGBA':
                            rgb_image.paste(pil_image, mask=pil_image.split()[-1])
                        else:
                            rgb_image.paste(pil_image.convert('L'))
                        pil_image = rgb_image
                    elif pil_image.mode not in ('RGB', 'L'):
                        pil_image = pil_image.convert('RGB')
                    
                    processed_input = pil_image
                    logger.info(f"BytesIO 입력을 PIL 이미지로 변환: 모드 {pil_image.mode}, 크기 {pil_image.size}")
                except Exception as e:
                    logger.error(f"BytesIO 이미지 처리 실패: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"이미지 처리 실패: {str(e)}")
            
            # ultralytics 기본값을 사용한 최적화된 예측 수행
            # 사용자 설정 신뢰도 임계값과 IoU 0.5 사용
            try:
                logger.info(f"YOLO 모델 예측 실행 중...")
                results = self.model.predict(
                    processed_input,
                    imgsz=640,  # 이미지 크기 명시적 지정
                    conf=effective_conf,  # 사용자 설정 신뢰도 값 사용
                    iou=0.5,  # IoU 기본값 0.5 사용
                    max_det=300,  # ultralytics 기본값 최대 검출 수
                    augment=False,  # 추론 시 증강 비활성화
                    agnostic_nms=False,  # ultralytics 기본값 클래스별 NMS
                    classes=None,  # 모든 클래스 허용 (후에 필터링)
                    half=False,  # FP32 사용 for 정확도
                    device=None,  # 자동 디바이스 선택
                    verbose=False,  # 로그 출력 최소화
                    save=False,  # 결과 저장 안함
                    save_txt=False,  # 텍스트 저장 안함
                    save_conf=False,  # 신뢰도 저장 안함
                    save_crop=False,  # 크롭 저장 안함
                    show=False,  # 결과 표시 안함
                    retina_masks=False,  # 세그멘테이션 마스크 비활성화
                    show_labels=True,  # 라벨 표시
                    show_conf=True,  # 신뢰도 표시
                    show_boxes=True,  # 박스 표시
                    vid_stride=1,  # 비디오 프레임 스트라이드
                    stream_buffer=False,  # 스트림 버퍼 비활성화
                    visualize=False,  # 모델 피처 시각화 비활성화
                    rect=True,  # 사각형 추론 (패딩 최소화)
                    batch=1  # 배치 크기 1
                )
                logger.info(f"YOLO 모델 예측 완료")
            except Exception as e:
                logger.error(f"YOLO 모델 예측 실행 실패: {str(e)}")
                raise HTTPException(status_code=500, detail=f"모델 예측 실행 실패: {str(e)}")
            
            # 예측 결과 처리
            try:
                result = results[0]  # 첫 번째 결과
                boxes = []
                
                logger.info(f"원본 이미지 크기: {result.orig_shape}")
                
                # YOLO 결과 처리
                if result.boxes is not None and len(result.boxes) > 0:
                    logger.info(f"YOLO 모델 클래스 정보: {self.model.names}")
                    logger.info(f"선택된 클래스: {selected_classes}")
                    logger.info(f"탐지된 박스 수: {len(result.boxes)}")
                    
                    # ultralytics 표준 방식으로 데이터 추출
                    for box in result.boxes:
                        try:
                            # 클래스 ID와 이름 추출
                            class_id = int(box.cls.item())
                            
                            # 클래스 이름 매핑
                            if hasattr(self.model, 'names') and self.model.names:
                                class_name = self.model.names.get(class_id, f"class_{class_id}")
                            else:
                                class_name = f"class_{class_id}"
                            
                            # 선택된 클래스 필터링
                            if selected_classes and len(selected_classes) > 0 and class_name not in selected_classes:
                                logger.debug(f"클래스 필터링: '{class_name}' 제외됨")
                                continue
                            
                            # 신뢰도
                            confidence = float(box.conf.item())
                            
                            # 정규화된 좌표 (ultralytics에서 제공)
                            xywhn = box.xywhn[0]  # 정규화된 중심점 좌표
                            x_center_norm = float(xywhn[0])
                            y_center_norm = float(xywhn[1])
                            width_norm = float(xywhn[2])
                            height_norm = float(xywhn[3])
                            
                            # 픽셀 좌표 (ultralytics에서 제공)
                            xywh = box.xywh[0]  # 픽셀 중심점 좌표
                            x_center = float(xywh[0])
                            y_center = float(xywh[1])
                            width = float(xywh[2])
                            height = float(xywh[3])
                            
                            # 좌상단 좌표 계산
                            x = x_center - width / 2
                            y = y_center - height / 2
                            
                            # 박스 정보 저장 (ultralytics 표준 형식)
                            box_info = {
                                "class_id": class_id,
                                "class_name": class_name,
                                "confidence": confidence,
                                "bbox": [float(x), float(y), float(width), float(height)],
                                "normalized_coords": [x_center_norm, y_center_norm, width_norm, height_norm]
                            }
                            
                            boxes.append(box_info)
                            logger.debug(f"박스 추가: {class_name} (ID: {class_id}, 신뢰도: {confidence:.3f})")
                            
                        except Exception as e:
                            logger.warning(f"박스 처리 중 오류: {str(e)}")
                            continue
                else:
                    logger.info("탐지된 객체가 없습니다.")
                
                logger.info(f"✅ ultralytics 최적화 예측 완료: {len(boxes)}개 객체 감지됨")
                
                return boxes
                
            except Exception as e:
                logger.error(f"예측 결과 처리 실패: {str(e)}")
                raise HTTPException(status_code=500, detail=f"예측 결과 처리 실패: {str(e)}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"이미지 예측 중 예상치 못한 오류: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"이미지 예측 중 오류가 발생했습니다: {str(e)}") 