import os

os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")

from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from image_agent.llm import resolve_llm


def build_text_llm() -> LLM:
    """Text model for the crew. GPT-6 tool calls go through the Responses API."""
    model = resolve_llm(os.getenv("MODEL"))
    if model.startswith("openai/gpt-6"):
        return LLM(model=model, api="responses")
    return LLM(model=model)


@CrewBase
class ImageAgent:
    """Sequential crew: image analyst writes a brief, then Instagram and Facebook writers."""

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
    def instagram_task(self) -> Task:
        return Task(
            config=self.tasks_config["instagram_task"],  # type: ignore[index]
            name="instagram",
            context=[self.image_analysis_task()],
        )

    @task
    def facebook_task(self) -> Task:
        return Task(
            config=self.tasks_config["facebook_task"],  # type: ignore[index]
            name="facebook",
            context=[self.image_analysis_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
