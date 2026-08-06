"""LLM validation boundary. Keep reviewer evidence and never overwrite auto decisions silently."""
PROMPT_TEMPLATE = """Decide whether these describe the same sellable product. Return JSON only with same_product (boolean), confidence (0..1), and reason.\nA: {left}\nB: {right}"""

def build_prompt(left: str, right: str) -> str:
    return PROMPT_TEMPLATE.format(left=left, right=right)
