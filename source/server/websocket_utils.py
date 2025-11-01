import asyncio
import os
from dataclasses import dataclass
from typing import Optional


MASK_LENGTH = 4


@dataclass
class WebSocketFrame:
    """Represents a single WebSocket frame."""

    fin: bool
    opcode: int
    payload: bytes
    masked: bool
    masking_key: Optional[bytes] = None


async def read_frame(reader: asyncio.StreamReader) -> WebSocketFrame:
    """Read a single WebSocket frame from the given reader."""

    header = await reader.readexactly(2)
    first_byte, second_byte = header

    fin = bool(first_byte & 0x80)
    opcode = first_byte & 0x0F

    masked = bool(second_byte & 0x80)
    payload_length = second_byte & 0x7F

    if payload_length == 126:
        extended = await reader.readexactly(2)
        payload_length = int.from_bytes(extended, 'big')
    elif payload_length == 127:
        extended = await reader.readexactly(8)
        payload_length = int.from_bytes(extended, 'big')

    masking_key = None
    if masked:
        masking_key = await reader.readexactly(MASK_LENGTH)

    payload_data = await reader.readexactly(payload_length)

    if masked and masking_key:
        payload_data = bytes(
            byte ^ masking_key[index % MASK_LENGTH]
            for index, byte in enumerate(payload_data)
        )

    return WebSocketFrame(
        fin=fin,
        opcode=opcode,
        payload=payload_data,
        masked=masked,
        masking_key=masking_key,
    )


async def write_frame(
    writer: asyncio.StreamWriter,
    payload: bytes | str,
    *,
    opcode: int = 0x1,
    fin: bool = True,
    mask: bool = False,
    masking_key: Optional[bytes] = None,
) -> None:
    """Write a WebSocket frame to the writer."""

    frame_bytes = encode_frame(
        payload=payload,
        opcode=opcode,
        fin=fin,
        mask=mask,
        masking_key=masking_key,
    )
    writer.write(frame_bytes)
    await writer.drain()


def encode_frame(
    *,
    payload: bytes | str,
    opcode: int = 0x1,
    fin: bool = True,
    mask: bool = False,
    masking_key: Optional[bytes] = None,
) -> bytes:
    """Encode payload and metadata into a WebSocket frame."""

    if isinstance(payload, str):
        payload_bytes = payload.encode('utf-8')
    else:
        payload_bytes = payload

    first_byte = (0x80 if fin else 0x00) | (opcode & 0x0F)

    header = bytearray([first_byte])
    payload_length = len(payload_bytes)

    mask_bit = 0x80 if mask else 0x00

    if payload_length < 126:
        header.append(mask_bit | payload_length)
    elif payload_length < (1 << 16):
        header.append(mask_bit | 126)
        header.extend(payload_length.to_bytes(2, 'big'))
    else:
        header.append(mask_bit | 127)
        header.extend(payload_length.to_bytes(8, 'big'))

    if mask:
        if masking_key is None:
            masking_key = os.urandom(MASK_LENGTH)
        if len(masking_key) != MASK_LENGTH:
            raise ValueError("Masking key must be exactly 4 bytes")
        header.extend(masking_key)
        payload_bytes = bytes(
            byte ^ masking_key[index % MASK_LENGTH]
            for index, byte in enumerate(payload_bytes)
        )

    return bytes(header) + payload_bytes


__all__ = [
    'WebSocketFrame',
    'encode_frame',
    'read_frame',
    'write_frame',
]
