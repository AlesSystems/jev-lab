"""Load the server API key from Jev Lab's root .env without a dependency."""

import os
import shlex
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / '.env'


def load_api_key(path: Path = ENV_PATH) -> None:
    if 'TYPESAFE_API_KEY' in os.environ:
        return
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return
    # ponytail: single-line key only; use python-dotenv if broader dotenv syntax is needed.
    for line in lines:
        key, separator, value = line.strip().removeprefix('export ').partition('=')
        if key.strip() != 'TYPESAFE_API_KEY':
            continue
        try:
            tokens = shlex.split(value, comments=True)
            if not separator or len(tokens) > 1:
                raise ValueError
            if tokens and tokens[0]:
                os.environ['TYPESAFE_API_KEY'] = tokens[0]
                return
        except ValueError:
            raise ValueError('Invalid TYPESAFE_API_KEY assignment in .env; use one value, optionally quoted.') from None


if __name__ == '__main__':
    load_api_key()
