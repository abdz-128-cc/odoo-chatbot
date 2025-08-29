from src.main import chat_once
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--q", required=True)
    parser.add_argument("--role", default=None)
    args = parser.parse_args()
    route, ans = chat_once(args.q, args.role)
    print(f"[route: {route}]")
    print(ans)
