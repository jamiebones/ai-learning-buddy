# AI Learning Buddy

A full-stack application featuring an intelligent learning assistant with chat capabilities, note management, and retrieval-augmented generation (RAG) technology powered by Lilypad Anura API which provides personalized learning experiences.

## Overview

AI Learning Buddy combines a modern NextJS frontend with a powerful Python backend to create an interactive learning platform. The application uses advanced AI technologies to understand and respond to user queries, organize learning materials, and enhance the learning experience through contextual information retrieval.

## Architecture

### Frontend
- **Framework**: Next.js
- **Language**: TypeScript/JavaScript
- **UI Components**: React components with modern styling
- **State Management**: Context API with hooks
- **API Communication**: Axios for backend communication

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML Stack**:
  - LangChain for AI application workflows
  - Sentence Transformers & HuggingFace for embeddings and NLP
  - ChromaDB for vector storage
  - PyTorch (v2.0+) for deep learning operations
- **Authentication**: JWT-based authentication

### Infrastructure
- **Containerization**: Docker with Docker Compose
- **Development**: Hot-reloading for both frontend and backend
- **Database Migrations**: Alembic for database schema changes

## Features

- **User Authentication**: Secure login/registration system
- **Interactive Chat**: AI-powered conversational interface
- **Note Management**: Create, edit, organize, and search through learning notes
- **Document Processing**: Handle PDF and Word documents for knowledge extraction
- **Retrieval-Augmented Generation**: Enhance AI responses with relevant context from user notes
- **Vector Search**: Semantic search capabilities for finding relevant information

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository
- API keys for Lilypad Anura API. Get your free API TOKEN https://anura.lilypad.tech 

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jamiebones/ai-learning-buddy.git
   cd ai-learning-buddy
   ```

2. **Environment Setup**
   Create a `.env` file in the project root with necessary variables:
   ```
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=learning_buddy
   
   # Backend
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   SECRET_KEY
   REFRESH_TOKEN_SECRET
   
   # AI Services 
   LILYPAD_API_TOKEN

   
   # Frontend
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start the application**
   ```bash
   docker compose up build -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Development

### Project Structure

```
ai-learning-buddy/
├── frontend/               # Next.js frontend application
│   ├── src/                # Source directory
│   │   ├── app/            # App Router based pages and layouts
│   │   │   ├── (auth)/     # Authentication route group
│   │   │   ├── dashboard/  # Dashboard pages
│   │   │   ├── api/        # API route handlers
│   │   │   ├── layout.tsx  # Root layout
│   │   │   └── page.tsx    # Home page
│   │   ├── components/     # Reusable React components
│   │   ├── lib/            # Utility functions and shared code
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript type definitions
│   │   └── styles/         # Global styles and CSS modules
│   ├── public/             # Static assets
│   ├── Dockerfile          # Frontend Docker configuration
│   └── package.json        # Frontend dependencies
│
├── backend/                # FastAPI backend application
│   ├── app/                # Main application code
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   └── main.py         # Application entry point
│   ├── migrations/         # Database migrations
│   ├── Dockerfile.dev      # Backend Docker configuration
│   └── requirements.txt    # Python dependencies
│
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # Project documentation
```

### Running in Development Mode

The Docker Compose setup includes development-friendly features:
- Hot reloading for both frontend and backend
- Volume mounts for code changes
- Development-specific optimizations



### Troubleshooting

#### Backend Package Issues

If encountering errors with specific Python packages:

1. **NumPy/PyTorch compatibility**: The backend requires `numpy<2.0` and `torch>=2.0.0`
2. **BuildKit cache**: The backend Dockerfile uses BuildKit cache mounts for faster rebuilds

For Docker Compose V1 users:
```bash
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
docker-compose up --build
```

#### Database Migrations

If database schema changes are needed:
```bash
docker compose exec backend alembic upgrade head
```

## API Documentation


Key API endpoints include:
- Authentication: `/api/auth/*`
- Chat functionality: `/api/chat/*`
- Note management: `/api/notes/*`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

