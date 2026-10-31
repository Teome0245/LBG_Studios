<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const props = defineProps({
  gauges: {
    type: Object,
    default: () => ({
      chaleur: 70,
      energie: 70,
      patience: 70,
      confiance: 70
    })
  },
  styleMode: {
    type: String,
    default: 'chaleureuse'
  },
  interactive: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update-gauge', 'apply-preset'])

const containerRef = ref(null)
const selectedPole = ref(null)
const isAutoRotate = ref(true)
const lastThoughtSignal = ref('Conscience active · Réseau synaptique en équilibre')

// Three.js instances
let renderer = null
let scene = null
let camera = null
let controls = null
let animFrameId = null
let resizeObserver = null

// Mesh refs
let coreKnot = null
let coreParticles = null
let haloParticles = null
let poles = {}
let synapseLines = []
let impulseParticles = []
let pulseLight = null

// Cinematic focus state
let targetCamPos = null
let targetLookAt = new THREE.Vector3(0, 0, 0)
let currentLookAt = new THREE.Vector3(0, 0, 0)
let focusTimer = 0

const POLE_CONFIGS = {
  chaleur: {
    label: 'Chaleur',
    icon: '🔥',
    colorHex: 0xf59e0b,
    desc: 'Empathie, écoute bienveillante et tonalité chaleureuse',
    pos: new THREE.Vector3(2.4, 0.8, 1.2)
  },
  energie: {
    label: 'Énergie',
    icon: '⚡',
    colorHex: 0x06b6d4,
    desc: 'Motivation, réactivité, vitesse et dynamisme cognitif',
    pos: new THREE.Vector3(-2.2, 1.2, 1.4)
  },
  patience: {
    label: 'Patience',
    icon: '🧘',
    colorHex: 0x10b981,
    desc: 'Sérénité, profondeur de réflexion et tolérance aux itérations',
    pos: new THREE.Vector3(-1.8, -1.6, -1.2)
  },
  confiance: {
    label: 'Confiance',
    icon: '⭐',
    colorHex: 0x8b5cf6,
    desc: 'Assurance, autonomie décisionnelle et clarté des propositions',
    pos: new THREE.Vector3(2.0, -1.2, -1.5)
  }
}

function initThree() {
  if (!containerRef.value) return
  const width = containerRef.value.clientWidth || 800
  const height = containerRef.value.clientHeight || 500

  // Scene
  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x030712, 0.04)

  // Camera
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
  camera.position.set(0, 1.5, 6.2)

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setClearColor(0x000000, 0)
  containerRef.value.appendChild(renderer.domElement)

  // Controls
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 2.5
  controls.maxDistance = 12
  controls.autoRotate = isAutoRotate.value
  controls.autoRotateSpeed = 0.8

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  pulseLight = new THREE.PointLight(0x38bdf8, 2, 10)
  pulseLight.position.set(0, 0, 0)
  scene.add(pulseLight)

  // 1. Core: Torus Knot (Noyau de Conscience)
  const knotGeo = new THREE.TorusKnotGeometry(0.85, 0.24, 100, 24)
  const knotMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.7,
    wireframe: true,
    transparent: true,
    opacity: 0.85,
    roughness: 0.2,
    metalness: 0.8
  })
  coreKnot = new THREE.Mesh(knotGeo, knotMat)
  scene.add(coreKnot)

  // 2. Core Internal Particle Cloud
  const coreParticlesCount = 350
  const corePartGeo = new THREE.BufferGeometry()
  const corePartPos = new Float32Array(coreParticlesCount * 3)
  for (let i = 0; i < coreParticlesCount * 3; i += 3) {
    const r = 0.7 * Math.cbrt(Math.random())
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    corePartPos[i] = r * Math.sin(phi) * Math.cos(theta)
    corePartPos[i + 1] = r * Math.sin(phi) * Math.sin(theta)
    corePartPos[i + 2] = r * Math.cos(phi)
  }
  corePartGeo.setAttribute('position', new THREE.BufferAttribute(corePartPos, 3))
  const corePartMat = new THREE.PointsMaterial({
    color: 0x38bdf8,
    size: 0.045,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  })
  coreParticles = new THREE.Points(corePartGeo, corePartMat)
  scene.add(coreParticles)

  // 3. Outer Halo (Champ Synaptique Global)
  const haloCount = 600
  const haloGeo = new THREE.BufferGeometry()
  const haloPos = new Float32Array(haloCount * 3)
  for (let i = 0; i < haloCount * 3; i += 3) {
    const r = 2.8 + (Math.random() - 0.5) * 1.2
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    haloPos[i] = r * Math.sin(phi) * Math.cos(theta)
    haloPos[i + 1] = r * Math.sin(phi) * Math.sin(theta)
    haloPos[i + 2] = r * Math.cos(phi)
  }
  haloGeo.setAttribute('position', new THREE.BufferAttribute(haloPos, 3))
  const haloMat = new THREE.PointsMaterial({
    color: 0x64748b,
    size: 0.035,
    transparent: true,
    opacity: 0.45,
    blending: THREE.AdditiveBlending
  })
  haloParticles = new THREE.Points(haloGeo, haloMat)
  scene.add(haloParticles)

  // 4. Pillars / Poles Satellites
  Object.keys(POLE_CONFIGS).forEach(key => {
    const cfg = POLE_CONFIGS[key]
    const group = new THREE.Group()
    group.position.copy(cfg.pos)

    // Satellite Core
    const sphereGeo = new THREE.SphereGeometry(0.22, 16, 16)
    const sphereMat = new THREE.MeshStandardMaterial({
      color: cfg.colorHex,
      emissive: cfg.colorHex,
      emissiveIntensity: 0.9,
      roughness: 0.3
    })
    const sphere = new THREE.Mesh(sphereGeo, sphereMat)
    group.add(sphere)

    // Orbit Ring around pole
    const ringGeo = new THREE.RingGeometry(0.32, 0.36, 32)
    const ringMat = new THREE.MeshBasicMaterial({
      color: cfg.colorHex,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5
    })
    const ring = new THREE.Mesh(ringGeo, ringMat)
    ring.rotation.x = Math.PI / 3
    group.add(ring)

    scene.add(group)
    poles[key] = { group, sphere, ring, basePos: cfg.pos.clone() }

    // 5. Synapse Beams to Center
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(cfg.pos.x * 0.4, cfg.pos.y * 0.4 + 0.3, cfg.pos.z * 0.4),
      cfg.pos
    )
    const points = curve.getPoints(24)
    const lineGeo = new THREE.BufferGeometry().setFromPoints(points)
    const lineMat = new THREE.LineBasicMaterial({
      color: cfg.colorHex,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending
    })
    const line = new THREE.Line(lineGeo, lineMat)
    scene.add(line)
    synapseLines.push({ line, curve, key })

    // Impulses traveling along the synapse
    for (let p = 0; p < 3; p++) {
      const impGeo = new THREE.SphereGeometry(0.04, 8, 8)
      const impMat = new THREE.MeshBasicMaterial({
        color: cfg.colorHex,
        blending: THREE.AdditiveBlending
      })
      const impMesh = new THREE.Mesh(impGeo, impMat)
      scene.add(impMesh)
      impulseParticles.push({
        mesh: impMesh,
        curve,
        progress: (p * 0.33 + Math.random() * 0.2) % 1,
        speed: 0.003
      })
    }
  })

  // Apply initial gauges styling
  applyGaugesToScene()

  // Resize handling
  resizeObserver = new ResizeObserver(() => {
    if (!containerRef.value || !renderer || !camera) return
    const w = containerRef.value.clientWidth
    const h = containerRef.value.clientHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
  })
  resizeObserver.observe(containerRef.value)

  // Start Animation Loop
  let clock = new THREE.Clock()
  function animate() {
    animFrameId = requestAnimationFrame(animate)
    const delta = clock.getDelta()
    const time = clock.getElapsedTime()

    // Gauge-driven speeds
    const energyVal = (props.gauges.energie || 50) / 100
    const heatVal = (props.gauges.chaleur || 50) / 100
    const patienceVal = (props.gauges.patience || 50) / 100

    // Core knot rotation and pulsation
    if (coreKnot) {
      coreKnot.rotation.x = time * (0.2 + energyVal * 0.3)
      coreKnot.rotation.y = time * (0.25 + energyVal * 0.35)
      const scale = 1 + Math.sin(time * (1.5 + energyVal * 2)) * (0.05 + heatVal * 0.04)
      coreKnot.scale.set(scale, scale, scale)
    }

    if (coreParticles) {
      coreParticles.rotation.y = -time * (0.15 + energyVal * 0.2)
    }

    if (haloParticles) {
      haloParticles.rotation.y = time * 0.06
      haloParticles.rotation.x = Math.sin(time * 0.05) * 0.1
    }

    // Poles floating bob and ring spin
    Object.keys(poles).forEach(k => {
      const p = poles[k]
      p.ring.rotation.z = time * (0.8 + energyVal * 0.5)
      const bob = Math.sin(time * 1.5 + p.basePos.x) * 0.08 * (1.2 - patienceVal * 0.5)
      p.group.position.y = p.basePos.y + bob
    })

    // Traveling impulses
    impulseParticles.forEach(imp => {
      imp.progress += (0.003 + energyVal * 0.007)
      if (imp.progress > 1) imp.progress = 0
      const pos = imp.curve.getPoint(imp.progress)
      imp.mesh.position.copy(pos)
    })

    // Cinematic smooth transition
    if (targetCamPos && focusTimer > 0) {
      focusTimer -= delta
      camera.position.lerp(targetCamPos, 0.05)
      currentLookAt.lerp(targetLookAt, 0.05)
      controls.target.copy(currentLookAt)
      if (focusTimer <= 0) {
        targetCamPos = null
      }
    }

    controls.update()
    renderer.render(scene, camera)
  }
  animate()
}

