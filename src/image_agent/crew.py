import os

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

from typing import Any

from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Crew, LLM, Process, Task, TaskOutput
from crewai.project import CrewBase, agent, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from image_agent.cliches import find_banned_phrases, find_photo_phrases
from image_agent.llm import resolve_llm
from image_agent.parsing import extract_platform_json


def build_text_llm() -> LLM:
    """Text model for the crew. GPT-6 tool calls go through the Responses API."""
    model = resolve_llm(os.getenv("MODEL"))
    if model.startswith("openai/gpt-6"):
        return LLM(model=model, api="responses")
    return LLM(model=model)


def validate_draft(output: TaskOutput) -> tuple[bool, Any]:
    """Send a draft back if it is not valid JSON, leans on stock phrases, or describes the photo."""
    try:
        draft = extract_platform_json(output.raw)
    except ValueError:
        return (False, 'Return valid JSON with keys "instagram" and "facebook".')
    if not isinstance(draft, dict):
        return (False, 'Return a JSON object with keys "instagram" and "facebook".')

    missing = [key for key in ("instagram", "facebook") if not str(draft.get(key) or "").strip()]
    if missing:
        return (False, f"Missing caption text for: {', '.join(missing)}.")

    captions = f"{draft['instagram']}\n{draft['facebook']}"
    found = find_banned_phrases(captions)
    if found:
        return (
            False,
            f"Rewrite without these generic phrases: {', '.join(found)}. "
            "Use a concrete detail from the brief instead.",
        )
    photo_talk = find_photo_phrases(captions)
    if photo_talk:
        return (
            False,
            f"Rewrite without describing the photo ({', '.join(photo_talk)}). "
            "Talk about the food and the moment as if the reader is at the table.",
        )
    return (True, output.raw)


@CrewBase
class ImageAgent:
    """Agents and tasks for the air-gapped caption pipeline.

    Each stage runs as its own small crew so drafters stay isolated:
    brief_crew -> one draft_crew per angle (fresh instance each) -> editor crews.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def image_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["image_analyst"],  # type: ignore[index]
            llm=build_text_llm(),
            verbose=True,
        )

    @agent
    def caption_drafter(self) -> Agent:
        return Agent(
            config=self.agents_config["caption_drafter"],  # type: ignore[index]
            llm=build_text_llm(),
            allow_delegation=False,
            memory=False,
            verbose=True,
        )

    @agent
    def instagram_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["instagram_writer"],  # type: ignore[index]
            llm=build_text_llm(),
            verbose=True,
        )

    @agent
    def facebook_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["facebook_writer"],  # type: ignore[index]
            llm=build_text_llm(),
            verbose=True,
        )

    @task
    def image_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["image_analysis_task"],  # type: ignore[index]
            name="image_analysis",
        )

    @task
    def draft_task(self) -> Task:
        return Task(
            config=self.tasks_config["draft_task"],  # type: ignore[index]
            name="draft",
            guardrail=validate_draft,
        )

    @task
    def instagram_task(self) -> Task:
        return Task(
            config=self.tasks_config["instagram_task"],  # type: ignore[index]
            name="instagram",
        )

    @task
    def facebook_task(self) -> Task:
        return Task(
            config=self.tasks_config["facebook_task"],  # type: ignore[index]
            name="facebook",
        )

    def _single_task_crew(self, worker: Agent, job: Task) -> Crew:
        return Crew(
            agents=[worker],
            tasks=[job],
            process=Process.sequential,
            memory=False,
            verbose=True,
        )

    def brief_crew(self) -> Crew:
        """Image analyst turns the vision output into a creative brief."""
        return self._single_task_crew(self.image_analyst(), self.image_analysis_task())

    def draft_crew(self) -> Crew:
        """One air-gapped drafter. Build each from a fresh ImageAgent() so no state is shared."""
        return self._single_task_crew(self.caption_drafter(), self.draft_task())

    def instagram_crew(self) -> Crew:
        """Blind Instagram editor that picks and polishes from anonymous drafts."""
        return self._single_task_crew(self.instagram_writer(), self.instagram_task())

    def facebook_crew(self) -> Crew:
        """Blind Facebook editor that picks and polishes from anonymous drafts."""
        return self._single_task_crew(self.facebook_writer(), self.facebook_task())
