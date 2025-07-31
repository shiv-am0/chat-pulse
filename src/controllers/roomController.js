import producer from '../config/kafka.js';

export const createRoom = async (req, res) => {
  try {
    const { name } = req.body;
    
    // Produce Kafka event for room creation (persistence handled by consumer)
    await producer.send({
      topic: 'room-events',
      messages: [
        { value: JSON.stringify({ type: 'CREATE_ROOM', room: { name } }) }
      ]
    });
    
    // Return immediate response (room will be created by Kafka consumer)
    res.status(201).json({ name, status: 'Room creation initiated' });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
};