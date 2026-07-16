# PursuitAI Social Engine

Fully autonomous social media marketing for [pursuitai.net](https://pursuitai.net) — generates branded content, live site screenshots, and short videos, then posts to X (@pursuit_ai) and Instagram daily via the official APIs. Runs free on GitHub Actions.

```
.github/workflows/daily.yml   cron: Mon–Sat 9:30 AM ET → prepare → commit → publish
engine/
  run.py          orchestrator (topic + format rotation, state, logging)
  cards.py        branded 1080x1350 / 1600x900 feature cards (PIL)
  screenshots.py  live-site captures via Playwright, platform-cropped
  video.py        ~13s vertical videos via PIL + ffmpeg (Reels / X)
  captions.py     platform captions; Claude-fresh variants if ANTHROPIC_API_KEY set
  post_x.py       X API v2 + media upload (tweepy)
  post_ig.py      Instagram Graph API (image + Reels publish)
content/
  calendar.json   brand config + 24 feature topics (single source of truth)
  state.json      rotation cursor (committed by the bot)
  posts_preview_14days.md   what the first two weeks look like
assets/           generated cards / screenshots / video (committed so IG can fetch)
logs/posted.jsonl every post: date, topic, format, IDs, captions
```

**Setup:** see [SETUP.md](SETUP.md). **Kill switch:** disable the workflow in the Actions tab.
