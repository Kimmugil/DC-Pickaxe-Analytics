"""관리자 비밀번호 설정. 직접 실행하세요 (비밀번호는 화면에 보이지 않고 어디에도 출력되지 않습니다).

    .venv\\Scripts\\python.exe tools\\set_admin_password.py

결과(해시와 세션 비밀키)는 web/.env.local 에 저장됩니다. 배포할 때는 같은 두 값을 Vercel 환경변수에 넣으세요.
"""
import getpass
import hashlib
import os
import secrets
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / "web" / ".env.local"
N = 16384


def read_env() -> dict:
    out = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v
    return out


def main() -> int:
    pw = getpass.getpass("새 관리자 비밀번호 (10자 이상): ")
    if not pw.isascii():
        print("한글(또는 다른 문자)이 섞여 있습니다. 한/영 키로 영문 입력 상태로 바꾼 뒤 다시 실행하세요.")
        return 1
    if len(pw) < 10:
        print("10자 이상으로 정해주세요.")
        return 1
    if pw != getpass.getpass("한 번 더 입력: "):
        print("두 번 입력한 값이 다릅니다.")
        return 1
    salt = os.urandom(16)
    digest = hashlib.scrypt(pw.encode(), salt=salt, n=N, r=8, p=1, dklen=32)
    env = read_env()
    env["ADMIN_PASSWORD_HASH"] = f"scrypt:{N}:{salt.hex()}:{digest.hex()}"
    env.setdefault("SESSION_SECRET", secrets.token_hex(32))
    env.setdefault("DB_SSL_INSECURE", "1")
    ENV.parent.mkdir(exist_ok=True)
    ENV.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8")
    print(f"저장했습니다: {ENV}")
    print("세션이 바뀌도록 개발 서버가 켜져 있다면 껐다 켜세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
