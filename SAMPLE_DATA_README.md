# Sample Healthcare Data Files

## Overview

Three CSV files with 20 records each, designed for testing FHIR to OMOP data transformation pipelines.

## Files Created

### 1. `sample_data_person.csv` (20 patients)

**Purpose:** Patient demographic and administrative data

**Columns:**
- `patient_id` - Unique patient identifier (P001-P020)
- `first_name`, `last_name` - Patient name
- `gender` - male/female
- `birth_date` - Date of birth (YYYY-MM-DD format)
- `mrn` - Medical Record Number
- `race` - White, Black, Asian, Hispanic
- `ethnicity` - Hispanic/Not Hispanic
- `zip_code` - 5-digit ZIP code
- `state` - Two-letter state code
- `phone` - Contact phone number
- `email` - Contact email
- `insurance_type` - Medicare, Medicaid, Private
- `primary_care_provider` - Assigned PCP name

**OMOP Mapping:**
- Target Table: `PERSON`
- Key Fields:
  - `patient_id` → `person_source_value`
  - `birth_date` → `year_of_birth`, `month_of_birth`, `day_of_birth`
  - `gender` → `gender_concept_id` (8507=MALE, 8532=FEMALE)
  - `race` → `race_concept_id`
  - `ethnicity` → `ethnicity_concept_id`

**Test Coverage:**
- 11 males, 9 females
- Multiple races and ethnicities
- Ages from 28 to 48 years old
- Diverse geographic locations (10 states)
- Mix of insurance types

---

### 2. `sample_data_conditions.csv` (20 diagnoses)

**Purpose:** Clinical condition/diagnosis data

**Columns:**
- `patient_id` - Links to person data
- `mrn` - Medical Record Number
- `first_name`, `last_name` - Patient name (for reference)
- `condition_id` - Unique condition identifier
- `diagnosis_date` - Date of diagnosis
- `diagnosis_code` - ICD-10-CM code
- `diagnosis_system` - Code system (ICD10CM)
- `diagnosis_description` - Human-readable condition name
- `onset_date` - When condition started
- `abatement_date` - When condition resolved (if applicable)
- `severity` - mild, moderate, severe
- `clinical_status` - active, resolved
- `verification_status` - confirmed
- `encounter_id` - Associated encounter
- `provider_name` - Diagnosing provider
- `department` - Clinical department

**OMOP Mapping:**
- Target Table: `CONDITION_OCCURRENCE`
- Key Fields:
  - `diagnosis_code` → `condition_source_value`
  - `diagnosis_code` → `condition_concept_id` (via semantic mapping)
  - `diagnosis_date` → `condition_start_date`
  - `abatement_date` → `condition_end_date`

**Clinical Conditions Included:**
1. Type 2 Diabetes (E11.9)
2. Essential Hypertension (I10)
3. Asthma (J45.909)
4. Panniculitis (M79.3)
5. Major Depressive Disorder (F32.9)
6. Hyperlipidemia (E78.5)
7. GERD (K21.9)
8. Chronic Kidney Disease Stage 3 (N18.3)
9. Atherosclerotic Heart Disease (I25.10)
10. Rheumatoid Arthritis (M06.9)
11. Obesity (E66.9)
12. Migraine (G43.909)
13. Psoriasis (L40.9)
14. Anxiety Disorder (F41.9)
15. Osteoporosis (M81.0)
16. Iron Deficiency Anemia (D50.9)
17. Peripheral Vascular Disease (I73.9)
18. Hypothyroidism (E03.9)
19. COPD (J44.9)
20. Urinary Tract Infection (N39.0)

**Test Coverage:**
- Mix of chronic and acute conditions
- Various clinical specialties (Cardiology, Endocrinology, Psychiatry, etc.)
- Different severity levels
- Some resolved conditions (2 with abatement dates)

---

### 3. `sample_data_labs.csv` (20 lab results)

**Purpose:** Laboratory test results and measurements

