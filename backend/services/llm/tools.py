"""Document search tools for LLM-based termsheet extraction.

These tools close over a markdown string and allow the LLM agent to search,
read sections, list headings, and read arbitrary line ranges.
"""

import re

from langchain_core.tools import tool


def make_tools(markdown: str):
    """Create document search tools that close over the markdown text."""

    lines = markdown.splitlines()

    @tool
    def search_termsheet(query: str) -> str:
        """Search the termsheet for lines matching a keyword query.
        Returns matching lines with ±5 lines of context.
        Use this to find specific values like ISIN, dates, percentages, or any field."""
        query_lower = query.lower()
        matches = [i for i, line in enumerate(lines) if query_lower in line.lower()]

        if not matches:
            return f"No matches found for '{query}'."

        # Cap at 10 matches
        matches = matches[:10]

        results = []
        for match_idx in matches:
            start = max(0, match_idx - 5)
            end = min(len(lines), match_idx + 6)
            chunk = "\n".join(
                f"{'>>>' if j == match_idx else '   '} {lines[j]}"
                for j in range(start, end)
            )
            results.append(chunk)

        return f"Found {len(matches)} match(es) for '{query}':\n\n" + "\n---\n".join(results)

    @tool
    def read_section(heading: str) -> str:
        """Read a specific section of the termsheet by its heading.
        Uses fuzzy matching — you don't need the exact heading text.
        Returns everything from the heading to the next same-level heading."""
        heading_lower = heading.lower()

        # Find all markdown headings and their line numbers
        section_starts = []
        for i, line in enumerate(lines):
            if re.match(r"^#{1,3}\s", line):
                section_starts.append(i)

        # Find the best matching heading
        best_idx = None
        best_score = 0
        for start in section_starts:
            line_lower = lines[start].lower()
            terms = heading_lower.split()
            matched_terms = sum(1 for t in terms if t in line_lower)
            score = matched_terms / len(terms) if terms else 0
            if score > best_score:
                best_score = score
                best_idx = start

        if best_idx is None or best_score == 0:
            return f"No section matching '{heading}' found. Use list_sections() to see available headings."

        # Find the end of this section (next same-level or higher heading)
        heading_level = len(re.match(r"^(#+)", lines[best_idx]).group(1))
        end_idx = len(lines)
        for start in section_starts:
            if start > best_idx:
                other_level = len(re.match(r"^(#+)", lines[start]).group(1))
                if other_level <= heading_level:
                    end_idx = start
                    break

        section_text = "\n".join(lines[best_idx:end_idx])
        return f"Section '{lines[best_idx].strip()}':\n\n{section_text}"

    @tool
    def list_sections() -> str:
        """List all section headings in the termsheet.
        Use this first to understand the document structure before searching."""
        headings = []
        for i, line in enumerate(lines):
            if re.match(r"^#{1,3}\s", line):
                headings.append(f"  Line {i}: {line.strip()}")

        if not headings:
            return "No markdown headings found in this document."

        return "Document sections:\n" + "\n".join(headings)

    @tool
    def read_lines(start: int, end: int) -> str:
        """Read a range of lines from the termsheet (1-indexed, inclusive).
        Use after search_termsheet to read broader context around a match.
        For example, if a search hit is at line 135, call read_lines(120, 160)
        to see the full surrounding prose and tables."""
        start_idx = max(0, start - 1)  # convert to 0-indexed
        end_idx = min(len(lines), end)
        if start_idx >= end_idx:
            return "Invalid range. Start must be less than end."
        selected = lines[start_idx:end_idx]
        numbered = [f"{i + start_idx + 1:4d} | {line}" for i, line in enumerate(selected)]
        return "\n".join(numbered)

    return [search_termsheet, read_section, list_sections, read_lines]
