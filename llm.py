import requests
import json
import config

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/complete"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

def generate_completion(prompt, api="ollama", model=None, max_tokens=100):
    if api == "ollama":
        return ollama_completion(prompt, model or "llama2", max_tokens)
    elif api == "anthropic":
        return anthropic_completion(prompt, model or "claude-2", max_tokens)
    elif api == "groq":
        return groq_completion(prompt, model or "mixtral-8x7b-32768", max_tokens)
    else:
        raise ValueError("Invalid API specified. Choose 'ollama', 'anthropic', or 'groq'.")

def ollama_completion(prompt, model, max_tokens):
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
        return result.get('response', '')
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama API: {e}")
        return None

def anthropic_completion(prompt, model, max_tokens):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": config.anthropic_API_key,
        "anthropic-version": "2023-06-01"
    }

    payload = {
        "model": model,
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "max_tokens_to_sample": max_tokens,
        "stop_sequences": ["\n\nHuman:"]
    }

    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get('completion', '')
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Anthropic API: {e}")
        return None

def groq_completion(prompt, model, max_tokens):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.groq_API_key}"
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
        return None

def matched_service(buyer_description, seller_description, api="ollama"):
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
    buyer_request = "I need a robot to mow my lawn and trim the hedges in my garden."
    robot_capabilities = "Our robot can perform various gardening tasks including lawn mowing, hedge trimming, and weeding."

    print("Using Ollama API:")
    is_match_ollama = matched_service(buyer_request, robot_capabilities)
    print(f"Is there a match? {'Yes' if is_match_ollama else 'No'}")
