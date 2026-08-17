# V1.0 CI/CD and monitoring research

## Cloudflare Pages Direct Upload

Source: https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/

Cloudflare Pages supports uploading prebuilt assets with Wrangler from CI. The documented command is `CLOUDFLARE_ACCOUNT_ID=<ACCOUNT_ID> npx wrangler pages deploy <DIRECTORY> --project-name=<PROJECT_NAME>`. The official GitHub Actions example uses `cloudflare/wrangler-action@v3`, with `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `GITHUB_TOKEN`. Cloudflare recommends an API token with Account / Cloudflare Pages / Edit permissions and storing credentials as GitHub Actions secrets.

## Render deploys and CI checks

Source: https://render.com/docs/deploys

Render can auto-deploy a linked branch on commit, or wait until repository CI checks pass. When configured as “After CI Checks Pass,” Render recognizes GitHub Actions checks and only deploys when checks conclude successfully, neutrally, or skipped. Render deploys use build, optional pre-deploy, and start commands; failed commands keep the most recent successful deploy running.

## Render health checks

Source: https://render.com/docs/health-checks

Render web services support HTTP health checks configured with a path such as `/health`. A healthy response is any 2xx or 3xx response within five seconds. Render uses health checks to validate new deploys before routing traffic and to restart unhealthy running instances. Health endpoints should verify operation-critical dependencies where appropriate.

## Render deploy hooks

Source: https://render.com/docs/deploy-hooks

Render deploy hook URLs are secret values and can trigger a deploy with GET or POST. They can be stored as a GitHub Actions repository secret such as `RENDER_DEPLOY_HOOK_URL`. Deploy hooks may include a `ref` query parameter to deploy a specific commit.
