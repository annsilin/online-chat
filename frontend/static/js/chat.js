let userId = localStorage.getItem('userId') || generateUUID();
localStorage.setItem('userId', userId);
let roomId = null;
let lastNotificationId = 0; // Track the last processed notification
let isOnline = false; // Track current presence status

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        let r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

async function checkPresence() {
    try {
        const response = await fetch(`http://localhost:5004/presence/${userId}`);
        if (response.ok) {
            const presence = await response.json();
            isOnline = presence.status === 'online';
            updateStatusButton();
        } else {
            isOnline = false; // Assume offline if not found
            updateStatusButton();
        }
    } catch (error) {
        console.error('Error checking presence:', error);
        isOnline = false;
        updateStatusButton();
    }
}

function updateStatusButton() {
    const button = document.getElementById('statusToggle');
    button.innerText = isOnline ? 'Go Offline' : 'Go Online';
}

async function toggleStatus() {
    try {
        if (isOnline) {
            const response = await fetch(`http://localhost:5004/presence/${userId}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error(`Failed to set offline: ${response.status} ${response.statusText}`);
            }
            isOnline = false;
            console.log('User set to offline');
        } else {
            const response = await fetch(`http://localhost:5004/presence/${userId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ status: 'online' })
            });
            if (!response.ok) {
                throw new Error(`Failed to set online: ${response.status} ${response.statusText}`);
            }
            isOnline = true;
            console.log('User set to online');
        }
        updateStatusButton();
    } catch (error) {
        console.error('Error toggling status:', error);
    }
}

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
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        if (!response.ok) {
            throw new Error(`Failed to join room: ${response.status} ${response.statusText}`);
        }
        const result = await response.json();
        console.log('Server response:', result);
        roomId = result.room_id;
        console.log('Set roomId to:', roomId);
        document.getElementById('chatSection').classList.remove('hidden');
        document.getElementById('chat').innerText = `Joined room: ${result.name}\n`;
        // Set user to online
        await fetch(`http://localhost:5004/presence/${userId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ status: 'online' })
        });
        isOnline = true;
        updateStatusButton();
        pollMessages();
    } catch (error) {
        console.error('Error joining room:', error);
    }
}

async function sendMessage() {
    const content = document.getElementById('message').value;
    console.log('Attempting to send message with roomId:', roomId, 'content:', content);
    if (!roomId || !content) {
        console.error('Cannot send message: Missing roomId or content', {roomId, content});
        return;
    }
    try {
        console.log('Sending message to:', `http://localhost:5003/rooms/${roomId}/messages`);
        const response = await fetch(`http://localhost:5003/rooms/${roomId}/messages`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId, content})
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
        const [messagesResponse, notificationsResponse] = await Promise.all([
            fetch(`http://localhost:5003/rooms/${roomId}/messages`),
            fetch(`http://localhost:5006/notifications/${userId}`)
        ]);

        if (!messagesResponse.ok) {
            throw new Error(`Failed to fetch messages: ${messagesResponse.status} ${messagesResponse.statusText}`);
        }
        if (!notificationsResponse.ok) {
            throw new Error(`Failed to fetch notifications: ${notificationsResponse.status} ${notificationsResponse.statusText}`);
        }

        const messages = await messagesResponse.json();
        const notifications = await notificationsResponse.json();
        console.log('Fetched messages:', messages);
        console.log('Fetched notifications:', notifications);

        const chat = document.getElementById('chat');
        const existingText = chat.innerText.startsWith('Joined room') ? chat.innerText.split('\n')[0] + '\n' : '';
        chat.innerText = existingText;

        // Display messages
        messages.forEach(msg => {
            chat.innerText += `User_${msg.user_id.slice(0, 4)}: ${msg.content}\n`;
        });

        // Handle notifications
        const newNotifications = notifications.filter(notif => notif.id > lastNotificationId);
        if (newNotifications.length > 0) {
            lastNotificationId = Math.max(...newNotifications.map(notif => notif.id));

            // Request permission for browser notifications if not already granted
            if (Notification.permission !== 'granted') {
                await Notification.requestPermission();
            }

            // Play sound and show browser notification
            const audio = new Audio('/static/notification.mp3');
            audio.play().catch(err => console.error('Error playing sound:', err));

            newNotifications.forEach(notif => {
                // Show browser notification if permission is granted
                if (Notification.permission === 'granted') {
                    new Notification('New Message', {
                        body: notif.message,
                        icon: '/static/icon.png' // Optional: add an icon if you have one
                    });
                }

                // Display notification in chat
                chat.innerText += `[Notification] ${notif.message} (Received at ${notif.created_at})\n`;
                markNotificationDelivered(notif.id);
            });
        }

        chat.scrollTop = chat.scrollHeight;
    } catch (error) {
        console.error('Error polling messages or notifications:', error);
    }
    setTimeout(pollMessages, 1000); // Poll every 1 second
}

async function markNotificationDelivered(notificationId) {
    try {
        await fetch(`http://localhost:5006/notifications/${notificationId}/delivered`, {
            method: 'POST'
        });
    } catch (err) {
        console.error('Error marking notification as delivered:', err);
    }
}

// Check presence on page load
window.addEventListener('load', checkPresence);

// Set user to offline when leaving the page
window.addEventListener('beforeunload', async () => {
    await fetch(`http://localhost:5004/presence/${userId}`, {
        method: 'DELETE'
    });
});