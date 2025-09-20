"""設定管理コマンド"""
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..config import ConfigManager
from ..api_client import OpenAIClient
from ..logging_config import get_logger


console = Console()
logger = get_logger(__name__)


@click.group()
@click.help_option('-h', '--help')
def config():
    """設定を管理する"""
    pass


@config.command()
@click.option('--config-file', type=click.Path(path_type=Path), help='設定ファイルのパス')
@click.option('--show-sensitive', is_flag=True,
              help='Show sensitive information like API keys')
@click.help_option('-h', '--help')
@click.pass_context
def show(ctx, config_file, show_sensitive):
    """現在の設定を表示する"""
    logger.info("=== Starting config show command ===")
    logger.debug(f"Input parameters: config_file={config_file}, show_sensitive={show_sensitive}")

    # グローバルオプションから設定ファイルパスを取得（優先度：ローカル > グローバル）
    if not config_file and ctx.obj:
        config_file = ctx.obj.get('config_file')
        logger.debug(f"Using config file from global context: {config_file}")

    logger.info(f"Loading configuration from: {config_file or 'default path'}")
    manager = ConfigManager(config_file)
    logger.debug(f"ConfigManager initialized with path: {manager.config_path}")

    try:
        config = manager.get_config()
        logger.info("Configuration loaded successfully")
        logger.debug(f"Config values: model={config.model}, threshold={config.threshold}, max_tokens={config.max_tokens}, temperature={config.temperature}")
        logger.debug(f"API key present: {bool(config.api_key)}")
        
        table = Table(title="現在の設定")
        table.add_column("項目", style="cyan")
        table.add_column("値", style="magenta")
        table.add_column("説明", style="green")
        
        # APIキーの表示制御
        logger.debug("Determining API key display format")
        env_key = manager.get_api_key_from_env()
        logger.debug(f"Environment API key present: {bool(env_key)}")

        api_key_display = "未設定"
        if config.api_key:
            logger.debug("Using API key from config file")
            if show_sensitive:
                api_key_display = config.api_key
                logger.debug("Displaying full API key (sensitive mode)")
            else:
                api_key_display = f"{config.api_key[:8]}..." if len(config.api_key) > 8 else "********"
                logger.debug("Displaying masked API key")
        elif env_key:
            # 環境変数のAPIキー
            logger.debug("Using API key from environment variable")
            if show_sensitive:
                api_key_display = f"{env_key} (環境変数)"
                logger.debug("Displaying full environment API key (sensitive mode)")
            else:
                api_key_display = f"{env_key[:8]}... (環境変数)" if len(env_key) > 8 else "******** (環境変数)"
                logger.debug("Displaying masked environment API key")
        
        table.add_row("API Key", api_key_display, "OpenAI API キー")
        table.add_row("Model", config.model, "使用するOpenAIモデル")
        table.add_row("Threshold", str(config.threshold), "自動停止の蓋然性閾値 (%)")
        table.add_row("Max Tokens", str(config.max_tokens), "API リクエストの最大トークン数")
        table.add_row("Temperature", str(config.temperature), "API リクエストの temperature")
        table.add_row("Console Log Level", config.console_log_level, "コンソール出力のログレベル")
        table.add_row("File Log Level", config.file_log_level, "ファイル出力のログレベル")
        
        logger.debug("Creating display table with configuration values")
        console.print(table)

        # 設定ファイルのパスを表示
        logger.debug(f"Displaying config file path: {manager.config_path}")
        console.print(f"\n設定ファイル: {manager.config_path}")

        # セキュリティに関する注意事項
        if not show_sensitive and (config.api_key or env_key):
            logger.debug("Showing API key masking notice")
            console.print("\n[dim]💡 APIキーは安全のため一部のみ表示されています。完全な値を確認するには --show-sensitive オプションを使用してください。[/dim]")

        # API キーの有効性チェック
        logger.debug("Validating API key availability")
        if not manager.validate_api_key():
            if env_key:
                logger.info("Config file API key not set, but environment variable available")
                console.print("[yellow]設定ファイルにAPIキーが設定されていませんが、環境変数 OPENAI_API_KEY が利用可能です[/yellow]")
            else:
                logger.warning("No API key found in config or environment")
                console.print("[red]APIキーが設定されていません。設定コマンドでAPIキーを設定してください[/red]")
        else:
            logger.info("API key validation successful")

        logger.info("=== Config show command completed successfully ===")

    except Exception as e:
        logger.error(f"Failed to show configuration: {e}")
        logger.exception("Full exception details:")
        console.print(f"[red]設定の読み込みに失敗しました: {e}[/red]")
        raise click.Abort()


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--config-file', type=click.Path(path_type=Path), help='設定ファイルのパス')
@click.help_option('-h', '--help')
@click.pass_context
def set(ctx, key: str, value: str, config_file):
    """設定値を変更する

    例:
      auspiq config set api-key sk-...
      auspiq config set model gpt-3.5-turbo
      auspiq config set threshold 85
    """
    logger.info("=== Starting config set command ===")
    logger.debug(f"Input parameters: key='{key}', value='{'***' if 'key' in key.lower() else value}', config_file={config_file}")

    # グローバルオプションから設定ファイルパスを取得（優先度：ローカル > グローバル）
    if not config_file and ctx.obj:
        config_file = ctx.obj.get('config_file')
        logger.debug(f"Using config file from global context: {config_file}")

    logger.info(f"Loading configuration manager for: {config_file or 'default path'}")
    manager = ConfigManager(config_file)
    logger.debug(f"ConfigManager initialized with path: {manager.config_path}")

    # キー名を正規化（ハイフンをアンダースコアに）
    normalized_key = key.replace('-', '_')
    logger.debug(f"Normalized key: '{key}' -> '{normalized_key}'")

    # 有効なキーのチェック
    valid_keys = {'api_key', 'model', 'threshold', 'max_tokens', 'temperature', 'console_log_level', 'file_log_level'}
    logger.debug(f"Checking if '{normalized_key}' is in valid keys: {valid_keys}")

    if normalized_key not in valid_keys:
        logger.warning(f"Invalid configuration key attempted: {key}")
        console.print(f"[red]無効な設定項目です: {key}[/red]")
        console.print(f"有効な項目: {', '.join(sorted(valid_keys))}")
        raise click.Abort()
    
    try:
        # 型変換
        if normalized_key == 'threshold':
            parsed_value = int(value)
            if not 0 <= parsed_value <= 100:
                raise ValueError("閾値は0-100の範囲で設定してください")
        elif normalized_key == 'max_tokens':
            parsed_value = int(value)
            if parsed_value <= 0:
                raise ValueError("最大トークン数は正の数で設定してください")
        elif normalized_key == 'temperature':
            parsed_value = float(value)
            if not 0.0 <= parsed_value <= 2.0:
                raise ValueError("temperature は0.0-2.0の範囲で設定してください")
        elif normalized_key in ('console_log_level', 'file_log_level'):
            valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
            parsed_value = value.upper()
            if parsed_value not in valid_log_levels:
                raise ValueError(f"ログレベルは{', '.join(valid_log_levels)}のいずれかを設定してください")
        else:
            parsed_value = value
        
        # 設定を更新
        manager.update_config(**{normalized_key: parsed_value})
        
        console.print(f"[green]設定を更新しました: {key} = {value}[/green]")
        
        # APIキーを設定した場合の確認メッセージ
        if normalized_key == 'api_key':
            console.print("[yellow]APIキーを設定しました。セキュリティのため、設定ファイルへの不正アクセスにご注意ください。[/yellow]")
    
    except ValueError as e:
        console.print(f"[red]設定値が無効です: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]設定の更新に失敗しました: {e}[/red]")
        raise click.Abort()


