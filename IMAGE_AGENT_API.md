# Image Agent API

Generate social media post content for **Instagram and Facebook** from a single food/restaurant image and brand context.

A vision model analyzes the image, an image analyst writes a creative brief, and a dedicated copywriter runs sequentially for each platform. The API returns one JSON object with a separate section per platform.

---

## Base URL

| Environment | URL                                                    |
| ----------- | ------------------------------------------------------ |
| Local       | `https://image-agent-385902914959.us-central1.run.app` |

Interactive docs: `GET /docs` (Swagger UI) · OpenAPI schema: `GET /openapi.json`

---

## Authentication

The API uses a static API key sent in the **`X-API-Key`** request header.

- The key is configured on the server via the `API_KEY` environment variable.
- If `API_KEY` is **set**, every protected request must include a matching key.
- If `API_KEY` is **not set** (e.g. local dev), auth is disabled and requests pass through.
- Keys are compared using a constant-time comparison to avoid timing attacks.

### Sending the key

Preferred — `X-API-Key` header:

```bash
curl -H "X-API-Key: $API_KEY" ...
```

Also accepted — `Authorization: Bearer` header:

```bash
curl -H "Authorization: Bearer $API_KEY" ...
```

### Public routes (no key required)

`/`, `/health`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico`

### Using it in Swagger (`/docs`)

1. Open `https://image-agent-385902914959.us-central1.run.app/docs`
2. Expand `POST /create_social_post` → **Try it out**
3. Paste your key into the **`X-API-Key`** field under **Parameters**
4. Fill the request body → **Execute**

### Failure response (`401 Unauthorized`)

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Invalid or missing API key.",
    "status": 401,
    "detail": "Send your API key via X-API-Key header or Authorization: Bearer <key>."
  }
}
```

---

## Endpoints

### `GET /health`

Liveness check. No auth required.

```json
{ "status": "ok" }
```

### `POST /create_social_post`

Generate per-platform social post content. Requires the API key when configured.

---

## Request

`Content-Type: application/json`

### Body fields

| Field           | Type         | Required | Description                               |
| --------------- | ------------ | -------- | ----------------------------------------- |
| `image_url`     | string (URL) | ✅       | Public HTTPS URL of the image to analyze. |
| `asset_type`    | string       | ✅       | Type of asset, e.g. `"post"`, `"story"`.  |
| `brand_context` | object       | ✅       | Brand details (see below).                |
| `options`       | object       | ❌       | Generation options (see below).           |

#### `brand_context`

| Field           | Type     | Required | Default | Description                                  |
| --------------- | -------- | -------- | ------- | -------------------------------------------- |
| `business_name` | string   | ✅       | —       | Business name.                               |
| `summary`       | string   | ✅       | —       | Short description of the business.           |
| `tone`          | string   | ✅       | —       | Desired voice, e.g. `"warm, casual, local"`. |
| `website_url`   | string   | ❌       | `""`    | Website URL.                                 |
| `cuisine`       | string   | ❌       | `""`    | Cuisine / category.                          |
| `location_hint` | string   | ❌       | `""`    | City/area for local tags.                    |
| `personality`   | string[] | ❌       | `[]`    | Personality traits.                          |
| `colors`        | string[] | ❌       | `[]`    | Brand colors (hex or names).                 |

#### `options`

| Field          | Type           | Required | Default   | Description                          |
| -------------- | -------------- | -------- | --------- | ------------------------------------ |
| `max_hashtags` | integer (1–30) | ❌       | `15`      | Max hashtags for Instagram/Facebook. |
| `include_cta`  | boolean        | ❌       | `true`    | Whether to include a call to action. |
| `locale`       | string         | ❌       | `"en-US"` | Locale for the copy.                 |

### Example request

```json
{
  "image_url": "https://ik.imagekit.io/fooai/socials/example/food.jpeg",
  "asset_type": "post",
  "brand_context": {
    "business_name": "Dates and Olives",
    "website_url": "https://datesandolives.com",
    "summary": "Family-owned business that sells Mediterranean food.",
    "tone": "warm, casual, local",
    "cuisine": "Middle Eastern",
    "location_hint": "Natick, MA",
    "personality": ["friendly", "authentic"],
    "colors": ["#C0392B", "#F5E6CA"]
  },
  "options": {
    "max_hashtags": 15,
    "include_cta": true,
    "locale": "en-US"
  }
}
```

### `curl`

```bash
curl -X POST http://127.0.0.1:8080/create_social_post \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d @examples/request.json
```

---

## Response

`200 OK` — a JSON object with one section per platform plus shared `image_tags`.

### Schema

| Field        | Type     | Description                                        |
| ------------ | -------- | -------------------------------------------------- |
| `instagram`  | object   | Instagram content.                                 |
| `facebook`   | object   | Facebook content.                                  |
| `image_tags` | string[] | Tags extracted from the image by the vision model. |

**Instagram** — `caption`, `caption_variants` (string[]), `hashtags` (string[]), `cta` (string \| null), `platform_notes` (string)

**Facebook** — `caption`, `caption_variants` (string[]), `hashtags` (string[]), `cta` (string \| null), `platform_notes` (string)

### Example response

```json
{
  "instagram": {
    "caption": "Golden spiral pasta meets Mediterranean flair 🍝 Fresh asparagus, chickpeas, and herbs, straight from our Natick kitchen.",
    "caption_variants": [
      "Spring on a plate — veggie-packed fusilli with a Middle Eastern twist.",
      "From our kitchen to your table: fresh, bright, and full of flavor."
    ],
    "hashtags": [
      "#MediterraneanEats",
      "#NattickFoodie",
      "#DatesAndOlives",
      "#LocalEats",
      "#FreshFlavors"
    ],
    "cta": "Tap the link in bio",
    "platform_notes": "Under 2200 chars; up to 15 hashtags."
  },
  "facebook": {
    "caption": "Feeling the warmth of the Mediterranean in every bite 🌞 Our fusilli bowl is a Natick favorite. Fresh? Just ask our locals!",
    "caption_variants": [
      "Lunch-break magic: spiral pasta, fresh veggies, and herbs.",
      "Cozy vibes on a plate — come try it today."
    ],
    "hashtags": ["#NattickMA", "#DatesAndOlives", "#MiddleEasternCuisine"],
    "cta": "Link in bio for online ordering",
    "platform_notes": "Conversational, community-focused; local tags."
  },
  "image_tags": [
    "pasta",
    "asparagus",
    "chickpeas",
    "white bowl",
    "wooden table"
  ]
}
```

---

## Errors

All errors share a consistent envelope:

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "LLM provider rate limit reached. Wait and retry.",
    "status": 429,
    "detail": "Optional technical detail."
  }
}
```

