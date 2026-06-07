# Contributing to climon

Thanks for your interest. climon is a small, non-commercial hobby project, so please keep
expectations modest: issues and pull requests are read when time allows, with no guaranteed
response time.

## Before you start

- climon is an unofficial fan project and is **not** affiliated with Nintendo, Creatures,
  GAME FREAK, or The Pokemon Company. Do **not** contribute additional copyrighted assets or
  names you do not have the right to share. Original or openly licensed art is very welcome.
- By contributing, you agree your contribution is licensed under the project's MIT `LICENSE`.

## Developer Certificate of Origin (sign-off)

This project uses the [Developer Certificate of Origin](https://developercertificate.org/).
It is a simple statement that you wrote the contribution, or otherwise have the right to
submit it under the project's open-source license.

Certify it by adding a `Signed-off-by` line to each commit (this is what `git commit -s`
does):

```
Signed-off-by: Your Name <your-email@example.com>
```

Pull requests whose commits are not signed off may be asked to amend before merging.

## Development

```
uv sync                 # create the env and install everything
uv run pytest           # tests
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy             # types
```

Conventional commit messages and small, focused PRs are appreciated. CI runs lint, types,
and tests on every push and pull request.
