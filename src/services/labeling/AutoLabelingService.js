import { API_SERVER } from '@/utils/config'

export class AutoLabelingService {
  constructor() {
    this.shouldStop = false
    this.isProcessing = false
    this.onProgressCallback = null
  }

  async processImages({ files, selectedClasses, confidenceThreshold, onProgress }) {
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
        const result = await this.processImage(file, selectedClasses, confidenceThreshold)
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

  async processImage(file, selectedClasses, confidenceThreshold = 0.5) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('classes', JSON.stringify(selectedClasses))
      formData.append('confidence_threshold', confidenceThreshold.toString())

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
}
