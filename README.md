# Prevent Poetry Downgrade

This [pre-commit](https://pre-commit.com) hook ensures that the *version of Poetry* used to manage a project's dependencies does not get inadvertently downgraded when editing the `poetry.lock` file.

It prevents cases where a collaborator with an outdated version of Poetry causes unintended changes, and encourages best-practices.

## Usage

Copy this to your [`.pre-commit-config`](https://pre-commit.com/#plugins) file

```yaml
- repo: https://github.com/ScDor/prevent-poetry-downgrade
  rev: v0.1.1
  hooks:
  - id: prevent-poetry-downgrade
```

To pass other arguments, add the `args` key, e.g.
```yaml
    args: ["--strict"]
```

**Arguments**:

* `lock-path`: Defaults to a `poetry.lock` in the current directory.

**Options**:

* `--prev-ref`: Git reference to the previous version of the lock file.  [default: HEAD]
* `--strict`: Whether to require that the exact same version of Poetry is used. Otherwise, will promote upgrading Poetry to the latest version.
