Job Market Analyzer
Overview

Job Market Analyzer is a data-driven application designed to transform job listings into structured market intelligence.

Instead of treating job searches as isolated actions, this project captures, processes, and aggregates job data to identify skill demand, market trends, and hiring patterns in real time.

The goal is to provide a reliable foundation for better technical and career decisions based on actual market signals.

Architecture

The system follows a modular, domain-oriented architecture with clear separation of concerns:

services: business logic and data processing

models: database schema and relationships

api: request handling and external interface

This structure allows the system to evolve without coupling core logic to delivery layers.

Tech Stack
Backend

Python

FastAPI
Used for building high-performance asynchronous APIs with minimal overhead.

SQLAlchemy
Provides explicit control over database interactions while maintaining flexibility.

MySQL
Relational database chosen for consistency, structured querying, and analytical capabilities.

Frontend

Next.js (React)
Enables hybrid rendering and efficient client-server interaction.

TypeScript
Ensures type safety and improves maintainability as the application scales.

TailwindCSS
Used for fast and consistent UI development.

Infrastructure

Render (backend hosting)

Vercel (frontend hosting)

GitHub (version control)

Data Modeling

The data layer is designed with a focus on:

avoiding duplication

enabling historical analysis

maintaining a lightweight structure

Core Entities

Role
Represents the primary search context (e.g., "frontend", "python").

Skill
Normalized entity reused across the system.

Company
Normalized to avoid repetition and enable future analysis.

Job
Deduplicated using a hash based on title, company, and location.

Market Snapshot
Aggregates data per day and per filter combination.
Stores job volume and number of searches.

Search Skill Stats
Captures user intent (input) by tracking which skills are being searched.

Snapshot Skills
Represents market output by storing aggregated skill frequency per snapshot.

Design Decisions
Data-Driven Approach

The system is built around collecting and structuring real market data rather than relying on assumptions.

Event-Oriented Thinking

Each user search is treated as a meaningful event that contributes to market analysis.

Selective Normalization

Critical entities such as skills and companies are normalized, while unnecessary complexity is avoided to keep the system efficient.

Deduplication Strategy

Jobs are uniquely identified using a deterministic hash to prevent redundant data storage.

Anti-Spam Control

Searches are validated using IP and time window constraints to prevent artificial data inflation.

Pragmatic MVP

The system prioritizes delivering value early while keeping the architecture flexible for incremental improvements.

Current Features

Job search with filters for:

role

location

remote/hybrid/onsite

time period

include/exclude skills

Aggregation of most frequent skills based on job results

Structured persistence of:

roles

skills

companies

jobs (deduplicated)

market snapshots

Initial foundation for market intelligence analysis

Short-Term Roadmap

Data visualization dashboard

Time-based trend analysis (skills over time)

Correlation between roles and skills

Resume vs market comparison

Positioning

This project is not intended to be just another job search interface.

It is designed as a foundation for a market intelligence system focused on developers, enabling data-informed decisions about skills, careers, and opportunities.