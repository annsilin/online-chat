let userId = Math.random().toString(36).substring(2, 10); // Anonymous ID
let roomId = null;

async function joinRoom() {
    const name = document.getElementById('roomName').value;
    console.log('Attempting to join room with name:', name);
    if (!name) {
        console.error('Room name is empty');
        return;
    }
    try {
        const response = await fetch('http://localhost:5003/rooms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        if (!response.ok) {
            throw new Error(`Failed to join room: ${response.status} ${response.statusText}`);
        }
        const result = await response.json();
        console.log('Server response:', result);
        roomId = result.room_id;
        console.log('Set roomId to:', roomId);
        document.getElementById('chat').innerText = `Joined room: ${result.name}\n`;
        pollMessages();
    } catch (error) {
        console.error('Error joining room:', error);
    }
}

async function sendMessage() {
    const content = document.getElementById('message').value;
    console.log('Attempting to send message with roomId:', roomId, 'content:', content);
    if (!roomId || !content) {
        console.error('Cannot send message: Missing roomId or content', { roomId, content });
        return;
    }
    try {
        console.log('Sending message to:', `http://localhost:5003/rooms/${roomId}/messages`);
        const response = await fetch(`http://localhost:5003/rooms/${roomId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, content })
        });
        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
        }
        const result = await response.json();
        console.log('Message sent successfully:', result);
        document.getElementById('message').value = '';
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

async function pollMessages() {
    if (!roomId) {
        console.error('Cannot poll messages: Missing roomId');
        return;
    }
    try {
        const response = await fetch(`http://localhost:5003/rooms/${roomId}/messages`);
        if (!response.ok) {
            throw new Error(`Failed to fetch messages: ${response.status} ${response.statusText}`);
        }
        const messages = await response.json();
        console.log('Fetched messages:', messages);
        const chat = document.getElementById('chat');
        const existingText = chat.innerText.startsWith('Joined room') ? chat.innerText.split('\n')[0] + '\n' : '';
        chat.innerText = existingText;
        messages.forEach(msg => {
            chat.innerText += `User_${msg.user_id.slice(0, 4)}: ${msg.content}\n`;
        });
        chat.scrollTop = chat.scrollHeight;
    } catch (error) {
        console.error('Error polling messages:', error);
    }
    setTimeout(pollMessages, 1000);
}