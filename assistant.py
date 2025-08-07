#!/usr/bin/env python3 

import os
import json
import datetime
from pathlib import Path

import click
import requests
import yaml
from dotenv import load_dotenv
from jinja2 import Template, StrictUndefined

# Load environment variables from .env
load_dotenv()

# Standardized output location
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@click.command()
@click.argument('yaml_file', type=click.Path(exists=True))
@click.option('--promptdir', default='prompts', type=click.Path(exists=True, file_okay=False), help='Directory containing prompt templates (default: prompts).')
@click.option('--var', multiple=True, help='Additional variables in key=value format. Can be used multiple times.')
@click.option('--output', type=click.Choice(['stdout', 'file']), default='stdout', help='Output destination: stdout (default) or file.')
@click.option('--output-path', type=click.Path(), help='Custom output file path. If not specified, uses outputs/<prompt-name>/<timestamp>.json')
def run_grok_prompt(yaml_file, promptdir, var, output, output_path):
    """Load a YAML file specifying prompt name and variables, render the Jinja template, run it with Grok API, and output the result."""
    # Parse additional vars
    extra_vars = {}
    for v in var:
        if '=' not in v:
            raise click.BadOptionUsage('--var', f"Invalid format for --var: {v}. Must be key=value.")
        key, value = v.split('=', 1)
        extra_vars[key] = value

    # Load YAML
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)

    prompt_name = config.get('prompt')
    if not prompt_name:
        raise click.BadOptionUsage('yaml_file', "YAML must specify 'prompt' key with template name.")

    # Construct prompt file path
    prompt_file = Path(promptdir) / f"{prompt_name}.jinja"
    if not prompt_file.exists():
        raise click.BadOptionUsage('prompt_file', f"Prompt file {prompt_file} does not exist in {promptdir}.")

    variables = config.get('variables', {})
    variables.update(extra_vars)

    # Load and render the template with StrictUndefined to error on missing vars
    with open(prompt_file, 'r') as f:
        template_content = f.read()
    template = Template(template_content, undefined=StrictUndefined)
    try:
        rendered_prompt = template.render(**variables)
    except Exception as e:
        raise click.ClickException(f"Error rendering template: {e}. Missing variable?")

    # Get API key from .env
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        raise click.ClickException("XAI_API_KEY not found in .env file.")

    # API request
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "grok-3-fast",
        "messages": [
            {"role": "user", "content": rendered_prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Debug: print response status and content
        click.echo(f"API Response Status: {response.status_code}", err=True)
        response_json = response.json()
        
        # Extract the completion content
        if "choices" in response_json and len(response_json["choices"]) > 0:
            api_output = response_json["choices"][0]["message"]["content"]
        else:
            raise click.ClickException(f"Unexpected API response format: {response_json}")
            
    except requests.exceptions.RequestException as e:
        raise click.ClickException(f"API request failed: {e}")
    except KeyError as e:
        raise click.ClickException(f"Unexpected API response format. Missing key: {e}. Full response: {response.json()}")
    except Exception as e:
        raise click.ClickException(f"Error processing API response: {e}")

    try:
        api_output = json.loads(cleaned_output)
    except:
        cleaned_output = api_output\
            .replace('\u2019', "'")\
            .replace('\u201c', '"')\
            .replace('\u201d', '"')
        api_output = json.loads(cleaned_output)
    
    result = {"prompt": rendered_prompt, "output": api_output}

    # Handle output destination
    if output == 'stdout':
        click.echo(json.dumps(result, indent=4))
    else:  # output == 'file'
        if output_path:
            output_file = Path(output_path)
        else:
            # Generate clean ISO timestamp without colons
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            prompt_output_dir = OUTPUT_DIR / prompt_name
            prompt_output_dir.mkdir(parents=True, exist_ok=True)
            output_file = prompt_output_dir / f"{timestamp}.json"
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=4)

        click.echo(f"Output saved to: {output_file}")

if __name__ == '__main__':
    run_grok_prompt()
