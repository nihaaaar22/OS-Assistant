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
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-4.1-nano",
        "openai/gpt-4.1-mini"
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
    ],
    "gemini": [
        "gemini/gemini-2.0-flash",
        "gemini/gemini-2.5-flash-preview-05-20"
    ]
}

# Define API key environment variables for each provider (matching litellm conventions)
API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY"
}

# --- Utility Functions ---

def clear_terminal():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_provider_from_model_name(model_name: str) -> str:
    """Extracts the provider from a litellm model string (e.g., 'openai/gpt-4o' -> 'openai')."""
    if not model_name or '/' not in model_name:
        print(f"Warning: Model name '{model_name}' may not be in 'provider/model' format. Attempting to use as provider.")
        return model_name 
    return model_name.split('/')[0]

# --- Configuration Management ---

def load_config(config_path: str) -> dict:
    """Load (or create) config.json and return its contents as a dict. If config.json does not exist, copy from config.example.json (or create a default) and update working_directory to os.getcwd()."""
    if not os.path.exists(config_path):
        example_path = os.path.join(os.path.dirname(__file__), '../config.example.json')
        if os.path.exists(example_path):
            shutil.copy2(example_path, config_path)
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = { "working_directory": os.getcwd(), "llm_provider": None, "model_name": None }
    else:
        with open(config_path, 'r') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print("Error reading config.json. File might be corrupted. Re-creating default.")
                config = { "working_directory": os.getcwd(), "llm_provider": None, "model_name": None }
    # Always update working_directory to current directory
    config["working_directory"] = os.getcwd()
    return config

def save_config(config_path: str, config: dict) -> None:
    """Save config dict (with updated working_directory) to config_path."""
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

# --- API Key Management ---

def ensure_api_key(provider: str):
    """Ensure that an API key for the given provider (e.g. "openai") is available (via .env or prompt) and return it. Raise an error if unknown provider."""
    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    env_var = API_KEYS.get(provider)
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")

    # Force reload .env (if it exists) so that any new key is picked up.
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)

    api_key = os.getenv(env_var)
    if not api_key:
        questions = [ inquirer.Text("api_key", message=f"Enter your {provider.upper()} API key", validate=lambda _, x: len(x.strip()) > 0) ]
        api_key = inquirer.prompt(questions)["api_key"]
        clear_terminal()
        # Save (or update) the key in .env
        lines = []
        if os.path.exists(env_path):
             with open(env_path, 'r') as f:
                 lines = f.readlines()
        key_line = f"{env_var}={api_key}\n"
        key_exists = False
        for (i, line) in enumerate(lines):
             if (line.strip().startswith(f"{env_var}=") or line.strip().startswith(f"#{env_var}=")):
                 lines[i] = key_line
                 key_exists = True
                 break
        if not key_exists:
             lines.append(key_line)
        with open(env_path, 'w') as f:
             f.writelines(lines)
        # Reload .env (override) so that the new key is available.
        load_dotenv(env_path, override=True)
    

# --- Model / Provider Management ---

def prompt_model_selection() -> tuple:
    """Prompt the user (via inquirer) to select a provider (from AVAILABLE_MODELS) and then a model (from that provider's list). Return (provider, model_name_full)."""
    questions = [ inquirer.List("provider_key", message="Select LLM Provider", choices=list(AVAILABLE_MODELS.keys())) ]
    selected_provider_key = inquirer.prompt(questions)["provider_key"]
    clear_terminal()
    # (Ensure API key for the selected provider.)
    ensure_api_key(selected_provider_key)
    questions = [ inquirer.List("model_name_full", message=f"Select {selected_provider_key} Model", choices=AVAILABLE_MODELS[selected_provider_key]) ]
    selected_model_name_full = inquirer.prompt(questions)["model_name_full"]
    clear_terminal()
    return (selected_provider_key, selected_model_name_full)

def update_model_config(config_path: str, provider_key: str, model_name_full: str) -> None:
    """Update config (at config_path) so that "llm_provider" is provider_key and "model_name" is model_name_full. (Also update "working_directory" to os.getcwd() if missing.)"""
    config = load_config(config_path)
    config["llm_provider"] = provider_key
    config["model_name"] = model_name_full
    if "working_directory" not in config or not config["working_directory"]:
         config["working_directory"] = os.getcwd()
    save_config(config_path, config)

# --- CLI Commands ---

