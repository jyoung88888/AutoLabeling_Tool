/**
 * 색상 관리 유틸리티
 * 모든 컴포넌트에서 일관된 클래스 색상을 사용하기 위한 유틸리티
 */

// 색상 캐시 객체
const colorCache = {};

// 눈에 잘 띄는 미리 정의된 색상 팔레트
const BRIGHT_COLORS = [
  '#FF5733', // 밝은 빨강
  '#33FF57', // 밝은 초록
  '#3357FF', // 밝은 파랑
  '#FF33F1', // 밝은 분홍
  '#F1FF33', // 밝은 노랑
  '#33FFF1', // 밝은 시안
  '#FF8C33', // 밝은 주황
  '#8C33FF', // 밝은 보라
  '#33FF8C', // 밝은 라임
  '#FF338C', // 밝은 분홍-빨강
  '#8CFF33', // 밝은 라임-노랑
  '#338CFF', // 밝은 하늘색
  '#FF5733', // 밝은 토마토
  '#57FF33', // 밝은 잔디
  '#3357FF', // 밝은 코발트
  '#FF3357', // 밝은 체리
  '#57FF57', // 밝은 네온 초록
  '#5733FF', // 밝은 인디고
  '#FF5757', // 밝은 산호
  '#33FF33'  // 밝은 에메랄드
];

/**
 * 클래스 이름에 대한 일관된 색상을 생성하거나 반환합니다.
 * @param {string} className - 클래스 이름
 * @param {Object} customColors - 사용자 지정 색상 맵
 * @returns {string} HEX 색상 코드
 */
export function getClassColor(className, customColors = {}) {
  // 1. 커스텀 색상이 있으면 우선 사용
  if (customColors && customColors[className]) {
    return customColors[className];
  }

  // 2. 캐시된 색상이 있으면 반환
  if (colorCache[className]) {
    return colorCache[className];
  }

  // 3. 클래스 이름이 없거나 unknown인 경우 기본 색상
  if (!className || className === 'unknown') {
    const defaultColor = '#FF9F43'; // 가독성 좋은 주황색
    colorCache[className] = defaultColor;
    return defaultColor;
  }

  // 4. 완전히 랜덤한 밝은 색상 생성
  const randomColor = generateRandomBrightColor();

  // 5. 캐시에 저장
  colorCache[className] = randomColor;

  return randomColor;
}

/**
 * 완전히 랜덤한 밝은 색상을 생성합니다.
 * @returns {string} HEX 색상 코드
 */
export function generateRandomBrightColor() {
  // 랜덤한 HSL 값 생성 (밝고 채도가 높은 색상)
  const hue = Math.floor(Math.random() * 360); // 0-360도
  const saturation = 70 + Math.floor(Math.random() * 30); // 70-100% 높은 채도
  const lightness = 45 + Math.floor(Math.random() * 25); // 45-70% 적당한 밝기

  return hslToHex(hue, saturation, lightness);
}

/**
 * 랜덤한 밝은 색상을 생성합니다.
 * @returns {string} HEX 색상 코드
 */
export function getRandomBrightColor() {
  const randomIndex = Math.floor(Math.random() * BRIGHT_COLORS.length);
  return BRIGHT_COLORS[randomIndex];
}

/**
 * HSL 기반으로 밝고 채도가 높은 색상을 생성합니다.
 * @param {string} seed - 시드 문자열
 * @returns {string} HEX 색상 코드
 */
export function generateBrightColor(seed) {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }

  // HSL 기반으로 밝고 채도가 높은 색상 생성
  const hue = Math.abs(hash) % 360; // 0-360도
  const saturation = 70 + (Math.abs(hash >> 8) % 30); // 70-100% 높은 채도
  const lightness = 45 + (Math.abs(hash >> 16) % 25); // 45-70% 적당한 밝기

  // HSL을 RGB로 변환
  const h = hue / 360;
  const s = saturation / 100;
  const l = lightness / 100;

  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((h * 6) % 2 - 1));
  const m = l - c / 2;

  let r, g, b;
  if (h < 1/6) {
    r = c; g = x; b = 0;
  } else if (h < 2/6) {
    r = x; g = c; b = 0;
  } else if (h < 3/6) {
    r = 0; g = c; b = x;
  } else if (h < 4/6) {
    r = 0; g = x; b = c;
  } else if (h < 5/6) {
    r = x; g = 0; b = c;
  } else {
    r = c; g = 0; b = x;
  }

  r = Math.round((r + m) * 255);
  g = Math.round((g + m) * 255);
  b = Math.round((b + m) * 255);

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * HSL 색상을 HEX로 변환합니다.
 * @param {number} h - 색조 (0-360)
 * @param {number} s - 채도 (0-100)
 * @param {number} l - 밝기 (0-100)
 * @returns {string} HEX 색상 코드
 */
export function hslToHex(h, s, l) {
  l /= 100;
  const a = s * Math.min(l, 1 - l) / 100;
  const f = n => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

/**
 * HEX 색상을 RGBA로 변환합니다.
 * @param {string} hex - HEX 색상 코드
 * @param {number} alpha - 투명도 (0-1)
 * @returns {string} RGBA 색상 문자열
 */
export function hexToRgba(hex, alpha = 1) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * 색상이 밝은지 어두운지 판단합니다.
 * @param {string} hex - HEX 색상 코드
 * @returns {boolean} 밝으면 true, 어두우면 false
 */
export function isLightColor(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return brightness > 128;
}

/**
 * 색상 캐시를 초기화합니다.
 */
export function clearColorCache() {
  Object.keys(colorCache).forEach(key => delete colorCache[key]);
}

/**
 * 현재 캐시된 색상들을 반환합니다.
 * @returns {Object} 색상 캐시 객체
 */
export function getColorCache() {
  return { ...colorCache };
}

/**
 * 색상 캐시를 설정합니다.
 * @param {Object} colors - 색상 맵
 */
export function setColorCache(colors) {
  Object.assign(colorCache, colors);
}

/**
 * UI 테마 색상들
 */
export const UI_COLORS = {
  primary: '#3982d4',
  secondary: '#4f9cf5',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',

  // 섹션별 테마 색상
  fileInfo: {
    bg: 'rgba(59, 130, 246, 0.15)',
    border: 'rgba(59, 130, 246, 0.3)',
    hover: 'rgba(59, 130, 246, 0.25)'
  },
  labelingType: {
    bg: 'rgba(16, 185, 129, 0.15)',
    border: 'rgba(16, 185, 129, 0.3)',
    hover: 'rgba(16, 185, 129, 0.25)'
  },
  labelList: {
    bg: 'rgba(139, 92, 246, 0.15)',
    border: 'rgba(139, 92, 246, 0.3)',
    hover: 'rgba(139, 92, 246, 0.25)'
  },
  controls: {
    bg: 'rgba(245, 101, 101, 0.15)',
    border: 'rgba(245, 101, 101, 0.3)',
    hover: 'rgba(245, 101, 101, 0.25)'
  }
};

export default {
  getClassColor,
  hslToHex,
  hexToRgba,
  isLightColor,
  clearColorCache,
  getColorCache,
  setColorCache,
  UI_COLORS
};
