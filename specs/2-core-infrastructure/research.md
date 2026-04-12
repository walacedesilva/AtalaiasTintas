# Research: Sistema Core de Infraestrutura

**Date**: 2026-04-11
**Feature**: 2-core-infrastructure
**Phase**: 0 - Research & Architecture Decisions

## Technical Decisions & Research

### Authentication Strategy

**Decision**: Django's built-in authentication with custom User model extending AbstractUser
**Rationale**: 
- Provides secure password hashing (PBKDF2 by default, configurable to Argon2)
- Built-in session management with configurable timeouts
- Mature permission system that can be extended for business function roles
- Extensive security features (CSRF protection, SQL injection prevention)

**Alternatives considered**:
- JWT tokens: Rejected due to stateless nature making session timeout difficult
- OAuth2/SAML: Rejected per clarification - local user management preferred
- Custom authentication: Rejected due to security complexity

### Database Architecture

**Decision**: PostgreSQL 15 with connection pooling via PgBouncer
**Rationale**:
- ACID compliance ensures zero data loss (meets FR-003)
- Excellent Django ORM support with advanced features
- Built-in backup and point-in-time recovery capabilities
- Horizontal read replica scaling for future growth

**Alternatives considered**:
- MySQL: Good option but PostgreSQL has better JSON support for configuration storage
- SQLite: Insufficient for multi-user concurrent access requirements

### Deployment Strategy

**Decision**: Blue-Green deployment using Docker containers + Nginx load balancer
**Rationale**:
- True zero-downtime deployment (meets FR-006)
- Instant rollback by switching Nginx upstream (meets FR-007)  
- Container isolation improves reliability and consistency
- Easy to scale horizontally by adding more green environment instances

**Implementation approach**:
1. Two identical environments (blue/green) behind Nginx load balancer
2. Deploy to inactive environment while active serves traffic
3. Health check new environment before switching traffic
4. Keep previous environment ready for instant rollback

**Alternatives considered**:
- Rolling deployment: Risk of partial failure affecting users
- Canary deployment: Added complexity not justified for initial deployment

### Monitoring & Alerting

**Decision**: Custom Django monitoring app + Celery tasks + SMTP/SMS gateway integration
**Rationale**:
- Native integration with Django application for detailed insights
- Celery provides reliable background task processing for health checks
- Direct SMTP integration for email alerts (no external dependencies)
- SMS via HTTP API to provider (Twilio/AWS SNS) for critical alerts

**Key metrics monitored**:
- Database response time and connection count
- Application response time (p50, p95, p99)
- System resources (CPU, memory, disk space)
- Authentication failure rates
- Backup success/failure status

**Alert thresholds**:
- CPU usage > 80% for 5 minutes
- Memory usage > 85%
- Disk space < 10% remaining
- Database response time > 1000ms
- Authentication failure rate > 10 failures/minute from single IP

**Alternatives considered**:
- External monitoring (DataDog, New Relic): Increased cost and external dependency
- Log-based monitoring only: Too reactive, doesn't prevent issues

### Backup Strategy

**Decision**: PostgreSQL pg_dump daily backups + WAL-E for continuous archiving
**Rationale**:
- Meets 90-day retention requirement with automated cleanup
- 30-minute RTO achievable with streaming replication standby
- 1-hour RPO met through WAL (Write Ahead Log) continuous archiving
- Encrypted backups stored in multiple locations

**Backup schedule**:
- Full backup: Daily at 2 AM local time
- WAL archiving: Continuous (every 16MB or 1 minute)
- Retention: 90 days (automatic cleanup)
- Storage: Local + cloud storage for disaster recovery

**Recovery procedures**:
1. **Point-in-time recovery**: Restore from base backup + replay WAL files
2. **Emergency failover**: Promote streaming replica to master (< 30 seconds)
3. **Full disaster recovery**: Restore from cloud backup (< 30 minutes)

### Session Management

**Decision**: Redis for session storage with database fallback
**Rationale**:
- High performance for session operations
- Built-in expiration handling (8-hour timeout per requirement)
- Graceful degradation to database sessions if Redis fails
- Distributed session sharing ready for multiple server scaling

**Session security**:
- Secure session cookies (HttpOnly, Secure, SameSite)
- Session rotation on login/privilege escalation
- IP binding and User-Agent validation for session hijacking prevention

### Performance Architecture

**Decision**: Django + Gunicorn + Nginx + Redis caching
**Rationale**:
- Nginx serves static files and terminates SSL
- Gunicorn provides multi-worker WSGI application server
- Redis caches frequent database queries and session data
- Django ORM with select_related/prefetch_related optimization

**Performance targets**:
- API endpoints: < 200ms p95 response time
- Database queries: < 100ms average
- Static assets: < 50ms with proper caching headers
- Concurrent users: 50 simultaneous without degradation

**Scaling strategy**:
- Vertical scaling: Increase server resources
- Horizontal scaling: Add load-balanced application servers
- Database scaling: Read replicas for reporting queries
- Caching: Redis cluster for high-availability caching

## Development Workflow

**Local development environment**:
- Docker Compose for consistent developer setup
- PostgreSQL and Redis containers
- Hot reload for development efficiency
- Pre-commit hooks for code quality

**CI/CD Pipeline**:
1. **Code commit** → Automated tests (unit + integration)
2. **Tests pass** → Build Docker images  
3. **Security scan** → Check for vulnerabilities
4. **Deploy staging** → Blue-green deployment to staging environment
5. **Manual approval** → Deploy to production via same process

**Quality gates**:
- 90%+ test coverage requirement
- Security vulnerability scan (Bandit, Safety)
- Code style enforcement (Black, isort, flake8)
- Performance regression testing