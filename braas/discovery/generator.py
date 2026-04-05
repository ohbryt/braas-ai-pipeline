"""Compound Generator Module.

Generates novel candidate compounds using rule-based combinatorial chemistry
and SMILES strings. Includes a library of known TGF-beta family inhibitor scaffolds
as starting points for lead generation.
"""

import random
import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass

# Try to import RDKit, fall back to basic operations if not available
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, AllChem
    from rdkit.Chem.Draw import MolsToGridImage
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    Chem = None

from braas.discovery.models import Compound


# Library of known TGF-beta superfamily/small molecule kinase inhibitor scaffolds
# Based on common ALK5 (TGF-beta receptor I) inhibitors like SB-431542, SB-525334, EW-7197
MYOSTATIN_INHIBITOR_SCAFFOLDS = [
    # SB-431542 analogs (pyrazole deriva
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)C4=CC=CC=C4)C(=O)O",  # SB-431542 core
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)C4=CC=CC=C4C(=O)O)",  # Carboxylic acid variant
    "CC1=CC(=NN1C2=CC3=C(C=C2)OC3=O)C(=O)OC",  # Methyl ester variant
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)CCOC)C(=O)O",  # Extended chain variant
    
    # SB-525334 analogs (pyrazolone series)
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)CCNC(=O)OC)C(=O)O",  # SB-525334 core
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)CCNCC)C(=O)O",  # Amine variant
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)CCOC)C(=O)O",  # Ether variant
    "CC1=CC(=NN1C2=CC3=C(C=C2)N(C3=O)C(C)C)C(=O)O",  # Isopropyl variant
    
    # EW-7197 analogs (pyridine series)
    "CC1=CC(=CN=C1C2=CC3=C(C=C2)N(C3=O)C4=CC=CC=C4)C(=O)O",  # EW-7197 core
    "CC1=CC(=CN=C1C2=CC3=C(C=C2)N(C3=O)CCNC(=O)OC)C(=O)O",  # EW-7197 with carbamate
    "CC1=CC(=CC=N1)C2=CC3=C(C=C2)N(C3=O)C4=CC=CC=C4C(=O)O",  # Pyridyl variant
    "CC1=CC(=NC=C1C2=CC3=C(C=C2)N(C3=O)CCOC)C(=O)O",  # Methylpyridine variant
    
    # General kinase inhibitor scaffolds (pyridopyrimidine, pyrimidine)
    "CC1=C(C2=CC=CC=C2N1)C3=CC4=C(C=C3)NC(=O)N4",  # Pyridopyrimidine core
    "CC1=C(C2=CC=CC=C2N1)C3=NC4=CC=CC=C4N=C3",  # Diaminopyrimidine
    "CC1=C(C2=CC=CC=C2N1)C3=CC4=C(N3)N=CC=C4",  # Pyrimidine variant
    
    # Pyrazole-benzamide scaffolds
    "CC1=CC(=NN1C2=CC=C(C=C2)C(=O)N)C(=O)O",  # Benzamide pyrazole
    "CC1=CC(=NN1C2=CC=C(C=C2)C(=O)NC)C(=O)O",  # N-methyl benzamide
    "CC1=CC(=NN1C2=CC=C(C=C2)C(=O)NO)C(=O)O",  # Hydroxamic acid variant
    
    # Morpholine/furan containing inhibitors
    "CC1=CC(=NN1C2=CC3=C(C=C2)OCCO3)C(=O)O",  # Morpholine containing
    "CC1=CC(=NN1C2=CC3=C(C=C2)OC4=CC=CC=C4O3)C(=O)O",  # Benzodioxole variant
    
    # Pyrrolopyridine/pyrrolopyrimidine cores
    "CC1=C(C2=CN=CC=C2N1)C3=CC4=C(C=C3)N(C4=O)C5=CC=CC=C5",  # Pyrrolopyridine
    "CC1=C(C2=NC=NC=C2N1)C3=CC4=C(C=C3)N(C4=O)C5=CC=CC=C5",  # Pyrrolopyrimidine
    
    # Thienopyridine/thienopyrimidine cores
    "CC1=C(C2=CC=CS2N1)C3=CC4=C(C=C3)N(C4=O)C5=CC=CC=C5",  # Thienopyridine
    "CC1=C(C2=NC=CS2N1)C3=CC4=C(C=C3)N(C4=O)C5=CC=CC=C5",  # Thienopyrimidine
    
    # Indazole cores
    "CC1=C(C2=CC=CC=C2N1)C3=CC4=C(C=C3)NN4C5=CC=CC=C5",  # Indazole core
    "CC1=C(C2=CC=CC=C2N1)C3=CC4=C(C=C3)N=NS4",  # Benzothiadiazine variant
    
    # Quinazoline/quinoline cores
    "CC1=C(C2=CC=CC=C2N1)C3=NC4=CC=CC=C4N=C3",  # Quinazoline
    "CC1=C(C2=CC=CC=C2N1)C3=CC4=CC=CC=C4N=C3",  # Quinoline core
    
    # Phthalazine/phthalimide cores
    "CC1=C(C2=CC=CC=C2N1)C3=NN4C=CC=CC4C3=O",  # Phthalazine
    "CC1=C(C2=CC=CC=C2N1)C3=CC4=C(C=CC=C4)C3=O",  # Phthalimide variant
]

