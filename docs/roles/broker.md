# Role: Broker (Makler)

The **Broker** (referred to internally as *Makler*) role is designed for realtors, real estate agencies, and professional property managers. Brokers typically manage a larger portfolio of properties compared to individual owners.

## Capabilities and Permissions
- **Portfolio Management**: Brokers can create, update, and manage multiple property listings on behalf of various owners or agencies.
- **Subscription & Quota Management**: Unlike standard owners, brokers often operate under subscription plans that grant specific listing limits (e.g., standard vs. premium listings). They can purchase subscriptions and manage their active listing quota.
- **Client Communications & Bookings**: Brokers act as intermediaries. They receive rental requests for their portfolio, communicate with potential tenants, and authorize the acceptance or rejection of bookings.
- **Payment Handling**: Brokers have access to manage transactional records tied to their portfolio, including subscription payments and listing promotion payments.

## Business Domain Context
The Broker role heavily interacts with the "Listings", "Rentals", "Subscriptions", and "Payments" domains. Their workflow is inherently scalable, requiring logical models that can handle batch operations, subscription usage tracking, and multi-property management seamlessly across the system architecture.
