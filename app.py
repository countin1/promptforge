"""
PromptForge Web UI

Streamlit 界面：不用写代码就能搜索最优 prompt 模板。
"""

import streamlit as st
import json
import os

st.set_page_config(
    page_title="PromptForge — Prompt 自动优化",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 PromptForge — Prompt 自动优化")
st.caption("给定评测集，自动找到最优 prompt 结构")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")

    # API 配置
    st.subheader("🔑 API 设置")
    api_key = st.text_input("API Key", type="password", help="输入你的 API Key")
    base_url = st.text_input("Base URL", value="https://token-plan-cn.xiaomimimo.com/v1")
    model_name = st.text_input("模型名称", value="mimo-v2.5-pro")

    st.markdown("---")

    # 搜索配置
    st.subheader("🔍 搜索设置")
    method = st.selectbox("搜索方法", ["grid", "bayesian", "genetic"],
                          help="网格搜索最全，贝叶斯最快，遗传算法适合大搜索空间")

    if method == "bayesian":
        iterations = st.slider("迭代次数", 5, 50, 20)
    elif method == "genetic":
        generations = st.slider("代数", 5, 30, 10)

    max_questions = st.slider("最大题目数", 5, 100, 10, help="限制题目数以加快搜索")

    st.markdown("---")
    st.caption("💡 搜索需要调用 API，会消耗 token")

# 主界面
tab1, tab2, tab3 = st.tabs(["🚀 开始搜索", "📊 查看结果", "❓ 使用说明"])

with tab1:
    st.subheader("搜索最优 Prompt 模板")

    # 检查数据文件
    data_path = "data/questions.json"
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
        st.info(f"📋 已加载 {len(questions)} 道评测题目")
    else:
        st.warning("⚠️ 未找到 data/questions.json，请先准备评测数据")
        st.stop()

    # 搜索按钮
    if st.button("🚀 开始搜索", type="primary", use_container_width=True):
        if not api_key:
            st.error("请在侧边栏填写 API Key")
            st.stop()

        # 设置环境变量
        os.environ["ANTHROPIC_AUTH_TOKEN"] = api_key

        from promptforge.api.client import ModelClient
        from promptforge.search.grid import GridSearch
        from promptforge.search.bayesian import BayesianSearch
        from promptforge.search.genetic import GeneticSearch

        client = ModelClient(api_key=api_key, base_url=base_url, model=model_name)

        with st.spinner(f"正在用 {method} 方法搜索..."):
            try:
                if method == "grid":
                    searcher = GridSearch()
                    result = searcher.search(questions, client, max_questions=max_questions)
                elif method == "bayesian":
                    searcher = BayesianSearch()
                    result = searcher.search(questions, client,
                                             n_iterations=iterations,
                                             max_questions=max_questions)
                elif method == "genetic":
                    searcher = GeneticSearch()
                    result = searcher.search(questions, client,
                                             generations=generations,
                                             max_questions=max_questions)

                st.session_state["result"] = result
                st.success("搜索完成！")

            except Exception as e:
                st.error(f"搜索失败: {e}")
                st.stop()

        # 显示结果
        st.text(result.summary())

with tab2:
    st.subheader("搜索结果")

    if "result" in st.session_state:
        result = st.session_state["result"]
        st.text(result.summary())

        # 如果有详细结果，显示对比表
        if hasattr(result, "comparisons") and result.comparisons:
            st.subheader("模板对比")
            import pandas as pd
            df = pd.DataFrame(result.comparisons)
            st.dataframe(df, use_container_width=True)
    else:
        st.info("请先在「开始搜索」标签页运行搜索")

with tab3:
    st.subheader("使用说明")

    st.markdown("""
    ### 什么是 PromptForge？

    PromptForge 是一个 Prompt 自动优化框架，类似 DSPy。
    给定一组评测题目，它会自动搜索最优的 prompt 模板结构。

    ### 搜索方法

    | 方法 | 优点 | 缺点 | 适用场景 |
    |------|------|------|----------|
    | 网格搜索 | 全局最优、可复现 | 组合爆炸、API 调用多 | 搜索空间小（<50） |
    | 贝叶斯优化 | 高效、智能选择 | 需要实现 GP | 搜索空间大 |
    | 遗传算法 | 简单、并行友好 | 不保证全局最优 | 超大搜索空间 |

    ### 搜索维度

    PromptForge 从 4 个维度组合 prompt：
    1. **角色**：无角色、教授、数据分析师
    2. **格式**：无要求、结构化、JSON
    3. **推理**：无、CoT、逐步思考
    4. **Few-shot**：无、1 个示例、2 个示例

    ### 输出

    搜索完成后会得到：
    - 最优模板组合
    - 平均得分
    - 各模板对比表
    - 统计检验结果（配对 t 检验 + Cohen's d）
    """)
