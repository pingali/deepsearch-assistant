# Grok API Prompt Runner

This script allows you to run prompts against the Grok API using a Jinja template and variables specified in a YAML file, with optional overrides via command line.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API key:
   ```
   XAI_API_KEY=your_api_key_here
   ```

3. Place your Jinja template in the `prompts/` directory, e.g., `prompts/usecases.jinja`.

4. Create a YAML file, e.g., `usecases.yaml`:
   ```yaml
   prompt: usecases
   variables:
     days: 7
     num: 20
   ```

## Usage

Run the script with:
```
python script.py config.yaml --promptdir prompts --var days=14 --var num=10
```

- The YAML file is required and specifies the prompt name (e.g., `usecases`) and default variables.
- The script constructs the prompt path as `<promptdir>/<prompt>.jinja`.
- Use `--promptdir` to specify the directory containing prompt templates (defaults to `prompts`).
- Use `--var key=value` multiple times to override or add variables.
- If a required variable in the template is missing, it will error out.
- Output is saved to `outputs/prompt/<ISO-timestamp>.json`.
- The `usecases.jinja` template outputs JSON with specific keys: `application`, `industry`, `inferred_prompt`, `user_persona`, `example_post`, `user_mention`, `date`, `details`, `source`, and `estimated_interest` (with `clicks`, `views`, `notes`).

## Dependencies

See `requirements.txt`.