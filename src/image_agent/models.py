from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    image_tags: list[str]
    scene_summary: str
    mood: str
    food_items: list[str] = Field(default_factory=list)


class InstagramPostContent(BaseModel):
    caption: str
    caption_variants: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    cta: str | None = None
    platform_notes: str = ""


class FacebookPostContent(BaseModel):
    caption: str
    caption_variants: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    cta: str | None = None
    platform_notes: str = ""


class SocialPostResponse(BaseModel):
    instagram: InstagramPostContent
    facebook: FacebookPostContent
    image_tags: list[str] = Field(default_factory=list)
