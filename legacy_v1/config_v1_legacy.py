import os
from dataclasses import dataclass


@dataclass
class AgentSettings:
    monday_api_token: str | None
    monday_mode: str
    monday_api_url: str
    monday_board_name_hints: list[str]
    monday_mcp_server_url: str
    monday_mcp_tool_list_boards: str
    monday_mcp_tool_get_board_items: str
    langsmith_api_key: str | None
    langsmith_project: str
    langsmith_tracing: bool
    llm_base_url: str
    llm_api_key: str | None
    llm_reasoning_model: str
    llm_sql_model: str
    llm_insight_model: str
    llm_provider: str
    google_api_key: str | None
    qwen_api_key: str | None
    qwen_base_url: str
    zhipuai_api_key: str | None
    zhipuai_base_url: str
    silicon_flow_api_key: str | None
    huggingface_api_key: str | None
    tavily_api_key: str | None
    groq_api_key: str | None
    groq_base_url: str
    llm_reasoning_model_variants: list[str]
    llm_sql_model_variants: list[str]
    llm_insight_model_variants: list[str]
    monday_deals_board_name: str
    monday_work_orders_board_name: str
    monday_deals_board_id: int | None
    monday_work_orders_board_id: int | None

    @classmethod
    def from_env(cls) -> "AgentSettings":
        hints_raw = os.getenv("MONDAY_BOARD_NAME_HINTS", "Deals,Work Orders")
        hints = [x.strip() for x in hints_raw.split(",") if x.strip()]
        sql_variants_raw = os.getenv(
            "LLM_SQL_MODEL_VARIANTS",
            "gemini-2.0-flash,gemini-1.5-flash",
        )
        sql_variants = [x.strip() for x in sql_variants_raw.split(",") if x.strip()]
        reasoning_variants_raw = os.getenv(
            "LLM_REASONING_MODEL_VARIANTS",
            "gemini-2.5-pro,gemini-2.5-flash",
        )
        reasoning_variants = [
            x.strip() for x in reasoning_variants_raw.split(",") if x.strip()
        ]
        insight_variants_raw = os.getenv(
            "LLM_INSIGHT_MODEL_VARIANTS",
            "llama-3.1-70b-versatile,llama-3.1-8b-instant",
        )
        insight_variants = [x.strip() for x in insight_variants_raw.split(",") if x.strip()]
        
        provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        if not provider:
            provider = "huggingface" if os.getenv("HUGGINGFACE_API_KEY") else ("groq" if os.getenv("GROQ_API_KEY") else "gemini")

        return cls(
            monday_api_token=os.getenv("MONDAY_API_TOKEN") or os.getenv("MONDAY_COM_API_KEY"),
            monday_mode=os.getenv("MONDAY_MODE", "graphql").strip().lower(),
            monday_api_url=os.getenv("MONDAY_API_URL", "https://api.monday.com/v2"),
            monday_board_name_hints=hints,
            monday_mcp_server_url=os.getenv(
                "MONDAY_MCP_SERVER_URL", "https://mcp.monday.com/mcp"
            ),
            monday_mcp_tool_list_boards=os.getenv(
                "MONDAY_MCP_TOOL_LIST_BOARDS", "list_boards"
            ),
            monday_mcp_tool_get_board_items=os.getenv(
                "MONDAY_MCP_TOOL_GET_BOARD_ITEMS", "get_board_items"
            ),
            langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "founder_bi_agent"),
            langsmith_tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
            llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_reasoning_model=os.getenv(
                "LLM_REASONING_MODEL", "llama-3.3-70b-versatile"
            ),
            llm_sql_model=os.getenv("LLM_SQL_MODEL", "qwen-2.5-coder-32b"),
            llm_insight_model=os.getenv("LLM_INSIGHT_MODEL", "llama-3.1-70b-versatile"),
            llm_provider=provider,
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            silicon_flow_api_key=os.getenv("SILICON_FLOW_API_KEY"),
            qwen_api_key=os.getenv("QWEN_API_KEY") or os.getenv("SILICON_FLOW_API_KEY"),
            qwen_base_url=os.getenv("QWEN_BASE_URL", "https://api.siliconflow.cn/v1" if os.getenv("SILICON_FLOW_API_KEY") and not os.getenv("QWEN_API_KEY") else "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            zhipuai_api_key=os.getenv("ZHIPUAI_API_KEY") or os.getenv("SILICON_FLOW_API_KEY"),
            zhipuai_base_url=os.getenv("ZHIPUAI_BASE_URL", "https://api.siliconflow.cn/v1" if os.getenv("SILICON_FLOW_API_KEY") and not os.getenv("ZHIPUAI_API_KEY") else "https://open.bigmodel.cn/api/paas/v4/"),
            huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            llm_reasoning_model_variants=reasoning_variants,
            llm_sql_model_variants=sql_variants,
            llm_insight_model_variants=insight_variants,
            monday_deals_board_name=os.getenv("MONDAY_DEALS_BOARD_NAME", "Deal funnel Data"),
            monday_work_orders_board_name=os.getenv(
                "MONDAY_WORK_ORDERS_BOARD_NAME", "Work_Order_Tracker Data"
            ),
            monday_deals_board_id=(
                int(os.getenv("MONDAY_DEALS_BOARD_ID"))
                if os.getenv("MONDAY_DEALS_BOARD_ID")
                else None
            ),
            monday_work_orders_board_id=(
                int(os.getenv("MONDAY_WORK_ORDERS_BOARD_ID"))
                if os.getenv("MONDAY_WORK_ORDERS_BOARD_ID")
                else None
            ),
        )
