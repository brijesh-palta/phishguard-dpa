# GoPhish Local Setup

Use GoPhish only for authorized security awareness training in a controlled lab or approved organization environment.

## Run GoPhish
1. Open PowerShell in `gophish-v0.12.1-windows-64bit`.
2. Start GoPhish:
   ```powershell
   .\gophish.exe
   ```
3. Open the admin console:
   ```text
   https://127.0.0.1:3333
   ```
4. Use the temporary admin password printed in the GoPhish terminal, then change it.

## Recommended Safe Demo Setup
- Sending profile: use a local SMTP test service or approved internal SMTP only.
- Landing page: show a training message and do not collect real passwords.
- Email template: use awareness training wording and a GoPhish tracking link.
- Users: use test accounts or classmates who explicitly consented.

## Connect This Dashboard to GoPhish
Set these environment variables before starting FastAPI:

```powershell
$env:GOPHISH_BASE_URL = "https://127.0.0.1:3333"
$env:GOPHISH_API_KEY = "paste-your-gophish-api-key"
python -m uvicorn app:app --reload --port 8000
```

Then use the GoPhish status panel in the dashboard.

## Demo Flow
1. Create a campaign in GoPhish with a safe training landing page.
2. Run the FastAPI dashboard.
3. Paste a simulated phishing email into the AI analyzer.
4. Record behavior events in the dashboard to show risk scoring and leaderboard updates.
5. Capture screenshots for the final project report.
