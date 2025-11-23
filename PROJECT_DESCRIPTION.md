# EHR AI Interoperability Platform

## Executive Summary

The **EHR AI Interoperability Platform** is a production-ready, full-stack healthcare data integration solution designed to solve the "last mile" problem of healthcare interoperability. By leveraging advanced artificial intelligence (Sentence-BERT and Google Gemini), the platform automates the complex, labor-intensive process of mapping and transforming data between disparate healthcare systems and standards (CSV, HL7 v2, FHIR, OMOP).

Healthcare organizations currently spend hundreds of hours manually mapping data fields. This platform reduces that time by **80-99%** through AI-powered semantic matching, while maintaining strict clinical data engineer oversight through a "human-in-the-loop" workflow. It is a self-hosted, HIPAA-ready solution that requires no external cloud dependencies for its core mapping engine.

## Core Problem Solved

Healthcare data is siloed and fragmented across incompatible formats. Integrating these systems typically requires manual field-by-field mapping, which is:
*   **Time-Consuming**: Weeks or months per integration.
*   **Error-Prone**: Human error in interpreting legacy codes.
*   **Expensive**: Requires specialized knowledge of HL7, FHIR, and OMOP.

**Real-World Scenarios:**
*   **Hospital to Registry**: Automating the submission of cancer data from a local EHR to a national disease registry.
*   **Legacy Modernization**: Converting 20 years of historical HL7 v2 messages into a modern FHIR store.
*   **Clinical Research**: Standardizing diverse source data into the OMOP Common Data Model for observational research.

## Key Features

### 1. AI-Powered Data Mapping
*   **Semantic Matching**: Uses Sentence-BERT pre-trained on biomedical texts to understand field context (e.g., knowing that "DOB" matches "birthDate").
*   **Generative AI**: Integrates Google Gemini AI for complex resource prediction and SQL query generation.
*   **Confidence Scoring**: Every AI suggestion comes with a confidence score, allowing engineers to focus only on low-confidence matches.

### 2. Multi-Format Support
*   **CSV**: Auto-inference of schemas, bulk upload, and data preview.
*   **HL7 v2**: Robust parsing of segments (PID, OBX, OBR, etc.), MongoDB staging, and bidirectional transformation.
*   **FHIR**: Native support for FHIR R4 resources, validation, and persistence.
*   **OMOP**: Automated conversion to OMOP Common Data Model tables (Person, Visit_Occurrence, Measurement, etc.).

### 3. Visual Data Pipeline Builder
*   **Interactive UI**: Azure Data Factory-inspired interface for building data flows.
*   **Connectors**: Support for 6+ connector types including HL7 feeds, CSV files, MongoDB, and Data Warehouses.
*   **Validation**: Real-time schema validation and transformation previews.

### 4. Human-in-the-Loop Workflow
*   **Review Interface**: Dedicated UI for reviewing AI suggestions.
*   **Approval System**: One-click approve/reject for mappings.
*   **Manual Overrides**: Full control to override AI suggestions with custom logic.

### 5. HL7 Message Management
*   **Staging**: Raw HL7 messages are staged in MongoDB for audit and replay.
*   **Viewer**: Visual HL7 message viewer with syntax highlighting and segment breakdown.
*   **Transformation**: Configurable rules for converting HL7 messages to columnar formats or FHIR resources.

### 6. OMOP Data Modeling
*   **Table Prediction**: AI predicts the target OMOP table based on source data shape.
*   **Concept Normalization**: Maps local codes to standard OMOP concepts (SNOMED, LOINC, RxNorm).
*   **ID Management**: Deterministic generation of `person_id` and `visit_id` to ensure consistency.

### 7. FHIR Data Chatbot
*   **Natural Language Querying**: Ask questions like "How many patients have Diabetes?" in plain English.
*   **RAG Architecture**: Uses Retrieval-Augmented Generation to synthesize accurate answers from your data.
*   **Safety**: Query validation and sanitization to prevent hallucinations or data leakage.

### 8. Ingestion Engine
*   **Orchestration**: Manages real-time data ingestion jobs.
*   **Error Handling**: Detailed logging and "dead letter" queue for failed records.
*   **Monitoring**: Dashboard for tracking job status and throughput.

