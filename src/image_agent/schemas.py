from pydantic import BaseModel, Field, HttpUrl

from image_agent.models import SocialPostResponse


class BrandContext(BaseModel):
    business_name: str
    summary: str
    tone: str
    website_url: str = ""
    cuisine: str = ""
    location_hint: str = ""
    personality: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)


class PostOptions(BaseModel):
    max_hashtags: int = Field(default=15, ge=1, le=30)
    include_cta: bool = True
    locale: str = "en-US"


class SocialPostRequest(BaseModel):
    image_url: HttpUrl
    asset_type: str = Field(..., min_length=1, examples=["post"])
    brand_context: BrandContext
    options: PostOptions = Field(default_factory=PostOptions)


__all__ = [
    "BrandContext",
    "PostOptions",
    "SocialPostRequest",
    "SocialPostResponse",
]
