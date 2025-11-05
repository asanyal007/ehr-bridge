# FHIR Data Chatbot - Example Queries

## Overview
The FHIR Data Chatbot provides a natural language interface for querying FHIR clinical data stored in MongoDB. It uses Google Gemini AI to translate questions into MongoDB queries, retrieve data, and synthesize human-readable answers.

## Example Queries by Category

### 1. Patient Counts and Demographics

**Basic Count**
```
How many patients do we have?
```
Expected: Total count of Patient resources

**Gender Filtering**
```
How many male patients are there?
Show me female patients
Count patients by gender
```
Expected: Filtered count or list of patients by gender

**Age/Birth Date Filtering**
```
Show me patients born after 1990
List patients older than 50
How many pediatric patients do we have?
```
Expected: Patients filtered by birth date ranges

**Geographic Filtering**
```
Show me patients from Boston
List all patients in Massachusetts
How many patients are from New York?
```
Expected: Patients filtered by address city/state

**Name/ID Search**
```
Find patient with ID P12345
Show me patients with last name Smith
```
Expected: Specific patient records

### 2. Observations and Clinical Data

**Observation Counts**
```
How many observations do we have?
Show me all lab results
```
Expected: Total count of Observation resources

**Vital Signs**
```
Show me blood pressure readings
What are the glucose levels?
List cholesterol observations
```
Expected: Observations filtered by code/display

**Value Ranges**
```
Show me high blood pressure readings
Find observations with values over 200
List abnormal lab results
```
Expected: Observations filtered by valueQuantity

**Time-Based Queries**
```
Show me observations from this month
List lab results from 2024
What observations were recorded yesterday?
```
Expected: Observations filtered by effectiveDateTime

**Patient-Specific Observations**
```
Show observations for patient P12345
What lab results does Jane Smith have?
```
Expected: Observations linked to specific patient via subject reference

### 3. Conditions and Diagnoses

**Condition Listing**
```
What conditions are in the database?
Show me all diagnoses
```
Expected: List of Condition resources

**Specific Conditions**
```
Show me diabetes patients
List patients with hypertension
How many cancer diagnoses do we have?
```
Expected: Conditions filtered by code/display

**Active vs Historical**
```
Show me active conditions
List resolved diagnoses
```
Expected: Conditions filtered by clinicalStatus

**Patient-Specific Conditions**
```
What conditions does patient P12345 have?
Show me John Doe's diagnoses
```
Expected: Conditions for specific patient

### 4. Medications

**Medication Requests**
```
What medications are prescribed?
Show me all prescriptions
```
Expected: List of MedicationRequest resources

**Specific Medications**
```
Show me insulin prescriptions
List patients on metformin
How many antibiotic prescriptions?
```
Expected: MedicationRequests filtered by medication code

**Recent Prescriptions**
```
Show medications prescribed this year
List recent prescriptions
```
Expected: MedicationRequests filtered by authoredOn date

### 5. Cross-Resource Queries

**Patient + Observations**
```
Show me male patients with cholesterol readings
List patients from Boston with lab results
```
Expected: Combined filtering across Patient and Observation

**Complex Analytics**
```
How many patients have more than 5 observations?
What's the average age of diabetes patients?
Show me patients with both hypertension and diabetes
```
Expected: Aggregated or computed results

### 6. Troubleshooting Queries

**Empty Results**
```
Show me patients from Antarctica
Find observations from 1800
```
Expected: "I couldn't find any matching records..."

**Broad Queries**
```
Tell me about the data
What information do we have?
```
Expected: Summary of available resource types and counts

## Query Tips

### Best Practices
1. **Be Specific**: "Show me male patients" is better than "patients"
2. **Use Medical Terms**: The AI understands clinical terminology (ICD codes, LOINC, SNOMED)
3. **Specify Filters**: Include gender, dates, locations for more precise results
4. **Follow-Up Questions**: The chatbot maintains conversation context

### What the Chatbot Can Do
- Count resources (patients, observations, conditions, medications)
- Filter by demographics (gender, birth date, location)
- Search by clinical codes and terms
- Filter by date ranges
- Link across resources (e.g., patient → observations)

### What the Chatbot Cannot Do (Yet)
- Modify or delete data
- Create new FHIR resources
- Complex statistical analysis (mean, median, standard deviation)
- Join more than 2 resource types in one query

## Technical Details

### Query Translation Process
1. Your natural language question
2. → Gemini AI translates to MongoDB query
3. → Query executes against `fhir_*` collections
4. → Raw FHIR results
5. → Gemini AI synthesizes human-readable answer

### Query Structure
Behind the scenes, queries are translated to:
```json
{
  "resourceType": "Patient",
  "filter": {"gender": "male"},
  "limit": 100
}
```

### Conversation Context
The chatbot remembers the last 3 exchanges in a conversation, allowing:
```
You: "Show me patients from Boston"
Bot: [Lists patients]
You: "How many of them are female?"
Bot: [Applies filter to previous context]
```

## Example Conversation Flow

```
User: How many patients do we have?
Bot: There are 24 Patient records in the database.

User: How many are male?
Bot: There are 13 male patients.

User: Show me their names
Bot: Here are the male patients:
     - John Smith
     - Michael Johnson
     - ...
     (Showing summary of 13 records)

User: Do any of them have diabetes?
Bot: I found 3 male patients with diabetes diagnoses.
```

## Getting Started

1. **Navigate to Chatbot**: Click "💬 FHIR Chatbot" in the sidebar under "AI TOOLS"
2. **Start Simple**: Try "How many patients do we have?"
3. **Refine Queries**: Add filters like gender, location, dates
4. **Explore**: Use the example queries above as starting points
5. **Experiment**: The AI is flexible and understands many phrasings

## Feedback and Limitations

### Known Limitations
- Results limited to 100 records per query (for performance)
- Complex multi-resource joins may not work perfectly
- Date parsing depends on consistent FHIR date formats
- Nested field queries (e.g., `name[0].given[1]`) may be challenging

### Providing Feedback
If a query doesn't work as expected:
1. Try rephrasing more explicitly
2. Break complex queries into simpler steps
3. Use the "View Query" details to see what MongoDB query was generated
4. Report issues to the development team with specific examples

## Advanced Usage

### Viewing Generated Queries
Click "View Query" in any assistant response to see the MongoDB query that was generated. This helps you understand:
- How your question was interpreted
- What filters were applied
- Why you got certain results

### Clearing Context
Click the "🗑️ Clear" button to start a fresh conversation and reset context.

### Technical Users
If you're familiar with MongoDB queries, you can use the generated queries as a learning tool to understand FHIR data structure and improve your questions.

