# Constitution: olist-analytics

1. **Reproducible from the raw files.** CSVs are pinned by SHA-256; CI rebuilds everything and
   fails if a committed export differs from the rebuild.
2. **Tested business rules.** Every rule the analysis depends on is a dbt test.
3. **Incremental must equal full.** An incremental model is only accepted with a check that,
   at every step of a replay, it is identical to a full rebuild.
4. **Stale data fails loudly.** Sources carry freshness thresholds that CI exercises, including
   the failing case.
5. **Decisions are recorded** as ADRs; superseded ones say so.
