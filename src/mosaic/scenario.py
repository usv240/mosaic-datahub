from __future__ import annotations

from dataclasses import dataclass

HERO_URN = "urn:li:dataset:(urn:li:dataPlatform:mosaic,research_export_clean,PROD)"


@dataclass(frozen=True)
class SyntheticEstate:
    rows: tuple[dict[str, str], ...]
    column_families: dict[str, str]
    lineage: dict[str, tuple[str, ...]]
    downstream_assets: tuple[str, ...]


def build_synthetic_estate() -> SyntheticEstate:
    """Frozen fictional population. It intentionally contains no direct identifier."""
    zips = ("02139", "02140", "10001", "94110", "60601", "30301")
    genders = ("female", "male", "nonbinary")
    rows: list[dict[str, str]] = []
    for index in range(120):
        # Date/day variation makes the three-field combination identifying.  The
        # values are fictional fixture data, never presented outside aggregation.
        year = 1970 + (index % 30)
        month = 1 + ((index * 7) % 12)
        day = 1 + ((index * 11) % 28)
        rows.append(
            {
                "zip5": zips[index % len(zips)],
                "birth_date": f"{year:04d}-{month:02d}-{day:02d}",
                "gender_category": genders[index % len(genders)],
                "diagnosis_group": ("respiratory", "cardiac", "orthopedic")[index % 3],
            }
        )
    return SyntheticEstate(
        rows=tuple(rows),
        column_families={
            "zip5": "location",
            "birth_date": "date_of_birth",
            "gender_category": "demographic",
        },
        lineage={
            "zip5": (
                "support_contacts.zip5",
                "research_export_clean.zip5",
            ),
            "birth_date": (
                "support_contacts.full_birth_date",
                "research_export_clean.birth_date",
            ),
            "gender_category": (
                "member_demographics_coarse.gender_category",
                "research_export_clean.gender_category",
            ),
        },
        downstream_assets=(
            "research_partner_delivery",
            "cohort_explorer_export",
            "readmission_model_training",
        ),
    )
