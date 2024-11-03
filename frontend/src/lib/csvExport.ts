export function exportToCsv(
    data: Record<string, any>[],
    columns: string[],
    filename: string
) {
    // Create CSV header
    const header = columns.join(',')

    // Create CSV rows
    const rows = data.map((record) =>
        columns
            .map((col) => {
                const value = record[col]
                // Handle values that might contain commas or quotes
                if (
                    typeof value === 'string' &&
                    (value.includes(',') || value.includes('"'))
                ) {
                    return `"${value.replace(/"/g, '""')}"`
                }
                return value
            })
            .join(',')
    )

    // Combine header and rows
    const csv = [header, ...rows].join('\n')

    // Create and trigger download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', filename)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }
}
