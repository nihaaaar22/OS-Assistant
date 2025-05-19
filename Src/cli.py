import click
import json
import os
import inquirer
import shutil
from OpenCopilot import OpenCopilot
from dotenv import load_dotenv

# Define available models for each provider
AVAILABLE_MODELS = {
    "mistral": [
        "mistral-tiny",
        "mistral-small",
        "mistral-medium",
        "mistral-large-latest"
    ],
    "groq": [
        "llama2-70b-4096",
        "mixtral-8x7b-32768",
        "gemma-7b-it"
    ],
    "openai": [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo-preview"
    ]
}

# Define API key environment variables for each provider
API_KEYS = {
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY"
}

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
            config = {
                "working_directory": os.getcwd(),
                "llm_provider": None,
                "model_name": None
            }
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
    else:
        # Read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Check if required fields are present
    if not config.get("llm_provider") or not config.get("model_name"):
        questions = [
            inquirer.List('provider',
                message="Select LLM Provider",
                choices=list(AVAILABLE_MODELS.keys())
            )
        ]
        provider = inquirer.prompt(questions)['provider']
        clear_terminal()
        
        # Ensure API key exists for the selected provider
        ensure_api_key(provider)
        
        questions = [
            inquirer.List('model',
                message=f"Select {provider} Model",
                choices=AVAILABLE_MODELS[provider]
            )
        ]
        model = inquirer.prompt(questions)['model']
        clear_terminal()
        
        config["llm_provider"] = provider
        config["model_name"] = model
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    # Ensure API key exists for the selected provider
    ensure_api_key(config["llm_provider"])
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
        
        questions = [
            inquirer.List('provider',
                message="Select LLM Provider",
                choices=list(AVAILABLE_MODELS.keys())
            )
        ]
        provider = inquirer.prompt(questions)['provider']
        clear_terminal()
        
        
        
        questions = [
            inquirer.List('model',
                message=f"Select {provider} Model",
                choices=AVAILABLE_MODELS[provider]
            )
        ]
        model = inquirer.prompt(questions)['model']
        clear_terminal()
        
        config["llm_provider"] = provider
        config["model_name"] = model
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        click.echo(f"Model changed to {provider}/{model}")
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
    """List all available LLM providers and their models"""
    click.echo("Available LLM Providers and Models:")
    for provider, models in AVAILABLE_MODELS.items():
        click.echo(f"\n{provider.upper()}:")
        for model in models:
            click.echo(f"  - {model}")

if __name__ == '__main__':
    cli() 