function applyGaugesToScene() {
  if (!coreKnot) return

  const chaleur = Math.max(0, Math.min(100, props.gauges.chaleur || 50))
  const energie = Math.max(0, Math.min(100, props.gauges.energie || 50))
  const patience = Math.max(0, Math.min(100, props.gauges.patience || 50))
  const confiance = Math.max(0, Math.min(100, props.gauges.confiance || 50))

  // Color interpolation for core
  // Cold (0) -> Cyan (50) -> Warm Amber/Gold (100)
  const coreColor = new THREE.Color()
  if (chaleur < 50) {
    const t = chaleur / 50
    coreColor.lerpColors(new THREE.Color(0x3b82f6), new THREE.Color(0x06b6d4), t)
  } else {
    const t = (chaleur - 50) / 50
    coreColor.lerpColors(new THREE.Color(0x06b6d4), new THREE.Color(0xf59e0b), t)
  }

  coreKnot.material.color.copy(coreColor)
  coreKnot.material.emissive.copy(coreColor)
  coreKnot.material.emissiveIntensity = 0.5 + (energie / 100) * 0.6
  coreParticles.material.color.copy(coreColor)

  if (pulseLight) {
    pulseLight.color.copy(coreColor)
    pulseLight.intensity = 1.5 + (energie / 100) * 1.5
  }

  // Outer halo reflects patience (smoothness) & confiance (density & size)
  if (haloParticles) {
    haloParticles.material.size = 0.025 + (confiance / 100) * 0.025
    haloParticles.material.opacity = 0.3 + (confiance / 100) * 0.4
  }

  if (controls) {
    controls.autoRotateSpeed = 0.4 + (energie / 100) * 0.9
  }
}

