import axios from 'axios'

/**
 * 폴더 선택 다이얼로그의 기본 경로를 가져옵니다.
 * @returns {Promise<Object>} 서버에서 제공하는 기본 경로 정보
 */
export async function selectFolder() {
  try {
    console.log('폴더 선택 API 호출 중...');
    const response = await axios.get('/api/select-folder', {
      headers: {
        'Accept': 'application/json'
      },
      responseType: 'text',  // 문자열로 응답을 받아 수동으로 처리
      timeout: 10000  // 10초 타임아웃 설정
    })

    // 응답 형식 검사
    if (!response.data) {
      console.error('서버 응답이 비어있습니다.');
      return {
        success: false,
        message: '서버에서 응답을 받지 못했습니다.'
      }
    }

    // 데이터 처리
    let data = response.data

    // response.data가 문자열인 경우 JSON 파싱 시도
    if (typeof data === 'string') {
      try {
        data = JSON.parse(data)
      } catch (e) {
        console.error('JSON 파싱 실패:', e, data.substr(0, 100))
        return {
          success: false,
          message: '서버 응답을 처리할 수 없습니다: 잘못된 형식',
          rawData: data.substr(0, 100)
        }
      }
    }

    // 응답이 성공/실패 상태를 포함하는지 확인
    if (!('success' in data)) {
      // 레거시 API와의 호환성을 위해 path 키만 있는 경우 처리
      if ('path' in data) {
        return {
          success: true,
          path: data.path
        }
      }

      return {
        success: false,
        message: '서버 응답에 성공/실패 정보가 없습니다.'
      }
    }

    // 성공적인 응답 로깅
    if (data.success) {
      console.log('폴더 선택 API 응답 성공:', data.path || '(경로 정보 없음)');
    }

    return data
  } catch (error) {
    console.error('폴더 선택 경로를 가져오는 중 오류 발생:', error)

    // API 오류 상세 정보 로깅
    let errorMessage = '서버 연결 오류'
    if (error.response) {
      errorMessage = `서버 오류: ${error.response.status} - ${error.response.data?.message || error.response.statusText || '알 수 없는 오류'}`
      console.error('서버 응답 상태:', error.response.status)
      console.error('서버 응답 데이터:', error.response.data)
    } else if (error.request) {
      errorMessage = '서버 응답이 없습니다. 네트워크 연결을 확인하세요.'
      console.error('요청은 전송되었지만 응답이 없음:', error.request)
    } else {
      errorMessage = `요청 오류: ${error.message}`
      console.error('요청 전송 중 오류:', error.message)
    }

    return {
      success: false,
      message: errorMessage
    }
  }
}

/**
 * 지정된 경로의 폴더 목록을 조회합니다.
 * @param {string} path - 조회할 경로 (옵션, 기본값 root 경로)
 * @returns {Promise<Object>} 경로의 디렉토리 목록 정보
 */
export async function browseFolders(path = null) {
  try {
    let url = '/api/browse-folders'
    if (path) {
      url += `?path=${encodeURIComponent(path)}`
    }

    console.log(`폴더 목록 요청: ${url}`)

    const response = await axios.get(url, {
      headers: {
        'Accept': 'application/json'
      },
      responseType: 'text',  // 문자열로 응답을 받아 수동으로 처리
      timeout: 10000  // 10초 타임아웃 설정
    })

    // 응답 형식 검사
    if (!response.data) {
      console.error('서버 응답이 비어있습니다.')
      return {
        success: false,
        message: '서버에서 응답을 받지 못했습니다.',
        directories: [],
        files: []
      }
    }

    // 데이터 처리
    let data = response.data

    // response.data가 문자열인 경우 JSON 파싱 시도
    if (typeof data === 'string') {
      try {
        // 응답 내용 로깅
        console.log('서버 응답 (처음 100자):', data.substr(0, 100))

        data = JSON.parse(data)
      } catch (e) {
        console.error('JSON 파싱 실패:', e)
        console.error('원본 데이터 (처음 100자):', data.substr(0, 100))
        return {
          success: false,
          message: '서버 응답을 처리할 수 없습니다: 잘못된 형식',
          rawData: data.substr(0, 100),
          directories: [],
          files: []
        }
      }
    }

    // 응답이 성공/실패 상태를 포함하는지 확인
    if (!('success' in data)) {
      console.error('서버 응답에 success 필드가 없습니다:', data)

      // 필요한 정보가 있는지 확인하여 호환성 유지
      if ('directories' in data && Array.isArray(data.directories)) {
        return {
          success: true,
          directories: data.directories,
          current_path: data.current_path || path || '/',
          parent_path: data.parent_path,
          files: data.files || []
        }
      }

      return {
        success: false,
        message: '서버 응답에 성공/실패 정보가 없습니다.',
        directories: [],
        files: []
      }
    }

    // 성공했지만 내용이 이상한 경우 체크
    if (data.success) {
      if (!data.directories || !Array.isArray(data.directories)) {
        console.warn('서버 응답에 directories 배열이 없습니다:', data)
        data.directories = []
      }

      if (!data.files || !Array.isArray(data.files)) {
        console.warn('서버 응답에 files 배열이 없습니다:', data)
        data.files = []
      }

      // 메시지가 있으면 로깅
      if (data.message) {
        console.log(`서버 메시지: ${data.message}`);
      }
    }

    console.log(`폴더 목록 결과: 디렉토리 ${data.directories?.length || 0}개, 파일 ${data.files?.length || 0}개`)
    return data
  } catch (error) {
    console.error('폴더 목록을 가져오는 중 오류 발생:', error)

    // 더 자세한 오류 정보 제공
    let errorMessage = '서버 연결 오류'
    if (error.response) {
      errorMessage = `서버 오류 (${error.response.status}): ${error.response.data?.message || error.response.statusText || '알 수 없는 오류'}`
      console.error('서버 응답 상태:', error.response.status)
      console.error('서버 응답 데이터:', error.response.data)
    } else if (error.request) {
      errorMessage = '서버 응답이 없습니다. 네트워크 연결을 확인하세요.'
      console.error('요청은 전송되었지만 응답이 없음:', error.request)
    } else {
      errorMessage = `요청 오류: ${error.message}`
      console.error('요청 전송 중 오류:', error.message)
    }

    return {
      success: false,
      message: errorMessage,
      directories: [],
      files: []
    }
  }
}
