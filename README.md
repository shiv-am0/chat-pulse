# Real-Time Chat Application

A modern, scalable real-time chat application built with Node.js, featuring real-time messaging, event-driven architecture, and comprehensive monitoring.

## 🚀 Features

- **Real-time messaging** with Socket.IO
- **Event-driven architecture** using Apache Kafka
- **In-memory caching** with Redis for room membership
- **Persistent storage** with MongoDB
- **Microservices-like architecture** with separated concerns
- **Comprehensive monitoring** with multiple UIs
- **Docker Compose** for easy development setup
- **Scalable design** ready for production deployment

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Main Server   │    │  Kafka Consumer │
│                 │    │                 │    │                 │
│ • Socket.IO     │◄──►│ • Express API   │───►│ • Data Persist  │
│ • HTTP Client   │    │ • Socket.IO     │    │ • MongoDB Ops   │
│ • Web UI        │    │ • Kafka Prod    │    │ • Event Process │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Infrastructure│
                       │                 │
                       │ • MongoDB       │
                       │ • Redis         │
                       │ • Kafka         │
                       │ • Zookeeper     │
                       └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Node.js, Express.js
- **Real-time**: Socket.IO
- **Database**: MongoDB
- **Cache**: Redis
- **Message Broker**: Apache Kafka
- **Containerization**: Docker & Docker Compose
- **Monitoring**: RedisInsight, Kafka UI, Mongo Express

## 📋 Prerequisites

- Node.js (v16 or higher)
- Docker & Docker Compose
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd real-time-chat-app-cli
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Set Up Environment Variables
```bash
# Copy the example environment file
cp env.example .env

# Edit .env file if needed (defaults work for local development)
```

### 4. Start Infrastructure Services
```bash
# Start all services with Docker Compose
docker compose up -d

# This will start:
# - MongoDB (port 27017)
# - Redis Stack (port 6379) + RedisInsight UI (port 8001)
# - Zookeeper (port 2181)
# - Kafka (port 9092) + Kafka UI (port 8080)
# - Mongo Express (port 8081)
```

### 5. Start the Application

**Terminal 1 - Main Server:**
```bash
npm run dev
# or
node src/index.js
```

**Terminal 2 - Kafka Consumer:**
```bash
npm run consumer
# or
node src/kafka/consumer.js
```

### 6. Make your client script executable
```bash
chmod +x client.js
```
### 7. Link it globally (for development)
```bash
npm link
```

### 8. Test the Application
```bash
# Run the test client
npm run client
# or
node client.js
```

## 📊 Monitoring UIs

| Service | URL | Purpose |
|---------|-----|---------|
| MongoDB UI | `http://localhost:8081` | Database monitoring |
| RedisInsight | `http://localhost:8001` | Redis monitoring |
| Kafka UI | `http://localhost:8080` | Kafka monitoring |

## 🔧 API Endpoints

- `POST /api/rooms` - Create a room

## 🔌 Socket.IO Events

### Client → Server
- `join_room` - Join a room
- `send_message` - Send a message
- `leave_room` - Leave a room

### Server → Client
- `room_joined` - Confirmation of room joining
- `user_joined` - User joined notification
- `user_left` - User left notification
- `receive_message` - New message received
- `error` - Error notifications

## 🐳 Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker compose down -v

# Restart a specific service
docker compose restart mongodb

# View running containers
docker compose ps
```

## 📁 Project Structure

```
real-time-chat-app-cli/
├── src/
│   ├── config/          # Configuration files
│   │   ├── db.js        # MongoDB connection
│   │   ├── redis.js     # Redis connection
│   │   └── kafka.js     # Kafka producer
│   ├── controllers/     # HTTP controllers
│   │   └── roomController.js
│   ├── models/          # MongoDB models
│   │   ├── Room.js
│   │   ├── Message.js
│   │   └── User.js
│   ├── routes/          # Express routes
│   │   └── roomRoutes.js
│   ├── services/        # Business logic
│   │   ├── roomService.js
│   │   └── messageService.js
│   ├── kafka/           # Kafka consumer
│   │   └── consumer.js
│   └── index.js         # Main server
├── client.js            # Test client
├── docker-compose.yml   # Infrastructure services
├── mongo-init.js        # MongoDB initialization
├── package.json
└── README.md
```

## 🔍 Development

### Environment Variables
```bash
# Server Configuration
PORT=5000
NODE_ENV=development

# MongoDB Database Configuration
MONGO_URI=mongodb://admin:password@localhost:27017/chat-app?authSource=admin

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Kafka Configuration
KAFKA_BROKER=localhost:9092

# Optional: JWT Secret
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
```

### Testing with Postman
1. **Create room**: `POST http://localhost:5000/api/rooms`
2. **Socket.IO connection**: `ws://localhost:5000`
3. **Test events**: `join_room`, `send_message`, `leave_room`

## 🚀 Production Deployment

