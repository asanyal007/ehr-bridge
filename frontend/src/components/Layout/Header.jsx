import React from 'react';
import { components } from '../../designSystem';

const Header = ({
    collapsed,
    username,
    breadcrumbs,
    onLogout
}) => {
    return (
        <header
            className={`fixed top-0 right-0 h-16 bg-white/80 backdrop-blur-md border-b border-gray-200 z-30 transition-all duration-300 flex items-center justify-between px-6 ${collapsed ? 'left-20' : 'left-64'
                }`}
        >
            {/* Breadcrumbs */}
            <div className="flex items-center text-sm text-gray-500">
                {breadcrumbs}
            </div>

            {/* User Actions */}
            <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3 pl-4 border-l border-gray-200">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-medium text-gray-900">{username || 'Guest User'}</p>
                        <p className="text-xs text-gray-500">Administrator</p>
                    </div>
                    <div className="w-9 h-9 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold border-2 border-white shadow-sm">
                        {username ? username.charAt(0).toUpperCase() : 'G'}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