@click.group(invoke_without_command=True, help="TaskAutomator – Your AI Task Automation Tool\n\nThis tool helps automate tasks using AI. You can run tasks directly or use various commands to manage settings and tools.")
@click.option("--task", "-t", help="The task to automate (e.g., 'create a python script that sorts files by date')")
@click.option("--max-iter", "-m", default=10, help="Maximum number of iterations for the task (default: 10)")
@click.option("--change-model", is_flag=True, help="Change the LLM provider and model before running the task")
@click.pass_context
def cli(ctx, task, max_iter, change_model):
    """TaskAutomator – Your AI Task Automation Tool
    
    This tool helps automate tasks using AI. You can:
    - Run tasks directly with --task
    - Change AI models with --change-model
    - Manage API keys with set-api-key and set-serp-key
    - List available tools and models
    """
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    config = load_config(config_path)
    save_config(config_path, config)
    
    clear_terminal()

    if change_model or not config.get("model_name"):
         (provider, model) = prompt_model_selection()
         update_model_config(config_path, provider, model)
         click.echo(f"Model changed to {model}")
         if not change_model:  # Only return if this was triggered by missing model
              return

    # Ensure API key for the configured model (or derive provider from model_name if missing) before running OpenCopilot.
    current_provider = config.get("llm_provider")
    if not current_provider and config.get("model_name"):
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

@cli.command("list-tools", help="List all available automation tools and their descriptions")
def list_tools():
    """List all available automation tools and their descriptions.
    
    This command shows all tools that can be used by the AI to automate tasks,
    including what each tool does and what arguments it accepts.
    """
    tools = OpenCopilot.list_available_tools()
    click.echo("Available Tools:")
    for tool in tools:
         click.echo(f"- {tool['name']}: {tool['summary']}")
         if tool.get("arguments"):
             click.echo(f"    Arguments: {tool['arguments']}")

@cli.command("list-models", help="List all available LLM providers and their models")
def list_models():
    """List all available LLM providers and their models.
    
    Shows all supported AI models that can be used for task automation,
    organized by provider (OpenAI, Mistral, Groq, Anthropic).
    """
    click.echo("Available LLM Providers and Models (litellm compatible):")
    for (provider_key, model_list) in AVAILABLE_MODELS.items():
         click.echo(f"\n{provider_key.upper()}:")
         for model_name_full in model_list:
             click.echo(f"  - {model_name_full}")

@cli.command("set-api-key", help="Set or update API key for an LLM provider")
@click.option("--provider", "-p", type=click.Choice(list(AVAILABLE_MODELS.keys())), help="The LLM provider to set API key for (e.g., openai, mistral, groq, anthropic)")
@click.option("--key", "-k", help="The API key to set (if not provided, will prompt for it securely)")
def set_api_key(provider, key):
    """Set or update API key for an LLM provider.
    
    This command allows you to set or update the API key for any supported LLM provider.
    The key will be stored securely in your .env file.
    
    Examples:
        piko set-api-key --provider openai
        piko set-api-key -p mistral -k your-key-here
    """
    if not provider:
         questions = [ inquirer.List("provider_key", message="Select LLM Provider to update API key", choices=list(AVAILABLE_MODELS.keys())) ]
         provider = inquirer.prompt(questions)["provider_key"]
    env_var = API_KEYS.get(provider)
    if not env_var:
         raise ValueError(f"Unknown provider: {provider}")
    if not key:
         questions = [ inquirer.Text("api_key", message=f"Enter your {provider.upper()} API key", validate=lambda _, x: len(x.strip()) > 0) ]
         key = inquirer.prompt(questions)["api_key"]
    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    lines = []
    if os.path.exists(env_path):
         with open(env_path, 'r') as f:
             lines = f.readlines()
    key_line = f"{env_var}={key}\n"
    key_exists = False
    for (i, line) in enumerate(lines):
         if (line.strip().startswith(f"{env_var}=") or line.strip().startswith(f"#{env_var}=")):
             lines[i] = key_line
             key_exists = True
             break
    if not key_exists:
         lines.append(key_line)
    with open(env_path, 'w') as f:
         f.writelines(lines)
    click.echo(f"API key for {provider.upper()} has been updated successfully in {env_path}")

@cli.command("set-serp-key", help="Set or update the SERP API key for web search functionality")
@click.option("--key", "-k", help="The SERP API key to set (if not provided, will prompt for it securely)")
def set_serp_key(key):
    """Set or update the SERP API key used for web search functionality.
    
    This command sets the API key used for web search operations when DuckDuckGo
    search is not available. The key will be stored securely in your .env file.
    
    Examples:
        piko set-serp-key
        piko set-serp-key -k your-key-here
    """
    if not key:
         questions = [ inquirer.Text("api_key", message="Enter your SERP API key", validate=lambda _, x: len(x.strip()) > 0) ]
         key = inquirer.prompt(questions)["api_key"]
    env_path = os.path.join(os.path.dirname(__file__), '../.env')
    lines = []
    if os.path.exists(env_path):
         with open(env_path, 'r') as f:
             lines = f.readlines()
    key_line = f"SERP_API_KEY={key}\n"
    key_exists = False
    for (i, line) in enumerate(lines):
         if (line.strip().startswith("SERP_API_KEY=") or line.strip().startswith("#SERP_API_KEY=")):
             lines[i] = key_line
             key_exists = True
             break
    if not key_exists:
         lines.append(key_line)
    with open(env_path, 'w') as f:
         f.writelines(lines)
    click.echo(f"SERP API key has been updated successfully in {env_path}")

if __name__ == '__main__':
    cli() 