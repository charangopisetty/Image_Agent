from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    image_tags: list[str]
    scene_summary: str
    mood: str
    food_items: list[str] = Field(default_factory=list)


class CaptionDraft(BaseModel):
    caption: str
    caption_variants: list[str] = Field(min_length=2, max_length=2)
    cta: str | None = None


class SocialPostResponse(BaseModel):
    caption: str
    caption_variants: list[str]
    hashtags: list[str]
    image_tags: list[str]
    cta: str | None = None
    platform_notes: str
