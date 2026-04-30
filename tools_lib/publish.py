"""tools_lib/publish.py — Publishing integrations for DataAgent.

Slack  : requires SLACK_WEBHOOK_URL in .env
Console: always available (fallback when no webhook configured)
File   : always available (saves to data/published/)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path("data/published")


class PublishTools:
    def __init__(self, slack_webhook_url: str = ""):
        self.slack_webhook_url = slack_webhook_url
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Slack
    # -------------------------------------------------------------------------

    async def publish_to_slack(self, content: str, title: str = "Open Claw Report") -> bool:
        if not self.slack_webhook_url:
            print(f"[publish] Slack webhook not configured. Set SLACK_WEBHOOK_URL in .env")
            return False

        import httpx

        payload = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": title}},
                {"type": "section", "text": {"type": "mrkdwn", "text": content[:2900]}},
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"_Published by Open Claw · {datetime.now().strftime('%Y-%m-%d %H:%M')}_"}
                    ],
                },
            ]
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.slack_webhook_url, json=payload)

        if resp.status_code == 200:
            print(f"[publish] Slack: posted '{title}'")
            return True
        else:
            print(f"[publish] Slack error: {resp.status_code} {resp.text}")
            return False

    # -------------------------------------------------------------------------
    # File (always available)
    # -------------------------------------------------------------------------

    def save_to_file(self, content: str, title: str = "report") -> Path:
        slug = title.lower().replace(" ", "_")[:40]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"{timestamp}_{slug}.md"
        path.write_text(f"# {title}\n\n{content}\n\n_Published: {datetime.now().isoformat()}_\n")
        print(f"[publish] Saved to {path}")
        return path

    # -------------------------------------------------------------------------
    # Console (always available — useful for testing)
    # -------------------------------------------------------------------------

    def publish_to_console(self, content: str, title: str = "Report"):
        width = 60
        print(f"\n{'─' * width}")
        print(f"  {title}")
        print(f"{'─' * width}")
        print(content)
        print(f"{'─' * width}\n")

    # -------------------------------------------------------------------------
    # Combined publish — tries Slack, always saves to file
    # -------------------------------------------------------------------------

    async def publish(self, content: str, title: str = "Open Claw Report") -> dict:
        results = {"file": None, "slack": False, "console": True}

        self.publish_to_console(content, title)
        results["file"] = str(self.save_to_file(content, title))

        if self.slack_webhook_url:
            results["slack"] = await self.publish_to_slack(content, title)

        return results
