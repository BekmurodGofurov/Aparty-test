# Engineering Stack

Aparty leverages a modern, high-performance technology stack designed for speed, scalability, and robust data management. Below is an overview of the current core technologies and their responsibilities within the platform.

## Backend 
- **FastAPI**: The core high-performance web framework used to build the API. It is responsible for routing, handling HTTP requests, and serving AI integrations.
- **PostgreSQL**: The primary relational database. It provides structured and reliable data storage for all core business domains, including users, listings, rentals, subscriptions, and payments.
- **Pydantic**: Utilized extensively for data validation and settings management. It enforces strict English API payloads and schemas, ensuring a robust contract between the frontend and backend.
- **Redis**: An in-memory data store responsible for ETag caching, real-time analytics, and providing high-speed data access to reduce database load.
- **RabbitMQ (via aio-pika)**: The message broker powering internal asynchronous events. It manages automated workflows, background tasks, and inter-component communication reliably.

## Frontend
- **React**: A component-based JavaScript library used for building the dynamic, interactive user interface.
- **Zustand**: A lightweight and fast state management solution. It is responsible for managing frontend stores, such as listing filters and authentication state.
- **Tailwind CSS**: A utility-first CSS framework used for rapid UI styling. It powers the platform's visually stunning design, including seamless dark/light modes and dynamic landing page animations.

## Development & Data Conventions
- **Strict English Enforcement**: All codebase variables, database schemas, states, and API payloads must strictly use English.
- **Data Population**: The platform utilizes a specialized strategy to extract and ingest listing data from Telegram advertisements, automating the growth of the marketplace.
