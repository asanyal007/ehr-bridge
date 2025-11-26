"""
MongoDB Client for HL7 Message Staging
Handles temporary storage of raw HL7 messages before processing
"""
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from bson import ObjectId


class MongoDBClient:
    """Client for HL7 message staging in MongoDB"""
    
    def __init__(self, connection_string: str = None):
        """
        Initialize MongoDB client
        
        Args:
            connection_string: MongoDB connection string
        """
        if connection_string is None:
            # Default to local containerized MongoDB
            mongo_host = os.getenv("MONGO_HOST", "localhost")
            mongo_port = os.getenv("MONGO_PORT", "27017")
            connection_string = f"mongodb://{mongo_host}:{mongo_port}/"
        
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            print(f"[OK] MongoDB connected: {connection_string}")
        except ConnectionFailure as e:
            print(f"[WARN] MongoDB connection failed: {e}")
            print("   Platform will work without HL7 staging capability")
            self.client = None
        
        if self.client:
            self.db = self.client.ehr_interop
            self.hl7_staging = self.db.hl7_staging
            self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        if self.client:
            # Index on jobId for quick lookups
            self.hl7_staging.create_index([("jobId", ASCENDING)])
            # Index on ingestionTimestamp for sorting
            self.hl7_staging.create_index([("ingestionTimestamp", DESCENDING)])
            # Index on messageId for unique lookups
            self.hl7_staging.create_index([("messageId", ASCENDING)], unique=True)
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        return self.client is not None
    
    def stage_hl7_message(
        self,
        message_id: str,
        job_id: str,
        raw_message: str,
        message_type: str = "HL7_V2",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Stage a raw HL7 message in MongoDB
        
        Args:
            message_id: Unique message identifier
            job_id: Associated job ID
            raw_message: Raw HL7 message content
            message_type: Type of message (HL7_V2, HL7_V3, etc.)
            metadata: Additional metadata
            
        Returns:
            MongoDB ObjectId as string
        """
        if not self.is_connected():
            raise Exception("MongoDB not connected")
        
        document = {
            "messageId": message_id,
            "jobId": job_id,
            "rawMessage": raw_message,
            "messageType": message_type,
            "ingestionTimestamp": datetime.utcnow(),
            "processed": False,
            "metadata": metadata or {}
        }
        
        result = self.hl7_staging.insert_one(document)
        return str(result.inserted_id)
    
    def get_staged_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a staged HL7 message by ID
        
        Args:
            message_id: Message identifier
            
        Returns:
            Message document or None
        """
        if not self.is_connected():
            return None
        
        doc = self.hl7_staging.find_one({"messageId": message_id})
        if doc:
            doc['_id'] = str(doc['_id'])
        return doc
    
    def get_messages_by_job(self, job_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all staged messages for a job
        
        Args:
            job_id: Job identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message documents
        """
        if not self.is_connected():
            return []
        
        cursor = self.hl7_staging.find(
            {"jobId": job_id}
        ).sort("ingestionTimestamp", DESCENDING).limit(limit)
        
        messages = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            messages.append(doc)
        
        return messages
    
    def mark_message_processed(self, message_id: str) -> bool:
        """
        Mark a message as processed
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            return False
        
        result = self.hl7_staging.update_one(
            {"messageId": message_id},
            {
                "$set": {
                    "processed": True,
                    "processedTimestamp": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def delete_staged_message(self, message_id: str) -> bool:
        """
        Delete a staged message
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if successful
        """
        if not self.is_connected():
            return False
        
        result = self.hl7_staging.delete_one({"messageId": message_id})
        return result.deleted_count > 0
    
    def delete_job_messages(self, job_id: str) -> int:
        """
        Delete all messages for a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Number of deleted messages
        """
        if not self.is_connected():
            return 0
        
        result = self.hl7_staging.delete_many({"jobId": job_id})
        return result.deleted_count
    
    def get_staging_stats(self) -> Dict[str, Any]:
        """
        Get statistics about staged messages
        
        Returns:
            Statistics dictionary
        """
        if not self.is_connected():
            return {
                "connected": False,
                "total_messages": 0,
                "unprocessed_messages": 0
            }
        
        total = self.hl7_staging.count_documents({})
        unprocessed = self.hl7_staging.count_documents({"processed": False})
        
        return {
            "connected": True,
            "total_messages": total,
            "unprocessed_messages": unprocessed,
            "processed_messages": total - unprocessed
        }
    
    def parse_hl7_message(self, raw_message: str) -> Dict[str, Any]:
        """
        Parse HL7 v2 message into structured format
        
        Args:
            raw_message: Raw HL7 message
            
        Returns:
            Parsed message structure
        """
        lines = raw_message.strip().split('\n')
        segments = {}
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split('|')
            if len(parts) < 1:
                continue
            
            segment_type = parts[0]
            
            if segment_type not in segments:
                segments[segment_type] = []
            
            # Store segment with field values
            segment_data = {
                'raw': line,
                'fields': parts[1:] if len(parts) > 1 else []
            }
            
            segments[segment_type].append(segment_data)
        
        return {
            'segments': segments,
            'segment_count': len(segments),
            'raw': raw_message
        }


# Global MongoDB client instance
mongo_client = None

def get_mongo_client(connection_string: str = None) -> MongoDBClient:
    """Get or create MongoDB client singleton"""
    global mongo_client
    if mongo_client is None:
        mongo_client = MongoDBClient(connection_string)
    return mongo_client

