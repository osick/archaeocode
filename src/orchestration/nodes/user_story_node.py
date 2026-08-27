"""
User Story Extraction Node
============================

Extracts user stories from legacy code using LLM analysis.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.orchestration.state.graph_state import MigrationState, CodeArtifact, AnalysisPhase


class UserStory:
    """Represents a generated user story"""

    def __init__(
        self,
        title: str,
        user_role: str,
        capability: str,
        benefit: str,
        acceptance_criteria: List[str],
        code_files: List[str],
        complexity: int,
        priority: str = "Medium",
        confidence: float = 0.0
    ):
        self.title = title
        self.user_role = user_role
        self.capability = capability
        self.benefit = benefit
        self.acceptance_criteria = acceptance_criteria
        self.code_files = code_files
        self.complexity = complexity
        self.priority = priority
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "user_role": self.user_role,
            "capability": self.capability,
            "benefit": self.benefit,
            "acceptance_criteria": self.acceptance_criteria,
            "code_files": self.code_files,
            "complexity": self.complexity,
            "priority": self.priority,
            "confidence": self.confidence
        }

    def to_markdown(self) -> str:
        """Convert to markdown format"""
        md = f"### User Story: {self.title}\n\n"
        md += f"**Priority**: {self.priority} | **Complexity**: {self.complexity} points | **Confidence**: {self.confidence:.2f}\n\n"
        md += f"As a **{self.user_role}**,\n"
        md += f"I want to **{self.capability}**,\n"
        md += f"So that **{self.benefit}**.\n\n"

        md += "**Acceptance Criteria**:\n"
        for i, criterion in enumerate(self.acceptance_criteria, 1):
            md += f"{i}. {criterion}\n"

        md += f"\n**Code Mapping**:\n"
        md += f"- Files: {', '.join(self.code_files)}\n"

        return md


class UserStoryExtractionNode:
    """
    Node that extracts user stories from code using LLM analysis.

    Responsibilities:
    - Analyze code artifacts for business logic
    - Generate user stories using LLM
    - Validate stories against INVEST criteria
    - Prioritize and rank stories
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM for user story generation"""
        try:
            from dotenv import load_dotenv
            load_dotenv()

            # Try Anthropic Claude first
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                from langchain_anthropic import ChatAnthropic
                model = os.getenv("MODEL_NAME", "claude-sonnet-5")
                kwargs = {"model": model, "api_key": api_key}
                # Claude 5 models no longer accept a temperature parameter
                temperature = os.getenv("USER_STORY_TEMPERATURE")
                if temperature and not model.startswith(("claude-sonnet-5", "claude-opus-5", "claude-fable-5", "claude-5")):
                    kwargs["temperature"] = float(temperature)
                self.llm = ChatAnthropic(**kwargs)
                return

            # Fallback to OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=os.getenv("MODEL_NAME", "gpt-4-turbo-preview"),
                    temperature=float(os.getenv("USER_STORY_TEMPERATURE", "0.3")),
                    api_key=api_key
                )
                return

            print("⚠️  No LLM API key found. User story extraction will be skipped.")
            print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file")
            self.llm = None

        except Exception as e:
            print(f"⚠️  Failed to initialize LLM: {e}")
            self.llm = None

    def _create_story_prompt(self, artifact: CodeArtifact) -> str:
        """Create prompt for user story generation"""

        # Truncate code if too long
        max_length = int(os.getenv("USER_STORY_MAX_CODE_LENGTH", "500"))
        code_content = artifact["content"]
        if len(code_content) > max_length:
            code_content = code_content[:max_length] + "\n... (truncated)"

        prompt = f"""Analyze this {artifact['language']} code and generate a user story.

Code File: {artifact['path']}
Language: {artifact['language']}
Lines of Code: {artifact['metadata'].get('line_count', 'unknown')}

Code:
```{artifact['language']}
{code_content}
```

Generate a user story following this format:

Title: [Short descriptive title]
User Role: [Who uses this feature]
Capability: [What they want to do]
Benefit: [Why they want to do it]
Priority: [High/Medium/Low]
Complexity: [Story points 1-13, Fibonacci scale]
Confidence: [0.0-1.0, how confident you are]

