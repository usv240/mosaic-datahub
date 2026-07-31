# Official DataHub showcase: positive convergence receipt

Captured on 2026-07-31 from a local DataHub Core quickstart that was populated with DataHub's packaged showcase e-commerce sample. Mosaic did not create the catalog asset, its schema, or its lineage.

## Environment

- DataHub server type: `quickstart`
- GMS image version: `v1.5.0.6` (`d0fce948555c06b3083479d40e8fa270d156c71f`)
- DataHub CLI: `1.6.0.6`
- Target: `urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.ORDER_ENTRY_DB.analytics.order_details,PROD)`
- Official bootstrap: [`datahub docker quickstart`](https://docs.datahub.com/)
- Lineage semantics: [DataHub lineage API tutorial](https://docs.datahub.com/docs/api/tutorials/lineage)

## Exact read-only command

```powershell
uv run mosaic discover --server http://localhost:8080 --max-hops 2 --urn "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.ORDER_ENTRY_DB.analytics.order_details,PROD)" --output evidence/external/datahub-showcase-positive-live.json
```

## Result

- `status`: `convergence`
- 55 schema fields inspected
- 17 fields classified from visible name evidence
- 3 independently represented families: financial, location, temporal
- 10 true upstream dataset URNs contributed classified column origins
- 32 dataset/column origin records retained
- data-job nodes and target self-edges excluded from the dataset count
- 0 person-level rows returned

This is a metadata screening candidate, not a privacy verdict about the showcase data and not evidence of real-world prevalence. Warehouse-side aggregate validation would still be required before a critical/elevated/low finding.

Receipt SHA-256: `e081854cd5c88828a4978b683d18d110706b2a302d11cf5101f2e1046fe696ac`.

The existing `datahub-showcase-ecommerce-live.json` remains as the single-source negative control. Together the two receipts show both sides of the fail-closed rule: Mosaic emits a convergence only when independently evidenced families and datasets clear the metadata gate.