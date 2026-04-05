"""
Knowledge Graph for BRaaS Pipeline
===================================

Manages structured knowledge for experiments:
- Protein and pathway information
- Reagent alternatives
- Protocol similarity matching
- Neo4j export capability
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

from braas.core.models import Experiment, ExperimentResult, Protocol


@dataclass
class ProteinInfo:
    """Protein information from knowledge base."""
    name: str
    uniprot_id: str
    function: str
    pathways: list[str]
    aliases: list[str]
    sequence: str


@dataclass
class PathwayInfo:
    """Pathway information from knowledge base."""
    name: str
    genes: list[str]
    reactions: list[str]
    disease_links: list[str]


@dataclass
class AlternativeReagent:
    """Alternative reagent information."""
    name: str
    catalog: str
    price: float
    compatibility: str


@dataclass
class SimilarProtocol:
    """Similar protocol from knowledge base."""
    protocol_id: str
    similarity_score: float
    key_differences: list[str]


class KnowledgeGraph:
    """Knowledge graph for BRaaS experiments and protocols.
    
    Maintains a graph-based representation of:
    - Proteins, pathways, and biological relationships
    - Reagent alternatives and suppliers
    - Historical experiment results
    - Protocol similarity for recommendations
    """
    
    def __init__(self, data_dir: str | None = None):
        """Initialize knowledge graph.
        
        Args:
            data_dir: Directory containing JSON data files for public databases
        """
        self._data_dir = data_dir or os.path.join(
            os.path.dirname(__file__), "data"
        )
        
        # Graph structure: {node_id: {type, properties, relationships}}
        self.graph: dict[str, dict[str, Any]] = {}
        
        # Indexes for fast queries
        self._protein_index: dict[str, str] = {}
        self._pathway_index: dict[str, str] = {}
        self._reagent_index: dict[str, str] = {}
        
        # Load public databases on init
        self.load_public_databases()
    
    def load_public_databases(self) -> None:
        """Load sample data from public databases in data/ directory."""
        sample_data_file = os.path.join(self._data_dir, "sample_knowledge.json")
        
        if os.path.exists(sample_data_file):
            with open(sample_data_file, 'r') as f:
                data = json.load(f)
                self._load_json_data(data)
        else:
            # Load built-in sample data
            self._load_builtin_data()
    
    def _load_json_data(self, data: dict[str, Any]) -> None:
        """Load data from JSON structure."""
        # Load proteins
        for protein in data.get("proteins", []):
            node_id = f"protein:{protein['uniprot_id']}"
            self.graph[node_id] = {
                "type": "protein",
                "properties": {
                    "name": protein["name"],
                    "uniprot_id": protein["uniprot_id"],
                    "function": protein.get("function", ""),
                    "pathways": protein.get("pathways", []),
                    "aliases": protein.get("aliases", []),
                    "sequence": protein.get("sequence", "")
                },
                "relationships": []
            }
            self._protein_index[protein["name"].lower()] = node_id
            self._protein_index[protein["uniprot_id"].lower()] = node_id
        
        # Load pathways
        for pathway in data.get("pathways", []):
            node_id = f"pathway:{pathway['name'].replace(' ', '_')}"
            self.graph[node_id] = {
                "type": "pathway",
                "properties": {
                    "name": pathway["name"],
                    "genes": pathway.get("genes", []),
                    "reactions": pathway.get("reactions", []),
                    "disease_links": pathway.get("disease_links", [])
                },
                "relationships": []
            }
            self._pathway_index[pathway["name"].lower()] = node_id
        
        # Load reagent alternatives
        for reagent in data.get("reagents", []):
            node_id = f"reagent:{reagent['name'].lower().replace(' ', '_')}"
            self.graph[node_id] = {
                "type": "reagent",
                "properties": {
                    "name": reagent["name"],
                    "catalog": reagent.get("catalog", ""),
                    "price": reagent.get("price", 0.0),
                    "compatibility": reagent.get("compatibility", "")
                },
                "relationships": []
            }
            self._reagent_index[reagent["name"].lower()] = node_id
    
    def _load_builtin_data(self) -> None:
        """Load built-in sample knowledge data."""
        # Sample proteins
        proteins = [
            {
                "name": "BRCA1",
                "uniprot_id": "P38398",
                "function": "DNA repair, tumor suppressor",
                "pathways": ["DNA repair", "Homologous recombination"],
                "aliases": ["BRCC1", "IRIS"],
                "sequence": "MFGLLRSR..."
            },
            {
                "name": "TP53",
                "uniprot_id": "P04637",
                "function": "Cell cycle regulation, tumor suppressor",
                "pathways": ["Apoptosis", "Cell cycle", "DNA damage response"],
                "aliases": ["p53", "LSFC1"],
                "sequence": "MEEPQSDPSV..."
            },
            {
                "name": "EGFR",
                "uniprot_id": "P00533",
                "function": "Cell growth, proliferation",
                "pathways": ["MAPK signaling", "PI3K signaling"],
                "aliases": ["HER1", "ERBB1"],
                "sequence": "MRPSGTAGA..."
            }
        ]
        
        for protein in proteins:
            node_id = f"protein:{protein['uniprot_id']}"
            self.graph[node_id] = {
                "type": "protein",
                "properties": protein,
                "relationships": []
            }
            self._protein_index[protein["name"].lower()] = node_id
            self._protein_index[protein["uniprot_id"].lower()] = node_id
        
        # Sample pathways
        pathways = [
            {
                "name": "DNA repair",
                "genes": ["BRCA1", "BRCA2", "TP53", "ATM"],
                "reactions": ["Base excision repair", "Nucleotide excision repair"],
                "disease_links": ["Breast cancer", "Ovarian cancer"]
            },
            {
                "name": "Apoptosis",
                "genes": ["TP53", "BAX", "BCL2", "CASP3"],
                "reactions": ["Intrinsic pathway", "Extrinsic pathway"],
                "disease_links": ["Cancer", "Neurodegeneration"]
            }
        ]
        
        for pathway in pathways:
            node_id = f"pathway:{pathway['name'].replace(' ', '_')}"
            self.graph[node_id] = {
                "type": "pathway",
                "properties": pathway,
                "relationships": []
            }
            self._pathway_index[pathway["name"].lower()] = node_id
        
        # Sample reagent alternatives
        reagents = [
            {"name": "DMEM", "catalog": "11965-092", "price": 45.00, "compatibility": "Standard cell culture"},
            {"name": "Fetal Bovine Serum", "catalog": "16000-044", "price": 280.00, "compatibility": "All media"},
            {"name": "Trypsin-EDTA", "catalog": "25200-056", "price": 35.00, "compatibility": "Detachment"},
            {"name": "Lipofectamine 3000", "catalog": "L3000001", "price": 220.00, "compatibility": "Transfection"},
        ]
        
        for reagent in reagents:
            node_id = f"reagent:{reagent['name'].lower().replace(' ', '_')}"
            self.graph[node_id] = {
                "type": "reagent",
                "properties": reagent,
                "relationships": []
            }
            self._reagent_index[reagent["name"].lower()] = node_id
    
    def query_protein(self, protein_name: str) -> ProteinInfo | None:
        """Query protein information by name or UniProt ID.
        
        Args:
            protein_name: Protein name or UniProt ID
            
        Returns:
            ProteinInfo if found, None otherwise
        """
        name_lower = protein_name.lower()
        
        node_id = self._protein_index.get(name_lower)
        
        if not node_id:
            # Try partial match
            for key, nid in self._protein_index.items():
                if name_lower in key:
                    node_id = nid
                    break
        
        if not node_id or node_id not in self.graph:
            return None
        
        node = self.graph[node_id]
        props = node["properties"]
        
        return ProteinInfo(
            name=props["name"],
            uniprot_id=props["uniprot_id"],
            function=props.get("function", ""),
            pathways=props.get("pathways", []),
            aliases=props.get("aliases", []),
            sequence=props.get("sequence", "")
        )
    
    def query_pathway(self, pathway_name: str) -> PathwayInfo | None:
        """Query pathway information by name.
        
        Args:
            pathway_name: Name of the pathway
            
        Returns:
            PathwayInfo if found, None otherwise
        """
        name_lower = pathway_name.lower()
        
        node_id = self._pathway_index.get(name_lower)
        
        if not node_id:
            # Try partial match
            for key, nid in self._pathway_index.items():
                if name_lower in key:
                    node_id = nid
                    break
        
        if not node_id or node_id not in self.graph:
            return None
        
        node = self.graph[node_id]
        props = node["properties"]
        
        return PathwayInfo(
            name=props["name"],
            genes=props.get("genes", []),
            reactions=props.get("reactions", []),
            disease_links=props.get("disease_links", [])
        )
    
    def query_reagent_alternatives(self, reagent_name: str) -> list[AlternativeReagent]:
        """Query alternative reagents for a given reagent.
        
        Args:
            reagent_name: Name of the reagent to find alternatives for
            
        Returns:
            List of AlternativeReagent options
        """
        name_lower = reagent_name.lower()
        
        # Find the original reagent
        original_id = self._reagent_index.get(name_lower)
        original_node = None
        
        if original_id and original_id in self.graph:
            original_node = self.graph[original_id]
        
        # Find alternatives by compatibility type
        alternatives = []
        compatibility_type = None
        
        if original_node:
            compatibility_type = original_node["properties"].get("compatibility", "")
        
        for node_id, node in self.graph.items():
            if node["type"] != "reagent":
                continue
            
            if node_id == original_id:
                continue
            
            props = node["properties"]
            
            # Same compatibility type suggests alternative
            if compatibility_type:
                node_compat = props.get("compatibility", "")
                if node_compat == compatibility_type:
                    alternatives.append(AlternativeReagent(
                        name=props["name"],
                        catalog=props.get("catalog", ""),
                        price=props.get("price", 0.0),
                        compatibility=node_compat
                    ))
            else:
                # Return all reagents as potential alternatives
                alternatives.append(AlternativeReagent(
                    name=props["name"],
                    catalog=props.get("catalog", ""),
                    price=props.get("price", 0.0),
                    compatibility=props.get("compatibility", "")
                ))
        
        return alternatives
    
    def add_experiment_result(self, exp_result: ExperimentResult) -> None:
        """Add experiment result as new knowledge nodes.
        
        Creates knowledge graph nodes from experimental results
        for future similarity matching and learning.
        
        Args:
            exp_result: The experiment result to add
        """
        # Create experiment node
        exp_node_id = f"experiment:{exp_result.experiment_id}"
        self.graph[exp_node_id] = {
            "type": "experiment_result",
            "properties": {
                "result_id": exp_result.result_id,
                "experiment_id": exp_result.experiment_id,
                "quality_score": exp_result.quality_score,
                "passed_qc": exp_result.passed_qc,
                "summary": exp_result.summary,
                "created_at": str(exp_result.created_at)
            },
            "relationships": []
        }
        
        # Add ML predictions as separate node if present
        if exp_result.ml_predictions:
            pred_node_id = f"prediction:{exp_result.result_id}"
            self.graph[pred_node_id] = {
                "type": "ml_prediction",
                "properties": exp_result.ml_predictions,
                "relationships": [{"target_id": exp_node_id, "type": "from_result", "properties": {}}]
            }
            
            # Link prediction to experiment
            self.graph[exp_node_id]["relationships"].append({
                "target_id": pred_node_id,
                "type": "has_prediction",
                "properties": {}
            })
    
    def query_similar_protocols(
        self, protocol_type: str, parameters: dict[str, Any]
    ) -> list[SimilarProtocol]:
        """Find protocols similar to given parameters.
        
        Uses parameter-based matching to find historically
        successful protocols.
        
        Args:
            protocol_type: Type of protocol (e.g., 'elisa', 'qpcr')
            parameters: Protocol parameters to match
            
        Returns:
            List of SimilarProtocol sorted by similarity score
        """
        similar = []
        
        # Search for experiment result nodes
        for node_id, node in self.graph.items():
            if node["type"] != "experiment_result":
                continue
            
            props = node["properties"]
            
            # Calculate similarity based on parameters
            similarity = self._calculate_protocol_similarity(
                protocol_type, parameters, props.get("summary", {})
            )
            
            if similarity > 0.3:  # Minimum threshold
                key_diff = self._find_key_differences(parameters, props.get("summary", {}))
                
                similar.append(SimilarProtocol(
                    protocol_id=props.get("experiment_id", node_id),
                    similarity_score=round(similarity, 3),
                    key_differences=key_diff
                ))
        
        # Sort by similarity
        similar.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return similar[:10]  # Top 10
    
    def export_to_neo4j_format(self) -> str:
        """Export knowledge graph to Neo4j Cypher query format.
        
        Returns:
            String containing Cypher CREATE statements
        """
        cypher_queries = []
        
        for node_id, node in self.graph.items():
            props = node["properties"]
            
            # Escape values for Cypher
            props_str = []
            for key, value in props.items():
                if isinstance(value, str):
                    escaped = value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
                    props_str.append(f"{key}: '{escaped}'")
                elif isinstance(value, (int, float, bool)):
                    props_str.append(f"{key}: {value}")
                elif isinstance(value, list):
                    items = []
                    for item in value:
                        if isinstance(item, str):
                            items.append(f"'{item}'")
                        else:
                            items.append(str(item))
                    props_str.append(f"{key}: [{', '.join(items)}]")
                else:
                    props_str.append(f"{key}: '{value}'")
            
            props_clause = ", ".join(props_str)
            
            # CREATE node
            node_type = node["type"]
            cypher_queries.append(
                f"CREATE (n:{node_type} {{{props_clause}}})"
            )
            
            # CREATE relationships
            for rel in node.get("relationships", []):
                target = rel["target_id"]
                rel_type = rel["type"]
                rel_props = rel.get("properties", {})
                
                if rel_props:
                    rp = []
                    for k, v in rel_props.items():
                        if isinstance(v, str):
                            rp.append(f"{k}: '{v}'")
                        else:
                            rp.append(f"{k}: {v}")
                    props_clause = ", ".join(rp)
                    cypher_queries.append(
                        f"CREATE (n:{node_type})-[r:{rel_type} {{{props_clause}}}]->(m)"
                    )
                else:
                    cypher_queries.append(
                        f"CREATE (n:{node_type})-[r:{rel_type}]->(m)"
                    )
        
        return "\n".join(cypher_queries)
    
    def _calculate_protocol_similarity(
        self, protocol_type: str, params1: dict, params2: dict
    ) -> float:
        """Calculate similarity between two protocol parameter sets."""
        if not params1 or not params2:
            return 0.0
        
        # Simple Jaccard-like similarity
        all_keys = set(params1.keys()) | set(params2.keys())
        if not all_keys:
            return 0.0
        
        matching = 0
        for key in all_keys:
            if key in params1 and key in params2:
                v1, v2 = params1[key], params2[key]
                if v1 == v2:
                    matching += 1
                elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    # Numerical similarity
                    max_val = max(abs(v1), abs(v2))
                    if max_val > 0:
                        diff = abs(v1 - v2) / max_val
                        matching += 1 - min(diff, 1.0)
        
        return matching / len(all_keys)
    
    def _find_key_differences(
        self, params1: dict, params2: dict
    ) -> list[str]:
        """Find key differences between parameter sets."""
        differences = []
        
        all_keys = set(params1.keys()) | set(params2.keys())
        
        for key in all_keys:
            if key in params1 and key in params2:
                v1, v2 = params1[key], params2[key]
                if v1 != v2:
                    differences.append(
                        f"{key}: {v1} vs {v2}"
                    )
            elif key in params1:
                differences.append(f"{key}: present in query, absent in comparison")
            else:
                differences.append(f"{key}: absent in query, present in comparison")
        
        return differences[:5]  # Top 5 differences
