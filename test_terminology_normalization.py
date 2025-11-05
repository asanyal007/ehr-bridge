import json
import requests

API = 'http://localhost:8000'


def get_token():
    r = requests.post(f"{API}/api/v1/auth/demo-token")
    r.raise_for_status()
    return r.json()['token'], r.json()['userId']


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_gender_normalization_flow():
    token, user_id = get_token()

    # Create a simple job
    source_schema = {"Gender": "string", "PatientLastName": "string"}
    target_schema = {"Patient.gender": "code", "Patient.name[0].family": "string"}
    r = requests.post(
        f"{API}/api/v1/jobs",
        json={"sourceSchema": source_schema, "targetSchema": target_schema, "userId": user_id},
        headers=auth_headers(token),
    )
    r.raise_for_status()
    job = r.json()

    # Analyze
    r = requests.post(
        f"{API}/api/v1/jobs/{job['jobId']}/analyze",
        json={"userId": user_id},
        headers=auth_headers(token),
    )
    r.raise_for_status()
    analyzed = r.json()
    assert analyzed['status'] in ('PENDING_REVIEW', 'ANALYZING', 'DRAFT')

    # Normalize terminology with sample values (M, 1 -> male)
    sample = [{"Gender": "M"}, {"Gender": "1"}, {"Gender": "Female"}]
    r = requests.post(
        f"{API}/api/v1/terminology/normalize/{job['jobId']}",
        json={"sampleData": sample, "sampleSize": 10},
        headers=auth_headers(token),
    )
    r.raise_for_status()
    suggestions = r.json()['suggestions']
    assert isinstance(suggestions, list)

    # Save normalization choosing canonical male/female
    items = []
    for sug in suggestions:
        if 'gender' in sug['fieldPath'].lower():
            mapping = {}
            for cand in sug.get('candidates', []):
                sv = cand['sourceValue']
                norm = cand.get('normalized') or sv
                mapping[sv] = {"normalized": norm}
            items.append({
                "fieldPath": sug['fieldPath'],
                "strategy": "hybrid",
                "mapping": mapping,
                "approvedBy": user_id,
            })
    if items:
        r = requests.put(
            f"{API}/api/v1/terminology/{job['jobId']}",
            json={"items": items, "cacheAlso": True},
            headers=auth_headers(token),
        )
        r.raise_for_status()

    # Verify retrieval
    r = requests.get(f"{API}/api/v1/terminology/{job['jobId']}", headers=auth_headers(token))
    r.raise_for_status()
    saved = r.json()['normalizations']
    assert isinstance(saved, list)


