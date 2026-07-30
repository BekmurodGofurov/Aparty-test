# Role: Guest (Student / Tenant)

The **Guest** role encompasses both unauthenticated visitors exploring the platform and registered tenants (internally referred to as *Students*) who are actively seeking housing. This role represents the demand side of the marketplace.

## Capabilities and Permissions
- **Marketplace Exploration**: Full access to browse and search the property marketplace. Unregistered guests can view listings, amenities, and pricing.
- **Smart Search & AI Assistance**: Guests utilize the platform's advanced search capabilities and AI-driven tools to find suitable roommates or available spaces based on their preferences.
- **Registration**: Guests can register and authenticate to become active tenants, utilizing pathways such as Telegram bot registration or standard web authentication.
- **Booking Workflow**: 
  - Authenticated tenants can initiate rental requests for desired properties.
  - They can track the status of their requests (pending, accepted, rejected).
- **Favorites & Reviews**: Tenants can save properties to their favorites list and, upon completing a rental lifecycle, submit reviews for properties.

## Business Domain Context
The Guest/Tenant role primarily consumes data from the "Listings" domain and initiates state changes within the "Rentals" domain. Their interactions generate the core demand signals (searches, views, requests) that drive the marketplace, requiring read-optimized access patterns and robust request-handling workflows.
