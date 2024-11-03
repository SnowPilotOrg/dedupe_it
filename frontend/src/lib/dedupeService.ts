import { z } from 'zod'
import { DedupeRecord } from './models'

export const GroupResult = z.object({
    group_id: z.string(),
    record_ids: z.array(z.string()),
    merged_data: z.record(z.any()),
})

export type GroupResult = z.infer<typeof GroupResult>

export const DedupeResult = z.object({
    groups: z.array(GroupResult),
})

export type DedupeResult = z.infer<typeof DedupeResult>

const DEDUPE_TIMEOUT_MS = 100000 // 100 second timeout

// Send records to dedupe service and return the result
export async function deduplicate(
    records: DedupeRecord[]
): Promise<DedupeResult> {
    const payload = records.map((record) => ({
        id: record.id,
        data: record.original_data,
    }))

    try {
        const controller = new AbortController()
        const timeoutId = setTimeout(
            () => controller.abort(),
            DEDUPE_TIMEOUT_MS
        )

        const url =
            process.env.NODE_ENV === 'production'
                ? 'https://api.dedupe.it/dedupe'
                : 'http://localhost:8080/dedupe'

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
            signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log('data', data)
        return DedupeResult.parse(data)
    } catch (error) {
        console.error('Deduplication error:', error)
        if (error instanceof DOMException && error.name === 'AbortError') {
            throw new Error('Deduplication request timed out')
        }
        throw error
    }
}

// Add a type to represent the hierarchy
export interface HierarchicalDedupeRecord extends DedupeRecord {
    isParent: boolean
    parentId?: string
    groupId?: string
    children?: HierarchicalDedupeRecord[]
}

// Update records to create parent-child relationships
export function applyDedupeResult(
    records: DedupeRecord[],
    dedupeResult: DedupeResult
): HierarchicalDedupeRecord[] {
    const updatedRecords = [...records] as HierarchicalDedupeRecord[]

    // Index the records by their ID for quick lookup
    const indexedRecords = new Map<string, HierarchicalDedupeRecord>(
        updatedRecords.map((record) => [record.id, record])
    )

    // Apply the dedupe result to the records
    for (const group of dedupeResult.groups) {
        const [parentId, ...childIds] = group.record_ids

        // Set up parent record
        const parentRecord = indexedRecords.get(parentId)!
        parentRecord.status = 'deduped'
        parentRecord.merged_data = group.merged_data
        parentRecord.isParent = true
        parentRecord.groupId = group.group_id
        parentRecord.children = []

        // Set up child records
        for (const childId of childIds) {
            const childRecord = indexedRecords.get(childId)!
            childRecord.status = 'removed'
            childRecord.parentId = parentId
            childRecord.groupId = group.group_id
            childRecord.isParent = false
            parentRecord.children!.push(childRecord)
        }
    }

    // Mark any records that are not in a dedupe group as unique
    for (const record of updatedRecords) {
        if (record.status === 'processing') {
            record.status = 'unique'
            record.isParent = false
        }
    }

    // Return only top-level records (parents and unique records)
    return updatedRecords.filter((record) => !record.parentId)
}
