import { useData } from '../store/DataContext'
import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { DedupeTable } from '../components/DedupeTable'
import { DedupeSummary } from '../components/DedupeSummary'
import { DedupeProgress } from '../components/DedupeProgress'
import {
    Card,
    CardBody,
    Button,
    Modal,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalFooter,
} from '@nextui-org/react'
import { ArrowLeft } from 'lucide-react'
import { TopBar } from '../components/TopBar'

export const Route = createFileRoute('/dedupe')({
    component: DedupePage,
})

function DedupePage() {
    const navigate = useNavigate()
    const { data } = useData()

    if (!data) {
        return (
            <>
                <div className="text-center">
                    <p className="text-gray-500 mb-4 text-lg">
                        No data to deduplicate. Please select a dataset first.
                    </p>
                    <button
                        type="button"
                        onClick={() => navigate({ to: '/' })}
                        className="text-blue-500 hover:underline"
                    >
                        Go back to home
                    </button>
                </div>
            </>
        )
    }

    if (data.status === 'error') {
        return (
            <Modal
                isOpen={true}
                hideCloseButton
                isDismissable={false}
                backdrop="blur"
            >
                <ModalContent>
                    <ModalHeader className="text-danger">
                        Deduplication Failed
                    </ModalHeader>
                    <ModalBody>
                        <p>Failed to deduplicate records. Please try again.</p>
                    </ModalBody>
                    <ModalFooter>
                        <Button
                            color="primary"
                            onPress={() => navigate({ to: '/' })}
                            autoFocus
                        >
                            Back to Home
                        </Button>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        )
    }

    return (
        <>
            <TopBar showUpgradeButton={false} />
            <Card className="mb-4">
                <CardBody>
                    <div className="flex items-center gap-4">
                        <Link to="/">
                            <Button isIconOnly variant="light" size="sm">
                                <ArrowLeft size={16} />
                            </Button>
                        </Link>
                        <div className="flex-1">
                            {data.status === 'processing' && (
                                <DedupeProgress
                                    recordCount={data.records.length}
                                    status={data.status}
                                />
                            )}
                            {data.status === 'done' && (
                                <DedupeSummary
                                    records={data.records}
                                    columns={data.columns}
                                />
                            )}
                        </div>
                    </div>
                </CardBody>
            </Card>
            <DedupeTable records={data.records} columns={data.columns} />
        </>
    )
}
