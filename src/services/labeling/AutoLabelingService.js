import { API_SERVER } from '@/utils/config'

export class AutoLabelingService {
  constructor() {
    this.shouldStop = false
    this.isProcessing = false
    this.onProgressCallback = null
  }

  async processImages({ files, selectedClasses, confidenceThreshold, supportsTextPrompt, textPrompt, boxThreshold, textThreshold, onProgress }) {
    this.shouldStop = false
    this.isProcessing = true
    this.onProgressCallback = onProgress

    try {
      const results = []
      const totalFiles = files.length
      const startTime = Date.now()

      for (let i = 0; i < files.length && !this.shouldStop; i++) {
        const file = files[i]
        const currentProgress = {
          percent: Math.round((i / totalFiles) * 100),
          currentFile: file.name,
          timeInfo: this.calculateTimeInfo(startTime, i, totalFiles)
        }

        if (this.onProgressCallback) {
          this.onProgressCallback(currentProgress)
        }

        // Process single image
        const result = await this.processImage(file, selectedClasses, confidenceThreshold, supportsTextPrompt, textPrompt, boxThreshold, textThreshold)
        if (result) {
          results.push(result)
        }
      }

      // Final progress update
      if (this.onProgressCallback && !this.shouldStop) {
        this.onProgressCallback({
          percent: 100,
          currentFile: '완료',
          timeInfo: this.calculateTimeInfo(startTime, totalFiles, totalFiles)
        })
      }

      return results
    } catch (error) {
      console.error('자동라벨링 처리 오류:', error)
      throw error
    } finally {
      this.isProcessing = false
    }
  }

  async processImage(file, selectedClasses, confidenceThreshold = 0.5, supportsTextPrompt = false, textPrompt = '', boxThreshold = 0.3, textThreshold = 0.25) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('classes', JSON.stringify(selectedClasses))
      formData.append('confidence_threshold', confidenceThreshold.toString())

      // Grounding DINO 텍스트 프롬프트 지원
      if (supportsTextPrompt && textPrompt) {
        formData.append('text_prompt', textPrompt)
        formData.append('box_threshold', boxThreshold.toString())
        formData.append('text_threshold', textThreshold.toString())
      }

