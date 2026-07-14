#!/usr/bin/env python3
"""
03_annotate_cnv_genes.py
========================
Map aggregated CNV features (arm-level and 5 Mb window) to named protein-coding
genes via the Ensembl REST API (GRCh38).

Input:
    reports/thesis_ch1/lgd2_cnv_feature_importance_aggregated.csv
        (632 features × importance metrics, produced by 07_aggregate_cnv_importance.py)

Outputs:
    reports/thesis_ch1/lgd2_cnv_feature_gene_annotation.csv
        All 632 features with n_protein_coding_genes, cancer_genes, top_cancer_genes
        (committed to git — no patient data)
    reports/thesis_ch1/lgd2_cnv_feature_gene_annotation_full.csv
        Same but with the full semicolon-separated gene list in 'all_genes' column
        (not committed — too wide for the allowlist, useful for local analysis)
    reports/thesis_ch1/lgd2_cnv_arm_gene_summary.csv
        Top-25 arm-level features with cancer gene annotations (for the chapter table)

No patient data is read or written; this script runs in the external sandbox.
Requires: pandas, urllib (stdlib) — no additional pip installs needed.

Usage:
    python scripts/03_annotate_cnv_genes.py

Runtime: ~20–25 minutes (Ensembl REST rate limit: ~15 req/s, tiled queries for arms).
"""

import re
import json
import time
import urllib.request
import os
import pandas as pd

# ---------------------------------------------------------------------------
# GRCh38 chromosome geometry
# ---------------------------------------------------------------------------

# Approximate centromere midpoints (bp) for chr1–22 — used to split arm features
CENTROMERES_GRCh38 = {
    '1':  122026459, '2':  92188145,  '3':  90772458,  '4':  49708101,
    '5':  46485900,  '6':  58553888,  '7':  58169653,  '8':  44033744,
    '9':  43389635,  '10': 39686682,  '11': 51078348,  '12': 34856694,
    '13': 16000000,  '14': 16000000,  '15': 17000000,  '16': 36311158,
    '17': 22813679,  '18': 15460897,  '19': 24498980,  '20': 26436232,
    '21': 10864560,  '22': 12954788,
}

CHR_LENGTHS_GRCh38 = {
    '1':  248956422, '2':  242193529, '3':  198295559, '4':  190214555,
    '5':  181538259, '6':  170805979, '7':  159345973, '8':  145138636,
    '9':  138394717, '10': 133797422, '11': 135086622, '12': 133275309,
    '13': 114364328, '14': 107043718, '15': 101991189, '16': 90338345,
    '17': 83257441,  '18': 80373285,  '19': 58617616,  '20': 64444167,
    '21': 46709983,  '22': 50818468,
}

# ---------------------------------------------------------------------------
# Cancer gene priority set
# TSGs and oncogenes relevant to OAC / Barrett's oesophagus + general CGC members
# ---------------------------------------------------------------------------

CANCER_GENES_PRIORITY = {
    # TSGs in OAC
    'TP53', 'CDKN2A', 'SMAD4', 'ARID1A', 'PTEN', 'RB1', 'APC', 'CDH1',
    'RUNX1', 'FBXW7', 'KMT2C', 'KMT2D', 'SETD2', 'PTPRT', 'ERBB4',
    # Oncogenes in OAC
    'EGFR', 'ERBB2', 'MYC', 'KRAS', 'PIK3CA', 'CCND1', 'CDK6', 'MDM2',
    'VEGFA', 'FGFR2', 'MET', 'BCL2', 'BCL6', 'MCL1',
    # OAC-specific amplicons / chromosome landmarks
    'GATA4', 'GATA6', 'SOX9', 'CTNNA3',
    # Cell cycle
    'CDK4', 'CDK6', 'CDKN1B', 'CDKN2B', 'CCNE1',
    # Additional Barrett's / ESCC
    'SOX2', 'FHIT', 'WWOX', 'CTNNB1', 'NFE2L2', 'KEAP1',
    # General tumour suppressors
    'NF1', 'NF2', 'VHL', 'BRCA1', 'BRCA2', 'MLH1', 'MSH2',
    # chr20p context (gains recurrent in OAC)
    'PCNA', 'CDC25B', 'FOXA2', 'JAG1', 'TASP1', 'MCM8', 'CSNK2A1',
    # Extended OAC gene set
    'CCNE2', 'STK11', 'SMARCA4', 'ARID2', 'EP300', 'CREBBP',
    'RAD51', 'PALB2', 'ATM', 'CHEK2', 'CHEK1',
    # 11q amplicon (CCND1 locus)
    'FGF19', 'FGF4', 'FGF3', 'ORAOV1', 'ANO1',
    # Miscellaneous cancer genes
    'SYNE1', 'HNF1A', 'DCLK1', 'TRIM44',
}

# Human-readable labels for known non-genomic features
NON_GENOMIC_LABELS = {
    'cx': 'cx (complexity score — not a genomic locus)',
}

# ---------------------------------------------------------------------------
# Feature parsing
# ---------------------------------------------------------------------------

def parse_feature(feat):
    """Parse a CNV feature string into (chrom, start, end, ftype)."""
    m = re.match(r'^chr(\d+)([pq])$', feat)
    if m:
        chrom = m.group(1)
        arm = m.group(2)
        cen = CENTROMERES_GRCh38.get(chrom)
        chrlen = CHR_LENGTHS_GRCh38.get(chrom)
        if cen and chrlen:
            if arm == 'p':
                return chrom, 1, cen, 'arm'
            else:
                return chrom, cen, chrlen, 'arm'
    m2 = re.match(r'^chr(\d+):(\d+)-(\d+)$', feat)
    if m2:
        return m2.group(1), int(m2.group(2)), int(m2.group(3)), 'window'
    return None, None, None, 'other'

