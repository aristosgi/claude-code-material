# Claude Code + LiteLLM Integration Guide

## 1. Install Claude Code Extension for VS Code

1. Open VS Code
2. Go to the Extensions tab (or press `Ctrl+Shift+X` / `Cmd+Shift+X`)
3. Search for "Claude Code"
4. Click Install
5. Reload VS Code if prompted

## 2. Install LiteLLM with Proxy Support

Open a terminal (in VS Code or system terminal) and run:

```bash
pip install litellm[proxy]
```

This installs LiteLLM along with the proxy components needed to redirect Claude Code requests.

## 3. Configure Claude Code to Use LiteLLM Proxy

In VS Code:
1. Go to **File → Preferences → Settings**
2. Search for "Claude"
3. Click **Open Settings (JSON)** to edit the raw `settings.json`
4. Add the following configuration to set environment variables for Claude Code:

```json
"claude-code.environmentVariables": [
    {
        "name": "ANTHROPIC_API_KEY",
        "value": "sk-"
    },
    {
        "name": "ANTHROPIC_AUTH_TOKEN",
        "value": "sk-actual-token"
    },
    {
        "name": "ANTHROPIC_BASE_URL",
        "value": "http://localhost:4000"
    },
    {
        "name": "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
        "value": "1"
    }
]
```

5. Save the file and reload VS Code to apply changes

## 4. Create LiteLLM Configuration (config.yaml)

In your project folder, create a file named `config.yaml` with the following content:

```yaml
# Model configuration
model_list:
    - model_name: claude-sonnet-4-5-20250929
      litellm_params:
        model: azure/DeepSeek-V3.1
        api_base: https://dg27aiservicesdev001.services.ai.azure.com
        api_version: 2024-05-01-preview
        api_key: azure_service_admin_key  # <- CHANGE THIS to your actual Azure service key

general_settings:
  "value": "sk-actual-token"

# LiteLLM server settings
litellm_settings:
  drop_params: true  # Drop unsupported params instead of erroring
  success_callback: []
  failure_callback: []
```

**Important**: Replace `azure_service_admin_key` with your actual Azure service key to allow LiteLLM to access your DeepSeek model.

## 5. Run the LiteLLM Proxy Server

1. Open a terminal in your project folder
2. Start the LiteLLM proxy server with the following command:

```bash
litellm --config config.yaml --host 127.0.0.1 --port 4000
```

The server should start and listen on `http://127.0.0.1:4000`.

3. Check the terminal for any errors to ensure the proxy is running correctly

## 6. Test the Claude Code Extension

1. Open a file in VS Code where you want to use Claude Code
2. Activate the Claude Code extension
3. Try running a simple request or code generation command (e.g., Ask Claude or Generate code snippet)
4. Verify that the request goes through and that LiteLLM handles it without returning a `400 Invalid model name` error
5. Check the LiteLLM server terminal — you should see incoming requests being logged

## Troubleshooting

- **Port 4000 already in use**: Use a different port and update the `ANTHROPIC_BASE_URL` in VS Code settings
- **Authentication errors**: Verify your Azure service key is correct in `config.yaml`
- **Model not found**: Ensure the model name and API endpoint are correctly configured
- **Connection refused**: Make sure the LiteLLM proxy server is running before using Claude Code

## Security Notes

- **CRITICAL**: Your current `config.yaml` file contains an exposed Azure service key on line 8. This should be immediately removed and replaced with an environment variable reference
- Never commit your actual API keys to version control
- Use environment variables for sensitive credentials in production
- The proxy runs locally on your machine, keeping your API keys secure

### Recommended Secure Configuration

Instead of hardcoding API keys in `config.yaml`, use environment variables:

```yaml
# Model configuration
model_list:
    - model_name: claude-sonnet-4-5-20250929
      litellm_params:
        model: azure/DeepSeek-V3.1
        api_base: https://dg27aiservicesdev001.services.ai.azure.com
        api_version: 2024-05-01-preview
        api_key: "${AZURE_SERVICE_KEY}"  # Use environment variable
```

Then set the environment variable before running LiteLLM:

```bash
export AZURE_SERVICE_KEY=your_actual_key_here
litellm --config config.yaml --host 127.0.0.1 --port 4000
```