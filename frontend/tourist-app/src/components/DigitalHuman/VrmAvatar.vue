<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm'
import type { VRM } from '@pixiv/three-vrm'

const props = withDefaults(
  defineProps<{
    emotion: string
    isSpeaking: boolean
    isThinking?: boolean
    modelUrl?: string
    /** 语音词边界脉冲计数，每次递增时嘴部做一次重读开合 */
    speechPulse?: number
  }>(),
  { modelUrl: '/models/guide.vrm', speechPulse: 0 }
)

const emit = defineEmits<{
  ready: []
  error: [reason: string]
}>()

const container = ref<HTMLDivElement | null>(null)
const loading = ref(true)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let vrm: VRM | null = null
let clock: THREE.Clock | null = null
let rafId = 0
let resizeObserver: ResizeObserver | null = null
let lookTarget: THREE.Object3D | null = null
let destroyed = false

/** 表情通道 -> VRM 1.0 / 0.x 候选名（按序解析） */
const EXPRESSION_CANDIDATES: Record<string, string[]> = {
  happy: ['happy', 'joy'],
  relaxed: ['relaxed'],
  surprised: ['surprised'],
  blink: ['blink'],
  aa: ['aa', 'a'],
  oh: ['oh', 'o'],
}

const resolvedExprNames = new Map<string, string | null>()
/** 当前各情绪通道的插值值 */
const exprCurrent: Record<string, number> = { happy: 0, relaxed: 0, surprised: 0 }

// 眨眼状态机
let nextBlinkAt = 0
let blinkStart = -1
const BLINK_DURATION = 0.16

// 口型状态
let mouthPhase = 0
let mouthAmp = 0
let mouthAmpTarget = 0
let ampRefreshAt = 0
let boundaryPulse = 0

watch(
  () => props.speechPulse,
  () => {
    boundaryPulse = 1
  }
)

function resolveExpressionName(channel: string): string | null {
  if (resolvedExprNames.has(channel)) return resolvedExprNames.get(channel) ?? null
  const manager = vrm?.expressionManager
  if (!manager) return null
  for (const name of EXPRESSION_CANDIDATES[channel] ?? []) {
    if (manager.getExpression(name)) {
      resolvedExprNames.set(channel, name)
      return name
    }
  }
  resolvedExprNames.set(channel, null)
  return null
}

function setExpression(channel: string, value: number) {
  const name = resolveExpressionName(channel)
  if (name && vrm?.expressionManager) {
    vrm.expressionManager.setValue(name, THREE.MathUtils.clamp(value, 0, 1))
  }
}

/** 情绪 -> 表情通道目标值 */
function emotionTargets(): Record<string, number> {
  switch (props.emotion) {
    case 'happy':
      return { happy: 0.85, relaxed: 0.15, surprised: 0 }
    case 'excited':
      return { happy: 1.0, relaxed: 0, surprised: 0.35 }
    case 'caring':
      return { happy: 0.2, relaxed: 0.75, surprised: 0 }
    case 'explaining':
      return { happy: 0.1, relaxed: 0.3, surprised: 0 }
    default:
      return { happy: 0, relaxed: 0, surprised: 0 }
  }
}

/** 手臂自然下垂（VRM 默认 T-pose 需要主动放下） */
function resetArms(vrm: VRM) {
  const h = vrm.humanoid
  const leftUpper = h.getNormalizedBoneNode('leftUpperArm')
  const rightUpper = h.getNormalizedBoneNode('rightUpperArm')
  const leftLower = h.getNormalizedBoneNode('leftLowerArm')
  const rightLower = h.getNormalizedBoneNode('rightLowerArm')

  // 上臂：自然垂在身体两侧，微向外张
  if (leftUpper) leftUpper.rotation.set(-0.02, -0.02, -1.2)
  if (rightUpper) rightUpper.rotation.set(-0.02, 0.02, 1.2)
  // 前臂：微弯手肘
  if (leftLower) leftLower.rotation.set(0, 0, 0.08)
  if (rightLower) rightLower.rotation.set(0, 0, -0.08)
}

