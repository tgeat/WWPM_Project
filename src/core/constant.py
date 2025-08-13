from pathlib import Path

#当前项目的目录
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

#外部文件
ACCOUNT_FILE = ROOT_DIR / "src" / "config" / "account.json"
