import importlib
import logging

from federation.exceptions import NoSuitableProtocolFoundError

logger = logging.getLogger("federation")

PROTOCOLS = (
    "diaspora",
)


def handle_receive(payload, user=None, sender_key_fetcher=None, skip_author_verification=False):
    """Takes a payload and passes it to the correct protocol.

    :arg payload: Payload blob (str)
    :arg user: User that will be passed to `protocol.receive` (required on private encrypted content)
    :arg sender_key_fetcher: Function that accepts sender handle and returns public key (optional)
    :arg skip_author_verification: Don't verify sender (test purposes, false default)
    :returns: Tuple of sender handle, protocol name and list of entity objects
    :raises NoSuitableProtocolFound: When no protocol was identified to pass message to
    """
    logger.debug("handle_receive: processing payload: %s", payload)
    found_protocol = None
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module("federation.protocols.%s.protocol" % protocol_name)
        if protocol.identify_payload(payload):
            found_protocol = protocol
            break

    if found_protocol:
        logger.debug("handle_receive: using protocol %s", found_protocol.PROTOCOL_NAME)
        protocol = found_protocol.Protocol()
        sender, message = protocol.receive(
            payload, user, sender_key_fetcher, skip_author_verification=skip_author_verification)
        logger.debug("handle_receive: sender %s, message %s", sender, message)
    else:
        raise NoSuitableProtocolFoundError()

    mappers = importlib.import_module("federation.entities.%s.mappers" % found_protocol.PROTOCOL_NAME)
    entities = mappers.message_to_objects(message)
    logger.debug("handle_receive: entities %s", entities)

    return sender, found_protocol.PROTOCOL_NAME, entities
