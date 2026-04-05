#!/usr/bin/env python3
"""
BRaaS Drug Discovery CLI

Usage:
    python scripts/discover_drug.py "myostatin" "sarcopenia" --organism human --num-candidates 20
    python scripts/discover_drug.py --target protein.txt --output-dir outputs/
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

try:
    from rdkit import Chem
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

from braas.discovery import DrugDiscoveryEngine
from braas.knowledge.sarcopenia_research import (
    MYOSTATIN_BIOLOGY, SARCOPENIA_DISEASE, DRUG_TARGET_LANDSCAPE,
    MECHANISMS_OF_ACTION, UNMET_NEEDS, COMPOUND_ANALYSIS_TABLE
)
from braas.knowledge.target_profile import (
    HUMAN_MYOSTATIN_SEQUENCE,
    STRUCTURAL_FEATURES,
    RECEPTOR_BINDING_ANALYSIS,
    NATURAL_GENETIC_NULLS,
    ACTIVE_SITE_ANALYSIS,
)


def print_banner():
    print("=" * 70)
    print("  BRaaS — Drug Discovery Engine for Sarcopenia")
    print("  Target: Myostatin (MSTN) Inhibition")
    print("=" * 70)


def print_research_context():
    print("\n[ RESEARCH CONTEXT ]")
    bio = MYOSTATIN_BIOLOGY.get("gene_info", {})
    print(f"\n  Myostatin Biology:")
    print(f"    - Gene: {bio.get('gene_symbol', 'MSTN')}")
    print(f"    - Family: {MYOSTATIN_BIOLOGY.get('protein_family', 'TGF-beta')}")
    print(f"    - Receptor: {MYOSTATIN_BIOLOGY.get('primary_receptor', 'ActRIIB')}")
    print(f"    - Pathway: {MYOSTATIN_BIOLOGY.get('signaling_pathway', 'SMAD2/3')}")

    sarc = SARCOPENIA_DISEASE
    print(f"\n  Sarcopenia Market:")
    print(f"    - Prevalence: {sarc.get('prevalence', '>50M patients worldwide')}")
    print(f"    - Market Size: {sarc.get('market_size', '$2.8B by 2030')}")
    print(f"    - Unmet Needs: {len(UNMET_NEEDS)} identified")

    print(f"\n  Competitive Landscape:")
    for compound in COMPOUND_ANALYSIS_TABLE[:5]:
        print(f"    - {compound.get('name', compound.get('compound', 'Unknown'))} ({compound.get('company', 'Unknown')}): "
              f"Phase {compound.get('phase', '?')} - {compound.get('mechanism', 'Unknown')}")


def run_discovery(target: str, disease: str, organism: str, num_candidates: int, output_dir: Path):
    print(f"\n[ PIPELINE ] Starting drug discovery for {target} → {disease}")
    print(f"  Organism: {organism}")
    print(f"  Target candidates: {num_candidates}")
    print(f"  RDKit available: {RDKIT_AVAILABLE}\n")

    engine = DrugDiscoveryEngine()
    results = engine.discover_drugs(
        target_protein=target,
        disease_area=disease,
        organism=organism,
        num_candidates=num_candidates
    )

    return results, engine


def print_results(candidates, engine):
    print(f"\n[ RESULTS ] Found {len(candidates)} drug candidates\n")

    if not candidates:
        print("  No candidates generated. Check RDKit installation:")
        print("  pip install rdkit-pypi")
        return

    print(f"  {'Rank':<5} {'Compound':<30} {'Score':<8} {'Efficacy':<10} {'Safety':<8} {'Stage'}")
    print(f"  {'-'*5} {'-'*30} {'-'*8} {'-'*10} {'-'*8} {'-'*20}")

    for i, candidate in enumerate(candidates[:15], 1):
        comp = candidate.compound
        efficacy = f"{candidate.efficacy_score:.2f}"
        safety = f"{candidate.safety_score:.2f}"
        name = comp.name[:28] if len(comp.name) > 28 else comp.name
        print(f"  {i:<5} {name:<30} {candidate.efficacy_score + candidate.safety_score + candidate.admet_profile.score:.2f}   "
              f"{efficacy:<10} {safety:<8} {candidate.stage}")

    report = candidates[0] if candidates else None
    if report:
        print("\n[ TOP CANDIDATE DETAILS ]")
        print(f"  Name: {report.compound.name}")
        print(f"  SMILES: {report.compound.smiles}")
        print(f"  MW: {report.compound.molecular_weight:.1f} Da")
        print(f"  LogP: {report.compound.logp:.2f}")
        print(f"  TPSA: {report.compound.tpsa:.1f} Å²")
        print(f"  HBD/HBA: {report.compound.hbd}/{report.compound.hba}")
        print(f"  Efficacy: {report.efficacy_score:.3f}")
        print(f"  Safety: {report.safety_score:.3f}")
        print(f"  Novelty: {report.novelty_score:.3f}")
        print(f"  ADMET Score: {report.admet_profile.score:.2f}")

        if report.recommendations:
            print(f"\n  Recommendations:")
            for rec in report.recommendations[:5]:
                print(f"    • {rec}")


async def main():
    parser = argparse.ArgumentParser(
        description="BRaaS Drug Discovery for Myostatin Inhibition in Sarcopenia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/discover_drug.py myostatin sarcopenia --organism human
  python scripts/discover_drug.py myostatin sarcopenia --num-candidates 30 --output-dir outputs/
  python scripts/discover_drug.py --target myostatin --list-mechanisms
        """
    )

    parser.add_argument("target", nargs="?", default="myostatin", help="Drug target protein")
    parser.add_argument("disease", nargs="?", default="sarcopenia", help="Disease area")
    parser.add_argument("--organism", default="human", help="Target organism (human/mouse/rat)")
    parser.add_argument("--num-candidates", type=int, default=20, help="Number of candidates to generate")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"), help="Output directory")
    parser.add_argument("--list-mechanisms", action="store_true", help="List known drug mechanisms")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    print_banner()

    if args.list_mechanisms:
        print_research_context()
        print("\n[ MECHANISMS OF ACTION ]")
        for moa, desc in MECHANISMS_OF_ACTION.items():
            print(f"\n  {moa}:")
            print(f"    {desc[:120]}...")
        return

    print_research_context()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run discovery
    candidates, engine = run_discovery(
        target=args.target,
        disease=args.disease,
        organism=args.organism,
        num_candidates=args.num_candidates,
        output_dir=args.output_dir
    )

    # Print results
    print_results(candidates, engine)

    # Save JSON output
    if args.json or True:  # Always save JSON
        output_file = args.output_dir / f"drug_candidates_{args.target}_{args.disease}.json"
        candidates_data = [
            {
                "rank": i + 1,
                "compound": {
                    "name": c.compound.name,
                    "smiles": c.compound.smiles,
                    "mw": round(c.compound.molecular_weight, 2),
                    "logp": round(c.compound.logp, 2),
                    "tpsa": round(c.compound.tpsa, 1),
                    "hbd": c.compound.hbd,
                    "hba": c.compound.hba,
                    "source": c.compound.source,
                },
                "efficacy_score": round(c.efficacy_score, 3),
                "safety_score": round(c.safety_score, 3),
                "admet_score": round(c.admet_profile.score, 2),
                "novelty_score": round(c.novelty_score, 3),
                "stage": c.stage,
                "recommendations": c.recommendations[:3],
            }
            for i, c in enumerate(candidates)
        ]
        with open(output_file, "w") as f:
            json.dump(candidates_data, f, indent=2)
        print(f"\n[ SAVED ] Results → {output_file}")

    # Generate markdown report
    report_file = args.output_dir / f"discovery_report_{args.target}_{args.disease}.md"
    report_text = engine.generate_report(candidates)
    with open(report_file, "w") as f:
        f.write(report_text)
    print(f"[ SAVED ] Report → {report_file}")

    print(f"\n{'=' * 70}")
    print("  Discovery complete. Use --json for machine-readable output.")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())