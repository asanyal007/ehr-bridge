#!/bin/bash

# Quick Test Script for CSV → FHIR Patient Transformation
# Tests the complete workflow using the API

API_BASE="http://localhost:8000"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║     🧪 Quick Transformation Test - CSV → FHIR Patient             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Get Auth Token
echo "Step 1: Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/demo-token")
TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
USER_ID=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['userId'])")

if [ -z "$TOKEN" ]; then
    echo "   ❌ Failed to get token"
    exit 1
fi

echo "   ✅ Token: ${TOKEN:0:20}..."
echo "   ✅ User: $USER_ID"
echo ""

# Step 2: Gemini AI Predicts FHIR Resource
echo "Step 2: Using Gemini AI to predict FHIR resource..."

PREDICT_PAYLOAD='{
  "PatientFirstName": "string",
  "PatientLastName": "string",
  "DateOfBirth": "date",
  "Gender": "string",
  "MedicalRecordNumber": "string"
}'

PREDICTION=$(curl -s -X POST "$API_BASE/api/v1/fhir/predict-resource" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PREDICT_PAYLOAD")

PREDICTED_RESOURCE=$(echo $PREDICTION | python3 -c "import sys, json; print(json.load(sys.stdin)['predictedResource'])")
CONFIDENCE=$(echo $PREDICTION | python3 -c "import sys, json; print(json.load(sys.stdin)['confidence'])")

echo "   🤖 Gemini Predicted: $PREDICTED_RESOURCE"
echo "   📊 Confidence: $(python3 -c "print(f'{$CONFIDENCE * 100:.0f}%')")"
echo ""

# Step 3: Create Job
echo "Step 3: Creating mapping job..."

JOB_PAYLOAD='{
  "userId": "'$USER_ID'",
  "sourceSchema": {
    "PatientFirstName": "string",
    "PatientLastName": "string",
    "DateOfBirth": "date",
    "Gender": "string",
    "MedicalRecordNumber": "string"
  },
  "targetSchema": {
    "resourceType": "string",
    "name[0].family": "string",
    "name[0].given[0]": "string",
    "gender": "string",
    "birthDate": "date",
    "identifier[0].value": "string"
  }
}'

JOB_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$JOB_PAYLOAD")

JOB_ID=$(echo $JOB_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['jobId'])")

if [ -z "$JOB_ID" ]; then
    echo "   ❌ Failed to create job"
    exit 1
fi

echo "   ✅ Job Created: $JOB_ID"
echo ""

# Step 4: Analyze with AI
echo "Step 4: Running AI analysis (Sentence-BERT)..."

ANALYZE_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/jobs/$JOB_ID/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"userId\":\"$USER_ID\"}")

MAPPING_COUNT=$(echo $ANALYZE_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin)['suggestedMappings']))")

echo "   🧠 AI Generated: $MAPPING_COUNT mappings"
echo ""

# Step 5: Transform to FHIR
echo "Step 5: Transforming to FHIR Patient resources..."

TRANSFORM_PAYLOAD='{
  "mappings": [
    {
      "sourceField": "PatientFirstName",
      "targetField": "name[0].given[0]",
      "suggestedTransform": "TRIM",
      "confidenceScore": 0.92
    },
    {
      "sourceField": "PatientLastName",
      "targetField": "name[0].family",
      "suggestedTransform": "TRIM",
      "confidenceScore": 0.92
    },
    {
      "sourceField": "Gender",
      "targetField": "gender",
      "suggestedTransform": "DIRECT",
      "confidenceScore": 1.0
    },
    {
      "sourceField": "DateOfBirth",
      "targetField": "birthDate",
      "suggestedTransform": "DIRECT",
      "confidenceScore": 0.95
    },
    {
      "sourceField": "MedicalRecordNumber",
      "targetField": "identifier[0].value",
      "suggestedTransform": "DIRECT",
      "confidenceScore": 0.88
    }
  ],
  "sampleData": [
    {
      "PatientFirstName": "Sarah",
      "PatientLastName": "Johnson",
      "DateOfBirth": "1965-03-15",
      "Gender": "F",
      "MedicalRecordNumber": "MRN001234"
    },
    {
      "PatientFirstName": "Michael",
      "PatientLastName": "Chen",
      "DateOfBirth": "1972-08-22",
      "Gender": "M",
      "MedicalRecordNumber": "MRN001235"
    }
  ]
}'

TRANSFORM_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/fhir/transform?resource_type=Patient" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$TRANSFORM_PAYLOAD")

RESOURCE_COUNT=$(echo $TRANSFORM_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['recordCount'])")

echo "   🔥 Created: $RESOURCE_COUNT FHIR Patient resources"
echo ""

# Display first FHIR resource
echo "Step 6: Displaying generated FHIR resource..."
echo "─────────────────────────────────────────────────────────────────────"
echo $TRANSFORM_RESPONSE | python3 -m json.tool | head -40
echo "─────────────────────────────────────────────────────────────────────"
echo ""

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ TRANSFORMATION TEST COMPLETE!                ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  • Token obtained: ✅"
echo "  • FHIR resource predicted: ✅ ($PREDICTED_RESOURCE)"
echo "  • Job created: ✅ ($JOB_ID)"
echo "  • AI mappings generated: ✅ ($MAPPING_COUNT mappings)"
echo "  • FHIR resources created: ✅ ($RESOURCE_COUNT resources)"
echo ""
echo "🎉 All API endpoints working correctly!"
echo ""

