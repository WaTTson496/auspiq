"""練習機能のコア実装"""
import time
import threading
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .models import (
    PracticeQuestion,
    PracticeAnswer,
    PracticeSession,
    PracticeStats,
    AnalysisPoint
)


class PracticeEngine:
    """練習機能のメインエンジン"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.session: Optional[PracticeSession] = None
        self.current_question_index = 0
        self.current_position = 0
        self.is_paused = False
        self.is_stopped = False
        self.auto_pause_threshold = 80
        self.display_speed = 0.1  # 文字表示間隔（秒）
        self._display_thread: Optional[threading.Thread] = None
        self._user_input_event = threading.Event()
        self._user_command: Optional[str] = None
        self._question_start_time: float = 0.0
        self._auto_pause_disabled: bool = False  # 自動停止が一度発生したら無効化
        self._player_score: int = 0  # プレイヤーの正解数
        self._system_score: int = 0  # システムの正解数
        self._player_incorrect: int = 0  # プレイヤーの不正解数
        self._system_incorrect: int = 0  # システムの不正解数
        self._answerer: Optional[str] = None  # 解答権を持つ者 ('player' or 'system')

    def start_session(self, questions: List[PracticeQuestion]) -> None:
        """練習セッションを開始"""
        self.session = PracticeSession(
            questions=questions,
            start_time=time.time()
        )
        self.current_question_index = 0
        self.is_stopped = False

        self.console.print(Panel(
            f"[bold green]練習セッションを開始します[/bold green]\n"
            f"問題数: {len(questions)}問\n"
            f"基本操作:\n"
            f"  - [Enter]: 一時停止/解答権獲得\n"
            f"  - 'a': 解答表示\n"
            f"  - 'q': 終了\n"
            f"  - 'n': 次の問題\n"
            f"解答権獲得後:\n"
            f"  - [Enter]: 解答入力へ\n"
            f"  - 'c': 問題文継続",
            title="練習開始"
        ))

        self._run_session()

    def _run_session(self) -> None:
        """セッション実行のメインループ"""
        if not self.session:
            return

        while (self.current_question_index < len(self.session.questions) and
               not self.is_stopped):
            self._run_question()
            if not self.is_stopped:
                self.current_question_index += 1

        # 停止理由に関わらず結果を表示
        self._finish_session()

    def _run_question(self) -> None:
        """単一問題の実行"""
        if not self.session:
            return

        question = self.session.questions[self.current_question_index]
        self.current_position = 0
        self.is_paused = False
        self._question_start_time = time.time()
        self._auto_pause_disabled = False  # 新しい問題では自動停止を再有効化
        self._answerer = None  # 解答権をリセット

        self.console.print(f"\n[bold]問題 {self.current_question_index + 1}/{len(self.session.questions)}[/bold]")

        # スコア表を作成
        score_table = Table(title="現在のスコア", show_header=True, header_style="bold blue")
        score_table.add_column("対戦相手", style="cyan", no_wrap=True)
        score_table.add_column("○", style="green", justify="center")
        score_table.add_column("×", style="red", justify="center")

        score_table.add_row("プレイヤー", str(self._player_score), str(self._player_incorrect))
        score_table.add_row("システム", str(self._system_score), str(self._system_incorrect))

        self.console.print(score_table)
        self.console.print()

        # 問題開始前の待機
        if not self._wait_for_question_start():
            return  # 練習終了が選択された

        # 問題文の段階的表示を開始
        self._start_question_display(question)

        # ユーザー入力待機
        self._wait_for_user_action()

        # 表示スレッドを停止
        if self._display_thread and self._display_thread.is_alive():
            self._display_thread.join(timeout=0.1)

    def _start_question_display(self, question: PracticeQuestion) -> None:
        """問題文の段階的表示を開始"""
        def display_loop():
            text_length = len(question.original_text)

            while (self.current_position < text_length and
                   not self.is_paused and not self.is_stopped):

                # 現在の位置までのテキストを表示
                current_text = question.original_text[:self.current_position + 1]
                self._display_current_text(current_text)

                # 自動一時停止の判定
                if self._should_auto_pause(question, self.current_position):
                    self.is_paused = True
                    self._answerer = 'system'  # システムが解答権を得る
                    self.console.print("\n[yellow]自動一時停止（蓋然性が閾値を超えました）[/yellow]")
                    self.console.print("[blue]システムが解答権を獲得しました[/blue]")
                    self.console.print("[cyan]操作: [Enter]解答入力へ, 'c'問題文継続[/cyan]")
                    break

                self.current_position += 1
                time.sleep(self.display_speed)

            if self.current_position >= text_length and not self.is_stopped:
                self.console.print("\n[blue]問題文表示完了[/blue]")
                self.is_paused = True

        self._display_thread = threading.Thread(target=display_loop, daemon=True)
        self._display_thread.start()

    def _resume_question_display(self, question: PracticeQuestion) -> None:
        """問題文の段階的表示を現在位置から再開"""
        def display_loop():
            text_length = len(question.original_text)

            while (self.current_position < text_length and
                   not self.is_paused and not self.is_stopped):

                # 現在の位置までのテキストを表示
                current_text = question.original_text[:self.current_position + 1]
                self._display_current_text(current_text)

                # 自動一時停止の判定
                if self._should_auto_pause(question, self.current_position):
                    self.is_paused = True
                    self._answerer = 'system'  # システムが解答権を得る
                    self.console.print("\n[yellow]自動一時停止（蓋然性が閾値を超えました）[/yellow]")
                    self.console.print("[blue]システムが解答権を獲得しました[/blue]")
                    self.console.print("[cyan]操作: [Enter]解答入力へ, 'c'問題文継続[/cyan]")
                    break

                self.current_position += 1
                time.sleep(self.display_speed)

            if self.current_position >= text_length and not self.is_stopped:
                self.console.print("\n[blue]問題文表示完了[/blue]")
                self.is_paused = True

        self._display_thread = threading.Thread(target=display_loop, daemon=True)
        self._display_thread.start()

    def _display_current_text(self, text: str) -> None:
        """現在のテキストを表示"""
        # 行全体をクリアしてからテキストを表示
        import sys
        # カーソルを行の始めに移動し、行全体をクリア
        sys.stdout.write("\r" + " " * 100 + "\r")  # 行を空白で上書きしてクリア
        sys.stdout.write(text)
        sys.stdout.flush()

    def _should_auto_pause(self, question: PracticeQuestion, position: int) -> bool:
        """自動一時停止が必要かどうかを判定"""
        # 既に自動停止が発生していたら以降チェックしない
        if self._auto_pause_disabled:
            return False

        for analysis_point in question.analysis_points:
            if (analysis_point.position == position and
                analysis_point.total_probability >= self.auto_pause_threshold):
                # 一度自動停止したら以降の自動停止を無効化
                self._auto_pause_disabled = True
                return True
        return False

    def _wait_for_user_action(self) -> None:
        """ユーザーアクションの待機"""
        while not self.is_stopped and self.current_question_index < len(self.session.questions):
            try:
                user_input = input().strip().lower()

                if user_input == 'q':
                    self.is_stopped = True
                    break
                elif user_input == 'a':
                    self._show_answer()
                    break
                elif user_input == 'n':
                    self._record_skip()
                    break
                elif user_input == 'c' and self.is_paused and self._answerer:
                    # 解答権獲得後の問題文継続
                    self._answerer = None  # 解答権をリセット
                    self.is_paused = False
                    if self.current_position >= len(self.session.questions[self.current_question_index].original_text):
                        # 既に表示完了の場合は解答入力に進む
                        self._handle_answer_input()
                        break
                    elif not self._display_thread or not self._display_thread.is_alive():
                        # 表示スレッドが停止している場合は現在位置から再開始
                        question = self.session.questions[self.current_question_index]
                        self._resume_question_display(question)
                        continue
                    else:
                        # まだ表示中の場合は表示を継続
                        continue
                elif user_input == '' and self.is_paused:
                    if self._answerer:
                        # 解答権が決まっている場合はEnterで解答入力に進む
                        self._handle_answer_input()
                        break
                    else:
                        # 解答権が未定の場合は一時停止中のEnterで再開
                        self.is_paused = False
                        if self.current_position >= len(self.session.questions[self.current_question_index].original_text):
                            # 表示が完了している場合は解答入力に進む
                            self._handle_answer_input()
                            break
                        elif not self._display_thread or not self._display_thread.is_alive():
                            # 表示スレッドが停止している場合は現在位置から再開始
                            question = self.session.questions[self.current_question_index]
                            self._resume_question_display(question)
                            continue
                        else:
                            # まだ表示中の場合は表示を継続
                            continue
                elif user_input == '':
                    # 表示中のEnterで一時停止、プレイヤーが解答権を獲得
                    self.is_paused = True
                    if not self._answerer:  # まだ解答権が決まっていない場合
                        self._answerer = 'player'
                        self.console.print("[green]プレイヤーが解答権を獲得しました[/green]")
                        self.console.print("[cyan]操作: [Enter]解答入力へ, 'c'問題文継続[/cyan]")

            except (EOFError, KeyboardInterrupt):
                self.is_stopped = True
                break

    def _show_answer(self) -> None:
        """解答を表示"""
        if not self.session:
            return

        self._handle_answer_input()

    def _handle_answer_input(self) -> None:
        """解答入力の処理"""
        if not self.session:
            return

        question = self.session.questions[self.current_question_index]

        # 問題文全文を表示
        self.console.print(f"\n[bold yellow]問題文:[/bold yellow]")
        self.console.print(f"{question.original_text}")

        # 解答を表示
        self.console.print(f"\n[bold green]解答: {question.correct_answer or '（不明）'}[/bold green]")

        # 解答権の表示
        if self._answerer == 'system':
            self.console.print("[blue]システムの解答権です[/blue]")
            # システムが自動回答
            self._handle_system_answer(question)
            return
        elif self._answerer == 'player':
            self.console.print("[green]プレイヤーの解答権です[/green]")
        else:
            # 解答権が決まっていない場合（問題文完了時など）
            self.console.print("[yellow]解答権: 未決定（プレイヤーが入力）[/yellow]")

        self.console.print("\n結果を入力してください:")
        self.console.print("  c: 正解, i: 不正解, s: スキップ")

        while True:
            try:
                result_input = input("結果: ").strip().lower()
                if result_input in ['c', 'correct']:
                    self._record_answer('correct', None)
                    if self._answerer == 'player':
                        self._player_score += 1
                    break
                elif result_input in ['i', 'incorrect']:
                    self._record_answer('incorrect', None)
                    if self._answerer == 'player':
                        self._player_incorrect += 1
                    break
                elif result_input in ['s', 'skip']:
                    self._record_skip()
                    break
                else:
                    self.console.print("[red]無効な入力です[/red]")
            except (EOFError, KeyboardInterrupt):
                self.is_stopped = True
                break

    def _record_answer(self, result: str, user_answer: Optional[str]) -> None:
        """回答を記録"""
        if not self.session:
            return

        time_taken = time.time() - self._question_start_time
        answer = PracticeAnswer(
            result=result,
            user_answer=user_answer,
            push_position=self.current_position,
            time_taken=time_taken
        )
        self.session.answers.append(answer)

    def _record_skip(self) -> None:
        """スキップを記録"""
        self._record_answer('skip', None)

    def _finish_session(self) -> None:
        """セッション終了処理"""
        if not self.session:
            return

        self.session.end_time = time.time()
        stats = self._calculate_stats()
        self._display_results(stats)

    def _calculate_stats(self) -> PracticeStats:
        """統計を計算"""
        if not self.session:
            return PracticeStats(
                total_questions=0,
                correct_answers=0,
                incorrect_answers=0,
                skipped_questions=0,
                average_push_position=0.0,
                total_time=0.0,
                accuracy_rate=0.0
            )

        answers = self.session.answers
        total_questions = len(answers)

        if total_questions == 0:
            return PracticeStats(
                total_questions=0,
                correct_answers=0,
                incorrect_answers=0,
                skipped_questions=0,
                average_push_position=0.0,
                total_time=0.0,
                accuracy_rate=0.0
            )

        correct_count = sum(1 for a in answers if a.result == 'correct')
        incorrect_count = sum(1 for a in answers if a.result == 'incorrect')
        skip_count = sum(1 for a in answers if a.result == 'skip')

        avg_push_position = sum(a.push_position for a in answers) / total_questions
        total_time = self.session.end_time - self.session.start_time if self.session.end_time and self.session.start_time else 0.0
        accuracy_rate = (correct_count / total_questions) * 100.0

        return PracticeStats(
            total_questions=total_questions,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            skipped_questions=skip_count,
            average_push_position=avg_push_position,
            total_time=total_time,
            accuracy_rate=accuracy_rate
        )

    def _display_results(self, stats: PracticeStats) -> None:
        """結果表示"""
        # 実際に実施した問題数
        attempted_questions = self.current_question_index

        # 対戦結果の表示
        battle_table = Table(title="対戦結果")
        battle_table.add_column("対戦相手", style="cyan", no_wrap=True)
        battle_table.add_column("成績", style="green")
        battle_table.add_column("正解率", style="magenta")

        player_total = self._player_score + self._player_incorrect
        system_total = self._system_score + self._system_incorrect

        player_rate = (self._player_score / player_total * 100.0) if player_total > 0 else 0.0
        system_rate = (self._system_score / system_total * 100.0) if system_total > 0 else 0.0

        battle_table.add_row("プレイヤー", f"{self._player_score}○{self._player_incorrect}×", f"{player_rate:.1f}%")
        battle_table.add_row("システム", f"{self._system_score}○{self._system_incorrect}×", f"{system_rate:.1f}%")

        # 勝敗判定
        if self._player_score > self._system_score:
            winner = "[bold green]プレイヤーの勝利！[/bold green]"
        elif self._system_score > self._player_score:
            winner = "[bold red]システムの勝利！[/bold red]"
        else:
            winner = "[bold yellow]引き分け[/bold yellow]"

        self.console.print(battle_table)
        self.console.print(f"\n{winner}")

        # 詳細統計の表示
        table = Table(title="詳細統計")
        table.add_column("項目", style="cyan", no_wrap=True)
        table.add_column("値", style="magenta")

        table.add_row("実施問題数", f"{attempted_questions}/{len(self.session.questions) if self.session else 0}")
        table.add_row("総回答数", str(stats.total_questions))
        table.add_row("正解数", str(stats.correct_answers))
        table.add_row("不正解数", str(stats.incorrect_answers))
        table.add_row("スキップ数", str(stats.skipped_questions))
        table.add_row("正解率", f"{stats.accuracy_rate:.1f}%")
        table.add_row("平均押しポイント", f"{stats.average_push_position:.1f}文字")
        table.add_row("総時間", f"{stats.total_time:.1f}秒")

        self.console.print(table)

    def set_auto_pause_threshold(self, threshold: int) -> None:
        """自動一時停止の閾値を設定"""
        self.auto_pause_threshold = threshold

    def set_display_speed(self, speed: float) -> None:
        """文字表示速度を設定"""
        self.display_speed = max(0.01, speed)  # 最小0.01秒

    def _wait_for_question_start(self) -> bool:
        """問題開始前の待機。Trueで問題開始、Falseで練習終了"""
        self.console.print("\n[yellow]操作:[/yellow]")
        self.console.print("  [Enter]: 問題開始")
        self.console.print("  'q': 練習終了（結果表示）")
        self.console.print("  'quit': 練習終了（結果表示）")

        while True:
            try:
                user_input = input("\n入力: ").strip().lower()

                if user_input == '':
                    # Enterで問題開始
                    return True
                elif user_input in ['q', 'quit']:
                    # 練習終了
                    self.is_stopped = True
                    return False
                else:
                    self.console.print("[red]無効な入力です。Enterで問題開始、'q'で練習終了してください。[/red]")

            except (EOFError, KeyboardInterrupt):
                self.is_stopped = True
                return False

    def _get_probability_at_position(self, question: PracticeQuestion, position: int) -> float:
        """指定位置での蓋然性を取得"""
        for analysis_point in question.analysis_points:
            if analysis_point.position == position:
                return analysis_point.total_probability
        return 0.0

    def _handle_system_answer(self, question: PracticeQuestion) -> None:
        """システムの解答表示と判定処理"""
        # システムの最有力候補を表示
        self._display_system_candidate(question)

        # ユーザーの判定入力を待つ
        self._wait_for_system_judgment(question)

    def _display_system_candidate(self, question: PracticeQuestion) -> None:
        """システムの最有力問題文候補と解答候補を表示"""
        # 現在位置での蓋然性情報を取得
        current_analysis = self._get_analysis_at_position(question, self.current_position)

        self.console.print("\n[bold blue]システムの判定:[/bold blue]")

        # 現在位置までの問題文を表示
        current_text = question.original_text[:self.current_position + 1]
        self.console.print(f"[yellow]問題文（現在位置まで）:[/yellow] {current_text}")

        if current_analysis and current_analysis.candidates:
            # 候補がある場合、最有力候補を表示
            top_candidate = current_analysis.candidates[0]  # 最初の候補が最有力
            self.console.print(f"[cyan]システムの最有力問題文候補:[/cyan] {top_candidate.full_text}")
            self.console.print(f"[cyan]システムの最有力解答候補:[/cyan] {top_candidate.answer}")
            self.console.print(f"[cyan]確信度:[/cyan] {top_candidate.probability:.1f}%")
            self.console.print(f"[cyan]全体蓋然性:[/cyan] {current_analysis.total_probability:.1f}%")
        else:
            # 候補データがない場合
            probability = self._get_probability_at_position(question, self.current_position)
            if probability > 0:
                self.console.print(f"[cyan]システムの推定確信度:[/cyan] {probability:.1f}%")
            else:
                self.console.print("[cyan]システム:[/cyan] 判定困難（蓋然性データなし）")

        self.console.print(f"[green]正解:[/green] {question.correct_answer or '（不明）'}")

    def _wait_for_system_judgment(self, question: PracticeQuestion) -> None:
        """システム解答のユーザー判定を待つ"""
        self.console.print("\n[bold yellow]判定を入力してください:[/bold yellow]")
        self.console.print("  [Enter]: システムの自動判定")
        self.console.print("  c: システム正解として記録")
        self.console.print("  i: システム不正解として記録")

        while True:
            try:
                user_input = input("判定: ").strip().lower()

                if user_input == '':
                    # Enterで自動判定
                    self._perform_automatic_judgment(question)
                    break
                elif user_input == 'c':
                    # 手動で正解として記録
                    self.console.print("[green]システム正解として記録しました[/green]")
                    self._record_answer('correct', None)
                    self._system_score += 1
                    break
                elif user_input == 'i':
                    # 手動で不正解として記録
                    self.console.print("[red]システム不正解として記録しました[/red]")
                    self._record_answer('incorrect', None)
                    self._system_incorrect += 1
                    break
                else:
                    self.console.print("[red]無効な入力です。Enter、c、またはiを入力してください。[/red]")

            except (EOFError, KeyboardInterrupt):
                self.is_stopped = True
                break

    def _perform_automatic_judgment(self, question: PracticeQuestion) -> None:
        """システムの自動判定を実行"""
        import random

        # 現在位置での蓋然性を取得
        probability = self._get_probability_at_position(question, self.current_position)

        if probability == 0:
            # 蓋然性データがない場合はランダム（50%の確率で正解）
            is_correct = random.random() < 0.5
        else:
            # 蓋然性に基づいて正誤を決定
            is_correct = random.random() < (probability / 100.0)

        if is_correct:
            self.console.print("[blue]システムの自動判定: 正解[/blue]")
            self._record_answer('correct', None)
            self._system_score += 1
        else:
            self.console.print("[blue]システムの自動判定: 不正解[/blue]")
            self._record_answer('incorrect', None)
            self._system_incorrect += 1

    def _get_analysis_at_position(self, question: PracticeQuestion, position: int) -> Optional[AnalysisPoint]:
        """指定位置での解析データを取得"""
        for analysis_point in question.analysis_points:
            if analysis_point.position == position:
                return analysis_point
        return None