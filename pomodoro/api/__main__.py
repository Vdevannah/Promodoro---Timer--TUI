"""python -m pomodoro.api entry point."""

import uvicorn


def main() -> None:
    uvicorn.run("pomodoro.api.app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
