import { Button } from '@nextui-org/react'
import { Download, Sparkles } from 'lucide-react'
import { HierarchicalDedupeRecord } from '../lib/dedupeService'
import { useMemo, useState } from 'react'
import { exportToCsv } from '../lib/csvExport'
import { UpgradeModal } from './UpgradeModal'

interface DedupeSummaryProps {
    records: HierarchicalDedupeRecord[]
    columns: string[]
}

export function DedupeSummary({ records, columns }: DedupeSummaryProps) {
    const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

    const stats = useMemo(() => {
        // Count all records including children
        const originalCount = records.reduce((count, record) => {
            return count + 1 + (record.children?.length ?? 0)
        }, 0)

        // Count only non-removed records (unique and deduped)
        const deduplicatedCount = records.filter(
            (r) => r.status !== 'removed'
        ).length

        const reduction =
            ((originalCount - deduplicatedCount) / originalCount) * 100

        return {
            originalCount,
            deduplicatedCount,
            reduction: reduction.toFixed(1),
        }
    }, [records])

    const handleExport = () => {
        // Filter out removed records and prepare data for export
        const exportData = records
            .filter((record) => record.status !== 'removed')
            .map((record) =>
                record.status === 'deduped'
                    ? record.merged_data!
                    : record.original_data
            )

        exportToCsv(exportData, columns, 'deduped_data.csv')
    }

    return (
        <>
            <div className="flex items-center gap-4 mr-2 justify-between">
                <div className="flex gap-8">
                    <div>
                        <span className="text-default-600">
                            Original Records:
                        </span>{' '}
                        <span className="font-semibold">
                            {stats.originalCount}
                        </span>
                    </div>
                    <div>
                        <span className="text-default-600">
                            After Deduplication:
                        </span>{' '}
                        <span className="font-semibold">
                            {stats.deduplicatedCount}
                        </span>
                    </div>
                    <div>
                        <span className="text-default-600">Reduction:</span>{' '}
                        <span className="font-semibold text-primary">
                            {stats.reduction}%
                        </span>
                    </div>
                </div>
                <div className="flex gap-4">
                    <Button
                        color="primary"
                        onPress={() => setUpgradeModalOpen(true)}
                        startContent={<Sparkles size={16} />}
                    >
                        Get Full Access
                    </Button>

                    <Button
                        color="default"
                        variant="bordered"
                        startContent={<Download size={16} />}
                        onClick={handleExport}
                    >
                        Export Deduped Data
                    </Button>
                </div>
                <UpgradeModal
                    isOpen={upgradeModalOpen}
                    onOpenChange={setUpgradeModalOpen}
                />
            </div>
        </>
    )
}
