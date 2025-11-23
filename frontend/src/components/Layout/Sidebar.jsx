import React from 'react';
import { components, colors } from '../../designSystem';
import Badge from '../Common/Badge';

const Sidebar = ({ currentView, setCurrentView, collapsed, setCollapsed }) => {
    const SidebarItem = ({ icon, label, view, badge = null }) => {
        const isActive = currentView === view;

        return (
            <button
                onClick={() => setCurrentView(view)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative ${isActive
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                title={collapsed ? label : ''}
            >
                <span className={`text-xl transition-colors ${isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-gray-600'}`}>
                    {icon}
                </span>
                {!collapsed && (
                    <>
                        <span className="flex-1 text-left text-sm">{label}</span>
                        {badge && <Badge variant="warning" className="ml-auto">{badge}</Badge>}
                    </>
                )}
            </button>
        );
    };

    return (
        <aside
            className={`fixed left-0 top-0 h-screen bg-white border-r border-gray-200 transition-all duration-300 z-40 flex flex-col ${collapsed ? 'w-20' : 'w-64'
                }`}
        >
            {/* Logo Area */}
            <div className="h-16 flex items-center px-4 border-b border-gray-100">
                <div className="flex items-center space-x-3 w-full">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center text-white font-bold shadow-sm flex-shrink-0">
                        AI
                    </div>
                    {!collapsed && (
                        <span className="font-bold text-gray-900 text-lg tracking-tight">EHR Bridge</span>
                    )}
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-8">
                {/* Primary Actions */}
                <div>
                    {!collapsed && (
                        <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Workflow</p>
                    )}
                    <div className="space-y-1">
                        <SidebarItem icon="🏥" label="Mapping Jobs" view="list" />
                        <SidebarItem icon="➕" label="Create Job" view="create" />
                        <SidebarItem icon="📡" label="Ingestion Pipelines" view="ingestion" />
                    </div>
                </div>

                {/* Data Viewers */}
                <div>
                    {!collapsed && (
                        <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Data Viewers</p>
                    )}
                    <div className="space-y-1">
                        <SidebarItem icon="📋" label="HL7 Messages" view="hl7viewer" />
                        <SidebarItem icon="🏷️" label="FHIR Resources" view="fhirviewer" />
                        <SidebarItem icon="🧬" label="OMOP Tables" view="omopviewer" />
                    </div>
                </div>

                {/* AI Tools */}
                <div>
                    {!collapsed && (
                        <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Intelligence</p>
                    )}
                    <div className="space-y-1">
                        <SidebarItem icon="💬" label="FHIR Chatbot" view="chatbot" />
                    </div>
                </div>
            </nav>

            {/* Footer / Collapse Toggle */}
            <div className="p-4 border-t border-gray-100">
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="w-full flex items-center justify-center p-2 rounded-lg text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition-colors"
                >
                    <span className="transform transition-transform duration-200" style={{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                        ◀
                    </span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