# ---------------------------------------------------------------------------
# Ensembl REST queries
# ---------------------------------------------------------------------------

def query_ensembl_genes(chrom, start, end, retries=3):
    """Return protein-coding gene names overlapping a region (<=5 Mb)."""
    url = (
        f"https://rest.ensembl.org/overlap/region/human/"
        f"{chrom}:{int(start)}-{int(end)}"
        f"?feature=gene&content-type=application/json"
    )
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            genes = [g for g in data if g.get('biotype') == 'protein_coding']
            return [g.get('external_name', g.get('gene_id', '?')) for g in genes]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 + attempt)
            else:
                return [f"ERROR:{e}"]


def query_genes_tiled(chrom, start, end, tile_size=4_900_000, delay=0.07):
    """
    Query protein-coding genes for a large region by tiling into <=5 Mb chunks.
    Deduplicates and returns a sorted list of gene names.
    """
    all_genes = set()
    pos = int(start)
    end = int(end)
    while pos < end:
        chunk_end = min(pos + tile_size, end)
        genes = query_ensembl_genes(chrom, pos, chunk_end)
        if any(g.startswith('ERROR') for g in genes):
            print(f"  Warning: tile {chrom}:{pos}-{chunk_end} -> {genes}")
        else:
            all_genes.update(genes)
        pos = chunk_end + 1
        time.sleep(delay)
    return sorted(all_genes)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_cancer_genes(all_genes_str, priority_set):
    """Return semicolon-joined cancer genes found in all_genes_str."""
    if not isinstance(all_genes_str, str) or not all_genes_str.strip():
        return ''
    return ';'.join(sorted(g for g in all_genes_str.split(';') if g in priority_set))

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    input_csv = 'reports/thesis_ch1/lgd2_cnv_feature_importance_aggregated.csv'
    out_csv = 'reports/thesis_ch1/lgd2_cnv_feature_gene_annotation.csv'
    out_full_csv = 'reports/thesis_ch1/lgd2_cnv_feature_gene_annotation_full.csv'
    out_arm_csv = 'reports/thesis_ch1/lgd2_cnv_arm_gene_summary.csv'

    df = pd.read_csv(input_csv)
    print(f"Input: {len(df)} features from {input_csv}")

    results = []
    n_total = len(df)
    errors = []

    for i, row in df.iterrows():
        feat = row['feature']
        chrom, start, end, ftype = parse_feature(feat)

        if ftype == 'other':
            # Use the canonical label from NON_GENOMIC_LABELS if known,
            # otherwise fall back to a generic descriptor.
            top_label = NON_GENOMIC_LABELS.get(feat, f'{feat} (non-genomic feature)')
            results.append({
                'feature': feat,
                'ftype': 'other',
                'n_protein_coding_genes': None,
                'all_genes': '',
                'cancer_genes': '',
                'top_cancer_genes': top_label,
            })
            continue

        if ftype == 'window':
            genes = query_ensembl_genes(chrom, start, end)
            time.sleep(0.07)
        else:  # arm
            genes = query_genes_tiled(chrom, start, end)

        error_genes = [g for g in genes if g.startswith('ERROR')]
        clean_genes = [g for g in genes if not g.startswith('ERROR')]
        if error_genes:
            errors.append((feat, error_genes))

        cancer = get_cancer_genes(';'.join(clean_genes), CANCER_GENES_PRIORITY)
        results.append({
            'feature': feat,
            'ftype': ftype,
            'n_protein_coding_genes': len(clean_genes),
            'all_genes': ';'.join(clean_genes),
            'cancer_genes': cancer,
            'top_cancer_genes': ', '.join(cancer.split(';')[:5]) if cancer else '',
        })

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{n_total} done, {len(errors)} errors so far")

    if errors:
        print(f"\nWarning: {len(errors)} features had Ensembl API errors:")
        for feat, errs in errors:
            print(f"  {feat}: {errs}")

    results_df = pd.DataFrame(results)
    final = df.merge(results_df, on='feature', how='left')

    commit_cols = [
        'overall_rank', 'feature', 'ftype',
        'importance_mean', 'importance_std', 'importance_min', 'importance_max',
        'rank_mean', 'rank_best', 'n_folds',
        'n_protein_coding_genes', 'cancer_genes', 'top_cancer_genes',
    ]

    final[commit_cols].fillna('').to_csv(out_csv, index=False, na_rep='')
    print(f"\nSaved: {out_csv}")

    final.fillna('').to_csv(out_full_csv, index=False, na_rep='')
    print(f"Saved: {out_full_csv}")

    arm_summary = final[final['ftype'] == 'arm'].sort_values('overall_rank').head(25)
    arm_summary[['overall_rank', 'feature', 'importance_mean', 'rank_mean',
                 'n_protein_coding_genes', 'cancer_genes']].fillna('').to_csv(
        out_arm_csv, index=False, na_rep=''
    )
    print(f"Saved: {out_arm_csv}")

    print("\nTop 20 by importance_mean:")
    print(final.head(20)[['overall_rank', 'feature', 'cancer_genes']].to_string(index=False))
    print(f"\nDone. {len(errors)} errors out of {n_total} features.")


if __name__ == '__main__':
    main()
