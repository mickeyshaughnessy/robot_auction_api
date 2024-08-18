import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def generate_completion(prompt, model="phi", max_tokens=100):
    """
    Generate a completion using the Ollama API.

    :param prompt: The input prompt for the model
    :param model: The model to use (default is "phi")
    :param max_tokens: Maximum number of tokens to generate (default is 100)
    :return: The generated text
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['response']
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama API: {e}")
        return None

def matched_service(buyer_description, seller_description):
    """
    Determine if a robot owner's services match a buyer's requirements.

    :param buyer_description: A string describing the service the buyer wants
    :param seller_description: A string describing the robot's capabilities
    :return: True if there's a match, False otherwise
    """
    prompt = f"""
Buyer's service request: {buyer_description}
Robot owner's service offering: {seller_description}

Based on the descriptions above, determine if the robot's capabilities match the buyer's requirements.
Answer with only 'True' if there's a match, or 'False' if there isn't a match.
"""

    response = generate_completion(prompt)
    if response:
        return response.strip().lower() == 'true'
    else:
        return False

if __name__ == "__main__":
    # Example usage
    buyer_request = "I need a robot to mow my lawn and trim the hedges in my garden."
    robot_capabilities = "Our robot can perform various gardening tasks including lawn mowing, hedge trimming, and weeding."

    is_match = matched_service(buyer_request, robot_capabilities)
    print(f"Is there a match? {'Yes' if is_match else 'No'}")