**Columns:**
- `patient_id` - Links to person data
- `mrn` - Medical Record Number
- `first_name`, `last_name` - Patient name (for reference)
- `lab_order_id` - Unique lab order identifier
- `specimen_date` - When specimen was collected
- `result_date` - When result was reported
- `lab_code` - LOINC code
- `lab_system` - Code system (LOINC)
- `lab_name` - Human-readable test name
- `result_value` - Numeric result
- `result_unit` - Unit of measurement
- `reference_range` - Normal range
- `interpretation` - Normal, High, Low
- `status` - final
- `provider_name` - Ordering provider
- `department` - Laboratory

**OMOP Mapping:**
- Target Table: `MEASUREMENT`
- Key Fields:
  - `lab_code` → `measurement_source_value`
  - `lab_code` → `measurement_concept_id` (via semantic mapping)
  - `result_value` → `value_as_number`
  - `result_unit` → `unit_concept_id`
  - `specimen_date` → `measurement_date`
  - `interpretation` → `value_source_value`

**Lab Tests Included:**
1. Glucose (2339-0)
2. Cholesterol (2093-3)
3. Hemoglobin (718-7)
4. Blood Urea Nitrogen (3094-0)
5. Creatinine (2160-0)
6. TSH - Thyroid Stimulating Hormone (3016-3)
7. Hemoglobin A1c (4548-4)
8. Sodium (2951-2)
9. Potassium (2823-3)
10. ALT - Alanine Aminotransferase (1742-6)
11. AST - Aspartate Aminotransferase (1920-8)
12. Total Bilirubin (1975-2)
13. Total Protein (2885-2)
14. Calcium (17861-6)
15. Alkaline Phosphatase (6768-6)
16. Platelets (777-3)
17. White Blood Cells (6690-2)
18. Microalbumin Urine (14959-1)
19. Triglycerides (2571-8)
20. eGFR - Estimated Glomerular Filtration Rate (33914-3)

**Test Coverage:**
- Common chemistry panel tests (glucose, creatinine, electrolytes)
- Lipid panel (cholesterol, triglycerides)
- Liver function tests (ALT, AST, bilirubin)
- Complete blood count components (hemoglobin, platelets, WBC)
- Specialty tests (HbA1c, TSH, eGFR)
- Mix of normal and abnormal results (3 high results)

---

## Usage Instructions

### For FHIR Ingestion Testing

1. **Upload Person Data:**
   ```bash
   # Create mapping job for person data
   # Target FHIR Resource: Patient
   # Map fields: patient_id → id, first_name → name.given, etc.
   ```

2. **Upload Condition Data:**
   ```bash
   # Create mapping job for conditions
   # Target FHIR Resource: Condition
   # Map fields: diagnosis_code → code.coding[0].code, etc.
   ```

3. **Upload Lab Data:**
   ```bash
   # Create mapping job for labs
   # Target FHIR Resource: Observation
   # Map fields: lab_code → code.coding[0].code, result_value → value, etc.
   ```

### For OMOP Testing

Each file can test different OMOP transformation scenarios:

**Person → OMOP PERSON:**
- Test deterministic `person_id` generation
- Test gender concept mapping (8507=Male, 8532=Female)
- Test birth date decomposition

**Conditions → OMOP CONDITION_OCCURRENCE:**
- Test ICD-10-CM to OMOP concept mapping
- Test semantic normalization (AI matching)
- Test date handling (start/end dates)
- Test condition status tracking

**Labs → OMOP MEASUREMENT:**
- Test LOINC to OMOP concept mapping
- Test numeric value handling
- Test unit concept mapping
- Test result interpretation (Normal/High/Low)

### Testing Workflow

```
1. Create Mapping Jobs (3 separate jobs, one per file)
   ├─ sample_data_person.csv → Patient FHIR resource
   ├─ sample_data_conditions.csv → Condition FHIR resource
   └─ sample_data_labs.csv → Observation FHIR resource

2. Create Ingestion Jobs (from each mapping)
   ├─ Data flows to MongoDB staging/FHIR collections
   └─ Check "View Records" to verify 20 records per job

3. OMOP Data Model Transformation
   ├─ Predict Table → Should detect correct OMOP table
   ├─ Normalize Concepts → AI maps codes to OMOP concepts
   ├─ Review Concepts → Approve/override AI suggestions
   ├─ Preview → Verify OMOP row structure
   └─ Persist → Write to omop_PERSON, omop_CONDITION_OCCURRENCE, omop_MEASUREMENT

4. Verify Results
   ├─ OMOP Tables viewer → Check persisted data
   └─ Expected: 20 PERSON, 20 CONDITION_OCCURRENCE, 20 MEASUREMENT rows
```

