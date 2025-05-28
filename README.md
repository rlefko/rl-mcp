# 🚀 RL-MCP: Ryan's Model Context Protocol Server

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)

> 🎯 **A powerful, scalable Model Context Protocol (MCP) server built with modern Python technologies**

## 🌟 What is RL-MCP?

RL-MCP is a robust **Model Context Protocol server** designed to provide AI models with structured access to external data and services. Think of it as a bridge 🌉 that allows AI assistants to interact with your applications, databases, and APIs in a standardized, secure way.

### 🎪 Current Features

- 🔐 **Secure Authentication** - Built-in auth system to protect your endpoints
- 📊 **RESTful API** - Clean, well-documented API endpoints with FastAPI
- 🗄️ **PostgreSQL Integration** - Robust database layer with SQLModel/SQLAlchemy
- 🐳 **Docker Ready** - Fully containerized development and deployment
- 🔄 **Database Migrations** - Alembic-powered schema management
- 📈 **Health Monitoring** - Built-in health checks and connection monitoring
- 🎨 **Interactive Docs** - Auto-generated API documentation
- 🛠️ **Development Tools** - Pre-commit hooks, linting, and formatting

### 🚀 Future Vision

This MCP server is designed to be the **foundation** for AI-powered applications that need:

- 🤖 **AI Model Integration** - Seamless connection between AI models and your data
- 🔌 **Plugin Architecture** - Extensible system for adding new capabilities
- 📡 **Real-time Communication** - WebSocket support for live data streaming
- 🌐 **Multi-tenant Support** - Serve multiple clients with isolated data
- 🔍 **Advanced Search** - Vector search and semantic querying capabilities
- 📊 **Analytics Dashboard** - Monitor usage, performance, and insights

## 🛠️ Technology Stack

- **🐍 Backend**: Python 3.12 + FastAPI
- **🗄️ Database**: PostgreSQL with SQLModel
- **🐳 Containerization**: Docker + Docker Compose
- **🔄 Migrations**: Alembic
- **🧪 Code Quality**: Black, isort, pylint, pre-commit hooks
- **📚 Documentation**: Auto-generated OpenAPI/Swagger docs

## 🚀 Quick Start

### Prerequisites

- 🐳 Docker and Docker Compose
- 🐍 Python 3.12+ (for local development)
- 🍺 Homebrew (macOS) or equivalent package manager

### 🎯 One-Command Setup

Get up and running in seconds! Our setup script handles everything:

```bash
make setup-environment
```

This magical command will:
- 🔧 Install all required dependencies
- 🐍 Create and configure a Python virtual environment
- 🐳 Set up Docker containers
- 📦 Install all Python packages
- ✅ Verify everything is working

### 🏃‍♂️ Running the Application

#### 🐳 Docker Development (Recommended)

```bash
# Build and start all services
make up

# Or run in background
docker compose up -d
```

Your services will be available at:
- 🌐 **API Server**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🗄️ **Database Admin**: http://localhost:8080 (Adminer)

#### 🐍 Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Start the api and db at port 8000
make up
```

## 📖 API Documentation

Once running, explore the interactive API documentation:

- **📊 Swagger UI**: http://localhost:8000/docs
- **📋 ReDoc**: http://localhost:8000/redoc
- **🔍 OpenAPI Spec**: http://localhost:8000/openapi.json

### 🔑 Authentication

All API endpoints require authentication. Include your auth token in requests:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/v1/item
```

## 🗄️ Database Management

### 🔄 Creating Migrations

When you modify database models:

```bash
MSG="Add new awesome feature" make migration
```

### 🏗️ Database Commands

```bash
# Start the api and db at port 8000
make up

# Check database health
curl http://localhost:8000/health
```

## 🛠️ Development Workflow

### 📦 Managing Dependencies

```bash
# Regenerate requirements.txt with latest versions
make regen-requirements
```

### 🧹 Cleanup

```bash
# Remove all containers and volumes
make clean
```

### 🔍 Code Quality

Pre-commit hooks automatically run:
- 🎨 **Black** - Code formatting
- 📋 **isort** - Import sorting  
- 🔍 **Pylint** - Code linting

## 🏗️ Project Structure

```
rl-mcp/
├── 📁 app/                    # Main application code
│   ├── 📁 api/               # API layer
│   │   └── 📁 v1/           # API version 1
│   │       ├── 📁 base/     # Base models and tables
│   │       └── 📁 item/     # Item management endpoints
│   ├── 📁 databases/        # Database configuration
│   └── 📄 main.py          # Application entry point
├── 📁 docker/               # Docker configurations
├── 📁 migrations/           # Database migrations
├── 📁 scripts/             # Utility scripts
├── 📁 utilities/           # Helper utilities
└── 📄 Makefile            # Development commands
```

## 🤝 Contributing

We welcome contributions! 🎉

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. ✨ Make your changes
4. 🧪 Run tests and linting
5. 📝 Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

Having issues? 🤔

- 📖 Check the [API Documentation](http://localhost:8000/docs)
- 🐛 Open an [Issue](https://github.com/rlefko/rl-mcp/issues)
- 💬 Start a [Discussion](https://github.com/rlefko/rl-mcp/discussions)

---

<div align="center">

**🚀 Built with ❤️ for the future of AI-powered applications**

*Ready to revolutionize how AI models interact with your data? Let's build something amazing together!* ✨

</div>
