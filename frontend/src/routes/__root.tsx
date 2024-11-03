import { Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { NextUIProvider } from '@nextui-org/react'
import { Toaster } from 'sonner'
import { DataProvider } from '../store/DataContext'

export const Route = createRootRoute({
    component: RootComponent,
})

function RootComponent() {
    const router = useRouter()

    return (
        <DataProvider>
            <NextUIProvider
                navigate={(to) => router.navigate({ to })}
                useHref={(to) => router.buildLocation({ to }).href}
            >
                <div className="min-h-screen p-4 bg-sky-50">
                    <Outlet />
                </div>
                <Toaster richColors position="top-center" />
            </NextUIProvider>
        </DataProvider>
    )
}
