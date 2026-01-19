import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
import os.path
import logging
import requests
import json

MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'messages.db')
WHATSAPP_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'whatsapp.db')
WHATSAPP_API_BASE_URL = "http://localhost:8080/api"
CONTACT_NAME_PRIORITY = ("full_name", "business_name", "first_name", "push_name")
CONTACT_NAME_CACHE: Dict[str, str] = {}
CONTACT_CACHE_LOADED = False
LOGGER = logging.getLogger("whatsapp-mcp")

@dataclass
class Message:
    timestamp: datetime
    sender: str
    sender_name: Optional[str]
    content: str
    is_from_me: bool
    chat_jid: str
    id: str
    chat_name: Optional[str] = None
    media_type: Optional[str] = None

@dataclass
class Chat:
    jid: str
    name: Optional[str]
    last_message_time: Optional[datetime]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_sender_name: Optional[str] = None
    last_is_from_me: Optional[bool] = None

    @property
    def is_group(self) -> bool:
        """Determine if chat is a group based on JID pattern."""
        return self.jid.endswith("@g.us")

@dataclass
class Contact:
    phone_number: str
    name: Optional[str]
    jid: str

@dataclass
class MessageContext:
    message: Message
    before: List[Message]
    after: List[Message]


def normalize_contact_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def derive_last_name(first_name: Optional[str], full_name: Optional[str]) -> Optional[str]:
    if not first_name or not full_name:
        return None
    first_trimmed = first_name.strip()
    full_trimmed = full_name.strip()
    if not first_trimmed or not full_trimmed:
        return None
    lower_first = first_trimmed.lower()
    lower_full = full_trimmed.lower()
    if not lower_full.startswith(lower_first):
        return None
    remainder = full_trimmed[len(first_trimmed):].strip()
    return remainder if remainder else None


def is_numeric_name(name: Optional[str]) -> bool:
    if not name:
        return False
    stripped = name.strip()
    return stripped.isdigit()


def select_contact_display_name(contact: Dict[str, Optional[str]]) -> Optional[str]:
    """Choose the highest-priority contact name."""
    first_name = normalize_contact_value(contact.get("first_name"))
    full_name = normalize_contact_value(contact.get("full_name"))
    last_name = normalize_contact_value(contact.get("last_name"))
    if not last_name:
        last_name = derive_last_name(first_name, full_name)
    if first_name and last_name:
        return f"{first_name} {last_name}"
    for field in CONTACT_NAME_PRIORITY:
        value = normalize_contact_value(contact.get(field))
        if value:
            return value
    return None


def is_group_jid(jid: Optional[str]) -> bool:
    return bool(jid) and jid.endswith("@g.us")


