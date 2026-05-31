export async function requestJson<T>(input: RequestInfo | URL, init?: RequestInit, fallbackMessage = '请求失败'): Promise<T> {
  const response = await fetch(input, init)
  const raw = await response.text()

  let payload: unknown = null
  if (raw) {
    try {
      payload = JSON.parse(raw)
    } catch {
      payload = raw
    }
  }

  if (!response.ok) {
    const detail =
      payload &&
      typeof payload === 'object' &&
      'detail' in payload &&
      typeof (payload as { detail?: unknown }).detail === 'string'
        ? (payload as { detail: string }).detail
        : ''

    throw new Error(detail || fallbackMessage)
  }

  return payload as T
}
