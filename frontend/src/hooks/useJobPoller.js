import { useState, useEffect, useRef } from 'react'
import { getJobStatus, getJobLog } from '../api/client'

export function useJobPoller(jobId, onDone) {
  const [status, setStatus] = useState(null)
  const [log, setLog]       = useState('')
  const [result, setResult] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!jobId) return
    setStatus('pending')
    setLog('')
    setResult(null)

    const poll = async () => {
      try {
        const [s, l] = await Promise.all([getJobStatus(jobId), getJobLog(jobId)])
        setStatus(s.status)
        setLog(l.log || '')
        if (s.result) setResult(s.result)

        if (s.status === 'done' || s.status === 'failed') {
          clearInterval(intervalRef.current)
          if (onDone) onDone(s)
        }
      } catch (e) {
        console.error('Poll error', e)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 2000)
    return () => clearInterval(intervalRef.current)
  }, [jobId])

  return { status, log, result }
}
