import { Chip } from '@nextui-org/react'
import { CircleDot, Check, XCircle, Clock } from 'lucide-react'

export type StatusVariant = 'processing' | 'deduped' | 'removed' | 'unique'

interface StatusChipProps {
    variant: StatusVariant
    dupeCount?: number
}

export const StatusChip = ({ variant, dupeCount }: StatusChipProps) => {
    const getChipProps = () => {
        switch (variant) {
            case 'deduped':
                return {
                    color: 'primary' as const,
                    startContent: dupeCount ? (
                        <div className="flex items-center justify-center w-4 h-4 rounded-full bg-primary-400/30 text-primary-600 text-xs">
                            {dupeCount}
                        </div>
                    ) : (
                        <CircleDot className="w-4 h-4" />
                    ),
                    children: 'Deduped',
                }
            case 'removed':
                return {
                    color: 'danger' as const,
                    startContent: <XCircle className="w-4 h-4" />,
                    children: 'Removed',
                }
            case 'unique':
                return {
                    color: 'success' as const,
                    startContent: <Check className="w-4 h-4" />,
                    children: 'Unique',
                }
            case 'processing':
                return {
                    color: 'default' as const,
                    startContent: (
                        <div className="rounded-full bg-gray-400 w-4 h-4 animate-pulse" />
                    ),
                    children: 'Processing',
                }
        }
    }

    return (
        <Chip size="sm" variant="flat" {...getChipProps()} className="gap-1" />
    )
}
