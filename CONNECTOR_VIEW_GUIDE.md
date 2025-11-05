# 📊 Data Connector & Pipeline Builder Guide

## Overview

The **Data Connector & Pipeline Builder** is a visual, drag-and-drop interface inspired by Azure Data Factory that allows you to configure data sources and targets for AI-powered mapping.

---

## 🆕 New UI Features

### 1. Visual Connector Selection
- **Palette of 6 connector types** displayed as clickable cards
- Each connector has an icon, name, and description
- Hover effects and visual feedback

### 2. Pipeline Canvas
- **Drag-and-drop inspired interface** (click to select for now)
- Visual representation of Source → Target flow
- Arrow showing AI mapping between connectors
- Real-time status updates

### 3. Configuration Modals
- Click on a connector to open configuration modal
- Paste JSON schema for that data source
- Context-sensitive examples for each connector type
- Save/Cancel options

### 4. Schema Extraction & Display
- Automatically displays detected schemas
- Side-by-side view of source and target
- JSON formatted with syntax highlighting
- Easy verification before generating mappings

---

## 🎨 Available Connectors

### Source Connectors

1. **📡 HL7 API**
   - Color: Blue
   - For: HL7 v2 message interfaces
   - Example Schema: `{"PID-5.1": "string", "PID-5.2": "string", "PID-7": "date"}`

2. **📄 CSV File**
   - Color: Green
   - For: Flat file data sources
   - Example Schema: `{"first_name": "string", "last_name": "string", "dob": "date"}`

3. **🍃 MongoDB**
   - Color: Emerald
   - For: Document databases
   - Example Schema: `{"patient.name.first": "string", "patient.name.last": "string"}`

### Target Connectors

4. **🏢 Data Warehouse**
   - Color: Purple
   - For: SQL databases, analytics platforms
   - Example Schema: `{"patient_name": "string", "birth_date": "datetime"}`

5. **🔥 FHIR API**
   - Color: Orange
   - For: FHIR servers
   - Example Schema: `{"Patient.name.family": "string", "Patient.birthDate": "date"}`

6. **🔌 JSON API**
   - Color: Cyan
   - For: REST APIs
   - Example Schema: `{"fullName": "string", "dateOfBirth": "datetime"}`

---

## 🚀 How to Use

### Step 1: Access the Connector View

1. Open http://localhost:3000
2. Click **"+ Create New Mapping Job"**
3. You'll see the **Data Connector & Pipeline Builder**

### Step 2: Configure Source

1. In the **Source** placeholder, click one of the quick-select buttons:
   - 📡 HL7 API
   - 📄 CSV File
   - 🍃 MongoDB

2. A modal will open for schema configuration

3. Paste your source schema in JSON format

4. Click **"Save Configuration"**

5. Source connector appears on the canvas

### Step 3: Configure Target

1. In the **Target** placeholder, click one of the quick-select buttons:
   - 🍃 MongoDB
   - 🏢 Data Warehouse
   - 🔥 FHIR API

2. Configuration modal opens

3. Paste your target schema

4. Click **"Save Configuration"**

5. Target connector appears on the canvas

### Step 4: Create Pipeline

1. Once both connectors are configured, **"🔗 Create Pipeline"** button appears

2. Click to create the mapping job

3. Job is created with DRAFT status

### Step 5: Generate AI Mappings

1. **"🧠 Generate Mappings (AI) →"** button appears

2. Click to trigger Sentence-BERT analysis

3. View switches to HITL Review with AI suggestions

### Step 6: Review & Approve

1. Review AI-generated mappings
2. Approve/reject each suggestion
3. Add manual mappings if needed
4. Finalize and approve

---

## 💡 Example Workflows

### Workflow 1: HL7 API → Data Warehouse

**Use Case**: Extract patient data from HL7 feeds for analytics

**Steps**:
1. Select **📡 HL7 API** as source
2. Configure with HL7 schema:
```json
{
  "PID-5.1": "string",
  "PID-5.2": "string",
  "PID-7": "date",
  "PID-18": "string"
}
```

3. Select **🏢 Data Warehouse** as target
4. Configure with columnar schema:
```json
{
  "last_name": "string",
  "first_name": "string",
  "birth_date": "datetime",
  "medical_record_number": "string"
}
```

5. Create pipeline
6. Generate AI mappings
7. Review suggestions:
   - PID-5.1 → last_name (95% confidence)
   - PID-5.2 → first_name (95% confidence)
   - PID-7 → birth_date (98% confidence, FORMAT_DATE)
   - PID-18 → medical_record_number (92% confidence)

---

### Workflow 2: CSV File → FHIR API

**Use Case**: Convert legacy CSV patient data to FHIR resources

**Steps**:
1. Select **📄 CSV File** as source
2. Configure schema:
```json
{
  "PatientLastName": "string",
  "PatientFirstName": "string",
  "DOB": "date",
  "EmailAddress": "string"
}
```

3. Select **🔥 FHIR API** as target
4. Configure FHIR schema:
```json
{
  "Patient.name.family": "string",
  "Patient.name.given": "string",
  "Patient.birthDate": "date",
  "Patient.telecom.value": "string"
}
```

5. AI generates semantic mappings
6. Transform CSV → FHIR JSON

---

### Workflow 3: MongoDB → HL7 API

**Use Case**: Send data warehouse records back as HL7 messages

**Steps**:
1. Select **🍃 MongoDB** as source
2. Configure document schema:
```json
{
  "patient.demographics.lastName": "string",
  "patient.demographics.firstName": "string",
  "patient.demographics.birthDate": "date"
}
```

