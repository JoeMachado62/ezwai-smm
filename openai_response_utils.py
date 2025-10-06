import logging
from typing import Any, Iterable, Iterator, Sequence

logger = logging.getLogger(__name__)


def _iter_response_fragments(response: Any) -> Iterator[str]:
    """
    Yield text fragments from an OpenAI Responses API result.

    Supports objects returned by openai.types.responses.response.Response as
    well as simple strings or dictionaries produced by mocked tests.
    """
    if response is None:
        return

    # Direct string responses
    if isinstance(response, str):
        yield response
        return

    # Some SDK objects expose `output_text`
    output_text = getattr(response, "output_text", None)
    if output_text:
        yield output_text

    # Iterate over structured output items
    output_items = getattr(response, "output", None)
    if output_items:
        for item in output_items:
            item_type = getattr(item, "type", None)

            if item_type == "message":
                # New SDK shape: message with content list
                content_list = getattr(item, "content", None)
                if isinstance(content_list, Sequence):
                    for content_item in content_list:
                        text_value = getattr(content_item, "text", None)
                        if text_value:
                            yield text_value
            elif item_type == "text":
                text_value = getattr(item, "text", None)
                if text_value:
                    yield text_value
            elif item_type == "reasoning":
                # Some responses carry reasoning summaries that may contain text
                summary = getattr(item, "summary", None)
                if isinstance(summary, Sequence):
                    for summary_item in summary:
                        if isinstance(summary_item, str):
                            yield summary_item
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    yield text_value

    # Some responses expose a top-level `content` attribute (e.g., tool mocks)
    content_attr = getattr(response, "content", None)
    if content_attr:
        if isinstance(content_attr, str):
            yield content_attr
        elif isinstance(content_attr, Sequence):
            for content_item in content_attr:
                text_value = getattr(content_item, "text", None)
                if text_value:
                    yield text_value


def extract_response_text(response: Any) -> str:
    """
    Collect all text fragments from an OpenAI Responses API object and return
    a single trimmed string.

    Ensures compatibility with both legacy and modern SDK object shapes.
    """
    fragments: Iterable[str] = (
        fragment.strip()
        for fragment in _iter_response_fragments(response)
        if fragment and isinstance(fragment, str) and fragment.strip()
    )

    combined = "\n".join(fragments).strip()

    if not combined:
        logger.debug("extract_response_text: no textual content extracted from response %r", response)

    return combined
