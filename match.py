import re

def normalize_text(text):
    return re.sub(r'\W+', ' ', text.lower()).strip()

def matched_service(buyer_description, seller_description):
    buyer_words = set(normalize_text(buyer_description).split())
    seller_words = set(normalize_text(seller_description).split())
    
    required_matches = {
        'lawn': ['lawn', 'mow', 'grass', 'yard', 'turf', 'landscaping'],
        'hedge': ['hedge', 'trim', 'prune', 'shear', 'topiary'],
        'garden': ['garden', 'plant', 'weed', 'cultivate', 'horticulture', 'flowerbed'],
        'cleaning': ['clean', 'vacuum', 'dust', 'mop', 'scrub', 'sanitize', 'disinfect'],
        'security': ['security', 'patrol', 'monitor', 'surveillance', 'guard', 'protect'],
        'delivery': ['deliver', 'transport', 'carry', 'courier', 'shipment', 'logistics'],
        'painting': ['paint', 'coat', 'varnish', 'stain', 'touch-up', 'spraying'],
        'plumbing': ['plumb', 'pipe', 'faucet', 'drain', 'leak', 'toilet', 'sink'],
        'electrical': ['electric', 'wiring', 'circuit', 'outlet', 'switch', 'lighting'],
        'carpentry': ['carpentry', 'woodwork', 'build', 'construct', 'repair', 'furniture'],
        'hvac': ['hvac', 'heating', 'cooling', 'ventilation', 'air conditioning', 'thermostat'],
        'roofing': ['roof', 'shingle', 'tile', 'gutter', 'flashing', 'waterproof'],
        'pet_care': ['pet', 'dog', 'cat', 'walk', 'feed', 'groom', 'sit'],
        'automotive': ['car', 'vehicle', 'repair', 'maintenance', 'oil change', 'tire'],
        'moving': ['move', 'relocate', 'pack', 'unpack', 'furniture', 'box', 'truck'],
        'window': ['window', 'glass', 'clean', 'wash', 'squeegee', 'pane'],
        'pest_control': ['pest', 'insect', 'rodent', 'exterminate', 'spray', 'trap'],
        'snow_removal': ['snow', 'ice', 'shovel', 'plow', 'salt', 'de-ice'],
        'pool': ['pool', 'swim', 'chlorine', 'filter', 'clean', 'maintenance'],
        'trash': ['trash', 'garbage', 'waste', 'dispose', 'recycle', 'bin'],
        'catering': ['cater', 'food', 'cook', 'serve', 'meal', 'prepare'],
        'photography': ['photo', 'camera', 'shoot', 'picture', 'portrait', 'event'],
        'tutoring': ['tutor', 'teach', 'lesson', 'education', 'homework', 'study'],
        'fitness': ['fitness', 'exercise', 'train', 'workout', 'gym', 'personal trainer'],
        'massage': ['massage', 'therapy', 'spa', 'relax', 'knead', 'bodywork'],
        'computer': ['computer', 'it', 'tech support', 'software', 'hardware', 'network'],
        'event_planning': ['event', 'plan', 'organize', 'party', 'wedding', 'coordinate'],
        'interior_design': ['interior', 'design', 'decorate', 'furnish', 'style', 'remodel'],
        'translation': ['translate', 'interpret', 'language', 'bilingual', 'localize'],
        'tax_preparation': ['tax', 'accounting', 'bookkeeping', 'financial', 'prepare', 'file']
    }

    buyer_category = None
    for category, keywords in required_matches.items():
        if any(word in buyer_words for word in keywords):
            buyer_category = category
            break
    
    if buyer_category is None:
        return False

    seller_categories = [category for category, keywords in required_matches.items()
                         if any(word in seller_words for word in keywords)]
    
    is_match = buyer_category in seller_categories
    
    return is_match

if __name__ == "__main__":
    buyer_request = "I need someone to mow my lawn."
    robot_capabilities = "Our service robots can handle various tasks including lawn care, gardening, window washing, and general home maintenance."
    
    is_match = matched_service(buyer_request, robot_capabilities)
    print(f"Is there a match? {'Yes' if is_match else 'No'}")
