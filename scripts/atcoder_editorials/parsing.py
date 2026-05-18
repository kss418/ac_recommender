"""HTML parsers for AtCoder editorial indexes and detail pages."""

from __future__ import annotations

import re
import urllib.parse
from html.parser import HTMLParser

from atcoder_editorials.contest import canonicalize_url, is_editorial_source_url
from atcoder_editorials.models import EditorialLink
from atcoder_editorials.text import clean_markdown, normalize_space


class EditorialIndexParser(HTMLParser):
    """Find editorial links and remember their nearest heading."""

    HEADING_TAGS = {"h1", "h2", "h3", "h4"}
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self, *, base_url: str, contest: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.contest = contest
        self.current_section = ""
        self.links: list[EditorialLink] = []

        self._skip_depth = 0
        self._heading_tag: str | None = None
        self._heading_chunks: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_chunks: list[str] = []
        self._li_depth = 0
        self._li_chunks: list[str] = []
        self._li_links: list[EditorialLink] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        attrs_dict = dict(attrs)
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self.HEADING_TAGS:
            self._heading_tag = tag
            self._heading_chunks = []
        if tag == "li":
            if self._li_depth == 0:
                self._li_chunks = []
                self._li_links = []
            self._li_depth += 1
        if tag == "a" and attrs_dict.get("href"):
            self._anchor_href = attrs_dict["href"]
            self._anchor_chunks = []
        if tag == "img":
            alt = attrs_dict.get("alt") or ""
            if alt:
                self._capture_text(alt)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == self._heading_tag:
            heading = normalize_space("".join(self._heading_chunks))
            if heading:
                self.current_section = heading
            self._heading_tag = None
            self._heading_chunks = []
        if tag == "a" and self._anchor_href is not None:
            label = normalize_space("".join(self._anchor_chunks))
            url = urllib.parse.urljoin(self.base_url, self._anchor_href)
            if is_editorial_source_url(url, self.contest):
                link = EditorialLink(
                    url=url,
                    label=label or url,
                    section=self.current_section,
                )
                if self._li_depth:
                    self._li_links.append(link)
                else:
                    self.links.append(link)
            self._anchor_href = None
            self._anchor_chunks = []
        if tag == "li" and self._li_depth:
            self._li_depth -= 1
            if self._li_depth == 0:
                context = normalize_space("".join(self._li_chunks))
                for link in self._li_links:
                    link.context = context
                    self.links.append(link)
                self._li_chunks = []
                self._li_links = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self._capture_text(data)

    def _capture_text(self, text: str) -> None:
        if self._heading_tag:
            self._heading_chunks.append(text)
        if self._anchor_href is not None:
            self._anchor_chunks.append(text)
        if self._li_depth:
            self._li_chunks.append(text)


