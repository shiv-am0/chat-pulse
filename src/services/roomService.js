import Room from '../models/Room.js';

async function createRoom(name) {
  const room = new Room({ name });
  return await room.save();
}

async function getRoomByName(name) {
  return await Room.findOne({ name });
}

export { createRoom, getRoomByName }; 