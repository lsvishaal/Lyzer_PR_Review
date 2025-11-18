"""Streamlit UI for GitHub PR Review Agent."""

import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
REQUEST_TIMEOUT = 120.0


def init_page_config():
    st.set_page_config(
        page_title="PR Review Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_custom_css():
    st.markdown(
        """
        <style>
        .stButton > button {
            background-color: #dc3545;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-size: 1.1rem;
        }
        .critical-issue {
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .warning-issue {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def check_api_health():
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


def review_pr_github(repo, pr_id):
    try:
        response = httpx.post(
            f"{API_BASE_URL}/review/pr",
            json={"repo": repo, "pr_id": pr_id},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.json().get('detail')}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def review_manual_diff(diff):
    try:
        response = httpx.post(
            f"{API_BASE_URL}/review/pr",
            json={"diff": diff},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.json().get('detail')}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def display_comments(comments):
    if not comments:
        st.success("✅ No issues found!")
        return

    critical = [c for c in comments if c.get("severity") == "critical"]
    warning = [c for c in comments if c.get("severity") == "warning"]

    if critical:
        st.markdown("### 🔴 Critical Issues")
        for c in critical:
            st.markdown(
                f"""
                <div class="critical-issue">
                <strong>{c['file_path']}:{c['line_number']}</strong><br>
                {c['message']}<br>
                <em>{c.get('suggestion', '')}</em>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if warning:
        st.markdown("### 🟡 Warnings")
        for c in warning:
            st.markdown(
                f"""
                <div class="warning-issue">
                <strong>{c['file_path']}:{c['line_number']}</strong><br>
                {c['message']}<br>
                <em>{c.get('suggestion', '')}</em>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main():
    init_page_config()
    apply_custom_css()

    st.title("🤖 GitHub PR Review Agent")
    st.markdown("**Automated code review powered by multi-agent LLM system**")

    with st.sidebar:
        st.header("⚙️ System Status")
        if check_api_health():
            st.success("✅ API: Healthy")
        else:
            st.error("❌ API: Unreachable")

    tab1, tab2 = st.tabs(["📦 GitHub PR", "📝 Manual Diff"])

    with tab1:
        st.markdown("### Review a Pull Request from GitHub")
        col1, col2 = st.columns([3, 1])

        with col1:
            repo = st.text_input(
                "Repository (owner/name)", placeholder="octocat/Hello-World"
            )
        with col2:
            pr_id = st.number_input("PR Number", min_value=1, value=1)

        if st.button("🔍 Review PR", key="review_github"):
            if repo and "/" in repo:
                with st.spinner("Analyzing..."):
                    result = review_pr_github(repo, pr_id)
                    if result:
                        st.success("✅ Review completed!")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Issues", result.get("total_issues", 0))
                        col2.metric("Critical", result.get("critical_count", 0))
                        col3.metric("Warnings", result.get("warning_count", 0))
                        st.markdown("---")
                        display_comments(result.get("comments", []))
            else:
                st.error("Please enter valid repo format: owner/repo")

    with tab2:
        st.markdown("### Review a Manual Diff")
        diff_input = st.text_area(
            "Diff Content", height=300, placeholder="Paste git diff here..."
        )

        if st.button("🔍 Review Diff", key="review_diff"):
            if diff_input.strip():
                with st.spinner("Analyzing..."):
                    result = review_manual_diff(diff_input)
                    if result:
                        st.success("✅ Review completed!")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Issues", result.get("total_issues", 0))
                        col2.metric("Critical", result.get("critical_count", 0))
                        col3.metric("Warnings", result.get("warning_count", 0))
                        st.markdown("---")
                        display_comments(result.get("comments", []))
            else:
                st.error("Please provide a diff to review")


if __name__ == "__main__":
    main()
