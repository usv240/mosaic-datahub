# DataHub quickstart sample traversal

These fixtures cover two kinds of external-catalog evidence:

- the normalized contract fixture exercises schema, glossary/tag evidence, and positive and negative column-lineage cases;
- the official `bootstrap` and `showcase-ecommerce` recipes ingest DataHub-authored packs into a real quickstart that Mosaic did not create.

The live acceptance run used DataHub Core `v1.5.0.6` and the DataHub CLI `1.6.0.16`:

```powershell
datahub docker quickstart
docker run --rm --add-host host.docker.internal:host-gateway -e DATAHUB_GMS_URL=http://host.docker.internal:8080 -v "<repository-root>:/work" -w /work ghcr.io/astral-sh/uv:python3.11-bookworm-slim uvx --from "acryl-datahub[demo-data]" datahub ingest -c fixtures/datahub_sample_recording/showcase-ecommerce-recipe.yml

uv run mosaic discover --server http://localhost:8080 --urn "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.order_items,PROD)" --max-hops 1 --output evidence/external/datahub-showcase-ecommerce-live.json
```

The official asset contained 11 fields, three classified fields across temporal and health families, and one independently evidenced Snowflake upstream. Mosaic returned `no_convergence` because its two-upstream requirement was not met. That is the intended fail-closed result: the reader reports what it saw and never manufactures a graph finding. No person-level rows were queried.
