import { useEffect, useState } from 'react'

export function useApi(fn, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  useEffect(() => {
    let alive = true
    setState({ data: null, loading: true, error: null })
    fn()
      .then((data) => alive && setState({ data, loading: false, error: null }))
      .catch((error) => alive && setState({ data: null, loading: false, error: String(error) }))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return state
}
