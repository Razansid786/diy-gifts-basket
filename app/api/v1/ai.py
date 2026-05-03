
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.db.session import get_db
from app.services.product_service import ProductService
from app.services.basket_service import BasketService
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/ai", tags=["AI"])

class ChatRequest(BaseModel):
    message: str
    current_step: Optional[int] = 1
    selected_base_id: Optional[str] = None
    selected_product_ids: List[str] = []

class ChatResponse(BaseModel):
    reply: str
    suggested_step: int
    recommendations: List[ProductResponse] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Groq API key not configured. Set GROQ_API_KEY in your .env file."
        )

    client = AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

    product_service = ProductService(db)
    basket_service = BasketService(db)

    try:
        products = await product_service.list_products(limit=100)
        bases = await basket_service.list_bases()

        catalog_summary = "AVAILABLE BASES:\n"
        for b in bases:
            catalog_summary += f"- {b.name} (ID: {b.id}, Price: ${b.price}, Capacity: {b.max_items} items)\n"

        catalog_summary += "\nAVAILABLE PRODUCTS:\n"
        for p in products:
            if getattr(p, 'inventory_count', 0) > 0:
                catalog_summary += f"- {p.title} (ID: {p.id}, Price: ${p.price}, Description: {p.description})\n"
    except Exception as e:
        print(f"Error gathering catalog: {e}")
        catalog_summary = "Catalog currently unavailable."

    system_prompt = f"""You are the 'DIY Gift Basket' Assistant. Give short, accurate guidance for the CURRENT step only.

CURRENT STEP: {request.current_step}

Step 1 — Base Selection: The user picks a container (basket/box) to hold their gifts. Name EXACTLY 1 base, or 2 at most. Hard limit — do not mention a third option under any circumstances.
Step 2 — Product Selection: The user adds individual products to fill their basket. Recommend up to 2 products from the catalog.
Step 3 — Personalization: The user fills in a TEXT MESSAGE field (just a written note), picks a RIBBON COLOR from a dropdown (Ruby Red, Saffron Gold, Ocean Teal, Ivory Pearl, or None), and sets an optional delivery date. There is NO gift card to select, NO products to add here. Only guide them on what to write in their message and which ribbon to pick.
Step 4 — Review: The user is reviewing their completed basket. Do NOT suggest adding items or making changes. Simply acknowledge what they have built and encourage them to click "Add to cart."

STRICT RULES:
- ONLY respond about step {request.current_step}. Never mention other steps.
- Suggest AT MOST 2 items from the catalog. Never suggest 3 or more.
- Keep the reply to 1-2 sentences.
- For step 3: never mention gift cards, never suggest adding products. Only mention the message field and ribbon color.
- For step 4: never suggest adding anything. Only praise the basket and encourage completing.
- Use warm, premium language.

CATALOG:
{catalog_summary}

USER STATE:
- Base selected: {request.selected_base_id or 'None'}
- Products added: {', '.join(request.selected_product_ids) if request.selected_product_ids else 'None'}"""

    try:
        completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        reply_text = completion.choices[0].message.content or ""

        suggested_step = request.current_step
        if not request.selected_base_id:
            suggested_step = 1
        elif not request.selected_product_ids:
            suggested_step = 2
        else:
            suggested_step = 3

        recommendations = []
        for p in products:
            if p.id in reply_text or (p.title and p.title.lower() in reply_text.lower()):
                try:
                    from pydantic import TypeAdapter
                    adapter = TypeAdapter(ProductResponse)
                    validated_p = adapter.validate_python(p)
                    recommendations.append(validated_p)
                except Exception:
                    continue
                if len(recommendations) >= 4:
                    break

        return ChatResponse(
            reply=reply_text,
            suggested_step=suggested_step,
            recommendations=recommendations
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
