import React from 'react';
import { components } from '../../designSystem';

const Badge = ({ variant = 'info', children, className = '' }) => {
    const baseStyles = components.badge.base;
    const variantStyles = components.badge[variant] || components.badge.info;

    return (
        <span className={`${baseStyles} ${variantStyles} ${className}`}>
            {children}
        </span>
    );
};

export default Badge;
