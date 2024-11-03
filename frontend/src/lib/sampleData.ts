export const sampleDatasets = [
    {
        key: 'people',
        label: 'People',
        description: 'Customer profile with name and email',
        url: '/samples/people.csv',
    },
    {
        key: 'companies',
        label: 'Companies',
        description: 'Business listing with industry and address',
        url: '/samples/companies.csv',
    },
    {
        key: 'products',
        label: 'Products',
        description: 'Inventory item with SKU and specifications',
        url: '/samples/products.csv',
    },
] as const
