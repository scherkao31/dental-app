import os
import json
import glob
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any, Tuple
import hashlib
from datetime import datetime

class EnhancedDentalRAG:
    def __init__(self, 
                 chroma_db_path: str = "./chroma_db",
                 model_name: str = "all-MiniLM-L6-v2",
                 cases_collection: str = "dental_cases",
                 knowledge_collection: str = "dental_knowledge"):
        
        self.chroma_db_path = chroma_db_path
        self.model_name = model_name
        self.cases_collection_name = cases_collection
        self.knowledge_collection_name = knowledge_collection
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=Settings(allow_reset=True)
        )
        
        # Initialize sentence transformer
        self.encoder = SentenceTransformer(model_name)
        
        # Initialize collections
        self.cases_collection = self._get_or_create_collection(self.cases_collection_name)
        self.knowledge_collection = self._get_or_create_collection(self.knowledge_collection_name)
        
        # Track indexed content
        self.cases_index_file = os.path.join(chroma_db_path, "cases_index.json")
        self.knowledge_index_file = os.path.join(chroma_db_path, "knowledge_index.json")
        
        print(f"✅ Enhanced Dental RAG initialized")
        print(f"   - Cases collection: {self.cases_collection_name}")
        print(f"   - Knowledge collection: {self.knowledge_collection_name}")
        print(f"   - Embedding model: {self.model_name}")
    
    def _get_or_create_collection(self, collection_name: str):
        """Get or create a ChromaDB collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            print(f"📚 Found existing collection: {collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"🆕 Created new collection: {collection_name}")
        return collection
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file"""
        if not os.path.exists(file_path):
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _load_index_state(self, index_file: str) -> Dict:
        """Load the indexing state from file"""
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading index state: {e}")
        return {}
    
    def _save_index_state(self, index_file: str, state: Dict):
        """Save the indexing state to file"""
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving index state: {e}")
    
    def index_treatment_cases(self, cases_directory: str = "DATA/TRAITEMENTS_JSON") -> int:
        """Index treatment cases from JSON files"""
        if not os.path.exists(cases_directory):
            print(f"❌ Cases directory not found: {cases_directory}")
            return 0
        
        # Load current index state
        index_state = self._load_index_state(self.cases_index_file)
        
        indexed_count = 0
        updated_files = []
        
        # Process each JSON file
        for filename in os.listdir(cases_directory):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(cases_directory, filename)
            file_hash = self._calculate_file_hash(file_path)
            
            # Check if file has changed
            if filename in index_state and index_state[filename].get('hash') == file_hash:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                
                # Extract and index case information
                case_id = f"case_{filename.replace('.json', '')}"
                
                # Create comprehensive text for embedding
                case_text = self._extract_case_text(case_data)
                
                # Generate embedding
                embedding = self.encoder.encode(case_text).tolist()
                
                # Prepare metadata
                metadata = {
                    "source": "treatment_case",
                    "filename": filename,
                    "case_id": case_id,
                    "consultation": case_data.get("consultation_text", ""),
                    "treatments_count": len(case_data.get("treatment_sequence", [])),
                    "indexed_at": datetime.now().isoformat()
                }
                
                # Add to collection (upsert)
                self.cases_collection.upsert(
                    ids=[case_id],
                    embeddings=[embedding],
                    documents=[case_text],
                    metadatas=[metadata]
                )
                
                # Update index state
                index_state[filename] = {
                    "hash": file_hash,
                    "indexed_at": datetime.now().isoformat(),
                    "case_id": case_id
                }
                
                indexed_count += 1
                updated_files.append(filename)
                
            except Exception as e:
                print(f"❌ Error indexing {filename}: {e}")
        
        # Save updated index state
        self._save_index_state(self.cases_index_file, index_state)
        
        if updated_files:
            print(f"📚 Indexed {indexed_count} treatment cases:")
            for filename in updated_files:
                print(f"   - {filename}")
        else:
            print("✅ All treatment cases are up to date")
        
        return indexed_count
    
    def index_dental_knowledge(self, knowledge_directory: str = "DATA/DENTAL_KNOWLEDGE") -> int:
        """Index dental knowledge from JSON files"""
        if not os.path.exists(knowledge_directory):
            print(f"❌ Knowledge directory not found: {knowledge_directory}")
            return 0
        
        # Load current index state
        index_state = self._load_index_state(self.knowledge_index_file)
        
        indexed_count = 0
        updated_files = []
        
        # Process each JSON file
        for filename in os.listdir(knowledge_directory):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(knowledge_directory, filename)
            file_hash = self._calculate_file_hash(file_path)
            
            # Check if file has changed
            if filename in index_state and index_state[filename].get('hash') == file_hash:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                # Process different types of knowledge
                file_indexed_count = self._index_knowledge_content(knowledge_data, filename)
                
                # Update index state
                index_state[filename] = {
                    "hash": file_hash,
                    "indexed_at": datetime.now().isoformat(),
                    "items_count": file_indexed_count
                }
                
                indexed_count += file_indexed_count
                updated_files.append(f"{filename} ({file_indexed_count} items)")
                
            except Exception as e:
                print(f"❌ Error indexing knowledge {filename}: {e}")
        
        # Save updated index state
        self._save_index_state(self.knowledge_index_file, index_state)
        
        if updated_files:
            print(f"🧠 Indexed {indexed_count} knowledge items:")
            for filename in updated_files:
                print(f"   - {filename}")
        else:
            print("✅ All dental knowledge is up to date")
        
        return indexed_count
    
    def index_specialized_knowledge(self, specialized_directory: str = "DATA/specialized_knowledge") -> int:
        """Index specialized knowledge from text files in subdirectories"""
        if not os.path.exists(specialized_directory):
            print(f"❌ Specialized knowledge directory not found: {specialized_directory}")
            return 0
        
        # Load current index state
        specialized_index_file = os.path.join(self.chroma_db_path, "specialized_index.json")
        index_state = self._load_index_state(specialized_index_file)
        
        indexed_count = 0
        updated_files = []
        
        # Process each subdirectory
        for category in os.listdir(specialized_directory):
            category_path = os.path.join(specialized_directory, category)
            if not os.path.isdir(category_path):
                continue
                
            # Process each text file in the category
            for filename in os.listdir(category_path):
                if not filename.endswith('.txt'):
                    continue
                    
                file_path = os.path.join(category_path, filename)
                file_key = f"{category}/{filename}"
                file_hash = self._calculate_file_hash(file_path)
                
                # Check if file has changed
                if file_key in index_state and index_state[file_key].get('hash') == file_hash:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Create knowledge ID
                    knowledge_id = f"specialized_{category}_{filename.replace('.txt', '')}"
                    
                    # Generate embedding
                    embedding = self.encoder.encode(content).tolist()
                    
                    # Prepare metadata
                    metadata = {
                        "source": "specialized_knowledge",
                        "type": "specialized",
                        "category": category,
                        "filename": filename,
                        "title": filename.replace('.txt', '').replace('_', ' ').title(),
                        "indexed_at": datetime.now().isoformat()
                    }
                    
                    # Add to knowledge collection
                    self.knowledge_collection.upsert(
                        ids=[knowledge_id],
                        embeddings=[embedding],
                        documents=[content],
                        metadatas=[metadata]
                    )
                    
                    # Update index state
                    index_state[file_key] = {
                        "hash": file_hash,
                        "indexed_at": datetime.now().isoformat(),
                        "knowledge_id": knowledge_id
                    }
                    
                    indexed_count += 1
                    updated_files.append(f"{category}/{filename}")
                    
                except Exception as e:
                    print(f"❌ Error indexing specialized knowledge {file_key}: {e}")
        
        # Save updated index state
        self._save_index_state(specialized_index_file, index_state)
        
        if updated_files:
            print(f"🧠 Indexed {indexed_count} specialized knowledge items:")
            for file_key in updated_files:
                print(f"   - {file_key}")
        else:
            print("✅ All specialized knowledge is up to date")
        
        return indexed_count
    
    def _index_knowledge_content(self, knowledge_data: Dict, filename: str) -> int:
        """Index individual knowledge items from a knowledge file"""
        indexed_count = 0
        
        # Process dental principles
        if "dental_principles" in knowledge_data:
            for principle_key, principle_data in knowledge_data["dental_principles"].items():
                indexed_count += self._index_principle_section(principle_key, principle_data, filename)
        
        # Process clinical guidelines
        if "clinical_guidelines" in knowledge_data:
            for guideline_key, guideline_data in knowledge_data["clinical_guidelines"].items():
                indexed_count += self._index_guideline_section(guideline_key, guideline_data, filename)
        
        # Process clinical protocols
        if "clinical_protocols" in knowledge_data:
            for protocol_key, protocol_data in knowledge_data["clinical_protocols"].items():
                indexed_count += self._index_protocol_section(protocol_key, protocol_data, filename)
        
        # Process emergency procedures
        if "emergency_procedures" in knowledge_data:
            for emergency_key, emergency_data in knowledge_data["emergency_procedures"].items():
                indexed_count += self._index_emergency_section(emergency_key, emergency_data, filename)
        
        # Process contraindications
        if "contraindications" in knowledge_data:
            for contra_key, contra_data in knowledge_data["contraindications"].items():
                indexed_count += self._index_contraindication_section(contra_key, contra_data, filename)
        
        # Process evidence-based recommendations
        if "evidence_based_recommendations" in knowledge_data:
            for evidence_key, evidence_data in knowledge_data["evidence_based_recommendations"].items():
                indexed_count += self._index_evidence_section(evidence_key, evidence_data, filename)
        
        return indexed_count
    
    def _index_principle_section(self, principle_key: str, principle_data: Dict, filename: str) -> int:
        """Index a dental principle section"""
        if "principles" not in principle_data:
            return 0
        
        indexed_count = 0
        for i, principle in enumerate(principle_data["principles"]):
            knowledge_id = f"principle_{principle_key}_{i}"
            
            # Create text for embedding
            text_parts = [
                f"Category: {principle_data.get('category', '')}",
                f"Title: {principle_data.get('title', '')}",
                f"Condition: {principle.get('condition', '')}",
                f"Recommendation: {principle.get('recommendation', '')}",
                f"Duration: {principle.get('duration', '')}",
                f"Rationale: {principle.get('rationale', '')}"
            ]
            knowledge_text = " | ".join(filter(None, text_parts))
            
            # Generate embedding
            embedding = self.encoder.encode(knowledge_text).tolist()
            
            # Prepare metadata
            metadata = {
                "source": "dental_knowledge",
                "type": "principle",
                "filename": filename,
                "category": principle_data.get("category", ""),
                "title": principle_data.get("title", ""),
                "condition": principle.get("condition", ""),
                "recommendation": principle.get("recommendation", ""),
                "indexed_at": datetime.now().isoformat()
            }
            
            # Add to collection
            self.knowledge_collection.upsert(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[metadata]
            )
            
            indexed_count += 1
        
        return indexed_count
    
    def _index_guideline_section(self, guideline_key: str, guideline_data: Dict, filename: str) -> int:
        """Index a clinical guideline section"""
        if "guidelines" not in guideline_data:
            return 0
        
        indexed_count = 0
        for i, guideline in enumerate(guideline_data["guidelines"]):
            knowledge_id = f"guideline_{guideline_key}_{i}"
            
            # Create text for embedding
            text_parts = [
                f"Category: {guideline_data.get('category', '')}",
                f"Title: {guideline_data.get('title', '')}",
                f"Procedure: {guideline.get('procedure', '')}",
                f"Duration: {guideline.get('duration', '')}",
                f"Frequency: {guideline.get('frequency', '')}",
                f"Notes: {guideline.get('notes', '')}"
            ]
            knowledge_text = " | ".join(filter(None, text_parts))
            
            # Generate embedding and store
            embedding = self.encoder.encode(knowledge_text).tolist()
            
            metadata = {
                "source": "dental_knowledge",
                "type": "guideline",
                "filename": filename,
                "category": guideline_data.get("category", ""),
                "title": guideline_data.get("title", ""),
                "procedure": guideline.get("procedure", ""),
                "indexed_at": datetime.now().isoformat()
            }
            
            self.knowledge_collection.upsert(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[metadata]
            )
            
            indexed_count += 1
        
        return indexed_count
    
    def _index_protocol_section(self, protocol_key: str, protocol_data: Dict, filename: str) -> int:
        """Index a clinical protocol section"""
        if "steps" not in protocol_data:
            return 0
        
        # Index the complete protocol as one item
        knowledge_id = f"protocol_{protocol_key}"
        
        # Create comprehensive text
        text_parts = [
            f"Category: {protocol_data.get('category', '')}",
            f"Title: {protocol_data.get('title', '')}",
            "Steps:"
        ]
        
        for step in protocol_data["steps"]:
            step_text = f"Step {step.get('step', '')}: {step.get('action', '')} - {step.get('details', '')} (Time: {step.get('time', '')}) Critical: {', '.join(step.get('critical_points', []))}"
            text_parts.append(step_text)
        
        knowledge_text = " | ".join(text_parts)
        
        # Generate embedding and store
        embedding = self.encoder.encode(knowledge_text).tolist()
        
        metadata = {
            "source": "dental_knowledge",
            "type": "protocol",
            "filename": filename,
            "category": protocol_data.get("category", ""),
            "title": protocol_data.get("title", ""),
            "steps_count": len(protocol_data["steps"]),
            "indexed_at": datetime.now().isoformat()
        }
        
        self.knowledge_collection.upsert(
            ids=[knowledge_id],
            embeddings=[embedding],
            documents=[knowledge_text],
            metadatas=[metadata]
        )
        
        return 1
    
    def _index_emergency_section(self, emergency_key: str, emergency_data: Dict, filename: str) -> int:
        """Index an emergency procedure section"""
        knowledge_id = f"emergency_{emergency_key}"
        
        # Create text for embedding
        text_parts = [
            f"Category: {emergency_data.get('category', '')}",
            f"Title: {emergency_data.get('title', '')}",
            "Emergency Steps:"
        ]
        
        # Handle different emergency data structures
        if "immediate_steps" in emergency_data:
            for step in emergency_data["immediate_steps"]:
                step_text = f"Priority {step.get('priority', '')}: {step.get('action', '')} - {step.get('details', '')} (Time: {step.get('time', '')})"
                text_parts.append(step_text)
        
        if "time_critical_steps" in emergency_data:
            for step in emergency_data["time_critical_steps"]:
                step_text = f"Timeframe {step.get('time_frame', '')}: {step.get('action', '')} - {step.get('details', '')} Critical: {', '.join(step.get('critical_points', []))}"
                text_parts.append(step_text)
        
        knowledge_text = " | ".join(text_parts)
        
        # Generate embedding and store
        embedding = self.encoder.encode(knowledge_text).tolist()
        
        metadata = {
            "source": "dental_knowledge",
            "type": "emergency",
            "filename": filename,
            "category": emergency_data.get("category", ""),
            "title": emergency_data.get("title", ""),
            "indexed_at": datetime.now().isoformat()
        }
        
        self.knowledge_collection.upsert(
            ids=[knowledge_id],
            embeddings=[embedding],
            documents=[knowledge_text],
            metadatas=[metadata]
        )
        
        return 1
    
    def _index_contraindication_section(self, contra_key: str, contra_data: Dict, filename: str) -> int:
        """Index a contraindication section"""
        if "contraindications" not in contra_data:
            return 0
        
        indexed_count = 0
        for i, contraindication in enumerate(contra_data["contraindications"]):
            knowledge_id = f"contraindication_{contra_key}_{i}"
            
            # Create text for embedding
            text_parts = [
                f"Category: {contra_data.get('category', '')}",
                f"Title: {contra_data.get('title', '')}",
                f"Condition: {contraindication.get('condition', '')}",
                f"Affected Procedures: {', '.join(contraindication.get('affected_procedures', []))}",
                f"Recommendation: {contraindication.get('recommendation', '')}",
                f"Rationale: {contraindication.get('rationale', '')}"
            ]
            knowledge_text = " | ".join(filter(None, text_parts))
            
            # Generate embedding and store
            embedding = self.encoder.encode(knowledge_text).tolist()
            
            metadata = {
                "source": "dental_knowledge",
                "type": "contraindication",
                "filename": filename,
                "category": contra_data.get("category", ""),
                "title": contra_data.get("title", ""),
                "condition": contraindication.get("condition", ""),
                "indexed_at": datetime.now().isoformat()
            }
            
            self.knowledge_collection.upsert(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[metadata]
            )
            
            indexed_count += 1
        
        return indexed_count
    
    def _index_evidence_section(self, evidence_key: str, evidence_data: Dict, filename: str) -> int:
        """Index an evidence-based recommendation section"""
        if "recommendations" not in evidence_data:
            return 0
        
        indexed_count = 0
        for i, recommendation in enumerate(evidence_data["recommendations"]):
            knowledge_id = f"evidence_{evidence_key}_{i}"
            
            # Create text for embedding
            text_parts = [
                f"Category: {evidence_data.get('category', '')}",
                f"Title: {evidence_data.get('title', '')}",
                f"Clinical Situation: {recommendation.get('clinical_situation', '')}",
                f"Material: {recommendation.get('material', '')}",
                f"Evidence Level: {recommendation.get('evidence_level', '')}",
                f"Rationale: {recommendation.get('rationale', '')}"
            ]
            knowledge_text = " | ".join(filter(None, text_parts))
            
            # Generate embedding and store
            embedding = self.encoder.encode(knowledge_text).tolist()
            
            metadata = {
                "source": "dental_knowledge",
                "type": "evidence",
                "filename": filename,
                "category": evidence_data.get("category", ""),
                "title": evidence_data.get("title", ""),
                "clinical_situation": recommendation.get("clinical_situation", ""),
                "indexed_at": datetime.now().isoformat()
            }
            
            self.knowledge_collection.upsert(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[metadata]
            )
            
            indexed_count += 1
        
        return indexed_count
    
    def _extract_case_text(self, case_data: Dict) -> str:
        """Extract comprehensive text from a treatment case"""
        text_parts = []
        
        # Add consultation text
        if "consultation_text" in case_data:
            text_parts.append(f"Consultation: {case_data['consultation_text']}")
        
        # Add treatment sequence information
        if "treatment_sequence" in case_data:
            text_parts.append("Treatment Sequence:")
            for i, treatment in enumerate(case_data["treatment_sequence"], 1):
                treatment_text = f"RDV {i}: {treatment.get('traitement', '')} - Duration: {treatment.get('duree', '')} - Doctor: {treatment.get('dr', '')} - Remarks: {treatment.get('remarque', '')}"
                text_parts.append(treatment_text)
        
        return " | ".join(text_parts)
    
    def search_cases(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant treatment cases"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search in cases collection
            results = self.cases_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'source': 'case'
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching cases: {e}")
            return []
    
    def search_knowledge(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant dental knowledge"""
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Search in knowledge collection
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'source': 'knowledge'
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching knowledge: {e}")
            return []
    
    def search_combined(self, query: str, case_results: int = 2, knowledge_results: int = 3) -> Dict[str, List[Dict]]:
        """Search both cases and knowledge, return combined results"""
        try:
            # Search both collections
            cases = self.search_cases(query, case_results)
            knowledge = self.search_knowledge(query, knowledge_results)
            
            return {
                'cases': cases,
                'knowledge': knowledge,
                'total_results': len(cases) + len(knowledge)
            }
            
        except Exception as e:
            print(f"❌ Error in combined search: {e}")
            return {'cases': [], 'knowledge': [], 'total_results': 0}
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the indexed collections"""
        try:
            cases_count = self.cases_collection.count()
            knowledge_count = self.knowledge_collection.count()
            
            return {
                'cases_count': cases_count,
                'knowledge_count': knowledge_count,
                'total_items': cases_count + knowledge_count,
                'collections': {
                    'cases': self.cases_collection_name,
                    'knowledge': self.knowledge_collection_name
                }
            }
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return {'cases_count': 0, 'knowledge_count': 0, 'total_items': 0}
    
    def reindex_all(self) -> Dict[str, int]:
        """Reindex all content (cases, knowledge, and specialized knowledge)"""
        print("🔄 Starting full reindexing...")
        
        # Index treatment cases
        cases_count = self.index_treatment_cases()
        
        # Index dental knowledge
        knowledge_count = self.index_dental_knowledge()
        
        # Index specialized knowledge
        specialized_count = self.index_specialized_knowledge()
        
        # Get final stats
        stats = self.get_collection_stats()
        
        print(f"✅ Reindexing complete!")
        print(f"   - Treatment cases: {stats['cases_count']}")
        print(f"   - Knowledge items: {stats['knowledge_count']}")
        print(f"   - Total indexed: {stats['total_items']}")
        
        return {
            'cases_indexed': cases_count,
            'knowledge_indexed': knowledge_count,
            'specialized_indexed': specialized_count,
            'total_cases': stats['cases_count'],
            'total_knowledge': stats['knowledge_count']
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize RAG system
    rag = EnhancedDentalRAG()
    
    # Test search
    test_query = "traitement de canal molaire"
    print(f"\n🔍 Testing search for: '{test_query}'")
    
    context, cases = rag.get_rag_context(test_query)
    print(f"\n📄 Context:\n{context}")
    
    # Print stats
    stats = rag.get_stats()
    print(f"\n📊 RAG System Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}") 