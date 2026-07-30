# DataHub quickstart sample traversal

This normalized fixture exercises Mosaic's external-catalog reader against `SampleHiveDataset`,
`SampleKafkaDataset`, and a downstream sample asset. Mosaic never creates these URNs. The fixture
contains schema, glossary/tag evidence, and column-lineage edges, plus a single-source negative
control. It is deliberately metadata-only.

Source family: DataHub's built-in quickstart sample metadata. Re-run the live acceptance command
against a local quickstart before submission:

```text
mosaic discover --server http://localhost:8080 --urn <existing-sample-urn>
```
