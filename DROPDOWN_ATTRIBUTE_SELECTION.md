# Dropdown Attribute Selection for Manual Mappings

## Overview

Enhanced the "Review AI Suggestions (HITL)" screen to allow users to select source and target fields from dropdown menus instead of typing them manually. This feature includes:

- **Searchable/filterable dropdowns** for both source and target fields
- **Hybrid input** allowing users to select from available fields or type custom values
- **FHIR nested path support** for complex target schemas (e.g., `Patient.name[0].family`)
- **Transform dropdown** for AI-suggested mappings
- **Validation** to ensure both source and target fields are provided before approval

## Changes Made

### 1. Frontend State Management (`frontend/src/App.jsx`)

**Added new state variables** (lines 38-40):
```javascript
// Dropdown options for manual mappings
const [sourceFieldOptions, setSourceFieldOptions] = useState([]);
const [targetFieldOptions, setTargetFieldOptions] = useState([]);
```

**Added useRef import** (line 1):
```javascript
import React, { useState, useEffect, useRef } from 'react';
```

### 2. Helper Functions

**extractFhirPaths function** (lines 634-661):
- Detects if a schema is FHIR-based (contains nested paths like `Patient.name[0].family`)
- Extracts all field paths from the schema
- Returns sorted list of available fields

**validateManualMapping function** (lines 774-782):
- Validates that both source and target fields are provided
- Returns validation result with error message if invalid

### 3. Updated editJob Function (lines 1344-1373)

When a job is loaded for editing:
- Extracts source field names from `job.sourceSchema`
- Extracts target field paths using `extractFhirPaths()` for FHIR schemas
- Populates dropdown options for manual mapping

### 4. SearchableDropdown Component (lines 1660-1742)

A reusable hybrid dropdown component with:
- **Search/filter functionality**: Type to filter available options
- **Click-to-select**: Click an option from the dropdown list
- **Custom value support**: Type any value not in the list
- **Outside click detection**: Closes dropdown when clicking outside
- **Visual feedback**: Shows "No matches found" message with custom value preview

### 5. Updated Manual Mapping UI (lines 2861-2897)

**Source Field** (lines 2865-2878):
- Replaced text input with `SearchableDropdown`
- Populated with `sourceFieldOptions`
- Placeholder: "Select or type source field"

**Target Field** (lines 2884-2897):
- Replaced text input with `SearchableDropdown`
- Populated with `targetFieldOptions`
- Placeholder: "Select or type target field (e.g., Patient.name[0].family)"

### 6. Transform Dropdown for AI Suggestions (lines 2904-2922)

- Added dropdown for AI-suggested mappings (not manual)
- Options: DIRECT, CONCAT, SPLIT, UPPERCASE, LOWERCASE, DATE_FORMAT, CUSTOM
- Manual mappings show transform as read-only text

### 7. Enhanced Validation (lines 787-798)

Updated `approveMappings` function to:
- Validate all manual mappings before approval
- Show alert with specific error message if validation fails
- Prevent approval if any manual mapping is incomplete

## User Experience Improvements

### Before
- Users had to manually type field names
- Risk of typos and errors
- No visibility into available fields
- No guidance for FHIR nested paths

### After
- Users can select from available fields via dropdown
- Type to filter and find fields quickly
- See all available options at a glance
- FHIR paths are properly formatted and visible
- Still flexible to enter custom values when needed
- Validation prevents incomplete mappings

## Usage Flow

1. **Create/Edit Mapping Job**: Load a job with source and target schemas
2. **Review AI Suggestions**: Navigate to the HITL review screen
3. **Add Manual Mapping**: Click "+ Add Manual Mapping"
4. **Select Source Field**:
   - Click the source field input
   - Dropdown shows all available source columns
   - Type to filter options
   - Click to select or type custom value
5. **Select Target Field**:
   - Click the target field input
   - Dropdown shows all available target paths (including FHIR nested paths)
   - Type to filter options
   - Click to select or type custom value
6. **Modify Transform** (for AI suggestions):
   - Use dropdown to change transform type
   - Options include DIRECT, CONCAT, SPLIT, etc.
7. **Approve Mapping**: Click "Approve" button
8. **Validation**: System validates that both fields are provided

## Technical Details

### Dropdown Behavior

- **Open on focus**: Dropdown opens when input is clicked
- **Filter on type**: Options are filtered as user types
- **Select on click**: Clicking an option populates the field and closes dropdown
- **Custom values**: Any typed value is accepted (hybrid mode)
- **Close on outside click**: Dropdown closes when clicking elsewhere
- **Visual feedback**: Shows filtered results or "no matches" message

### FHIR Path Extraction

The `extractFhirPaths` function:
1. Checks if schema contains FHIR-like patterns (dots, brackets)
2. If FHIR: Extracts nested paths like `Patient.name[0].family`
3. If CSV/regular: Extracts simple column names
4. Returns sorted list for consistent display

### Validation Logic

The `validateManualMapping` function:
1. Checks if `sourceField` is provided
2. Checks if `targetField` is provided
3. Returns `{ valid: false, message: '...' }` if either is missing
4. Returns `{ valid: true }` if both are present

## Testing Checklist

- [x] Load a job with CSV source schema and FHIR target schema
- [x] Click "+ Add Manual Mapping"
- [x] Verify source field dropdown shows CSV column names
- [x] Verify target field dropdown shows FHIR paths
- [x] Test typing to filter dropdown options
- [x] Test entering custom field name not in dropdown
- [x] Test transform dropdown for AI-suggested mappings
- [x] Verify validation prevents empty source/target fields
- [x] No linter errors

## Benefits

1. **Reduced Errors**: Selecting from available fields prevents typos
2. **Better Discovery**: Users can see all available fields
3. **FHIR Support**: Proper handling of nested FHIR paths
4. **Flexibility**: Still allows custom values when needed
5. **Better UX**: Searchable, filterable dropdowns improve usability
6. **Validation**: Ensures data quality before approval
7. **Transform Control**: Users can modify transform types for AI suggestions

## Files Modified

- `frontend/src/App.jsx`: Added dropdown components, updated manual mapping UI, added validation

## Next Steps

This feature is complete and ready for testing. Future enhancements could include:

1. **Autocomplete suggestions**: Show recently used field names
2. **Field type indicators**: Show data types next to field names
3. **Smart matching**: Suggest likely target fields based on source field name
4. **Bulk operations**: Apply same transform to multiple mappings
5. **Field preview**: Show sample values when hovering over field names

