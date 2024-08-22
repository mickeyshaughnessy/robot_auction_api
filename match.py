import re
from match_data import default_matches

def normalize_text(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()

def matched_service(buyer_description, seller_description):
    buyer_words = set(normalize_text(buyer_description).split())
    seller_words = set(normalize_text(seller_description).split())
    
    # Direct word match
    if buyer_words & seller_words:
        return True
    
    # Category match
    buyer_categories = set()
    seller_categories = set()
    
    for category, keywords in default_matches.items():
        if any(word in buyer_words for word in keywords):
            buyer_categories.add(category)
        if any(word in seller_words for word in keywords):
            seller_categories.add(category)
    
    return bool(buyer_categories & seller_categories)

if __name__ == "__main__":
    buyer_request = "cleaning"
    robot_capabilities = "cleaning"
    
    is_match = matched_service(buyer_request, robot_capabilities)
    print(f"Is there a match? {'Yes' if is_match else 'No'}")