class MarkdownExtractor(HTMLParser):
    """Small HTML-to-Markdown-ish extractor tuned for AtCoder pages."""

    SKIP_TAGS = {"script", "style", "noscript", "svg"}
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    BLOCK_TAGS = {
        "article",
        "blockquote",
        "div",
        "dl",
        "fieldset",
        "form",
        "hr",
        "main",
        "nav",
        "p",
        "pre",
        "section",
        "table",
    }

    def __init__(self, *, base_url: str, target_ids: set[str] | None) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.target_ids = target_ids
        self.seen_target = target_ids is None
        self._active = target_ids is None
        self._active_depth = 0
        self._skip_depth = 0
        self._pre_depth = 0
        self._link_href: str | None = None
        self._link_chunks: list[str] = []
        self._list_depth = 0
        self._table_cell_open = False
        self._out: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        attrs_dict = dict(attrs)

        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        if self.target_ids is not None:
            if self._active:
                if tag not in self.VOID_TAGS:
                    self._active_depth += 1
            elif self._is_target(tag, attrs_dict):
                self.seen_target = True
                self._active = True
                self._active_depth = 1
            else:
                return

        if tag in self.BLOCK_TAGS:
            self._ensure_newlines(2)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            self._ensure_newlines(2)
            self._append_raw("#" * level + " ")
        elif tag == "br":
            self._ensure_newlines(1)
        elif tag == "pre":
            self._pre_depth += 1
            self._append_raw("```\n")
        elif tag == "ul" or tag == "ol":
            self._list_depth += 1
            self._ensure_newlines(1)
        elif tag == "li":
            self._ensure_newlines(1)
            self._append_raw("  " * max(0, self._list_depth - 1) + "- ")
        elif tag == "code" and not self._pre_depth:
            self._append_raw("`")
        elif tag == "a" and attrs_dict.get("href"):
            self._link_href = urllib.parse.urljoin(self.base_url, attrs_dict["href"])
            self._link_chunks = []
        elif tag == "img":
            src = attrs_dict.get("src")
            alt = attrs_dict.get("alt") or "image"
            if src:
                image_md = f"![{normalize_space(alt)}]({urllib.parse.urljoin(self.base_url, src)})"
                if self._link_href is not None:
                    self._link_chunks.append(normalize_space(alt))
                else:
                    self._append_text(image_md)
        elif tag in {"td", "th"}:
            if self._table_cell_open:
                self._append_raw(" | ")
            self._table_cell_open = True
        elif tag == "tr":
            self._ensure_newlines(1)
            self._table_cell_open = False

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if not self._active:
            return

        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "section"}:
            self._ensure_newlines(2)
        elif tag == "pre":
            self._pre_depth = max(0, self._pre_depth - 1)
            self._append_raw("\n```\n")
            self._ensure_newlines(2)
        elif tag == "ul" or tag == "ol":
            self._list_depth = max(0, self._list_depth - 1)
            self._ensure_newlines(1)
        elif tag == "li":
            self._ensure_newlines(1)
        elif tag == "code" and not self._pre_depth:
            self._append_raw("`")
        elif tag == "a" and self._link_href is not None:
            label = normalize_space("".join(self._link_chunks)) or self._link_href
            self._append_text(f"[{label}]({self._link_href})")
            self._link_href = None
            self._link_chunks = []
        elif tag == "tr":
            self._ensure_newlines(1)
            self._table_cell_open = False
        elif tag == "table":
            self._ensure_newlines(2)

        if self.target_ids is not None:
            self._active_depth -= 1
            if self._active_depth <= 0:
                self._active = False
                self._active_depth = 0

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not self._active:
            return
        if self._link_href is not None:
            self._link_chunks.append(data)
        elif self._pre_depth:
            self._append_raw(data)
        else:
            self._append_text(data)

    def text(self) -> str:
        return clean_markdown("".join(self._out))

    def _is_target(self, tag: str, attrs: dict[str, str | None]) -> bool:
        if tag == "main" and "main" in (self.target_ids or set()):
            return True
        element_id = attrs.get("id")
        return bool(element_id and element_id in (self.target_ids or set()))

    def _append_raw(self, text: str) -> None:
        if text:
            self._out.append(text)

    def _append_text(self, text: str) -> None:
        text = normalize_space(text)
        if not text:
            return
        if self._out:
            tail = self._out[-1]
            if tail and not tail.endswith((" ", "\n", "(", "[", "`")):
                self._out.append(" ")
        self._out.append(text)

    def _ensure_newlines(self, count: int) -> None:
        current = "".join(self._out[-4:])
        existing = len(current) - len(current.rstrip("\n"))
        if existing < count:
            self._out.append("\n" * (count - existing))


def extract_editorial_links(html: str, *, base_url: str, contest: str) -> list[EditorialLink]:
    parser = EditorialIndexParser(base_url=base_url, contest=contest)
    parser.feed(html)

    seen: set[str] = set()
    unique_links: list[EditorialLink] = []
    for link in parser.links:
        normalized = canonicalize_url(link.url)
        if normalized in seen:
            continue
        seen.add(normalized)
        link.url = normalized
        unique_links.append(link)
    return unique_links


def is_english_editorial_link(link: EditorialLink) -> bool:
    text = normalize_space(f"{link.label} {link.context}")
    if not text:
        return False
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    ascii_ratio = ascii_chars / len(text)
    if ascii_ratio < 0.8:
        return False
    lowered = text.lower()
    english_markers = ("editorial", "solution", "supplement", "alternative")
    return any(marker in lowered for marker in english_markers)


def html_to_markdown(html: str, *, base_url: str) -> str:
    candidates: tuple[set[str] | None, ...] = (
        {"main-div"},
        {"main"},
        {"main-container"},
        None,
    )
    for target_ids in candidates:
        parser = MarkdownExtractor(base_url=base_url, target_ids=target_ids)
        parser.feed(html)
        text = parser.text()
        if parser.seen_target and looks_like_editorial_text(text):
            return text
    return ""


def looks_like_editorial_text(text: str) -> bool:
    if len(text) < 200:
        return False
    lowered = text.lower()

    page_markers = ("posted:", "last update:")
    if any(marker in lowered for marker in page_markers):
        return True

    editorial_markers = (
        "editorial",
        "official",
        "user editorial",
        "\u89e3\u8aac",
        "there is no editorial yet",
    )
    body_markers = (
        "algorithm",
        "implementation",
        "sample code",
        "solution",
        "\u89e3\u6cd5",
        "\u5b9f\u88c5",
    )
    return any(marker in lowered for marker in editorial_markers) and any(
        marker in lowered for marker in body_markers
    )


def title_from_markdown(markdown: str, fallback: str) -> str:
    headings: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            headings.append(plain_markdown_heading(line.lstrip("#").strip()))
    for heading in headings:
        lowered = heading.lower()
        if heading and lowered not in {"editorial", "official", "user"}:
            if "editorial" in lowered or "\u89e3\u8aac" in heading:
                return heading
    for heading in headings:
        lowered = heading.lower()
        if heading and lowered not in {"editorial", "official", "user"}:
            return heading
    return fallback


def plain_markdown_heading(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return normalize_space(text)
