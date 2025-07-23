import { ref, computed } from 'vue'

export function useLowConfidenceImages() {
  // State
  const rawLowConfidenceImages = ref([])
  const lowConfidenceThreshold = ref(0.5)

  // Computed
  const lowConfidenceImages = computed(() => {
    return rawLowConfidenceImages.value.map(img => ({
      ...img,
      displayIndex: img.index || 0
    }))
  })

  // Methods
  const rebuildLowConfidenceImages = (results) => {
    console.log('=== 저신뢰도 이미지 정보 재구성 시작 ===')
    console.log('현재 results 개수:', results.length)

    // 기존 저신뢰도 정보 초기화
    rawLowConfidenceImages.value = []

    // 모든 결과에 대해 저신뢰도 박스 재검사
    let lowConfidenceCount = 0
    results.forEach((result, index) => {
      console.log(`재구성 [${index + 1}/${results.length}]: ${result.filename}`)

      if (result.boxes && result.boxes.length > 0) {
        const lowConfidenceBoxes = result.boxes.filter(box =>
          box.confidence < lowConfidenceThreshold.value
        )

        if (lowConfidenceBoxes.length > 0) {
          lowConfidenceCount++

          // 신뢰도 정보를 문자열로 포맷팅
          const avgConfidence = lowConfidenceBoxes.reduce((sum, box) => sum + box.confidence, 0) / lowConfidenceBoxes.length;
          const detailsString = lowConfidenceBoxes.map(box =>
            `${box.class_name || box.class || 'unknown'}: ${(box.confidence * 100).toFixed(1)}%`
          ).join(', ');

          const imageEntry = {
            filename: result.filename,
            index: index + 1, // 1-based index for UI
            count: lowConfidenceBoxes.length,
            confidence: avgConfidence,
            details: detailsString
          }
          rawLowConfidenceImages.value.push(imageEntry)
        }
      }
    })

    console.log(`저신뢰도 이미지 재구성 완료: ${lowConfidenceCount}개 이미지에서 저신뢰도 박스 발견`)
    console.log('저신뢰도 이미지 목록:', rawLowConfidenceImages.value)
    console.log('=== 저신뢰도 이미지 정보 재구성 완료 ===')
  }

  const checkLowConfidenceBoxes = (result) => {
    if (!result.boxes || result.boxes.length === 0) return

    const lowConfidenceBoxes = result.boxes.filter(box =>
      box.confidence < lowConfidenceThreshold.value
    )

    if (lowConfidenceBoxes.length > 0) {
      const existingIndex = rawLowConfidenceImages.value.findIndex(
        img => img.filename === result.filename
      )

      // 신뢰도 정보를 문자열로 포맷팅
      const avgConfidence = lowConfidenceBoxes.reduce((sum, box) => sum + box.confidence, 0) / lowConfidenceBoxes.length;
      const detailsString = lowConfidenceBoxes.map(box =>
        `${box.class_name || box.class || 'unknown'}: ${(box.confidence * 100).toFixed(1)}%`
      ).join(', ');

      const imageEntry = {
        filename: result.filename,
        index: result.index || rawLowConfidenceImages.value.length + 1,
        count: lowConfidenceBoxes.length,
        confidence: avgConfidence,
        details: detailsString
      }

      if (existingIndex >= 0) {
        rawLowConfidenceImages.value[existingIndex] = imageEntry
      } else {
        rawLowConfidenceImages.value.push(imageEntry)
      }
    }
  }

  const clearLowConfidenceImages = () => {
    rawLowConfidenceImages.value = []
  }

  const setLowConfidenceImagesFromProject = (projectLowConfidenceImages, results) => {
    console.log('=== 프로젝트에서 저신뢰도 이미지 설정 시작 ===')
    console.log('프로젝트 저신뢰도 이미지:', projectLowConfidenceImages)
    console.log('결과 이미지 개수:', results.length)

    // 기존 저신뢰도 정보 초기화
    rawLowConfidenceImages.value = []

    if (projectLowConfidenceImages && projectLowConfidenceImages.length > 0) {
      const formattedLowConfidenceImages = projectLowConfidenceImages.map((img) => {
        // 실제 이미지 목록에서 해당 파일명의 인덱스 찾기
        const imageIndex = results.findIndex(result => result.filename === img.filename)
        return {
          filename: img.filename,
          index: imageIndex >= 0 ? imageIndex + 1 : 1, // 1-based index for UI, 찾지 못하면 1
          count: 1, // 저장된 정보에는 개수가 없으므로 기본값 1
          confidence: parseFloat(img.confidence.replace('%', '')) / 100, // "31%" -> 0.31
          details: `저신뢰도: ${img.confidence}`
        }
      })

      rawLowConfidenceImages.value = formattedLowConfidenceImages
      console.log('프로젝트 로드 시 저신뢰도 이미지 설정 완료:', formattedLowConfidenceImages)
    } else {
      console.log('프로젝트에 저신뢰도 이미지가 없습니다.')
    }

    console.log('=== 프로젝트에서 저신뢰도 이미지 설정 완료 ===')
  }

  return {
    // State
    rawLowConfidenceImages,
    lowConfidenceThreshold,

    // Computed
    lowConfidenceImages,

    // Methods
    rebuildLowConfidenceImages,
    checkLowConfidenceBoxes,
    clearLowConfidenceImages,
    setLowConfidenceImagesFromProject
  }
}