3. Select **📡 HL7 API** as target
4. Configure HL7 structure:
```json
{
  "PID-5.1": "string",
  "PID-5.2": "string",
  "PID-7": "date"
}
```

5. AI suggests reverse transformation
6. Generate HL7 v2 messages

---

## 🎯 Visual Design Elements

### Pipeline Canvas
```
┌─────────────────────────────────────────────────────────────┐
│              Data Integration Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│     Source            AI Mapping           Target            │
│                                                              │
│   ┌─────────┐           →          ┌─────────┐            │
│   │   📡    │                       │   🏢    │            │
│   │ HL7 API │       Sentence-BERT  │   DW    │            │
│   │         │                       │         │            │
│   └─────────┘                       └─────────┘            │
│   ✓ Configured                      ✓ Configured           │
│                                                              │
└─────────────────────────────────────────────────────────────┘

     [🔗 Create Pipeline]  [🧠 Generate Mappings (AI) →]
```

### Connector Palette
```
┌──────────────────────────────────────────────────────────────┐
│ Available Connectors                                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐     │
│  │ 📡  │  │ 📄  │  │ 🍃  │  │ 🏢  │  │ 🔥  │  │ 🔌  │     │
│  │ HL7 │  │ CSV │  │Mongo│  │ DW  │  │FHIR │  │JSON │     │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Implementation

### State Management
```javascript
// Connector state
const [sourceConnector, setSourceConnector] = useState(null);
const [targetConnector, setTargetConnector] = useState(null);
const [showSourceModal, setShowSourceModal] = useState(false);
const [showTargetModal, setShowTargetModal] = useState(false);
```

### Connector Data Model
```javascript
{
  id: 'hl7_api',
  name: 'HL7 API',
  icon: '📡',
  color: 'blue',
  description: 'HL7 v2 Interface'
}
```

---

## 📱 Responsive Design

- **Desktop**: Full 3-column layout with modals
- **Tablet**: 2-column grid, stacked pipeline
- **Mobile**: Single column, full-width modals

---

## 🎨 Color Coding

| Connector Type | Color | Use Case |
|----------------|-------|----------|
| HL7 API | Blue | Hospital systems |
| CSV File | Green | Legacy data |
| MongoDB | Emerald | Document stores |
| Data Warehouse | Purple | Analytics |
| FHIR API | Orange | Modern EHR |
| JSON API | Cyan | Web services |

---

## ✨ Interactive Elements

1. **Connector Cards**
   - Hover: Border color changes, shadow appears
   - Click: Opens configuration modal

2. **Pipeline Canvas**
   - Dashed border when empty
   - Solid border with connectors
   - Visual connection line (arrow)

3. **Modals**
   - Full-screen overlay
   - Dismissible by clicking X or Cancel
   - Validation before saving

4. **Action Buttons**
   - Appear dynamically based on configuration state
   - Loading states with spinners
   - Disabled when not ready

---

## 🔄 Workflow

```
User Action             System Response             Next State
───────────────────────────────────────────────────────────────
Click "+ Create Job" → Show Connector View     → SELECT_SOURCE
Select Source        → Open Source Modal      → CONFIGURE_SOURCE
Save Source Config   → Close Modal, Show Icon → SELECT_TARGET
Select Target        → Open Target Modal      → CONFIGURE_TARGET
Save Target Config   → Close Modal, Show Icon → CREATE_PIPELINE
Click Create         → Create Job in DB        → GENERATE_MAPPINGS
Click Generate       → AI Analysis            → HITL_REVIEW
```

---

## 🎓 Best Practices

### For Clinical Data Engineers

1. **Start with Well-Known Schemas**
   - Use example schemas as templates
   - Validate JSON before saving

2. **Match Connector Types to Data**
   - HL7 API for hospital systems
   - CSV for flat files
   - Data Warehouse for analytics

3. **Review Schema Display**
   - Verify field names
   - Check data types
   - Ensure all fields visible

4. **Use Descriptive Job Names**
   - Name reflects source → target
   - Include date or version

---

## 📊 Benefits Over Text Input

| Feature | Old Text View | New Connector View |
|---------|---------------|-------------------|
| Visual Feedback | None | Icons, colors, arrows |
| Context | Generic | Connector-specific |
| Ease of Use | Manual typing | Click and configure |
| Understanding | Abstract | Concrete pipeline |
| Error Prevention | Easy to mix up | Clear source/target |

---

## 🔍 Future Enhancements

- Actual drag-and-drop from palette
- Multiple source/target connectors
- Transform nodes in middle
- Visual mapping lines
- Real-time schema validation
- Auto-save draft configurations

---

## 🚀 Try It Now!

1. Open http://localhost:3000
2. Click **"+ Create New Mapping Job"**
3. See the new **Connector & Pipeline Builder**
4. Click connectors to configure
5. Generate AI mappings
6. Review and approve!

---

## 📞 Support

- **Frontend Code**: `frontend/src/App.jsx` (lines 627-901)
- **Backend API**: http://localhost:8000/docs
- **Examples**: `examples/ehr_hl7_schemas.json`

---

## ✨ Summary

The **Data Connector & Pipeline Builder** provides:
- ✅ Visual connector selection (6 types)
- ✅ Interactive pipeline canvas
- ✅ Configuration modals with validation
- ✅ Schema display and verification
- ✅ Seamless integration with AI mapping
- ✅ Azure Data Factory-inspired UX

**Access**: http://localhost:3000 → Click "+ Create New Mapping Job"

---

*Feature Added: October 2024*  
*Version: 2.5+*  
*UI Pattern: Azure Data Factory Inspired*

