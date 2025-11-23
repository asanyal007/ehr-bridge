import React, { useEffect } from 'react';
import { components, animations } from '../../designSystem';
import { createPortal } from 'react-dom';

const Modal = ({ isOpen, onClose, title, children, size = 'md' }) => {
    useEffect(() => {
        const handleEscape = (e) => {
            if (e.key === 'Escape') onClose();
        };

        if (isOpen) {
            document.body.style.overflow = 'hidden';
            window.addEventListener('keydown', handleEscape);
        }

        return () => {
            document.body.style.overflow = 'unset';
            window.removeEventListener('keydown', handleEscape);
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const maxWidthClass = {
        sm: 'sm:max-w-sm',
        md: 'sm:max-w-lg',
        lg: 'sm:max-w-2xl',
        xl: 'sm:max-w-4xl',
        full: 'sm:max-w-full sm:m-4'
    }[size] || 'sm:max-w-lg';

    return createPortal(
        <div className="relative z-50" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className={`${components.modal.overlay} ${animations.fadeIn}`} onClick={onClose}></div>

            <div className={components.modal.container}>
                <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
                    <div
                        className={`${components.modal.content} ${maxWidthClass} ${animations.pulse} sm:scale-100`}
                        onClick={e => e.stopPropagation()}
                    >
                        {title && (
                            <div className="bg-white px-4 py-3 sm:px-6 border-b border-gray-100 flex justify-between items-center">
                                <h3 className="text-lg font-semibold leading-6 text-gray-900" id="modal-title">
                                    {title}
                                </h3>
                                <button
                                    onClick={onClose}
                                    className="text-gray-400 hover:text-gray-500 focus:outline-none"
                                >
                                    <span className="sr-only">Close</span>
                                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        )}
                        <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4 text-left">
                            {children}
                        </div>
                    </div>
                </div>
            </div>
        </div>,
        document.body
    );
};

export default Modal;
