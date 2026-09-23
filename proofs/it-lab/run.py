"""Run one isolated demo on JSON. Reject malformed input without traceback."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def load(name):
    if name not in {p.name for p in ROOT.iterdir() if p.is_dir() and (p / "project.py").is_file()}:
        raise ValueError("unknown project")
    spec = importlib.util.spec_from_file_location(name, ROOT / name / "project.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("input", nargs="?")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    try:
        module = load(args.project)
        if args.serve:
            if args.project != "service-desk-web":
                raise ValueError("--serve is only available for service-desk-web")
            server = module.make_server(8765)
            print("Local demo: http://127.0.0.1:8765 (Ctrl+C to stop)", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
                server.database.close()
            return
        path = Path(args.input) if args.input else ROOT / args.project / "sample.json"
        result = module.analyze(json.loads(path.read_text(encoding="utf-8")))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Invalid input: {exc}\n")

if __name__ == "__main__":
    main()