function focusPole(key) {
  const cfg = POLE_CONFIGS[key]
  if (!cfg) return
  selectedPole.value = key
  isAutoRotate.value = false
  if (controls) controls.autoRotate = false

  targetLookAt = cfg.pos.clone()
  const offset = cfg.pos.clone().normalize().multiplyScalar(2.2)
  targetCamPos = cfg.pos.clone().add(offset)
  focusTimer = 4.0

  triggerPulse(cfg.colorHex)
  lastThoughtSignal.value = `Focus sur le pôle ${cfg.label} (${cfg.icon}) : ${cfg.desc}`
}

function resetView() {
  selectedPole.value = null
  isAutoRotate.value = true
  if (controls) {
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.8
  }
  targetLookAt = new THREE.Vector3(0, 0, 0)
  targetCamPos = new THREE.Vector3(0, 1.5, 6.2)
  focusTimer = 2.5
  lastThoughtSignal.value = 'Vue globale rétablie · Orbite 360° active'
}

function toggleAutoRotate() {
  isAutoRotate.value = !isAutoRotate.value
  if (controls) controls.autoRotate = isAutoRotate.value
}

function triggerPulse(customColorHex = null) {
  if (!pulseLight || !coreKnot) return
  const originalIntensity = pulseLight.intensity
  const originalMatIntensity = coreKnot.material.emissiveIntensity

  pulseLight.intensity = 5.0
  coreKnot.material.emissiveIntensity = 1.8
  if (customColorHex) {
    pulseLight.color.setHex(customColorHex)
  }

  setTimeout(() => {
    if (pulseLight) pulseLight.intensity = originalIntensity
    if (coreKnot) coreKnot.material.emissiveIntensity = originalMatIntensity
    applyGaugesToScene()
  }, 450)

  lastThoughtSignal.value = `Pulsion synaptique émise · Onde de pensée propagée (${new Date().toLocaleTimeString('fr-FR')})`
}

