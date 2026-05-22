# Zava AI Portal - Hackathon Starter

Welcome to the **Zava AI Portal** hackathon starter project!

## 🎯 Your Mission

This is an **evolving starter project** that you'll progressively build throughout all hackathon challenges. Use **GitHub Copilot** to complete each challenge, building upon the previous foundation.

**Challenge 1**: Build the core AI-powered application (FastAPI, MCP, Azure OpenAI)  
**Challenge 2**: Add GitHub automation workflows (issues, PRs, AI review)  
**Challenge 3**: Secure deployments with OIDC and Azure  
**Challenge 4**: Production deployment with GitHub Actions  

The architecture is predefined—use Copilot to generate the implementations!

## 📁 Project Structure

This starter preserves the exact architecture of the full Zava application but removes core implementations. Your task is to use Copilot to fill in the TODOs across all challenges.

```
hackathon-starter/
├── backend/
│   ├── api/v1/endpoints/    # API endpoints (health, agents)
│   ├── core/                # Config & database
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── main.py              # FastAPI app
├── mcp_server/              # AI service with Azure OpenAI
│   ├── server.py
│   └── requirements.txt
├── frontend/                # Static web UI
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── .github/workflows/       # GitHub Actions (Challenge 2+)
│   ├── issue-automation.yml
│   └── pr-automation.yml
├── .env.example
├── .env.github-example      # GitHub automation config (Challenge 2)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🚀 Progressive Challenges

### Challenge 1: AI-Powered Development (Core Foundation)
- FastAPI backend with async database
- MCP Server with Azure OpenAI
- Agent CRUD endpoints
- Docker Compose setup

### Challenge 2: Agentic Workflows on GitHub.com
- GitHub automation service (builds on Challenge 1 agents)
- Issue analysis and auto-labeling
- PR code review automation
- GitHub Actions workflows

### Challenge 3: Secure Deployments
- OIDC authentication
- Azure deployment configurations
- Security best practices

### Challenge 4: Production CI/CD
- GitHub Actions deployment pipeline
- Azure App Service deployment
- Production monitoring

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Docker & Docker Compose
- VS Code with GitHub Copilot extension
- Azure OpenAI access (endpoint & API key)

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure OpenAI credentials
```

### 3. Follow the Challenge Guides

Start with Challenge 1 and progress sequentially:
- `../challenge-1-guide.md` - Core application foundation
- `../challenge-2-guide.md` - GitHub automation workflows
- More challenges to come...

## 📚 Key TODOs

Each file contains detailed TODO comments with:
- **What** needs to be implemented
- **Copilot prompts** to use
- **Expected outcomes**

Start with these files in order:
1. `backend/core/config.py` - Configuration
2. `backend/core/database.py` - Database setup
3. `backend/models/agent.py` - Data models
4. `backend/schemas/agent.py` - Request/response schemas
5. `backend/services/mcp_service.py` - MCP integration
6. `backend/api/v1/endpoints/health.py` - Health check
7. `backend/api/v1/endpoints/agents.py` - Agent endpoints
8. `backend/api/v1/router.py` - Router setup
9. `backend/main.py` - FastAPI application
10. `mcp_server/server.py` - Azure OpenAI integration
11. `requirements.txt` - Dependencies
12. `docker-compose.yml` - Container orchestration

## 🎓 Learning Objectives

By completing this challenge, you'll learn to:
- Use GitHub Copilot Chat for scaffolding
- Generate FastAPI endpoints with AI assistance
- Create SQLAlchemy models via Copilot
- Implement Azure OpenAI integration
- Build MCP (Model Context Protocol) servers
- Use Copilot for Dockerfiles and configuration

## ✅ Success Criteria

Your implementation is complete when:
- ✅ FastAPI backend starts without errors
- ✅ MCP server connects to Azure OpenAI
- ✅ Database models are created
- ✅ Health check endpoint responds
- ✅ Agent CRUD endpoints work
- ✅ Docker Compose runs all services
- ✅ Frontend displays and calls backend

## 🆘 Need Help?

- Check the TODO comments in each file
- Use the Copilot prompts provided
- Refer to the challenge guide for detailed steps
- Compare with reference solution (after attempting!)

Good luck! 🚀
