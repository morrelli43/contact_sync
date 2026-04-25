const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DATA_DIR = process.env.DATA_DIR || __dirname;
const dbPath = path.join(DATA_DIR, 'sms_gateway.db');
const db = new Database(dbPath);

// Initialize database schema
db.exec(`
  CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    address TEXT NOT NULL,
    body TEXT,
    direction TEXT NOT NULL, -- 'inbound' or 'outbound'
    media_path TEXT,
    mime_type TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    thread_id TEXT,
    status TEXT
  );

  CREATE TABLE IF NOT EXISTS conversations (
    thread_id TEXT PRIMARY KEY,
    address TEXT NOT NULL,
    last_message_body TEXT,
    last_message_timestamp DATETIME,
    unread_count INTEGER DEFAULT 0
  );
`);

// Create media directory if it doesn't exist
const mediaDir = path.join(DATA_DIR, 'media');
if (!fs.existsSync(mediaDir)) {
  fs.mkdirSync(mediaDir, { recursive: true });
}

/**
 * Save a message to the database
 */
function saveMessage(message) {
  const { id, deviceId, address, body, direction, mediaPath, mimeType, timestamp, threadId, status } = message;
  
  const insert = db.prepare(`
    INSERT INTO messages (id, device_id, address, body, direction, media_path, mime_type, timestamp, thread_id, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      status = excluded.status,
      body = COALESCE(excluded.body, messages.body),
      media_path = COALESCE(excluded.media_path, messages.media_path)
  `);

  insert.run(id, deviceId, address, body, direction, mediaPath || null, mimeType || null, timestamp || new Date().toISOString(), threadId || null, status || 'received');

  // Update conversation summary
  const upsertConv = db.prepare(`
    INSERT INTO conversations (thread_id, address, last_message_body, last_message_timestamp)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(thread_id) DO UPDATE SET
      last_message_body = excluded.last_message_body,
      last_message_timestamp = excluded.last_message_timestamp
  `);

  if (threadId) {
    upsertConv.run(threadId, address, body ? body.substring(0, 100) : (mediaPath ? '[Media]' : ''), timestamp || new Date().toISOString());
  }
}

/**
 * Get messages for a specific address or thread
 */
function getMessages(query) {
  const { address, threadId, limit = 50, offset = 0 } = query;
  
  let stmt;
  if (threadId) {
    stmt = db.prepare(`
      SELECT * FROM messages 
      WHERE thread_id = ? 
      ORDER BY timestamp DESC 
      LIMIT ? OFFSET ?
    `);
    return stmt.all(threadId, limit, offset);
  } else if (address) {
    stmt = db.prepare(`
      SELECT * FROM messages 
      WHERE address = ? 
      ORDER BY timestamp DESC 
      LIMIT ? OFFSET ?
    `);
    return stmt.all(address, limit, offset);
  }
  
  return [];
}

/**
 * Get all conversations
 */
function getConversations(limit = 100, offset = 0) {
  const stmt = db.prepare(`
    SELECT * FROM conversations 
    ORDER BY last_message_timestamp DESC 
    LIMIT ? OFFSET ?
  `);
  return stmt.all(limit, offset);
}

module.exports = {
  saveMessage,
  getMessages,
  getConversations,
  mediaDir
};
