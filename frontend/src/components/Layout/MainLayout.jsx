import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

const MainLayout = ({
    children,
    currentView,
    setCurrentView,
    sidebarCollapsed,
    setSidebarCollapsed,
    username,
    breadcrumbs
}) => {
    return (
        <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
            <Sidebar
                currentView={currentView}
                setCurrentView={setCurrentView}
                collapsed={sidebarCollapsed}
                setCollapsed={setSidebarCollapsed}
            />

            <Header
                collapsed={sidebarCollapsed}
                username={username}
                breadcrumbs={breadcrumbs}
            />

            <main
                className={`pt-24 pb-12 px-8 transition-all duration-300 min-h-screen ${sidebarCollapsed ? 'ml-20' : 'ml-64'
                    }`}
            >
                <div className="max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default MainLayout;
