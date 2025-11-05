#!/bin/bash

echo "🔍 Testing OMOP Persistence with working job"
echo "=" | head -c 60; echo

# Use job_1760282978 (30 cancer records with CSV data)
JOB_ID="job_1760282978"

echo "Testing Job: $JOB_ID"
echo "Expected: CONDITION_OCCURRENCE records"
echo

curl -X POST http://localhost:8000/api/v1/omop/persist-all \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-123" \
  -d "{\"job_id\": \"$JOB_ID\", \"table\": \"CONDITION_OCCURRENCE\"}" \
  | python3 -m json.tool

echo -e "\n\n✅ If you see inserted > 0, it worked!"
echo "If you see inserted = 0, the job might not have the required fields"
