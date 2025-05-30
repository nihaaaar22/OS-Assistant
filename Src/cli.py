import click
import json
import os
import inquirer
import shutil
from OpenCopilot import OpenCopilot
from dotenv import load_dotenv

# Define available models for each provider using litellm compatible strings
AVAILABLE_MODELS = {
    "openai": [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "openai/gpt-4-turbo-preview",
        "openai/gpt-4o" 
    ],
    "mistral": [
        "mistral/mistral-tiny",
        "mistral/mistral-small",
        "mistral/mistral-medium",
        "mistral/mistral-large-latest"
    ],
    "groq": [
        "groq/llama2-70b-4096", 
        "groq/mixtral-8x7b-32768",
        "groq/gemma-7b-it"
    ],
    "anthropic": [
        "anthropic/claude-3-opus-20240229",
        "anthropic/claude-3-sonnet-20240229",
        "anthropic/claude-3-haiku-20240307"
    ]
}

# Define API key environment variables for each provider (matching litellm conventions)
API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY"
}

def get_provider_from_model_name(model_name: str) -> str:
    """Extracts the provider from a litellm model string (e.g., 'openai/gpt-4o' -> 'openai')."""
    if not model_name or '/' not in model_name:
        # Fallback or error handling if model_name is not in expected format
        # For now, try to return the model_name itself if it doesn't contain '/',
        # as it might be a provider name already or an old format.
        # This case should ideally be handled based on how robust the system needs to be.
        print(f"Warning: Model name '{model_name}' may not be in 'provider/model' format. Attempting to use as provider.")
        return model_name 
    return model_name.split('/')[0]

def clear_terminal():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def ensure_api_key(provider):
    """Ensure API key exists for the given provider"""
    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    env_var = API_KEYS.get(provider)
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Force reload of .env file
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    
    # Check if API key exists in environment
    api_key = os.getenv(env_var)
    
    if not api_key:
        # Ask for API key
        questions = [
            inquirer.Text('api_key',
                message=f"Enter your {provider.upper()} API key",
                validate=lambda _, x: len(x.strip()) > 0
            )
        ]
        api_key = inquirer.prompt(questions)['api_key']
        clear_terminal()
        
        # Save to .env file
        if not os.path.exists(env_path):
            with open(env_path, 'w') as f:
                f.write(f"{env_var}={api_key}\n")
        else:
            # Read existing .env file
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Check if key already exists
            key_exists = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{env_var}=") or line.strip().startswith(f"#{env_var}="):
                    lines[i] = f"{env_var}={api_key}\n"
                    key_exists = True
                    break
            
            # If key doesn't exist, append it
            if not key_exists:
                lines.append(f"{env_var}={api_key}\n")
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(lines)
        
        # Reload environment with new key
        load_dotenv(env_path, override=True)
    
    return api_key

def ensure_config_exists():
    """Ensure config.json exists and has required fields"""
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    config = None
    
    if not os.path.exists(config_path):
        # Copy config from example if it doesn't exist
        example_path = os.path.join(os.path.dirname(__file__), '../config.example.json')
        if os.path.exists(example_path):
            shutil.copy2(example_path, config_path)
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            # Create a default config if example is missing
            config = {
                "working_directory": os.getcwd(),
                "llm_provider": None, # Will store the provider part, e.g., "openai"
                "model_name": None    # Will store the full litellm string, e.g., "openai/gpt-4o"
            }
    else:
        # Read existing config
        with open(config_path, 'r') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print("Error reading config.json. File might be corrupted. Re-creating default.")
                config = {
                    "working_directory": os.getcwd(),
                    "llm_provider": None,
                    "model_name": None
                }

    # Ensure 'working_directory' exists, default if not
    if "working_directory" not in config or not config["working_directory"]:
        config["working_directory"] = os.getcwd()

    # Check if model configuration is needed
    if not config.get("model_name") or not config.get("llm_provider"):
        print("LLM provider or model not configured.")
        questions = [
            inquirer.List('provider_key',
                message="Select LLM Provider",
                choices=list(AVAILABLE_MODELS.keys()) # User selects "openai", "mistral", etc.
            )
        ]
        selected_provider_key = inquirer.prompt(questions)['provider_key']
        clear_terminal()
        
        # Ensure API key exists for the selected provider
        ensure_api_key(selected_provider_key) # Uses "openai", "mistral", etc.
        
        questions = [
            inquirer.List('model_name_full',
                message=f"Select {selected_provider_key} Model",
                choices=AVAILABLE_MODELS[selected_provider_key] # Shows "openai/gpt-3.5-turbo", etc.
            )
        ]
        selected_model_name_full = inquirer.prompt(questions)['model_name_full']
        clear_terminal()
        
        config["llm_provider"] = selected_provider_key # Store "openai"
        config["model_name"] = selected_model_name_full # Store "openai/gpt-4o"
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved: Provider '{selected_provider_key}', Model '{selected_model_name_full}'")

    else:
        # Config exists, ensure API key for the stored provider
        # llm_provider should already be the provider part, e.g., "openai"
        # If old config only had model_name, try to parse provider from it
        provider_to_check = config.get("llm_provider")
        if not provider_to_check and config.get("model_name"):
            provider_to_check = get_provider_from_model_name(config["model_name"])
            # Optionally, update config if llm_provider was missing
            if provider_to_check != config.get("llm_provider"): # Check if it's different or was None
                config["llm_provider"] = provider_to_check
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)

        if provider_to_check:
             ensure_api_key(provider_to_check)
        else:
            # This case should ideally be handled by the initial setup logic
            print("Warning: Could not determine LLM provider from config to ensure API key.")


    # Create config file if it was created from scratch without example
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
    return config_path

