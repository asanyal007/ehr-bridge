#!/usr/bin/env python3
"""
Generate and store S-BERT embeddings for OMOP concepts.

This script pre-computes embeddings for all OMOP standard concepts to enable
fast semantic similarity search during concept matching.

Usage:
    python generate_concept_embeddings.py [--vocabulary LOINC] [--domain Condition] [--limit 1000]
"""

import argparse
import sys
import os
import numpy as np
from typing import List, Dict, Any
from tqdm import tqdm

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omop_vocab import get_vocab_service
from database import get_db_manager


def generate_embeddings(
    vocabulary_id: str = None,
    domain_id: str = None,
    limit: int = 10000,
    batch_size: int = 100
):
    """
    Generate and store S-BERT embeddings for OMOP concepts
    
    Args:
        vocabulary_id: Filter by vocabulary (LOINC, SNOMED, etc.)
        domain_id: Filter by domain (Condition, Measurement, etc.)
        limit: Maximum number of concepts to process
        batch_size: Batch size for processing
    """
    print("🚀 Starting OMOP concept embedding generation...")
    
    # Get services
    vocab_service = get_vocab_service()
    db_manager = get_db_manager()
    
    # Get concepts to process
    print(f"📊 Fetching concepts (vocab={vocabulary_id}, domain={domain_id}, limit={limit})...")
    concepts = vocab_service.get_all_standard_concepts(
        vocabulary_id=vocabulary_id,
        domain_id=domain_id,
        limit=limit
    )
    
    if not concepts:
        print("❌ No concepts found to process")
        return
    
    print(f"✅ Found {len(concepts)} concepts to process")
    
    # Check existing embeddings
    existing_embeddings = vocab_service.get_embeddings(
        vocabulary_id=vocabulary_id,
        domain_id=domain_id,
        limit=100000
    )
    existing_ids = {e['concept_id'] for e in existing_embeddings}
    
    # Filter out already processed concepts
    concepts_to_process = [c for c in concepts if c['concept_id'] not in existing_ids]
    
    if not concepts_to_process:
        print("✅ All concepts already have embeddings")
        return
    
    print(f"📝 Processing {len(concepts_to_process)} new concepts...")
    
    # Process in batches
    processed = 0
    errors = 0
    
    for i in tqdm(range(0, len(concepts_to_process), batch_size), desc="Generating embeddings"):
        batch = concepts_to_process[i:i + batch_size]
        
        for concept in batch:
            try:
                # Generate embedding (simulated for now)
                # In production, this would use actual S-BERT model
                embedding = _generate_concept_embedding(concept)
                
                # Store embedding
                vocab_service.store_embedding(
                    concept_id=concept['concept_id'],
                    concept_name=concept['concept_name'],
                    vocabulary_id=concept['vocabulary_id'],
                    domain_id=concept['domain_id'],
                    embedding=embedding,
                    standard_concept=concept['standard_concept']
                )
                
                processed += 1
                
            except Exception as e:
                print(f"⚠️ Error processing concept {concept['concept_id']}: {e}")
                errors += 1
                continue
    
    print(f"✅ Embedding generation complete!")
    print(f"   📊 Processed: {processed}")
    print(f"   ❌ Errors: {errors}")
    print(f"   📈 Total embeddings: {len(existing_embeddings) + processed}")


def _generate_concept_embedding(concept: Dict[str, Any]) -> np.ndarray:
    """
    Generate embedding for a concept (simulated)
    
    In production, this would use a pre-trained S-BERT model:
    
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('clinicalbert-base-uncased')
    embedding = model.encode(concept['concept_name'])
    
    Args:
        concept: Concept dictionary
    
    Returns:
        Numpy array embedding
    """
    # For now, generate a random embedding as placeholder
    # In production, use actual S-BERT model
    concept_text = f"{concept['concept_name']} {concept.get('concept_code', '')}"
    
    # Simulate embedding generation with hash-based approach
    import hashlib
    hash_obj = hashlib.md5(concept_text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert to numpy array (simulate 384-dimensional embedding)
    embedding = np.frombuffer(hash_bytes * 24, dtype=np.float32)[:384]
    
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding


def verify_embeddings(
    vocabulary_id: str = None,
    domain_id: str = None,
    sample_size: int = 10
):
    """
    Verify that embeddings were generated correctly
    
    Args:
        vocabulary_id: Filter by vocabulary
        domain_id: Filter by domain
        sample_size: Number of samples to check
    """
    print("🔍 Verifying embeddings...")
    
    vocab_service = get_vocab_service()
    embeddings = vocab_service.get_embeddings(
        vocabulary_id=vocabulary_id,
        domain_id=domain_id,
        limit=sample_size
    )
    
    if not embeddings:
        print("❌ No embeddings found")
        return
    
    print(f"✅ Found {len(embeddings)} embeddings")
    
    # Check a few samples
    for i, embedding in enumerate(embeddings[:sample_size]):
        try:
            # Deserialize embedding
            import pickle
            embedding_array = pickle.loads(embedding['embedding'])
            
            print(f"   📊 Concept {embedding['concept_id']}: {embedding['concept_name']}")
            print(f"      📏 Embedding shape: {embedding_array.shape}")
            print(f"      📈 Norm: {np.linalg.norm(embedding_array):.4f}")
            
        except Exception as e:
            print(f"   ❌ Error verifying embedding {embedding['concept_id']}: {e}")
    
    print("✅ Embedding verification complete!")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate OMOP concept embeddings")
    parser.add_argument("--vocabulary", help="Vocabulary ID (LOINC, SNOMED, etc.)")
    parser.add_argument("--domain", help="Domain ID (Condition, Measurement, etc.)")
    parser.add_argument("--limit", type=int, default=10000, help="Maximum concepts to process")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--verify", action="store_true", help="Verify embeddings after generation")
    
    args = parser.parse_args()
    
    try:
        # Generate embeddings
        generate_embeddings(
            vocabulary_id=args.vocabulary,
            domain_id=args.domain,
            limit=args.limit,
            batch_size=args.batch_size
        )
        
        # Verify if requested
        if args.verify:
            verify_embeddings(
                vocabulary_id=args.vocabulary,
                domain_id=args.domain
            )
        
    except KeyboardInterrupt:
        print("\n⏹️ Generation interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
