import json
import os
import sys
from pathlib import Path


def main():
    root = Path.cwd().resolve()
    request = json.loads(sys.stdin.read())
    readable = [root, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    windows = os.environ.get("SYSTEMROOT")
    if windows:
        readable.append(Path(windows, "Fonts").resolve())

    def inside(path, directories):
        if isinstance(path, int):
            return True
        resolved = Path(os.fsdecode(path)).resolve()
        return any(resolved.is_relative_to(directory) for directory in directories)

    def audit(event, arguments):
        if event == "open":
            path, mode, flags = arguments
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if not inside(path, [root] if writing else readable):
                raise PermissionError("File access outside the permitted directories")
        elif event.startswith(("socket.", "subprocess.", "os.exec", "os.spawn")) or event in {
            "os.system",
            "os.startfile",
            "os.fork",
            "os.kill",
            "winreg.OpenKey",
        }:
            raise PermissionError("Network, process and registry access are disabled")
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chdir", "os.chmod", "os.utime"}:
            if not inside(arguments[0], [root]):
                raise PermissionError("Mutation outside the working directory")
        elif event in {"os.rename", "os.link", "os.symlink"}:
            if not all(inside(path, [root]) for path in arguments[:2]):
                raise PermissionError("Mutation outside the working directory")
        elif event in {"os.listdir", "os.scandir"}:
            if arguments[0] is not None and not inside(arguments[0], readable):
                raise PermissionError("Listing outside the permitted directories")

    sys.addaudithook(audit)
    exec(compile(request["code"], "<model-tool>", "exec"), {"__name__": "__main__"})


if __name__ == "__main__":
    main()
