import { Kafka } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'chat-app',
  brokers: [process.env.KAFKA_BROKER || 'localhost:9092']
});

const producer = kafka.producer();

// Initialize producer
const initProducer = async () => {
  try {
    await producer.connect();
    console.log('Kafka Producer is connected and ready.');
  } catch (err) {
    console.error('Kafka Producer connection error:', err);
  }
};

// Initialize on import
initProducer();

export default producer; 