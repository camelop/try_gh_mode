from dotenv import load_dotenv
import litellm
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TextPart

from messenger import Messenger

load_dotenv()


class Agent:
    def __init__(self):
        self.messages = []

    async def run(self, input_text: str, updater: TaskUpdater) -> None:
        print(f"> {input_text}")
        self.messages.append({"content": input_text, "role": "user"})
        completion = litellm.completion(model="gpt-4o", messages=self.messages)
        response = completion.choices[0].message.content
        self.messages.append({"content": response, "role": "assistant"})
        print(response)

        await updater.add_artifact(
            parts=[Part(root=TextPart(text=response))],
            name="Result",
        )
