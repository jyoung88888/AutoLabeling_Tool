#!/usr/bin/env python3
"""
Iljoo AutoLabeling 개발 서버 실행 스크립트
백엔드(FastAPI)와 프론트엔드(Vue.js)를 동시에 실행합니다.

사용법:
    python run.py [dev|build] [옵션]

모드:
    dev     - 개발 모드 (기본값): Vue.js 개발 서버 + FastAPI 서버 동시 실행
              🔧 백엔드 포트: 8000 (자동 리로드 활성화)
              📁 데이터 디렉토리: server/uploaded_images
              
    build   - 빌드 모드: Vue.js 빌드 후 FastAPI 서버 + UI 서버 동시 실행
              🏭 백엔드 포트: 8000 (운영용)
              📁 데이터 디렉토리: server/uploaded_images

옵션:
    --no-install    - npm install을 건너뜁니다
    --port PORT     - 백엔드 서버 포트 (기본값: 8000)
    --ui-port PORT  - UI 서버 포트 (build 모드용, 기본값: 자동 할당)
    --host HOST     - 백엔드 서버 호스트 (기본값: 0.0.0.0)
    --help          - 도움말 표시

데이터 저장:
    개발 모드와 빌드 모드 모두 동일한 server/uploaded_images 디렉토리를 사용합니다.
    개발 모드에서는 자동 리로드 기능으로 코드 변경이 즉시 반영됩니다.
"""

import sys
import subprocess
import threading
import time
import signal
import logging
import re
import argparse
import socket
import json
import os
import shutil
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import urllib.request
import urllib.error