---

## Data Quality Notes

### Realistic Clinical Data
- All ICD-10-CM codes are valid and clinically appropriate
- All LOINC codes are standard laboratory test codes
- Reference ranges match real-world clinical standards
- Patient demographics are diverse and representative

### Data Relationships
- Each condition and lab result links to a patient via `patient_id`
- MRNs are consistent across all three files
- Dates follow logical chronology (specimen dates before result dates)

### Edge Cases Covered
- **Resolved conditions**: 2 conditions have `abatement_date` (temporary conditions)
- **Abnormal results**: 3 lab results are flagged as "High"
- **Missing data**: Birth dates without abatement dates (ongoing conditions)
- **Clinical diversity**: 12 different clinical specialties represented

---

## Expected OMOP Concept Mappings

### High-Confidence Mappings (should auto-approve)
- **Gender**: Male → 8507, Female → 8532 (100% confidence)
- **Common LOINC codes**: Glucose, Cholesterol, Hemoglobin (>95% confidence)
- **Common ICD-10**: Diabetes (E11.9), Hypertension (I10) (>90% confidence)

### Medium-Confidence Mappings (may require review)
- **Less common conditions**: Panniculitis, Psoriasis (70-85% confidence)
- **Specialty labs**: Microalbumin, eGFR (75-85% confidence)

### Expected Review Queue
- Approximately 2-4 concepts requiring human review (confidence <70%)
- User should be able to select from top 3 AI suggestions
- System should learn from approved mappings for future use

---

## File Locations

```
/Users/aritrasanyal/EHR_Test/
├── sample_data_person.csv       (20 patients)
├── sample_data_conditions.csv   (20 diagnoses)
└── sample_data_labs.csv         (20 lab results)
```

---

## Testing Checklist

### Person Data
- [ ] All 20 patients ingested successfully
- [ ] FHIR Patient resources created with proper structure
- [ ] Gender mapped to OMOP concepts (8507/8532)
- [ ] Birth dates decomposed into year/month/day
- [ ] `person_id` generated deterministically
- [ ] 20 rows persisted to `omop_PERSON`

### Condition Data
- [ ] All 20 conditions ingested successfully
- [ ] FHIR Condition resources created
- [ ] ICD-10-CM codes mapped to OMOP `condition_concept_id`
- [ ] Date ranges handled correctly (start/end)
- [ ] 20 rows persisted to `omop_CONDITION_OCCURRENCE`

### Lab Data
- [ ] All 20 lab results ingested successfully
- [ ] FHIR Observation resources created
- [ ] LOINC codes mapped to OMOP `measurement_concept_id`
- [ ] Numeric values and units preserved
- [ ] 20 rows persisted to `omop_MEASUREMENT`

### AI Semantic Matching
- [ ] High-confidence mappings auto-approved (>90%)
- [ ] Low-confidence mappings queued for review (<70%)
- [ ] Review interface shows top 3 suggestions with reasoning
- [ ] User can approve/override AI suggestions
- [ ] Approved mappings cached for future use

---

## Quick Start Commands

### Upload and Test Person Data
```bash
# Via UI:
# 1. Go to "+ Create New Mapping Job"
# 2. Upload sample_data_person.csv
# 3. Target: Patient FHIR resource
# 4. Map fields, approve
# 5. Create ingestion job
# 6. Click "Data Model" → OMOP → Persist
```

### Direct API Test (if backend running)
```bash
# Upload via API
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_data_person.csv" \
  -F "target_resource=Patient"
```

---

## Support

For issues or questions:
- Check `INGESTION_TEST_GUIDE.md` for troubleshooting
- Review `OMOP_PERSISTENCE_FIX.md` for OMOP transformation details
- See `END_TO_END_FLOW_TEST.md` for complete workflow

**Last Updated:** October 22, 2025  
**Data Version:** 1.0  
**Total Records:** 60 (20 per file)

