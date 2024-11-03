import { Key, useState } from 'react'
import {
    Table,
    TableBody,
    TableCell,
    TableColumn,
    TableHeader,
    TableRow,
    Button,
} from '@nextui-org/react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { HierarchicalDedupeRecord } from '../lib/dedupeService'
import { StatusChip } from './StatusChip'
import { diffWords } from 'diff'

const STATUS_COLUMN = 'status'
const EXPAND_COLUMN = 'expand'

const DiffCell = ({
    oldText,
    newText,
}: {
    oldText: string
    newText: string
}) => {
    const differences = diffWords(String(oldText), String(newText))

    return (
        <span>
            {differences.map((part, index) => {
                if (part.added) {
                    return (
                        <span
                            key={index}
                            className="bg-green-100 text-green-800"
                        >
                            {part.value}
                        </span>
                    )
                }
                if (part.removed) {
                    return (
                        <span
                            key={index}
                            className="bg-red-100 text-red-800 line-through"
                        >
                            {part.value}
                        </span>
                    )
                }
                return <span key={index}>{part.value}</span>
            })}
        </span>
    )
}

const CellValue = ({
    record,
    columnKey,
    onToggleExpand,
    isExpanded,
}: {
    record: HierarchicalDedupeRecord
    columnKey: string
    onToggleExpand?: () => void
    isExpanded?: boolean
}) => {
    if (columnKey === EXPAND_COLUMN) {
        if (!record.children?.length) return null
        return (
            <Button
                isIconOnly
                size="sm"
                variant="light"
                onClick={onToggleExpand}
            >
                <div
                    className={`transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
                >
                    <ChevronRight size={16} />
                </div>
            </Button>
        )
    }

    if (columnKey === STATUS_COLUMN) {
        const dupeCount = record.children?.length ?? 0
        return (
            <StatusChip
                variant={record.status}
                dupeCount={dupeCount > 0 ? dupeCount : undefined}
            />
        )
    }

    if (record.status === 'deduped') {
        const originalValue = record.original_data[columnKey]
        const mergedValue = record.merged_data?.[columnKey]

        if (originalValue !== mergedValue) {
            return (
                <DiffCell oldText={originalValue} newText={mergedValue ?? ''} />
            )
        }
    }

    return record.status === 'deduped'
        ? record.merged_data?.[columnKey]
        : record.original_data[columnKey]
}

export const DedupeTable = ({
    records,
    columns,
}: {
    records: HierarchicalDedupeRecord[]
    columns: string[]
}) => {
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
    const displayColumns = [EXPAND_COLUMN, STATUS_COLUMN, ...columns]

    const toggleGroup = (groupId: string) => {
        setExpandedGroups((prev) => {
            const next = new Set(prev)
            if (next.has(groupId)) {
                next.delete(groupId)
            } else {
                next.add(groupId)
            }
            return next
        })
    }

    const flattenedRows = records.reduce<HierarchicalDedupeRecord[]>(
        (acc, record) => {
            acc.push(record)
            if (record.children && expandedGroups.has(record.groupId!)) {
                acc.push(...record.children)
            }
            return acc
        },
        []
    )

    return (
        <Table
            aria-label="Dedupe results table"
            isHeaderSticky={true}
            classNames={{
                tr: 'group-data-[parent=true]:bg-default-100',
            }}
        >
            <TableHeader columns={displayColumns}>
                {displayColumns.map((column) => (
                    <TableColumn
                        key={column}
                        width={column === EXPAND_COLUMN ? 24 : undefined}
                    >
                        {column === STATUS_COLUMN
                            ? 'Status'
                            : column === EXPAND_COLUMN
                              ? ''
                              : column}
                    </TableColumn>
                ))}
            </TableHeader>
            <TableBody>
                {flattenedRows.map((row) => (
                    <TableRow
                        key={row.id}
                        data-parent={row.isParent}
                        className={row.parentId ? 'pl-8 bg-default-50' : ''}
                    >
                        {(columnKey: Key) => (
                            <TableCell
                                className={
                                    columnKey === EXPAND_COLUMN ? 'px-0' : ''
                                }
                            >
                                <CellValue
                                    record={row}
                                    columnKey={columnKey as string}
                                    onToggleExpand={() =>
                                        row.groupId && toggleGroup(row.groupId)
                                    }
                                    isExpanded={
                                        row.groupId
                                            ? expandedGroups.has(row.groupId)
                                            : false
                                    }
                                />
                            </TableCell>
                        )}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    )
}