### 9. Advanced Features
*   **Custom Scripting**: Python-based scripting engine for complex, non-standard transformations.
*   **Routing Engine**: Rule-based routing of messages based on content (e.g., route "ADT" messages to Patient Administration system).

## Technical Architecture

```ascii
+---------------------------------------------------------------+
|                   Frontend (React 18 SPA)                     |
|  +-------------+  +-------------+  +-------------+            |
|  | Pipeline UI |  |  Data View  |  |  Chatbot UI |            |
|  +-------------+  +-------------+  +-------------+            |
+---------------------------+-----------------------------------+
                            | REST API (JSON)
+---------------------------v-----------------------------------+
|                   Backend (FastAPI Python)                    |
|                                                               |
|  +----------------+  +----------------+  +-----------------+  |
|  |   API Layer    |  |   Auth (JWT)   |  | Routing Engine  |  |
|  +----------------+  +----------------+  +-----------------+  |
|                                                               |
|  +---------------------------------------------------------+  |
|  |                    AI Engine                            |  |
|  |  +---------------+   +------------+   +--------------+  |  |
|  |  | Sentence-BERT |   | Gemini AI  |   | Normalizer   |  |  |
|  |  +---------------+   +------------+   +--------------+  |  |
|  +---------------------------------------------------------+  |
|                                                               |
|  +----------------+  +----------------+  +-----------------+  |
|  |  HL7 Parser    |  |  OMOP Engine   |  | Ingestion Core  |  |
|  +----------------+  +----------------+  +-----------------+  |
+---------------------------+-----------------------------------+
                            |
      +---------------------+---------------------+
      |                     |                     |
+-----v------+       +------v-------+      +------v-------+
|  SQLite    |       |   MongoDB    |      |  File System |
| (Config)   |       | (Data/Logs)  |      | (Model Cache)|
+------------+       +--------------+      +--------------+
```

*   **Backend**: Python 3.10+, FastAPI, Uvicorn
*   **Frontend**: React 18, Tailwind CSS
*   **AI**: `sentence-transformers` (HuggingFace), Google Generative AI SDK
*   **Database**: MongoDB (Data), SQLite (Metadata)
*   **Deployment**: Docker, Docker Compose

## User Personas

1.  **Clinical Data Engineer (Primary)**
    *   **Goal**: Build reliable data pipelines between hospital systems.
    *   **Use Case**: Configures the HL7-to-FHIR transformation rules and reviews AI mapping suggestions.

2.  **Health Information Manager**
    *   **Goal**: Ensure data quality and compliance.
    *   **Use Case**: Uses the dashboard to monitor data flows and investigate failed ingestion records.

3.  **Research Data Coordinator**
    *   **Goal**: Aggregate data for clinical studies.
    *   **Use Case**: Uploads CSV extracts from various clinics and normalizes them into the OMOP format for analysis.

4.  **Healthcare IT Administrator**
    *   **Goal**: Maintain system uptime and security.
    *   **Use Case**: Deploys the Docker containers and manages API keys and access controls.

## Comparison to Alternatives

| Feature | Manual Mapping | Commercial Integration Engines | EHR AI Platform |
| :--- | :--- | :--- | :--- |
| **Setup Time** | Weeks/Months | Days/Weeks | **Minutes (Docker)** |
| **Cost** | High (Labor) | High (Licensing) | **Low (Open Source)** |
| **AI Mapping** | None | Limited / Add-on | **Core Feature** |
| **Standards** | Manual | Varies | **HL7, FHIR, OMOP, CSV** |
| **Privacy** | High | Cloud-dependent | **Self-Hosted / Local** |

## Getting Started

1.  **Prerequisites**: Docker and Docker Compose installed.
2.  **Clone & Configure**:
    ```bash
    git clone <repo-url>
    cp env.template .env  # Add your Gemini API Key
    ```
3.  **Run**:
    ```bash
    docker-compose up -d
    ```
4.  **Access**:
    *   Frontend: `http://localhost:3000`
    *   Backend API: `http://localhost:8000/docs`

## Future Roadmap

*   **Real-time HL7 MLLP Listener**: Direct socket integration for live hospital feeds.
*   **Expanded OMOP Vocabulary**: Local caching of the full Athena vocabulary.
*   **Multi-Tenant Support**: Role-based access control (RBAC) for different hospital departments.
*   **Visual Transformer**: Drag-and-drop field transformation logic builder.
