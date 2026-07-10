# Sales Dashboard (Flask)

Configurable sales and campaign performance dashboard built with Flask, CSV data files, and Chart.js.

## Hosted Example

Live example URL:

- https://perf-sales-campaign-template.spal-project.com/

This link is provided as a demo reference. You can open it to quickly understand the layout, chart behavior, and runtime customization flow.

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python main.py
```

4. Open:

- http://127.0.0.1:5000

Local behavior should look very similar to the hosted example.

## Config Route

Open the config page at:

- `/config`

From this route, you can modify active dashboard options such as:

- branding title and title color
- chart types
- trend style
- table visibility and row counts
- top products settings

Saved values are written to:

- `config/active_dashboard_options.yaml`

This lets you tweak the dashboard quickly without editing template code.

After you change options in `/config` and click save, the main dashboard reflects those updated settings.

## Configuration Files

- `config/dashboard_config.yaml`: Base/default dashboard configuration.
- `config/active_dashboard_options.yaml`: Active runtime overrides saved from `/config`.

## Ephemeral Behavior (Important)

The hosted example is intentionally ephemeral.

- No database is used for config persistence.
- Runtime changes are available while the underlying Cloud Function container/session is active.
- After inactivity, the container may be stopped/recycled by the platform.
- When a new container starts, prior runtime changes may be lost.

So this deployment is a proof-of-concept demonstration of runtime customization, not a permanent persistence setup.

## Intended Usage Pattern

This template is designed as a fast client onboarding accelerator:

1. Share a ready dashboard quickly.
2. Let stakeholders adjust options from `/config`.
3. Capture preferred parameter values.
4. Convert those selected values into stable config for a client-specific deployment.

In short, it is a quick way to present configurable dashboard capabilities for basic client needs, then finalize and redeploy with persistent settings as needed.