@config.command()
@click.option('--config-file', type=click.Path(path_type=Path), help='設定ファイルのパス')
@click.confirmation_option(prompt='設定をデフォルトに戻しますか？')
@click.help_option('-h', '--help')
@click.pass_context
def reset(ctx, config_file):
    """設定をデフォルト値に戻す"""
    # グローバルオプションから設定ファイルパスを取得（優先度：ローカル > グローバル）
    if not config_file and ctx.obj:
        config_file = ctx.obj.get('config_file')
    manager = ConfigManager(config_file)
    
    try:
        manager.reset_to_default()
        console.print("[green]設定をデフォルト値に戻しました[/green]")
    except Exception as e:
        console.print(f"[red]設定のリセットに失敗しました: {e}[/red]")
        raise click.Abort()


@config.command()
@click.option('--config-file', type=click.Path(path_type=Path), help='設定ファイルのパス')
@click.confirmation_option(prompt='設定ファイルを削除しますか？')
@click.help_option('-h', '--help')
@click.pass_context
def delete(ctx, config_file):
    """設定ファイルを削除する"""
    # グローバルオプションから設定ファイルパスを取得（優先度：ローカル > グローバル）
    if not config_file and ctx.obj:
        config_file = ctx.obj.get('config_file')
    manager = ConfigManager(config_file)
    
    try:
        manager.delete_config_file()
        console.print("[green]設定ファイルを削除しました[/green]")
    except Exception as e:
        console.print(f"[red]設定ファイルの削除に失敗しました: {e}[/red]")
        raise click.Abort()


