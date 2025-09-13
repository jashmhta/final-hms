package hms

default allow = true

# Example RBAC: only specific roles can call billing discount endpoint
allow {
  input.path == "/api/billing/bills/set_discount"
  input.role == "SUPER_ADMIN"
}
allow {
  input.path == "/api/billing/bills/set_discount"
  input.role == "HOSPITAL_ADMIN"
}
allow {
  input.path == "/api/billing/bills/set_discount"
  input.role == "BILLING_CLERK"
}
