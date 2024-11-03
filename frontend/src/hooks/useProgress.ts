import { useState, useEffect } from 'react'

// Easing function that approaches 100% asymptotically
const customEase = (x: number): number => {
    // For x = 1, this will give us ~90%
    // For x = 2, this will give us ~95%
    // Approaches but never quite reaches 100%
    return 100 * (1 - 1 / (1 + x * 4))
}

export function useProgress(
    recordCount: number,
    status: 'processing' | 'done'
) {
    const [progress, setProgress] = useState(0)
    const [startTime] = useState(Date.now())

    useEffect(() => {
        if (status === 'done') {
            setProgress(100)
            return
        }

        const expectedDuration = 1000 + recordCount * 120

        const updateProgress = () => {
            const elapsed = Date.now() - startTime
            const rawProgress = elapsed / expectedDuration

            const calculatedProgress = customEase(rawProgress)
            setProgress(calculatedProgress)

            if (calculatedProgress < 99.9) {
                requestAnimationFrame(updateProgress)
            }
        }

        requestAnimationFrame(updateProgress)
    }, [recordCount, status, startTime])

    return Math.round(progress * 10) / 10 // Round to 1 decimal place
}
