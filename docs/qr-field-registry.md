# QR Field Registry

_Part of the [Crispy Print documentation](README.md)._

## Purpose

Crispy Print keeps QR/document-code field definitions in a backend-owned registry file:

```text
crispy_print/qr_registry/fields.v1.json
```

This registry is the canonical allow-list for fields that may be used in QR payloads. Users do not type arbitrary document paths. They select registry-backed fields through `Crispy Document Code Profile`.

## Data Model

The registry itself is not a fixture and is not stored as editable site data. It is repo-owned JSON so changes are versioned, reviewed, and shipped with code.

User-selected fields are stored as Frappe child rows:

```text
Crispy Document Code Profile
  selected_fields -> Crispy Document Code Field
```

Each selected row stores:

- `source_doctype`
- `field_key`
- optional `output_key`
- hydrated read-only metadata: label, source path, datatype, source, purpose

The legacy `selected_fields_json` field remains hidden/read-only for compatibility and fallback behavior.

## Registry Structure

The registry has four main parts:

- `doctypes`: available QR fields by source DocType
- `authorities`: authority-specific required/optional field sets
- `business_field_sets`: reusable internal-use field bundles
- `version`: schema version for future migration

Example:

```json
{
  "version": 1,
  "doctypes": {
    "Sales Invoice": {
      "fields": {
        "company": {
          "label": "Seller Company",
          "path": "company",
          "source": "document",
          "datatype": "Link",
          "purpose": "seller_identity"
        }
      }
    }
  }
}
```

## Adding Fields

To add a selectable QR field:

1. Add the field to `crispy_print/qr_registry/fields.v1.json` under the correct DocType.
2. Include label, path, source, datatype, and purpose.
3. If relevant, add the field key to an authority required/optional list.
4. If relevant, add the field key to a business field set.
5. Run registry and document-code tests.

The backend validates every selected child row against the registry. Invalid fields fail with:

```text
Selected QR fields are not allowed for <DocType>: <field_key>
```

## Business Field Sets

Business field sets are convenience bundles for non-regulatory use cases such as inventory traceability or payment receipts. They live in the repo registry, but applying them adds normal `Crispy Document Code Field` child rows to the profile.

This keeps site configuration explicit while avoiding repetitive manual row entry.

## Authority Filtering

When a `Crispy Document Code Profile` is regulatory and links a `Crispy QR Regulatory Profile`, the selected field rows are checked against that authority's allowed field set.

For example, a ZATCA profile for `Sales Invoice` may allow `company` and `grand_total` while rejecting registry fields that are not part of the ZATCA profile.

## Migration Note

`bench migrate` is required for this change because it adds the `Crispy Document Code Field` child DocType and the `selected_fields` table field.

The post-model-sync patch:

```text
crispy_print.patches.post_model_sync.migrate_document_code_selected_fields
```

converts existing safe `selected_fields_json` values into child rows when the profile has exactly one clear target DocType from its document rules. Profiles that cannot be safely inferred keep their hidden legacy JSON fallback.

## Smoke Test

Backend smoke:

```bash
bench --site fdev.local execute crispy_print.dev_utils.qr_registry_smoke.run
```

Focused tests:

```bash
bench --site fdev.local run-tests --app crispy_print --module crispy_print.tests.qr_registry.test_loader
bench --site fdev.local run-tests --app crispy_print --module crispy_print.crispy_print.doctype.crispy_document_code_profile.test_crispy_document_code_profile
bench --site fdev.local run-tests --app crispy_print --module crispy_print.tests.api.test_document_codes
```
