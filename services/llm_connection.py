from openai import AzureOpenAI #type: ignore
from utils.config import ai_config
def get_azure_response(text):  
    try:
        endpoint=ai_config.endpoint
        deployment=ai_config.deployment
        subscription_key=ai_config.subscription_key
        api_version=ai_config.api_version
        print("=+="*30)
        print(endpoint, deployment, subscription_key, api_version)
        
        if not subscription_key:
            return "Error: AZURE_OPENAI_KEY not found in environment variables"
        
        client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
        )
        
        response = client.chat.completions.create(
        messages=[
        {
        "role": "system",
        "content": "You are a helpful assistant.",
        },
        {
        "role": "user",
        "content": text,
        }
        ],
        
        model=deployment
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return {"Azure Error": {str(e)},
        "endpoint": {endpoint},
        "deployment": {deployment},
        "subscription_key": {subscription_key},
        "api_version": {api_version}
        }
        
if __name__ == "__main__":
    print(get_azure_response("Hello, how are you?"))