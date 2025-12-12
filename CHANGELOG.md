# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial portfolio documentation
- Performance benchmarks and metrics
- GitHub Actions CI/CD pipeline
- Comprehensive architecture documentation

## [1.0.0] - 2024-12-11

### Added
- Multi-agent system using LangGraph
- Transaction classification with Mixtral-8x7B
- Bank reconciliation agent with fuzzy matching
- Treasury forecasting and cash flow projections
- Document parsing for CSV, OFX formats
- PostgreSQL + pgvector for embeddings
- Redis caching for embeddings
- FastAPI async backend
- React + Vite frontend
- Multi-tenancy with Row Level Security
- JWT authentication
- Human-in-the-loop workflow with agent checkpoints
- Structured logging with structlog
- Database migrations with Alembic

### Changed
- Migrated from passlib to direct bcrypt usage (Windows compatibility)
- Switched to OpenAI-compatible HuggingFace router
- Implemented lazy initialization for external clients

### Fixed
- Multi-path .env file discovery
- Indentation errors in conciliacion agent
- Missing email-validator dependency
- Redis connection pool exhaustion
- Startup time from 180s to 2s (lazy init)

### Security
- Apache License 2.0
- JWT token expiration
- Row Level Security for multi-tenancy
- Secrets management via environment variables

## [0.1.0] - 2024-11-01

### Added
- Initial project setup
- Database schema design
- Basic API structure

---

## Version History

**[1.0.0]** - Production-ready release with full documentation  
**[0.1.0]** - Initial development version

---

## Upgrade Guide

### From 0.1.0 to 1.0.0

1. **Update dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Run migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Update .env**:
   - Add `HF_TOKEN` (required)
   - Add `email-validator` is now required

4. **Database**:
   - Backup before upgrading
   - New indexes on embeddings

---

**Contributors**: Eduardo Glez-Mesones

