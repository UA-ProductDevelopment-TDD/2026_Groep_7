# docs-home

| | |
|---|---|
| Link in de slides | docs.petoi.com |
| Opgehaald van | https://docs.petoi.com/readme.md |
| Opgehaald op | 2026-10-06 |
| HTTP-status | 200 |
| Methode | GitBook-markdownexport (.md); GitBook-kop en -voettekst "Agent Instructions" weggelaten |

---

# Page Not Found

The URL `readme` does not exist. This page may have been moved, renamed, or deleted.

## Suggested Pages

You may be looking for one of the following:
- [Upload Firmware](https://docs.petoi.com/upload-firmware.md)
- [Getting Started Guide](https://docs.petoi.com/getting-started-guide.md)
- [Welcome to Petoi Doc Center for Bittle, Bittle X & Nybble](https://docs.petoi.com/master.md)
- [FAQ(Frequently Asked Questions)](https://docs.petoi.com/faq-frequently-asked-questions.md)
- [ROS and ROS2](https://docs.petoi.com/apis/ros-and-ros2.md)

## How to find the correct page

If the exact page cannot be found, you can still retrieve the information using the documentation query interface.

### Option 1 — Ask a question (recommended)

Perform an HTTP GET request on the documentation index with the `ask` parameter, and the optional `goal` parameter:

```
GET https://docs.petoi.com/upload-firmware.md?ask=<question>&goal=<end_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is optional and describes the broader end goal you are ultimately trying to accomplish on behalf of the user. GitBook uses it to tailor the answer towards what is most useful for that goal.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

### Option 2 — Browse the documentation index

Full index: https://docs.petoi.com/sitemap.md

Use this to discover valid page paths or navigate the documentation structure.

### Option 3 — Retrieve the full documentation corpus

Full export: https://docs.petoi.com/llms-full.txt

Use this to access all content at once and perform your own parsing or retrieval. It will be more expensive.

## Tips for requesting documentation

Prefer `.md` URLs for structured content, append `.md` to URLs (e.g., `/upload-firmware.md`).

You may also use `Accept: text/markdown` header for content negotiation.
