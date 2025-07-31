import axios from 'axios';
import { io } from 'socket.io-client';

const API_URL = 'http://localhost:5000/api';
const SOCKET_URL = 'http://localhost:5000';

// HTTP API functions
async function createRoom(name) {
  try {
    const res = await axios.post(`${API_URL}/rooms`, { name });
    console.log('Room created:', res.data);
    return res.data;
  } catch (err) {
    console.error('Create room error:', err.response?.data || err.message);
  }
}

// Socket.IO functions
function connectSocket() {
  const socket = io(SOCKET_URL);
  
  socket.on('connect', () => {
    console.log('Connected to server');
  });
  
  socket.on('room_joined', (data) => {
    console.log('Successfully joined room:', data);
  });
  
  socket.on('user_joined', (data) => {
    console.log(`${data.username} joined the room`);
  });
  
  socket.on('user_left', (data) => {
    console.log(`${data.username} left the room`);
  });
  
  socket.on('receive_message', (data) => {
    console.log(`[${data.roomName}] ${data.username}: ${data.content}`);
  });
  
  socket.on('error', (data) => {
    console.error('Socket error:', data.message);
  });
  
  return socket;
}

function joinRoom(socket, roomName, username) {
  socket.emit('join_room', { roomName, username });
}

function sendMessage(socket, roomName, username, content) {
  socket.emit('send_message', { roomName, username, content });
}

function leaveRoom(socket, roomName, username) {
  socket.emit('leave_room', { roomName, username });
}

// Example usage
(async () => {
  // 1. Create room via HTTP
  await createRoom('general');
  
  // 2. Connect via Socket.IO
  const socket = connectSocket();
  
  // Wait for connection
  await new Promise(resolve => socket.on('connect', resolve));
  
  // 3. Join room via Socket.IO
  joinRoom(socket, 'general', 'alice');
  
  // Wait a bit then send a message
  setTimeout(() => {
    sendMessage(socket, 'general', 'alice', 'Hello, world!');
  }, 1000);
  
  // Wait a bit then leave the room
  setTimeout(() => {
    leaveRoom(socket, 'general', 'alice');
  }, 3000);
  
  // Keep the process alive for a while to see the events
  setTimeout(() => {
    socket.disconnect();
    process.exit(0);
  }, 5000);
})(); 