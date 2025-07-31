import 'dotenv/config';
import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import { redisClient, connectRedis } from './config/redis.js';
import roomRoutes from './routes/roomRoutes.js';
import producer from './config/kafka.js';

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

// Middleware
app.use(cors());
app.use(express.json());

// API Routes
app.use('/api/rooms', roomRoutes);

// Socket.IO logic
io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  socket.on('join_room', async ({ roomName, username }) => {
    try {
      // Join the socket room
      socket.join(roomName);
      
      // Store user in Redis for room membership (no Kafka needed)
      const roomKey = `room:${roomName}:users`;
      await redisClient.sAdd(roomKey, username);
      
      // Notify others in the room
      socket.to(roomName).emit('user_joined', { username, roomName });
      
      // Send confirmation to the user
      socket.emit('room_joined', { roomName, username });
      
      console.log(`${username} joined room: ${roomName}`);
    } catch (err) {
      console.error('Join room error:', err);
      socket.emit('error', { message: 'Failed to join room' });
    }
  });

  socket.on('send_message', async ({ roomName, username, content }) => {
    try {
      // Validate user is in the room
      const roomKey = `room:${roomName}:users`;
      const isMember = await redisClient.sIsMember(roomKey, username);
      
      if (!isMember) {
        socket.emit('error', { message: 'You are not a member of this room' });
        return;
      }

      // Broadcast to all users in the room
      io.to(roomName).emit('receive_message', { username, content, roomName, timestamp: new Date() });
      
      // Produce Kafka event for persistence (only for messages, not joins)
      await producer.send({
        topic: 'message-events',
        messages: [
          { value: JSON.stringify({ type: 'SEND_MESSAGE', roomName, username, content }) }
        ]
      });
      
      console.log(`Message from ${username} in ${roomName}: ${content}`);
    } catch (err) {
      console.error('Send message error:', err);
      socket.emit('error', { message: 'Failed to send message' });
    }
  });

  socket.on('leave_room', async ({ roomName, username }) => {
    try {
      // Remove user from Redis
      const roomKey = `room:${roomName}:users`;
      await redisClient.sRem(roomKey, username);
      
      // Leave the socket room
      socket.leave(roomName);
      
      // Notify others
      socket.to(roomName).emit('user_left', { username, roomName });
      
      console.log(`${username} left room: ${roomName}`);
    } catch (err) {
      console.error('Leave room error:', err);
    }
  });

  socket.on('disconnect', async () => {
    console.log('User disconnected:', socket.id);
    // Clean up user from all rooms (optional)
    // This would require tracking which rooms the user was in
  });
});

// Redis pub/sub for cross-server message sync (if running multiple instances)
(async () => {
  await connectRedis();
  const sub = redisClient.duplicate();
  await sub.connect();
  await sub.subscribe('chat-messages', (message) => {
    const { roomName, username, content } = JSON.parse(message);
    io.to(roomName).emit('receive_message', { username, content, roomName, timestamp: new Date() });
  });
})();

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => console.log(`Server running on port ${PORT}`)); 