@config.command()
@click.option('--config-file', type=click.Path(path_type=Path), help='設定ファイルのパス')
@click.help_option('-h', '--help')
@click.pass_context
def check(ctx, config_file):
    """設定の妥当性をチェックする"""
    logger.info("=== Starting config check command ===")
    logger.debug(f"Input parameters: config_file={config_file}")

    # グローバルオプションから設定ファイルパスを取得（優先度：ローカル > グローバル）
    if not config_file and ctx.obj:
        config_file = ctx.obj.get('config_file')
        logger.debug(f"Using config file from global context: {config_file}")

    logger.info(f"Loading configuration for validation from: {config_file or 'default path'}")
    manager = ConfigManager(config_file)
    logger.debug(f"ConfigManager initialized with path: {manager.config_path}")

    try:
        config = manager.get_config()
        issues = []
        logger.info("Configuration loaded, starting validation checks")

        console.print("[blue]設定をチェック中...[/blue]\n")

        # APIキーのチェック
        logger.info("Starting API key validation")
        console.print("🔑 APIキーの確認...")
        effective_key = manager.get_effective_api_key()
        logger.debug(f"Effective API key present: {bool(effective_key)}")

        if not effective_key:
            logger.warning("No API key found")
            issues.append("APIキーが設定されていません")
            console.print("  [red]✗ APIキーが設定されていません[/red]")
        elif not effective_key.startswith('sk-'):
            logger.warning(f"Invalid API key format: {effective_key[:10]}...")
            issues.append("APIキーの形式が無効です")
            console.print("  [red]✗ APIキーの形式が無効です[/red]")
        else:
            key_source = "設定ファイル" if config.api_key else "環境変数"
            logger.info(f"Valid API key found in {key_source}")
            console.print(f"  [green]✓ APIキーが設定されています ({key_source})[/green]")

        # モデル名のチェック（OpenAI APIで検証）
        logger.info("Starting model validation")
        console.print("\n🤖 モデルの検証...")
        if effective_key:
            logger.debug(f"Validating model '{config.model}' with OpenAI API")
            try:
                console.print(f"  OpenAI APIで '{config.model}' を検証中...")
                logger.debug("Creating OpenAI client for model validation")
                client = OpenAIClient(config, effective_key)

                logger.debug("Calling client.validate_model()")
                if client.validate_model():
                    logger.info(f"Model '{config.model}' validation successful")
                    console.print(f"  [green]✓ モデル '{config.model}' は利用可能です[/green]")
                else:
                    logger.warning(f"Model '{config.model}' validation failed")
                    issues.append(f"OpenAI APIで利用できないモデルです: {config.model}")
                    console.print(f"  [red]✗ モデル '{config.model}' は利用できません[/red]")
            except Exception as e:
                logger.error(f"Model validation error: {e}")
                logger.exception("Model validation exception details:")
                issues.append(f"モデル検証でエラーが発生しました: {e}")
                console.print(f"  [red]✗ モデル検証エラー: {e}[/red]")
        else:
            logger.warning("Skipping model validation due to missing API key")
            issues.append("APIキーが設定されていないため、モデル名を検証できません")
            console.print("  [yellow]⚠ APIキーが設定されていないため、モデル名を検証できません[/yellow]")

        # 閾値のチェック
        logger.info("Validating configuration values")
        console.print("\n📊 設定値の確認...")
        console.print(f"  閾値: {config.threshold}%")
        logger.debug(f"Checking threshold value: {config.threshold}")

        if not 0 <= config.threshold <= 100:
            logger.warning(f"Invalid threshold value: {config.threshold}")
            issues.append(f"閾値が範囲外です: {config.threshold}")
            console.print("  [red]✗ 閾値は0-100の範囲で設定してください[/red]")
        else:
            logger.debug("Threshold value is within valid range")
            console.print("  [green]✓ 閾値は有効範囲内です[/green]")

        logger.debug(f"Other config values - max_tokens: {config.max_tokens}, temperature: {config.temperature}")
        logger.debug(f"Log level settings - console: {config.console_log_level}, file: {config.file_log_level}")
        console.print(f"  最大トークン数: {config.max_tokens}")
        console.print(f"  Temperature: {config.temperature}")
        console.print(f"  コンソールログレベル: {config.console_log_level}")
        console.print(f"  ファイルログレベル: {config.file_log_level}")

        # ログレベルの妥当性チェック
        valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if config.console_log_level not in valid_log_levels:
            logger.warning(f"Invalid console log level: {config.console_log_level}")
            issues.append(f"無効なコンソールログレベル: {config.console_log_level}")
            console.print("  [red]✗ コンソールログレベルが無効です[/red]")
        if config.file_log_level not in valid_log_levels:
            logger.warning(f"Invalid file log level: {config.file_log_level}")
            issues.append(f"無効なファイルログレベル: {config.file_log_level}")
            console.print("  [red]✗ ファイルログレベルが無効です[/red]")

        console.print(f"\n📁 設定ファイル: {manager.config_path}")

        # 結果表示
        logger.info(f"Validation completed. Found {len(issues)} issues")
        console.print("\n" + "="*50)
        if issues:
            logger.warning(f"Configuration validation failed with {len(issues)} issues:")
            for i, issue in enumerate(issues, 1):
                logger.warning(f"Issue {i}: {issue}")
            console.print("[red]❌ 設定に問題があります:[/red]")
            for issue in issues:
                console.print(f"  - {issue}")
        else:
            logger.info("All configuration validation checks passed")
            console.print("[green]✅ 設定に問題はありません[/green]")

        logger.info("=== Config check command completed successfully ===")

    except Exception as e:
        logger.error(f"Failed to check configuration: {e}")
        logger.exception("Full exception details:")
        console.print(f"[red]設定のチェックに失敗しました: {e}[/red]")
        raise click.Abort()