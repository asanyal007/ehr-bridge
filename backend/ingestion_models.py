from __future__ import annotations

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


class ConnectorType(str, Enum):
    csv_file = "csv_file"
    hl7_tcp = "hl7_tcp"
    mongodb = "mongodb"
    fhir_api = "fhir_api"
    data_warehouse = "data_warehouse"
    json_api = "json_api"


@dataclass
class ConnectorConfigModel:
    connector_type: ConnectorType
    name: str
    config: Dict[str, Any]
    enabled: bool = True


@dataclass
class CreateConnectorRequest:
    connector_type: ConnectorType
    name: str
    config: Dict[str, Any]
    enabled: bool = True


@dataclass
class ConnectorConfigResponse:
    connector_id: str
    connector_type: ConnectorType
    name: str
    config: Dict[str, Any]
    enabled: bool


@dataclass
class CreateIngestionJobRequest:
    job_name: str
    source_connector_config: ConnectorConfigModel
    destination_connector_config: ConnectorConfigModel
    transformation_rules: List[Dict[str, Any]] = field(default_factory=list)
    schedule_config: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobControlRequest:
    action: str  # start | stop | pause | resume


@dataclass
class JobMetrics:
    received: int = 0
    processed: int = 0
    failed: int = 0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "received": self.received,
            "processed": self.processed,
            "failed": self.failed,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }


@dataclass
class JobStatusResponse:
    job_id: str
    job_name: str
    status: str
    source_connector: ConnectorConfigResponse
    destination_connector: ConnectorConfigResponse
    metrics: JobMetrics


@dataclass
class FHIRStoreSettings:
    enabled: bool = True
    database: str = "ehr"
    mode: str = "per_resource"  # reserved for future


@dataclass
class JobListResponse:
    jobs: List[JobStatusResponse]


@dataclass
class EngineStatsResponse:
    total_jobs: int
    running_jobs: int
    total_received: int
    total_processed: int
    total_failed: int


# Simple connector templates for UI scaffolding
CONNECTOR_TEMPLATES: Dict[ConnectorType, Dict[str, Any]] = {
    ConnectorType.csv_file: {
        "name": "CSV File",
        "description": "Read records from a local CSV file",
        "config_schema": {"file_path": "string", "delimiter": ","},
        "example_config": {"file_path": "/data/input.csv", "delimiter": ","},
    },
    ConnectorType.hl7_tcp: {
        "name": "HL7 TCP Listener",
        "description": "Listen to incoming HL7 v2 messages over TCP",
        "config_schema": {"host": "string", "port": "number"},
        "example_config": {"host": "0.0.0.0", "port": 2575},
    },
    ConnectorType.mongodb: {
        "name": "MongoDB",
        "description": "Write records to MongoDB collection",
        "config_schema": {"uri": "string", "database": "string", "collection": "string"},
        "example_config": {"uri": "mongodb://localhost:27017", "database": "ehr", "collection": "fhir"},
    },
    ConnectorType.fhir_api: {
        "name": "FHIR API",
        "description": "Write FHIR resources to a FHIR server",
        "config_schema": {"base_url": "string", "auth_token": "string"},
        "example_config": {"base_url": "http://localhost:8080/fhir", "auth_token": "TOKEN"},
    },
}
