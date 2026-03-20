from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from founder_bi_agent.backend.service import run_founder_query


def render_chart(result_df: pd.DataFrame, chart_spec: dict) -> None:
    if result_df.empty or not chart_spec:
        return
    if chart_spec.get("kind") == "bar":
        x = chart_spec.get("x")
        y = chart_spec.get("y")
        if x in result_df.columns and y in result_df.columns:
            fig = px.bar(result_df, x=x, y=y, title=chart_spec.get("title", "Chart"))
            st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Monday Founder BI Agent", layout="wide")
    st.title("Monday.com Founder BI Agent")
    st.caption(
        "Strict scope: only Deal funnel Data + Work_Order_Tracker Data. "
        "Every query performs live API calls."
    )

    if "history" not in st.session_state:
        st.session_state.history = []

    question = st.chat_input("Ask a founder-level BI question")
    if not question:
        return

    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.status("Running live monday.com analysis...", expanded=True) as status:
        response = run_founder_query(question, st.session_state.history)
        status.update(label="Analysis complete", state="complete")

    with st.chat_message("assistant"):
        if response.get("needs_clarification"):
            st.write(response.get("clarification_question"))
            return

        st.write(response.get("answer"))
        sql_query = response.get("sql_query")
        if sql_query:
            st.code(sql_query, language="sql")

        result_df = pd.DataFrame(response.get("result_records", []))
        if not result_df.empty:
            st.dataframe(result_df, use_container_width=True)
            render_chart(result_df, response.get("chart_spec", {}))

        st.subheader("Data Quality Caveats")
        st.json(response.get("quality_report", {}))

        st.subheader("Resolved Boards")
        st.json(response.get("board_map", {}))

        st.subheader("Tool/API Trace")
        traces = response.get("traces", [])
        if not traces:
            st.info("No trace entries.")
        else:
            for idx, trace in enumerate(traces, start=1):
                with st.expander(f"{idx}. {trace.get('node')}"):
                    st.json(trace)

    st.session_state.history.append(
        {"role": "assistant", "content": response.get("answer", "")}
    )


if __name__ == "__main__":
    main()
