"""M2 semantic-dimension foundation (separate from primary M0 classification)."""

from normshift.semantic_dimensions.authority import (
    FullVerificationReceipt,
    VerifiedReportAuthority,
    VerifiedSourceBinding,
    bind_verified_report_file,
    canonical_change_sha256,
    canonical_report_sha256,
    canonical_requirement_sha256,
    create_full_verification_receipt,
    full_verification_receipt_json_bytes,
    full_verification_receipt_json_schema,
    parse_full_verification_receipt_bytes,
)
from normshift.semantic_dimensions.builder import (
    build_semantic_dimensions,
    verify_semantic_dimensions,
)
from normshift.semantic_dimensions.errors import SemanticDimensionsError
from normshift.semantic_dimensions.models import (
    DimensionDisposition,
    NormalizedTextSpan,
    ObservationVerification,
    SemanticChangeClass,
    SemanticDimension,
    SemanticDimensionsDocument,
    StructuralForm,
)
from normshift.semantic_dimensions.serialization import (
    parse_semantic_dimensions_bytes,
    semantic_dimensions_json_bytes,
    semantic_dimensions_json_schema,
)

__all__ = [
    "DimensionDisposition",
    "FullVerificationReceipt",
    "NormalizedTextSpan",
    "ObservationVerification",
    "SemanticChangeClass",
    "SemanticDimension",
    "SemanticDimensionsDocument",
    "SemanticDimensionsError",
    "StructuralForm",
    "VerifiedReportAuthority",
    "VerifiedSourceBinding",
    "bind_verified_report_file",
    "build_semantic_dimensions",
    "canonical_change_sha256",
    "canonical_report_sha256",
    "canonical_requirement_sha256",
    "create_full_verification_receipt",
    "full_verification_receipt_json_bytes",
    "full_verification_receipt_json_schema",
    "parse_semantic_dimensions_bytes",
    "parse_full_verification_receipt_bytes",
    "semantic_dimensions_json_bytes",
    "semantic_dimensions_json_schema",
    "verify_semantic_dimensions",
]
