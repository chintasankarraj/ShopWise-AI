from app.agents.gemini_agent import client

import json
def analyze_price(product):

    prompt = f"""
You are ShopWise AI's Price Intelligence Agent.

Product:
{product.title}

Current Price:
{product.price}

Analyze:

1. Is the current price good?
2. Is it overpriced or underpriced?
3. Expected sale price.
4. Should the customer Buy Now or Wait?

Return only:

Current Value:
...

Expected Sale Price:
...

Buy Advice:
...

Reason:
...
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )
    print("=" * 50)
    print(response.text)
    print("=" * 50)

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)

    #return json.loads(response.text)