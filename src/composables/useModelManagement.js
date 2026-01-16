import { ref } from 'vue'
import { API_SERVER } from '@/utils/config'

export function useModelManagement() {
  // State
  const models = ref([])
  const selectedModelType = ref(null)
  const selectedModel = ref(null)
  const modelDetails = ref([])
  const modelLoaded = ref(false)
  const modelStatusMessage = ref('')
  const modelStatusSuccess = ref(false)
  const deviceInfo = ref(['알 수 없음'])
  const isLoadingModel = ref(false)
  const modelClasses = ref({})
  const supportsTextPrompt = ref(false)  // Grounding DINO 등 텍스트 프롬프트 지원 여부

  // Methods
  const refreshModels = async () => {
    try {
      const response = await fetch(`${API_SERVER}/models/`)
      if (!response.ok) throw new Error('서버 응답 오류')
      const data = await response.json()

      console.log('서버 응답 데이터:', data)

      // 안전한 모델 목록 처리
      if (!data || !data.models) {
        console.warn('모델 데이터가 없습니다:', data)
        models.value = []
        selectedModelType.value = null
        selectedModel.value = null
        modelDetails.value = []
        return
      }

      if (data.models && typeof data.models === 'object' && !Array.isArray(data.models)) {
        // 객체 형태의 모델 데이터인 경우
        const modelKeys = Object.keys(data.models)
        if (modelKeys.length === 0) {
          models.value = []
        } else {
          models.value = modelKeys.map(modelType => {
            const modelList = data.models[modelType]
            const count = Array.isArray(modelList) ? modelList.length : 0
            return {
              text: `${modelType} (${count}개 모델)`,
              value: modelType
            }
          })
        }
      } else if (Array.isArray(data.models)) {
        // 배열 형태의 모델 데이터인 경우
        models.value = data.models.map(model => ({
          text: model,
          value: model
        }))
      } else {
        // 예상하지 못한 형태인 경우
        console.warn('예상하지 못한 모델 데이터 형태:', data.models)
        models.value = []
      }

      selectedModelType.value = null
      selectedModel.value = null
      modelDetails.value = []

      console.log('모델 목록 새로고침 완료:', models.value)
    } catch (e) {
      console.error('모델 목록 새로고침 오류:', e)
      models.value = []
      selectedModelType.value = null
      selectedModel.value = null
      modelDetails.value = []
      alert(`모든 상태 정보 가져오기 실패. ${e.message}`)
    }
  }

    const fetchModelDetails = async (modelTypeData) => {
    // 매개변수가 전달되지 않은 경우 현재 선택된 모델 타입 사용
    const targetModelType = modelTypeData || selectedModelType.value

    console.log('fetchModelDetails 호출됨:', { targetModelType, selectedModelType: selectedModelType.value })

    if (!targetModelType || !targetModelType.value) {
      console.log('모델 타입이 선택되지 않았습니다. 상세 정보를 초기화합니다.')
      modelDetails.value = []
      selectedModel.value = null
      return
    }

    try {
      const modelType = targetModelType.value
      const apiUrl = `${API_SERVER}/models/${encodeURIComponent(modelType)}`

      console.log('모델 상세 정보 API 호출:', apiUrl)

      const response = await fetch(apiUrl)

      console.log('API 응답 상태:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('API 응답 오류:', response.status, errorText)
        throw new Error(`서버 응답 오류 (${response.status}): ${errorText}`)
      }

      const data = await response.json()

      console.log('모델 상세 정보 응답 데이터:', data)

      // 안전한 모델 상세 정보 처리
      if (!data || data.details === undefined) {
        console.warn('모델 상세 정보가 없습니다:', data)
        modelDetails.value = []
        selectedModel.value = null
        return
      }

      if (Array.isArray(data.details)) {
        if (data.details.length === 0) {
          console.log(`모델 타입 '${modelType}'에 사용 가능한 모델이 없습니다.`)
          modelDetails.value = []
        } else {
          modelDetails.value = data.details.map(detail => ({
            text: detail,
            value: detail
          }))
          console.log(`모델 타입 '${modelType}'에서 ${data.details.length}개의 모델을 발견했습니다:`, data.details)
        }
      } else {
        console.warn('예상하지 못한 모델 상세 정보 형태:', data.details)
        modelDetails.value = []
      }

      selectedModel.value = null
    } catch (e) {
      console.error('모델 상세 정보 가져오기 오류:', e)
      modelDetails.value = []
      selectedModel.value = null
      alert(`모델 상세 정보 가져오기 실패: ${e.message}`)
    }
  }

  const loadModel = async () => {
    try {
      if (!selectedModelType.value || !selectedModel.value) {
        throw new Error('모델 경로가 선택되지 않았습니다.')
      }

      const modelPath = `${selectedModelType.value.value}/${selectedModel.value.value}`
      const cleanPath = modelPath.trim()

      console.log('모델 로드 시작:', cleanPath)
      modelStatusSuccess.value = false
      modelStatusMessage.value = '모델을 로드하는 중...'
      isLoadingModel.value = true

      const response = await fetch(`${API_SERVER}/models/load/${encodeURIComponent(cleanPath)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `모델 로드 실패: ${response.status}`)
      }

      const data = await response.json()

      modelLoaded.value = true
      modelStatusSuccess.value = true

      // 텍스트 프롬프트 지원 여부 확인 (Grounding DINO 등)
      supportsTextPrompt.value = data.supports_text_prompt || false
      console.log('텍스트 프롬프트 지원:', supportsTextPrompt.value)

      // 장치 정보 업데이트
      if (data.device_info) {
        deviceInfo.value = Array.isArray(data.device_info) ? data.device_info : [data.device_info]
      }

      console.log('모델 로드 성공:', data)

      // 텍스트 프롬프트 지원 모델이 아닌 경우에만 클래스 정보 로드
      if (!supportsTextPrompt.value) {
        await loadModelClasses()
        // 클래스 개수 포함한 성공 메시지
        const classCount = Object.keys(modelClasses.value).length
        modelStatusMessage.value = `모델 로드 완료: ${cleanPath} (${classCount}개 클래스, YOLO ID 순서)`
        console.log(`✅ 모델 로드 및 클래스 정보 로드 완료: ${classCount}개 클래스 (사이드바와 저장 시 순서 동일)`)
      } else {
        // 텍스트 프롬프트 지원 모델
        modelStatusMessage.value = `모델 로드 완료: ${cleanPath} (텍스트 프롬프트 지원)`
        modelClasses.value = {}  // 클래스 정보 초기화
        console.log(`✅ 텍스트 프롬프트 지원 모델 로드 완료`)
      }

    } catch (error) {
      console.error('모델 로드 오류:', error)
      modelLoaded.value = false
      modelStatusSuccess.value = false
      modelStatusMessage.value = `모델 로드 실패: ${error.message}`
      modelClasses.value = {}
    } finally {
      isLoadingModel.value = false
    }
  }

    const loadModelClasses = async () => {
    try {
      console.log('=== YOLO 모델 클래스 정보 로드 시작 (ID 포함) ===')

      // 새로운 API 엔드포인트 사용 (ID 정보 포함)
      const response = await fetch(`${API_SERVER}/model/classes-with-ids`)

      if (response.ok) {
        const data = await response.json()

        if (data.success && data.classes && Array.isArray(data.classes)) {
          console.log(`서버에서 받은 클래스 정보: ${data.total}개`)

          // 클래스 정보를 딕셔너리 형태로 변환 (기존 호환성 유지)
          const classesDict = {}
          data.classes.forEach(cls => {
            classesDict[cls.id] = cls.name
          })

          console.log('✅ YOLO 모델 클래스 정보 (프로젝트 저장과 동일한 순서):')
          data.classes.forEach(cls => {
            console.log(`  ID ${cls.id}: '${cls.name}'`)
          })

          modelClasses.value = classesDict
          console.log('✅ 모델 클래스 정보 로드 완료 - 사이드바와 저장 시 순서 완전 일치')

        } else {
          console.warn('유효한 클래스 정보가 없습니다:', data)
          modelClasses.value = {}
        }
      } else {
        // fallback: 기존 API 사용
        console.warn('새로운 API 실패, 기존 API로 fallback:', response.status)
        const fallbackResponse = await fetch(`${API_SERVER}/model/classes`)

        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json()
          const classes = fallbackData.classes || {}

          console.log('Fallback - 서버에서 받은 클래스 정보:', classes)

          if (typeof classes === 'object' && Object.keys(classes).length > 0) {
            const sortedEntries = Object.entries(classes)
              .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))

            console.log('✅ Fallback - YOLO 모델 클래스 정보 (ID 순서):')
            sortedEntries.forEach(([id, name]) => {
              console.log(`  ID ${id}: '${name}'`)
            })

            modelClasses.value = classes
            console.log('✅ Fallback - 모델 클래스 정보 로드 완료')
          } else {
            console.warn('Fallback - 유효한 클래스 정보가 없습니다:', classes)
            modelClasses.value = {}
          }
        } else {
          const errorText = await fallbackResponse.text()
          console.warn('Fallback API도 실패:', fallbackResponse.status, errorText)
          modelClasses.value = {}
        }
      }
    } catch (error) {
      console.error('모델 클래스 정보 로드 오류:', error)
      modelClasses.value = {}
    }
  }

  return {
    // State
    models,
    selectedModelType,
    selectedModel,
    modelDetails,
    modelLoaded,
    modelStatusMessage,
    modelStatusSuccess,
    deviceInfo,
    isLoadingModel,
    modelClasses,
    supportsTextPrompt,

    // Methods
    refreshModels,
    fetchModelDetails,
    loadModel,
    loadModelClasses
  }
}
