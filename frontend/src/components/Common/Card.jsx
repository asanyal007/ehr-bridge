import React from 'react';
import { components } from '../../designSystem';

const Card = ({ children, className = '', compact = false, ...props }) => {
    const baseStyles = compact ? components.cardCompact : components.card;

    return (
        <div className={`${baseStyles} ${className}`} {...props}>
            {children}
        </div>
    );
};

export const CardHeader = ({ children, className = '' }) => (
    <div className={`${components.cardHeader} ${className}`}>
        {children}
    </div>
);

export const CardBody = ({ children, className = '' }) => (
    <div className={`${components.cardBody} ${className}`}>
        {children}
    </div>
);

export const CardFooter = ({ children, className = '' }) => (
    <div className={`${components.cardFooter} ${className}`}>
        {children}
    </div>
);

export default Card;
