import { Link } from '@tanstack/react-router'
import { Button } from '@nextui-org/react'
import { Sparkles } from 'lucide-react'

type TopBarProps = {
    showUpgradeButton?: boolean
    onUpgradeClick?: () => void
}

export function TopBar({
    showUpgradeButton = false,
    onUpgradeClick,
}: TopBarProps) {
    return (
        <div className="flex items-center flex-col gap-4 mb-8">
            <Link to="/" className="hover:opacity-80 transition-opacity">
                <h1 className="text-4xl font-['Permanent_Marker'] text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                    Dedupe It!
                </h1>
            </Link>
            <p className="text-md text-gray-700">
                Deduplicate your CSV in one click
            </p>
            {showUpgradeButton && (
                <div className="absolute top-4 right-4 hidden sm:block">
                    <Button
                        color="primary"
                        variant="ghost"
                        onPress={onUpgradeClick}
                        startContent={<Sparkles size={16} />}
                    >
                        Get Full Access
                    </Button>
                </div>
            )}
        </div>
    )
}
