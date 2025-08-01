#!/usr/bin/env node
import { Command } from 'commander';
import inquirer from 'inquirer';
import axios from 'axios';
import chalk from 'chalk';
import readline from 'readline';
import { io } from 'socket.io-client';

const program = new Command();
const API_URL = 'http://localhost:5000/api';
const SOCKET_URL = 'http://localhost:5000';

let socket;
let currentRoom;
let username;

// CLI setup
program
  .name('chat')
  .description('CLI for real-time chat')
  .version('1.0.0');

// Create room command (HTTP)
program
  .command('create <room>')
  .description('Create a new chat room')
  .action(async (room) => {
    try {
      const res = await axios.post(`${API_URL}/rooms`, { name: room });
      console.log(chalk.green(`✔ Room created:`), res.data.name);
    } catch (err) {
      console.error(chalk.red('✖ Failed to create room:'), err.response?.data || err.message);
    }
  });

// Join room and start interactive chat (Socket.IO only)
program
  .command('join [room] [user]')
  .description('Join an existing chat room')
  .action(async (roomArg, userArg) => {
    // Prompt for missing values
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'room',
        message: 'Room name:',
        when: () => !roomArg,
      },
      {
        type: 'input',
        name: 'username',
        message: 'Your username:',
        when: () => !userArg,
      }
    ]);
    currentRoom = roomArg || answers.room;
    username    = userArg   || answers.username;

    // Connect to Socket.IO
    socket = io(SOCKET_URL, { transports: ['websocket'] });

    // Listen for events
    socket.on('connect', () => {
      console.log(chalk.blue('🟢 Connected to server'));
      socket.emit('join_room', { roomName: currentRoom, username });
    });

    socket.on('room_joined', (data) => {
      console.log(chalk.blue(`🟢 Joined room '${data.roomName}' as ${data.username}`));
    });

    socket.on('user_joined', (data) => {
      console.log(chalk.cyan(`\n↪ ${data.username} joined`));
      rl.prompt(true);
    });

    socket.on('user_left', (data) => {
      console.log(chalk.cyan(`\n↪ ${data.username} left`));
      rl.prompt(true);
    });

    socket.on('receive_message', (data) => {
      if (data.username === username) return; // Don't echo own message
      console.log(chalk.yellow(`\n[${data.roomName}] ${data.username}:`) + ' ' + data.content);
      rl.prompt(true);
    });

    socket.on('error', (data) => {
      console.error(chalk.red('Socket error:'), data.message);
    });

    socket.on('disconnect', () => {
      console.log(chalk.red('\n⚠ Disconnected from server'));
      process.exit(0);
    });

    // Interactive readline for chat
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: chalk.green(`${username}@${currentRoom}> `),
    });

    rl.prompt();
    rl.on('line', (line) => {
      const content = line.trim();
      if (!content) { rl.prompt(); return; }
      socket.emit('send_message', { roomName: currentRoom, username, content });
      console.log(chalk.magenta(`[You]:`) + ' ' + content);
      rl.prompt();
    });

    rl.on('SIGINT', () => {
      socket.emit('leave_room', { roomName: currentRoom, username });
      console.log(chalk.red('\n👋 Leaving chat...'));
      process.exit(0);
    });
  });

program.parse(process.argv);

// Show help if no command
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