function updateExpressions(delta: number, elapsed: number) {
  // 情绪通道平滑插值
  const targets = emotionTargets()
  const lerp = Math.min(1, delta * 5)
  for (const channel of ['happy', 'relaxed', 'surprised']) {
    const target = targets[channel] ?? 0
    exprCurrent[channel] += (target - exprCurrent[channel]) * lerp
    setExpression(channel, exprCurrent[channel])
  }

  // 眨眼
  if (blinkStart < 0 && elapsed >= nextBlinkAt) {
    blinkStart = elapsed
  }
  if (blinkStart >= 0) {
    const t = (elapsed - blinkStart) / BLINK_DURATION
    if (t >= 1) {
      blinkStart = -1
      setExpression('blink', 0)
      const base = props.isSpeaking ? 1.6 : 2.4
      const variance = props.isSpeaking ? 2.2 : 3.6
      nextBlinkAt = elapsed + base + Math.random() * variance
    } else {
      setExpression('blink', Math.sin(Math.PI * t))
    }
  }

  // 口型：说话节律 + 词边界重读脉冲
  let mouth = 0
  if (props.isSpeaking) {
    if (elapsed >= ampRefreshAt) {
      mouthAmpTarget = 0.35 + Math.random() * 0.55
      ampRefreshAt = elapsed + 0.12
    }
    mouthAmp += (mouthAmpTarget - mouthAmp) * Math.min(1, delta * 10)
    mouthPhase += delta * 11
    mouth = (0.1 + 0.9 * Math.abs(Math.sin(mouthPhase))) * mouthAmp
    if (boundaryPulse > 0) {
      mouth = Math.min(1, mouth + boundaryPulse * 0.4)
      boundaryPulse = Math.max(0, boundaryPulse - delta * 5)
    }
  } else {
    mouthAmp += (0 - mouthAmp) * Math.min(1, delta * 8)
    boundaryPulse = 0
  }
  setExpression('aa', mouth)
  setExpression('oh', mouth * 0.25 * Math.abs(Math.sin(mouthPhase * 0.53)))
}

function updateBody(delta: number, elapsed: number) {
  if (!vrm) return
  const humanoid = vrm.humanoid

  const head = humanoid.getNormalizedBoneNode('head')
  if (head) {
    const yaw = Math.sin(elapsed * 0.45) * 0.05 + (props.isSpeaking ? Math.sin(elapsed * 2.2) * 0.02 : 0)
    let nod = props.isSpeaking ? Math.sin(elapsed * 2.8) * 0.025 : Math.sin(elapsed * 0.8) * 0.012
    let tilt = 0
    if (props.isThinking) {
      tilt = 0.1
      nod += 0.04
    }
    // 平滑接近目标姿态，避免突变
    head.rotation.x += (nod - head.rotation.x) * Math.min(1, delta * 6)
    head.rotation.y += (yaw - head.rotation.y) * Math.min(1, delta * 6)
    head.rotation.z += (tilt - head.rotation.z) * Math.min(1, delta * 4)
  }

  // 呼吸：胸腔轻微起伏
  const chest = humanoid.getNormalizedBoneNode('chest')
  if (chest) {
    chest.rotation.x = 0.03 + Math.sin(elapsed * 1.6) * 0.015
  }

  // 手臂自然微摆（说话时幅度稍大）
  const leftUpper = humanoid.getNormalizedBoneNode('leftUpperArm')
  const rightUpper = humanoid.getNormalizedBoneNode('rightUpperArm')
  if (leftUpper) {
    const sway = (props.isSpeaking ? 0.012 : 0.005) * Math.sin(elapsed * 0.9)
    leftUpper.rotation.x += (-0.02 + sway - leftUpper.rotation.x) * delta * 3
  }
  if (rightUpper) {
    const sway = (props.isSpeaking ? 0.012 : 0.005) * Math.sin(elapsed * 0.9 + 0.5)
    rightUpper.rotation.x += (-0.02 + sway - rightUpper.rotation.x) * delta * 3
  }

  // 视线跟随镜头，带轻微游移
  if (lookTarget && camera) {
    lookTarget.position.set(
      Math.sin(elapsed * 0.31) * 0.12,
      camera.position.y - 0.02 + Math.sin(elapsed * 0.23) * 0.04,
      camera.position.z
    )
  }
}