@click.group(invoke_without_command=True)
@click.option('--task', '-t', help='The task to automate')
@click.option('--max-iter', '-m', default=10, help='Maximum number of iterations for the task')
@click.option('--change-model', is_flag=True, help='Change the LLM provider and model')
@click.pass_context
def cli(ctx, task, max_iter, change_model):
    """TaskAutomator - Your AI Task Automation Tool"""
    # Ensure config exists and has required fields
    config_path = ensure_config_exists()
    clear_terminal()
    
    # If change-model flag is set, update the model
    if change_model:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("Current configuration: Provider: {}, Model: {}".format(config.get("llm_provider"), config.get("model_name")))
        questions = [
            inquirer.List('provider_key',
                message="Select LLM Provider",
                choices=list(AVAILABLE_MODELS.keys()) # User selects "openai", "mistral", etc.
            )
        ]
        selected_provider_key = inquirer.prompt(questions)['provider_key']
        clear_terminal()
        
        # Ensure API key exists for the selected provider
        ensure_api_key(selected_provider_key)
        
        questions = [
            inquirer.List('model_name_full',
                message=f"Select {selected_provider_key} Model",
                choices=AVAILABLE_MODELS[selected_provider_key] # Shows "openai/gpt-3.5-turbo", etc.
            )
        ]
        selected_model_name_full = inquirer.prompt(questions)['model_name_full']
        clear_terminal()
        
        config["llm_provider"] = selected_provider_key # Store "openai"
        config["model_name"] = selected_model_name_full # Store "openai/gpt-4o"
        
        # Ensure working_directory is preserved or set
        if "working_directory" not in config or not config["working_directory"]:
            config["working_directory"] = os.getcwd()

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        click.echo(f"Model changed to {selected_model_name_full}")
        return
    
    # Ensure API key for the configured model before running OpenCopilot
    # This is a bit redundant if ensure_config_exists already did it, but good for safety
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    current_provider = config.get("llm_provider")
    if not current_provider and config.get("model_name"): # If llm_provider is missing, try to derive it
        current_provider = get_provider_from_model_name(config["model_name"])
    
    if current_provider:
        ensure_api_key(current_provider)
    else:
        click.echo("Error: LLM provider not configured. Please run with --change-model to set it up.", err=True)
        return

    copilot = OpenCopilot()
    if ctx.invoked_subcommand is None:
        if task:
            copilot.run_task(user_prompt=task, max_iter=max_iter)
        else:
            copilot.run()

@cli.command('list-tools')
def list_tools():
    """List all available automation tools"""
    tools = OpenCopilot.list_available_tools()
    click.echo("Available Tools:")
    for tool in tools:
        click.echo(f"- {tool['name']}: {tool['summary']}")
        if tool.get('arguments'):
            click.echo(f"    Arguments: {tool['arguments']}")

@cli.command('list-models')
def list_models():
    """List all available LLM providers and their models (litellm compatible)"""
    click.echo("Available LLM Providers and Models (litellm compatible):")
    for provider_key, model_list in AVAILABLE_MODELS.items():
        click.echo(f"\n{provider_key.upper()}:") # provider_key is "openai", "mistral", etc.
        for model_name_full in model_list: # model_name_full is "openai/gpt-4o", etc.
            click.echo(f"  - {model_name_full}")

@cli.command('set-api-key')
@click.option('--provider', '-p', type=click.Choice(list(AVAILABLE_MODELS.keys())), 
              help='The LLM provider to set API key for')
@click.option('--key', '-k', help='The API key to set (if not provided, will prompt for it)')
def set_api_key(provider, key):
    """Set or update API key for a specific LLM provider"""
    if not provider:
        # If no provider specified, ask user to choose
        questions = [
            inquirer.List('provider_key',
                message="Select LLM Provider to update API key",
                choices=list(AVAILABLE_MODELS.keys())
            )
        ]
        provider = inquirer.prompt(questions)['provider_key']
    
    # Get the environment variable name for this provider
    env_var = API_KEYS.get(provider)
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Get the API key (either from command line or prompt)
    if not key:
        questions = [
            inquirer.Text('api_key',
                message=f"Enter your {provider.upper()} API key",
                validate=lambda _, x: len(x.strip()) > 0
            )
        ]
        key = inquirer.prompt(questions)['api_key']
    
    # Get the path to .env file
    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    
    # Read existing .env file if it exists
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add the API key
    key_line = f"{env_var}={key}\n"
    key_exists = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{env_var}=") or line.strip().startswith(f"#{env_var}="):
            lines[i] = key_line
            key_exists = True
            break
    
    if not key_exists:
        lines.append(key_line)
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    click.echo(f"API key for {provider.upper()} has been updated successfully in {env_path}")

if __name__ == '__main__':
    cli() 