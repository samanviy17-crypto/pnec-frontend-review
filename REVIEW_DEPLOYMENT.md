# GitHub Pages review deployment

This supersedes the snapshot README's old prohibition on review workflows. The
existing Frontend CI is preserved. Deployment is a separate manual workflow.

Public project URL:
https://samanviy17-crypto.github.io/pnec-frontend-review/

`_config.pages.yml` defines the GitHub origin and `/pnec-frontend-review` baseurl.
Settings > Pages must use **GitHub Actions**. Run **Deploy Frontend Review (GitHub
Pages)** manually on `main`. It runs the existing Node tests, builds Jekyll, checks
generated local paths, uploads the artifact and deploys with Pages-only permissions
in the deployment job. There is no CNAME or production destination.

The default review API is deliberately an unavailable `.invalid` origin. A visible
notice identifies the static preview; login, live risk, chat and persistence are
not claimed to work. The incomplete RPG displays an unavailable explanation in
review builds instead of importing its missing engine.

After the separate Render review service is approved and verified, set repository
Actions variable `PNEC_REVIEW_API_URL` to its actual HTTPS root URL. Only a
`pnec-backend-review[-suffix].onrender.com` destination is accepted. Re-run the
Pages workflow. The build refuses an API that fails public review health, readiness
or exact Pages-origin CORS. Never configure a production API here.

The shared runtime include supplies the same API root to the frontend clients.
No browser secret is needed. For Render Free, use synthetic data only: storage
resets on restart, and SMTP/AI provider credentials are not provisioned.

The wider cross-repository browser release suite retains documented baseline
limitations; these workflows do not certify it or production readiness.
