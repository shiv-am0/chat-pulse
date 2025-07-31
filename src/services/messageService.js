import Message from '../models/Message.js';
import Room from '../models/Room.js';
import User from '../models/User.js';

async function createMessage(roomName, username, content) {
  const room = await Room.findOne({ name: roomName });
  if (!room) throw new Error('Room not found');
  let user = await User.findOne({ username });
  if (!user) user = await User.create({ username });
  const message = new Message({ room: room._id, user: user._id, content });
  return await message.save();
}

async function getMessagesByRoom(roomName) {
  const room = await Room.findOne({ name: roomName });
  if (!room) throw new Error('Room not found');
  return await Message.find({ room: room._id }).populate('user').sort({ createdAt: 1 });
}

export { createMessage, getMessagesByRoom }; 