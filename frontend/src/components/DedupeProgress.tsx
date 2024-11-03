import { Progress } from '@nextui-org/react'
import { useEffect, useState } from 'react'
import { useProgress } from '../hooks/useProgress'

function LoadingLabel() {
    const [dots, setDots] = useState(0)

    useEffect(() => {
        const interval = setInterval(() => {
            setDots((d) => (d + 1) % 4)
        }, 400)
        return () => clearInterval(interval)
    }, [])

    return (
        <span>
            Deduplicating
            <span className="inline-block w-8">{'.'.repeat(dots)}</span>
        </span>
    )
}

export function DedupeProgress({
    recordCount,
    status,
}: {
    recordCount: number
    status: 'processing' | 'done'
}) {
    const progress = useProgress(recordCount, status)

    return (
        <div className="w-full">
            <div className="max-w-md mx-auto w-full">
                <Progress
                    label={<LoadingLabel />}
                    value={progress}
                    color={status === 'done' ? 'success' : 'primary'}
                    showValueLabel={true}
                    classNames={{
                        label: 'text-default-600',
                    }}
                    disableAnimation={true}
                />
            </div>
        </div>
    )
}
