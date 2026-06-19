import json
import os

from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, before_kickoff, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from image_agent.llm import resolve_llm
from image_agent.vision import analyze_image_url

DEFAULT_LLM = resolve_llm(os.getenv("MODEL"))


@CrewBase
class ImageAgent:
    """Social post caption crew: vision pre-step, then copy + platform optimization."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @before_kickoff
    def enrich_with_image_analysis(self, inputs: dict) -> dict:
        """Run vision outside CrewAI tools (Groq breaks multimodal + structured output)."""
        analysis = analyze_image_url(inputs["image_url"])
        data = analysis.model_dump()
        inputs["image_analysis_json"] = json.dumps(data, indent=2)
        inputs["image_tags_list"] = ", ".join(data["image_tags"])
        inputs["scene_summary"] = data["scene_summary"]
        inputs["mood"] = data["mood"]
        inputs["food_items"] = ", ".join(data["food_items"])
        return inputs

    @agent
    def brand_copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_copywriter"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @agent
    def social_optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config["social_optimizer"],  # type: ignore[index]
            llm=DEFAULT_LLM,
            verbose=True,
        )

    @task
    def write_caption_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_caption_task"],  # type: ignore[index]
        )

    @task
    def optimize_post_task(self) -> Task:
        return Task(
            config=self.tasks_config["optimize_post_task"],  # type: ignore[index]
            context=[self.write_caption_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
