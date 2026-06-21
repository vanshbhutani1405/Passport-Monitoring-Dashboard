import logging
from datetime import datetime, UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.analysis import Analysis
from app.models.post import Post
from app.models.translation import Translation
from app.nlp.groq_analyzer import GroqAnalyzer


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/translate", tags=["translate"])


class TranslateRequest(BaseModel):
    target_language: str
    translate_summary_only: bool = False


class TranslateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    post_id: UUID
    language: str
    translated_text: str


SUPPORTED_LANGUAGES = {
    "English": "english",
    "Hindi": "hindi",
    "Punjabi": "punjabi",
    "Spanish": "spanish",
    "French": "french",
    "German": "german",
    "Arabic": "arabic",
    "Chinese": "chinese",
    "Russian": "russian",
    "Japanese": "japanese",
}


@router.post("/{post_id}", response_model=TranslateResponse)
def translate_post(
    post_id: UUID, request: TranslateRequest, db: Session = Depends(get_db)
) -> TranslateResponse:
    try:
        target_lang_key = request.target_language.strip()
        normalized_target = SUPPORTED_LANGUAGES.get(target_lang_key, target_lang_key.lower())
        normalized_target = next(
            (k.lower() for k in SUPPORTED_LANGUAGES if k.lower() == normalized_target),
            normalized_target,
        )
        if normalized_target not in [v.lower() for v in SUPPORTED_LANGUAGES.values()]:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {target_lang_key}. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}")

        post = db.scalar(
            select(Post)
            .where(Post.id == post_id)
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing_translation = db.scalar(
            select(Translation)
            .where(Translation.post_id == post_id, Translation.target_language == normalized_target)
        )

        analysis = db.scalar(select(Analysis).where(Analysis.post_id == post_id))
        source_language = analysis.language if analysis else "unknown"
        
        if request.translate_summary_only:
            content_to_translate = analysis.summary if analysis and analysis.summary else (post.title or post.content)
            cache_key_prefix = "summary_"
        else:
            content_to_translate = f"{post.title or ''}\n{post.content}".strip()
            cache_key_prefix = "full_"

        normalized_target_with_prefix = f"{cache_key_prefix}{normalized_target}"
        # Check existing translation with prefix
        existing_translation = db.scalar(
            select(Translation)
            .where(Translation.post_id == post_id, Translation.target_language == normalized_target_with_prefix)
        )

        if existing_translation:
            return TranslateResponse(
                post_id=post.id,
                language=request.target_language,
                translated_text=existing_translation.translated_content
            )

        if not content_to_translate:
            return TranslateResponse(
                post_id=post.id,
                language=request.target_language,
                translated_text="No content to translate"
            )

        groq_analyzer = GroqAnalyzer(get_settings())
        client = groq_analyzer._get_client()

        system_prompt = f"Translate the following text to {target_lang_key}. Only return the translated text, no extra comments or explanations."

        response = client.chat.completions.create(
            model=get_settings().groq_model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_to_translate[:6000]},
            ],
        )

        translated_text = response.choices[0].message.content.strip() if response.choices and response.choices[0].message.content else ""

        new_translation = Translation(
            post_id=post_id,
            source_language=source_language,
            target_language=normalized_target_with_prefix,
            translated_content=translated_text,
            translated_at=datetime.now(UTC),
        )
        db.add(new_translation)
        db.commit()
        db.refresh(new_translation)

        return TranslateResponse(
            post_id=post.id,
            language=request.target_language,
            translated_text=translated_text
        )

    except SQLAlchemyError:
        logger.exception("Failed to translate post_id=%s", post_id)
        raise HTTPException(status_code=500, detail="Failed to translate post")
    except Exception as e:
        logger.exception("Unexpected error translating post_id=%s", post_id)
        raise HTTPException(status_code=500, detail=str(e))
