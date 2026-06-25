import os

from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from image_agent.llm import resolve_llm

DEFAULT_LLM = resolve_llm(os.getenv("MODEL"))


@CrewBase
class ImageAgent:
    """Sequential crew: image analyst writes a brief, then one writer per platform."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def image_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["image_analyst"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @agent
    def twitter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["twitter_writer"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @agent
    def reddit_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["reddit_writer"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @agent
    def instagram_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["instagram_writer"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @agent
    def facebook_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["facebook_writer"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @task
    def image_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["image_analysis_task"],  # type: ignore[index]
            name="image_analysis",
        )

    @task
    def twitter_task(self) -> Task:
        return Task(
            config=self.tasks_config["twitter_task"],  # type: ignore[index]
            name="twitter",
            context=[self.image_analysis_task()],
        )

    @task
    def reddit_task(self) -> Task:
        return Task(
            config=self.tasks_config["reddit_task"],  # type: ignore[index]
            name="reddit",
            context=[self.image_analysis_task()],
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
