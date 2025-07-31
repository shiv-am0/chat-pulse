// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the chat-app database
db = db.getSiblingDB('chat-app');

// Create collections with proper indexes
db.createCollection('rooms');
db.createCollection('messages');
db.createCollection('users');

// Create indexes for better performance
db.rooms.createIndex({ "name": 1 }, { unique: true });
db.messages.createIndex({ "room": 1, "createdAt": 1 });
db.messages.createIndex({ "user": 1 });
db.users.createIndex({ "username": 1 }, { unique: true });

// Insert some sample data (optional)
db.rooms.insertOne({
  name: "general",
  createdAt: new Date()
});

db.users.insertOne({
  username: "system",
  createdAt: new Date()
});

print("MongoDB initialization completed successfully!");
print("Database: chat-app");
print("Collections: rooms, messages, users");
print("Indexes created for optimal performance"); 