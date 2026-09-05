# PyPI release process

Publishing is implemented in the repository; a PyPI account alone does not build or
upload the package.

## What each part does

- `cli/pyproject.toml` defines the `chatpulse-cli` distribution, version, dependencies,
  supported Python versions, build backend, and the `chatpulse` console entry point.
- `cli/chatpulse_cli/` contains the code included in the wheel and source archive.
- `.github/workflows/publish.yml` runs when a Git tag matching `v*` is pushed. It builds
  `cli/`, then uploads `cli/dist/*` with Twine.
- The PyPI account owns the project and authorizes the upload. The current workflow
  reads a long-lived project/API token from the GitHub Actions secret `PYPI_TOKEN`.

Formatting or reinstalling a local operating system does not remove GitHub repository
secrets or an existing PyPI project. Verify `PYPI_TOKEN` in the repository's GitHub
Actions secrets before the next release; do not paste the token into source, docs,
issues, logs, or chat.

## Current release sequence

1. Update the version in `cli/pyproject.toml`.
2. Build and inspect locally:

   ```bash
   python -m build ./cli
   python -m twine check cli/dist/*
   ```

3. Review the complete diff and run the CLI smoke checks.
4. With explicit authorization, commit and push the release change.
5. With separate explicit authorization, create and push a matching `v*` tag. Pushing
   the tag publishes externally and cannot be treated as a local-only action.
6. Verify the version and both artifacts on PyPI, then install that exact version into
   a clean pipx environment.

Do not reuse a broadly scoped account token. Prefer a token scoped only to
`chatpulse-cli`. A future hardening task is to configure PyPI Trusted Publishing for
this GitHub repository and replace the long-lived secret with GitHub OIDC. Configure
the trusted publisher in PyPI first, then change and test the workflow; changing only
one side will break releases.
