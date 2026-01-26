import { ref, computed, watch } from 'vue'

export function useImageManagement() {
  // State
  const uploadedImages = ref([])
  const imageStatusMessage = ref('')
  const imageStatusSuccess = ref(false)
  const availableClasses = ref([])
  const selectedClasses = ref({})
  const selectAllClasses = ref(false)
  const showClassChangeAlert = ref(false)
  const classChangeMessage = ref('')
  const classSelectionApplied = ref(false)
  const classesFromModel = ref(false) // 클래스가 모델에서 왔는지 여부

  // Computed
  const allClassesSelected = computed(() => {
    const classes = availableClasses.value
    if (classes.length === 0) return false
    return classes.every(cls => selectedClasses.value[cls])
  })

  const selectedClassesInfo = computed(() => {
    const selected = Object.keys(selectedClasses.value).filter(key => selectedClasses.value[key])
    return {
      count: selected.length,
      names: selected
    }
  })

  const canStartLabeling = computed(() => {
    const hasImages = uploadedImages.value.length > 0
    const hasClasses = availableClasses.value.length > 0
    const hasSelectedClasses = Object.values(selectedClasses.value).some(selected => selected) || selectAllClasses.value
    const isApplied = classSelectionApplied.value

    return hasImages && hasClasses && hasSelectedClasses && isApplied
  })

  // Methods
  const handleFileUpload = (eventOrFiles) => {
    // event 객체인지 파일 배열인지 확인
    let files
    if (eventOrFiles && eventOrFiles.target && eventOrFiles.target.files) {
      // event 객체인 경우
      files = Array.from(eventOrFiles.target.files)
    } else if (Array.isArray(eventOrFiles)) {
      // 파일 배열인 경우
      files = eventOrFiles
    } else {
      console.error('잘못된 파일 업로드 데이터:', eventOrFiles)
      imageStatusSuccess.value = false
      imageStatusMessage.value = '파일 업로드에 실패했습니다.'
      return
    }

    uploadedImages.value = files
    imageStatusSuccess.value = true
    imageStatusMessage.value = `${files.length}개 이미지가 업로드되었습니다.`
    console.log(`업로드된 파일 개수: ${files.length}`)

    // 기존에 availableClasses가 있고 모델에서 온 경우 (모델에서 로드된 클래스 정보) 유지
    // 모델 클래스 정보가 없는 경우에만 이미지에서 클래스 추출
    if (availableClasses.value.length === 0 || !classesFromModel.value) {
      // Extract unique classes from uploaded images
      const classSet = new Set()
      files.forEach(file => {
        if (file.classes && Array.isArray(file.classes)) {
          file.classes.forEach(cls => classSet.add(cls))
        }
      })

      const extractedClasses = Array.from(classSet).sort()
      if (extractedClasses.length > 0) {
        availableClasses.value = extractedClasses
        classesFromModel.value = false // 이미지에서 추출된 클래스임을 표시
        initializeSelectedClasses()
      }
    } else {
      // 기존 클래스 정보가 있는 경우 선택 상태만 초기화 (클래스 목록은 유지)
      console.log('기존 모델 클래스 정보 유지:', availableClasses.value)
      // 선택 상태는 유지하되, 새로운 클래스가 있다면 선택 상태를 false로 초기화
      const currentSelectedClasses = { ...selectedClasses.value }
      availableClasses.value.forEach(cls => {
        if (!(cls in currentSelectedClasses)) {
          currentSelectedClasses[cls] = false
        }
      })
      selectedClasses.value = currentSelectedClasses
    }
  }

  const clearUploadedFiles = () => {
    uploadedImages.value = []
    imageStatusMessage.value = ''
    imageStatusSuccess.value = false
    selectAllClasses.value = false
    classSelectionApplied.value = false

    // 모델 클래스 정보가 있는 경우 유지, 없는 경우에만 초기화
    if (availableClasses.value.length > 0 && classesFromModel.value) {
      // 모델에서 온 클래스 정보는 유지하되 선택 상태만 초기화
      initializeSelectedClasses()
    } else {
      // 이미지에서 추출된 클래스이거나 클래스가 없는 경우 모두 초기화
      availableClasses.value = []
      selectedClasses.value = {}
      classesFromModel.value = false
    }
  }

  const initializeSelectedClasses = () => {
    const newSelectedClasses = {}
    availableClasses.value.forEach(cls => {
      newSelectedClasses[cls] = false
    })
    selectedClasses.value = newSelectedClasses
    selectAllClasses.value = false
  }

  const toggleAllClasses = () => {
    const newValue = !selectAllClasses.value
    console.log('toggleAllClasses 호출됨, 새 값:', newValue)

    selectAllClasses.value = newValue

    // 새로운 selectedClasses 객체 생성
    const newSelectedClasses = {}
    availableClasses.value.forEach(cls => {
      newSelectedClasses[cls] = newValue
    })
    selectedClasses.value = newSelectedClasses

    console.log('토글 완료 - selectAllClasses:', selectAllClasses.value)
    console.log('토글 완료 - selectedClasses:', selectedClasses.value)
  }

    const selectAllClassesChanged = (value) => {
    console.log('selectAllClassesChanged 호출됨:', value)
    console.log('현재 selectAllClasses:', selectAllClasses.value)
    console.log('현재 selectedClasses:', selectedClasses.value)

    // UI에서 이미 selectAllClasses와 selectedClasses를 업데이트했으므로
    // 여기서는 추가 로직이나 검증만 수행
    console.log('모든 클래스 선택 상태 변경 완료')
  }

  const checkSelectedClasses = () => {
    const selectedCount = Object.values(selectedClasses.value).filter(Boolean).length
    const isSelectAllChecked = selectAllClasses.value

    console.log('checkSelectedClasses - 선택된 개수:', selectedCount, '모든 클래스 선택:', isSelectAllChecked)

    // "모든 클래스"가 선택되어 있거나, 개별 클래스가 하나라도 선택되어 있으면 유효
    if (selectedCount === 0 && !isSelectAllChecked) {
      showClassChangeAlert.value = true
      classChangeMessage.value = '최소 하나의 클래스를 선택해야 합니다.'
      return false
    }

    return true
  }

  const applyClassSelection = () => {
    console.log('applyClassSelection 호출됨')
    console.log('현재 상태:', {
      selectAllClasses: selectAllClasses.value,
      selectedClasses: selectedClasses.value,
      selectedClassesInfo: selectedClassesInfo.value
    })

    if (!checkSelectedClasses()) return

    classSelectionApplied.value = true
    showClassChangeAlert.value = false

    // "모든 클래스" 선택 시와 개별 클래스 선택 시를 구분하여 메시지 표시
    if (selectAllClasses.value) {
      imageStatusMessage.value = `모든 클래스(${availableClasses.value.length}개)가 선택되었습니다`
    } else {
      imageStatusMessage.value = `${selectedClassesInfo.value.count}개 클래스가 선택되었습니다`
    }

    console.log('클래스 선택 적용 완료:', imageStatusMessage.value)
  }

  const dismissClassChangeAlert = () => {
    showClassChangeAlert.value = false
  }

  const handleClassSelectionChanged = () => {
    // 선택이 변경되면 적용 상태를 해제
    classSelectionApplied.value = false
  }

      const updateAvailableClassesFromModel = (modelClassesData) => {
    console.log('=== 사이드바 클래스 선택 UI 업데이트 시작 ===')
    console.log('받은 모델 클래스 데이터:', modelClassesData)
    console.log('데이터 타입:', typeof modelClassesData)

    let classNames = []

    if (Array.isArray(modelClassesData)) {
      // 배열 형태의 클래스 정보 (서버에서 변환된 형태)
      classNames = modelClassesData.filter(cls => cls && typeof cls === 'string')
      console.log('✅ 배열 형태의 클래스 정보 처리:', classNames)
    } else if (modelClassesData && typeof modelClassesData === 'object') {
      // 객체 형태의 클래스 정보 {0: 'person', 1: 'bicycle', ...}
      const sortedEntries = Object.entries(modelClassesData)
        .filter(entry => entry[1] && typeof entry[1] === 'string')
        .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))

      classNames = sortedEntries.map(entry => entry[1])

      console.log('✅ 객체 형태의 클래스 정보 처리 (YOLO ID 순서 - 프로젝트 저장과 동일):')
      sortedEntries.forEach(([id, name]) => {
        console.log(`  사이드바 표시 순서 ${sortedEntries.findIndex(e => e[0] === id)}: ID ${id} -> '${name}'`)
      })
      console.log('사이드바 최종 클래스 순서:', classNames)
    }

    if (classNames.length > 0) {
      console.log(`🎯 사이드바 클래스 선택 UI에 ${classNames.length}개 클래스 적용 중...`)
      availableClasses.value = classNames
      classesFromModel.value = true // 모델에서 온 클래스임을 표시
      initializeSelectedClasses()
      console.log('✅ 사이드바 클래스 선택 UI 업데이트 완료')
      console.log('🔗 이 순서는 프로젝트 저장 시 yolo_test2_info.json과 완전히 동일합니다')
      console.log('사이드바 표시 클래스 목록:', classNames)
      return
    }

    // 모델 클래스 정보가 없거나 올바르지 않은 경우
    console.warn('❌ 유효하지 않은 모델 클래스 데이터:', modelClassesData)
    classesFromModel.value = false
  }

  // Watchers
  watch(selectedClasses, (newVal) => {
    const selectedCount = Object.values(newVal).filter(Boolean).length
    const totalCount = availableClasses.value.length

    if (selectedCount === 0) {
      selectAllClasses.value = false
    } else if (selectedCount === totalCount) {
      selectAllClasses.value = true
    } else {
      selectAllClasses.value = false
    }
  }, { deep: true })

  return {
    // State
    uploadedImages,
    imageStatusMessage,
    imageStatusSuccess,
    availableClasses,
    selectedClasses,
    selectAllClasses,
    showClassChangeAlert,
    classChangeMessage,
    classSelectionApplied,
    classesFromModel,

    // Computed
    allClassesSelected,
    selectedClassesInfo,
    canStartLabeling,

    // Methods
    handleFileUpload,
    clearUploadedFiles,
    initializeSelectedClasses,
    toggleAllClasses,
    selectAllClassesChanged,
    checkSelectedClasses,
    applyClassSelection,
    dismissClassChangeAlert,
    handleClassSelectionChanged,
    updateAvailableClassesFromModel
  }
}