| HTTP status | `code`                 | When                                                             |
| ----------- | ---------------------- | ---------------------------------------------------------------- |
| 401         | `unauthorized`         | Missing or invalid API key.                                      |
| 422         | `validation_error`     | Invalid request body (e.g. bad `image_url`).                     |
| 422         | `vision_error`         | Image analysis failed (verify public HTTPS URL / vision model).  |
| 429         | `rate_limit_exceeded`  | LLM provider rate limit hit — retry after `Retry-After` seconds. |
| 413         | `context_too_large`    | Input exceeds model context window.                              |
| 502         | `authentication_error` | LLM provider rejected its API key (server-side).                 |
| 503         | `upstream_unavailable` | LLM provider unreachable/unavailable.                            |
| 504         | `upstream_timeout`     | LLM request timed out.                                           |
| 500         | `generation_failed`    | Unexpected generation failure.                                   |

---

## Configuration

Set via environment variables (`.env` for local, or your deploy platform):

| Variable         | Required | Description                                     |
| ---------------- | -------- | ----------------------------------------------- |
| `OPENAI_API_KEY` | ✅       | OpenAI API key for ChatGPT Luna (`gpt-6-luna`). |
| `API_KEY`        | ❌       | If set, clients must send it via `X-API-Key`.   |
| `MODEL`          | ❌       | Text model (default `openai/gpt-6-luna`).       |
| `VISION_MODEL`   | ❌       | Vision model (default `openai/gpt-6-luna`).     |

---

## Running locally

```bash
# start the API (http://127.0.0.1:8080)
uv run dev-api

# or run the crew directly on the example (no server)
uv run run_with_trigger examples/request.json
```
