# Role: Admin

The **Admin** role represents the highest level of system authorization within the Aparty platform. Admins possess superuser capabilities and are responsible for overall system moderation, governance, and management.

## Authentication Workflow
- Admins authenticate through a dedicated, segregated login portal to protect the system's integrity.
- Standard user login flows intentionally reject admin credentials, enforcing a strict separation of access paths.

## Capabilities and Permissions
- **System Moderation**: Full access to moderate all user-generated content across the platform.
- **Listing Management**: Ability to view, approve, edit, or remove any property listing, ensuring marketplace quality.
- **User Management**: Comprehensive control over user accounts. Admins can view user profiles, manage roles, and resolve access issues.
- **Complaint Resolution**: Access to the complaints system to investigate and resolve issues reported by tenants, owners, or brokers.
- **Revenue & Payment Oversight**: Full visibility into platform revenue, subscription payments, and transactional data for auditing and financial management purposes.

## Business Domain Context
Admin workflows are fundamentally independent of how the underlying data is stored. Whether interacting with a unified database or communicating across distributed services (e.g., Identity, Listings, Payments), the Admin role is defined by its authoritative capability to query and mutate data across all business domains.
