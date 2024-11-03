import { useCallback, useState } from 'react'
import {
    Button,
    Dropdown,
    DropdownTrigger,
    DropdownMenu,
    DropdownItem,
    cn,
    Spinner,
} from '@nextui-org/react'
import { ChevronDown, UploadCloud } from 'lucide-react'

import { useDropzone } from 'react-dropzone'
import { z } from 'zod'
import { parse } from 'papaparse'
import { toast } from 'sonner'
import { DedupeRecord } from '../lib/models'
import { v4 as uuidv4 } from 'uuid'
import { sampleDatasets } from '../lib/sampleData'

function parseCsvText(csvText: string): {
    records: DedupeRecord[]
    columns: string[]
} {
    const { data, meta } = parse(csvText, {
        header: true,
        skipEmptyLines: true,
    })
    const records = z.record(z.any()).array().parse(data)
    const enrichedRecords = records.map((record) => ({
        id: uuidv4(),
        original_data: record,
        status: 'processing' as const,
    }))
    return { records: enrichedRecords, columns: meta.fields || [] }
}

export const DropUpload = ({
    className,
    onDataLoaded,
}: {
    className?: string
    onDataLoaded: (rows: DedupeRecord[], columns: string[]) => void
}) => {
    const [isProcessing, setIsProcessing] = useState(false)

    const handleSampleSelect = async (key: string) => {
        setIsProcessing(true)
        const dataset = sampleDatasets.find((d) => d.key === key)
        if (!dataset) return

        try {
            const response = await fetch(dataset.url)
            const csvText = await response.text()
            const { records, columns } = parseCsvText(csvText)

            onDataLoaded(records, columns)
        } catch (error) {
            console.error('Error loading sample dataset:', error)
            toast.error('Failed to load sample dataset')
        } finally {
            setIsProcessing(false)
        }
    }

    const onDrop = useCallback(
        async (acceptedFiles: Blob[]) => {
            const file = acceptedFiles[0]
            if (!file) return

            setIsProcessing(true)

            const reader = new FileReader()

            reader.onabort = () => {
                console.log('file reading was aborted')
                setIsProcessing(false)
            }
            reader.onerror = () => {
                console.log('file reading has failed')
                setIsProcessing(false)
            }

            reader.onload = async () => {
                try {
                    const csvText = reader.result as string
                    const { data, meta } = parse(csvText, {
                        header: true,
                        skipEmptyLines: true,
                    })
                    const { records, columns } = parseCsvText(csvText)

                    onDataLoaded(records, columns)
                } catch (error) {
                    console.error('Error deduplicating records:', error)
                } finally {
                    setIsProcessing(false)
                }
            }

            reader.readAsText(file)
        },
        [onDataLoaded]
    )

    const onDropRejected = useCallback((fileRejections: any[]) => {
        const rejection = fileRejections[0]
        if (rejection?.errors[0]?.code === 'file-too-large') {
            toast.error('File is too large. Maximum size is 100KB')
        }
    }, [])

    const { getRootProps, getInputProps, isDragAccept, isDragReject } =
        useDropzone({
            onDrop,
            onDropRejected,
            accept: { 'text/csv': ['.csv'] },
            maxFiles: 1,
            maxSize: 100 * 1024,
            disabled: isProcessing,
        })

    return (
        <div className="flex w-full flex-col items-center gap-4">
            <div className="flex gap-4 items-center mb-4">
                <Dropdown>
                    <DropdownTrigger>
                        <Button
                            variant="flat"
                            className="text-lg font-medium relative text-white bg-gradient-to-r from-[#0047AB]/80 to-[#0066CC]/80 hover:from-[#0047AB]/90 hover:to-[#0066CC]/90 transition-all duration-300 animate-glow-pulse"
                            endContent={<ChevronDown size={16} />}
                        >
                            Try a Sample Dataset
                        </Button>
                    </DropdownTrigger>
                    <DropdownMenu
                        aria-label="Sample datasets"
                        onAction={(key) => handleSampleSelect(key as string)}
                    >
                        {sampleDatasets.map((dataset) => (
                            <DropdownItem
                                key={dataset.key}
                                description={dataset.description}
                            >
                                {dataset.label}
                            </DropdownItem>
                        ))}
                    </DropdownMenu>
                </Dropdown>
                <span className="text-gray-500">or</span>
            </div>

            <div
                {...getRootProps()}
                className={cn(
                    'flex flex-col items-center justify-center w-full max-w-96 h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100',
                    isProcessing &&
                        'opacity-50 cursor-not-allowed hover:bg-gray-50 ',
                    isDragAccept && 'border-green-500',
                    isDragReject && 'border-red-500',
                    className
                )}
            >
                <input {...getInputProps()} />
                {isProcessing ? (
                    <Spinner
                        label="Processing..."
                        color="default"
                        labelColor="foreground"
                    />
                ) : (
                    <>
                        <UploadCloud
                            size={32}
                            className="w-8 h-8 mb-4 text-gray-500"
                        />
                        <p className="mb-2 text-sm text-gray-500">
                            <span className="font-semibold">
                                Click to upload
                            </span>{' '}
                            or drag and drop
                        </p>
                        <p className="text-xs text-gray-500">
                            CSV (Max 100 rows / 100KB)
                        </p>
                    </>
                )}
            </div>
        </div>
    )
}