Acceptance Criteria (3-5 specific, testable criteria):
1. Given [context], When [action], Then [outcome]
2. Given [context], When [action], Then [outcome]
3. Given [context], When [action], Then [outcome]

Focus on the BUSINESS VALUE, not technical implementation.
Use simple, non-technical language that stakeholders can understand.
"""
        return prompt

    def _parse_story_response(self, response: str, artifact: CodeArtifact) -> Optional[UserStory]:
        """Parse LLM response into UserStory object"""
        try:
            # Simple parsing - look for key patterns
            lines = response.strip().split('\n')

            title = ""
            user_role = ""
            capability = ""
            benefit = ""
            priority = "Medium"
            complexity = 5
            confidence = 0.7
            acceptance_criteria = []

            for line in lines:
                # Normalize markdown decoration (e.g. "**Title:**", "## Title:")
                line = line.strip().lstrip('#').replace('**', '').strip()

                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                elif line.startswith("User Role:"):
                    user_role = line.replace("User Role:", "").strip()
                elif line.startswith("Capability:"):
                    capability = line.replace("Capability:", "").strip()
                elif line.startswith("Benefit:"):
                    benefit = line.replace("Benefit:", "").strip()
                elif line.startswith("Priority:"):
                    priority = line.replace("Priority:", "").strip()
                elif line.startswith("Complexity:"):
                    try:
                        complexity = int(line.replace("Complexity:", "").strip().split()[0])
                    except:
                        complexity = 5
                elif line.startswith("Confidence:"):
                    try:
                        confidence = float(line.replace("Confidence:", "").strip())
                    except:
                        confidence = 0.7
                elif line.startswith(("1.", "2.", "3.", "4.", "5.")):
                    # Acceptance criteria
                    criterion = line[2:].strip()
                    if criterion:
                        acceptance_criteria.append(criterion)

            # Validation
            if not title or not user_role or not capability:
                return None

            return UserStory(
                title=title,
                user_role=user_role,
                capability=capability,
                benefit=benefit,
                acceptance_criteria=acceptance_criteria,
                code_files=[artifact["path"]],
                complexity=complexity,
                priority=priority,
                confidence=confidence
            )

        except Exception as e:
            print(f"  Warning: Failed to parse story response: {e}")
            return None

    def generate_story_for_artifact(self, artifact: CodeArtifact) -> Optional[UserStory]:
        """Generate a user story for a single code artifact"""
        if not self.llm:
            return None

        try:
            # Create prompt
            prompt = self._create_story_prompt(artifact)

            # Call LLM
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Parse response
            story = self._parse_story_response(response_text, artifact)

            return story

        except Exception as e:
            print(f"  Error generating story for {artifact['path']}: {e}")
            return None

    def __call__(self, state: MigrationState) -> MigrationState:
        """
        Execute the user story extraction node.

        Args:
            state: Current workflow state

        Returns:
            Updated state with user stories
        """
        print(f"\n📖 Extracting user stories from code...")

        if not self.llm:
            print("  ⚠️  Skipping user story extraction (no LLM configured)")
            state["phase"] = AnalysisPhase.COMPLETE
            return state

        stories = []
        artifacts_to_analyze = state["code_artifacts"][:5]  # Limit to first 5 for now

        print(f"  Analyzing {len(artifacts_to_analyze)} code files...")

        for i, artifact in enumerate(artifacts_to_analyze):
            print(f"  [{i+1}/{len(artifacts_to_analyze)}] Analyzing {artifact['path']}...")

            story = self.generate_story_for_artifact(artifact)

            if story:
                stories.append(story)
                print(f"    ✓ Generated story: {story.title}")

        # Add stories to state
        state["user_stories"] = [s.to_dict() for s in stories]
        state["phase"] = AnalysisPhase.COMPLETE

        print(f"\n✅ Generated {len(stories)} user stories")

        # Print summary
        if stories:
            print("\n📋 User Stories Generated:")
            for i, story in enumerate(stories, 1):
                print(f"  {i}. {story.title} ({story.priority} priority, {story.complexity} points)")

        return state


# Wrapper function for user story extraction node
def user_story_extraction_node(state):
    """Wrapper function for UserStoryExtractionNode class"""
    node = UserStoryExtractionNode()
    return node(state)

