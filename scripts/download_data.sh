#!/usr/bin/env bash
# Download the nine Olist CSV files into data/raw/ and verify them.
#
# The Kaggle download needs a login, so this uses a public GitHub copy of the same dataset,
# pinned to one commit. The SHA-256 list (scripts/olist_csv.sha256) proves the files are exactly
# the ones the published results were built from. To use the Kaggle files instead, put them in
# data/raw/ and skip this script.
set -euo pipefail
cd "$(dirname "$0")/.."
mirror=https://raw.githubusercontent.com/dapanew/Ecommify_Database_Design/01e7a13821c227e700ac15e464e9b53a0474c507/postgresql/seed_data
mkdir -p data/raw
while read -r _ file; do
  curl -fsSL -o "data/raw/$file" "$mirror/$file"
done < scripts/olist_csv.sha256
(cd data/raw && sha256sum --check --strict ../../scripts/olist_csv.sha256)
