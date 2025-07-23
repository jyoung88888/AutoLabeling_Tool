import { ref } from 'vue'
import { API_SERVER } from '@/utils/config.js'

export function useProjectManagement() {
  // State
  const projectPath = ref('')
  const projectList = ref([])
  const isLoadingProject = ref(false)

  // Methods
  const onProjectLoaded = (data) => {
    console.log('프로젝트 로드됨:', data)
    projectPath.value = data.projectPath || ''
  }

  const onProjectLoading = () => {
    console.log('프로젝트 로딩 중...')
    isLoadingProject.value = true
  }

  const onProjectError = (error) => {
    console.error('프로젝트 오류:', error)
    isLoadingProject.value = false
  }

  const onClassesUpdated = (classes) => {
    console.log('클래스 업데이트됨:', classes)
  }

  const onResultsUpdated = (results) => {
    console.log('결과 업데이트됨:', results.length, '개 이미지')
    isLoadingProject.value = false
  }

  const loadSelectedProject = async (projectName) => {
    try {
      isLoadingProject.value = true
      console.log('프로젝트 로드 시작:', projectName)

      // 백엔드 API 호출
      const response = await fetch(`${API_SERVER}/api/load-project`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectName: projectName
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `프로젝트 로드 실패 (${response.status})`)
      }

      const data = await response.json()
      console.log('프로젝트 로드 성공:', data)

      return {
        success: true,
        projectName: data.projectName,
        projectPath: data.projectPath,
        results: data.results,
        classes: data.classes,
        totalImages: data.totalImages,
        lowConfidenceImages: data.lowConfidenceImages || [],
        projectInfo: data.projectInfo
      }
    } catch (error) {
      console.error('프로젝트 로드 오류:', error)
      isLoadingProject.value = false
      throw error
    }
  }

  const closeLoadProjectDialog = () => {
    console.log('프로젝트 다이얼로그 닫기')
  }

  const handleProjectSaveComplete = (saveResult) => {
    console.log('프로젝트 저장 완료:', saveResult)

    // 저장 완료 후 화면 초기화 신호 반환
    return {
      shouldReset: true,
      message: saveResult.message || '프로젝트가 성공적으로 저장되었습니다.',
      success: saveResult.success || true
    }
  }

  return {
    // State
    projectPath,
    projectList,
    isLoadingProject,

    // Methods
    onProjectLoaded,
    onProjectLoading,
    onProjectError,
    onClassesUpdated,
    onResultsUpdated,
    loadSelectedProject,
    closeLoadProjectDialog,
    handleProjectSaveComplete
  }
}
