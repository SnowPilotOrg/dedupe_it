import {
    createContext,
    useContext,
    ReactNode,
    useState,
    useEffect,
    useCallback,
} from 'react'
import { HierarchicalDedupeRecord } from '../lib/dedupeService'
import { deduplicate, applyDedupeResult } from '../lib/dedupeService'

type Dataset = {
    status: 'processing' | 'done' | 'error'
    records: HierarchicalDedupeRecord[]
    columns: string[]
}

type DataContextType = {
    data: Dataset | null
    setData: (data: Dataset | null) => void
}

const DataContext = createContext<DataContextType | undefined>(undefined)

export function DataProvider({ children }: { children: ReactNode }) {
    const [data, setData] = useState<Dataset | null>(null)

    const runDedupe = useCallback(async () => {
        if (!data) return

        let dedupeResult
        try {
            dedupeResult = await deduplicate(data.records)
        } catch (error) {
            setData((prev) =>
                prev
                    ? {
                          ...prev,
                          status: 'error',
                          records: prev.records.map((record) => ({
                              ...record,
                              status: 'failed',
                          })),
                      }
                    : null
            )
            return
        }
        const updatedRecords = applyDedupeResult(data.records, dedupeResult)

        setData((prev) =>
            prev
                ? {
                      ...prev,
                      records: updatedRecords,
                      status: 'done',
                  }
                : null
        )
    }, [data, setData])

    useEffect(() => {
        if (data?.status === 'processing') {
            console.log('start running dedupe')
            runDedupe()
        }
    }, [data?.status])

    return (
        <DataContext.Provider
            value={{
                data,
                setData,
            }}
        >
            {children}
        </DataContext.Provider>
    )
}

export function useData() {
    const context = useContext(DataContext)
    if (context === undefined) {
        throw new Error('useData must be used within a DataProvider')
    }
    return context
}
