# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [ ] Backup cũng phải ở trong lãnh thổ VN
- [ ] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training
- [ ] Có mechanism để user rút consent (Right to Erasure)
- [ ] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [ ] Có incident response plan
- [ ] Alert tự động khi phát hiện breach
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [ ] Đã bổ nhiệm Data Protection Officer
- [ ] DPO có thể liên hệ tại: privacy@medviet.vn (địa chỉ dự kiến; cần xác nhận khi bổ nhiệm)

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256 at rest, TLS 1.3 in transit | 🚧 In Progress | Infra Team |
| Audit logging | CloudTrail + immutable API access logs in an encrypted, VN-hosted S3 bucket; 365-day retention and alerts for privileged actions | 🚧 Planned | Platform Team |
| Breach detection | Prometheus rules for unusual 401/403 rates, bulk reads/exports, and latency spikes; Alertmanager pages the Security Team and starts the 72-hour incident workflow | 🚧 Planned | Security Team |

## F. Implementation plan

- **Audit logging:** Add structured middleware logs containing request ID, authenticated subject, role, resource, action, result, source IP, and timestamp. Stream logs to CloudWatch/CloudTrail and an append-only encrypted bucket hosted in Vietnam. Deny application roles permission to alter or delete audit records.
- **Breach detection:** Export authentication, authorization, and data-access counters to Prometheus. Alert through Alertmanager on repeated failed authentication, denied privileged operations, abnormal bulk access, or restricted-data export attempts; route alerts to the Security Team and preserve evidence for the NĐ13 72-hour notification process.
