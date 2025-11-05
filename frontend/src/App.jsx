import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { components, typography, shadows } from './designSystem';
import FHIRChatbot from './FHIRChatbot';
import ConceptReviewPanel from './ConceptReviewPanel';

// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Main Application Component
 * Single-file React application for AI Data Interoperability Platform
 * Healthcare/EHR/HL7 Data Mapping with Sentence-BERT
 * JWT Authentication, SQLite backend, containerized deployment
 */
function App() {
  // Authentication state
  const [token, setToken] = useState(null);
  const [userId, setUserId] = useState(null);
  const [username, setUsername] = useState(null);
  const [isAuthReady, setIsAuthReady] = useState(false);
  
  // Application state
  const [jobs, setJobs] = useState([]);
  const [currentView, setCurrentView] = useState('list'); // 'list', 'connector', 'review', 'terminology', 'transform', 'hl7viewer'
  const [currentJob, setCurrentJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Form state
  const [sourceSchema, setSourceSchema] = useState('');
  const [targetSchema, setTargetSchema] = useState('');
  const [sampleData, setSampleData] = useState('');
  const [selectedMappings, setSelectedMappings] = useState([]);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingJobId, setEditingJobId] = useState(null);
  
  // Dropdown options for manual mappings
  const [sourceFieldOptions, setSourceFieldOptions] = useState([]);
  const [targetFieldOptions, setTargetFieldOptions] = useState([]);

  // Terminology normalization state
  const [terminologySuggestions, setTerminologySuggestions] = useState([]);
  const [terminologyEdits, setTerminologyEdits] = useState({}); // { fieldPath: { sourceValue: { normalized, system?, code?, display? } } }
  const [terminologyLoading, setTerminologyLoading] = useState(false);
  const [terminologyError, setTerminologyError] = useState(null);
  
  // HL7 Viewer state
  const [stagedMessages, setStagedMessages] = useState([]);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [hl7Input, setHl7Input] = useState('');
  
  // Connector Configuration state (Azure Data Factory inspired)
  const [sourceConnector, setSourceConnector] = useState(null);
  const [targetConnector, setTargetConnector] = useState(null);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [fhirResourceType, setFhirResourceType] = useState('Patient');
  const [fhirResources, setFhirResources] = useState([]);

  // Ingestion job state
  const [ingestJobId, setIngestJobId] = useState(null);
  const [ingestStatus, setIngestStatus] = useState(null);
  const [ingestMetrics, setIngestMetrics] = useState(null);
  const [isIngestLoading, setIsIngestLoading] = useState(false);
  const [showIngestionModal, setShowIngestionModal] = useState(false);
  const [selectedIngestJobId, setSelectedIngestJobId] = useState('');

  // Ingestion jobs list screen state
  const [ingestionJobs, setIngestionJobs] = useState([]);
  const [isIngestionListLoading, setIsIngestionListLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [showLoadingCancel, setShowLoadingCancel] = useState(false);
  const [cancelTokenSource, setCancelTokenSource] = useState(null);

  // Records modal state
  const [showRecordsModal, setShowRecordsModal] = useState(false);
  const [recordsModalJobId, setRecordsModalJobId] = useState(null);
  const [recordsModalData, setRecordsModalData] = useState([]);
  const [recordsLoading, setRecordsLoading] = useState(false);

  // Failed records modal state
  const [showFailedModal, setShowFailedModal] = useState(false);
  const [failedModalJobId, setFailedModalJobId] = useState(null);
  const [failedModalData, setFailedModalData] = useState([]);
  const [failedLoading, setFailedLoading] = useState(false);

  // Data Model screen state
  const [showDataModel, setShowDataModel] = useState(false);
  const [dataModelTab, setDataModelTab] = useState('FHIR'); // 'FHIR' | 'OMOP'
  const [omopSubTab, setOmopSubTab] = useState('predict'); // 'predict', 'normalize', 'review', 'preview', 'persist'
  const [omopPrediction, setOmopPrediction] = useState(null);
  const [omopPreview, setOmopPreview] = useState({ table: null, rows: [], fieldCoverage: {} });
  const [omopConceptSuggestions, setOmopConceptSuggestions] = useState([]);
  const [omopConceptEdits, setOmopConceptEdits] = useState({});
  const [reviewQueueCount, setReviewQueueCount] = useState(0);
  
  // OMOP Compatible filter state
  const [showOMOPCompatibleOnly, setShowOMOPCompatibleOnly] = useState(false);
  const [omopCompatibleJobs, setOmopCompatibleJobs] = useState([]);
  const [selectedCompatibleJobId, setSelectedCompatibleJobId] = useState(null);

  // UI/UX Enhancement state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [sortBy, setSortBy] = useState('createdAt');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedJobs, setSelectedJobs] = useState([]);

  // Chatbot state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  /**
   * ============================================================================
   * REUSABLE UI COMPONENTS (Design System)
   * ============================================================================
   */
  
  // Button Component
  const Button = ({ variant = 'primary', children, className = '', ...props }) => (
    <button className={`${components.button[variant]} ${className}`} {...props}>
      {children}
    </button>
  );

  // Card Component
  const Card = ({ children, className = '', compact = false }) => (
    <div className={`${compact ? components.cardCompact : components.card} ${className}`}>
      {children}
    </div>
  );

  // Badge Component
  const Badge = ({ variant = 'info', children, className = '' }) => (
    <span className={`${components.badge[variant]} ${className}`}>
      {children}
    </span>
  );

  // Status Badge with automatic variant mapping
  const StatusBadge = ({ status }) => {
    const variantMap = {
      DRAFT: 'info',
      ANALYZING: 'warning',
      PENDING_REVIEW: 'warning',
      APPROVED: 'success',
      ERROR: 'error',
      COMPLETED: 'success',
      RUNNING: 'info',
      STOPPED: 'neutral',
      PAUSED: 'warning'
    };
    return <Badge variant={variantMap[status] || 'info'}>{status}</Badge>;
  };

  // Typography Components
  const H1 = ({ children, className = '' }) => (
    <h1 className={`${typography.h1} ${className}`}>{children}</h1>
  );
  
  const H2 = ({ children, className = '' }) => (
    <h2 className={`${typography.h2} ${className}`}>{children}</h2>
  );
  
  const H3 = ({ children, className = '' }) => (
    <h3 className={`${typography.h3} ${className}`}>{children}</h3>
  );
  
  const Label = ({ children, className = '' }) => (
    <label className={`${typography.label} ${className}`}>{children}</label>
  );
  
  const Caption = ({ children, className = '' }) => (
    <p className={`${typography.caption} ${className}`}>{children}</p>
  );

  /**
   * Toast Notification System
   */
  const showToast = (message, type = 'info', duration = 3000) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  };

  const ToastContainer = () => (
    <div className="fixed top-20 right-4 z-50 space-y-2">
      {toasts.map(toast => (
        <div 
          key={toast.id} 
          className={`${components.card} ${
            toast.type === 'success' ? 'border-l-4 border-green-500' :
            toast.type === 'error' ? 'border-l-4 border-red-500' :
            toast.type === 'warning' ? 'border-l-4 border-yellow-500' :
            'border-l-4 border-blue-500'
          } shadow-lg animate-slide-in-right min-w-[300px]`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{toast.message}</span>
            <button 
              onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} 
              className="ml-4 text-gray-400 hover:text-gray-600 font-bold"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  /**
   * Info Tooltip Component
   */
  const InfoTooltip = ({ content }) => (
    <div className="inline-block group relative">
      <span className="ml-1 text-gray-400 hover:text-gray-600 cursor-help text-sm">ⓘ</span>
      <div className="absolute z-50 hidden group-hover:block bg-gray-900 text-white text-xs 
        rounded-lg p-3 w-64 -mt-2 ml-2 shadow-xl pointer-events-none">
        {content}
        <div className="absolute top-4 -left-1 w-2 h-2 bg-gray-900 transform rotate-45" />
      </div>
    </div>
  );

  /**
   * Collapsible Section Component
   */
  const CollapsibleSection = ({ title, children, defaultOpen = false }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    
    return (
      <div className="border-b border-gray-200 py-4">
        <button 
          onClick={() => setIsOpen(!isOpen)} 
          className="w-full flex justify-between items-center text-left font-semibold text-gray-700 hover:text-gray-900 transition-colors"
        >
          <span>{title}</span>
          <span className={`transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>
        {isOpen && <div className="mt-4">{children}</div>}
      </div>
    );
  };

  /**
   * Sidebar Navigation Component
   */
  const Sidebar = () => {
    const SidebarItem = ({ icon, label, view, badge = null }) => {
      const isActive = currentView === view;
      return (
        <button
          onClick={() => setCurrentView(view)}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-150 ${
            isActive 
              ? 'bg-amber-100 text-amber-800 font-semibold' 
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <span className="text-xl">{icon}</span>
          {!sidebarCollapsed && (
            <>
              <span className="flex-1 text-left">{label}</span>
              {badge && <Badge variant="warning">{badge}</Badge>}
            </>
          )}
        </button>
      );
    };

    return (
      <aside className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white border-r-2 
        border-amber-200 shadow-lg transition-all duration-300 z-40 
        ${sidebarCollapsed ? 'w-20' : 'w-64'}`}>
        <nav className="p-4 overflow-y-auto h-full">
          {/* Primary Actions */}
          <div className="mb-6">
            {!sidebarCollapsed && (
              <p className="text-xs font-semibold text-gray-500 mb-2 px-2">WORKFLOWS</p>
            )}
            <div className="space-y-1">
              <SidebarItem icon="🏥" label="Mapping Jobs" view="list" />
              <SidebarItem icon="📡" label="Ingestion Pipelines" view="ingestion" />
            </div>
          </div>

          {/* Data Viewers */}
          <div className="mb-6 border-t pt-4">
            {!sidebarCollapsed && (
              <p className="text-xs font-semibold text-gray-500 mb-2 px-2">DATA VIEWERS</p>
            )}
            <div className="space-y-1">
              <SidebarItem icon="📋" label="HL7 Messages" view="hl7viewer" />
              <SidebarItem icon="🏷️" label="FHIR Resources" view="fhirviewer" />
              <SidebarItem icon="🧬" label="OMOP Tables" view="omopviewer" />
            </div>
          </div>

          {/* AI Tools */}
          <div className="mb-6 border-t pt-4">
            {!sidebarCollapsed && (
              <p className="text-xs font-semibold text-gray-500 mb-2 px-2">AI TOOLS</p>
            )}
            <div className="space-y-1">
              <SidebarItem icon="💬" label="FHIR Chatbot" view="chatbot" />
            </div>
          </div>
        </nav>
      </aside>
    );
  };

  /**
   * Breadcrumb Navigation Component
   */
  const Breadcrumbs = () => {
    const pathsMap = {
      list: ['Home', 'Mapping Jobs'],
      connector: ['Home', 'Mapping Jobs', 'Configure'],
      review: ['Home', 'Mapping Jobs', currentJob?.jobId?.substring(0,8) || 'Job', 'Review'],
      terminology: ['Home', 'Mapping Jobs', currentJob?.jobId?.substring(0,8) || 'Job', 'Terminology'],
      transform: ['Home', 'Mapping Jobs', currentJob?.jobId?.substring(0,8) || 'Job', 'Transform'],
      ingestion: ['Home', 'Ingestion Pipelines'],
      hl7viewer: ['Home', 'Data Viewers', 'HL7 Messages'],
      fhirviewer: ['Home', 'Data Viewers', 'FHIR Resources'],
      omopviewer: ['Home', 'Data Viewers', 'OMOP Tables'],
      chatbot: ['Home', 'AI Tools', 'FHIR Chatbot']
    };

    const paths = pathsMap[currentView] || ['Home'];

    return (
      <div className="text-sm text-gray-600 mb-4 flex items-center space-x-2">
        {paths.map((path, idx) => (
          <React.Fragment key={idx}>
            {idx > 0 && <span className="text-gray-400">/</span>}
            <span className={idx === paths.length - 1 ? 'font-semibold text-gray-900' : 'hover:text-amber-600 cursor-pointer'}>
              {path}
            </span>
          </React.Fragment>
        ))}
      </div>
    );
  };

  /**
   * Bulk Actions Bar
   */
  const BulkActionsBar = () => selectedJobs.length > 0 && (
    <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-amber-600 text-white 
      rounded-full shadow-2xl px-6 py-3 flex items-center space-x-4 z-50 animate-slide-in-left">
      <span className="font-semibold">{selectedJobs.length} selected</span>
      <button 
        onClick={() => {
          if (window.confirm(`Delete ${selectedJobs.length} job(s)?`)) {
            showToast(`Deleted ${selectedJobs.length} jobs`, 'success');
            setSelectedJobs([]);
          }
        }}
        className="hover:underline"
      >
        Delete
      </button>
      <button 
        onClick={() => {
          showToast('Export feature coming soon!', 'info');
        }}
        className="hover:underline"
      >
        Export
      </button>
      <button onClick={() => setSelectedJobs([])} className="ml-4 font-bold text-lg">×</button>
    </div>
  );

  /**
   * ============================================================================
   * END REUSABLE COMPONENTS
   * ============================================================================
   */

  /**
   * Initialize app and handle authentication
   */
  useEffect(() => {
    const initAuth = async () => {
      // Check if token exists in localStorage
      const storedToken = localStorage.getItem('auth_token');
      const storedUserId = localStorage.getItem('user_id');
      const storedUsername = localStorage.getItem('username');
      
      if (storedToken && storedUserId) {
        // Use stored credentials
        setToken(storedToken);
        setUserId(storedUserId);
        setUsername(storedUsername || storedUserId);
        setIsAuthReady(true);
      } else {
        // Generate demo token for first-time users
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/demo-token`);
          const { token: newToken, userId: newUserId, username: newUsername } = response.data;
          
          // Store credentials
          localStorage.setItem('auth_token', newToken);
          localStorage.setItem('user_id', newUserId);
          localStorage.setItem('username', newUsername);
          
          setToken(newToken);
          setUserId(newUserId);
          setUsername(newUsername);
          setIsAuthReady(true);
        } catch (err) {
          console.error('Authentication error:', err);
          setError('Failed to authenticate. Please refresh the page.');
        }
      }
    };
    
    initAuth();
  }, []);

  /**
   * Fetch jobs from API
   */
  const fetchJobs = async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/jobs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: {
          user_id: userId
        }
      });
      setJobs(response.data);
    } catch (err) {
      console.error('Error fetching jobs:', err);
    }
  };

  /**
   * Fetch OMOP-compatible job IDs
   */
  const fetchOMOPCompatibleJobs = async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/omop/compatible-jobs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setOmopCompatibleJobs(response.data.compatible_jobs || []);
    } catch (err) {
      console.error('Error fetching OMOP-compatible jobs:', err);
    }
  };

  /**
   * Fetch jobs on mount and when auth is ready
   * Skip auto-refresh when modals are open or on viewer pages to prevent closing them
   */
  useEffect(() => {
    if (isAuthReady) {
      fetchJobs();
      // Refresh jobs every 5 seconds (but not when modals are open or on viewer pages)
      const interval = setInterval(() => {
        // Don't auto-refresh if any modal is open or on viewer pages
        const isModalOpen = showRecordsModal || showFailedModal || showDataModel || showIngestionModal;
        const isOnViewerPage = currentView === 'fhirviewer' || currentView === 'hl7viewer' || currentView === 'omopviewer' || currentView === 'chatbot' || currentView === 'ingestion';
        
        if (!isModalOpen && !isOnViewerPage) {
          fetchJobs();
        }
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isAuthReady, token, showRecordsModal, showFailedModal, showDataModel, showIngestionModal, currentView]);

  /**
   * Fetch OMOP-compatible jobs when checkbox is enabled
   */
  useEffect(() => {
    if (showOMOPCompatibleOnly && isAuthReady) {
      fetchOMOPCompatibleJobs();
    }
  }, [showOMOPCompatibleOnly, isAuthReady, token]);

  /**
   * Keyboard Shortcuts
   */
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Don't interfere with typing in input fields
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }
      
      if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
          case 'k': // Cmd/Ctrl+K: Quick search (placeholder)
            e.preventDefault();
            showToast('Quick search coming soon! Use Cmd+K', 'info');
            break;
          case 'n': // Cmd/Ctrl+N: New job
            e.preventDefault();
            if (currentView === 'list') {
              startNewJob();
              showToast('Starting new mapping job', 'success');
            }
            break;
          case 'h': // Cmd/Ctrl+H: Home
            e.preventDefault();
            setCurrentView('list');
            showToast('Navigated to home', 'success');
            break;
          default:
            break;
        }
      }
      if (e.key === 'Escape' && currentView !== 'list') {
        setCurrentView('list');
        showToast('Navigated to home', 'info');
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentView]);

  /**
   * Create a new mapping job
   */
  const createJob = async () => {
    if (!sourceSchema || !targetSchema) {
      setError('Please provide both source and target schemas');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Parse schemas
      const sourceParsed = JSON.parse(sourceSchema);
      const targetParsed = JSON.parse(targetSchema);
      
      // Extract field options for dropdowns
      const sourceFields = Object.keys(sourceParsed);
      setSourceFieldOptions(sourceFields);
      
      const targetFields = extractFhirPaths(targetParsed);
      setTargetFieldOptions(targetFields);
      
      // Create job via API
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/jobs`,
        {
          sourceSchema: sourceParsed,
          targetSchema: targetParsed,
          userId: userId
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setCurrentJob(response.data);
      setCurrentView('configure');
      fetchJobs(); // Refresh job list
    } catch (err) {
      console.error('Error creating job:', err);
      setError(`Failed to create job: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Analyze schemas with Sentence-BERT AI
   */
  const analyzeSchemas = async () => {
    if (!currentJob) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/jobs/${currentJob.jobId}/analyze`,
        { userId: userId },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      setCurrentJob(response.data);
      setSelectedMappings(response.data.suggestedMappings.map(m => ({...m, isApproved: false})));
      
      // Extract field options for dropdowns
      if (response.data.sourceSchema) {
        const sourceFields = Object.keys(response.data.sourceSchema);
        setSourceFieldOptions(sourceFields);
      }
      if (response.data.targetSchema) {
        const targetFields = extractFhirPaths(response.data.targetSchema);
        setTargetFieldOptions(targetFields);
      }
      
      setCurrentView('review');
      fetchJobs(); // Refresh job list
    } catch (err) {
      console.error('Error analyzing schemas:', err);
      setError(`Failed to analyze schemas: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Toggle mapping approval
   */
  const toggleMappingApproval = (index) => {
    const updated = [...selectedMappings];
    updated[index].isApproved = !updated[index].isApproved;
    updated[index].isRejected = false;
    setSelectedMappings(updated);
  };

  /**
   * Toggle mapping rejection
   */
  const toggleMappingRejection = (index) => {
    const updated = [...selectedMappings];
    updated[index].isRejected = !updated[index].isRejected;
    updated[index].isApproved = false;
    setSelectedMappings(updated);
  };

  /**
   * Extract FHIR paths from schema
   */
  const extractFhirPaths = (schema) => {
    const paths = [];
    
    // Check if it's a FHIR schema (has resourceType or FHIR-like structure)
    const isFhir = Object.keys(schema).some(k => 
      k.includes('.') || k.includes('[') || k === 'resourceType'
    );
    
    if (isFhir) {
      // Extract nested FHIR paths like Patient.name[0].family
      Object.keys(schema).forEach(key => {
        if (key.includes('.')) {
          paths.push(key);
        } else {
          // Simple fields
          paths.push(key);
        }
      });
    } else {
      // Regular schema (CSV, etc.)
      paths.push(...Object.keys(schema));
    }
    
    return paths.sort();
  };

  /**
   * Add manual mapping
   */
  const addManualMapping = () => {
    const newMapping = {
      sourceField: '',
      targetField: '',
      confidenceScore: 1.0,
      suggestedTransform: 'DIRECT',
      isApproved: true,
      isRejected: false,
      isManual: true
    };
    setSelectedMappings([...selectedMappings, newMapping]);
  };

  /**
   * Generate terminology suggestions (post-mapping step)
   */
  const generateTerminology = async () => {
    if (!currentJob) return;
    setTerminologyLoading(true);
    setTerminologyError(null);
    try {
      // Collect a small sample dataset for terminology analysis
      const sample = [
        {
          patient_first_name: 'John',
          patient_last_name: 'Doe',
          gender: 'M',
          primary_diagnosis_icd10: 'C50.9'
        }
      ];
      const res = await axios.post(
        `${API_BASE_URL}/api/v1/terminology/normalize/${currentJob.jobId}`,
        {
          sampleData: sample,
          sampleSize: 200
        },
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      const { suggestions } = res.data || { suggestions: [] };
      setTerminologySuggestions(suggestions || []);
      // Initialize edit map
      const initEdits = {};
      (suggestions || []).forEach(s => {
        initEdits[s.fieldPath] = {};
        (s.candidates || []).forEach(c => {
          initEdits[s.fieldPath][c.sourceValue] = {
            normalized: c.normalized,
            system: c.system || '',
            code: c.code || '',
            display: c.display || ''
          };
        });
      });
      setTerminologyEdits(initEdits);
      setCurrentView('terminology');
    } catch (err) {
      console.error('Error generating terminology suggestions:', err);
      setTerminologyError(`Failed to generate terminology: ${err.response?.data?.detail || err.message}`);
    } finally {
      setTerminologyLoading(false);
    }
  };

  /**
   * Save terminology normalization
   */
  const saveTerminology = async () => {
    if (!currentJob) return;
    setTerminologyLoading(true);
    setTerminologyError(null);
    try {
      const items = Object.keys(terminologyEdits).map(fieldPath => ({
        fieldPath,
        strategy: 'hybrid',
        system: (terminologySuggestions.find(s => s.fieldPath === fieldPath)?.suggestedSystem) || undefined,
        mapping: terminologyEdits[fieldPath],
        approvedBy: userId
      }));
      await axios.put(
        `${API_BASE_URL}/api/v1/terminology/${currentJob.jobId}`,
        {
          items,
          cacheAlso: true
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setCurrentView('review');
    } catch (err) {
      console.error('Error saving terminology:', err);
      setTerminologyError(`Failed to save terminology: ${err.response?.data?.detail || err.message}`);
    } finally {
      setTerminologyLoading(false);
    }
  };

  /**
   * Update manual mapping
   */
  const updateManualMapping = (index, field, value) => {
    const updated = [...selectedMappings];
    updated[index][field] = value;
    setSelectedMappings(updated);
  };

  /**
   * Validate manual mapping
   */
  const validateManualMapping = (mapping) => {
    if (!mapping.sourceField || !mapping.targetField) {
      return { valid: false, message: 'Both source and target fields are required' };
    }
    return { valid: true };
  };

  /**
   * Finalize and approve mappings
   */
  const approveMappings = async () => {
    if (!currentJob) return;
    
    // Validate manual mappings
    const manualMappings = selectedMappings.filter(m => m.isManual && m.isApproved);
    for (const mapping of manualMappings) {
      const validation = validateManualMapping(mapping);
      if (!validation.valid) {
        alert(`Invalid manual mapping: ${validation.message}`);
        return;
      }
    }
    
    // Get only approved mappings
    const finalMappings = selectedMappings.filter(m => m.isApproved && !m.isRejected);
    
    if (finalMappings.length === 0) {
      setError('Please approve at least one mapping');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.put(
        `${API_BASE_URL}/api/v1/jobs/${currentJob.jobId}/approve`,
        {
          finalMappings: finalMappings,
          userId: userId
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      // Update job and navigate to connector view
      setCurrentJob(response.data);
      setCurrentView('connector');
      
      // Automatically create and start an ingestion pipeline
      await createIngestionJob();
      await startIngestionJob();
      
      // Keep schemas/connectors so the ingestion panel remains visible
      fetchJobs(); // Refresh job list
    } catch (err) {
      console.error('Error approving mappings:', err);
      setError(`Failed to approve mappings: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Test transformation
   */
  const testTransformation = async () => {
    if (!currentJob || !sampleData) {
      setError('Please provide sample data');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const sampleParsed = JSON.parse(sampleData);
      const dataArray = Array.isArray(sampleParsed) ? sampleParsed : [sampleParsed];
      
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/jobs/${currentJob.jobId}/transform`,
        {
          mappings: currentJob.finalMappings,
          sampleData: dataArray
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      alert(`Transformation successful!\n\nTransformed ${response.data.recordCount} records.\n\nCheck console for results.`);
      console.log('Transformation Results:', response.data);
    } catch (err) {
      console.error('Error testing transformation:', err);
      setError(`Failed to test transformation: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Generate OMOP concept suggestions for fields that need normalization
   */
  const generateOmopConcepts = async () => {
    if (!currentJob) return;
    try {
      // Determine OMOP table from prediction or default
      const targetTable = omopPrediction?.table || 'PERSON';
      
      // Fetch sample records to extract real values
      let sampleRecords = [];
      try {
        const ingestResp = await axios.get(`${API_BASE_URL}/api/v1/ingestion/records/${currentJob.jobId}?limit=10`, { headers: { ...authHeaders } });
        sampleRecords = ingestResp.data.records || [];
      } catch (e) {
        console.warn('Could not fetch ingested records, using synthetic data');
      }

      // Map OMOP table to fields that need concept normalization
      const domainFields = {};
      if (targetTable === 'CONDITION_OCCURRENCE') {
        domainFields['condition_concept_id'] = {
          domain: 'Condition',
          sourceFields: ['primary_diagnosis_icd10', 'diagnosis_code', 'icd10', 'icd_code']
        };
      } else if (targetTable === 'MEASUREMENT') {
        domainFields['measurement_concept_id'] = {
          domain: 'Measurement',
          sourceFields: ['loinc', 'lab_code', 'test_code']
        };
      } else if (targetTable === 'DRUG_EXPOSURE') {
        domainFields['drug_concept_id'] = {
          domain: 'Drug',
          sourceFields: ['drug', 'medication', 'rxnorm', 'drug_code']
        };
      }

      const suggestions = {};
      let lastDataSource = 'unknown';  // Track data source from API responses
      
      for (const [field, config] of Object.entries(domainFields)) {
        // Extract actual values from sample records
        let sampleValues = [];
        for (const record of sampleRecords) {
          for (const sourceField of config.sourceFields) {
            const val = record[sourceField];
            if (val && !sampleValues.includes(val)) {
              sampleValues.push(val);
            }
          }
        }
        
        // Fallback to synthetic examples if no real data
        if (sampleValues.length === 0) {
          sampleValues = config.domain === 'Condition' ? ['C50.9', 'E11.9', 'I10'] :
                        config.domain === 'Measurement' ? ['2951-2', '2345-7', '718-7'] :
                        ['6809', '10600', 'C258'];
        }

        // Limit to first 10 unique values
        sampleValues = sampleValues.slice(0, 10);

        const resp = await axios.post(`${API_BASE_URL}/api/v1/omop/concepts/normalize`,
          { 
            values: sampleValues.length > 0 ? sampleValues : null,  // Pass null if no values to trigger auto-fetch
            domain: config.domain,
            job_id: currentJob.jobId,  // Pass job_id for automatic data extraction
            target_table: targetTable  // Pass target table to help field inference
          },
          { headers: { ...authHeaders } }
        );
        
        // Check if backend returned no data
        if (!resp.data.success) {
          alert(`❌ ${resp.data.message || 'No concepts to map for this job.'}`);
          return;
        }
        
        suggestions[field] = resp.data.suggestions;
        lastDataSource = resp.data.source || lastDataSource;  // Track the data source
      }

      // Check if we got any suggestions
      const totalMappings = Object.values(suggestions).flat().length;
      if (totalMappings === 0) {
        alert(`❌ No concepts to map.\n\nNo ${targetTable} data found for job: ${currentJob.jobId}\n\nPlease ensure you have ingested data for this resource type.`);
        return;
      }

      setOmopConceptSuggestions(suggestions);

      // Initialize edits
      const edits = {};
      Object.keys(suggestions).forEach(field => {
        edits[field] = {};
        suggestions[field].forEach(s => {
          edits[field][s.source_value] = {
            concept_id: s.concept_id,
            concept_name: s.concept_name,
            vocabulary_id: s.vocabulary_id,
            concept_code: s.concept_code
          };
        });
      });
      setOmopConceptEdits(edits);
      
      // Show success message with data source info
      const sourceLabel = lastDataSource === 'real_data' ? '✅ from real FHIR data' : 
                          lastDataSource === 'provided_values' ? 'from provided values' :
                          lastDataSource === 'none' ? '❌ no data found' : 'unknown source';
      
      alert(`✅ Generated ${totalMappings} concept mapping(s) for ${targetTable}\n\nData source: ${sourceLabel}`);
    } catch (e) {
      console.error('OMOP concept generation error:', e);
      alert(`Failed to generate concept suggestions: ${e.response?.data?.detail || e.message}`);
    }
  };

  /**
   * Save OMOP concept mappings
   */
  const saveOmopConcepts = async () => {
    if (!currentJob) return;
    try {
      // Save concept mappings
      for (const [field, edits] of Object.entries(omopConceptEdits)) {
        await axios.put(`${API_BASE_URL}/api/v1/omop/concepts/approve`,
          {
            job_id: currentJob.jobId,
            field_path: field,
            mapping: edits,
            approved_by: userId
          },
          { headers: { ...authHeaders } }
        );
      }
      
      // Automatically trigger OMOP persistence after saving mappings
      try {
        const persistResp = await axios.post(`${API_BASE_URL}/api/v1/omop/persist-all`, 
          { 
            job_id: currentJob.jobId, 
            table: omopPrediction?.table || omopPreview?.table || null 
          }, 
          { headers: { ...authHeaders } }
        );
        
        const data = persistResp.data;
        const message = `✅ Concept Mappings Saved & OMOP Persisted!\n\n` +
          `Table: omop_${data.table || 'PERSON'}\n` +
          `Inserted/Updated: ${data.inserted || 0} rows\n` +
          `Total Records Found: ${data.total_records_found || 0}\n` +
          `Source: ${data.source || 'Unknown'}\n` +
          `Job ID: ${currentJob.jobId.substring(0, 16)}...`;
        alert(message);
      } catch (persistError) {
        console.warn('OMOP persistence failed, but mappings were saved:', persistError);
        alert('Concept mappings saved successfully, but OMOP persistence failed. You can manually trigger persistence from the Persist tab.');
      }
    } catch (e) {
      console.error('Save OMOP concepts error:', e);
      alert('Failed to save concept mappings.');
    }
  };

  /**
   * Start new job flow
   */
  const startNewJob = () => {
    setCurrentJob(null);
    setCurrentView('connector');
    setSourceSchema('');
    setTargetSchema('');
    setSampleData('');
    setSelectedMappings([]);
    setSourceConnector(null);
    setTargetConnector(null);
    setError(null);
  };

  /**
   * Connector templates
   */
  const connectorTypes = [
    { id: 'hl7_api', name: 'HL7 API', icon: '📡', color: 'blue', description: 'HL7 v2 Interface' },
    { id: 'csv_file', name: 'CSV File', icon: '📄', color: 'green', description: 'Flat File' },
    { id: 'mongodb', name: 'MongoDB', icon: '🍃', color: 'emerald', description: 'Document Database' },
    { id: 'data_warehouse', name: 'Data Warehouse', icon: '🏢', color: 'purple', description: 'SQL Database' },
    { id: 'fhir_api', name: 'FHIR API', icon: '🔥', color: 'orange', description: 'FHIR Server' },
    { id: 'json_api', name: 'JSON API', icon: '🔌', color: 'cyan', description: 'REST API' }
  ];

  /**
   * Set source connector
   */
  const selectSourceConnector = (connector) => {
    setSourceConnector(connector);
    setShowSourceModal(true);
  };

  /**
   * Set target connector
   */
  const selectTargetConnector = async (connector) => {
    setTargetConnector(connector);
    
    // If MongoDB, load FHIR resources
    if (connector.id === 'mongodb' || connector.id === 'fhir_api') {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/v1/fhir/resources`);
        setFhirResources(response.data.resources || []);
      } catch (err) {
        console.error('Error loading FHIR resources:', err);
        setFhirResources(['Patient', 'Observation', 'Condition']);
      }
    }
    
    setShowTargetModal(true);
  };

  /**
   * Load FHIR schema for selected resource type
   */
  const loadFHIRSchema = async (resourceType) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/fhir/schema/${resourceType}`);
      const schemaJson = JSON.stringify(response.data.schema, null, 2);
      setTargetSchema(schemaJson);
      setFhirResourceType(resourceType);
    } catch (err) {
      console.error('Error loading FHIR schema:', err);
      setError(`Failed to load FHIR schema: ${err.message}`);
    }
  };

  /**
   * Predict FHIR resource using Gemini AI
   */
  const predictFHIRResource = async () => {
    if (!sourceSchema) {
      setError('Please configure source schema first');
      return;
    }
    
    setLoading(true);
    
    try {
      const sourceParsed = JSON.parse(sourceSchema);
      
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/fhir/predict-resource`,
        sourceParsed,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      const prediction = response.data;
      
      // Set predicted resource
      setFhirResourceType(prediction.predictedResource);
      
      // Load FHIR schema for predicted resource
      const schemaJson = JSON.stringify(prediction.fhirSchema, null, 2);
      setTargetSchema(schemaJson);
      
      // Show prediction to user
      alert(
        `🔥 AI Predicted FHIR Resource: ${prediction.predictedResource}\n\n` +
        `Confidence: ${(prediction.confidence * 100).toFixed(0)}%\n\n` +
        `Reasoning: ${prediction.reasoning}\n\n` +
        `Key Indicators: ${prediction.keyIndicators.join(', ')}`
      );
      
      console.log('FHIR Resource Prediction:', prediction);
    } catch (err) {
      console.error('Error predicting FHIR resource:', err);
      setError(`Failed to predict FHIR resource: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Save connector configuration
   */
  const saveConnectorConfig = (isSource) => {
    if (isSource) {
      setShowSourceModal(false);
    } else {
      setShowTargetModal(false);
    }
  };

  /**
   * Generate mappings from connector config
   */
  const generateMappingsFromConnectors = async () => {
    if (!sourceSchema || !targetSchema) {
      setError('Please configure both source and target schemas');
      return;
    }
    
    // Create job first
    await createJob();
  };

  /**
   * Load staged HL7 messages for a job
   */
  const loadStagedMessages = async (jobId) => {
    if (!token) return;
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/hl7/messages/${jobId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      setStagedMessages(response.data.messages || []);
    } catch (err) {
      console.error('Error loading staged messages:', err);
      setStagedMessages([]);
    }
  };

  /**
   * Handle CSV file upload and schema inference
   */
  const handleCSVUpload = async (event, isSource) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/csv/infer-schema`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      const { schema, columnCount, rowCount, preview } = response.data;
      
      // Set the inferred schema
      const schemaJson = JSON.stringify(schema, null, 2);
      if (isSource) {
        setSourceSchema(schemaJson);
        alert(`CSV Schema Inferred!\n\n${columnCount} columns detected from ${rowCount} rows.\n\nSchema auto-populated. Review and save.`);
      } else {
        setTargetSchema(schemaJson);
        alert(`CSV Schema Inferred!\n\n${columnCount} columns detected from ${rowCount} rows.\n\nSchema auto-populated. Review and save.`);
      }
      
      console.log('CSV Preview (first 5 rows):', preview);
    } catch (err) {
      console.error('Error uploading CSV:', err);
      setError(`Failed to infer schema from CSV: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Ingest HL7 message
   */
  const ingestHL7Message = async () => {
    if (!hl7Input || !currentJob) {
      setError('Please provide an HL7 message');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const messageId = `MSG_${Date.now()}`;
      
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/hl7/ingest`,
        {
          jobId: currentJob.jobId,
          messageId: messageId,
          rawMessage: hl7Input,
          messageType: 'HL7_V2'
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      alert(`HL7 Message ingested successfully!\n\nMessage ID: ${response.data.messageId}\nSegments: ${response.data.segments.join(', ')}`);
      setHl7Input('');
      loadStagedMessages(currentJob.jobId);
    } catch (err) {
      console.error('Error ingesting HL7:', err);
      setError(`Failed to ingest HL7 message: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * View job details
   */
  const viewJobDetails = (job) => {
    setCurrentJob(job);

    // Pre-populate schemas from job
    if (job.sourceSchema) {
      setSourceSchema(JSON.stringify(job.sourceSchema, null, 2));
      // Extract source field options
      const sourceFields = Object.keys(job.sourceSchema);
      setSourceFieldOptions(sourceFields);
    }
    if (job.targetSchema) {
      setTargetSchema(JSON.stringify(job.targetSchema, null, 2));
      // Extract target field options (handle FHIR nested paths)
      const targetFields = extractFhirPaths(job.targetSchema);
      setTargetFieldOptions(targetFields);
    }

    // Navigate to appropriate view based on status
    if (job.status === 'APPROVED') {
      setCurrentView('transform');
    } else if (job.status === 'PENDING_REVIEW') {
      setSelectedMappings(job.suggestedMappings || []);
      setCurrentView('review');
    } else if (job.status === 'DRAFT' || job.status === 'ANALYZING') {
      // For draft jobs, show connector view with schemas pre-populated
      setCurrentView('connector');

      // Set up default connectors if schemas exist
      if (job.sourceSchema && !sourceConnector) {
        // Auto-select a connector based on schema structure
        const hasHL7Fields = Object.keys(job.sourceSchema).some(k => k.includes('PID-') || k.includes('OBX-'));
        if (hasHL7Fields) {
          setSourceConnector(connectorTypes.find(c => c.id === 'hl7_api'));
        } else {
          setSourceConnector(connectorTypes.find(c => c.id === 'csv_file'));
        }
      }

      if (job.targetSchema && !targetConnector) {
        setTargetConnector(connectorTypes.find(c => c.id === 'data_warehouse'));
      }
    } else {
      setCurrentView('connector');
    }
  };

  /**
   * Edit existing job - load job data for editing
   */
  const editJob = (job) => {
    setEditingJobId(job.jobId);
    setIsEditMode(true);
    setCurrentJob(job);

    // Pre-populate schemas from job
    if (job.sourceSchema) {
      setSourceSchema(JSON.stringify(job.sourceSchema, null, 2));
      // Extract source field options
      const sourceFields = Object.keys(job.sourceSchema);
      setSourceFieldOptions(sourceFields);
    }
    if (job.targetSchema) {
      setTargetSchema(JSON.stringify(job.targetSchema, null, 2));
      // Extract target field options (handle FHIR nested paths)
      const targetFields = extractFhirPaths(job.targetSchema);
      setTargetFieldOptions(targetFields);
    }

    // Pre-populate connectors if available
    if (job.sourceConnector) {
      setSourceConnector(job.sourceConnector);
    }
    if (job.targetConnector) {
      setTargetConnector(job.targetConnector);
    }

    setCurrentView('connector');
    setSelectedMappings(job.finalMappings || []);
  };

  /**
   * Update job schemas via API
   */
  const updateJobSchemas = async () => {
    if (!editingJobId) return;

    setLoading(true);
    setError(null);

    try {
      // Parse schemas
      const sourceParsed = JSON.parse(sourceSchema);
      const targetParsed = JSON.parse(targetSchema);

      // Update job via API
      const response = await axios.put(
        `${API_BASE_URL}/api/v1/jobs/${editingJobId}/schemas`,
        {
          sourceSchema: sourceParsed,
          targetSchema: targetParsed,
          userId: userId
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      // Update local job state
      setCurrentJob(response.data);

      // Re-run analysis
      await analyzeSchemas();

      // Exit edit mode
      setIsEditMode(false);
      setEditingJobId(null);

      fetchJobs(); // Refresh job list
    } catch (err) {
      console.error('Error updating job schemas:', err);
      setError(`Failed to update job schemas: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get status badge color
   */
  const getStatusColor = (status) => {
    const colors = {
      'DRAFT': 'bg-gray-200 text-gray-800',
      'ANALYZING': 'bg-blue-200 text-blue-800',
      'PENDING_REVIEW': 'bg-yellow-200 text-yellow-800',
      'APPROVED': 'bg-green-200 text-green-800',
      'ERROR': 'bg-red-200 text-red-800'
    };
    return colors[status] || 'bg-gray-200 text-gray-800';
  };

  /**
   * Get confidence color
   */
  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-orange-600';
  };

  // Ingestion API helpers
  const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : {};

  // Open Data Model for a given ingestion job status
  const openDataModelForIngestion = async (ingJob) => {
    try {
      // Use the INGESTION job_id, not the mapping_job_id
      // The ingestion job ID is what has the actual data in MongoDB
      const ingestionJobId = ingJob?.job_id || ingJob?.jobId;
      
      console.log('Opening Data Model for ingestion job:', ingestionJobId);
      
      // Create a synthetic job object for the ingestion job
      // We don't need the mapping job - OMOP works directly with ingestion data
      const syntheticJob = {
        jobId: ingestionJobId,
        jobName: ingJob?.job_name || 'Ingestion Job',
        status: 'APPROVED', // Treat as approved for OMOP processing
        sourceSchema: {},
        targetSchema: {},
        // Include mapping_job_id for reference if needed
        mapping_job_id: ingJob?.mapping_job_id
      };
      
      setCurrentJob(syntheticJob);
      setDataModelTab('OMOP');
      setShowDataModel(true);
    } catch (e) {
      console.error('Open Data Model error:', e);
      alert('Unable to open Data Model. Check console for details.');
    }
  };

  const createIngestionJob = async (jobIdFromList = null) => {
    try {
      setIsIngestLoading(true);
      setError(null);

      let srcCfg;
      let dstCfg;

      if (jobIdFromList) {
        // Create ingestion based on a selected approved mapping job from the list view
        const job = jobs.find(j => j.jobId === jobIdFromList);
        if (!job) {
          setError('Selected mapping job not found');
          return;
        }
        // Use sensible defaults for demo ingestion
        srcCfg = {
          connector_type: 'csv_file',
          name: 'Patient CSV (Demo)',
          config: { file_path: '/Users/aritrasanyal/EHR_Test/test_ehr_data.csv', delimiter: ',' },
          enabled: true
        };
        dstCfg = {
          connector_type: 'mongodb',
          name: 'MongoDB (ehr.staging)',
          config: { uri: 'mongodb://localhost:27017', database: 'ehr', collection: 'staging' },
          enabled: true
        };
      } else {
        // Create ingestion from connector view configuration
        if (!sourceConnector || !targetConnector || !sourceSchema || !targetSchema) {
          setError('Configure source and target before creating ingestion job');
          return;
        }
        srcCfg = {
          connector_type: sourceConnector.id,
          name: `${sourceConnector.name} Source`,
          config: {}
        };
        dstCfg = {
          connector_type: targetConnector.id === 'mongodb' ? 'mongodb' : targetConnector.id,
          name: `${targetConnector.name} Target`,
          config: {}
        };
        if (sourceConnector.id === 'csv_file') {
          srcCfg.config = { file_path: '/Users/aritrasanyal/EHR_Test/test_ehr_data.csv', delimiter: ',' };
        }
        if (dstCfg.connector_type === 'mongodb') {
          dstCfg.config = { uri: 'mongodb://localhost:27017', database: 'ehr', collection: 'staging' };
        }
      }

      const resp = await axios.post(`${API_BASE_URL}/api/v1/ingestion/jobs`, {
        job_name: 'UI_Ingestion_Pipeline',
        source_connector_config: srcCfg,
        destination_connector_config: dstCfg,
        mapping_job_id: jobIdFromList || (currentJob?.jobId || null),
        resource_type: fhirResourceType || null,
        transformation_rules: [],
        schedule_config: {},
        error_handling: {}
      }, { headers: { ...authHeaders, 'Content-Type': 'application/json' } });

      setIngestJobId(resp.data.job_id);
      setIngestStatus('CREATED');
      setIngestMetrics(null);
    } catch (err) {
      console.error('Create ingestion job error:', err);
      setError(`Create ingestion job failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsIngestLoading(false);
    }
  };

  const fetchIngestionJobs = useCallback(async () => {
    try {
      console.log('🔄 Fetching ingestion jobs...');
      
      // Cancel any existing request
      if (cancelTokenSource) {
        cancelTokenSource.cancel('New request started');
      }
      
      // Create new cancel token
      const source = axios.CancelToken.source();
      setCancelTokenSource(source);
      
      setIsIngestionListLoading(true);
      setLoadingStartTime(Date.now());
      setShowLoadingCancel(false);
      
      // Show cancel button after 2 seconds
      const cancelButtonTimeout = setTimeout(() => {
        setShowLoadingCancel(true);
      }, 2000);
      
      // Safety timeout - reset loading state after 15 seconds
      const safetyTimeout = setTimeout(() => {
        console.warn('⚠️ Safety timeout triggered - resetting loading state');
        source.cancel('Safety timeout');
        setIsIngestionListLoading(false);
        setLoadingStartTime(null);
        setShowLoadingCancel(false);
        setCancelTokenSource(null);
        showToast('Loading is taking longer than expected. Please try refreshing.', 'warning');
      }, 15000);
      
      const resp = await axios.get(`${API_BASE_URL}/api/v1/ingestion/jobs`, { 
        headers: authHeaders,
        timeout: 10000, // 10 second timeout
        cancelToken: source.token
      });
      
      // Clear timeouts since request completed
      clearTimeout(safetyTimeout);
      clearTimeout(cancelButtonTimeout);
      
      const jobs = resp.data.jobs || resp.data?.jobs || resp.data?.results || resp.data || [];
      console.log('✅ Successfully fetched ingestion jobs:', jobs.length);
      setIngestionJobs(jobs);
    } catch (e) {
      if (axios.isCancel(e)) {
        console.log('🚫 Request cancelled:', e.message);
        return; // Don't show error for cancelled requests
      }
      
      console.error('❌ Error fetching ingestion jobs:', e);
      console.error('Error details:', {
        message: e.message,
        status: e.response?.status,
        statusText: e.response?.statusText,
        data: e.response?.data
      });
      
      // Show error to user
      showToast(`Failed to load ingestion jobs: ${e.response?.data?.detail || e.message}`, 'error');
      
      // Set empty array to show "no jobs" instead of hanging
      setIngestionJobs([]);
    } finally {
      setIsIngestionListLoading(false);
      setLoadingStartTime(null);
      setShowLoadingCancel(false);
      setCancelTokenSource(null);
    }
  }, [token, showToast, API_BASE_URL, cancelTokenSource]);

  // Function to manually cancel loading
  const cancelLoading = useCallback(() => {
    console.log('🛑 User cancelled loading');
    
    // Cancel the actual request
    if (cancelTokenSource) {
      cancelTokenSource.cancel('User cancelled');
    }
    
    setIsIngestionListLoading(false);
    setLoadingStartTime(null);
    setShowLoadingCancel(false);
    setCancelTokenSource(null);
    showToast('Loading cancelled', 'info');
  }, [cancelTokenSource]);

  useEffect(() => {
    if (currentView === 'ingestion' && token) {
      fetchIngestionJobs();
      // Removed auto-refresh to prevent constant loading state
    }
    
    // Cleanup function to handle component unmount
    return () => {
      // Cancel any pending requests when component unmounts or view changes
      if (cancelTokenSource) {
        cancelTokenSource.cancel('Component unmounting or view changing');
        setCancelTokenSource(null);
      }
    };
  }, [currentView, token, fetchIngestionJobs, cancelTokenSource]);

  const startIngestionJob = async (jobIdParam = null) => {
    const targetId = jobIdParam || ingestJobId;
    if (!targetId) return;
    setIsIngestLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API_BASE_URL}/api/v1/ingestion/jobs/${targetId}/control`,
        { action: 'start' }, { headers: { ...authHeaders, 'Content-Type': 'application/json' } });
      if (!jobIdParam) {
        setIngestStatus(resp.data.status?.status || 'RUNNING');
        setIngestMetrics(resp.data.status?.metrics || null);
      } else {
        await fetchIngestionJobs();
      }
    } catch (err) {
      console.error('Start ingestion job error:', err);
      setError(`Start ingestion failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsIngestLoading(false);
    }
  };

  const stopIngestionJob = async (jobIdParam = null) => {
    const targetId = jobIdParam || ingestJobId;
    if (!targetId) return;
    setIsIngestLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API_BASE_URL}/api/v1/ingestion/jobs/${targetId}/control`,
        { action: 'stop' }, { headers: { ...authHeaders, 'Content-Type': 'application/json' } });
      if (!jobIdParam) {
        setIngestStatus(resp.data.status?.status || 'STOPPED');
        setIngestMetrics(resp.data.status?.metrics || null);
      } else {
        await fetchIngestionJobs();
      }
    } catch (err) {
      console.error('Stop ingestion job error:', err);
      setError(`Stop ingestion failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsIngestLoading(false);
    }
  };

  // Poll ingestion status every 2s when running
  useEffect(() => {
    if (!ingestJobId || ingestStatus !== 'RUNNING') return;
    const iv = setInterval(async () => {
      try {
        const resp = await axios.get(`${API_BASE_URL}/api/v1/ingestion/jobs/${ingestJobId}`, { headers: authHeaders });
        setIngestStatus(resp.data.job_status?.status || ingestStatus);
        setIngestMetrics(resp.data.job_status?.metrics || ingestMetrics);
      } catch (e) {
        // ignore transient errors
      }
    }, 2000);
    return () => clearInterval(iv);
  }, [ingestJobId, ingestStatus, token]);

  const openRecordsModal = async (jobId) => {
    setRecordsModalJobId(jobId);
    setShowRecordsModal(true);
    setRecordsLoading(true);
    try {
      const resp = await axios.get(`${API_BASE_URL}/api/v1/ingestion/jobs/${jobId}/records?limit=50`, { headers: authHeaders });
      setRecordsModalData(resp.data.records || []);
    } catch (e) {
      setRecordsModalData([]);
    } finally {
      setRecordsLoading(false);
    }
  };

  const openFailedModal = async (jobId) => {
    setFailedModalJobId(jobId);
    setShowFailedModal(true);
    setFailedLoading(true);
    try {
      const resp = await axios.get(`${API_BASE_URL}/api/v1/ingestion/jobs/${jobId}/failed?limit=50`, { headers: authHeaders });
      setFailedModalData(resp.data.records || []);
    } catch (e) {
      setFailedModalData([]);
    } finally {
      setFailedLoading(false);
    }
  };

  /**
   * Searchable Dropdown Component
   * Hybrid dropdown that allows selecting from options or typing custom values
   */
  const SearchableDropdown = ({ 
    value, 
    onChange, 
    options, 
    placeholder,
    allowCustom = true 
  }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState(value || '');
    const [isFocused, setIsFocused] = useState(false);
    const dropdownRef = useRef(null);
    const inputRef = useRef(null);
    
    // Only sync with parent value when not focused/typing
    useEffect(() => {
      if (!isFocused) {
        setSearchTerm(value || '');
      }
    }, [value, isFocused]);
    
    useEffect(() => {
      const handleClickOutside = (event) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
          setIsOpen(false);
          setIsFocused(false);
        }
      };
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);
    
    const filteredOptions = options.filter(opt => 
      opt.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    const handleSelect = (option) => {
      setSearchTerm(option);
      onChange(option);
      setIsOpen(false);
      setIsFocused(false);
    };
    
    const handleInputChange = (e) => {
      const newValue = e.target.value;
      setSearchTerm(newValue);
      setIsOpen(true);
    };
    
    const handleBlur = () => {
      // Delay to allow click on dropdown items
      setTimeout(() => {
        setIsFocused(false);
        // Update parent with final value on blur
        if (allowCustom && searchTerm !== value) {
          onChange(searchTerm);
        }
      }, 200);
    };
    
    const handleFocus = () => {
      setIsFocused(true);
      setIsOpen(true);
    };
    
    return (
      <div ref={dropdownRef} className="relative">
        <input
          ref={inputRef}
          type="text"
          className="w-full px-3 py-2 border border-amber-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
          placeholder={placeholder}
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
        />
        
        {isOpen && filteredOptions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-amber-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {filteredOptions.map((option, idx) => (
              <div
                key={idx}
                className="px-3 py-2 hover:bg-amber-50 cursor-pointer text-sm font-mono"
                onMouseDown={(e) => {
                  e.preventDefault(); // Prevent blur
                  handleSelect(option);
                }}
              >
                {option}
              </div>
            ))}
          </div>
        )}
        
        {isOpen && filteredOptions.length === 0 && searchTerm && allowCustom && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-amber-300 rounded-lg shadow-lg p-3">
            <p className="text-xs text-gray-600">
              No matches found. Press Enter to use custom value: <span className="font-mono font-semibold">{searchTerm}</span>
            </p>
          </div>
        )}
      </div>
    );
  };

  /**
   * FHIR Viewer Component
   * Displays FHIR resources from the fhir_<ResourceType> collections
   */
  const FHIRViewer = ({ token }) => {
    const [resourceTypes, setResourceTypes] = React.useState([]);
    const [selectedResourceType, setSelectedResourceType] = React.useState('');
    const [resources, setResources] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [jobIdFilter, setJobIdFilter] = React.useState('');
    const [searchQuery, setSearchQuery] = React.useState('');
    const [selectedResource, setSelectedResource] = React.useState(null);
    const [showDetailModal, setShowDetailModal] = React.useState(false);

    // Fetch available resource types
    React.useEffect(() => {
      const fetchResourceTypes = async () => {
        try {
          const resp = await axios.get(`${API_BASE_URL}/api/v1/fhir/store/resources`);
          setResourceTypes(resp.data.resources || []);
          if (resp.data.resources && resp.data.resources.length > 0) {
            setSelectedResourceType(resp.data.resources[0]);
          }
        } catch (e) {
          console.error('Failed to fetch resource types:', e);
        }
      };
      fetchResourceTypes();
    }, []);

    // Fetch resources when type/filters change (but not when modal is open)
    React.useEffect(() => {
      if (!selectedResourceType || showDetailModal) return;
      
      const fetchResources = async () => {
        setLoading(true);
        try {
          let url = `${API_BASE_URL}/api/v1/fhir/store/${selectedResourceType}?limit=100`;
          if (jobIdFilter) url += `&job_id=${jobIdFilter}`;
          if (searchQuery) url += `&q=${searchQuery}`;
          
          const resp = await axios.get(url);
          setResources(resp.data.entries || []);
        } catch (e) {
          console.error('Failed to fetch resources:', e);
          setResources([]);
        } finally {
          setLoading(false);
        }
      };
      
      fetchResources();
    }, [selectedResourceType, jobIdFilter, searchQuery, showDetailModal]);

    const openDetailModal = (resource) => {
      setSelectedResource(resource);
      setShowDetailModal(true);
    };

    return (
      <div>
        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Resource Type</label>
              <select
                value={selectedResourceType}
                onChange={(e) => setSelectedResourceType(e.target.value)}
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
              >
                {resourceTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Job ID Filter (optional)</label>
              <input
                type="text"
                value={jobIdFilter}
                onChange={(e) => setJobIdFilter(e.target.value)}
                placeholder="Filter by job ID..."
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
              />
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Search</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by ID, name..."
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
              />
            </div>
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading resources...</p>
          </div>
        ) : resources.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-600">
            No {selectedResourceType} resources found. Try adjusting your filters.
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b-2 border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Name/Code</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Job ID</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Last Updated</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {resources.map((resource, idx) => {
                    const displayName = selectedResourceType === 'Patient' 
                      ? `${resource.name?.[0]?.given?.[0] || ''} ${resource.name?.[0]?.family || ''}`.trim() || 'N/A'
                      : resource.code?.coding?.[0]?.display || resource.code?.text || 'N/A';
                    
                    return (
                      <tr key={idx} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm font-mono text-gray-900">
                          {resource.id?.substring(0, 12) || 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-700">{displayName}</td>
                        <td className="px-6 py-4 text-sm font-mono text-gray-600">
                          {resource.job_id?.substring(0, 8) || 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {resource.meta?.lastUpdated 
                            ? new Date(resource.meta.lastUpdated).toLocaleString()
                            : 'N/A'}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => openDetailModal(resource)}
                            className="text-amber-600 hover:text-amber-800 font-semibold text-sm"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            {/* Results count */}
            <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                Showing {resources.length} {selectedResourceType} resource{resources.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        )}

        {/* Detail Modal */}
        {showDetailModal && selectedResource && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-4xl w-full mx-4 max-h-[85vh] overflow-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-gray-800">
                  {selectedResourceType} Details
                </h3>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4 font-mono text-xs overflow-auto">
                <pre>{JSON.stringify(selectedResource, null, 2)}</pre>
              </div>
              
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(selectedResource, null, 2));
                    alert('Resource JSON copied to clipboard');
                  }}
                  className="bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2 px-4 rounded-lg mr-2"
                >
                  Copy JSON
                </button>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold py-2 px-4 rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };


  // Show loading state while initializing
  if (!isAuthReady) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-amber-600 mx-auto mb-4"></div>
          <p className="text-amber-700 text-lg">Initializing Healthcare Data Platform...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100">
      {/* Toast Notifications */}
      <ToastContainer />

      {/* Bulk Actions Bar */}
      <BulkActionsBar />

      {/* Header */}
      <header className="bg-white shadow-md border-b-2 border-amber-200 fixed top-0 left-0 right-0 z-50">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Toggle Sidebar"
              >
                <span className="text-2xl">{sidebarCollapsed ? '☰' : '✕'}</span>
              </button>
              <div>
                <h1 className="text-3xl font-bold text-amber-800">
                  🏥 AI Data Interoperability Platform
                </h1>
                <p className="text-sm text-amber-600 mt-1">
                  Healthcare EHR/HL7 Mapping • Powered by Sentence-BERT
                </p>
              </div>
            </div>
            {userId && (
              <div className="text-right">
                <p className="text-xs text-amber-500">Clinical Data Engineer</p>
                <p className="text-sm font-mono text-amber-700 truncate max-w-xs">
                  {username || userId.substring(0, 16)}
                </p>
                <Caption className="mt-1">Cmd+K: Search • Cmd+N: New • Cmd+H: Home</Caption>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Error Banner */}
      {error && (
        <div className={`mx-auto px-4 sm:px-6 lg:px-8 mt-20 ${sidebarCollapsed ? 'ml-20' : 'ml-64'} transition-all duration-300`}>
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
            <button
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={() => setError(null)}
            >
              <span className="text-2xl">&times;</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Content with Sidebar Offset */}
      <main className={`mx-auto px-4 sm:px-6 lg:px-8 py-8 mt-20 ${sidebarCollapsed ? 'ml-20' : 'ml-64'} transition-all duration-300`}>
        {/* Breadcrumb Navigation */}
        <Breadcrumbs />
        {/* Job List View */}
        {currentView === 'list' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-amber-800">EHR/HL7 Mapping Jobs</h2>
              <div className="flex space-x-3">
                <button
                  onClick={() => { setCurrentView('hl7viewer'); setCurrentJob(null); }}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition duration-200"
                >
                  📋 HL7 Viewer
                </button>
                <button
                  onClick={() => setCurrentView('fhirviewer')}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition duration-200"
                >
                  🏷️ FHIR Viewer
                </button>
                <button
                  onClick={() => setCurrentView('ingestion')}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition duration-200"
                >
                  📡 Ingestion Jobs
                </button>
                <button
                  onClick={() => setCurrentView('omopviewer')}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition duration-200"
                >
                  🧬 OMOP Viewer
                </button>
                <button
                  onClick={startNewJob}
                  className="bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2 px-6 rounded-lg shadow-md transition duration-200"
                >
                  + Create New Mapping Job
                </button>
              </div>
            </div>

            {/* Ingestion Modal */}
            {showIngestionModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-gray-800">Create Ingestion Pipeline</h3>
                    <button onClick={() => setShowIngestionModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
                  </div>

                  {/* OMOP Compatible Filter */}
                  <div className="mb-4 p-3 border rounded-lg bg-gray-50">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={showOMOPCompatibleOnly}
                        onChange={(e) => {
                          setShowOMOPCompatibleOnly(e.target.checked);
                          // Reset selection when toggling filter
                          setSelectedIngestJobId('');
                        }}
                        className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                      />
                      <span className="text-sm font-medium text-gray-700">
                        Show OMOP-Compatible Jobs Only
                      </span>
                    </label>
                    {showOMOPCompatibleOnly && (
                      <div className="mt-2 text-xs text-gray-600">
                        ✅ Filter jobs with CSV data or supported FHIR resources for OMOP data model creation
                      </div>
                    )}
                  </div>

                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Select {showOMOPCompatibleOnly ? 'OMOP-Compatible ' : 'Approved '}Mapping Job
                  </label>
                  
                  {showOMOPCompatibleOnly && omopCompatibleJobs.length === 0 ? (
                    <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
                      ⚠️ No OMOP-compatible jobs found. Uncheck the filter to see all approved jobs.
                    </div>
                  ) : (
                    <select
                      className="w-full border-2 border-gray-300 rounded-lg p-3 mb-4 focus:border-amber-500 focus:ring-2 focus:ring-amber-200"
                      value={selectedIngestJobId || ''}
                      onChange={(e) => setSelectedIngestJobId(e.target.value)}
                    >
                      <option value="">-- Select Job --</option>
                      {showOMOPCompatibleOnly ? (
                        // Show OMOP-compatible jobs with detailed info
                        omopCompatibleJobs.map(compatJob => (
                          <option key={compatJob.job_id} value={compatJob.job_id}>
                            {compatJob.job_id.substring(0, 16)}... — {compatJob.source_type} ({compatJob.record_count} records) — {compatJob.resource_types.join(', ')}
                          </option>
                        ))
                      ) : (
                        // Show all approved jobs
                        jobs.filter(j => j.status === 'APPROVED').map(j => (
                          <option key={j.jobId} value={j.jobId}>
                            {j.jobId.substring(0,12)} — {Object.keys(j.sourceSchema).length}→{Object.keys(j.targetSchema).length} fields
                          </option>
                        ))
                      )}
                    </select>
                  )}

                  {/* Show selected job info if OMOP-compatible */}
                  {showOMOPCompatibleOnly && selectedIngestJobId && omopCompatibleJobs.find(cj => cj.job_id === selectedIngestJobId) && (
                    <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="text-sm">
                        <p className="font-semibold text-blue-900 mb-1">Selected Job Details:</p>
                        <p className="text-blue-700">
                          Type: <span className="font-mono">{omopCompatibleJobs.find(cj => cj.job_id === selectedIngestJobId)?.source_type}</span>
                        </p>
                        <p className="text-blue-700">
                          Records: {omopCompatibleJobs.find(cj => cj.job_id === selectedIngestJobId)?.record_count}
                        </p>
                        <p className="text-blue-700">
                          Resources: {omopCompatibleJobs.find(cj => cj.job_id === selectedIngestJobId)?.resource_types.join(', ')}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end space-x-2">
                    <button onClick={() => setShowIngestionModal(false)} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg">Cancel</button>
                    <button
                      disabled={!selectedIngestJobId || isIngestLoading}
                      onClick={async () => {
                        await createIngestionJob(selectedIngestJobId);
                        await startIngestionJob();
                        setShowIngestionModal(false);
                      }}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg disabled:opacity-50"
                    >
                      {isIngestLoading ? 'Creating...' : 'Create & Start'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {jobs.length === 0 ? (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="text-6xl mb-4">🏥</div>
                <h3 className="text-xl font-semibold text-amber-700 mb-2">No mapping jobs yet</h3>
                <p className="text-amber-600 mb-6">Create your first EHR/HL7 mapping job to accelerate data integration</p>
                <button
                  onClick={startNewJob}
                  className="bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2 px-6 rounded-lg"
                >
                  Create Job
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {jobs.map((job) => (
                  <div
                    key={job.jobId}
                    className="bg-white rounded-lg shadow-md hover:shadow-lg transition duration-200 p-6 cursor-pointer"
                    onClick={() => viewJobDetails(job)}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-lg font-semibold text-amber-800">
                          Job {job.jobId.substring(0, 12)}
                        </h3>
                        <p className="text-sm text-amber-600">
                          {Object.keys(job.sourceSchema).length} source fields →{' '}
                          {Object.keys(job.targetSchema).length} target fields
                        </p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </div>
                    
                    {job.suggestedMappings && job.suggestedMappings.length > 0 && (
                      <p className="text-sm text-amber-600 mb-2">
                        🧠 {job.suggestedMappings.length} AI suggestions (Sentence-BERT)
                      </p>
                    )}
                    
                    {job.finalMappings && job.finalMappings.length > 0 && (
                      <p className="text-sm text-green-600 font-semibold">
                        ✓ {job.finalMappings.length} approved mappings
                      </p>
                    )}
                    
                    {job.createdAt && (
                      <p className="text-xs text-amber-500 mt-2">
                        Created: {new Date(job.createdAt).toLocaleString()}
                      </p>
                    )}

                    {/* Edit buttons for approved/draft jobs */}
                    {(job.status === 'APPROVED' || job.status === 'DRAFT') && (
                      <div className="mt-4 flex space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            editJob(job);
                          }}
                          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded"
                        >
                          ✏️ Edit
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Connector Configuration View (Azure Data Factory Inspired) */}
        {currentView === 'connector' && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">
                📊 Data Connector & Pipeline Builder
                {isEditMode && <span className="ml-2 text-sm text-blue-600">(Edit Mode)</span>}
              </h2>
            </div>

            {/* Connector Palette */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-lg font-semibold text-amber-800 mb-4">Available Connectors</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {connectorTypes.map((connector) => (
                  <div
                    key={connector.id}
                    className={`bg-${connector.color}-50 border-2 border-${connector.color}-300 hover:border-${connector.color}-500 rounded-lg p-4 text-center cursor-pointer transition hover:shadow-lg`}
                    title={connector.description}
                  >
                    <div className="text-4xl mb-2">{connector.icon}</div>
                    <p className={`text-sm font-semibold text-${connector.color}-800`}>{connector.name}</p>
                    <p className="text-xs text-gray-500 mt-1">{connector.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Pipeline Canvas */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg shadow-md p-8 mb-6 min-h-96 border-2 border-dashed border-gray-300">
              <h3 className="text-lg font-semibold text-gray-700 mb-6 text-center">
                Data Integration Pipeline
              </h3>

              <div className="flex items-center justify-center space-x-8">
                {/* Source Connector */}
                <div className="flex flex-col items-center">
                  <p className="text-sm font-semibold text-gray-600 mb-3">Source</p>
                  {!sourceConnector ? (
                    <div className="w-48 h-48 border-4 border-dashed border-gray-400 rounded-lg flex flex-col items-center justify-center bg-white hover:bg-gray-50 transition cursor-pointer">
                      <div className="text-6xl mb-2 text-gray-300">+</div>
                      <p className="text-sm text-gray-500">Select Source</p>
                      <div className="mt-4 space-y-2">
                        {connectorTypes.slice(0, 3).map((c) => (
                          <button
                            key={c.id}
                            onClick={() => selectSourceConnector(c)}
                            className={`block w-full px-4 py-2 text-sm bg-${c.color}-100 hover:bg-${c.color}-200 rounded transition`}
                          >
                            {c.icon} {c.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div
                      className={`w-48 h-48 border-4 border-${sourceConnector.color}-500 rounded-lg bg-${sourceConnector.color}-50 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition`}
                      onClick={() => setShowSourceModal(true)}
                    >
                      <div className="text-6xl mb-2">{sourceConnector.icon}</div>
                      <p className={`text-sm font-semibold text-${sourceConnector.color}-800`}>
                        {sourceConnector.name}
                      </p>
                      <p className="text-xs text-gray-600 mt-2">
                        {sourceSchema ? '✓ Configured' : 'Click to configure'}
                      </p>
                    </div>
                  )}
                </div>

                {/* Connection Arrow */}
                <div className="flex flex-col items-center">
                  <div className="text-4xl text-amber-600">→</div>
                  <p className="text-xs text-gray-500 mt-2">AI Mapping</p>
                </div>

                {/* Target Connector */}
                <div className="flex flex-col items-center">
                  <p className="text-sm font-semibold text-gray-600 mb-3">Target</p>
                  {!targetConnector ? (
                    <div className="w-48 h-48 border-4 border-dashed border-gray-400 rounded-lg flex flex-col items-center justify-center bg-white hover:bg-gray-50 transition cursor-pointer">
                      <div className="text-6xl mb-2 text-gray-300">+</div>
                      <p className="text-sm text-gray-500">Select Target</p>
                      <div className="mt-4 space-y-2">
                        {connectorTypes.slice(2, 5).map((c) => (
                          <button
                            key={c.id}
                            onClick={() => selectTargetConnector(c)}
                            className={`block w-full px-4 py-2 text-sm bg-${c.color}-100 hover:bg-${c.color}-200 rounded transition`}
                          >
                            {c.icon} {c.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div
                      className={`w-48 h-48 border-4 border-${targetConnector.color}-500 rounded-lg bg-${targetConnector.color}-50 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition`}
                      onClick={() => setShowTargetModal(true)}
                    >
                      <div className="text-6xl mb-2">{targetConnector.icon}</div>
                      <p className={`text-sm font-semibold text-${targetConnector.color}-800`}>
                        {targetConnector.name}
                      </p>
                      <p className="text-xs text-gray-600 mt-2">
                        {targetSchema ? '✓ Configured' : 'Click to configure'}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-center mt-8 space-x-4">
                {sourceConnector && targetConnector && sourceSchema && targetSchema && (
                  <>
                    {isEditMode && editingJobId ? (
                      <button
                        onClick={updateJobSchemas}
                        disabled={loading}
                        className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
                      >
                        {loading ? 'Updating...' : '💾 Save Changes'}
                      </button>
                    ) : !currentJob ? (
                      <button
                        onClick={createJob}
                        disabled={loading}
                        className="bg-amber-600 hover:bg-amber-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
                      >
                        {loading ? 'Creating Pipeline...' : '🔗 Create Pipeline'}
                      </button>
                    ) : null}

                    {currentJob && !isEditMode && (
                      <button
                        onClick={analyzeSchemas}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50 flex items-center"
                      >
                        {loading ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                            Analyzing...
                          </>
                        ) : (
                          <>🧠 Generate Mappings (AI) →</>
                        )}
                      </button>
                    )}

                    {isEditMode && (
                      <button
                        onClick={() => {
                          setIsEditMode(false);
                          setEditingJobId(null);
                          setCurrentView('list');
                          // Reset form state
                          setSourceSchema('');
                          setTargetSchema('');
                          setSourceConnector(null);
                          setTargetConnector(null);
                          setCurrentJob(null);
                        }}
                        className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200"
                      >
                        Cancel Edit
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Schema Display */}
            {(sourceSchema || targetSchema) && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-amber-800 mb-4">Detected Schemas</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  {sourceSchema && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">
                        {sourceConnector?.icon} {sourceConnector?.name} Schema
                      </h4>
                      <div className="bg-gray-50 rounded p-3 max-h-64 overflow-auto">
                        <pre className="text-xs font-mono">{JSON.stringify(JSON.parse(sourceSchema), null, 2)}</pre>
                      </div>
                    </div>
                  )}
                  {targetSchema && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">
                        {targetConnector?.icon} {targetConnector?.name} Schema
                      </h4>
                      <div className="bg-gray-50 rounded p-3 max-h-64 overflow-auto">
                        <pre className="text-xs font-mono">{JSON.stringify(JSON.parse(targetSchema), null, 2)}</pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Ingestion Job Panel */}
            {sourceConnector && targetConnector && (
              <div className="bg-white rounded-lg shadow-md p-6 mt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-amber-800">⚡ Real-time Ingestion Job</h3>
                  <span className="text-xs text-gray-500">Create → Start → Monitor</span>
                </div>

                {!ingestJobId ? (
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">Create a streaming pipeline from your configured source to target.</p>
                    <button
                      onClick={createIngestionJob}
                      disabled={isIngestLoading || !sourceSchema || !targetSchema}
                      className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg disabled:opacity-50"
                    >
                      {isIngestLoading ? 'Creating...' : '➕ Create Ingestion Job'}
                    </button>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-sm text-gray-700">Job ID: <span className="font-mono">{ingestJobId}</span></p>
                        <p className="text-sm text-gray-700">Status: <span className={`font-semibold ${ingestStatus === 'RUNNING' ? 'text-green-600' : ingestStatus === 'STOPPED' ? 'text-gray-600' : 'text-amber-600'}`}>{ingestStatus || 'N/A'}</span></p>
                      </div>
                      <div className="space-x-2">
                        {ingestStatus !== 'RUNNING' && (
                          <button
                            onClick={() => startIngestionJob()}
                            disabled={isIngestLoading}
                            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50"
                          >
                            {isIngestLoading ? 'Starting...' : '▶ Start'}
                          </button>
                        )}
                        {ingestStatus === 'RUNNING' && (
                          <button
                            onClick={() => stopIngestionJob()}
                            disabled={isIngestLoading}
                            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg disabled:opacity-50"
                          >
                            {isIngestLoading ? 'Stopping...' : '⏸ Stop'}
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div className="bg-gray-50 rounded p-4">
                        <p className="text-xs text-gray-500">Received</p>
                        <p className="text-xl font-semibold">{ingestMetrics?.received ?? 0}</p>
                      </div>
                      <div className="bg-gray-50 rounded p-4">
                        <p className="text-xs text-gray-500">Processed</p>
                        <p className="text-xl font-semibold text-green-700">{ingestMetrics?.processed ?? 0}</p>
                      </div>
                      <div className="bg-gray-50 rounded p-4">
                        <p className="text-xs text-gray-500">Failed</p>
                        <p className="text-xl font-semibold text-red-700">{ingestMetrics?.failed ?? 0}</p>
                      </div>
                    </div>

                    {ingestMetrics?.last_update && (
                      <p className="text-xs text-gray-500 mt-3">Last update: {new Date(ingestMetrics.last_update).toLocaleTimeString()}</p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Source Connector Modal */}
            {showSourceModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-gray-800">
                      Configure {sourceConnector?.icon} {sourceConnector?.name}
                    </h3>
                    <button
                      onClick={() => setShowSourceModal(false)}
                      className="text-gray-500 hover:text-gray-700 text-2xl"
                    >
                      ×
                    </button>
                  </div>

                  {/* CSV File Upload Option */}
                  {sourceConnector?.id === 'csv_file' && (
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Upload CSV File for Schema Inference
                      </label>
                      <div className="flex items-center space-x-4">
                        <label className="flex-1 bg-blue-50 border-2 border-blue-300 border-dashed rounded-lg p-4 text-center cursor-pointer hover:bg-blue-100 transition">
                          <input
                            type="file"
                            accept=".csv"
                            onChange={(e) => handleCSVUpload(e, true)}
                            className="hidden"
                          />
                          <div className="text-3xl mb-2">📁</div>
                          <p className="text-sm font-semibold text-blue-700">Select Local CSV File</p>
                          <p className="text-xs text-blue-600 mt-1">Schema will be auto-detected</p>
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Upload a CSV file and the schema will be automatically inferred from column names and data types
                      </p>
                    </div>
                  )}

                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {sourceConnector?.id === 'csv_file' ? 'Inferred Schema (or paste manually)' : 'Source Schema (JSON)'}
                    </label>
                    <textarea
                      className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      placeholder='{"patient_first_name": "string", "patient_last_name": "string", "date_of_birth": "date"}'
                      value={sourceSchema}
                      onChange={(e) => setSourceSchema(e.target.value)}
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      {sourceConnector?.id === 'hl7_api' ? 'Example: {"PID-5.1": "string", "PID-5.2": "string", "PID-7": "date"}' : 
                       sourceConnector?.id === 'csv_file' ? 'Auto-populated from CSV or paste manually: {"first_name": "string", "last_name": "string", "dob": "date"}' :
                       'Paste your schema in JSON format'}
                    </p>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => {setShowSourceModal(false); setSourceConnector(null);}}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => saveConnectorConfig(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Save Configuration
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Target Connector Modal */}
            {showTargetModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-gray-800">
                      Configure {targetConnector?.icon} {targetConnector?.name}
                    </h3>
                    <button
                      onClick={() => setShowTargetModal(false)}
                      className="text-gray-500 hover:text-gray-700 text-2xl"
                    >
                      ×
                    </button>
                  </div>

                  {/* FHIR Resource Selection for MongoDB/FHIR Targets */}
                  {(targetConnector?.id === 'mongodb' || targetConnector?.id === 'fhir_api') && (
                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-3">
                        <label className="block text-sm font-semibold text-gray-700">
                          FHIR Resource Type
                        </label>
                        <button
                          onClick={predictFHIRResource}
                          disabled={loading || !sourceSchema}
                          className="px-4 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg text-sm hover:from-purple-600 hover:to-pink-600 transition disabled:opacity-50 flex items-center"
                        >
                          {loading ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
                              Predicting...
                            </>
                          ) : (
                            <>🤖 AI Predict Resource (Gemini)</>
                          )}
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        {['Patient', 'Observation', 'Condition', 'Procedure', 'Encounter', 'MedicationRequest', 'DiagnosticReport'].map((resourceType) => (
                          <button
                            key={resourceType}
                            onClick={() => loadFHIRSchema(resourceType)}
                            className={`p-3 rounded-lg border-2 transition ${
                              fhirResourceType === resourceType
                                ? 'border-purple-500 bg-purple-50 font-semibold'
                                : 'border-gray-300 hover:border-purple-300'
                            }`}
                          >
                            <p className="text-sm font-semibold">{resourceType}</p>
                            <p className="text-xs text-gray-500">FHIR R4</p>
                          </button>
                        ))}
                      </div>
                      <p className="text-xs text-gray-500">
                        Click "🤖 AI Predict Resource" to let Gemini AI suggest the best FHIR resource, or select manually
                      </p>
                    </div>
                  )}

                  {/* CSV File Upload Option for Target */}
                  {targetConnector?.id === 'csv_file' && (
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Upload CSV File for Schema Inference
                      </label>
                      <div className="flex items-center space-x-4">
                        <label className="flex-1 bg-purple-50 border-2 border-purple-300 border-dashed rounded-lg p-4 text-center cursor-pointer hover:bg-purple-100 transition">
                          <input
                            type="file"
                            accept=".csv"
                            onChange={(e) => handleCSVUpload(e, false)}
                            className="hidden"
                          />
                          <div className="text-3xl mb-2">📁</div>
                          <p className="text-sm font-semibold text-purple-700">Select Local CSV File</p>
                          <p className="text-xs text-purple-600 mt-1">Schema will be auto-detected</p>
                        </label>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Upload a CSV template and the schema will be automatically inferred
                      </p>
                    </div>
                  )}

                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      {targetConnector?.id === 'csv_file' ? 'Inferred Schema (or paste manually)' :
                       (targetConnector?.id === 'mongodb' || targetConnector?.id === 'fhir_api') ? `FHIR ${fhirResourceType} Schema (auto-loaded)` :
                       'Target Schema (JSON)'}
                    </label>
                    <textarea
                      className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                      placeholder='{"patientFullName": "string", "birthDate": "datetime", "mrn": "string"}'
                      value={targetSchema}
                      onChange={(e) => setTargetSchema(e.target.value)}
                      readOnly={(targetConnector?.id === 'mongodb' || targetConnector?.id === 'fhir_api') && targetSchema.includes('name[0].family')}
                    />
                    <p className="text-xs text-gray-500 mt-2">
                      {targetConnector?.id === 'data_warehouse' ? 'Example: {"patient_name": "string", "birth_date": "datetime", "medical_record_number": "string"}' :
                       targetConnector?.id === 'fhir_api' ? 'FHIR resource schema auto-loaded. Select resource type above to change.' :
                       targetConnector?.id === 'mongodb' ? 'FHIR resource schema for MongoDB. Select resource type above to change.' :
                       targetConnector?.id === 'csv_file' ? 'Auto-populated from CSV or paste manually' :
                       'Paste your target schema in JSON format'}
                    </p>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => {setShowTargetModal(false); setTargetConnector(null);}}
                      className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => saveConnectorConfig(false)}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                      Save Configuration
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Legacy Configuration View (Keep for backward compatibility) */}
        {currentView === 'configure_legacy' && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">Configure EHR/HL7 Mapping</h2>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6">
                <p className="text-sm text-blue-800">
                  <strong>Healthcare Data Mapping:</strong> Enter your EHR schemas, HL7 message structures, or clinical data models. 
                  The AI will use biomedical semantic understanding to suggest optimal field mappings.
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-semibold text-amber-700 mb-2">
                    Source Schema (JSON) - e.g., Local EHR
                  </label>
                  <textarea
                    className="w-full h-64 px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono text-sm"
                    placeholder='{"patient_first_name": "string", "patient_last_name": "string", "date_of_birth": "date", "mrn": "string"}'
                    value={sourceSchema}
                    onChange={(e) => setSourceSchema(e.target.value)}
                  />
                  <p className="text-xs text-amber-500 mt-1">
                    Example: Local EHR fields, HL7 v2 segments (PID, OBX, etc.)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-amber-700 mb-2">
                    Target Schema (JSON) - e.g., National Registry
                  </label>
                  <textarea
                    className="w-full h-64 px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono text-sm"
                    placeholder='{"patientFullName": "string", "birthDate": "datetime", "medicalRecordNumber": "string"}'
                    value={targetSchema}
                    onChange={(e) => setTargetSchema(e.target.value)}
                  />
                  <p className="text-xs text-amber-500 mt-1">
                    Example: Cancer registry fields, FHIR resources, HL7 v3
                  </p>
                </div>
              </div>

              <div className="flex justify-between items-center">
                {!currentJob ? (
                  <button
                    onClick={createJob}
                    disabled={loading}
                    className="bg-amber-600 hover:bg-amber-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Creating...' : 'Create Mapping Job'}
                  </button>
                ) : (
                  <button
                    onClick={analyzeSchemas}
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                        Analyzing with Sentence-BERT...
                      </>
                    ) : (
                      <>
                        🧠 Analyze with AI (Sentence-BERT) →
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* HITL Review View */}
        {currentView === 'review' && currentJob && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">Review AI Suggestions (HITL)</h2>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-amber-800">
                    Job {currentJob.jobId.substring(0, 12)}
                  </h3>
                  <p className="text-sm text-amber-600">
                    Review and approve AI-suggested mappings from Sentence-BERT analysis
                  </p>
                </div>
                <button
                  onClick={addManualMapping}
                  className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg text-sm"
                >
                  + Add Manual Mapping
                </button>
              </div>

              <div className="space-y-4">
                {selectedMappings.map((mapping, index) => (
                  <div
                    key={index}
                    className={`border-2 rounded-lg p-4 ${
                      mapping.isApproved
                        ? 'border-green-400 bg-green-50'
                        : mapping.isRejected
                        ? 'border-red-400 bg-red-50'
                        : 'border-amber-200 bg-white'
                    }`}
                  >
                    <div className="grid md:grid-cols-2 gap-4 mb-3">
                      <div>
                        <label className="block text-xs font-semibold text-amber-600 mb-1">
                          Source Field
                        </label>
                        {mapping.isManual ? (
                          <SearchableDropdown
                            value={mapping.sourceField}
                            onChange={(value) => updateManualMapping(index, 'sourceField', value)}
                            options={sourceFieldOptions}
                            placeholder="Select or type source field"
                            allowCustom={true}
                          />
                        ) : (
                          <p className="font-mono text-sm text-amber-800 bg-amber-100 px-3 py-2 rounded">
                            {mapping.sourceField}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-amber-600 mb-1">
                          Target Field
                        </label>
                        {mapping.isManual ? (
                          <SearchableDropdown
                            value={mapping.targetField}
                            onChange={(value) => updateManualMapping(index, 'targetField', value)}
                            options={targetFieldOptions}
                            placeholder="Select or type target field (e.g., Patient.name[0].family)"
                            allowCustom={true}
                          />
                        ) : (
                          <p className="font-mono text-sm text-amber-800 bg-amber-100 px-3 py-2 rounded">
                            {mapping.targetField}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-4">
                        <div>
                          <span className="text-xs font-semibold text-amber-600">Transform: </span>
                          {!mapping.isManual ? (
                            <select
                              className="text-xs font-mono bg-amber-100 px-2 py-1 rounded border border-amber-300 focus:ring-2 focus:ring-amber-500"
                              value={mapping.suggestedTransform}
                              onChange={(e) => updateManualMapping(index, 'suggestedTransform', e.target.value)}
                            >
                              <option value="DIRECT">DIRECT</option>
                              <option value="CONCAT">CONCAT</option>
                              <option value="SPLIT">SPLIT</option>
                              <option value="UPPERCASE">UPPERCASE</option>
                              <option value="LOWERCASE">LOWERCASE</option>
                              <option value="DATE_FORMAT">DATE_FORMAT</option>
                              <option value="CUSTOM">CUSTOM</option>
                            </select>
                          ) : (
                            <span className="text-xs font-mono bg-amber-100 px-2 py-1 rounded">
                              {mapping.suggestedTransform}
                            </span>
                          )}
                        </div>
                        {!mapping.isManual && (
                          <div>
                            <span className="text-xs font-semibold text-amber-600">Confidence: </span>
                            <span className={`text-xs font-bold ${getConfidenceColor(mapping.confidenceScore)}`}>
                              {(mapping.confidenceScore * 100).toFixed(0)}%
                            </span>
                          </div>
                        )}
                        {mapping.isManual && (
                          <span className="text-xs font-semibold text-blue-600">✎ Manual Entry</span>
                        )}
                      </div>

                      <div className="flex space-x-2">
                        <button
                          onClick={() => toggleMappingApproval(index)}
                          className={`px-4 py-1 rounded text-sm font-semibold ${
                            mapping.isApproved
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-green-100'
                          }`}
                        >
                          ✓ Approve
                        </button>
                        <button
                          onClick={() => toggleMappingRejection(index)}
                          className={`px-4 py-1 rounded text-sm font-semibold ${
                            mapping.isRejected
                              ? 'bg-red-500 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-red-100'
                          }`}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={generateTerminology}
                  disabled={terminologyLoading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
                >
                  {terminologyLoading ? 'Analyzing…' : 'Normalize Terminology'}
                </button>
                <button
                  onClick={approveMappings}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
                >
                  {loading ? 'Finalizing...' : 'Finalize and Approve Mappings'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Terminology Normalization View */}
        {currentView === 'terminology' && currentJob && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('review')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">Terminology Normalization</h2>
            </div>

            {terminologyError && (
              <div className="mb-4 bg-red-50 text-red-700 border border-red-200 px-4 py-2 rounded">
                {terminologyError}
              </div>
            )}

            <div className="bg-white rounded-lg shadow-md p-6">
              {terminologySuggestions.length === 0 ? (
                <p className="text-sm text-gray-600">No terminology candidates detected. Go back and approve mappings first.</p>
              ) : (
                <div className="space-y-6">
                  {terminologySuggestions.map((sug, idx) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex justify-between items-center mb-3">
                        <div>
                          <p className="text-sm text-gray-700"><span className="font-semibold">Field:</span> <span className="font-mono">{sug.fieldPath}</span></p>
                          {sug.suggestedSystem && (
                            <p className="text-xs text-amber-600">Suggested system: {sug.suggestedSystem}</p>
                          )}
                        </div>
                        <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded">Hybrid</span>
                      </div>

                      <div className="overflow-x-auto">
                        <table className="min-w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-600 border-b">
                              <th className="py-2 pr-4">Source Value</th>
                              <th className="py-2 pr-4">Normalized</th>
                              <th className="py-2 pr-4">System</th>
                              <th className="py-2 pr-4">Code</th>
                              <th className="py-2 pr-4">Display</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(sug.candidates || []).map((c, i) => (
                              <tr key={i} className="border-b hover:bg-gray-50">
                                <td className="py-2 pr-4 font-mono">{c.sourceValue}</td>
                                <td className="py-2 pr-4">
                                  <input
                                    className="px-2 py-1 border rounded w-40"
                                    value={terminologyEdits?.[sug.fieldPath]?.[c.sourceValue]?.normalized || ''}
                                    onChange={(e) => {
                                      setTerminologyEdits(prev => ({
                                        ...prev,
                                        [sug.fieldPath]: {
                                          ...(prev[sug.fieldPath] || {}),
                                          [c.sourceValue]: {
                                            ...(prev[sug.fieldPath]?.[c.sourceValue] || {}),
                                            normalized: e.target.value
                                          }
                                        }
                                      }));
                                    }}
                                  />
                                </td>
                                <td className="py-2 pr-4">
                                  <input
                                    className="px-2 py-1 border rounded w-56"
                                    value={terminologyEdits?.[sug.fieldPath]?.[c.sourceValue]?.system || ''}
                                    onChange={(e) => {
                                      setTerminologyEdits(prev => ({
                                        ...prev,
                                        [sug.fieldPath]: {
                                          ...(prev[sug.fieldPath] || {}),
                                          [c.sourceValue]: {
                                            ...(prev[sug.fieldPath]?.[c.sourceValue] || {}),
                                            system: e.target.value
                                          }
                                        }
                                      }));
                                    }}
                                  />
                                </td>
                                <td className="py-2 pr-4">
                                  <input
                                    className="px-2 py-1 border rounded w-40"
                                    value={terminologyEdits?.[sug.fieldPath]?.[c.sourceValue]?.code || ''}
                                    onChange={(e) => {
                                      setTerminologyEdits(prev => ({
                                        ...prev,
                                        [sug.fieldPath]: {
                                          ...(prev[sug.fieldPath] || {}),
                                          [c.sourceValue]: {
                                            ...(prev[sug.fieldPath]?.[c.sourceValue] || {}),
                                            code: e.target.value
                                          }
                                        }
                                      }));
                                    }}
                                  />
                                </td>
                                <td className="py-2 pr-4">
                                  <input
                                    className="px-2 py-1 border rounded w-56"
                                    value={terminologyEdits?.[sug.fieldPath]?.[c.sourceValue]?.display || ''}
                                    onChange={(e) => {
                                      setTerminologyEdits(prev => ({
                                        ...prev,
                                        [sug.fieldPath]: {
                                          ...(prev[sug.fieldPath] || {}),
                                          [c.sourceValue]: {
                                            ...(prev[sug.fieldPath]?.[c.sourceValue] || {}),
                                            display: e.target.value
                                          }
                                        }
                                      }));
                                    }}
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <button
                  onClick={saveTerminology}
                  disabled={terminologyLoading}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
                >
                  {terminologyLoading ? 'Saving…' : 'Save Normalization'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* HL7 Viewer */}
        {currentView === 'hl7viewer' && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">HL7 Message Viewer & Staging</h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Left Panel: Ingest HL7 */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-amber-800 mb-4">Ingest HL7 v2 Message</h3>
                
                <div className="mb-4">
                  <label className="block text-sm font-semibold text-amber-700 mb-2">
                    Select Job
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                    onChange={(e) => {
                      const job = jobs.find(j => j.jobId === e.target.value);
                      setCurrentJob(job);
                      if (job) loadStagedMessages(job.jobId);
                    }}
                    value={currentJob?.jobId || ''}
                  >
                    <option value="">Select a job...</option>
                    {jobs.map(job => (
                      <option key={job.jobId} value={job.jobId}>
                        Job {job.jobId.substring(0, 12)} ({job.status})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-semibold text-amber-700 mb-2">
                    HL7 v2 Message
                  </label>
                  <textarea
                    className="w-full h-96 px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono text-xs"
                    placeholder="MSH|^~\&|SENDING_APP|FACILITY|...&#10;PID|1||MRN123456...&#10;OBR|1|ORDER123...&#10;OBX|1|NM|..."
                    value={hl7Input}
                    onChange={(e) => setHl7Input(e.target.value)}
                  />
                  <p className="text-xs text-amber-500 mt-1">
                    Paste raw HL7 v2 message (MSH, PID, OBR, OBX segments)
                  </p>
                </div>

                <button
                  onClick={ingestHL7Message}
                  disabled={loading || !currentJob}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Ingesting...' : '📥 Ingest to MongoDB Staging'}
                </button>

                <div className="mt-4 bg-blue-50 border-l-4 border-blue-500 p-3">
                  <p className="text-sm text-blue-800">
                    <strong>MongoDB Staging:</strong> Messages are stored temporarily for processing. 
                    Use this for high-volume HL7 feeds from hospital systems.
                  </p>
                </div>
              </div>

              {/* Right Panel: Staged Messages */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-amber-800 mb-4">
                  Staged Messages {currentJob ? `(Job: ${currentJob.jobId.substring(0, 12)})` : ''}
                </h3>

                {!currentJob ? (
                  <div className="text-center py-12 text-amber-600">
                    <div className="text-4xl mb-3">📋</div>
                    <p>Select a job to view staged messages</p>
                  </div>
                ) : stagedMessages.length === 0 ? (
                  <div className="text-center py-12 text-amber-600">
                    <div className="text-4xl mb-3">📭</div>
                    <p>No messages staged yet</p>
                    <p className="text-sm mt-2">Ingest HL7 messages to see them here</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {stagedMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`border-2 rounded-lg p-4 cursor-pointer transition ${
                          selectedMessage?.messageId === msg.messageId
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-amber-200 hover:border-amber-400'
                        }`}
                        onClick={() => setSelectedMessage(msg)}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="font-mono text-sm font-semibold text-amber-800">
                              {msg.messageId}
                            </p>
                            <p className="text-xs text-amber-600">
                              {msg.messageType}
                            </p>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            msg.processed ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'
                          }`}>
                            {msg.processed ? 'Processed' : 'Pending'}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">
                          Ingested: {new Date(msg.ingestionTimestamp).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {selectedMessage && (
                  <div className="mt-4 border-t-2 border-amber-200 pt-4">
                    <h4 className="text-sm font-semibold text-amber-700 mb-2">Message Preview</h4>
                    <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto max-h-64 overflow-y-auto">
{selectedMessage.rawMessage}
                    </pre>
                  </div>
                )}
              </div>
            </div>

            {/* HL7 Examples */}
            <div className="mt-6 bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-amber-800 mb-4">Sample HL7 Messages</h3>
              
              <div className="grid md:grid-cols-3 gap-4">
                <button
                  onClick={() => setHl7Input('MSH|^~\\&|EPIC|UCSF|INTERFACE|UCSF|20241011143052||ADT^A01|MSG000001|P|2.5\nPID|1||MRN123456^^^UCSF^MR||DOE^JOHN^ROBERT||19800515|M|||123 MAIN ST^^SAN FRANCISCO^CA^94102||555-1234\nPV1|1|I|3N^301^01^UCSF||||123456^SMITH^JANE^^^MD')}
                  className="bg-amber-100 hover:bg-amber-200 p-4 rounded-lg text-left transition"
                >
                  <p className="font-semibold text-amber-800 mb-1">Patient Admission (ADT^A01)</p>
                  <p className="text-xs text-amber-600">MSH, PID, PV1 segments</p>
                </button>
                
                <button
                  onClick={() => setHl7Input('MSH|^~\\&|LAB|UCSF|INTERFACE|UCSF|20241011103052||ORU^R01|MSG000002|P|2.5\nPID|1||MRN123456|||DOE^JOHN^ROBERT||19800515|M\nOBR|1|ORD123456|RES789012|2951-2^SODIUM^LN|||20241011080000\nOBX|1|NM|2951-2^SODIUM^LN||142|mmol/L|135-145|N|||F')}
                  className="bg-blue-100 hover:bg-blue-200 p-4 rounded-lg text-left transition"
                >
                  <p className="font-semibold text-blue-800 mb-1">Lab Result (ORU^R01)</p>
                  <p className="text-xs text-blue-600">MSH, PID, OBR, OBX segments</p>
                </button>
                
                <button
                  onClick={() => setHl7Input('MSH|^~\\&|ONCOLOGY|UCSF|REGISTRY|STATE|20240115090000||ADT^A04|MSG000003|P|2.5\nPID|1||MRN123456|||JOHNSON^SARAH^M||19650315|F\nDG1|1|ICD10|C50.9^BREAST CANCER^ICD10|BREAST CANCER||A\nPR1|1|CPT|19301^MASTECTOMY^CPT|MASTECTOMY|20240120080000')}
                  className="bg-green-100 hover:bg-green-200 p-4 rounded-lg text-left transition"
                >
                  <p className="font-semibold text-green-800 mb-1">Cancer Registry (ADT^A04)</p>
                  <p className="text-xs text-green-600">PID, DG1, PR1 segments</p>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Transformation Test View */}
        {currentView === 'transform' && currentJob && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">Test Data Transformation</h2>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-amber-800 mb-3">
                  Approved Mappings ({currentJob.finalMappings?.length || 0})
                </h3>
                <div className="space-y-2">
                  {currentJob.finalMappings?.map((mapping, index) => (
                    <div key={index} className="flex items-center text-sm bg-amber-50 px-4 py-2 rounded">
                      <span className="font-mono text-amber-700">{mapping.sourceField}</span>
                      <span className="mx-2 text-amber-500">→</span>
                      <span className="font-mono text-amber-700">{mapping.targetField}</span>
                      <span className="ml-auto text-xs text-amber-600">({mapping.suggestedTransform})</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-semibold text-amber-700 mb-2">
                  Sample Data (JSON) - Test your mappings
                </label>
                <textarea
                  className="w-full h-48 px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono text-sm"
                  placeholder='[{"patient_first_name": "John", "patient_last_name": "Doe", "date_of_birth": "1980-01-15"}]'
                  value={sampleData}
                  onChange={(e) => setSampleData(e.target.value)}
                />
                <p className="text-xs text-amber-500 mt-1">
                  Provide sample patient records to test the transformation
                </p>
              </div>

              <button
                onClick={testTransformation}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
              >
                {loading ? 'Testing...' : 'Run Transformation Test'}
              </button>
            </div>
          </div>
        )}

        {/* Ingestion Jobs View */}
        {currentView === 'ingestion' && (
          <div>
            <div className="flex items-center mb-6">
              <button onClick={() => setCurrentView('list')} className="text-amber-600 hover:text-amber-800 mr-4">← Back</button>
              <h2 className="text-2xl font-semibold text-amber-800">📡 Ingestion Jobs</h2>
            </div>

            <div className="bg-white rounded-lg shadow-md p-4 mb-4 flex justify-between items-center">
              <p className="text-sm text-gray-600">Monitor and control all streaming ingestion pipelines.</p>
              <div className="space-x-2">
                <button onClick={() => setShowIngestionModal(true)} className="px-3 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm">➕ Create Ingestion Job</button>
                <button onClick={fetchIngestionJobs} className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">Refresh</button>
              </div>
            </div>

            {isIngestionListLoading ? (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <div className="flex flex-col items-center space-y-4">
                  {/* Animated spinner */}
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
                  
                  {/* Loading message */}
                  <div className="text-gray-600">
                    <p className="text-lg font-medium">Loading ingestion jobs...</p>
                    {loadingStartTime && (
                      <p className="text-sm text-gray-500 mt-1">
                        {Math.floor((Date.now() - loadingStartTime) / 1000)}s elapsed
                      </p>
                    )}
                  </div>
                  
                  {/* Cancel button (shown after 2 seconds) */}
                  {showLoadingCancel && (
                    <button
                      onClick={cancelLoading}
                      className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm font-medium transition-colors"
                    >
                      Cancel Loading
                    </button>
                  )}
                  
                  {/* Helpful message if loading takes too long */}
                  {loadingStartTime && (Date.now() - loadingStartTime) > 5000 && (
                    <div className="text-sm text-amber-600 bg-amber-50 px-4 py-2 rounded-lg">
                      <p>This is taking longer than usual. You can cancel and try refreshing.</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="grid gap-4">
                {Array.isArray(ingestionJobs) && ingestionJobs.length > 0 ? ingestionJobs.map(j => (
                  <div key={j.job_id || j.jobId} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold text-amber-800">{j.job_name || 'Ingestion Job'}</h3>
                        <p className="text-xs text-gray-500 font-mono mt-1">{(j.job_id || j.jobId)}</p>
                        <p className="text-sm text-gray-700 mt-2">Status: <span className={`font-semibold ${j.status === 'RUNNING' ? 'text-green-600' : j.status === 'STOPPED' ? 'text-gray-600' : 'text-amber-600'}`}>{j.status}</span></p>
                      </div>
                      <div className="space-x-2">
                        {j.status !== 'RUNNING' && (
                          <button onClick={() => startIngestionJob(j.job_id || j.jobId)} className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg">▶ Start</button>
                        )}
                        {j.status === 'RUNNING' && (
                          <button onClick={() => stopIngestionJob(j.job_id || j.jobId)} className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg">⏸ Stop</button>
                        )}
                        <button onClick={() => openRecordsModal(j.job_id || j.jobId)} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg">👁 View Records</button>
                        <button onClick={() => openDataModelForIngestion(j)} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg">📊 Data Model</button>
                        <button onClick={() => openFailedModal(j.job_id || j.jobId)} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg">⚠ View Failed</button>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mt-4">
                      <div className="bg-gray-50 rounded p-4">
                        <p className="text-xs text-gray-500">Received</p>
                        <p className="text-xl font-semibold">{j.metrics?.received ?? 0}</p>
                      </div>
                      <div className="bg-gray-50 rounded p-4">
                        <p className="text-xs text-gray-500">Processed</p>
                        <p className="text-xl font-semibold text-green-700">{j.metrics?.processed ?? 0}</p>
                      </div>
                      <div className="bg-gray-50 rounded p-4">
                        <p className="text-xs text-gray-500">Failed</p>
                        <p className="text-xl font-semibold text-red-700">{j.metrics?.failed ?? 0}</p>
                      </div>
                    </div>

                    <div className="text-xs text-gray-500 mt-3">
                      Last update: {j.metrics?.last_update ? new Date(j.metrics.last_update).toLocaleTimeString() : '—'}
                    </div>
                  </div>
                )) : (
                  <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-600">No ingestion jobs yet</div>
                )}
              </div>
            )}

            {/* Ingestion Modal (Ingestion View) */}
            {showIngestionModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-xl p-6 max-w-xl w-full mx-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-gray-800">Create Ingestion Pipeline</h3>
                    <button onClick={() => setShowIngestionModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
                  </div>

                  <label className="block text-sm font-semibold text-gray-700 mb-2">Select Approved Mapping Job</label>
                  <select
                    className="w-full border border-gray-300 rounded-lg p-2 mb-4"
                    value={selectedIngestJobId || ''}
                    onChange={(e) => setSelectedIngestJobId(e.target.value)}
                  >
                    <option value="">-- Select Job --</option>
                    {jobs.filter(j => j.status === 'APPROVED').map(j => (
                      <option key={j.jobId} value={j.jobId}>
                        {j.jobId.substring(0,12)} — {Object.keys(j.sourceSchema).length}→{Object.keys(j.targetSchema).length} fields
                      </option>
                    ))}
                  </select>

                  <div className="flex justify-end space-x-2">
                    <button onClick={() => setShowIngestionModal(false)} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg">Cancel</button>
                    <button
                      disabled={!selectedIngestJobId || isIngestLoading}
                      onClick={async () => {
                        await createIngestionJob(selectedIngestJobId);
                        await startIngestionJob();
                        setShowIngestionModal(false);
                        fetchIngestionJobs();
                      }}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg disabled:opacity-50"
                    >
                      {isIngestLoading ? 'Creating...' : 'Create & Start'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* OMOP Viewer */}
        {currentView === 'omopviewer' && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">OMOP Viewer</h2>
            </div>

            <OMOPViewer token={token} />
          </div>
        )}

        {/* FHIR Viewer */}
        {currentView === 'fhirviewer' && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">FHIR Viewer</h2>
            </div>

            <FHIRViewer token={token} />
          </div>
        )}

        {/* FHIR Chatbot */}
        {currentView === 'chatbot' && (
          <div>
            <div className="flex items-center mb-6">
              <button
                onClick={() => setCurrentView('list')}
                className="text-amber-600 hover:text-amber-800 mr-4"
              >
                ← Back
              </button>
              <h2 className="text-2xl font-semibold text-amber-800">💬 FHIR Data Chatbot</h2>
            </div>

            <FHIRChatbot token={token} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t-2 border-amber-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 text-center text-sm text-amber-600">
          <p>AI Data Interoperability Platform v2.0.0</p>
          <p className="mt-1">Healthcare EHR/HL7 Mapping • Sentence-BERT • SQLite • JWT • Containerized</p>
        </div>
      </footer>

      {showRecordsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-3xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Ingested Records — {recordsModalJobId}</h3>
              <button onClick={() => setShowRecordsModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            {recordsLoading ? (
              <div className="text-gray-600">Loading...</div>
            ) : recordsModalData.length === 0 ? (
              <div className="text-gray-600">No records found.</div>
            ) : (
            <div className="space-y-3">
                {recordsModalData.map((r, idx) => (
                  <div key={idx} className="bg-gray-50 rounded p-3 text-xs font-mono overflow-auto">
                    <pre>{JSON.stringify(r, null, 2)}</pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {showDataModel && currentJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-5xl w-full mx-4 max-h-[85vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">Data Model — Job {currentJob.jobId.substring(0,12)}</h3>
              <button onClick={() => setShowDataModel(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            <div className="mb-4 border-b">
              <button className={`px-3 py-2 mr-2 ${dataModelTab==='FHIR'?'border-b-2 border-amber-600':''}`} onClick={()=>setDataModelTab('FHIR')}>FHIR</button>
              <button className={`px-3 py-2 ${dataModelTab==='OMOP'?'border-b-2 border-amber-600':''}`} onClick={()=>setDataModelTab('OMOP')}>OMOP</button>
            </div>
            {dataModelTab==='FHIR' && (
              <div className="text-sm text-gray-700">
                <p className="mb-3">Preview FHIR resources generated from recent ingestion records based on your approved mappings.</p>
                <p className="text-gray-500">Use your existing Ingestion + View Records to validate FHIR output (already implemented).</p>
              </div>
            )}
            {dataModelTab==='OMOP' && (
              <div className="text-sm text-gray-700">
                {/* OMOP Sub-tabs - Simplified Workflow */}
                <div className="flex items-center space-x-1 mb-4 border-b">
                  <button 
                    className={`px-3 py-2 ${omopSubTab==='predict'?'border-b-2 border-amber-600 bg-amber-50':'text-gray-600'}`} 
                    onClick={()=>setOmopSubTab('predict')}
                  >
                    1. Predict Table
                  </button>
                  <button 
                    className={`px-3 py-2 ${omopSubTab==='normalize'?'border-b-2 border-amber-600 bg-amber-50':'text-gray-600'}`} 
                    onClick={()=>setOmopSubTab('normalize')}
                  >
                    2. Normalize & Review Concepts
                  </button>
                  <button 
                    className={`px-3 py-2 ${omopSubTab==='preview'?'border-b-2 border-amber-600 bg-amber-50':'text-gray-600'}`} 
                    onClick={()=>setOmopSubTab('preview')}
                  >
                    3. Preview OMOP Rows
                  </button>
                  <button 
                    className={`px-3 py-2 ${omopSubTab==='persist'?'border-b-2 border-amber-600 bg-amber-50':'text-gray-600'}`} 
                    onClick={()=>setOmopSubTab('persist')}
                  >
                    4. Persist to MongoDB
                  </button>
                </div>

                {/* Predict Table Tab */}
                {omopSubTab === 'predict' && (
                  <div>
                    <div className="flex items-center space-x-2 mb-3">
                      <button onClick={async ()=>{
                        try{
                          // Pass both schema and job_id to allow FHIR resource detection
                          const resp = await axios.post(`${API_BASE_URL}/api/v1/omop/predict-table`, { 
                            schema: currentJob.sourceSchema || {},
                            job_id: currentJob.jobId 
                          }, { headers: { ...authHeaders } });
                          setOmopPrediction(resp.data);
                        }catch(e){ console.error(e); }
                      }} className="px-3 py-2 bg-blue-600 text-white rounded">Predict OMOP Table</button>
                    </div>
                    
                    <div className="mb-4">
                      <p className="text-gray-800"><span className="font-semibold">Predicted Table:</span> {omopPrediction?.table || '—'} <span className="ml-2 text-gray-500">(conf: {omopPrediction?.confidence?.toFixed?.(2) || '—'})</span></p>
                      {omopPrediction?.alternatives && (
                        <p className="text-xs text-amber-600 mt-1">Alternatives: {omopPrediction.alternatives.map(a => `${a.table}(${a.confidence.toFixed(2)})`).join(', ')}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Normalize Concepts Tab */}
                {omopSubTab === 'normalize' && (
                  <div>
                    {/* Info Banner */}
                    <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-2">📋 Normalize & Review Concepts</h4>
                      <p className="text-sm text-blue-700">
                        This step uses AI to map FHIR codes (ICD-10, LOINC, SNOMED) to OMOP Standard Concept IDs.
                        All mappings are shown below with confidence scores. Review and edit any mappings before proceeding to Preview.
                      </p>
                      <div className="mt-2 text-xs text-blue-600">
                        💡 <strong>Tip:</strong> High-confidence mappings (≥80%) can usually be auto-approved. 
                        Review medium/low-confidence mappings (shown in yellow/red) more carefully.
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 mb-3">
                      <button onClick={generateOmopConcepts} className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors">
                        🔄 Normalize Concepts
                      </button>
                    </div>

                    {/* Concept Normalization Section */}
                    {Object.keys(omopConceptSuggestions).length > 0 && (
                      <div className="mb-4 border rounded-lg p-4 bg-blue-50">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-semibold text-lg">Concept Normalization Results</h4>
                          <div className="text-sm text-gray-600">
                            {Object.values(omopConceptSuggestions).flat().length} total mappings
                          </div>
                        </div>
                        
                        {/* Summary Statistics */}
                        <div className="grid grid-cols-3 gap-4 mb-6">
                          <div className="bg-green-100 border border-green-300 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-green-800">
                              {Object.values(omopConceptSuggestions).flat().filter(s => s.confidence >= 0.8).length}
                            </div>
                            <div className="text-sm text-green-700">High Confidence (&ge;80%)</div>
                          </div>
                          <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-yellow-800">
                              {Object.values(omopConceptSuggestions).flat().filter(s => s.confidence >= 0.5 && s.confidence < 0.8).length}
                            </div>
                            <div className="text-sm text-yellow-700">Medium Confidence (50-79%)</div>
                          </div>
                          <div className="bg-red-100 border border-red-300 rounded-lg p-3 text-center">
                            <div className="text-2xl font-bold text-red-800">
                              {Object.values(omopConceptSuggestions).flat().filter(s => s.confidence < 0.5).length}
                            </div>
                            <div className="text-sm text-red-700">Low Confidence (&lt;50%)</div>
                          </div>
                        </div>

                        {Object.entries(omopConceptSuggestions).map(([field, suggestions]) => (
                          <div key={field} className="mb-6 border border-gray-200 rounded-lg p-4 bg-white">
                            <div className="flex items-center justify-between mb-3">
                              <h5 className="font-semibold text-amber-800">{field}</h5>
                              <span className="text-sm text-gray-600">{suggestions.length} mappings</span>
                            </div>
                            
                            <div className="space-y-3">
                              {suggestions.map((s, i) => (
                                <div key={i} className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
                                  <div className="grid grid-cols-12 gap-3 items-center">
                                    {/* Source Value */}
                                    <div className="col-span-2">
                                      <div className="text-xs text-gray-500 mb-1">Source Value</div>
                                      <div className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                                        {s.source_value}
                                      </div>
                                    </div>
                                    
                                    {/* Arrow */}
                                    <div className="col-span-1 flex justify-center">
                                      <span className="text-gray-400 text-lg">→</span>
                                    </div>
                                    
                                    {/* Concept ID Input */}
                                    <div className="col-span-2">
                                      <div className="text-xs text-gray-500 mb-1">Concept ID</div>
                                      <input
                                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                        value={omopConceptEdits[field]?.[s.source_value]?.concept_id || s.concept_id}
                                        onChange={(e) => {
                                          setOmopConceptEdits(prev => ({
                                            ...prev,
                                            [field]: {
                                              ...prev[field],
                                              [s.source_value]: {
                                                ...prev[field]?.[s.source_value],
                                                concept_id: parseInt(e.target.value) || 0
                                              }
                                            }
                                          }));
                                        }}
                                        placeholder="concept_id"
                                      />
                                    </div>
                                    
                                    {/* Concept Name */}
                                    <div className="col-span-3">
                                      <div className="text-xs text-gray-500 mb-1">Concept Name</div>
                                      <div className="text-sm text-gray-700 truncate" title={s.concept_name}>
                                        {s.concept_name}
                                      </div>
                                    </div>
                                    
                                    {/* Vocabulary */}
                                    <div className="col-span-2">
                                      <div className="text-xs text-gray-500 mb-1">Vocabulary</div>
                                      <div className="text-sm text-gray-600">
                                        {s.vocabulary_id || 'Unknown'}
                                      </div>
                                    </div>
                                    
                                    {/* Confidence Score */}
                                    <div className="col-span-2">
                                      <div className="text-xs text-gray-500 mb-1">Confidence</div>
                                      <div className="flex items-center space-x-2">
                                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                                          <div 
                                            className={`h-2 rounded-full transition-all duration-300 ${
                                              s.confidence >= 0.8 ? 'bg-green-500' : 
                                              s.confidence >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                                            }`}
                                            style={{ width: `${s.confidence * 100}%` }}
                                          />
                                        </div>
                                        <span className={`text-xs font-semibold ${
                                          s.confidence >= 0.8 ? 'text-green-700' : 
                                          s.confidence >= 0.5 ? 'text-yellow-700' : 'text-red-700'
                                        }`}>
                                          {(s.confidence * 100).toFixed(0)}%
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                  
                                  {/* Reasoning (if available) */}
                                  {s.reasoning && (
                                    <div className="mt-2 text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
                                      <strong>Reasoning:</strong> {s.reasoning}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                            
                            <div className="mt-4 flex justify-end">
                              <button 
                                onClick={saveOmopConcepts} 
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-semibold transition-colors"
                              >
                                Save Mappings for {field}
                              </button>
                            </div>
                          </div>
                        ))}
                        
                        {/* Global Actions */}
                        <div className="mt-6 flex justify-between items-center pt-4 border-t border-gray-200">
                          <div className="text-sm text-gray-600">
                            Review all mappings before saving. High confidence mappings can be auto-approved.
                          </div>
                          <div className="flex space-x-2">
                            <button 
                              onClick={async () => {
                                // Auto-approve high confidence mappings
                                const edits = {};
                                Object.entries(omopConceptSuggestions).forEach(([field, suggestions]) => {
                                  edits[field] = {};
                                  suggestions.forEach(s => {
                                    if (s.confidence >= 0.8) {
                                      edits[field][s.source_value] = { concept_id: s.concept_id };
                                    }
                                  });
                                });
                                setOmopConceptEdits(prev => ({ ...prev, ...edits }));
                                
                                // Automatically save and persist
                                try {
                                  // Save concept mappings
                                  for (const [field, fieldEdits] of Object.entries(edits)) {
                                    await axios.put(`${API_BASE_URL}/api/v1/omop/concepts/approve`,
                                      {
                                        job_id: currentJob.jobId,
                                        field_path: field,
                                        mapping: fieldEdits,
                                        approved_by: userId
                                      },
                                      { headers: { ...authHeaders } }
                                    );
                                  }
                                  
                                  // Trigger OMOP persistence
                                  const persistResp = await axios.post(`${API_BASE_URL}/api/v1/omop/persist-all`, 
                                    { 
                                      job_id: currentJob.jobId, 
                                      table: omopPrediction?.table || omopPreview?.table || null 
                                    }, 
                                    { headers: { ...authHeaders } }
                                  );
                                  
                                  const data = persistResp.data;
                                  const message = `✅ Auto-Approved High Confidence Mappings & OMOP Persisted!\n\n` +
                                    `Table: omop_${data.table || 'PERSON'}\n` +
                                    `Inserted/Updated: ${data.inserted || 0} rows\n` +
                                    `Total Records Found: ${data.total_records_found || 0}\n` +
                                    `Source: ${data.source || 'Unknown'}\n` +
                                    `Job ID: ${currentJob.jobId.substring(0, 16)}...`;
                                  alert(message);
                                } catch (error) {
                                  console.error('Auto-approve and persist error:', error);
                                  alert('Auto-approved mappings, but persistence failed. Check the Persist tab.');
                                }
                              }}
                              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors"
                            >
                              Auto-Approve High Confidence & Persist
                            </button>
                            <button 
                              onClick={saveOmopConcepts} 
                              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-semibold transition-colors"
                            >
                              Save All Mappings
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Review Concepts Tab */}
                {/* Review step removed - now integrated into Normalize Concepts tab */}

                {/* Preview Tab */}
                {omopSubTab === 'preview' && (
                  <div>
                    <div className="flex items-center space-x-2 mb-3">
                      <button onClick={async ()=>{
                        try{
                          const resp = await axios.post(`${API_BASE_URL}/api/v1/omop/preview`, { job_id: currentJob.jobId, table: omopPrediction?.table || null, limit: 10 }, { headers: { ...authHeaders } });
                          setOmopPreview(resp.data);
                        }catch(e){ console.error(e); }
                      }} className="px-3 py-2 bg-amber-600 text-white rounded">Preview OMOP Rows</button>
                    </div>

                    <div className="bg-gray-50 border rounded p-3 max-h-96 overflow-auto text-xs font-mono">
                      <pre>{JSON.stringify(omopPreview, null, 2)}</pre>
                    </div>
                  </div>
                )}

                {/* Persist Tab */}
                {omopSubTab === 'persist' && (
                  <div>
                    {/* Info about current job */}
                    <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-900 font-semibold mb-2">Ready to persist OMOP data:</p>
                      <p className="text-sm text-blue-700">
                        Job ID: <span className="font-mono">{currentJob.jobId}</span>
                      </p>
                      <p className="text-sm text-blue-700">
                        Target Table: <span className="font-mono">omop_{omopPrediction?.table || omopPreview?.table || 'PERSON'}</span>
                      </p>
                    </div>

                    {/* Persist Button */}
                    <div className="flex items-center space-x-2 mb-3">
                      <button onClick={async ()=>{
                        try{
                          const resp = await axios.post(`${API_BASE_URL}/api/v1/omop/persist-all`, { 
                            job_id: currentJob.jobId, 
                            table: omopPrediction?.table || omopPreview?.table || null 
                          }, { headers: { ...authHeaders } });
                          const data = resp.data;
                          
                          // Check if there was an error message
                          if (data.message && data.message.includes('❌')) {
                            alert(data.message);
                          } else {
                            const message = `✅ OMOP Persist Complete\n\n` +
                              `Table: omop_${data.table || 'PERSON'}\n` +
                              `Inserted/Updated: ${data.inserted || 0} rows\n` +
                              `Total Records Found: ${data.total_records_found || 0}\n` +
                              `Source: ${data.source || 'Unknown'}\n` +
                              `Job ID: ${currentJob.jobId.substring(0, 16)}...`;
                            alert(message);
                          }
                        }catch(e){ 
                          console.error(e); 
                          const errorMsg = e.response?.data?.detail || e.response?.data?.message || e.message;
                          alert(`❌ Error: ${errorMsg}`);
                        }
                      }} className="px-4 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-semibold shadow-md">
                        Persist ALL to Mongo
                      </button>
                    </div>

                    <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
                      <p className="mb-1">💡 <strong>Tip:</strong> Make sure you've completed the previous steps:</p>
                      <ul className="list-disc list-inside ml-2 space-y-1">
                        <li>1. Predict Table - to determine target OMOP table</li>
                        <li>2. Normalize & Review Concepts - to map codes to OMOP concepts</li>
                        <li>3. Preview - to verify OMOP row structure</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {showFailedModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-800">Failed Records</h3>
                <p className="text-sm text-gray-500 font-mono mt-1">Job: {failedModalJobId}</p>
              </div>
              <button onClick={() => setShowFailedModal(false)} className="text-gray-500 hover:text-gray-700 text-2xl">×</button>
            </div>
            
            {failedLoading ? (
              <div className="text-gray-600">Loading failed records...</div>
            ) : failedModalData.length === 0 ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 font-semibold">✅ No failed records!</p>
                <p className="text-green-600 text-sm mt-1">All records were successfully ingested.</p>
              </div>
            ) : (
              <div>
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-800 font-semibold">❌ {failedModalData.length} record(s) failed to ingest</p>
                  <p className="text-red-600 text-sm mt-1">Review the error details below and fix the source data or transformation logic.</p>
                </div>
                
                <div className="space-y-4">
                  {failedModalData.map((r, idx) => {
                    // Extract error info
                    const errorReason = r.error_reason || 'Unknown error';
                    const failedAt = r.failed_at ? new Date(r.failed_at).toLocaleString() : 'Unknown time';
                    
                    // Get source data fields (exclude metadata)
                    const metadataKeys = ['_id', 'job_id', 'error_reason', 'failed_at', 'ingested_at'];
                    const sourceFields = Object.keys(r).filter(k => !metadataKeys.includes(k));
                    const sourceData = {};
                    sourceFields.forEach(k => sourceData[k] = r[k]);
                    
                    return (
                      <div key={idx} className="border border-red-200 rounded-lg overflow-hidden">
                        {/* Error Header */}
                        <div className="bg-red-100 px-4 py-3 border-b border-red-200">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-semibold text-red-900">Record #{idx + 1}</p>
                              <p className="text-sm text-red-700 mt-1">
                                <span className="font-semibold">Error:</span> {errorReason}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-xs text-red-600">{failedAt}</p>
                            </div>
                          </div>
                        </div>
                        
                        {/* Source Data */}
                        <div className="bg-white px-4 py-3">
                          <p className="text-sm font-semibold text-gray-700 mb-2">Source Data:</p>
                          {sourceFields.length > 0 ? (
                            <div className="bg-gray-50 rounded p-3 text-xs font-mono overflow-auto max-h-60">
                              <pre>{JSON.stringify(sourceData, null, 2)}</pre>
                            </div>
                          ) : (
                            <p className="text-sm text-gray-500 italic">No source data available</p>
                          )}
                        </div>
                        
                        {/* Action Suggestions */}
                        <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
                          <p className="text-xs text-gray-600">
                            💡 <strong>Tip:</strong> {
                              errorReason.includes('simulated') ? 
                                'This is a simulated failure for testing. Remove test failures in production.' :
                              errorReason.includes('validation') ?
                                'Check if the source data meets validation requirements.' :
                              errorReason.includes('transformation') ?
                                'Review the transformation logic and mapping configuration.' :
                                'Check the backend logs for detailed error information.'
                            }
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function OMOPViewer({ token }) {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [jobFilter, setJobFilter] = useState('');
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : {};

  const loadTables = async () => {
    try {
      const resp = await axios.get(`${API_BASE_URL}/api/v1/omop/tables`, { headers: { ...authHeaders } });
      setTables(resp.data.tables || []);
      if (!selectedTable && (resp.data.tables || []).length > 0) {
        setSelectedTable(resp.data.tables[0]);
      }
    } catch (e) {
      setError(`Failed to load OMOP tables: ${e.response?.data?.detail || e.message}`);
    }
  };

  const fetchData = async () => {
    if (!selectedTable) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ table: selectedTable, limit: '200' });
      if (jobFilter) params.append('job_id', jobFilter);
      const resp = await axios.get(`${API_BASE_URL}/api/v1/omop/data?${params.toString()}`, { headers: { ...authHeaders } });
      setRows(resp.data.rows || []);
    } catch (e) {
      setError(`Failed to load OMOP data: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadTables(); }, []);

  const columns = React.useMemo(() => {
    if (!rows || rows.length === 0) return [];
    const keys = Array.from(new Set(rows.flatMap(r => Object.keys(r))));
    return keys;
  }, [rows]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="grid md:grid-cols-4 gap-4 mb-4">
        <div>
          <label className="block text-sm font-semibold text-amber-700 mb-2">OMOP Table</label>
          <select
            className="w-full px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            value={selectedTable}
            onChange={(e) => setSelectedTable(e.target.value)}
          >
            <option value="">Select table…</option>
            {tables.map(t => (<option key={t} value={t}>{t}</option>))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-amber-700 mb-2">Filter by Job ID (optional)</label>
          <input
            type="text"
            value={jobFilter}
            onChange={(e) => setJobFilter(e.target.value)}
            placeholder="e.g., job_1760388571 or mapping job id"
            className="w-full px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={fetchData}
            disabled={!selectedTable || loading}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Loading…' : 'Fetch Data'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-3 text-red-800 text-sm">{error}</div>
      )}

      {rows.length === 0 ? (
        <div className="text-center py-12 text-amber-600">
          <div className="text-4xl mb-3">📭</div>
          <p>No rows loaded. Choose a table and click Fetch Data.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map(col => (
                  <th key={col} className="px-3 py-2 text-left text-xs font-semibold text-gray-600">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {rows.map((r, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  {columns.map(c => (
                    <td key={c} className="px-3 py-2 text-xs text-gray-700 whitespace-nowrap">
                      {typeof r[c] === 'object' ? JSON.stringify(r[c]) : String(r[c] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FHIRViewer({ token }) {
  const [resources, setResources] = useState([]);
  const [resourceType, setResourceType] = useState('');
  const [jobFilter, setJobFilter] = useState('');
  const [query, setQuery] = useState('');
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const authHeaders = token ? { 'Authorization': `Bearer ${token}` } : {};

  const loadResources = async () => {
    try {
      const resp = await axios.get(`${API_BASE_URL}/api/v1/fhir/store/resources`, { headers: { ...authHeaders } });
      setResources(resp.data.resources || []);
      if (!resourceType && (resp.data.resources || []).length > 0) {
        setResourceType(resp.data.resources[0]);
      }
    } catch (e) {
      setError(`Failed to load FHIR resource types: ${e.response?.data?.detail || e.message}`);
    }
  };

  const fetchEntries = async () => {
    if (!resourceType) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (jobFilter) params.append('job_id', jobFilter);
      if (query) params.append('q', query);
      const resp = await axios.get(`${API_BASE_URL}/api/v1/fhir/store/${resourceType}?${params.toString()}`, { headers: { ...authHeaders } });
      setEntries(resp.data.entries || []);
    } catch (e) {
      setError(`Failed to load FHIR entries: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadResources(); }, []);

  const columns = React.useMemo(() => {
    if (!entries || entries.length === 0) return [];
    const keys = Array.from(new Set(entries.flatMap(r => Object.keys(r))));
    return keys;
  }, [entries]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="grid md:grid-cols-5 gap-4 mb-4">
        <div>
          <label className="block text-sm font-semibold text-amber-700 mb-2">Resource Type</label>
          <select
            className="w-full px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
            value={resourceType}
            onChange={(e) => setResourceType(e.target.value)}
          >
            <option value="">Select resource…</option>
            {resources.map(r => (<option key={r} value={r}>{r}</option>))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-amber-700 mb-2">Filter by Job ID (optional)</label>
          <input
            type="text"
            value={jobFilter}
            onChange={(e) => setJobFilter(e.target.value)}
            placeholder="job_..."
            className="w-full px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-semibold text-amber-700 mb-2">Search (id, name, identifier)</label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Garcia, MRN123..."
            className="w-full px-3 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={fetchEntries}
            disabled={!resourceType || loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition duration-200 disabled:opacity-50"
          >
            {loading ? 'Loading…' : 'Fetch Resources'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-3 text-red-800 text-sm">{error}</div>
      )}

      {entries.length === 0 ? (
        <div className="text-center py-12 text-amber-600">
          <div className="text-4xl mb-3">📭</div>
          <p>No entries loaded. Choose a resource and click Fetch.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map(col => (
                  <th key={col} className="px-3 py-2 text-left text-xs font-semibold text-gray-600">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {entries.map((r, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  {columns.map(c => (
                    <td key={c} className="px-3 py-2 text-xs text-gray-700 whitespace-nowrap">
                      {typeof r[c] === 'object' ? JSON.stringify(r[c]) : String(r[c] ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
export default App;