function animate() {
  if (destroyed) return
  rafId = requestAnimationFrame(animate)
  if (!renderer || !scene || !camera || !clock) return

  const delta = Math.min(clock.getDelta(), 0.1)
  const elapsed = clock.elapsedTime

  if (vrm) {
    updateExpressions(delta, elapsed)
    updateBody(delta, elapsed)
    vrm.update(delta)
  }
  renderer.render(scene, camera)
}

function handleResize() {
  if (!container.value || !renderer || !camera) return
  const width = container.value.clientWidth || 320
  const height = container.value.clientHeight || 320
  renderer.setSize(width, height)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function loadVrm() {
  if (!scene) return
  const loader = new GLTFLoader()
  loader.register((parser) => new VRMLoaderPlugin(parser))

  loader.load(
    props.modelUrl,
    (gltf) => {
      if (destroyed || !scene || !camera) return
      const loaded = gltf.userData.vrm as VRM | undefined
      if (!loaded) {
        emit('error', '模型文件不含 VRM 数据')
        return
      }
      VRMUtils.removeUnnecessaryVertices(gltf.scene)
      VRMUtils.combineSkeletons(gltf.scene)

      // VRM 0.x 模型朝向 +Z，需要转身面向镜头
      if (loaded.meta?.metaVersion === '0') {
        loaded.scene.rotation.y = Math.PI
      }

      vrm = loaded
      scene.add(loaded.scene)

      if (vrm.lookAt && lookTarget) {
        vrm.lookAt.target = lookTarget
      }

      // 依据头部骨骼取景（半身像构图 — 露出额头 + 肩膀/上胸）
      vrm.update(0)
      scene.updateMatrixWorld(true)
      const head = vrm.humanoid.getNormalizedBoneNode('head')
      if (head) {
        const headPos = new THREE.Vector3()
        head.getWorldPosition(headPos)
        // 相机拉远 + 抬高，让画面整体上移且能看到上半身
        camera.position.set(0, headPos.y + 0.05, 0.72)
        camera.lookAt(0, headPos.y - 0.03, 0)
      }

      // 手臂自然下垂，不再 T-pose
      resetArms(vrm)

      nextBlinkAt = 1.2
      loading.value = false
      emit('ready')
    },
    undefined,
    (err) => {
      console.warn('VRM 模型加载失败:', err)
      emit('error', '3D 模型加载失败')
    }
  )
}

onMounted(() => {
  if (!container.value) return
  try {
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  } catch {
    emit('error', '当前环境不支持 WebGL')
    return
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.value.appendChild(renderer.domElement)

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(38, 1, 0.1, 20)
  camera.position.set(0, 1.2, 1.5)

  const hemisphere = new THREE.HemisphereLight(0xffffff, 0x3a3a55, 1.25)
  scene.add(hemisphere)
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.6)
  keyLight.position.set(0.6, 1.6, 1.4)
  scene.add(keyLight)
  const fillLight = new THREE.DirectionalLight(0x8899ff, 0.5)
  fillLight.position.set(-1.2, 0.8, 0.6)
  scene.add(fillLight)

  lookTarget = new THREE.Object3D()
  scene.add(lookTarget)

  clock = new THREE.Clock()
  handleResize()
  resizeObserver = new ResizeObserver(handleResize)
  resizeObserver.observe(container.value)

  loadVrm()
  animate()
})

onUnmounted(() => {
  destroyed = true
  cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  if (scene) {
    scene.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.geometry?.dispose()
        const materials = Array.isArray(obj.material) ? obj.material : [obj.material]
        for (const mat of materials) mat?.dispose()
      }
    })
  }
  renderer?.dispose()
  renderer?.domElement.remove()
  renderer = null
  scene = null
  camera = null
  vrm = null
})
</script>

<template>
  <div class="vrm-avatar">
    <div ref="container" class="vrm-canvas" />
    <div v-if="loading" class="vrm-loading">
      <span class="loading-ring" />
      <span class="loading-text">3D 数字人加载中</span>
    </div>
  </div>
</template>

<style scoped>
.vrm-avatar {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 240px;
}

.vrm-canvas {
  width: 100%;
  height: 100%;
}

.vrm-canvas :deep(canvas) {
  display: block;
}

.vrm-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(10, 10, 26, 0.35);
  border-radius: 12px;
}

.loading-ring {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.15);
  border-top-color: rgba(255, 255, 255, 0.75);
  animation: loading-spin 0.9s linear infinite;
}

.loading-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

@keyframes loading-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