For production deployment, consider:
- Using managed services (MongoDB Atlas, Redis Cloud, Confluent Cloud)
- Setting up proper authentication and authorization
- Implementing rate limiting and security measures
- Using environment-specific configurations
- Setting up monitoring and logging

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or issues, please open an issue on GitHub.

## Features
- REST API for creating/joining rooms and sending messages
- Real-time messaging with Socket.IO
- Redis pub/sub for message sync
- Kafka for event streaming
- MongoDB for persistent storage
- Modular codebase (controllers, services, routes, utils)

## Project Structure
```
real-time-chat-app-cli/
  ├── src/
  │   ├── controllers/
  │   ├── models/
  │   ├── routes/
  │   ├── services/
  │   ├── utils/
  │   ├── config/
  │   ├── kafka/
  │   └── index.js
  ├── client.js
  ├── package.json
  └── README.md
```

## Setup
1. Install dependencies:
   ```bash
   npm install
   ```
2. Start MongoDB, Redis, and Kafka locally (see their docs for setup).
3. Start the main server:
   ```bash
   npm run dev
   ```
4. Start the Kafka consumer (in a separate terminal):
   ```bash
   npm run consumer
   ```
5. Use `client.js` or Postman to test APIs.

## Environment Variables
1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Update the `.env` file with your configuration:
   ```bash
   # Server Configuration
   PORT=5000
   NODE_ENV=development

   # MongoDB Database Configuration
   MONGO_URI=mongodb://localhost:27017/chat-app

   # Redis Configuration
   REDIS_URL=redis://localhost:6379

   # Kafka Configuration
   KAFKA_BROKER=localhost:9092

   # Optional: JWT Secret (if you plan to add authentication later)
   JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
   ```

### Prerequisites
Before running the application, make sure you have the following services running:

#### Option 1: Using Docker Compose (Recommended)
The easiest way to set up all required services is using Docker Compose:

```bash
# Start all services with Docker Compose
docker-compose up -d

# This will start:
# - MongoDB (port 27017)
# - Redis Stack (port 6379) + RedisInsight UI (port 8001)
# - Zookeeper (port 2181)
# - Kafka (port 9092) + Kafka UI (port 8080)
```

#### Option 2: Manual Setup
If you prefer to run services manually:

1. **MongoDB** - Database for persistent storage
   ```bash
   # Install MongoDB or use Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

2. **Redis** - In-memory storage for room membership
   ```bash
   # Install Redis or use Docker
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

3. **Kafka** - Message broker for event streaming
   ```bash
   # Install Kafka or use Docker Compose
   # You'll need Zookeeper and Kafka running
   ```

### Docker Compose Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete all data)
docker-compose down -v

# Restart a specific service
docker-compose restart mongodb

# View running containers
docker-compose ps
```

### Development UIs
The Docker Compose setup includes monitoring UIs for development:

- **MongoDB UI (Mongo Express)**: `http://localhost:8081`
  - Browse databases, collections, and documents
  - View chat messages and room data
  - Execute MongoDB queries
  - **Login**: admin / password

- **Redis Stack UI (RedisInsight)**: `http://localhost:8001`
  - Monitor Redis keys, memory usage, and performance
  - View room membership data in real-time
  - Execute Redis commands directly

- **Kafka UI**: `http://localhost:8080`
  - Monitor Kafka topics, messages, and consumers
  - View message events in real-time
  - Manage topics and partitions

### Service Ports

| Service | Port | Purpose | UI |
|---------|------|---------|----|
| MongoDB | 27017 | Database | - |
| Mongo Express | 8081 | MongoDB monitoring | ✅ |
| Redis Stack | 6379 | Cache/Room membership | - |
| RedisInsight | 8001 | Redis monitoring | ✅ |
| Zookeeper | 2181 | Kafka coordination | - |
| Kafka | 9092 | Message broker | - |
| Kafka UI | 8080 | Kafka monitoring | ✅ |

### What to Monitor in Development

#### Mongo Express (http://localhost:8081)
- **Database**: `chat-app`
- **Collections**: `rooms`, `messages`, `users`
- **Documents**: View chat messages, room data, and user information
- **Queries**: Execute MongoDB queries to analyze data

#### RedisInsight (http://localhost:8001)
- **Room Membership**: Look for keys like `room:general:users`
- **Memory Usage**: Monitor Redis memory consumption
- **Commands**: Execute Redis commands to debug room membership

#### Kafka UI (http://localhost:8080)
- **Topics**: `room-events` and `message-events`
- **Messages**: View real-time message events
- **Consumers**: Monitor the `chat-app-group` consumer
- **Partitions**: Check topic partitioning and offsets

## API Endpoints
- `POST /api/rooms` - Create a room

## Socket.IO Events
- `join_room` - Join a room (real-time)
- `send_message` - Send a message (real-time)
- `leave_room` - Leave a room (real-time)

## Socket.IO Event Listeners
- `room_joined` - Confirmation of room joining
- `user_joined` - Notification when user joins room
- `user_left` - Notification when user leaves room
- `receive_message` - Receive messages in real-time
- `error` - Error notifications

## License
MIT 