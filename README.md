# Webby — Slack Web Hosting Bot

**Webby brings Cloudflare troubleshooting and basic website diagnostics right into Slack for U-M ITS Web Hosting.**  

---

## Why Webby?

Investigating websites and Cloudflare security events required ITS Web Hosting staff to manually navigate through complex, layered dashboards, making both the process and daily workflows increasingly time-consuming and inefficient.

---

## Slash-commands

| Command | Purpose (see `docs/` for full examples) |
|---------|-----------------------------------------|
| `/cf -ray [ray_id]` | Lookup a Cloudflare Firewall Event (IP, action, bot score, JA3/JA4, etc.) via the GraphQL Analytics API. |
| `/website [domain]` | Resolve DNS, check IP ownership (RDAP), and detect Cloudflare protection for a domain. |
| `/webby` or `/webby help` | Overview of everything Webby can do. |
| `/webby flip` / `/webby roll` | Utility commands (coin-flip, dice). |

> All commands return within Slack’s 3 s window **except** `/website`, which posts a quick “Processing your request …” placeholder before sending final results.

---

## Architecture

```
Slack Slash-Command
│
└─► API Gateway (HTTP API)
    │   • Single Endpoint: /ITS-WebHosting-SlackBot
    │
    └─► AWS Lambda (Python 3.9)
        │
        ├─ main.py (handler)
        │
        ├─ cmd_cf.py
        ├─ cmd_website.py
        ├─ cmd_webby.py
        └─ cloudflare_utils.py
```

---

## Repository layout

```
.
├── cmd_cf.py             # Handler for the /cf command
├── cmd_website.py        # Handler for the /website command
├── cmd_webby.py          # Handler for /webby (help) commands
├── cloudflare_utils.py   # Helper functions for DNS lookups (/website command)
├── main.py               # Lambda function entry point
├── requirements.txt      # Python dependencies
├── docs/                 # Examples, methods, and details of slash commands
└── README.md             # This file
```

---

## Quick start (local)

```bash
git clone https://github.com/<org>/webby.git
cd webby
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in real tokens
python main.py            # optional: run locally via ngrok
````

Required **.env** keys:

| Key                    | Description                                  |
| ---------------------- | -------------------------------------------- |
| `SLACK_TOKEN`          | Bot token (`xoxb-…`)                         |
| `SIGNING_SECRET`       | Slack app signing secret                     |
| `CLOUDFLARE_API_TOKEN` | Scoped token (`Zone:Read`, `Analytics:Read`) |

---

## Deploying to AWS Lambda

### 1. Package the code

```bash
zip -r lambda_deploy.zip \
    main.py cmd_*.py cloudflare_utils.py \
    requirements.txt
```

> Ensure your `.env` file is **not** included in the ZIP (use Lambda environment variables instead).

---

### 2. Create or update your Lambda function

| Setting | Value                 |
| ------- | --------------------- |
| Runtime | Python 3.9            |
| Handler | `main.lambda_handler` |
| Memory  | 256 MB                |
| Timeout | 15 seconds            |

Set environment variables (e.g., `SLACK_TOKEN`, `CLOUDFLARE_API_TOKEN`) manually in the Lambda UI under **Configuration > Environment variables**.

---

### 3. Attach an execution role

Attach the built-in `AWSLambdaBasicExecutionRole` to enable logging to **CloudWatch Logs**.

If you're storing secrets in **AWS Secrets Manager**, also attach the necessary `secretsmanager:GetSecretValue` permission.

---

### 4. Add an API Gateway trigger

* Create an **HTTP API**
* Set method to `ANY`
* Set resource path to `/ITS-WebHosting-SlackBot`
* Deploy it and copy the **Invoke URL** (e.g.,):

```
https://t45z5xq4rj.execute-api.us-east-2.amazonaws.com/default/ITS-WebHosting-SlackBot
```

---

### 5. Configure Slack commands

In the [Slack Developer Portal](https://api.slack.com/apps):

* Navigate to **Slash Commands**
* For each command (`/website`, `/cf`, `/webby`), edit the **Request URL** to:

```
<InvokeURL>/website      # for /website
<InvokeURL>/cf           # for /cf -ray
<InvokeURL>/webby        # for /webby
```

After updating all commands, click **Reinstall App to Workspace** to apply changes.

---

### 6. Upload new code

Every time you make updates:

```bash
zip -r lambda_deploy.zip \
    main.py cmd_*.py cloudflare_utils.py \
    requirements.txt
```

Then go to the Lambda **Code** tab, upload the zip, and click **Deploy**.

> Add `lambda_deploy.zip` to your `.gitignore` to avoid committing it to GitHub.

---

### 7. Debugging with CloudWatch Logs

To view logs and debug print statements:

1. Go to the **CloudWatch Console**
2. Navigate to **Logs > Log groups**
3. Look for your function name under `/aws/lambda/your-function-name`
4. Click into the latest log stream to view:

   * `print()` statements
   * any raised exceptions
   * parsed Slack command data

You can also add temporary debug prints in `main.py` or `cmd_website.py`, like:

```python
print("DEBUG: Received Slack command:", command)
```

These will appear in near real-time in the log stream after Lambda invocation.

---

## Usage examples

```bash
/cf -ray 783dd7324ebfbb62
```

```bash
/website giving.umich.edu
```

See `docs/` for full JSON payloads and Slack-formatted blocks.

---

## Contributing

1. Fork > feature-branch > pull-request.
2. Follow `CONTRIBUTING.md` for linting and commit format.
3. All CI checks must pass.

---

## License

MIT © Regents of the University of Michigan

