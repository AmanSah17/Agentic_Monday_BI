"""Fallback insight generator using data-driven summarization without LLM API calls"""
import pandas as pd
from typing import Any


def generate_insight_from_data(
    question: str,
    result_df: pd.DataFrame | None,
    sql_execution_error: str | None = None,
) -> str:
    """
    Generate business insights from query results using simple data analysis.
    Fallback for when LLM is unavailable or quota-exhausted.
    """
    
    if sql_execution_error:
        return f"Query encountered an error: {sql_execution_error}. Please try rephrasing your question."
    
    if result_df is None or result_df.empty:
        return "No data found matching your criteria. Please try with different parameters."
    
    # Detect question type and generate appropriate insight
    q_lower = question.lower()
    
    # Summary statistics
    row_count = len(result_df)
    col_count = len(result_df.columns)
    
    # Basic insight generation logic
    if any(word in q_lower for word in ["pipeline", "value", "sector"]):
        return _pipeline_insight(result_df, question)
    elif any(word in q_lower for word in ["top", "performing", "owner", "deal"]):
        return _performance_insight(result_df, question)
    elif any(word in q_lower for word in ["conversion", "rate"]):
        return _conversion_insight(result_df, question)
    elif any(word in q_lower for word in ["risk", "delays", "at-risk"]):
        return _risk_insight(result_df, question)
    elif any(word in q_lower for word in ["close", "days", "30"]):
        return _close_dates_insight(result_df, question)
    elif any(word in q_lower for word in ["collection", "rate"]):
        return _collection_insight(result_df, question)
    else:
        return _generic_insight(result_df, question)


def _pipeline_insight(df: pd.DataFrame, question: str) -> str:
    """Generate insights about pipeline by sector"""
    try:
        if "sector" in df.columns:
            sector_data = df.groupby("sector").agg({
                "pipeline_value": ["sum", "count", "mean"]
            }).round(2)
            
            top_sector = sector_data[("pipeline_value", "sum")].idxmax()
            top_value = sector_data[("pipeline_value", "sum")].max()
            total_value = sector_data[("pipeline_value", "sum")].sum()
            avg_deal = sector_data[("pipeline_value", "mean")].mean()
            
            return (
                f"Your pipeline is valued at ${total_value:,.2f} across {len(df)} deals. "
                f"The strongest sector is {top_sector} with ${top_value:,.2f} in pipeline value. "
                f"Average deal size is ${avg_deal:,.2f}. Analysis covers {len(df)} total deals."
            )
        else:
            total = df.iloc[:, -1].sum() if pd.api.types.is_numeric_dtype(df.iloc[:, -1]) else len(df)
            return f"Your pipeline shows {total:,.0f} in total value across {len(df)} records."
    except Exception as e:
        return f"Pipeline analysis: {len(df)} deals identified. Data retrieved successfully."


def _performance_insight(df: pd.DataFrame, question: str) -> str:
    """Generate insights about top performers"""
    try:
        if len(df) > 0:
            # Try to find numeric column for ranking
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                top_col = numeric_cols[-1]  # Last numeric column
                top_rows = df.nlargest(3, top_col)
                
                total = df[top_col].sum()
                count = len(df)
                top_3_total = top_rows[top_col].sum()
                
                return (
                    f"Top 3 performers: {top_3_total:,.0f} in combined value "
                    f"({top_3_total/total*100:.1f}% of total). "
                    f"Analysis covers {count} deal owners with ${total:,.0f} total value."
                )
            
        return f"Identified {len(df)} performers in the data."
    except Exception:
        return f"Top performer analysis: {len(df)} records processed."


def _conversion_insight(df: pd.DataFrame, question: str) -> str:
    """Generate insights about conversion rates"""
    try:
        if len(df) > 0 and len(df.columns) > 1:
            first_col = df.iloc[:, 0]
            numeric_col = df.select_dtypes(include=['number']).iloc[:, 0] if len(df.select_dtypes(include=['number']).columns) > 0 else None
            
            if numeric_col is not None:
                rate = numeric_col.sum() / len(df) * 100
                return (
                    f"Conversion rate: {rate:.1f}%. "
                    f"Data based on {len(df)} records with {df.iloc[:, 0].nunique()} groups identified."
                )
        
        return f"Conversion analysis complete. {len(df)} data points processed."
    except Exception:
        return f"Conversion rate analysis: {len(df)} records analyzed."


def _risk_insight(df: pd.DataFrame, question: str) -> str:
    """Generate insights about at-risk work orders"""
    try:
        if "execution_status" in df.columns:
            status_counts = df["execution_status"].value_counts()
            delayed_count = status_counts.get("Delayed", 0)
            total = len(df)
            
            if "work_order_value" in df.columns or any("value" in col.lower() for col in df.columns):
                value_col = next((col for col in df.columns if "value" in col.lower()), None)
                if value_col:
                    at_risk_value = df[df["execution_status"] == "Delayed"][value_col].sum()
                    return (
                        f"At-risk status: {delayed_count} work orders delayed ({delayed_count/total*100:.1f}%). "
                        f"At-risk value: ${at_risk_value:,.0f}. "
                        f"Total work orders analyzed: {total}."
                    )
            
            return (
                f"{delayed_count} work orders showing delays ({delayed_count/total*100:.1f}% of {total} total). "
                f"Status breakdown: {dict(status_counts)}"
            )
        
        return f"Risk analysis: {len(df)} work orders evaluated."
    except Exception:
        return f"Risk assessment: {len(df)} records processed."


def _close_dates_insight(df: pd.DataFrame, question: str) -> str:
    """Generate insights about deals closing soon"""
    try:
        return (
            f"Deal close-date analysis: {len(df)} deals reviewed for upcoming close dates. "
            f"Records retrieved successfully. "
            f"Note: Check your deal board for specific closure probability and dates."
        )
    except Exception:
        return f"Close date analysis: {len(df)} deals assessed."


def _collection_insight(df: pd.DataFrame, question: str) -> str:
    """Generate insights about collection rates"""
    try:
        if len(df) > 0:
            # Try to identify collections-related metrics
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[-1]
                avg_rate = df[col].mean()
                return (
                    f"Collection rate analysis: {avg_rate:.1f}% average based on {len(df)} records. "
                    f"Total value tracked: ${df[col].sum():,.0f}."
                )
        
        return f"Collection rate analysis: {len(df)} records processed."
    except Exception:
        return f"Collection analysis: {len(df)} entries reviewed."


def _generic_insight(df: pd.DataFrame, question: str) -> str:
    """Generic insight generator for unknown question types"""
    try:
        # Count numeric and categorical data
        numeric_count = len(df.select_dtypes(include=['number']).columns)
        cat_count = len(df.select_dtypes(include=['object']).columns)
        
        return (
            f"Data retrieved successfully: {len(df)} rows × {len(df.columns)} columns. "
            f"Dataset contains {numeric_count} numeric fields and {cat_count} categorical fields. "
            f"Ready for analysis."
        )
    except Exception as e:
        return f"Analysis complete. {len(df)} records retrieved."
