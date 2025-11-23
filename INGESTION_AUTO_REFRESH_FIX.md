# Ingestion Pipeline Auto-Refresh Fix

## Issue
The ingestion pipeline screen was getting stuck and showing a loading state indefinitely due to aggressive auto-refresh polling that was blocking the browser.

## Root Causes Identified

1. **Aggressive 2-second polling** (line 1730-1742): A useEffect was polling ingestion job status every 2 seconds for ANY running job, which could block the browser if:
   - API responses were slow
   - Multiple jobs were running simultaneously
   - The polling caused excessive re-renders

2. **Dependency array issue** (line 1651): The `fetchIngestionJobs` callback included `cancelTokenSource` in its dependencies, creating potential infinite loops since it updates the state it depends on.

3. **Stale closure references**: The cleanup function in useEffect was accessing `cancelTokenSource` from closure, but it wasn't in the dependency array, leading to stale references.

## Changes Made

### 1. Added Ref for Cancel Token (Line 75)
```javascript
const cancelTokenRef = useRef(null); // Use ref to avoid dependency issues
```
- Uses a ref to store cancel token source to avoid dependency issues
- Refs don't trigger re-renders when updated

### 2. Updated fetchIngestionJobs to Use Ref (Lines 1580-1651)
```javascript
// Cancel any existing request using ref
if (cancelTokenRef.current) {
  cancelTokenRef.current.cancel('New request started');
}

// Create new cancel token
const source = axios.CancelToken.source();
cancelTokenRef.current = source;
```
- Changed from state-based to ref-based cancel token management
- Removed `cancelTokenSource` from dependency array to prevent infinite loops

### 3. Reduced Polling Interval (Lines 1734-1749)
**Before**: 2 seconds (2000ms)
**After**: 10 seconds (10000ms)

```javascript
// Poll ingestion status every 10s when running (reduced from 2s to prevent browser blocking)
useEffect(() => {
  if (!ingestJobId || ingestStatus !== 'RUNNING') return;
  const iv = setInterval(async () => {
    try {
      const resp = await axios.get(`${API_BASE_URL}/api/v1/ingestion/jobs/${ingestJobId}`, { 
        headers: authHeaders,
        timeout: 5000 // 5 second timeout
      });
      // ... update status
    } catch (e) {
      console.log('Polling error (ignoring):', e.message);
    }
  }, 10000); // Changed from 2000ms to 10000ms
  return () => clearInterval(iv);
}, [ingestJobId, ingestStatus, token]);
```

### 4. Enhanced Manual Refresh Button (Lines 3507-3517)
```javascript
<p className="text-sm text-gray-600">
  Monitor and control all streaming ingestion pipelines. Click Refresh to update status.
</p>
<button 
  onClick={fetchIngestionJobs} 
  disabled={isIngestionListLoading}
  className="px-3 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
>
  🔄 Refresh
</button>
```
- Improved button styling with amber color for better visibility
- Added disabled state that prevents clicking while loading
- Updated helper text to inform users to use manual refresh

### 5. Fixed cancelLoading Function (Lines 1654-1669)
```javascript
const cancelLoading = useCallback(() => {
  console.log('🛑 User cancelled loading');
  
  // Cancel the actual request using the ref
  if (cancelTokenRef.current) {
    cancelTokenRef.current.cancel('User cancelled');
    cancelTokenRef.current = null;
  }
  
  setIsIngestionListLoading(false);
  setLoadingStartTime(null);
  setShowLoadingCancel(false);
  setCancelTokenSource(null);
  showToast('Loading cancelled', 'info');
}, [showToast]);
```
- Uses ref instead of state for cancel token access
- Cleaner dependency array with only `showToast`

### 6. Fixed useEffect Cleanup (Lines 1671-1685)
```javascript
useEffect(() => {
  if (currentView === 'ingestion' && token) {
    fetchIngestionJobs();
    // Auto-refresh removed - use manual refresh button instead
  }
  
  // Cleanup function to handle component unmount
  return () => {
    // Cancel any pending requests when component unmounts or view changes
    if (cancelTokenRef.current) {
      cancelTokenRef.current.cancel('Component unmounting or view changing');
      cancelTokenRef.current = null;
    }
    setCancelTokenSource(null);
  };
}, [currentView, token, fetchIngestionJobs]);
```
- Uses ref in cleanup to access current cancel token
- Prevents stale closure issues

## Benefits

1. **No more browser blocking**: Reduced polling from 2s to 10s dramatically reduces API calls
2. **No infinite loops**: Fixed dependency arrays prevent re-render loops
3. **Better UX**: Prominent manual refresh button gives users control
4. **Proper cleanup**: Using refs ensures cancel tokens are properly cleaned up
5. **Faster UI**: Less frequent polling means smoother user experience

## Testing Recommendations

1. Navigate to Ingestion Pipelines view
2. Verify the page loads without getting stuck
3. Click the "🔄 Refresh" button to manually update status
4. Start a job and verify it polls status every 10 seconds (not 2)
5. Switch views and verify no errors in console
6. Check that loading states work correctly

## Performance Impact

- **Before**: Up to 30 API calls per minute (every 2 seconds)
- **After**: 6 API calls per minute (every 10 seconds)
- **Reduction**: 80% fewer API calls, significantly reducing browser load

## Files Modified

- `frontend/src/App.jsx` - All changes in this single file

## Status

✅ **FIXED** - Auto-refresh disabled, manual refresh button enhanced, polling interval increased from 2s to 10s

