import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.pipeline import SkillGapPipeline

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Skill Gap Analyzer | AI Career Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #64748B;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    .metric-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1E293B;
    }
    
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Badges */
    .badge-ready { background-color: #DCFCE7; color: #166534; padding: 4px 12px; border-radius: 9999px; font-weight: 700; }
    .badge-almost { background-color: #FEF9C3; color: #854D0E; padding: 4px 12px; border-radius: 9999px; font-weight: 700; }
    .badge-needs { background-color: #FEE2E2; color: #991B1B; padding: 4px 12px; border-radius: 9999px; font-weight: 700; }
    
    .badge-high { background-color: #FEE2E2; color: #DC2626; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }
    .badge-med { background-color: #FEF3C7; color: #D97706; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }
    .badge-low { background-color: #E0E7FF; color: #4338CA; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }
    
    .badge-existing { background-color: #D1FAE5; color: #065F46; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem; }
    .badge-partial { background-color: #DBEAFE; color: #1E40AF; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem; }
    .badge-missing { background-color: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem; }

    /* Gap Card */
    .gap-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .gap-card-high { border-left-color: #EF4444; }
    .gap-card-med { border-left-color: #F59E0B; }
    .gap-card-low { border-left-color: #6366F1; }
    
    /* Course Card */
    .course-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Pipeline Initialization (Cached)
# ---------------------------------------------------------
@st.cache_resource(show_spinner="Initializing AI Skill Gap Pipeline...")
def load_pipeline():
    return SkillGapPipeline()

pipeline = load_pipeline()

# Sample Profile Preset
SAMPLE_PROFILE_TEXT = (
    "Final-year CS student. Built projects in Python using pandas, numpy, matplotlib and sklearn. "
    "Know basic SQL from coursework. Completed a TensorFlow image classifier. "
    "Familiar with Git and Streamlit."
)

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎯 Target Goal")
    roles_list = list(pipeline.roles.keys())
    default_role_idx = roles_list.index("Data Scientist") if "Data Scientist" in roles_list else 0
    selected_role = st.selectbox(
        "Select Target Role",
        options=roles_list,
        index=default_role_idx,
        help="Choose a pre-configured role from our verified industry taxonomy."
    )
    
    st.markdown("---")
    st.markdown("### 📝 Or Custom Job Description")
    custom_jd_input = st.text_area(
        "Paste Job Description (JD)",
        height=140,
        placeholder="Paste JD text with requirements (e.g. 'Must have 3+ years in Python, SQL, AWS, and strong communication...')"
    )
    
    st.markdown("---")
    st.markdown("### ⏱️ Learning Budget")
    weekly_hours = st.slider(
        "Weekly Study Commitment (Hours)",
        min_value=2,
        max_value=40,
        value=8,
        step=1,
        help="Used to calculate realistic completion timelines in your personalized roadmap."
    )
    
    st.markdown("---")
    st.markdown("<small style='color: #64748B;'>⚡ Team VORTEX4 | Problem Statement 44<br>Fully offline capable • 0 API keys required</small>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Main UI Header
# ---------------------------------------------------------
st.markdown("<h1 class='main-title'>AI-Based Skill Gap Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Context-aware competency evaluation, transferable skill equivalence, mathematical prioritization, and explainable learning roadmaps.</p>", unsafe_allow_html=True)

# Profile Input Area
col_in1, col_in2 = st.columns([3, 1])
with col_in2:
    st.write("")
    st.write("")
    if st.button("📋 Load Sample Profile", use_container_width=True):
        st.session_state["profile_text_input"] = SAMPLE_PROFILE_TEXT
    
    uploaded_file = st.file_uploader(
        "Upload Resume / Profile (.txt, .pdf)",
        type=["txt", "pdf"],
        help="Supports raw text files and formatted PDF resumes."
    )

if "profile_text_input" not in st.session_state:
    st.session_state["profile_text_input"] = SAMPLE_PROFILE_TEXT

# Read uploaded file if provided
if uploaded_file is not None:
    extracted_text = pipeline.extractor.extract_from_file(uploaded_file.read(), uploaded_file.name)
    if extracted_text:
        st.session_state["profile_text_input"] = extracted_text
        st.success(f"Successfully extracted text from {uploaded_file.name}!")

with col_in1:
    profile_text = st.text_area(
        "Candidate Profile (Free-text resume summary, project history, or comma-separated skills):",
        value=st.session_state.get("profile_text_input", ""),
        height=140
    )

# Interactive Ambiguity Edge Case Check
ambiguous_detected = pipeline.edge_cases.detect_ambiguous_terms(
    custom_jd_input if custom_jd_input.strip() else profile_text
)

confirmed_skills = []
if ambiguous_detected:
    with st.expander("🔍 Ambiguous Requirements Detected in Context - Confirm Interpretations", expanded=True):
        st.info("The text contains general phrases. Select how you'd like the analyzer to interpret them:")
        for phrase, candidates in ambiguous_detected.items():
            st.markdown(f"**Ambiguous Phrase:** *\"{phrase}\"*")
            cols = st.columns(len(candidates))
            for i, cand in enumerate(candidates):
                with cols[i]:
                    if st.checkbox(f"Include {cand}", value=True, key=f"amb_{phrase}_{cand}"):
                        confirmed_skills.append(cand)

# Run Analysis Button
analyze_clicked = st.button("🚀 Analyze Skill Gap & Generate Roadmap", type="primary", use_container_width=True)

if analyze_clicked or "last_analysis" in st.session_state:
    if analyze_clicked:
        with st.spinner("Analyzing profile against role requirements..."):
            res = pipeline.analyze(
                profile_text=profile_text,
                role_name=selected_role,
                custom_jd_text=custom_jd_input if custom_jd_input.strip() else None,
                weekly_hours=weekly_hours,
                confirmed_ambiguous_skills=confirmed_skills if ambiguous_detected else None
            )
            st.session_state["last_analysis"] = res
    else:
        res = st.session_state["last_analysis"]

    if not res.get("success"):
        st.error(f"⚠️ {res.get('error')}")
    else:
        stats = res["summary_stats"]
        readiness = res["readiness"]
        matches = res["matches"]
        roadmap = res["roadmap"]
        equivalents = res["equivalents"]

        # -----------------------------------------------------
        # Edge Case 1: Equivalent Experience Banner
        # -----------------------------------------------------
        if equivalents:
            for eq in equivalents:
                st.success(
                    f"💡 **Detected Equivalent Competency:** You possess experience in **{eq['user_skill']}**, "
                    f"which satisfies **{int(eq['overlap']*100)}%** of the concepts required for **{eq['target_skill']}**. "
                    f"Your roadmap applies a targeted **40% study time discount**!"
                )

        # -----------------------------------------------------
        # Edge Case 5: Unrecognized Tokens Suggestion
        # -----------------------------------------------------
        if res.get("unrecognized_tokens"):
            with st.expander("❓ Unrecognized or Typo Skill Suggestions"):
                for u in res["unrecognized_tokens"]:
                    st.write(f"- \"`{u['token']}`\" didn't match directly. Did you mean **{u['suggestion']}**? ({u['similarity']}% similarity)")

        st.markdown("---")

        # -----------------------------------------------------
        # KPI Metric Dashboard
        # -----------------------------------------------------
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            v_class = "badge-ready" if readiness["verdict"] == "Ready" else ("badge-almost" if readiness["verdict"] == "Almost there" else "badge-needs")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{readiness['readiness_score']}%</div>
                <div class="metric-label">Readiness Score</div>
                <div style="margin-top: 6px;"><span class="{v_class}">{readiness['verdict']}</span></div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #059669;">{stats['existing']}</div>
                <div class="metric-label">Existing Skills</div>
                <div style="margin-top: 6px; font-size: 0.8rem; color: #059669;">Fully Validated</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #2563EB;">{stats['partial']}</div>
                <div class="metric-label">Partial Skills</div>
                <div style="margin-top: 6px; font-size: 0.8rem; color: #2563EB;">Level or Equivalent</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #DC2626;">{stats['missing']}</div>
                <div class="metric-label">Missing Skills</div>
                <div style="margin-top: 6px; font-size: 0.8rem; color: #DC2626;">Action Required</div>
            </div>
            """, unsafe_allow_html=True)
        with k5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number" style="color: #7C3AED;">{roadmap['total_weeks']}w</div>
                <div class="metric-label">Roadmap Duration</div>
                <div style="margin-top: 6px; font-size: 0.8rem; color: #7C3AED;">{roadmap['total_hours']}h @ {weekly_hours}h/wk</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -----------------------------------------------------
        # Tabbed Navigation
        # -----------------------------------------------------
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 Executive Summary",
            "🔍 Skill Comparison Matrix",
            "🎯 Priority Gaps & Why",
            "🗺️ Phased Learning Roadmap",
            "📊 Analytics & Radar Charts",
            "🏆 Multi-Role Benchmarking"
        ])

        # -----------------------------------------------------
        # TAB 1: Summary
        # -----------------------------------------------------
        with tab1:
            st.markdown(f"### Evaluation for: **{res['role_name']}**")
            
            # Start Here top 3 banner
            if readiness.get("start_here"):
                st.markdown("#### 🎯 Recommended 'Start Here' Action Plan (Top 3 Priority Gaps):")
                sh_cols = st.columns(len(readiness["start_here"]))
                for idx, skill_name in enumerate(readiness["start_here"]):
                    with sh_cols[idx]:
                        st.info(f"**Step {idx+1}: {skill_name}**\n\nHigh impact foundational target to unblock next phase.")

            st.markdown("---")
            st.markdown("#### 📖 Candidate Recognized Skills")
            user_s_list = list(res["user_skills"].values())
            if user_s_list:
                user_pills = [f"**{u['name']}** ({u['level']})" for u in user_s_list]
                st.write(" • ".join(user_pills))
            else:
                st.write("No recognized skills in candidate profile.")

        # -----------------------------------------------------
        # TAB 2: Skill Comparison Table
        # -----------------------------------------------------
        with tab2:
            st.markdown("### Required Competencies vs Candidate Level")
            
            table_data = []
            for m in matches:
                stat_badge = m["status"]
                table_data.append({
                    "Skill": m["name"],
                    "Required Level": m["required_level"].capitalize(),
                    "Your Level": m["user_level"].capitalize(),
                    "Status": stat_badge,
                    "Match %": f"{int(m['match_score']*100)}%",
                    "Priority": m.get("priority_bucket", "LOW"),
                    "Mandatory": "Yes ⚠️" if m.get("mandatory") else "No"
                })
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

        # -----------------------------------------------------
        # TAB 3: Priority Gaps & Explanations
        # -----------------------------------------------------
        with tab3:
            st.markdown("### Prioritized Improvement Areas with Factual Explanations")
            st.markdown("<small style='color: #64748B;'>Priority formula incorporates importance, gap distance, mandatory weighting (1.5x), and downstream prerequisite unlock bonus.</small>", unsafe_allow_html=True)
            
            gap_items = [m for m in matches if m.get("gap", 0) > 0]
            if not gap_items:
                st.success("🎉 Outstanding! You possess all required competencies for this target role!")
            else:
                for item in gap_items:
                    bucket = item.get("priority_bucket", "LOW")
                    card_class = "gap-card-high" if bucket == "HIGH" else ("gap-card-med" if bucket == "MEDIUM" else "gap-card-low")
                    badge_class = "badge-high" if bucket == "HIGH" else ("badge-med" if bucket == "MEDIUM" else "badge-low")
                    
                    st.markdown(f"""
                    <div class="gap-card {card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #1E293B;">{item['name']}</h4>
                            <div>
                                <span class="{badge_class}">{bucket} PRIORITY</span>
                                <span style="margin-left: 8px; font-weight: 600; font-size: 0.85rem; color: #64748B;">Score: {item.get('priority_score', 0)}</span>
                            </div>
                        </div>
                        <p style="margin: 0.6rem 0; color: #334155; font-size: 0.95rem; line-height: 1.5;">
                            <b>Why:</b> {item.get('explanation')}
                        </p>
                        <div style="font-size: 0.8rem; color: #64748B;">
                            Status: <b>{item['status']}</b> | Match: <b>{int(item['match_score']*100)}%</b> | Importance: <b>{item.get('importance')}</b> | Mandatory: <b>{item.get('mandatory')}</b> | Unlock Bonus: <b>{item.get('unlock_bonus')}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # -----------------------------------------------------
        # TAB 4: Phased Learning Roadmap
        # -----------------------------------------------------
        with tab4:
            st.markdown("### 🗺️ Topologically Ordered Learning Plan")
            st.markdown(
                f"**Total Learning Commitment:** {roadmap['total_hours']} hours "
                f"(~{roadmap['total_weeks']} weeks at {weekly_hours} hours/week)."
            )

            if not roadmap["phases"]:
                st.info("No gaps to learn!")
            else:
                for phase in roadmap["phases"]:
                    with st.expander(f"📌 {phase['phase_title']}  —  {phase['phase_weeks']} Weeks ({phase['phase_hours']} Hours)", expanded=True):
                        st.markdown(f"*{phase['description']}*")
                        
                        for item in phase["items"]:
                            st.markdown(f"#### 🔹 {item['name']}")
                            st.markdown(f"<span style='color: #2563EB; font-weight: 600;'>{item['discount_note']}</span> — Est. {item['effective_hours']} hrs (~{item['estimated_weeks']} weeks)", unsafe_allow_html=True)
                            
                            c_cols = st.columns(len(item.get("courses", [])[:3]))
                            for c_idx, c in enumerate(item.get("courses", [])[:3]):
                                with c_cols[c_idx]:
                                    st.markdown(f"""
                                    <div class="course-card">
                                        <b>{c['title']}</b><br>
                                        <small style="color: #64748B;">{c['provider']} • {c['type']} • {c['est_hours']}h ({c['level']})</small><br>
                                        <a href="{c['url']}" target="_blank" style="color: #2563EB; font-size: 0.85rem; text-decoration: none; font-weight: 600;">Open Free Resource ↗</a>
                                    </div>
                                    """, unsafe_allow_html=True)

        # -----------------------------------------------------
        # TAB 5: Analytics & Plotly Charts
        # -----------------------------------------------------
        with tab5:
            st.markdown("### 📊 Skill Distribution & Priority Visualizations")
            c_chart1, c_chart2 = st.columns(2)

            with c_chart1:
                # Plotly Radar Chart: Required vs Candidate by Category
                categories = []
                req_scores = []
                user_scores = []

                # Aggregate by category
                cat_data = {}
                for m in matches:
                    cat = m.get("category", "General")
                    if cat not in cat_data:
                        cat_data[cat] = {"req": [], "user": []}
                    cat_data[cat]["req"].append(1.0)
                    cat_data[cat]["user"].append(m["match_score"])

                for cat, val in cat_data.items():
                    categories.append(cat)
                    req_scores.append(1.0)
                    user_scores.append(sum(val["user"]) / max(1, len(val["user"])))

                # Close loop for radar
                if categories:
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=req_scores + [req_scores[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name='Role Benchmark',
                        line=dict(color='#94A3B8')
                    ))
                    fig_radar.add_trace(go.Scatterpolar(
                        r=user_scores + [user_scores[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        name='Candidate Level',
                        line=dict(color='#2563EB')
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        showlegend=True,
                        title="Category Mastery Radar",
                        margin=dict(l=40, r=40, t=50, b=40)
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)

            with c_chart2:
                # Priority Bar Chart
                bar_data = [
                    {"Skill": m["name"], "Priority": m.get("priority_score", 0), "Bucket": m.get("priority_bucket", "LOW")}
                    for m in matches if m.get("gap", 0) > 0
                ]
                if bar_data:
                    df_bar = pd.DataFrame(bar_data).sort_values("Priority", ascending=True)
                    fig_bar = px.bar(
                        df_bar,
                        x="Priority",
                        y="Skill",
                        orientation="h",
                        color="Bucket",
                        color_discrete_map={"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#6366F1"},
                        title="Skill Gap Priority Scores"
                    )
                    fig_bar.update_layout(margin=dict(l=40, r=40, t=50, b=40))
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.write("No priority gaps to display.")

        # -----------------------------------------------------
        # TAB 6: Multi-Role Benchmarking (Stretch Goal)
        # -----------------------------------------------------
        with tab6:
            st.markdown("### 🏆 Profile Fit Across All Industry Roles")
            st.write("Discover which other careers your existing skill profile is best positioned for:")
            
            multi_role_data = pipeline.compare_multiple_roles(profile_text)
            df_multi = pd.DataFrame(multi_role_data)
            df_multi.rename(columns={
                "role_name": "Target Role",
                "readiness_score": "Readiness %",
                "verdict": "Fit Verdict",
                "existing": "Existing",
                "partial": "Partial",
                "missing": "Missing",
                "total_required": "Total Skills"
            }, inplace=True)
            st.dataframe(df_multi, use_container_width=True, hide_index=True)

        # -----------------------------------------------------
        # Download Section
        # -----------------------------------------------------
        st.markdown("---")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            json_report = json.dumps(res, indent=2)
            st.download_button(
                "📥 Download Full JSON Report",
                data=json_report,
                file_name=f"skill_gap_{res['role_name'].replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True
            )
        with d_col2:
            md_report = pipeline.generate_markdown_report(res)
            st.download_button(
                "📥 Download Markdown Report",
                data=md_report,
                file_name=f"skill_gap_{res['role_name'].replace(' ', '_').lower()}.md",
                mime="text/markdown",
                use_container_width=True
            )
