# chatbot_utils.py

import os
import pandas as pd
import re
from datetime import datetime
from dateparser import parse as parse_date
from typing import Optional, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# --- LLM Setup ---
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    # temperature=0.5
)

# --- Load prompt examples ---
with open("few_shot_prompt.txt", "r", encoding="utf-8") as f:
    examples = f.read()

# --- Schemas ---
class AppState(BaseModel):
    question: str
    code: Optional[str] = None
    result: Optional[Any] = None
    answer: Optional[str] = None


# --- Prompt Builder ---
def build_prompt(question: str, df: pd.DataFrame) -> str:
    schema = df.dtypes.to_string()
    head = df.head(2).to_string(index=False)

    return f"""
You are a pandas expert. You are given a DataFrame named `df` which tracks student attendance.
Each row is a student with a roll number, name, and dates (YYYY-MM-DD) as columns.
'P' means present; '' (empty string) means absent.

DataFrame schema:
{schema}

Sample data:
{head}

Your task is to write one line of Python code using pandas to answer the following question:

{examples}

Question: {question}

Rules:
- Only use pandas methods, not print statements.
- Use df as the DataFrame name.
- Do NOT modify df.
- Only return the line of code (nothing else).
"""


# --- Date Normalization ---
def normalize_dates_in_question(inputs: dict, df) -> dict:
    question = inputs["question"]

    possible_phrases = re.findall(
        r"\b(?:today|yesterday|tomorrow|\d+\s+days?\s+(?:ago|before|after)|next\s+\w+|on\s+\w+day|\d{4}-\d{2}-\d{2})\b",
        question,
        re.IGNORECASE,
    )
    normalized_dates = []

    for phrase in possible_phrases:
        resolved = parse_date(phrase)
        if resolved:
            formatted = resolved.strftime("%Y-%m-%d")
            if resolved > datetime.today():
                return {"error": f"⚠️ Attendance can't be checked for a future date: {formatted}"}
            if formatted not in df.columns:
                latest = max(df.columns[-10:], key=lambda x: x)
                return {"error": f"⚠️ Date '{formatted}' not found in records. Latest date is: {latest}"}
            question = question.replace(phrase, formatted)
            normalized_dates.append(formatted)

    return {"question": question}


# --- Nodes ---
def normalize_node(state: AppState, df) -> AppState:
    out = normalize_dates_in_question({"question": state.question}, df)
    if "error" in out:
        return AppState(question=state.question, result=out["error"], answer=out["error"])
    return AppState(question=out["question"])

def generate_code_node(state: AppState, df: pd.DataFrame) -> AppState:
    prompt = build_prompt(state.question, df)
    response = gemini_llm.invoke(prompt)
    return AppState(question=state.question, code=response.content.strip())

def execute_code_node(state: AppState, df: pd.DataFrame) -> AppState:
    try:
        result = eval(state.code, {"df": df.copy()})
        return AppState(question=state.question, code=state.code, result=result)
    except Exception as e:
        return AppState(question=state.question, code=state.code, result=f"ERROR: {str(e)}")

def format_response(state: AppState) -> AppState:
    question = state.question
    result = state.result

    # Generate new answer string
    if isinstance(result, str) and (result.startswith("ERROR") or result.startswith("⚠️")):
        new_answer = f"❌ Failed to answer: {result}"
    elif isinstance(result, (int, float, str, bool)) or hasattr(result, "__str__"):
        new_answer = f"📊 Answer to: '{question}' is → {result}"
    else:
        new_answer = f"✅ Answer to your question: '{question}'\n\n{result}"

    # Create new state with updated answer (override old answer)
    state_dict = state.model_dump()
    state_dict["answer"] = new_answer
    return AppState(**state_dict)


# --- Entry Point ---
def get_agent_for_df(df: pd.DataFrame):
    def norm(state): return normalize_node(state, df)
    def codegen(state): return generate_code_node(state, df)
    def execute(state): return execute_code_node(state, df)
    def respond(state): return format_response(state)

    graph = StateGraph(AppState)
    graph.add_node("normalize", norm)
    graph.add_node("generate_code", codegen)
    graph.add_node("execute", execute)
    graph.add_node("respond", respond)

    graph.set_entry_point("normalize")
    graph.add_edge("normalize", "generate_code")
    graph.add_edge("generate_code", "execute")
    graph.add_edge("execute", "respond")
    graph.set_finish_point("respond")

    return graph.compile()
