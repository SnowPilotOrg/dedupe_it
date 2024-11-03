import {
    Button,
    Modal,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Input,
    Textarea,
} from '@nextui-org/react'
import { useState } from 'react'

interface UpgradeModalProps {
    isOpen: boolean
    onOpenChange: (isOpen: boolean) => void
}

export function UpgradeModal({ isOpen, onOpenChange }: UpgradeModalProps) {
    const [email, setEmail] = useState('')
    const [dataDescription, setDataDescription] = useState('')
    const [isValid, setIsValid] = useState(true)
    const [isLoading, setIsLoading] = useState(false)
    const [submitStatus, setSubmitStatus] = useState<
        'idle' | 'success' | 'error'
    >('idle')

    const validateEmail = (email: string) => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        return regex.test(email)
    }

    const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value
        setEmail(value)
        setIsValid(value === '' || validateEmail(value))
        setSubmitStatus('idle')
    }

    const handleSubmit = async () => {
        if (validateEmail(email)) {
            setIsLoading(true)
            try {
                const formData = new FormData()
                formData.append('u', '7f74a2ba4ae6c0447e9d58e4d')
                formData.append('id', 'd7b10a4c9c')
                formData.append('MERGE0', email)
                formData.append('MERGE1', dataDescription)

                const response = await fetch(
                    'https://snowpilot.us22.list-manage.com/subscribe/post',
                    {
                        method: 'POST',
                        body: formData,
                        mode: 'no-cors',
                    }
                )
                setSubmitStatus('success')
            } catch (error) {
                console.log(error)
                setSubmitStatus('error')
            } finally {
                setIsLoading(false)
            }
        }
    }

    return (
        <Modal isOpen={isOpen} onOpenChange={onOpenChange}>
            <ModalContent>
                {(onClose) => (
                    <>
                        <ModalHeader>Get Full Access</ModalHeader>
                        <ModalBody>
                            <div className="space-y-4">
                                {submitStatus === 'idle' && (
                                    <>
                                        <p className="text-default-700">
                                            Get unlimited access to all
                                            features:
                                        </p>
                                        <Input
                                            label="Email"
                                            type="email"
                                            value={email}
                                            onChange={handleEmailChange}
                                            isInvalid={!isValid}
                                            errorMessage={
                                                !isValid &&
                                                'Please enter a valid email'
                                            }
                                            name="MERGE0"
                                            isDisabled={isLoading}
                                        />
                                        <Textarea
                                            label="What data do you need to dedupe? (Optional)"
                                            value={dataDescription}
                                            onChange={(e) =>
                                                setDataDescription(
                                                    e.target.value
                                                )
                                            }
                                            name="MERGE1"
                                            isDisabled={isLoading}
                                        />
                                    </>
                                )}
                                {submitStatus === 'success' && (
                                    <div className="text-center py-4">
                                        <p className="text-success font-semibold text-lg mb-2">
                                            Thanks for signing up!
                                        </p>
                                        <p className="text-default-600">
                                            We'll be in touch soon with next
                                            steps.
                                        </p>
                                    </div>
                                )}
                                {submitStatus === 'error' && (
                                    <div className="text-center py-4">
                                        <p className="text-danger font-semibold text-lg mb-2">
                                            Something went wrong
                                        </p>
                                        <p className="text-default-600">
                                            Please try again or contact support
                                            at founders@snowpilot.com.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </ModalBody>
                        <ModalFooter>
                            <Button
                                variant="light"
                                onPress={onClose}
                                isDisabled={isLoading}
                            >
                                {submitStatus === 'success'
                                    ? 'Close'
                                    : 'Cancel'}
                            </Button>
                            {submitStatus === 'idle' && (
                                <Button
                                    color="primary"
                                    onPress={handleSubmit}
                                    isDisabled={
                                        !email ||
                                        !validateEmail(email) ||
                                        isLoading
                                    }
                                    isLoading={isLoading}
                                >
                                    Get Full Access
                                </Button>
                            )}
                        </ModalFooter>
                    </>
                )}
            </ModalContent>
        </Modal>
    )
}
