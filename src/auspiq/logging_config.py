"""ログ設定の管理"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    console_level: Optional[str] = None,
    file_level: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Path:
    """
    アプリケーション全体のログ設定を初期化する

    Args:
        console_level: コンソール出力ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        file_level: ファイル出力ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        timestamp: ログファイル名に使用するタイムスタンプ（未指定時は現在時刻）

    Returns:
        ログファイルのPath
    """

    # デフォルト値の設定
    if console_level is None:
        console_level = os.environ.get('CONSOLE_LOG_LEVEL', 'INFO').upper()
    if file_level is None:
        file_level = os.environ.get('FILE_LOG_LEVEL', 'DEBUG').upper()

    # ログレベルの検証関数
    def validate_level(level_str: str, default: str = 'INFO') -> int:
        numeric_level = getattr(logging, level_str.upper(), None)
        if not isinstance(numeric_level, int):
            print(f"Warning: Invalid log level '{level_str}', using {default}", file=sys.stderr)
            return getattr(logging, default)
        return numeric_level

    console_numeric_level = validate_level(console_level, 'INFO')
    file_numeric_level = validate_level(file_level, 'DEBUG')

    # 既存のハンドラーをクリア（重複を防ぐ）
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # フォーマッタの定義
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラーの設定
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_numeric_level)

    # ファイルハンドラーの設定（ログディレクトリを作成）
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"auspiq_{timestamp}.log"

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(file_numeric_level)

    # ルートロガーの設定（両方のレベルの最小値を使用）
    root_level = min(console_numeric_level, file_numeric_level)
    root_logger.setLevel(root_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 外部ライブラリのログレベルを調整
    # OpenAI関連のデバッグログを抑制
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    # アプリケーション自体のログレベルは最小値に設定
    logging.getLogger('auspiq').setLevel(root_level)

    # ログ設定完了メッセージ
    logger = logging.getLogger('auspiq.logging')
    logger.info(f"Logging initialized - Console: {console_level}, File: {file_level}, Log file: {log_file}")

    return log_file


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得する

    Args:
        name: ロガー名（通常は __name__ を使用）

    Returns:
        設定済みのロガー
    """
    return logging.getLogger(name)