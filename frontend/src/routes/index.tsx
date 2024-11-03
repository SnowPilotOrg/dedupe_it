import { createFileRoute, useNavigate } from '@tanstack/react-router'

import { DropUpload } from '../components/DropUpload'
import { useData } from '../store/DataContext'
import { DedupeRecord } from '../lib/models'
import { HierarchicalDedupeRecord } from '../lib/dedupeService'
import { TopBar } from '../components/TopBar'
import { useState } from 'react'
import { UpgradeModal } from '../components/UpgradeModal'

export const Route = createFileRoute('/')({
    component: HomeComponent,
})

function HomeComponent() {
    const navigate = useNavigate()
    const { setData } = useData()
    const [upgradeModalOpen, setUpgradeModalOpen] = useState(false)

    const handleDataLoaded = async (
        records: DedupeRecord[],
        columns: string[]
    ) => {
        const hierarchicalRecords: HierarchicalDedupeRecord[] = records.map(
            (record) => ({
                ...record,
                isParent: false,
                children: [],
            })
        )
        setData({ records: hierarchicalRecords, columns, status: 'processing' })
        navigate({ to: '/dedupe' })
    }

    return (
        <>
            <TopBar
                showUpgradeButton={true}
                onUpgradeClick={() => setUpgradeModalOpen(true)}
            />
            <div className="container mx-auto px-4 pt-8">
                <DropUpload onDataLoaded={handleDataLoaded} />
            </div>
            <UpgradeModal
                isOpen={upgradeModalOpen}
                onOpenChange={setUpgradeModalOpen}
            />
        </>
    )
}