# 터미널 색상 코드
class Colors:
    """터미널 색상을 위한 ANSI 코드"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # 기본 색상 (실제 사용되는 것들만)
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    
    # 밝은 색상 (실제 사용되는 것들만)
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_CYAN = '\033[96m'

def colorize_log(message, is_backend=True):
    """로그 메시지에 색상을 적용합니다."""
    # 에러 패턴 검사
    error_patterns = [
        r'error', r'Error', r'ERROR',
        r'exception', r'Exception', r'EXCEPTION',
        r'fail', r'Fail', r'FAIL',
        r'fatal', r'Fatal', r'FATAL',
        r'critical', r'Critical', r'CRITICAL',
        r'traceback', r'Traceback', r'TRACEBACK'
    ]
    
    # 경고 패턴 검사
    warning_patterns = [
        r'warn', r'Warn', r'WARNING',
        r'deprecated', r'Deprecated', r'DEPRECATED'
    ]
    
    # 성공 패턴 검사
    success_patterns = [
        r'success', r'Success', r'SUCCESS',
        r'complete', r'Complete', r'COMPLETED',
        r'ready', r'Ready', r'READY',
        r'started', r'Started', r'STARTED'
    ]
    
    # 에러 메시지인지 확인
    if any(re.search(pattern, message) for pattern in error_patterns):
        color = Colors.BRIGHT_RED
    # 경고 메시지인지 확인
    elif any(re.search(pattern, message) for pattern in warning_patterns):
        color = Colors.BRIGHT_YELLOW
    # 성공 메시지인지 확인
    elif any(re.search(pattern, message) for pattern in success_patterns):
        color = Colors.BRIGHT_GREEN
    # 일반 메시지
    else:
        if is_backend:
            color = Colors.BRIGHT_BLUE  # 백엔드는 파란색
        else:
            color = Colors.BRIGHT_CYAN  # 프론트엔드는 시안색
    
    # 태그 색상
    if is_backend:
        tag_color = Colors.BLUE + Colors.BOLD
        tag = "[BACKEND]"
    else:
        tag_color = Colors.CYAN + Colors.BOLD
        tag = "[FRONTEND]"
    
    return f"{tag_color}{tag}{Colors.RESET} {color}{message}{Colors.RESET}"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_local_ip():
    """로컬 네트워크 IP 주소 가져오기"""
    try:
        # 구글 DNS(8.8.8.8)에 연결을 시도하여 로컬 IP 주소 확인
        # 실제로 패킷을 보내지는 않고 소켓만 생성
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        try:
            # 대안 방법: 호스트명으로 IP 주소 가져오기
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip.startswith("127."):
                # 127.x.x.x인 경우 네트워크 인터페이스에서 찾기
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                if result.returncode == 0:
                    ips = result.stdout.strip().split()
                    for ip in ips:
                        if not ip.startswith("127.") and not ip.startswith("::"):
                            return ip
            return local_ip
        except Exception:
            return "127.0.0.1"

class SPAHandler(SimpleHTTPRequestHandler):
    """SPA(Single Page Application)를 위한 커스텀 HTTP 핸들러"""
    
    def __init__(self, *args, **kwargs):
        self.backend_port = kwargs.pop('backend_port', 8000)
        super().__init__(*args, directory=kwargs.pop('directory', None), **kwargs)
    
    def end_headers(self):
        # CORS 헤더 추가 (개발 환경에서 필요할 수 있음)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        """GET 요청 처리 - API 프록시 및 SPA 라우팅 지원"""
        # URL 파싱
        parsed_path = urlparse(self.path)
        file_path = parsed_path.path
        
        # API 요청인 경우 백엔드로 프록시
        if self.is_api_request(file_path):
            self.proxy_to_backend()
            return
        
        # 루트 경로면 index.html로 리다이렉트
        if file_path == '/':
            file_path = '/index.html'
        
        # 실제 파일 경로 생성
        full_path = Path(self.directory) / file_path.lstrip('/')
        
        # 파일이 존재하는지 확인
        if full_path.exists() and full_path.is_file():
            # 파일이 존재하면 기본 핸들러로 처리
            super().do_GET()
        else:
            # 파일이 존재하지 않으면 확장자 확인
            if '.' in file_path.split('/')[-1]:
                # 확장자가 있는 파일(이미지, CSS, JS 등)은 404 반환
                self.send_error(404, f"File not found: {file_path}")
            else:
                # 확장자가 없는 경로(라우트)는 index.html 반환
                self.serve_spa_route()
    
    def do_POST(self):
        """POST 요청 처리 - API 프록시"""
        parsed_path = urlparse(self.path)
        file_path = parsed_path.path
        
        # API 요청인 경우 백엔드로 프록시
        if self.is_api_request(file_path):
            self.proxy_to_backend()
        else:
            self.send_error(404, "POST not supported for static files")
    
    def do_DELETE(self):
        """DELETE 요청 처리 - API 프록시"""
        parsed_path = urlparse(self.path)
        file_path = parsed_path.path
        
        # API 요청인 경우 백엔드로 프록시
        if self.is_api_request(file_path):
            self.proxy_to_backend()
        else:
            self.send_error(404, "DELETE not supported for static files")
    
    def do_OPTIONS(self):
        """OPTIONS 요청 처리 - CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def is_api_request(self, path):
        """API 요청인지 확인"""
        api_prefixes = [
            '/api/', '/models/', '/files/', '/upload/', '/image/', 
            '/server-image/', '/device-info/', '/device/', '/model/', 
            '/labeling/', '/project/', '/refresh/'
        ]
        return any(path.startswith(prefix) for prefix in api_prefixes)
    
    def proxy_to_backend(self):
        """백엔드 서버로 요청 프록시"""
        try:
            # 백엔드 URL 구성
            backend_url = f"http://localhost:{self.backend_port}{self.path}"
            
            # 요청 데이터 읽기 (POST 요청의 경우)
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # 요청 헤더 복사
            headers = {}
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ['host', 'connection']:
                    headers[header_name] = header_value
            
            # 백엔드에 요청
            req = urllib.request.Request(
                backend_url,
                data=post_data,
                headers=headers,
                method=self.command
            )
            
            with urllib.request.urlopen(req) as response:
                # 응답 상태 코드
                self.send_response(response.getcode())
                
                # 응답 헤더 복사
                for header_name, header_value in response.headers.items():
                    if header_name.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header_name, header_value)
                
                self.end_headers()
                
                # 응답 본문 전달
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            # HTTP 에러 응답 전달
            self.send_response(e.code)
            for header_name, header_value in e.headers.items():
                if header_name.lower() not in ['connection', 'transfer-encoding']:
                    self.send_header(header_name, header_value)
            self.end_headers()
            
            try:
                error_content = e.read()
                self.wfile.write(error_content)
            except Exception:
                pass
                
        except Exception as e:
            # 연결 오류 등
            self.send_error(502, f"Backend connection failed: {str(e)}")
    
    def serve_spa_route(self):
        """SPA 라우트를 위해 index.html 제공"""
        index_path = Path(self.directory) / 'index.html'
        
        if not index_path.exists():
            self.send_error(404, "index.html not found")
            return
        
        try:
            with open(index_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_error(500, f"Error serving index.html: {str(e)}")
    
    def log_message(self, format, *args):
        """로그 메시지 커스터마이징"""
        message = format % args
        # 성공적인 요청은 간단히 로그
        if ' 200 ' in message:
            print(colorize_log(f"UI Server: {message}", is_backend=False))
        # 에러는 더 자세히 로그
        elif ' 404 ' in message or ' 500 ' in message:
            print(colorize_log(f"UI Server ERROR: {message}", is_backend=False))
        else:
            print(colorize_log(f"UI Server: {message}", is_backend=False))

class DevServerManager:
    def __init__(self, mode='dev', host='0.0.0.0', port=None, ui_port=None, no_install=False):
        self.base_dir = Path(__file__).parent.resolve()
        self.mode = mode
        self.host = host
        
        # YOLO 설정 디렉토리 환경 변수 설정
        yolo_config_dir = self.base_dir / "server" / "config" / "yolo"
        yolo_config_dir.mkdir(parents=True, exist_ok=True)
        os.environ['YOLO_CONFIG_DIR'] = str(yolo_config_dir)
        logger.info(f"✅ YOLO 설정 디렉토리 설정: {yolo_config_dir}")
        
        # 모든 모드에서 8000번 포트 사용 (개발/운영 구분은 데이터 디렉토리로)
        if port is None:
            self.port = 8000  # 개발 모드와 빌드 모드 모두 8000번 포트
        else:
            self.port = port
            
        self.ui_port = ui_port
        self.no_install = no_install
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
        # 실제 IP 주소 가져오기
        self.local_ip = get_local_ip()
        
        # 포트 범위 설정
        self.ui_port_range = range(3000, 4000)  # UI 서버용 포트 범위
        self.backend_port_range = range(8000, 8100)  # 백엔드 서버용 포트 범위
        
        # 사용 중인 포트 추적을 위한 파일
        self.port_lock_file = self.base_dir / ".port_locks"
        
        # 프로세스 종료를 위한 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def is_port_available(self, port, host='localhost'):
        """포트가 사용 가능한지 확인"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0
        except Exception:
            return False
    
    def get_used_ports(self):
        """현재 사용 중인 포트 목록 가져오기"""
        used_ports = set()
        
        # 락 파일에서 사용 중인 포트 읽기
        if self.port_lock_file.exists():
            try:
                with open(self.port_lock_file, 'r') as f:
                    port_data = json.load(f)
                    current_time = time.time()
                    
                    # 오래된 락 제거 (1시간 이상 된 것)
                    valid_ports = {}
                    for port_str, timestamp in port_data.items():
                        if current_time - timestamp < 3600:  # 1시간
                            valid_ports[port_str] = timestamp
                            used_ports.add(int(port_str))
                    
                    # 유효한 포트만 다시 저장
                    with open(self.port_lock_file, 'w') as f:
                        json.dump(valid_ports, f)
                        
            except (json.JSONDecodeError, ValueError):
                # 파일이 손상된 경우 새로 생성
                pass
        
        return used_ports
    
    def lock_port(self, port):
        """포트 사용 락 생성"""
        port_data = {}
        if self.port_lock_file.exists():
            try:
                with open(self.port_lock_file, 'r') as f:
                    port_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                pass
        
        port_data[str(port)] = time.time()
        
        os.makedirs(self.port_lock_file.parent, exist_ok=True)
        with open(self.port_lock_file, 'w') as f:
            json.dump(port_data, f)
    
    def unlock_port(self, port):
        """포트 사용 락 해제"""
        if not self.port_lock_file.exists():
            return
        
        try:
            with open(self.port_lock_file, 'r') as f:
                port_data = json.load(f)
            
            port_data.pop(str(port), None)
            
            with open(self.port_lock_file, 'w') as f:
                json.dump(port_data, f)
                
        except (json.JSONDecodeError, ValueError):
            pass
    
    def find_available_port(self, port_range, preferred_port=None):
        """사용 가능한 포트 찾기"""
        used_ports = self.get_used_ports()
        
        # 선호하는 포트가 지정되고 사용 가능하면 사용
        if preferred_port and preferred_port in port_range:
            if (preferred_port not in used_ports and 
                self.is_port_available(preferred_port, self.host)):
                return preferred_port
        
        # 포트 범위에서 사용 가능한 포트 찾기
        for port in port_range:
            if (port not in used_ports and 
                self.is_port_available(port, self.host)):
                return port
        
        return None
    
    def assign_ports(self):
        """포트 할당"""
        # 백엔드 포트 할당
        if not self.is_port_available(self.port, self.host):
            logger.warning(f"지정된 백엔드 포트 {self.port}가 사용 중입니다. 다른 포트를 찾는 중...")
            new_port = self.find_available_port(self.backend_port_range, self.port)
            if new_port:
                self.port = new_port
                logger.info(f"백엔드 포트를 {self.port}로 변경했습니다.")
            else:
                logger.error("사용 가능한 백엔드 포트를 찾을 수 없습니다.")
                return False
        
        # UI 포트 할당 (build 모드인 경우)
        if self.mode == 'build':
            if self.ui_port is None:
                self.ui_port = self.find_available_port(self.ui_port_range)
                if self.ui_port is None:
                    logger.error("사용 가능한 UI 포트를 찾을 수 없습니다.")
                    return False
            else:
                if not self.is_port_available(self.ui_port, self.host):
                    logger.warning(f"지정된 UI 포트 {self.ui_port}가 사용 중입니다. 다른 포트를 찾는 중...")
                    new_ui_port = self.find_available_port(self.ui_port_range, self.ui_port)
                    if new_ui_port:
                        self.ui_port = new_ui_port
                        logger.info(f"UI 포트를 {self.ui_port}로 변경했습니다.")
                    else:
                        logger.error("사용 가능한 UI 포트를 찾을 수 없습니다.")
                        return False
        
        # 포트 락 생성
        self.lock_port(self.port)
        if self.mode == 'build' and self.ui_port:
            self.lock_port(self.ui_port)
        
        return True
    
    def signal_handler(self, signum, _):
        """Ctrl+C 등의 시그널 처리"""
        logger.info(f"\n시그널 {signum} 수신. 서버들을 종료하는 중...")
        self.shutdown()
        sys.exit(0)
    
    def check_prerequisites(self):
        """필수 조건 확인"""
        logger.info("필수 조건을 확인하는 중...")
        
        # Python 서버 파일 확인
        server_file = self.base_dir / "server" / "main.py"
        if not server_file.exists():
            logger.error(f"백엔드 서버 파일을 찾을 수 없습니다: {server_file}")
            return False
        
        # package.json 확인
        package_json = self.base_dir / "package.json"
        if not package_json.exists():
            logger.error(f"package.json 파일을 찾을 수 없습니다: {package_json}")
            return False
        
        # npm 설치 확인
        try:
            subprocess.run("npm --version", capture_output=True, check=True, shell=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("npm이 설치되지 않았거나 PATH에 없습니다.")
            return False
        
        # Python 패키지 확인
        try:
            import fastapi
            import uvicorn
        except ImportError as e:
            logger.error(f"필수 Python 패키지가 설치되지 않았습니다: {e}")
            return False
        
        logger.info("✅ 모든 필수 조건이 충족되었습니다.")
        return True
    
    def install_dependencies(self):
        """의존성 설치"""
        if self.no_install:
            logger.info("--no-install 옵션이 지정되어 의존성 설치를 건너뜁니다.")
            return True
            
        logger.info("npm 의존성을 설치하는 중...")
        try:
            result = subprocess.run(
                "npm install",
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=300,  # 5분 타임아웃
                shell=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                logger.info("✅ npm 의존성 설치 완료")
                return True
            else:
                logger.error(f"npm install 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("npm install 시간 초과 (5분)")
            return False
        except Exception as e:
            logger.error(f"npm install 중 오류 발생: {e}")
            return False
    
    def check_build_files(self):
        """빌드 파일 상태 확인"""
        dist_dir = self.base_dir / "dist"
        
        if not dist_dir.exists():
            logger.error("❌ dist 디렉토리가 존재하지 않습니다.")
            return False
        
        # 필수 파일들 확인
        index_html = dist_dir / "index.html"
        if not index_html.exists():
            logger.error("❌ index.html 파일이 존재하지 않습니다.")
            return False
        
        # 빌드된 파일들 개수 확인
        build_files = list(dist_dir.rglob('*'))
        build_files = [f for f in build_files if f.is_file()]
        
        logger.info(f"✅ 빌드 파일 확인 완료: {len(build_files)}개 파일")
        logger.info(f"   📁 빌드 디렉토리: {dist_dir}")
        logger.info(f"   📄 index.html: {'존재' if index_html.exists() else '없음'}")
        
        # assets 폴더 확인
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            asset_files = list(assets_dir.glob('*'))
            logger.info(f"   📦 Assets: {len(asset_files)}개 파일")
        
        return True

    def start_ui_server(self):
        """UI 서버 시작 (build 모드용 - 빌드된 정적 파일 제공)"""
        logger.info("🎨 UI 서버를 시작하는 중...")
        
        dist_dir = self.base_dir / "dist"
        if not dist_dir.exists():
            logger.error("빌드된 파일(dist 디렉토리)을 찾을 수 없습니다.")
            return False
        
        # 빌드 파일 상태 확인
        if not self.check_build_files():
            logger.error("빌드 파일 확인에 실패했습니다.")
            return False
        
        try:
            # 커스텀 SPA 핸들러를 사용한 HTTP 서버 실행
            def start_server():
                try:
                    # 핸들러에 디렉토리 정보와 백엔드 포트 전달
                    handler = lambda *args, **kwargs: SPAHandler(*args, directory=str(dist_dir), backend_port=self.port, **kwargs)
                    
                    # HTTP 서버 생성 (ui_port는 이미 할당 검증됨)
                    if self.ui_port is None:
                        raise ValueError("UI 포트가 할당되지 않았습니다.")
                    server = HTTPServer((self.host, self.ui_port), handler)
                    
                    logger.info(f"✅ UI 서버 시작됨")
                    logger.info(f"   🌐 로컬 접속: http://localhost:{self.ui_port}")
                    logger.info(f"   🌍 네트워크 접속: http://{self.local_ip}:{self.ui_port}")
                    logger.info(f"   📁 제공 디렉토리: {dist_dir}")
                    
                    # 서버 실행
                    server.serve_forever()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"UI 서버 실행 중 오류: {e}")
            
            # 별도 스레드에서 서버 실행
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            
            # 서버가 시작될 때까지 잠시 대기
            time.sleep(2)
            
            # 프로세스 객체 대신 스레드 정보 저장 (종료 처리를 위해)
            self.ui_server_thread = server_thread
            
            return True
            
        except Exception as e:
            logger.error(f"UI 서버 시작 실패: {e}")
            return False

    def build_frontend(self):
        """프론트엔드 빌드 (build 모드용)"""
        logger.info("🏗️ 프론트엔드를 빌드하는 중...")
        
        # 기존 dist 디렉토리 정리
        dist_dir = self.base_dir / "dist"
        if dist_dir.exists():
            logger.info("🗑️ 기존 빌드 파일을 정리하는 중...")
            shutil.rmtree(dist_dir)
        
        try:
            result = subprocess.run(
                "npm run build",
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=300,  # 5분 타임아웃
                shell=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                logger.info("✅ 프론트엔드 빌드 완료")
                
                # 빌드 결과 확인
                if dist_dir.exists():
                    build_files = list(dist_dir.rglob('*'))
                    build_files = [f for f in build_files if f.is_file()]
                    logger.info(f"📦 생성된 파일: {len(build_files)}개")
                
                # 빌드 출력이 있으면 표시
                if result.stdout and result.stdout.strip():
                    print(colorize_log("빌드 결과:", is_backend=False))
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            print(colorize_log(line.strip(), is_backend=False))
                return True
            else:
                logger.error("프론트엔드 빌드 실패:")
                if result.stderr:
                    print(result.stderr)
                if result.stdout:
                    print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("프론트엔드 빌드 시간 초과 (5분)")
            return False
        except Exception as e:
            logger.error(f"프론트엔드 빌드 중 오류 발생: {e}")
            return False
    
    def start_backend(self):
        """백엔드 서버 시작"""
        logger.info("🚀 백엔드 서버를 시작하는 중...")
        
        try:
            # uvicorn으로 FastAPI 서버 실행
            server_dir = self.base_dir / "server"
            
            # 개발 모드와 프로덕션 모드에 따라 다른 옵션 사용
            uvicorn_args = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--host", self.host, 
                "--port", str(self.port),
                "--log-level", "info"
            ]
            
            # 개발 모드에서만 --reload 옵션 추가
            if self.mode == 'dev':
                uvicorn_args.append("--reload")
            
            # 환경 변수 설정
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # 개발 모드에서만 --reload 옵션과 개발 모드 표시를 위한 환경 변수 설정
            if self.mode == 'dev':
                env['AUTOLABELING_MODE'] = 'development'
                logger.info("🔧 개발 모드 설정:")
                logger.info(f"   📁 데이터 디렉토리: server/uploaded_images (기본값)")
                logger.info(f"   🔄 자동 리로드: 활성화")
            else:
                # 빌드 모드는 명시적으로 운영 모드로 설정
                env['AUTOLABELING_MODE'] = 'production'
                logger.info("🏭 운영 모드 설정:")
                logger.info(f"   📁 데이터 디렉토리: server/uploaded_images (기본값)")
                logger.info(f"   🔄 자동 리로드: 비활성화")
            
            # 환경 변수 설정 확인 로그
            logger.info("=== 환경 변수 설정 확인 ===")
            logger.info(f"AUTOLABELING_MODE: {env.get('AUTOLABELING_MODE')}")
            logger.info("AUTOLABELING_DATA_DIR: 설정 안함 (config.py 기본값 사용)")
            logger.info("==========================")
            
            self.backend_process = subprocess.Popen(
                uvicorn_args,
                cwd=str(server_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                env=env  # 환경 변수 전달
            )
            
            # 백엔드 로그 출력을 위한 스레드
            def log_backend_output():
                try:
                    if self.backend_process and self.backend_process.stdout:
                        for line in iter(self.backend_process.stdout.readline, ''):
                            if self.running and line.strip():
                                print(colorize_log(line.strip(), is_backend=True))
                        self.backend_process.stdout.close()
                except Exception as e:
                    if self.running:
                        logger.error(f"백엔드 로그 출력 오류: {e}")
            
            backend_thread = threading.Thread(target=log_backend_output, daemon=True)
            backend_thread.start()
            
            # 로컬 IP와 함께 백엔드 서버 시작 로그 출력
            logger.info(f"✅ 백엔드 서버 시작됨")
            logger.info(f"   🌐 로컬 접속: http://localhost:{self.port}")
            logger.info(f"   🌍 네트워크 접속: http://{self.local_ip}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"백엔드 서버 시작 실패: {e}")
            return False
    
    def start_frontend(self):
        """프론트엔드 개발 서버 시작 (dev 모드용)"""
        logger.info("🎨 프론트엔드 개발 서버를 시작하는 중...")
        
        try:
            self.frontend_process = subprocess.Popen(
                "npm run dev",
                cwd=str(self.base_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                shell=True
            )
            
            # 프론트엔드 로그 출력을 위한 스레드
            def log_frontend_output():
                try:
                    if self.frontend_process and self.frontend_process.stdout:
                        for line in iter(self.frontend_process.stdout.readline, ''):
                            if self.running and line.strip():
                                print(colorize_log(line.strip(), is_backend=False))
                        self.frontend_process.stdout.close()
                except Exception as e:
                    if self.running:
                        logger.error(f"프론트엔드 로그 출력 오류: {e}")
            
            frontend_thread = threading.Thread(target=log_frontend_output, daemon=True)
            frontend_thread.start()
            
            logger.info("✅ 프론트엔드 개발 서버 시작됨")
            return True
            
        except Exception as e:
            logger.error(f"프론트엔드 서버 시작 실패: {e}")
            return False
    
    def wait_for_servers(self):
        """서버들이 실행되는 동안 대기"""
        logger.info("\n" + "="*70)
        if self.mode == 'dev':
            logger.info("🎉 개발 서버들이 실행 중입니다!")
            logger.info("="*70)
            logger.info("🔧 개발 환경 설정:")
            logger.info(f"   📁 데이터 디렉토리: server/uploaded_images")
            logger.info(f"   🔄 자동 리로드: 활성화 (코드 변경 시 자동 재시작)")
            logger.info("")
            logger.info(f"📚 백엔드 API 문서:")
            logger.info(f"   🌐 로컬: http://localhost:{self.port}/docs")
            logger.info(f"   🌍 네트워크: http://{self.local_ip}:{self.port}/docs")
            logger.info("🌐 프론트엔드: 자동으로 브라우저에서 열림 (일반적으로 http://localhost:5173)")
        else:
            logger.info("🚀 운영 서버가 실행 중입니다!")
            logger.info("="*70)
            logger.info("🏭 운영 환경 설정:")
            logger.info(f"   📁 데이터 디렉토리: server/uploaded_images")
            logger.info(f"   🔄 자동 리로드: 비활성화 (안정성 우선)")
            logger.info("")
            logger.info(f"📚 백엔드 API 문서:")
            logger.info(f"   🌐 로컬: http://localhost:{self.port}/docs")
            logger.info(f"   🌍 네트워크: http://{self.local_ip}:{self.port}/docs")
            if self.ui_port:
                logger.info(f"🌐 UI 화면 (SPA 라우팅 지원):")
                logger.info(f"   🌐 로컬: http://localhost:{self.ui_port}")
                logger.info(f"   🌍 네트워크: http://{self.local_ip}:{self.ui_port}")
            logger.info(f"🔗 통합 API:")
            logger.info(f"   🌐 로컬: http://localhost:{self.port}")
            logger.info(f"   🌍 네트워크: http://{self.local_ip}:{self.port}")
        
        logger.info("="*70)
        logger.info("📋 참고사항:")
        logger.info("   • 개발 모드와 운영 모드가 동일한 데이터 디렉토리를 공유합니다")
        logger.info("   • 개발 모드에서는 자동 리로드로 코드 변경이 즉시 반영됩니다")
        logger.info("="*70)
        logger.info("종료하려면 Ctrl+C를 누르세요")
        logger.info("="*70)
        
        try:
            while self.running:
                # 프로세스 상태 확인
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("백엔드 서버가 예기치 않게 종료되었습니다.")
                    break
                    
                if self.mode == 'dev' and self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("프론트엔드 서버가 예기치 않게 종료되었습니다.")
                    break
                
                # UI 서버는 스레드로 실행되므로 스레드 상태 확인
                if (self.mode == 'build' and hasattr(self, 'ui_server_thread') and 
                    not self.ui_server_thread.is_alive()):
                    logger.error("UI 서버 스레드가 예기치 않게 종료되었습니다.")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nCtrl+C 감지. 서버들을 종료하는 중...")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """서버들 종료"""
        self.running = False
        
        # 포트 락 해제
        if hasattr(self, 'port'):
            self.unlock_port(self.port)
        if hasattr(self, 'ui_port') and self.ui_port:
            self.unlock_port(self.ui_port)
        
        if self.frontend_process:
            logger.info("프론트엔드 서버를 종료하는 중...")
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                logger.info("✅ 프론트엔드 서버 종료됨")
            except subprocess.TimeoutExpired:
                logger.warning("프론트엔드 서버 강제 종료")
                self.frontend_process.kill()
            except Exception as e:
                logger.error(f"프론트엔드 서버 종료 오류: {e}")
        
        # UI 서버는 스레드로 실행되므로 따로 종료 처리 (데몬 스레드라 자동 종료됨)
        if hasattr(self, 'ui_server_thread'):
            logger.info("UI 서버를 종료하는 중...")
            logger.info("✅ UI 서버 종료됨")
        
        if self.backend_process:
            logger.info("백엔드 서버를 종료하는 중...")
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                logger.info("✅ 백엔드 서버 종료됨")
            except subprocess.TimeoutExpired:
                logger.warning("백엔드 서버 강제 종료")
                self.backend_process.kill()
            except Exception as e:
                logger.error(f"백엔드 서버 종료 오류: {e}")
    
    def run(self):
        """메인 실행 함수"""
        print("\n" + "="*70)
        if self.mode == 'dev':
            print("🚀 Iljoo AutoLabeling 개발 환경을 시작합니다...")
        else:
            print("🚀 Iljoo AutoLabeling 운영 환경을 시작합니다...")
        print("="*70)
        print(f"모드: {self.mode.upper()}")
        print(f"호스트: {self.host}")
        print(f"실제 IP: {self.local_ip}")
        print(f"백엔드 포트: {self.port}")
        print(f"데이터 디렉토리: server/uploaded_images")
        if self.mode == 'build':
            print(f"UI 포트: {self.ui_port if self.ui_port else '자동 할당'}")
        print("="*70)
        
        # 포트 할당
        if not self.assign_ports():
            logger.error("포트 할당에 실패했습니다. 종료합니다.")
            return False
        
        # 최종 할당된 포트 정보 출력
        print(f"✅ 할당된 백엔드 포트: {self.port}")
        if self.mode == 'build':
            print(f"✅ 할당된 UI 포트: {self.ui_port}")
        print(f"✅ 네트워크 IP: {self.local_ip}")
        print("="*70)
        
        # 필수 조건 확인
        if not self.check_prerequisites():
            logger.error("필수 조건이 충족되지 않았습니다. 종료합니다.")
            return False
        
        # npm 의존성 확인 및 설치
        node_modules = self.base_dir / "node_modules"
        if not node_modules.exists() and not self.no_install:
            logger.info("node_modules가 없습니다. 의존성을 설치합니다...")
            if not self.install_dependencies():
                logger.error("의존성 설치에 실패했습니다. 종료합니다.")
                return False
        elif self.no_install:
            logger.info("--no-install 옵션으로 의존성 설치를 건너뜁니다.")
        
        # 빌드 모드인 경우 프론트엔드 빌드
        if self.mode == 'build':
            if not self.build_frontend():
                logger.error("프론트엔드 빌드에 실패했습니다.")
                return False
        
        # 백엔드 서버 시작
        if not self.start_backend():
            logger.error("백엔드 서버 시작에 실패했습니다.")
            return False
        
        # 잠시 대기 (백엔드가 완전히 시작될 때까지)
        time.sleep(3)
        
        # 개발 모드인 경우에만 프론트엔드 개발 서버 시작
        if self.mode == 'dev':
            if not self.start_frontend():
                logger.error("프론트엔드 서버 시작에 실패했습니다.")
                self.shutdown()
                return False
        # 빌드 모드인 경우 UI 서버 시작
        elif self.mode == 'build':
            if not self.start_ui_server():
                logger.error("UI 서버 시작에 실패했습니다.")
                self.shutdown()
                return False
        
        # 서버들이 실행되는 동안 대기
        self.wait_for_servers()
        
        logger.info("👋 서버들이 모두 종료되었습니다.")
        return True

def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="Iljoo AutoLabeling 서버 실행 스크립트",
        epilog="""
예시:
  python run.py                       # 개발 모드로 실행 (포트: 8000, 데이터: server/uploaded_images)
  python run.py dev                   # 개발 모드로 실행 (포트: 8000, 데이터: server/uploaded_images)
  python run.py build                 # 빌드 모드로 실행 (포트: 8000, 데이터: server/uploaded_images)
  python run.py build --ui-port 3000  # UI 포트 3000으로 빌드 모드 실행
  python run.py dev --port 9000       # 포트 9000으로 개발 모드 실행
  python run.py build --port 9000     # 포트 9000으로 빌드 모드 실행
  python run.py build --no-install    # 의존성 설치 없이 빌드 모드 실행

개발/운영 환경 설정:
  - 개발 모드: 자동 리로드, server/uploaded_images 디렉토리 사용
  - 빌드 모드: 운영용, server/uploaded_images 디렉토리 사용
  - 두 모드 모두 동일한 디렉토리를 사용하며, 개발 모드에서는 자동 리로드 제공
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'mode',
        nargs='?',
        choices=['dev', 'build'],
        default='dev',
        help='실행 모드 (기본값: dev)'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='백엔드 서버 호스트 (기본값: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='백엔드 서버 포트 (기본값: 8000)'
    )
    
    parser.add_argument(
        '--ui-port',
        type=int,
        help='UI 서버 포트 (build 모드용, 기본값: 자동 할당)'
    )
    
    parser.add_argument(
        '--no-install',
        action='store_true',
        help='npm install을 건너뜁니다'
    )
    
    return parser.parse_args()

def main():
    """메인 함수"""
    try:
        args = parse_arguments()
        
        manager = DevServerManager(
            mode=args.mode,
            host=args.host,
            port=args.port,
            ui_port=args.ui_port,
            no_install=args.no_install
        )
        
        success = manager.run()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("실행이 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"예기치 않은 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 