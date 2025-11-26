import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ConceptReviewPanel = ({ jobId, authHeaders, onStatsUpdate }) => {
  const [reviewQueue, setReviewQueue] = useState([]);
  const [currentReview, setCurrentReview] = useState(0);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ pending: 0, approved: 0, rejected: 0, total: 0 });
  const [selectedConcept, setSelectedConcept] = useState(null);

  // Fetch review queue on mount
  useEffect(() => {
    fetchReviewQueue();
    fetchStats();
  }, [jobId]);

  const fetchReviewQueue = async () => {
    try {
      setLoading(true);
      const resp = await axios.get(
        `${API_BASE_URL}/api/v1/omop/concepts/review-queue/${jobId}?status=pending`,
        { headers: authHeaders }
      );
      setReviewQueue(resp.data.items || []);
    } catch (e) {
      console.error('Failed to fetch review queue:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const resp = await axios.get(
        `${API_BASE_URL}/api/v1/omop/concepts/stats/${jobId}`,
        { headers: authHeaders }
      );
      const newStats = resp.data.stats;
      setStats(newStats);
      if (onStatsUpdate) {
        onStatsUpdate(newStats);
      }
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  };

  const approveMapping = async (reviewId, conceptId) => {
    try {
      await axios.post(
        `${API_BASE_URL}/api/v1/omop/concepts/approve-mapping`,
        { review_id: reviewId, selected_concept_id: conceptId },
        { headers: authHeaders }
      );
      
      // Remove from queue and move to next
      setReviewQueue(prev => prev.filter(item => item.id !== reviewId));
      if (currentReview >= reviewQueue.length - 1) {
        setCurrentReview(Math.max(0, currentReview - 1));
      }
      
      // Refresh stats
      fetchStats();
      
      // Show success message
      alert('✅ Concept mapping approved successfully');
    } catch (e) {
      console.error('Failed to approve mapping:', e);
      alert(`❌ Error: ${e.response?.data?.detail || e.message}`);
    }
  };

  const rejectMapping = async (reviewId) => {
    try {
      await axios.post(
        `${API_BASE_URL}/api/v1/omop/concepts/reject-mapping`,
        { review_id: reviewId },
        { headers: authHeaders }
      );
      
      // Remove from queue and move to next
      setReviewQueue(prev => prev.filter(item => item.id !== reviewId));
      if (currentReview >= reviewQueue.length - 1) {
        setCurrentReview(Math.max(0, currentReview - 1));
      }
      
      // Refresh stats
      fetchStats();
      
      // Show success message
      alert('❌ Concept mapping rejected');
    } catch (e) {
      console.error('Failed to reject mapping:', e);
      alert(`❌ Error: ${e.response?.data?.detail || e.message}`);
    }
  };

  const nextReview = () => {
    if (currentReview < reviewQueue.length - 1) {
      setCurrentReview(currentReview + 1);
    }
  };

  const previousReview = () => {
    if (currentReview > 0) {
      setCurrentReview(currentReview - 1);
    }
  };

  const autoApproveAll = async () => {
    if (!window.confirm('Auto-approve all high-confidence mappings? This action cannot be undone.')) {
      return;
    }
    
    try {
      const highConfidenceItems = reviewQueue.filter(item => item.confidence >= 0.9);
      const approvals = highConfidenceItems.map(item => ({
        review_id: item.id,
        concept_id: item.suggested_concept_id
      }));
      
      if (approvals.length === 0) {
        alert('No high-confidence mappings found to auto-approve');
        return;
      }
      
      await axios.post(
        `${API_BASE_URL}/api/v1/omop/concepts/bulk-approve`,
        { job_id: jobId, approvals },
        { headers: authHeaders }
      );
      
      // Refresh queue and stats
      fetchReviewQueue();
      fetchStats();
      
      alert(`✅ Auto-approved ${approvals.length} high-confidence mappings`);
    } catch (e) {
      console.error('Failed to auto-approve:', e);
      alert(`❌ Error: ${e.response?.data?.detail || e.message}`);
    }
  };

  const currentItem = reviewQueue[currentReview];

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600"></div>
        <span className="ml-2 text-gray-600">Loading review queue...</span>
      </div>
    );
  }

  if (reviewQueue.length === 0) {
    return (
      <div className="text-center p-8">
        <div className="text-6xl mb-4">✅</div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">No Items to Review</h3>
        <p className="text-gray-600">All concept mappings have been processed or no mappings require review.</p>
        <button
          onClick={fetchReviewQueue}
          className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
        >
          Refresh Queue
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{stats.approved}</div>
          <div className="text-sm text-green-700">Auto-Approved</div>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
          <div className="text-sm text-amber-700">Needs Review</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
          <div className="text-sm text-red-700">Rejected</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-600">{stats.total}</div>
          <div className="text-sm text-gray-700">Total</div>
        </div>
      </div>

      {/* Current review item */}
      {currentItem && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Source Information */}
            <div>
              <h4 className="text-lg font-semibold text-gray-800 mb-4">Source Information</h4>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-600">Code System:</dt>
                  <dd className="text-sm text-gray-900 font-mono">{currentItem.source_system}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Code:</dt>
                  <dd className="text-sm text-gray-900 font-mono">{currentItem.source_code}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Display:</dt>
                  <dd className="text-sm text-gray-900">{currentItem.source_display}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Field:</dt>
                  <dd className="text-sm text-gray-900 font-mono">{currentItem.source_field}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Target Domain:</dt>
                  <dd className="text-sm text-gray-900">{currentItem.target_domain}</dd>
                </div>
              </dl>
            </div>

            {/* Suggested Concepts */}
            <div>
              <h4 className="text-lg font-semibold text-gray-800 mb-4">Suggested OMOP Concepts</h4>
              <div className="space-y-3">
                {JSON.parse(currentItem.alternatives || '[]').map((alt, idx) => (
                  <ConceptOption
                    key={alt.concept_id}
                    rank={idx + 1}
                    concept={alt}
                    isRecommended={idx === 0}
                    isSelected={selectedConcept === alt.concept_id}
                    onSelect={() => setSelectedConcept(alt.concept_id)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="mt-6 flex items-center space-x-3">
            <button
              onClick={() => approveMapping(currentItem.id, selectedConcept || currentItem.suggested_concept_id)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
            >
              Approve Selected
            </button>
            <button
              onClick={() => approveMapping(currentItem.id, currentItem.suggested_concept_id)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
            >
              Approve Recommended
            </button>
            <button
              onClick={() => rejectMapping(currentItem.id)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold"
            >
              Reject
            </button>
            <button
              onClick={autoApproveAll}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-semibold"
            >
              Auto-Approve All High-Confidence
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={previousReview}
          disabled={currentReview === 0}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <span className="text-sm text-gray-600">
          {currentReview + 1} of {reviewQueue.length}
        </span>
        
        <button
          onClick={nextReview}
          disabled={currentReview >= reviewQueue.length - 1}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
};

const ConceptOption = ({ rank, concept, isRecommended, isSelected, onSelect }) => {
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'text-green-600 bg-green-50 border-green-200';
    if (confidence >= 0.7) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <div 
      className={`border rounded-lg p-4 cursor-pointer transition-all ${
        isSelected ? 'ring-2 ring-blue-500 border-blue-300' : 'border-gray-200 hover:border-gray-300'
      } ${isRecommended ? 'bg-blue-50' : 'bg-white'}`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm font-semibold text-gray-600">#{rank}</span>
            {isRecommended && (
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Recommended</span>
            )}
          </div>
          
          <h5 className="font-semibold text-gray-900 mb-1">{concept.concept_name}</h5>
          <p className="text-sm text-gray-600 font-mono">ID: {concept.concept_id}</p>
          <p className="text-sm text-gray-600">Vocabulary: {concept.vocabulary_id}</p>
        </div>
        
        <div className="text-right">
          <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold border ${getConfidenceColor(concept.confidence)}`}>
            {(concept.confidence * 100).toFixed(0)}%
          </div>
        </div>
      </div>
      
      {concept.reasoning && (
        <div className="mt-2 text-xs text-gray-500">
          <strong>Reasoning:</strong> {concept.reasoning}
        </div>
      )}
    </div>
  );
};

export default ConceptReviewPanel;
