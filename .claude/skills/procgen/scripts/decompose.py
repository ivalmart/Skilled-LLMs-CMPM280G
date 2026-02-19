import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from baml_client.sync_client import b


def main():
    result = b.DecomposeProblem(sys.argv[1])
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