watch(() => props.gauges, () => {
  applyGaugesToScene()
}, { deep: true })

onMounted(() => {
  initThree()
})

onUnmounted(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId)
  if (resizeObserver) resizeObserver.disconnect()
  if (renderer) {
    renderer.dispose()
    if (renderer.domElement && renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
  }
})
</script>

<template>
  <div class="relative w-full h-full flex flex-col overflow-hidden select-none bg-slate-950/80 rounded-3xl border border-white/5">
    
    <!-- Canvas WebGL Container -->
    <div ref="containerRef" class="w-full h-full min-h-[380px] cursor-grab active:cursor-grabbing"></div>

    <!-- Top Overlay HUD : Titre et état émotionnel -->
    <div class="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none">
      <div class="flex items-center gap-3 glass-panel px-4 py-2 rounded-2xl border border-white/10 pointer-events-auto backdrop-blur-md">
        <span class="text-xl">🧠</span>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-white font-outfit">Conscience 3D de Lyra</span>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-widest">
              {{ styleMode || 'Équilibrée' }}
            </span>
          </div>
          <div class="text-[11px] text-slate-400 font-mono flex items-center gap-2 mt-0.5">
            <span>🔥 {{ gauges.chaleur }}%</span>
            <span>⚡ {{ gauges.energie }}%</span>
            <span>🧘 {{ gauges.patience }}%</span>
            <span>⭐ {{ gauges.confiance }}%</span>
          </div>
        </div>
      </div>

      <!-- Controls Toolbar -->
      <div class="flex items-center gap-2 glass-panel p-1.5 rounded-2xl border border-white/10 pointer-events-auto backdrop-blur-md">
        <button
          type="button"
          class="px-3 py-1.5 rounded-xl text-xs font-medium transition-colors flex items-center gap-1.5"
          :class="isAutoRotate ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'text-slate-400 hover:text-white hover:bg-white/5'"
          @click="toggleAutoRotate"
          title="Activer/Désactiver l'orbite 360°"
        >
          <span>🔄</span>
          <span class="hidden sm:inline">Orbite {{ isAutoRotate ? 'ON' : 'OFF' }}</span>
        </button>

        <button
          type="button"
          class="px-3 py-1.5 rounded-xl text-xs font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors flex items-center gap-1.5"
          @click="resetView"
          title="Recentrer la caméra"
        >
          <span>👁️</span>
          <span class="hidden sm:inline">Recentrer</span>
        </button>

        <button
          type="button"
          class="px-3 py-1.5 rounded-xl text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/30 transition-colors flex items-center gap-1.5"
          @click="triggerPulse()"
          title="Déclencher une pulsion synaptique"
        >
          <span>⚡</span>
          <span>Pulsion</span>
        </button>
      </div>
    </div>

    <!-- Bottom Overlay HUD : Focus Pôles & Flux de Pensée -->
    <div class="absolute bottom-4 left-4 right-4 flex flex-col sm:flex-row items-end sm:items-center justify-between gap-3 pointer-events-none">
      
      <!-- Pôles Switcher -->
      <div class="flex items-center gap-1.5 glass-panel p-1.5 rounded-2xl border border-white/10 pointer-events-auto backdrop-blur-md">
        <button
          v-for="(cfg, key) in POLE_CONFIGS"
          :key="key"
          type="button"
          class="px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5"
          :class="selectedPole === key ? 'bg-white/20 text-white shadow-sm ring-1 ring-white/30' : 'text-slate-400 hover:text-white hover:bg-white/5'"
          @click="focusPole(key)"
        >
          <span>{{ cfg.icon }}</span>
          <span class="hidden md:inline">{{ cfg.label }}</span>
        </button>
      </div>

      <!-- Flux d'état de pensée direct -->
      <div class="glass-panel px-4 py-2 rounded-2xl border border-white/10 text-xs text-slate-300 font-mono pointer-events-auto backdrop-blur-md max-w-md truncate">
        <span class="text-cyan-400 mr-1.5">●</span>
        <span>{{ lastThoughtSignal }}</span>
      </div>

    </div>

  </div>
</template>

