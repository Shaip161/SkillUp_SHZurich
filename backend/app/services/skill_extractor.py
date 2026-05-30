import asyncio
import json
import logging

from anthropic import AsyncAnthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
_MODEL = "claude-sonnet-4-6"

_SYSTEM_PROMPT = """\
You are a technical skill extractor. Extract structured information from a job posting or CV.

Return ONLY valid JSON — no markdown fences, no explanation:
{
  "title": "cleaned job title in English",
  "description": "cleaned description in English with boilerplate removed",
  "embedding_summary": "max 150 chars in English: for a job — 1 sentence on the core role focus and must-have tech stack; for a CV — 1 sentence on the candidate's domain, top skills, and seniority",
  "skills": {
    "required":     ["skill1", "skill2"],
    "nice_to_have": ["skill3"],
    "soft_skills":  ["skill4"]
  },
  "seniority": "junior | mid | senior | lead | unknown",
  "languages": ["English", "German"]
}

SKILL TYPES — extract ALL of the following when present:
- Programming languages: Python, Go, Java, C++, TypeScript, Rust, SQL, R, Scala
- Frameworks & libraries: React, FastAPI, Django, Spring, Node.js, Next.js, PyTorch, TensorFlow, scikit-learn, Pandas
- Databases: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, Cassandra, DynamoDB, Snowflake, BigQuery
- Cloud platforms: AWS, GCP, Azure — and their specific services (EC2, S3, Lambda, GKE, Cloud Run, Azure Functions)
- DevOps & infrastructure: Docker, Kubernetes, Terraform, Helm, Ansible, CI/CD, GitHub Actions, Jenkins, ArgoCD
- Data & ML tools: Spark, Kafka, Airflow, dbt, MLflow, Weights & Biases, Hugging Face, LangChain
- APIs & protocols: REST, GraphQL, gRPC, WebSockets, MQTT
- Monitoring & observability: Prometheus, Grafana, Datadog, OpenTelemetry, ELK stack
- Security: OAuth2, JWT, SAML, penetration testing, SOC2
- Version control & collaboration: Git, GitHub, GitLab, Jira, Confluence
- Domain-specific: ROS2, MATLAB, AutoCAD, SAP, Salesforce, Bloomberg Terminal, IFRS, Basel III
- Methodologies: Agile, Scrum, TDD, CI/CD, DevSecOps

CLASSIFICATION RULES:
- required: explicitly stated as mandatory ("must have", "required", "essential", 
  "you have", "minimum qualifications", "what you must have")
- nice_to_have: explicitly stated as optional ("preferred", "plus", "bonus", 
  "nice to have", "beneficial", "get some bonus points", "preferred qualifications")
- soft_skills: interpersonal and behavioural only ("Communication", "Leadership", 
  "Problem Solving", "Teamwork") — never mix with technical skills
- When unclear whether required or nice_to_have, default to required

NORMALISATION — always use these canonical forms:
- ReactJS / React.js → React
- NodeJS / Node.JS → Node.js  
- ML → Machine Learning
- JS → JavaScript
- TS → TypeScript
- K8s → Kubernetes
- Postgres / PG → PostgreSQL
- Mongo → MongoDB
- GH Actions → GitHub Actions
- TF → Terraform or TensorFlow (use context)
- LLM APIs → keep specific: "OpenAI API", "Anthropic API"

ADDITIONAL RULES:
- Extract skills from ALL sections: responsibilities, qualifications, 
  nice-to-haves, about the role, and even implicit mentions in the description
- If a responsibility implies a skill ("build REST APIs" → REST, "train ML models" 
  → Machine Learning), extract the skill
- No duplicates across any bucket
- languages = spoken human languages ONLY (English, German, French) — 
  never programming languages
- Strip boilerplate: equal opportunity statements, legal disclaimers, 
  excessive "about us" paragraphs
- seniority must be exactly one of: junior, mid, senior, lead, unknown
- Translate ALL output text fields (title, description, embedding_summary) to English
  regardless of the input language — French, German, Italian, or any other\
"""

async def extract_skills(title: str, description: str) -> dict:
    response = await _client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Title: {title}\n\nDescription:\n{description}",
            }
        ],
    )
    raw = response.content[0].text.strip()
    # Strip accidental markdown fences the model might still emit
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def extract_skills_batch(
    items: list[tuple[str, str]],
    concurrency: int = 5,
) -> list[dict | None]:
    semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(title: str, description: str) -> dict | None:
        async with semaphore:
            try:
                return await extract_skills(title, description)
            except Exception as exc:
                logger.warning("Batch extraction failed for '%s': %s", title, exc)
                return None

    return list(
        await asyncio.gather(*[_guarded(t, d) for t, d in items])
    )
