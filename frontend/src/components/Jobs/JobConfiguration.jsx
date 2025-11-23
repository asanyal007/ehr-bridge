import React, { useState } from 'react';
import Card, { CardBody, CardFooter, CardHeader } from '../Common/Card';
import Button from '../Common/Button';
import { components } from '../../designSystem';

const JobConfiguration = ({ onCreateJob, onCancel, loading, error }) => {
    const [sourceType, setSourceType] = useState('json');
    const [sourceContent, setSourceContent] = useState('');
    const [sourceSchema, setSourceSchema] = useState('');
    const [targetSchema, setTargetSchema] = useState('');
    const [activeTab, setActiveTab] = useState('source'); // 'source', 'target'

    // Handlers for schema generation
    const generateSchemaFromCSV = (csvContent) => {
        try {
            const headers = csvContent.split('\n')[0].split(',');
            const schema = {};
            headers.forEach(h => {
                schema[h.trim()] = "string";
            });
            setSourceSchema(JSON.stringify(schema, null, 2));
        } catch (e) {
            console.error("Failed to parse CSV", e);
        }
    };

    const handleSourceTypeChange = (type) => {
        setSourceType(type);
        setSourceContent('');
        setSourceSchema('');
        if (type === 'ehr') {
            setSourceSchema(JSON.stringify({
                "patient_id": "VARCHAR(50)",
                "encounter_id": "VARCHAR(50)",
                "diagnosis_code": "VARCHAR(10)",
                "admit_date": "DATETIME"
            }, null, 2));
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onCreateJob(sourceSchema, targetSchema);
    };

    const handleSampleLoad = () => {
        setSourceType('json');
        const sampleSource = {
            "patient_id": "12345",
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1980-01-01",
            "gender": "M"
        };
        const sampleTarget = {
            "resourceType": "Patient",
            "id": "example",
            "name": [
                {
                    "family": "Doe",
                    "given": ["John"]
                }
            ],
            "birthDate": "1980-01-01",
            "gender": "male"
        };

        setSourceSchema(JSON.stringify(sampleSource, null, 2));
        setTargetSchema(JSON.stringify(sampleTarget, null, 2));
    };

    return (
        <div className="max-w-5xl mx-auto">
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900">Configure Data Mapping</h2>
                <p className="text-gray-500">Define your source data structure and target FHIR resource.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Configuration Steps */}
                <div className="lg:col-span-2 space-y-6">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-gray-900">1. Source Configuration</h3>
                                <div className="flex space-x-2">
                                    {['json', 'csv', 'api', 'ehr'].map(type => (
                                        <button
                                            key={type}
                                            onClick={() => handleSourceTypeChange(type)}
                                            className={`px-3 py-1 text-xs font-medium rounded-full uppercase tracking-wider transition-colors ${sourceType === type
                                                    ? 'bg-primary-100 text-primary-700 border border-primary-200'
                                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                                }`}
                                        >
                                            {type}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </CardHeader>
                        <CardBody>
                            <div className="space-y-4">
                                {sourceType === 'csv' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Paste CSV Header / Sample Row
                                        </label>
                                        <textarea
                                            className={components.textarea}
                                            placeholder="id,first_name,last_name,dob,gender"
                                            rows={3}
                                            value={sourceContent}
                                            onChange={(e) => {
                                                setSourceContent(e.target.value);
                                                generateSchemaFromCSV(e.target.value);
                                            }}
                                        />
                                        <p className="text-xs text-gray-500 mt-1">We'll automatically infer the schema from your headers.</p>
                                    </div>
                                )}

                                {sourceType === 'api' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            API Endpoint URL
                                        </label>
                                        <input
                                            type="text"
                                            className={components.input}
                                            placeholder="https://api.hospital-system.org/v1/patients"
                                        />
                                        <div className="mt-4">
                                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                                Sample Response JSON
                                            </label>
                                            <textarea
                                                className={components.textarea}
                                                rows={5}
                                                placeholder='{"id": "123", "name": "John"}'
                                                onChange={(e) => setSourceSchema(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                )}

                                {sourceType === 'ehr' && (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">System Type</label>
                                            <select className={components.input}>
                                                <option>Epic Clarity</option>
                                                <option>Cerner Millennium</option>
                                                <option>Allscripts</option>
                                                <option>PostgreSQL / SQL Server</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-2">Table Name</label>
                                            <input type="text" className={components.input} placeholder="PATIENT_DIM" />
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Generated Source Schema
                                    </label>
                                    <textarea
                                        value={sourceSchema}
                                        onChange={(e) => setSourceSchema(e.target.value)}
                                        className={`${components.textarea} font-mono text-xs bg-gray-50`}
                                        rows={8}
                                        placeholder='{"field": "type", ...}'
                                    />
                                </div>
                            </div>
                        </CardBody>
                    </Card>

                    <Card>
                        <CardHeader>
                            <h3 className="text-lg font-semibold text-gray-900">2. Target Configuration (FHIR)</h3>
                        </CardHeader>
                        <CardBody>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Target FHIR Resource Schema
                                </label>
                                <textarea
                                    value={targetSchema}
                                    onChange={(e) => setTargetSchema(e.target.value)}
                                    className={`${components.textarea} font-mono text-xs`}
                                    rows={10}
                                    placeholder='{"resourceType": "Patient", ...}'
                                />
                                <div className="flex gap-2 mt-2">
                                    <button
                                        type="button"
                                        onClick={() => setTargetSchema(JSON.stringify({
                                            "resourceType": "Patient",
                                            "id": "example",
                                            "name": [{ "family": "", "given": [] }],
                                            "gender": "",
                                            "birthDate": ""
                                        }, null, 2))}
                                        className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                                    >
                                        Load Patient Template
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setTargetSchema(JSON.stringify({
                                            "resourceType": "Observation",
                                            "status": "final",
                                            "code": { "coding": [{ "system": "http://loinc.org", "code": "" }] },
                                            "valueQuantity": { "value": 0, "unit": "" }
                                        }, null, 2))}
                                        className="text-xs text-primary-600 hover:text-primary-800 font-medium"
                                    >
                                        Load Observation Template
                                    </button>
                                </div>
                            </div>
                        </CardBody>
                    </Card>
                </div>

                {/* Right Column: Summary & Actions */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <h3 className="text-lg font-semibold text-gray-900">Job Summary</h3>
                        </CardHeader>
                        <CardBody>
                            <div className="space-y-4 text-sm">
                                <div className="flex justify-between py-2 border-b border-gray-100">
                                    <span className="text-gray-500">Source Type</span>
                                    <span className="font-medium uppercase">{sourceType}</span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-gray-100">
                                    <span className="text-gray-500">Target Standard</span>
                                    <span className="font-medium text-primary-600">FHIR R4</span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-gray-100">
                                    <span className="text-gray-500">AI Model</span>
                                    <span className="font-medium">Gemini Pro + SBERT</span>
                                </div>
                            </div>

                            {error && (
                                <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-xs">
                                    {error}
                                </div>
                            )}
                        </CardBody>
                        <CardFooter className="flex flex-col space-y-3">
                            <Button
                                variant="primary"
                                onClick={handleSubmit}
                                isLoading={loading}
                                disabled={!sourceSchema || !targetSchema}
                                className="w-full justify-center"
                            >
                                Create Mapping Job
                            </Button>
                            <Button variant="secondary" onClick={onCancel} className="w-full justify-center">
                                Cancel
                            </Button>
                            <Button variant="ghost" size="sm" onClick={handleSampleLoad} className="w-full">
                                Load Full Example
                            </Button>
                        </CardFooter>
                    </Card>

                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                        <div className="flex items-start space-x-3">
                            <span className="text-2xl">💡</span>
                            <div>
                                <h4 className="text-sm font-semibold text-blue-900">AI Assistant</h4>
                                <p className="text-xs text-blue-700 mt-1">
                                    I will analyze your source schema and automatically suggest mappings to the target FHIR resource using semantic similarity.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default JobConfiguration;
