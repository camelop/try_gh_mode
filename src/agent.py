import json
import chess
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, Part, TextPart, DataPart
from a2a.utils import new_agent_text_message

from messenger import Messenger


class Agent:
    def __init__(self):
        self.messenger = Messenger()
        # initialize other state here

    async def run(self, input_text: str, updater: TaskUpdater) -> None:
        """Implement your agent logic here.

        Args:
            input_text: The incoming message text
            updater: Report progress (update_status) and results (add_artifact)

        Use self.messenger.talk_to_agent(message, url) to call other agents.
        """
        data = json.loads(
            input_text
        )  # no need to be made robust for now, as eval happens in repo
        participants = data["participants"]

        # init board
        board = chess.Board()
        print("Initial board:", board.fen())

        # Game loop
        next = "player_w"  # "player_w" or "player_b"
        winner = None
        result = {}
        while True:
            target_url = participants[next]
            response = await self.messenger.talk_to_agent(
                f"Your turn to play. Current board state (FEN): {board.fen()}. Please provide your move in UCI format. Only provide the move string.",
                target_url,
            )
            move_uci = response.strip()
            try:
                move = chess.Move.from_uci(move_uci)
                if move in board.legal_moves:
                    board.push(move)
                    await updater.update_status(
                        TaskState.IN_PROGRESS,
                        new_agent_text_message(
                            f"{next} played move: {move_uci}. Current board FEN: {board.fen()}"
                        ),
                    )
                else:
                    raise Exception("Illegal move")
            except Exception as e:
                print("Error processing move:", e)
                import traceback

                traceback.print_stack()
                # invalid move format, opponent wins
                winner = "player_b" if next == "player_w" else "player_w"
                result = {
                    "reason": "invalid_move_format",
                    "invalid_move": move_uci,
                    "fen": board.fen(),
                    "winner": winner,
                }
                break
            if board.is_game_over():
                outcome = board.outcome()
                if outcome.winner is None:
                    winner = "draw"
                elif outcome.winner == chess.WHITE:
                    winner = "player_w"
                else:
                    winner = "player_b"
                result = {
                    "reason": "game_over",
                    "fen": board.fen(),
                    "winner": winner,
                }
                break
            # switch turns
            next = "player_b" if next == "player_w" else "player_w"

        await updater.add_artifact(
            parts=[
                Part(root=TextPart(text="Game Over")),
                Part(root=DataPart(data=result)),
            ],
            name="Result",
        )
