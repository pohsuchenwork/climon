# Third-party licenses

climon's own source code is licensed under the MIT License (see `LICENSE`).

climon does **not** bundle or redistribute the libraries below. They are declared
dependencies that each user installs themselves (via `uv` or `pip`), so each library's own
license text ships with that package, not with climon. They are listed here for transparency.

All dependencies are permissive (MIT, BSD, Apache-2.0, ISC, MIT-CMU/HPND, PSF). None are GPL,
LGPL, or AGPL. One transitive, dev-only dependency (`pathspec`) is MPL-2.0 (weak, file-level
copyleft); climon does not modify or redistribute it, so no copyleft obligation attaches to
climon's code.

| Name                    | Version | License                              |
|-------------------------|---------|--------------------------------------|
| coverage                | 7.14.1  | Apache-2.0                           |
| pytest-asyncio          | 1.4.0   | Apache-2.0                           |
| packaging               | 26.2    | Apache-2.0 OR BSD-2-Clause           |
| Jinja2                  | 3.1.6   | BSD License                          |
| nodeenv                 | 1.10.0  | BSD License                          |
| Pygments                | 2.20.0  | BSD-2-Clause                         |
| MarkupSafe              | 3.0.3   | BSD-3-Clause                         |
| python-dotenv           | 1.2.2   | BSD-3-Clause                         |
| websockets              | 16.0    | BSD-3-Clause                         |
| shellingham             | 1.5.4   | ISC License (ISCL)                   |
| annotated-doc           | 0.0.4   | MIT                                  |
| ast_serialize           | 0.5.0   | MIT                                  |
| cfgv                    | 3.5.0   | MIT                                  |
| filelock                | 3.29.1  | MIT                                  |
| identify                | 2.6.19  | MIT                                  |
| iniconfig               | 2.3.0   | MIT                                  |
| librt                   | 0.11.0  | MIT                                  |
| mypy                    | 2.1.0   | MIT                                  |
| mypy_extensions         | 1.1.0   | MIT                                  |
| platformdirs            | 4.10.0  | MIT                                  |
| pre_commit              | 4.6.0   | MIT                                  |
| pydantic                | 2.13.4  | MIT                                  |
| pydantic-settings       | 2.14.1  | MIT                                  |
| pydantic_core           | 2.46.4  | MIT                                  |
| pytest                  | 9.0.3   | MIT                                  |
| ruff                    | 0.15.16 | MIT                                  |
| syrupy                  | 5.3.1   | MIT                                  |
| typer                   | 0.26.7  | MIT                                  |
| typing-inspection       | 0.4.2   | MIT                                  |
| virtualenv              | 21.4.2  | MIT                                  |
| PyYAML                  | 6.0.3   | MIT License                          |
| annotated-types         | 0.7.0   | MIT License                          |
| linkify-it-py           | 2.1.0   | MIT License                          |
| markdown-it-py          | 4.2.0   | MIT License                          |
| mdit-py-plugins         | 0.6.1   | MIT License                          |
| mdurl                   | 0.1.2   | MIT License                          |
| pluggy                  | 1.6.0   | MIT License                          |
| pytest-textual-snapshot | 1.0.0   | MIT License                          |
| python-discovery        | 1.4.0   | MIT License                          |
| rich                    | 15.0.0  | MIT License                          |
| textual                 | 8.2.7   | MIT License                          |
| uc-micro-py             | 2.0.0   | MIT License                          |
| pillow                  | 12.2.0  | MIT-CMU                              |
| pathspec                | 1.1.1   | Mozilla Public License 2.0 (MPL 2.0) |
| typing_extensions       | 4.15.0  | PSF-2.0                              |
| distlib                 | 0.4.1   | Python Software Foundation License   |

## Bundled assets are NOT covered by the MIT License

The MIT License applies ONLY to climon's original source code. The bundled Pokemon sprite
artwork (`src/climon/assets/sprites/`) and the Pokemon names are trademarks and copyrighted
works of Nintendo, Creatures Inc., GAME FREAK Inc., and The Pokemon Company. They are **not**
licensed under MIT and are **not** owned by the climon authors. See `legal/DISCLAIMER.md`.
