import asyncio
import os
import sys

TEST_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_ROOT, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from source.server.websocket_utils import encode_frame, read_frame


def test_read_frame_unmasks_payload():
    payload = b"hello websocket"
    masking_key = b"\x01\x02\x03\x04"

    frame_bytes = encode_frame(payload=payload, mask=True, masking_key=masking_key)

    async def run():
        reader = asyncio.StreamReader()
        reader.feed_data(frame_bytes)
        reader.feed_eof()

        frame = await read_frame(reader)

        assert frame.fin is True
        assert frame.opcode == 0x1
        assert frame.masked is True
        assert frame.masking_key == masking_key
        assert frame.payload == payload

    asyncio.run(run())


def test_encode_frame_uses_extended_length_for_large_payload():
    payload = b"a" * 130

    frame_bytes = encode_frame(payload=payload, opcode=0x2, mask=False)

    assert frame_bytes[0] == 0x80 | 0x2
    assert frame_bytes[1] == 126
    assert int.from_bytes(frame_bytes[2:4], 'big') == len(payload)
    assert frame_bytes[4:] == payload
