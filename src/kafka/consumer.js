import 'dotenv/config';
import { Kafka } from 'kafkajs';
import connectDB from '../config/db.js';
import { createRoom } from '../services/roomService.js';
import { createMessage } from '../services/messageService.js';

(async () => {
  await connectDB();

  const kafka = new Kafka({
    clientId: 'chat-app-consumer',
    brokers: [process.env.KAFKA_BROKER || 'localhost:9092']
  });

  const consumer = kafka.consumer({ groupId: 'chat-app-group' });

  try {
    await consumer.connect();
    await consumer.subscribe({ topics: ['room-events', 'message-events'], fromBeginning: true });

    await consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        try {
          const event = JSON.parse(message.value.toString());
          
          if (event.type === 'CREATE_ROOM') {
            await createRoom(event.room.name);
            console.log('Room created:', event.room.name);
          } else if (event.type === 'SEND_MESSAGE') {
            await createMessage(event.roomName, event.username, event.content);
            console.log('Message saved:', event.username, '->', event.roomName);
          }
          // Note: JOIN_ROOM events are no longer processed here
          // Room joining is handled via Socket.IO and Redis
        } catch (err) {
          console.error('Kafka consumer error:', err);
        }
      }
    });

    console.log('Kafka consumer is running...');
  } catch (err) {
    console.error('Kafka consumer connection error:', err);
  }

  // Graceful shutdown
  const errorTypes = ['unhandledRejection', 'uncaughtException'];
  const signalTraps = ['SIGTERM', 'SIGINT', 'SIGUSR2'];

  errorTypes.forEach(type => {
    process.on(type, async e => {
      try {
        console.log(`process.on ${type}`);
        console.error(e);
        await consumer.disconnect();
        process.exit(0);
      } catch (_) {
        process.exit(1);
      }
    });
  });

  signalTraps.forEach(type => {
    process.once(type, async () => {
      try {
        await consumer.disconnect();
      } finally {
        process.kill(process.pid, type);
      }
    });
  });
})(); 