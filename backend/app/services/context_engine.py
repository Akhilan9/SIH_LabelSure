from typing import Dict, Any, List
from backend.app.models import ProductContext, Declaration

FOOD_KEYWORDS = [
    "food", "snack", "flour", "atta", "oil", "biscuit", "cookie", "rice",
    "tea", "coffee", "milk", "spice", "masala", "beverage", "juice",
    "fssai", "ingredients", "nutritional", "veg", "non-veg"
]

DOMESTIC_KEYWORDS = ["india", "bharat", "delhi", "mumbai", "bengaluru", "chennai", "kolkata", "hyderabad", "pune"]

def enrich_context_from_declarations(
    context: ProductContext,
    declarations: List[Dict[str, Any]],
    ocr_full_text: str
) -> ProductContext:
    """
    Intelligently infers commodity context cues from raw declarations and full text,
    without overriding explicit human inspector edits.
    """
    text_lower = ocr_full_text.lower()
    
    # 1. Food vs Non-Food inference
    if not context.is_food:
        if any(kw in text_lower for kw in FOOD_KEYWORDS):
            context.is_food = True
            if context.commodity_category == "GENERAL_COMMODITY":
                context.commodity_category = "FOOD_BEVERAGE"
                
    # 2. Origin country & import status inference
    for decl in declarations:
        if decl.get("category") == "COUNTRY_OF_ORIGIN":
            val = str(decl.get("normalized_value") or decl.get("raw_text", "")).strip().lower()
            if val:
                context.origin_country = val.title()
                if not any(dom in val for dom in DOMESTIC_KEYWORDS):
                    context.is_imported = True
                    
        elif decl.get("category") == "NET_QUANTITY":
            norm = decl.get("normalized_value")
            if isinstance(norm, dict):
                context.declared_net_quantity = norm.get("value")
                context.declared_unit = norm.get("unit")
                
    return context
