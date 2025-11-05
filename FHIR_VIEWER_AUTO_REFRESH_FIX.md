# FHIR Viewer Auto-Refresh Fix

## Problem

When viewing FHIR Resources and clicking "View Details", the modal would automatically close due to auto-refresh.

## Root Cause

The App component had a `setInterval` that refreshed jobs every 5 seconds:

```javascript
useEffect(() => {
  if (isAuthReady) {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);  // ← Causes re-render
    return () => clearInterval(interval);
  }
}, [isAuthReady, token]);
```

This caused:
1. **Every 5 seconds**: `fetchJobs()` runs
2. **State updates**: Jobs state changes trigger re-render
3. **Component re-renders**: All child components re-render
4. **Modals close**: FHIRViewer modal state resets

## Solution Implemented

### Fix 1: Prevent Fetch When Modal Open

Updated FHIRViewer to skip fetching resources when detail modal is open:

```javascript
React.useEffect(() => {
  if (!selectedResourceType || showDetailModal) return;  // ← Skip if modal open
  
  const fetchResources = async () => {
    // ... fetch logic
  };
  
  fetchResources();
}, [selectedResourceType, jobIdFilter, searchQuery, showDetailModal]);
```

### Fix 2: Pause Auto-Refresh on Viewer Pages

Updated the main auto-refresh logic to pause when:
- Any modal is open
- User is on a viewer page (FHIR, HL7, OMOP)

```javascript
useEffect(() => {
  if (isAuthReady) {
    fetchJobs();
    
    const interval = setInterval(() => {
      // Check if modal is open
      const isModalOpen = showRecordsModal || showFailedModal || 
                         showDataModel || showIngestionModal;
      
      // Check if on viewer page
      const isOnViewerPage = currentView === 'fhirviewer' || 
                            currentView === 'hl7viewer' || 
                            currentView === 'omopviewer';
      
      // Only refresh if no modal and not on viewer page
      if (!isModalOpen && !isOnViewerPage) {
        fetchJobs();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }
}, [isAuthReady, token, showRecordsModal, showFailedModal, 
    showDataModel, showIngestionModal, currentView]);
```

## Benefits

✅ **Modals stay open**: No more auto-closing when viewing details
✅ **Better UX on viewer pages**: No jarring refreshes while browsing FHIR/HL7/OMOP data
✅ **Auto-refresh still works**: Jobs list still updates every 5 seconds on main pages
✅ **Performance**: Reduces unnecessary API calls when on viewer pages

## Affected Pages

### Auto-Refresh Paused On:
- FHIR Viewer (`currentView === 'fhirviewer'`)
- HL7 Viewer (`currentView === 'hl7viewer'`)
- OMOP Viewer (`currentView === 'omopviewer'`)
- Any page with open modals (Records, Failed, Data Model, Ingestion)

### Auto-Refresh Active On:
- Mapping Jobs list (`currentView === 'list'`)
- Connector Configuration (`currentView === 'connector'`)
- Review page (`currentView === 'review'`)
- Terminology page (`currentView === 'terminology'`)
- Transform page (`currentView === 'transform'`)
- Ingestion list (`currentView === 'ingestion'`)

## Testing

### Before Fix
1. Go to FHIR Viewer
2. Click "View Details" on any resource
3. Wait 5 seconds
4. ❌ Modal closes automatically

### After Fix
1. Go to FHIR Viewer
2. Click "View Details" on any resource
3. Wait 5+ seconds
4. ✅ Modal stays open
5. Close modal and go back to list
6. ✅ Auto-refresh resumes

## Files Modified

1. ✅ `frontend/src/App.jsx` - Updated auto-refresh logic

## Status

✅ **Fixed and Deployed**
- Frontend restarted with fix
- Compiled successfully
- Ready for testing

## Future Enhancements

Consider:
- Add manual refresh button on viewer pages
- Show last updated timestamp
- Add "Live" toggle to enable/disable auto-refresh per user preference
- Implement WebSocket for real-time updates instead of polling

