import inspect
import requests
import json
import re
from typing import Any, Callable, Awaitable, Dict

class DispatcherClient:
    from abc import ABC, abstractmethod

    @abstractmethod
    def get_function_registry(self):
        ...

    @abstractmethod
    def get_model(self):
        ...


class LLMDispatcher:
    """
    LLMDispatcher

    This class handles interaction with an external Large Language Model (LLM) service 
    and dispatches the model's function call responses to registered local methods.

    The dispatcher sends prompts to the LLM service, extracts structured JSON responses 
    indicating which function to call, and dynamically invokes the appropriate function 
    with provided arguments. This allows LLM-driven workflows to integrate seamlessly 
    with local business logic.

    Attributes:
        llm_service_url (str): The URL of the LLM service endpoint.
        function_registry (Dict[str, Callable]): A mapping of function names to callable methods.
        event_emitter (Callable[[str], Awaitable[None]]): Optional asynchronous callback for emitting progress events.
    """

    import json, re
    from typing import Final
    _JSON_BLOCK: Final[re.Pattern] = re.compile(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", re.DOTALL)

    def __init__(self, 
                 llm_service_url: str, 
                 client: DispatcherClient,
                 event_emitter: Callable[[str], Awaitable[None]] = None):
        """
        Initialize the LLMDispatcher.

        Args:
            llm_service_url (str): URL of the external LLM service.
            function_registry (Dict[str, Callable]): Registry mapping function names to local callable methods.
            event_emitter (Callable[[str], Awaitable[None]], optional): 
                Optional asynchronous callback for emitting progress or debug events.
        """
        self.llm_service_url = llm_service_url
        self.function_registry = client.get_function_registry()
        self.model = client.get_model()
        self.event_emitter = event_emitter

    async def _dispatch(self, 
                  state: Any, 
                  dispatch_msg: dict) -> None:
        """
        Dispatches a parsed LLM function call to the corresponding local method.

        Args:
            state (Any): The current state object, typically representing diagnostic state or workflow context.
            dispatch_msg (dict): A dictionary containing "function_name" and "arguments" keys.

        Raises:
            ValueError: If the function name is not registered in the function registry.
        """
        fn_name = dispatch_msg["function_name"]
        fn_args = dispatch_msg["arguments"]

        if fn_name not in self.function_registry:
            raise ValueError(f"Unknown function: {fn_name}")

        func = self.function_registry[fn_name]
        if self.event_emitter:
            await self.event_emitter(f"LLM Dispatching: {fn_name} with args: {fn_args}")

        try:
            if inspect.iscoroutinefunction(func):
                await func(state, **fn_args)
            else:
                func(state, **fn_args)
        except Exception as exc:
            if self.event_emitter:
                await self.event_emitter(
                    f"Error while executing {fn_name}: {exc.__class__.__name__}: {exc}"
                )
            # Re‑raise to let upstream handlers/logging deal with it as well
            raise

    async def run(self, 
                  state: Any, 
                  prompt: str) -> None:
        """
        Executes an LLM prompt and dispatches the function call result.

        This method sends a prompt to the configured LLM service, extracts the JSON 
        function call from the response, and invokes the corresponding registered 
        function with the provided arguments.

        Args:
            state (Any): The current workflow state, which will be passed into the dispatched function.
            prompt (str): The input prompt to send to the LLM service.
            model (str, optional): The model identifier to use when making the request. Defaults to "thewindmom/llama3-med42-8b:latest".

        Raises:
            RuntimeError: If the LLM service request fails or returns an invalid response.
            Exception: If the LLM response does not contain a valid JSON object to dispatch.
        """
        try:
            response = requests.post(
                self.llm_service_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            response.raise_for_status()
            content = response.json().get("response")

            match = self._JSON_BLOCK.search(content)
            if not match:
                raise Exception("No JSON content from LLM")

            dispatch_msg = json.loads(match.group(0))
            await self._dispatch(state, dispatch_msg)

        except requests.RequestException as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