def is_device_authenticated() -> bool:
    """Return True when the WhatsApp store has a device row."""
    try:
        conn = sqlite3.connect(WHATSAPP_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM whatsmeow_device LIMIT 1")
        return cursor.fetchone() is not None
    except sqlite3.Error:
        LOGGER.exception("Database error while checking device authentication")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def ensure_contact_cache_loaded() -> None:
    """Load contacts into memory on first authenticated request."""
    global CONTACT_NAME_CACHE, CONTACT_CACHE_LOADED
    if CONTACT_CACHE_LOADED:
        return
    if not is_device_authenticated():
        return
    LOGGER.info("Loading contact cache")
    try:
        conn = sqlite3.connect(WHATSAPP_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT their_jid, full_name, business_name, first_name, push_name
            FROM whatsmeow_contacts
        """)
        contacts = cursor.fetchall()
        cache: Dict[str, str] = {}
        for contact_data in contacts:
            contact = {
                "their_jid": contact_data[0],
                "full_name": contact_data[1],
                "business_name": contact_data[2],
                "first_name": contact_data[3],
                "push_name": contact_data[4],
            }
            display_name = select_contact_display_name(contact)
            contact_jid = contact["their_jid"]
            if contact_jid and display_name:
                cache[contact_jid] = display_name
        CONTACT_NAME_CACHE = cache
        CONTACT_CACHE_LOADED = True
        LOGGER.info("Contact cache loaded", extra={"count": len(cache)})
    except sqlite3.Error:
        LOGGER.exception("Database error while loading contacts")
    finally:
        if 'conn' in locals():
            conn.close()


def resolve_contact_name(jid: Optional[str]) -> Optional[str]:
    """Return a cached contact name for a full JID."""
    is_group = is_group_jid(jid)
    if not jid or is_group:
        return None
    ensure_contact_cache_loaded()
    return CONTACT_NAME_CACHE.get(jid)


def resolve_chat_name(chat_jid: Optional[str], current_name: Optional[str]) -> Optional[str]:
    """Return a chat name, filling from contacts when missing."""
    if current_name and not is_numeric_name(current_name):
        return current_name
    resolved_contact_name = resolve_contact_name(chat_jid)
    return resolved_contact_name or current_name


def get_sender_name(sender_jid: Optional[str]) -> Optional[str]:
    if not sender_jid:
        return None

    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()

        # First try matching by exact JID
        cursor.execute("""
            SELECT name
            FROM chats
            WHERE jid = ?
            LIMIT 1
        """, (sender_jid,))

        result = cursor.fetchone()

        # If no result, try looking for the number within JIDs
        if not result:
            # Extract the phone number part if it's a JID
            if '@' in sender_jid:
                phone_part = sender_jid.split('@')[0]
            else:
                phone_part = sender_jid

            cursor.execute("""
                SELECT name
                FROM chats
                WHERE jid LIKE ?
                LIMIT 1
            """, (f"%{phone_part}%",))

            result = cursor.fetchone()

        if result and result[0]:
            return result[0]

        return sender_jid

    except sqlite3.Error:
        LOGGER.exception("Database error while getting sender name", extra={"sender_jid": sender_jid})
        return sender_jid
    finally:
        if 'conn' in locals():
            conn.close()


def resolve_sender_name(sender_jid: Optional[str], chat_jid: Optional[str]) -> Optional[str]:
    """Return a sender name, using cached contacts for direct chats."""
    if not sender_jid:
        return None

    sender_name = get_sender_name(sender_jid)
    if sender_name and sender_name != sender_jid and not is_numeric_name(sender_name):
        return sender_name

    contact_name = resolve_contact_name(sender_jid)
    if contact_name:
        return contact_name

    return sender_name


def format_message(message: Message, show_chat_info: bool = True) -> None:
    """Print a single message with consistent formatting."""
    output = ""
    
    if show_chat_info and message.chat_name:
        output += f"[{message.timestamp:%Y-%m-%d %H:%M:%S}] Chat: {message.chat_name} "
    else:
        output += f"[{message.timestamp:%Y-%m-%d %H:%M:%S}] "
        
    content_prefix = ""
    if hasattr(message, 'media_type') and message.media_type:
        content_prefix = f"[{message.media_type} - Message ID: {message.id} - Chat JID: {message.chat_jid}] "
    
    try:
        resolved_sender_name = message.sender_name or resolve_sender_name(message.sender, message.chat_jid) or message.sender
        sender_name = "Me" if message.is_from_me else resolved_sender_name
        output += f"From: {sender_name}: {content_prefix}{message.content}\n"
    except Exception:
        LOGGER.exception("Error formatting message", extra={"message_id": message.id})
    return output

def format_messages_list(messages: List[Message], show_chat_info: bool = True) -> None:
    output = ""
    if not messages:
        output += "No messages to display."
        return output
    
    for message in messages:
        output += format_message(message, show_chat_info)
    return output


def message_to_dict(message: Message) -> Dict[str, Any]:
    return {
        "id": message.id,
        "chat_jid": message.chat_jid,
        "chat_name": message.chat_name,
        "sender": message.sender,
        "sender_name": message.sender_name or message.sender,
        "content": message.content,
        "timestamp": message.timestamp.isoformat(),
        "is_from_me": message.is_from_me,
        "media_type": message.media_type or "",
    }


def chat_to_dict(chat: Chat) -> Dict[str, Any]:
    last_sender_name = chat.last_sender_name
    if chat.last_sender and not last_sender_name:
        last_sender_name = chat.last_sender

    return {
        "jid": chat.jid,
        "name": chat.name,
        "last_message_time": chat.last_message_time.isoformat() if chat.last_message_time else None,
        "last_message": chat.last_message,
        "last_sender": chat.last_sender,
        "last_sender_name": last_sender_name,
        "last_is_from_me": chat.last_is_from_me,
    }


def list_messages(
    message_id: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1
) -> List[Dict[str, Any]]:
    """Get messages matching the specified criteria with optional context."""
    if message_id:
        try:
            context = get_message_context(message_id, context_before, context_after)
        except ValueError:
            LOGGER.warning("list_messages missing message_id", extra={"message_id": message_id})
            return []
        except sqlite3.Error:
            LOGGER.exception("Database error in list_messages", extra={"message_id": message_id})
            return []
        messages = (
            context.before + [context.message] + context.after
            if include_context
            else [context.message]
        )
        return [message_to_dict(message) for message in messages]

    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        # Build base query
        query_parts = ["SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type FROM messages"]
        query_parts.append("JOIN chats ON messages.chat_jid = chats.jid")
        where_clauses = []
        params = []
        
        # Add filters
        if after:
            try:
                after = datetime.fromisoformat(after)
            except ValueError:
                raise ValueError(f"Invalid date format for 'after': {after}. Please use ISO-8601 format.")
            
            where_clauses.append("messages.timestamp > ?")
            params.append(after)

        if before:
            try:
                before = datetime.fromisoformat(before)
            except ValueError:
                raise ValueError(f"Invalid date format for 'before': {before}. Please use ISO-8601 format.")
            
            where_clauses.append("messages.timestamp < ?")
            params.append(before)

        if sender_phone_number:
            where_clauses.append("messages.sender = ?")
            params.append(sender_phone_number)
            
        if chat_jid:
            where_clauses.append("messages.chat_jid = ?")
            params.append(chat_jid)
            
        if query:
            where_clauses.append("LOWER(messages.content) LIKE LOWER(?)")
            params.append(f"%{query}%")
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
            
        # Add pagination
        offset = page * limit
        query_parts.append("ORDER BY messages.timestamp DESC")
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        messages = cursor.fetchall()
        
        result = []
        for msg in messages:
            sender = msg[1]
            chat_jid = msg[5]
            chat_name = resolve_chat_name(chat_jid, msg[2])
            sender_name = resolve_sender_name(sender, chat_jid) or sender
            message = Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=sender,
                sender_name=sender_name,
                chat_name=chat_name,
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=chat_jid,
                id=msg[6],
                media_type=msg[7]
            )
            result.append(message)

        if include_context and result:
            # Add context for each message
            messages_with_context = []
            for msg in result:
                context = get_message_context(msg.id, context_before, context_after)
                messages_with_context.extend(context.before)
                messages_with_context.append(context.message)
                messages_with_context.extend(context.after)

            return [message_to_dict(message) for message in messages_with_context]

        return [message_to_dict(message) for message in result]
        
    except sqlite3.Error:
        LOGGER.exception("Database error in list_messages")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> MessageContext:
    """Get context around a specific message."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        # Get the target message first
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.chat_jid, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.id = ?
        """, (message_id,))
        msg_data = cursor.fetchone()
        
        if not msg_data:
            raise ValueError(f"Message with ID {message_id} not found")
            
        sender = msg_data[1]
        chat_jid = msg_data[5]
        chat_name = resolve_chat_name(chat_jid, msg_data[2])
        sender_name = resolve_sender_name(sender, chat_jid) or sender
        target_message = Message(
            timestamp=datetime.fromisoformat(msg_data[0]),
            sender=sender,
            sender_name=sender_name,
            chat_name=chat_name,
            content=msg_data[3],
            is_from_me=msg_data[4],
            chat_jid=chat_jid,
            id=msg_data[6],
            media_type=msg_data[8]
        )
        
        # Get messages before
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp < ?
            ORDER BY messages.timestamp DESC
            LIMIT ?
        """, (msg_data[7], msg_data[0], before))
        
        before_messages = []
        for msg in cursor.fetchall():
            sender = msg[1]
            chat_jid = msg[5]
            chat_name = resolve_chat_name(chat_jid, msg[2])
            sender_name = resolve_sender_name(sender, chat_jid) or sender
            before_messages.append(Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=sender,
                sender_name=sender_name,
                chat_name=chat_name,
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=chat_jid,
                id=msg[6],
                media_type=msg[7]
            ))
        
        # Get messages after
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp > ?
            ORDER BY messages.timestamp ASC
            LIMIT ?
        """, (msg_data[7], msg_data[0], after))
        
        after_messages = []
        for msg in cursor.fetchall():
            sender = msg[1]
            chat_jid = msg[5]
            chat_name = resolve_chat_name(chat_jid, msg[2])
            sender_name = resolve_sender_name(sender, chat_jid) or sender
            after_messages.append(Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=sender,
                sender_name=sender_name,
                chat_name=chat_name,
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=chat_jid,
                id=msg[6],
                media_type=msg[7]
            ))
        
        return MessageContext(
            message=target_message,
            before=before_messages,
            after=after_messages
        )
        
    except sqlite3.Error:
        LOGGER.exception("Database error in get_message_context", extra={"message_id": message_id})
        raise
    finally:
        if 'conn' in locals():
            conn.close()


def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active",
    contact_jid: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get chats matching the specified criteria."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()

        # Build base query
        query_parts = ["""
            SELECT 
                chats.jid,
                chats.name,
                chats.last_message_time,
                messages.content as last_message,
                messages.sender as last_sender,
                messages.is_from_me as last_is_from_me
            FROM chats
        """]

        if include_last_message:
            query_parts.append("""
                LEFT JOIN messages ON chats.jid = messages.chat_jid 
                AND chats.last_message_time = messages.timestamp
            """)

        where_clauses = []
        params = []

        if query:
            where_clauses.append("(LOWER(chats.name) LIKE LOWER(?) OR chats.jid LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if contact_jid:
            where_clauses.append(
                "(chats.jid = ? OR EXISTS ("
                "SELECT 1 FROM messages contact_messages "
                "WHERE contact_messages.chat_jid = chats.jid "
                "AND contact_messages.sender = ?))"
            )
            params.extend([contact_jid, contact_jid])

        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))

        # Add sorting
        order_by = "chats.last_message_time DESC" if sort_by == "last_active" else "chats.name"
        query_parts.append(f"ORDER BY {order_by}")

        # Add pagination
        offset = (page ) * limit
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])

        cursor.execute(" ".join(query_parts), tuple(params))
        chats = cursor.fetchall()

        result = []
        for chat_data in chats:
            chat_jid = chat_data[0]
            db_name = chat_data[1]
            chat_name = resolve_chat_name(chat_jid, db_name)
            last_sender = chat_data[4]
            last_sender_name = resolve_sender_name(last_sender, chat_jid) if last_sender else None
            chat = Chat(
                jid=chat_jid,
                name=chat_name,
                last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
                last_message=chat_data[3],
                last_sender=last_sender,
                last_sender_name=last_sender_name,
                last_is_from_me=chat_data[5]
            )
            result.append(chat)

        return [chat_to_dict(chat) for chat in result]
        
    except sqlite3.Error:
        LOGGER.exception("Database error in list_chats")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def search_contacts(query: str) -> List[Contact]:
    """Search contacts by name or phone number."""
    try:
        conn = sqlite3.connect(WHATSAPP_DB_PATH)
        cursor = conn.cursor()

        search_pattern = '%' + query + '%'
        params = (search_pattern,) * 6

        cursor.execute("""
            SELECT DISTINCT
                their_jid,
                first_name,
                full_name,
                push_name,
                business_name,
                redacted_phone
            FROM whatsmeow_contacts
            WHERE
                (LOWER(first_name) LIKE LOWER(?)
                 OR LOWER(full_name) LIKE LOWER(?)
                 OR LOWER(push_name) LIKE LOWER(?)
                 OR LOWER(business_name) LIKE LOWER(?)
                 OR LOWER(redacted_phone) LIKE LOWER(?)
                 OR LOWER(their_jid) LIKE LOWER(?))
                AND their_jid NOT LIKE '%@g.us'
            ORDER BY full_name, first_name, push_name, their_jid
            LIMIT 50
        """, params)

        contacts = cursor.fetchall()

        result = []
        for contact_data in contacts:
            contact = {
                "their_jid": contact_data[0],
                "first_name": contact_data[1],
                "full_name": contact_data[2],
                "push_name": contact_data[3],
                "business_name": contact_data[4],
            }
            display_name = select_contact_display_name(contact)
            contact_entry = Contact(
                phone_number=contact_data[0].split('@')[0],
                name=display_name,
                jid=contact_data[0]
            )
            result.append(contact_entry)

        return result

    except sqlite3.Error:
        LOGGER.exception("Database error in search_contacts", extra={"query_present": bool(query)})
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def get_last_interaction(jid: str) -> str:
    """Get most recent message involving the contact."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.timestamp,
                m.sender,
                c.name,
                m.content,
                m.is_from_me,
                c.jid,
                m.id,
                m.media_type
            FROM messages m
            JOIN chats c ON m.chat_jid = c.jid
            WHERE m.sender = ? OR c.jid = ?
            ORDER BY m.timestamp DESC
            LIMIT 1
        """, (jid, jid))
        
        msg_data = cursor.fetchone()
        
        if not msg_data:
            return None
            
        sender = msg_data[1]
        chat_jid = msg_data[5]
        chat_name = resolve_chat_name(chat_jid, msg_data[2])
        sender_name = resolve_sender_name(sender, chat_jid) or sender
        message = Message(
            timestamp=datetime.fromisoformat(msg_data[0]),
            sender=sender,
            sender_name=sender_name,
            chat_name=chat_name,
            content=msg_data[3],
            is_from_me=msg_data[4],
            chat_jid=chat_jid,
            id=msg_data[6],
            media_type=msg_data[7]
        )
        
        return format_message(message)
        
    except sqlite3.Error:
        LOGGER.exception("Database error in get_last_interaction", extra={"jid": jid})
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_chat(chat_jid: str, include_last_message: bool = True) -> Optional[Dict[str, Any]]:
    """Get chat metadata by JID."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
        """
        
        if include_last_message:
            query += """
                LEFT JOIN messages m ON c.jid = m.chat_jid 
                AND c.last_message_time = m.timestamp
            """
            
        query += " WHERE c.jid = ?"
        
        cursor.execute(query, (chat_jid,))
        chat_data = cursor.fetchone()

        if not chat_data:
            return None

        chat_jid = chat_data[0]
        chat_name = resolve_chat_name(chat_jid, chat_data[1])
        last_sender = chat_data[4]
        last_sender_name = resolve_sender_name(last_sender, chat_jid) if last_sender else None
        chat = Chat(
            jid=chat_jid,
            name=chat_name,
            last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
            last_message=chat_data[3],
            last_sender=last_sender,
            last_sender_name=last_sender_name,
            last_is_from_me=chat_data[5]
        )

        return chat_to_dict(chat)
        
    except sqlite3.Error:
        LOGGER.exception("Database error in get_chat", extra={"chat_jid": chat_jid})
        return None
    finally:
        if 'conn' in locals():
            conn.close()


def get_direct_chat_by_contact(sender_phone_number: str) -> Optional[Dict[str, Any]]:
    """Get chat metadata by sender phone number."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.jid,
                c.name,
                c.last_message_time,
                m.content as last_message,
                m.sender as last_sender,
                m.is_from_me as last_is_from_me
            FROM chats c
            LEFT JOIN messages m ON c.jid = m.chat_jid 
                AND c.last_message_time = m.timestamp
            WHERE c.jid LIKE ? AND c.jid NOT LIKE '%@g.us'
            LIMIT 1
        """, (f"%{sender_phone_number}%",))
        
        chat_data = cursor.fetchone()
        
        if not chat_data:
            return None
            
        chat_jid = chat_data[0]
        chat_name = resolve_chat_name(chat_jid, chat_data[1])
        last_sender = chat_data[4]
        last_sender_name = resolve_sender_name(last_sender, chat_jid) if last_sender else None
        chat = Chat(
            jid=chat_jid,
            name=chat_name,
            last_message_time=datetime.fromisoformat(chat_data[2]) if chat_data[2] else None,
            last_message=chat_data[3],
            last_sender=last_sender,
            last_sender_name=last_sender_name,
            last_is_from_me=chat_data[5]
        )

        return chat_to_dict(chat)
        
    except sqlite3.Error:
        LOGGER.exception(
            "Database error in get_direct_chat_by_contact",
            extra={"sender_phone_number": sender_phone_number},
        )
        return None
    finally:
        if 'conn' in locals():
            conn.close()
 

def send(recipient: str, message: Optional[str] = None, media_path: Optional[str] = None) -> Tuple[bool, str]:
    try:
        if not recipient:
            return False, "Recipient must be provided"

        if not message and not media_path:
            return False, "Message or media path must be provided"

        if media_path:
            if not os.path.isfile(media_path):
                return False, f"Media file not found: {media_path}"

        url = f"{WHATSAPP_API_BASE_URL}/send"
        payload: Dict[str, Any] = {
            "recipient": recipient,
        }
        if message:
            payload["message"] = message
        if media_path:
            payload["media_path"] = media_path

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown response")
        LOGGER.error(
            "send HTTP error",
            extra={"recipient": recipient, "status_code": response.status_code},
        )
        return False, f"Error: HTTP {response.status_code} - {response.text}"

    except requests.RequestException:
        LOGGER.exception("Request error in send", extra={"recipient": recipient})
        return False, "Request error"
    except json.JSONDecodeError:
        LOGGER.exception("Response parse error in send", extra={"recipient": recipient})
        return False, "Error parsing response"
    except Exception:
        LOGGER.exception("Unexpected error in send", extra={"recipient": recipient})
        return False, "Unexpected error"


def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media from a message and return the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        The local file path if download was successful, None otherwise
    """
    try:
        url = f"{WHATSAPP_API_BASE_URL}/download"
        payload = {
            "message_id": message_id,
            "chat_jid": chat_jid
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success", False):
                path = result.get("path")
                LOGGER.info("Media downloaded", extra={"message_id": message_id})
                return path
            LOGGER.error(
                "Download failed",
                extra={"message_id": message_id},
            )
            return None
        LOGGER.error(
            "Download failed with HTTP error",
            extra={
                "message_id": message_id,
                "status_code": response.status_code,
            },
        )
        return None
            
    except requests.RequestException:
        LOGGER.exception("Request error in download_media", extra={"message_id": message_id})
        return None
    except json.JSONDecodeError:
        LOGGER.exception("Response parse error in download_media", extra={"message_id": message_id})
        return None
    except Exception:
        LOGGER.exception("Unexpected error in download_media", extra={"message_id": message_id})
        return None