      const response = await fetch(`${API_SERVER}/labeling/process`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`라벨링 실패: ${response.status}`)
      }

      const result = await response.json()

      // 이미지 크기 정보 확인 및 리사이즈 여부 판단
      const originalWidth = result.width || 0
      const originalHeight = result.height || 0
      const wasResized = result.was_resized || result.resize_applied || false
      const veryLowRes = result.very_low_resolution || false
      const resizeMethod = result.resize_method || 'none'

      // 리사이즈 정보 로깅
      if (veryLowRes) {
        console.log(`🔧 [자동라벨링] ${file.name}: 매우 낮은 해상도 (${originalWidth}x${originalHeight}) 감지, 고품질 letterbox 리사이즈 적용하여 성능 최적화`)
      } else if (wasResized) {
        console.log(`🔄 [자동라벨링] ${file.name}: 낮은 해상도 (${originalWidth}x${originalHeight}) 감지, 자동 리사이즈 적용하여 성능 향상`)
      } else {
        console.log(`✅ [자동라벨링] ${file.name}: 충분한 해상도 (${originalWidth}x${originalHeight}), 리사이즈 불필요`)
      }

      return {
        filename: file.name,
        boxes: result.boxes || [],
        imageData: result.imageData,
        width: originalWidth,
        height: originalHeight,
        confidence: result.confidence,
        processing_time: result.processing_time,
        // 확장된 리사이즈 정보
        wasResized: wasResized,
        veryLowResolution: veryLowRes,
        resizeMethod: resizeMethod,
        originalResolution: `${originalWidth}x${originalHeight}`,
        resizeReason: veryLowRes ? '매우 낮은 해상도 - 고품질 letterbox 리사이즈 적용' :
                     wasResized ? '성능 향상을 위한 자동 리사이즈 적용' : null
      }
    } catch (error) {
      console.error(`이미지 처리 오류 (${file.name}):`, error)
      return null
    }
  }

  calculateTimeInfo(startTime, current, total) {
    const elapsed = (Date.now() - startTime) / 1000
    const avgTimePerImage = elapsed / Math.max(current, 1)
    const remaining = (total - current) * avgTimePerImage

    return {
      elapsed: this.formatTime(elapsed),
      eta: current >= total ? '완료' : this.formatTime(remaining)
    }
  }

  formatTime(seconds) {
    if (seconds < 60) {
      return `${Math.round(seconds)}초`
    } else if (seconds < 3600) {
      const mins = Math.floor(seconds / 60)
      const secs = Math.round(seconds % 60)
      return `${mins}분 ${secs}초`
    } else {
      const hours = Math.floor(seconds / 3600)
      const mins = Math.floor((seconds % 3600) / 60)
      return `${hours}시간 ${mins}분`
    }
  }

  stop() {
    this.shouldStop = true
    console.log('자동라벨링 중단 요청됨')
  }

  isRunning() {
    return this.isProcessing && !this.shouldStop
  }

  // ============================================================================
  // 멀티모델 파이프라인 메서드
  // ============================================================================

  /**
   * 파이프라인 정보 조회
   */
  async getPipelineInfo() {
    try {
      const response = await fetch(`${API_SERVER}/pipeline/info`)
      if (!response.ok) {
        throw new Error(`파이프라인 정보 조회 실패: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('파이프라인 정보 조회 오류:', error)
      throw error
    }
  }

  /**
   * 파이프라인에 모델 로드
   */
  async loadPipelineModel({ taskName, modelName, modelPath, config = {} }) {
    try {
      const formData = new FormData()
      formData.append('task_name', taskName)
      formData.append('model_name', modelName)
      if (modelPath) {
        formData.append('model_path', modelPath)
      }
      if (Object.keys(config).length > 0) {
        formData.append('config', JSON.stringify(config))
      }

      const response = await fetch(`${API_SERVER}/pipeline/load-model`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`모델 로드 실패: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('모델 로드 오류:', error)
      throw error
    }
  }

  /**
   * 멀티태스크 파이프라인으로 이미지 처리
   */
  async processImageWithPipeline({
    file,
    tasks = ['detection'],
    detectionConfig = {},
    keypointConfig = {},
    ocrConfig = {}
  }) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('tasks', JSON.stringify(tasks))

      if (detectionConfig && Object.keys(detectionConfig).length > 0) {
        formData.append('detection_config', JSON.stringify(detectionConfig))
      }
      if (keypointConfig && Object.keys(keypointConfig).length > 0) {
        formData.append('keypoint_config', JSON.stringify(keypointConfig))
      }
      if (ocrConfig && Object.keys(ocrConfig).length > 0) {
        formData.append('ocr_config', JSON.stringify(ocrConfig))
      }

      const response = await fetch(`${API_SERVER}/pipeline/process-multi`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`파이프라인 처리 실패: ${response.status}`)
      }

      const result = await response.json()

      console.log(`✅ [멀티모델 파이프라인] ${file.name}: 처리 완료`)
      console.log(`   - 실행된 태스크: ${tasks.join(', ')}`)
      console.log(`   - 처리 시간: ${result.processing_time}초`)

      return {
        filename: file.name,
        results: result.results,
        imageData: result.image,
        width: result.image_size.width,
        height: result.image_size.height,
        processing_time: result.processing_time,
        pipeline_info: result.pipeline_info,
        tasks: tasks
      }
    } catch (error) {
      console.error(`파이프라인 처리 오류 (${file.name}):`, error)
      throw error
    }
  }

  /**
   * 사용 가능한 모델 목록 조회
   */
  async getAvailableModels() {
    try {
      const response = await fetch(`${API_SERVER}/models/available`)
      if (!response.ok) {
        throw new Error(`모델 목록 조회 실패: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      console.error('모델 목록 조회 오류:', error)
      throw error
    }
  }

  /**
   * Grounding DINO로 텍스트 프롬프트 기반 탐지
   */
  async processWithGroundingDINO({
    file,
    textPrompt,
    boxThreshold = 0.35,
    textThreshold = 0.25
  }) {
    return await this.processImageWithPipeline({
      file,
      tasks: ['detection'],
      detectionConfig: {
        text_prompt: textPrompt,
        box_threshold: boxThreshold,
        text_threshold: textThreshold
      }
    })
  }

  /**
   * YOLO Pose로 키포인트 탐지
   */
  async processWithYOLOPose({ file, confidenceThreshold = 0.5 }) {
    return await this.processImageWithPipeline({
      file,
      tasks: ['keypoint'],
      keypointConfig: {
        confidence_threshold: confidenceThreshold
      }
    })
  }

  /**
   * EasyOCR로 텍스트 인식
   */
  async processWithOCR({ file, languages = ['en', 'ko'], textThreshold = 0.7 }) {
    return await this.processImageWithPipeline({
      file,
      tasks: ['ocr'],
      ocrConfig: {
        text_threshold: textThreshold
      }
    })
  }

  /**
   * 전체 파이프라인 실행 (detection + keypoint + ocr)
   */
  async processFullPipeline({
    file,
    detectionConfig = { confidence_threshold: 0.5 },
    keypointConfig = { confidence_threshold: 0.5 },
    ocrConfig = { text_threshold: 0.7 }
  }) {
    return await this.processImageWithPipeline({
      file,
      tasks: ['detection', 'keypoint', 'ocr'],
      detectionConfig,
      keypointConfig,
      ocrConfig
    })
  }
}
