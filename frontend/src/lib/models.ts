import { z } from 'zod'

export const Status = z.enum([
    'processing',
    'unique',
    'deduped',
    'removed',
    'failed',
])

export type Status = z.infer<typeof Status>

export const DedupeRecord = z.object({
    id: z.string(),
    status: Status,
    original_data: z.record(z.any()),
    merged_data: z.record(z.any()).optional(),
})

export type DedupeRecord = z.infer<typeof DedupeRecord>
