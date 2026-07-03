package medviet.data_access

import future.keywords.if
import future.keywords.in

# Default: deny all
default allow := false

# Admin được phép tất cả
allow if {
    input.user.role == "admin"
    not restricted_export
}

# ML Engineer được đọc training data và model artifacts
allow if {
    input.user.role == "ml_engineer"
    input.resource in {"training_data", "model_artifacts"}
    input.action in {"read", "write"}
    not restricted_export
}

deny if {
    input.user.role == "ml_engineer"
    input.resource == "production_data"
    input.action == "delete"
}

allow if {
    input.user.role == "data_analyst"
    input.resource == "aggregated_metrics"
    input.action == "read"
    not restricted_export
}

allow if {
    input.user.role == "data_analyst"
    input.resource == "reports"
    input.action == "write"
    not restricted_export
}

allow if {
    input.user.role == "intern"
    input.resource == "sandbox_data"
    input.action in {"read", "write"}
    not restricted_export
}

# Rule: không ai được export restricted data ra ngoài VN servers
restricted_export if {
    input.data_classification == "restricted"
    input.destination_country != "VN"
}

deny if {
    restricted_export
}
