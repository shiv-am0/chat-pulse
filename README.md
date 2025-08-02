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