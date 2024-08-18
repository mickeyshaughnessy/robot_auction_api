import requests
import json
from config import anthropic_API_key, groq_API_key

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_completion(prompt, api="anthropic", model=None, max_tokens=100):
    """
    Generate a completion using either the Anthropic or Groq API.
    :param prompt: The input prompt for the model
    :param api: The API to use ("anthropic" or "groq")
    :param model: The model to use (default is None, which uses API-specific defaults)
    :param max_tokens: Maximum number of tokens to generate (default is 100)
    :return: The generated text
    """
    if api == "anthropic":
        return anthropic_completion(prompt, model or "claude-3-opus-20240229", max_tokens)
    elif api == "groq":
        return groq_completion(prompt, model or "mixtral-8x7b-32768", max_tokens)
    else:
        raise ValueError("Invalid API specified. Choose 'anthropic' or 'groq'.")

def anthropic_completion(prompt, model, max_tokens):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": anthropic_API_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text']
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Anthropic API: {e}")
        if response.text:
            print(f"Response content: {response.text}")
        return None

def groq_completion(prompt, model, max_tokens):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {groq_API_key}"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Groq API: {e}")
        if response.text:
            print(f"Response content: {response.text}")
        return None

def matched_service(buyer_description, seller_description, api="anthropic"):
    """
    Determine if a robot owner's services match a buyer's requirements.
    :param buyer_description: A string describing the service the buyer wants
    :param seller_description: A string describing the robot's capabilities
    :param api: The API to use ("anthropic" or "groq")
    :return: True if there's a match, False otherwise
    """
    prompt = f"""
Buyer's service request: {buyer_description}
Robot owner's service offering: {seller_description}
Based on the descriptions above, determine if the robot's capabilities match the buyer's requirements.
Answer with only 'True' if there's a match, or 'False' if there isn't a match.
"""
    response = generate_completion(prompt, api=api)
    if response:
        return response.strip().lower() == 'true'
    else:
        return False

if __name__ == "__main__":
    # Example usage
    buyer_request = "I need a robot to mow my lawn and trim the hedges in my garden."
    robot_capabilities = "Our robot can perform various gardening tasks including lawn mowing, hedge trimming, and weeding."
    
    print("Using Anthropic API:")
    is_match_anthropic = matched_service(buyer_request, robot_capabilities, api="anthropic")
    print(f"Is there a match? {'Yes' if is_match_anthropic else 'No'}")
    
    print("\nUsing Groq API:")
    is_match_groq = matched_service(buyer_request, robot_capabilities, api="groq")
    print(f"Is there a match? {'Yes' if is_match_groq else 'No'}")
