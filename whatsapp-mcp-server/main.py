from typing import List, Dict, Any, Optional
import logging

from fastmcp import FastMCP
from logging_config import configure_logging
from whatsapp import (
    search_contacts as whatsapp_search_contacts,
    list_messages as whatsapp_list_messages,
    list_chats as whatsapp_list_chats,
    get_chat as whatsapp_get_chat,
    get_direct_chat_by_contact as whatsapp_get_direct_chat_by_contact,
    get_contact_chats as whatsapp_get_contact_chats,
    send as whatsapp_send,
    download_media as whatsapp_download_media
)

configure_logging()
logger = logging.getLogger("whatsapp-mcp")

# Initialize FastMCP server
mcp = FastMCP("whatsapp")

@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.
    
    Args:
        query: Search term to match against contact names or phone numbers
    """
    logger.info("search_contacts request", extra={"query_present": bool(query)})
    try:
        contacts = whatsapp_search_contacts(query)
    except Exception:
        logger.exception("search_contacts failed", extra={"query_present": bool(query)})
        raise
    logger.info("search_contacts result", extra={"count": len(contacts)})
    return contacts

@mcp.tool()
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
    """Get WhatsApp messages matching specified criteria with optional context.
    
    Args:
        message_id: Optional message ID to fetch with surrounding context (other filters ignored)
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        chat_jid: Optional chat JID to filter messages by chat
        query: Optional search term to filter messages by content
        limit: Maximum number of messages to return (default 20)
        page: Page number for pagination (default 0)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)

    Returns:
        List of message objects with fields: id, chat_jid, chat_name, sender, sender_name, content, timestamp,
        is_from_me, media_type.
    """
    logger.info(
        "list_messages request",
        extra={
            "message_id": message_id,
            "after": after,
            "before": before,
            "sender_phone_number": sender_phone_number,
            "chat_jid": chat_jid,
            "query_present": bool(query),
            "limit": limit,
            "page": page,
            "include_context": include_context,
        },
    )
    try:
        messages = whatsapp_list_messages(
            message_id=message_id,
            after=after,
            before=before,
            sender_phone_number=sender_phone_number,
            chat_jid=chat_jid,
            query=query,
            limit=limit,
            page=page,
            include_context=include_context,
            context_before=context_before,
            context_after=context_after,
        )
    except Exception:
        logger.exception("list_messages failed", extra={"chat_jid": chat_jid})
        raise
    logger.info("list_messages result", extra={"count": len(messages)})
    return messages

@mcp.tool()
def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria.
    
    Args:
        query: Optional search term to filter chats by name or JID
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
        include_last_message: Whether to include the last message in each chat (default True)
        sort_by: Field to sort results by, either "last_active" or "name" (default "last_active")

    Returns:
        List of chat objects with fields: jid, name, last_message_time, last_message, last_sender,
        last_sender_name, last_is_from_me.
    """
    logger.info(
        "list_chats request",
        extra={
            "query_present": bool(query),
            "limit": limit,
            "page": page,
            "include_last_message": include_last_message,
            "sort_by": sort_by,
        },
    )
    try:
        chats = whatsapp_list_chats(
            query=query,
            limit=limit,
            page=page,
            include_last_message=include_last_message,
            sort_by=sort_by,
        )
    except Exception:
        logger.exception("list_chats failed", extra={"query_present": bool(query)})
        raise
    logger.info("list_chats result", extra={"count": len(chats)})
    return chats

@mcp.tool()
def get_chat(
    chat_jid: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    include_last_message: bool = True
) -> Optional[Dict[str, Any]]:
    """Get WhatsApp chat metadata by JID or sender phone number.
    
    Args:
        chat_jid: The JID of the chat to retrieve
        sender_phone_number: The phone number to search for when chat_jid is not provided
        include_last_message: Whether to include the last message (default True)
    """
    logger.info(
        "get_chat request",
        extra={
            "chat_jid": chat_jid,
            "sender_phone_number": sender_phone_number,
            "include_last_message": include_last_message,
        },
    )
    if not chat_jid and not sender_phone_number:
        logger.error("get_chat missing identifier")
        return None
    try:
        if chat_jid:
            chat = whatsapp_get_chat(chat_jid, include_last_message)
        else:
            if sender_phone_number is None:
                logger.error("get_chat missing sender_phone_number")
                return None
            chat = whatsapp_get_direct_chat_by_contact(sender_phone_number)
    except Exception:
        logger.exception("get_chat failed", extra={"chat_jid": chat_jid, "sender_phone_number": sender_phone_number})
        raise
    if not chat:
        logger.warning("get_chat missing", extra={"chat_jid": chat_jid, "sender_phone_number": sender_phone_number})
    else:
        logger.info("get_chat result", extra={"chat_jid": chat_jid, "sender_phone_number": sender_phone_number})
    return chat

@mcp.tool()
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact.
    
    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    logger.info("get_contact_chats request", extra={"jid": jid, "limit": limit, "page": page})
    try:
        chats = whatsapp_get_contact_chats(jid, limit, page)
    except Exception:
        logger.exception("get_contact_chats failed", extra={"jid": jid})
        raise
    logger.info("get_contact_chats result", extra={"count": len(chats), "jid": jid})
    return chats

@mcp.tool()
def send(
    recipient: str,
    message: Optional[str] = None,
    media_path: Optional[str] = None
) -> Dict[str, Any]:
    """Send a WhatsApp message or media to a person or group. For group chats use the JID.

    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        message: The message text to send
        media_path: The absolute path to the media file to send (image, video, document)

    Returns:
        A dictionary containing success status and a status message
    """
    logger.info(
        "send request",
        extra={
            "recipient": recipient,
            "has_message": bool(message),
            "has_media": bool(media_path),
        },
    )
    if not recipient:
        logger.error("send missing recipient")
        return {
            "success": False,
            "message": "Recipient must be provided",
        }
    if not message and not media_path:
        logger.error("send missing payload", extra={"recipient": recipient})
        return {
            "success": False,
            "message": "Message or media path must be provided",
        }

    try:
        success, status_message = whatsapp_send(
            recipient,
            message=message,
            media_path=media_path,
        )
    except Exception:
        logger.exception("send failed", extra={"recipient": recipient})
        raise
    logger.info("send result", extra={"recipient": recipient, "success": success})
    return {
        "success": success,
        "message": status_message,
    }

@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        A dictionary containing success status, a status message, and the file path if successful
    """
    logger.info("download_media request", extra={"message_id": message_id, "chat_jid": chat_jid})
    try:
        file_path = whatsapp_download_media(message_id, chat_jid)
    except Exception:
        logger.exception("download_media failed", extra={"message_id": message_id, "chat_jid": chat_jid})
        raise
    
    if file_path:
        logger.info("download_media result", extra={"message_id": message_id})
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "file_path": file_path
        }
    logger.error("download_media failed", extra={"message_id": message_id, "chat_jid": chat_jid})
    return {
        "success": False,
        "message": "Failed to download media"
    }

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        uvicorn_config={"access_log": False},
    )
