#!/bin/bash

set -e

CHAT_SERVICE_URL="http://localhost:5003"
PRESENCE_SERVICE_URL="http://localhost:5004"
NOTIFICATION_SERVICE_URL="http://localhost:5006"
FRONTEND_URL="http://localhost:8000"
TIMEOUT=5
RETRY_INTERVAL=2

USER_A="user-a-$(date +%s)"
USER_B="user-b-$(date +%s)"
ROOM_NAME="room-for-2-$(date +%s)"
MESSAGE_B="Hello from B"
MESSAGE_A="Hi from A to B!"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}SUCCESS: $2${NC}"
    else
        echo -e "${RED}ERROR: $2${NC}"
        exit 1
    fi
}

echo "Test 1: Checking service availability..."
for url in "$CHAT_SERVICE_URL" "$PRESENCE_SERVICE_URL" "$NOTIFICATION_SERVICE_URL" "$FRONTEND_URL"; do
    curl -s -o /dev/null -m $TIMEOUT "$url" && log_result 0 "$url is up" || log_result 1 "$url is down"
done

echo "Test 2: Creating a shared room..."
response=$(curl -s -X POST "$CHAT_SERVICE_URL/rooms" -H "Content-Type: application/json" \
    -d "{\"name\": \"$ROOM_NAME\"}" -m $TIMEOUT)
room_id=$(echo "$response" | jq -r '.room_id')
[ -n "$room_id" ] && [ "$room_id" != "null" ] && log_result 0 "Room created: $room_id" || log_result 1 "Room creation failed: $response"

echo "Test 3: Setting both users online..."
for user in "$USER_A" "$USER_B"; do
    response=$(curl -s -X POST "$PRESENCE_SERVICE_URL/presence/$user" -H "Content-Type: application/json" \
        -d "{\"status\": \"online\"}" -m $TIMEOUT)
    status=$(echo "$response" | jq -r '.status')
    [ "$status" = "online" ] && log_result 0 "$user is online" || log_result 1 "Failed to set $user online"
done

echo "Test 4: User B greets the room..."
response=$(curl -s -X POST "$CHAT_SERVICE_URL/rooms/$room_id/messages" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_B\", \"content\": \"$MESSAGE_B\"}" -m $TIMEOUT)
message_id=$(echo "$response" | jq -r '.message_id')
[ -n "$message_id" ] && [ "$message_id" != "null" ] && log_result 0 "User B sent message ID: $message_id" || log_result 1 "Message sending failed: $response"

echo "Test 5: User A sends message to room..."
response=$(curl -s -X POST "$CHAT_SERVICE_URL/rooms/$room_id/messages" -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_A\", \"content\": \"$MESSAGE_A\"}" -m $TIMEOUT)
message_id=$(echo "$response" | jq -r '.message_id')
[ -n "$message_id" ] && [ "$message_id" != "null" ] && log_result 0 "User A sent message ID: $message_id" || log_result 1 "Message sending failed: $response"

echo "Test 6: User B sees A's message..."
response=$(curl -s -X GET "$CHAT_SERVICE_URL/rooms/$room_id/messages" -m $TIMEOUT)
found=$(echo "$response" | jq -r --arg msg "$MESSAGE_A" '.[] | select(.content == $msg)')
[ -n "$found" ] && log_result 0 "User B sees A's message" || log_result 1 "Message from A not visible to B"

echo "Test 7: User B receives notification..."
sleep $RETRY_INTERVAL
response=$(curl -s -X GET "$NOTIFICATION_SERVICE_URL/notifications/$USER_B" -m $TIMEOUT)
notif_count=$(echo "$response" | jq '. | length')
if [ "$notif_count" -gt 0 ]; then
    notif_msg=$(echo "$response" | jq -r '.[0].message')
    log_result 0 "User B received notification: $notif_msg"
else
    log_result 1 "No notification for User B"
fi

echo "Test 8: Marking notification as delivered..."
notif_id=$(echo "$response" | jq -r '.[0].id')
response=$(curl -s -X POST "$NOTIFICATION_SERVICE_URL/notifications/$notif_id/delivered" -m $TIMEOUT)
echo "$response" | grep -q "Notification marked as delivered" && \
    log_result 0 "Notification $notif_id marked delivered" || \
    log_result 1 "Failed to mark notification delivered"

echo -e "${GREEN}All two-user interaction tests passed successfully!${NC}"