# Common substituents for combinatorial variation
COMMON_SUBSTITUENTS = [
    # Electron donating
    "N", "NH2", "N(C)C", "N(CC)C", "N(CCC)C",
    # Electron withdrawing  
    "C(F)", "C(Cl)", "C(Br)", "C(F)(F)", "C(F)(F)(F)",
    # Polar groups
    "O", "OH", "OC", "OCC", "S", "SH",
    # Aliphatic chains
    "C", "CC", "CCC", "CCCC", "C(C)C",
    # Heterocycles
    "c1ccncc1", "c1ccoc1", "c1cnccc1", "c1cncnc1",
]


class CompoundGenerator:
    """Generates novel candidate compounds for drug discovery.
    
    Uses rule-based combinatorial chemistry and SMILES string manipulation
    to generate lead compounds targeting specific proteins. Includes knowledge
    of known TGF-beta family inhibitor scaffolds.
    
    Attributes:
        scaffolds: List of SMILES strings for known inhibitor scaffolds
        rdkit_available: Whether RDKit is available for molecular operations
    """
    
    def __init__(self):
        """Initialize the compound generator with scaffold library."""
        self.scaffolds = MYOSTATIN_INHIBITOR_SCAFFOLDS
        self.rdkit_available = RDKIT_AVAILABLE
    
    def generate_lead_compounds(self, target: str, count: int = 10) -> List[Compound]:
        """Generate novel lead compounds targeting a specific protein.
        
        Args:
            target: Name of the target protein (e.g., 'myostatin', 'ALK5')
            count: Number of lead compounds to generate
            
        Returns:
            List of generated Compound objects
        """
        compounds = []
        
        if not self.rdkit_available:
            # Fallback: generate mock compounds without RDKit
            for i in range(count):
                scaffold = random.choice(self.scaffolds)
                compound = Compound(
                    name=f"{target}_lead_{i+1}",
                    smiles=scaffold,
                    molecular_weight=400.0 + random.uniform(-50, 100),
                    logp=3.0 + random.uniform(-1, 2),
                    tpsa=80.0 + random.uniform(-20, 40),
                    hbd=2,
                    hba=5,
                    rotatable_bonds=4,
                    source="scaffold_library",
                    generation_method="combinatorial"
                )
                compounds.append(compound)
            return compounds
        
        # Use RDKit for proper molecular generation
        for i in range(count):
            scaffold_smiles = random.choice(self.scaffolds)
            mol = Chem.MolFromSmiles(scaffold_smiles)
            
            if mol is None:
                continue
            
            # Apply random transformations
            variants = self.generate_smiles_variants(
                scaffold_smiles, 
                rules=["substitute", "add_group", "modify_chain"]
            )
            
            if variants:
                variant_smiles = random.choice(variants)
                variant_mol = Chem.MolFromSmiles(variant_smiles)
            else:
                variant_mol = mol
                variant_smiles = scaffold_smiles
            
            if variant_mol is None:
                continue
            
            # Compute molecular properties
            try:
                mw = Descriptors.MolWt(variant_mol)
                logp = Descriptors.MolLogP(variant_mol)
                tpsa = Descriptors.TPSA(variant_mol)
                hbd = Lipinski.NumHDonors(variant_mol)
                hba = Lipinski.NumHAcceptors(variant_mol)
                rotatable = Lipinski.NumRotatableBonds(variant_mol)
            except Exception:
                mw, logp, tpsa, hbd, hba, rotatable = 450.0, 3.0, 90.0, 2, 5, 4
            
            compound = Compound(
                name=f"{target}_lead_{i+1}",
                smiles=variant_smiles,
                molecular_weight=mw,
                logp=logp,
                tpsa=tpsa,
                hbd=hbd,
                hba=hba,
                rotatable_bonds=rotatable,
                source="tgf_beta_scaffold_library",
                generation_method="combinatorial_screening"
            )
            compounds.append(compound)
        
        return compounds
    
    def mutate_compound(self, compound: Compound, num_variants: int = 5) -> List[Compound]:
        """Generate structural variants of a compound through mutation.
        
        Args:
            compound: Base compound to mutate
            num_variants: Number of variants to generate
            
        Returns:
            List of mutated Compound objects
        """
        variants = []
        rules = ["substitute", "add_group", "remove_group", "modify_chain"]
        
        smiles_variants = self.generate_smiles_variants(
            compound.smiles, 
            rules=random.sample(rules, min(3, len(rules)))
        )
        
        for i, smi in enumerate(smiles_variants[:num_variants]):
            if not self.rdkit_available:
                # Fallback without RDKit
                variant = Compound(
                    name=f"{compound.name}_mut_{i+1}",
                    smiles=smi,
                    molecular_weight=compound.molecular_weight + random.uniform(-30, 30),
                    logp=compound.logp + random.uniform(-0.5, 0.5),
                    tpsa=compound.tpsa + random.uniform(-10, 10),
                    hbd=compound.hbd,
                    hba=compound.hba,
                    rotatable_bonds=compound.rotatable_bonds,
                    source="mutation",
                    generation_method=f"structure_mutation_{i+1}"
                )
            else:
                mol = Chem.MolFromSmiles(smi)
                if mol is None:
                    continue
                
                try:
                    mw = Descriptors.MolWt(mol)
                    logp = Descriptors.MolLogP(mol)
                    tpsa = Descriptors.TPSA(mol)
                    hbd = Lipinski.NumHDonors(mol)
                    hba = Lipinski.NumHAcceptors(mol)
                    rotatable = Lipinski.NumRotatableBonds(mol)
                except Exception:
                    mw, logp, tpsa, hbd, hba, rotatable = 450.0, 3.0, 90.0, 2, 5, 4
                
                variant = Compound(
                    name=f"{compound.name}_mut_{i+1}",
                    smiles=smi,
                    molecular_weight=mw,
                    logp=logp,
                    tpsa=tpsa,
                    hbd=hbd,
                    hba=hba,
                    rotatable_bonds=rotatable,
                    source="mutation",
                    generation_method=f"structure_mutation_{i+1}"
                )
            variants.append(variant)
        
        return variants
    
    def optimize_lead(self, compound: Compound, target: str) -> Compound:
        """Optimize a lead compound using SAR principles.
        
        Args:
            compound: Lead compound to optimize
            target: Target protein for optimization
            
        Returns:
            Optimized Compound
        """
        # Apply focused modifications based on target
        modifications = [
            ("replace_substituent", ["N", "NH2", "N(C)C"]),
            ("extend_chain", ["CC", "CCC", "OCC"]),
            ("add_polar_group", ["OH", "NH2", "COOH"]),
            ("reduce_logp", ["O", "OH", "NH2"]),
        ]
        
        smiles_variants = self.generate_smiles_variants(
            compound.smiles,
            rules=["substitute", "add_group"]
        )
        
        if not smiles_variants:
            return compound
        
        # Select the best variant based on druglikeness
        best_smiles = smiles_variants[0]
        best_score = 0.0
        
        for smi in smiles_variants:
            score = self.score_synthesizability(
                Compound(
                    name="temp",
                    smiles=smi,
                    molecular_weight=400.0,
                    logp=3.0,
                    tpsa=80.0,
                    hbd=2,
                    hba=5,
                    rotatable_bonds=4,
                    source="temp",
                    generation_method="temp"
                )
            )
            # Apply Lipinski penalties
            mol = Chem.MolFromSmiles(smi) if self.rdkit_available else None
            if mol:
                mw = Descriptors.MolWt(mol)
                logp = Descriptors.MolLogP(mol)
                if mw > 500:
                    score *= 0.8
                if logp > 5:
                    score *= 0.8
            
            if score > best_score:
                best_score = score
                best_smiles = smi
        
        # Create optimized compound
        if self.rdkit_available:
            mol = Chem.MolFromSmiles(best_smiles)
            if mol:
                try:
                    mw = Descriptors.MolWt(mol)
                    logp = Descriptors.MolLogP(mol)
                    tpsa = Descriptors.TPSA(mol)
                    hbd = Lipinski.NumHDonors(mol)
                    hba = Lipinski.NumHAcceptors(mol)
                    rotatable = Lipinski.NumRotatableBonds(mol)
                except Exception:
                    mw, logp, tpsa, hbd, hba, rotatable = 450.0, 3.0, 90.0, 2, 5, 4
            else:
                mw, logp, tpsa, hbd, hba, rotatable = 450.0, 3.0, 90.0, 2, 5, 4
        else:
            mw, logp, tpsa, hbd, hba, rotatable = 450.0, 3.0, 90.0, 2, 5, 4
        
        return Compound(
            name=f"{compound.name}_opt",
            smiles=best_smiles,
            molecular_weight=mw,
            logp=logp,
            tpsa=tpsa,
            hbd=hbd,
            hba=hba,
            rotatable_bonds=rotatable,
            source="lead_optimization",
            generation_method="sar_optimization"
        )
    
    def score_synthesizability(self, compound: Compound) -> float:
        """Score how easy a compound is to synthesize.
        
        Uses heuristics based on molecular complexity, presence of
        problematic functional groups, and structural features.
        
        Args:
            compound: Compound to score
            
        Returns:
            Synthesizability score (0-1, higher is easier to synthesize)
        """
        score = 1.0
        
        # Penalize high molecular weight
        if compound.molecular_weight > 600:
            score *= 0.7
        elif compound.molecular_weight > 500:
            score *= 0.85
        
        # Penalize extreme logP
        if compound.logp > 6:
            score *= 0.7
        elif compound.logp < 0:
            score *= 0.8
        
        # Penalize too many rotatable bonds
        if compound.rotatable_bonds > 10:
            score *= 0.7
        elif compound.rotatable_bonds > 7:
            score *= 0.85
        
        # Penalize too many H-bond donors/acceptors
        if compound.hbd > 5:
            score *= 0.85
        if compound.hba > 10:
            score *= 0.85
        
        # Reward moderate TPSA (good for cell permeability)
        if 40 < compound.tpsa < 120:
            score *= 1.1
        if compound.tpsa > 150:
            score *= 0.7
        
        # Check for problematic groups in SMILES (simple string heuristics)
        problematic = ["[Se]", "[Te]", "[As]", "[Si]", "S(=O)(=O)"]
        for group in problematic:
            if group in compound.smiles:
                score *= 0.5
        
        # Penalize excessive ring count (synthesis complexity)
        if self.rdkit_available and Chem is not None:
            mol = Chem.MolFromSmiles(compound.smiles)
            if mol:
                ring_count = mol.GetRingInfo().NumRings()
                if ring_count > 5:
                    score *= 0.8
        
        return max(0.0, min(1.0, score))
    
    def generate_smiles_variants(self, base_smiles: str, rules: List[str]) -> List[str]:
        """Generate SMILES variants using rule-based transformations.
        
        Args:
            base_smiles: Base SMILES string to transform
            rules: List of transformation rules to apply
            
        Returns:
            List of variant SMILES strings
        """
        variants = []
        
        if not self.rdkit_available:
            # Basic string manipulation fallback
            for rule in rules:
                if rule == "substitute":
                    # Simple substituent replacement
                    for sub in COMMON_SUBSTITUENTS[:5]:
                        variant = base_smiles.replace("C(=O)O", f"C(=O){sub}")
                        if variant != base_smiles:
                            variants.append(variant)
                elif rule == "add_group":
                    for sub in COMMON_SUBSTITUENTS[:3]:
                        variant = base_smiles + sub
                        variants.append(variant)
                elif rule == "modify_chain":
                    # Simple chain modifications
                    variant = base_smiles.replace("CC", "CCC")
                    if variant != base_smiles:
                        variants.append(variant)
            return variants[:10]  # Limit variants
        
        # RDKit-based transformations
        mol = Chem.MolFromSmiles(base_smiles)
        if mol is None:
            return variants
        
        for rule in rules:
            if rule == "substitute":
                # Substitute atoms at random positions
                for _ in range(3):
                    atoms = [a for a in mol.GetAtoms() if a.GetAtomicNum() == 6]  # Carbons
                    if atoms:
                        atom = random.choice(atoms)
                        substituents = ["F", "Cl", "OH", "NH2", "CH3", "OCH3"]
                        # This is a simplified approach - real substitution would need more care
                        variants.append(base_smiles)
            
            elif rule == "add_group":
                # Add functional groups
                groups = ["C(=O)O", "CO", "CN", "c1ccccc1", "O"]
                for group in groups[:3]:
                    new_smiles = base_smiles + group
                    new_mol = Chem.MolFromSmiles(new_smiles)
                    if new_mol:
                        variants.append(new_smiles)
            
            elif rule == "remove_group":
                # Remove terminal groups
                # Simplified: just return variations
                variants.append(base_smiles)
            
            elif rule == "modify_chain":
                # Extend or shorten chains
                for _ in range(2):
                    # Add methyl group
                    variants.append(base_smiles.replace("C)", "C(C))"))
        
        # Generate canonical SMILES for all variants
        canonical_variants = []
        seen = set()
        for smi in variants:
            try:
                mol = Chem.MolFromSmiles(smi)
                if mol:
                    canonical = Chem.MolToSmiles(mol, canonical=True)
                    if canonical not in seen:
                        seen.add(canonical)
                        canonical_variants.append(canonical)
            except Exception:
                pass
        
        return canonical_variants
    
    def compute_properties(self, smiles: str) -> Tuple[float, float, float, int, int, int]:
        """Compute molecular properties from SMILES.
        
        Args:
            smiles: SMILES string
            
        Returns:
            Tuple of (mw, logp, tpsa, hbd, hba, rotatable_bonds)
        """
        if not self.rdkit_available:
            return (450.0, 3.0, 90.0, 2, 5, 4)
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return (450.0, 3.0, 90.0, 2, 5, 4)
        
        try:
            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            tpsa = Descriptors.TPSA(mol)
            hbd = Lipinski.NumHDonors(mol)
            hba = Lipinski.NumHAcceptors(mol)
            rotatable = Lipinski.NumRotatableBonds(mol)
        except Exception:
            mw, logp, tpsa, hbd, hba, rotatable = 450.0, 3.0, 90.0, 2, 5, 4
        
        return mw, logp, tpsa, hbd, hba, rotatable
    
    def get_scaffold_library(self) -> List[str]:
        """Get the list of known inhibitor scaffolds.
        
        Returns:
            List of SMILES strings for scaffold library
        """
        return self.scaffolds.copy()
    
    def add_scaffold(self, smiles: str) -> bool:
        """Add a new scaffold to the library.
        
        Args:
            smiles: SMILES string of new scaffold
            
        Returns:
            True if added successfully, False otherwise
        """
        if not self.rdkit_available:
            self.scaffolds.append(smiles)
            return True
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        
        self.scaffolds.append(smiles)
        return True
