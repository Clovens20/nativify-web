type BuildMode = 'remote' | 'local'

const STORAGE_MODE_KEY = 'nativify.buildMode'
const STORAGE_URL_KEY = 'nativify.buildBackendUrl'

const normalizeUrl = (url: string) => url.replace(/\/+$/, '')

export function getBuildBackendConfig(): { mode: BuildMode; url: string } {
  const defaultUrl = normalizeUrl(process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')

  if (typeof window === 'undefined') {
    return { mode: 'remote', url: defaultUrl }
  }

  const mode = (window.localStorage.getItem(STORAGE_MODE_KEY) as BuildMode) || 'remote'
  const url = window.localStorage.getItem(STORAGE_URL_KEY) || defaultUrl
  return { mode, url: normalizeUrl(url) }
}

export function setBuildBackendConfig(config: { mode: BuildMode; url: string }) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_MODE_KEY, config.mode)
  window.localStorage.setItem(STORAGE_URL_KEY, normalizeUrl(config.url))
}

export function getBuildBackendUrl(): string {
  const { mode, url } = getBuildBackendConfig()
  return mode === 'local' ? url : normalizeUrl(process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000')
}

export function getBuildApiBaseUrl(): string {
  return `${getBuildBackendUrl()}/api`
}

