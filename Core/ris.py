import hashlib
import json
import time


REQUIRED_RIS_FIELDS = (
	"project_name",
	"project_purpose",
	"creation_trigger",
	"source_context",
	"user_intent_summary",
)


def capture_provenance(payload):
	"""Validate required fields and create the initial locked RIS snapshot."""
	for field_name in REQUIRED_RIS_FIELDS:
		if field_name not in payload:
			raise ValueError(f"Missing {field_name}")

	ris_payload = payload.copy()
	ris_payload["_locked"] = True
	return ris_payload


def finalize_ris(ris_payload):
	"""Attach canonical RIS metadata and deterministic hash."""
	ris_payload["ris_version"] = "1.1"
	ris_payload["timestamp"] = time.time()
	ris_payload["_hash"] = hashlib.sha256(
		json.dumps(ris_payload, sort_keys=True).encode()
	).hexdigest()
	return ris_payload
