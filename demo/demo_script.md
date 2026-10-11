# 3-Minute Demo Presentation Script: AI-Based Skill Gap Analyzer

**Team:** VORTEX4 | **Domain:** AI & ML | **Problem Statement:** 44  
**Presenter:** Lead AI/Full-Stack Engineer  
**Duration:** ~3 Minutes  

---

## ⏱️ Timeline Breakdown

| Timestamp | Phase | Demo Screen / Action | Speaker Talking Points |
|---|---|---|---|
| **0:00 - 0:30** | **1. The Problem & Vision** | App Landing Page | Why traditional skill checks fail and why our solution is smarter. |
| **0:30 - 1:00** | **2. Profile Loading & Target Role** | Profile Input & Sidebar | Loading sample profile, picking Data Scientist, weekly hours. |
| **1:00 - 1:35** | **3. Comparison & Deep Matching** | Results: Summary & Matrix Tab | 4-tier classification: Existing, Partial (level), Partial (equivalent), Missing. |
| **1:35 - 2:05** | **4. Priority Scoring & Factual Explanations** | Priority Gaps Tab & Charts | Explainability formula, unlock bonus, why sentence facts. |
| **2:05 - 2:35** | **5. Phased Learning Roadmap** | Roadmap Tab & Resources | Topologically sorted phases, 40% equivalent discount, hours/weeks. |
| **2:35 - 3:00** | **6. Edge Cases & Multi-Role Fit** | Edge Cases Banner & Role Ranking | Equivalent skill banner, ambiguous JD terms, best-fit multi-role comparison. |

---

## 🎙️ Spoken Script

### [0:00 - 0:30] Phase 1: Problem & Vision
> *"Good morning judges and team! Most job applicants face a frustrating reality: automated ATS keyword filters either blindly reject them or dump an unhelpful list of 20 missing tools with zero context. If a candidate knows TensorFlow, traditional systems say they have 0% PyTorch. If they know basic SQL, they're treated identically to someone who has never seen a database.*
> 
> *Today, Team VORTEX4 presents the **AI-Based Skill Gap Analyzer**—an intelligent, explainable, and offline-capable system that goes beyond simple keyword matching. It normalizes terminology, understands transferable equivalencies, weights prerequisites, prioritizes gaps mathematically, and crafts tailored roadmaps."*

---

### [0:30 - 1:00] Phase 2: Profile Input & Target Selection
*(Action: Click the **'Load Sample Profile'** button in the main interface.)*
> *"Let's test this with a realistic profile: a final-year CS student with experience in Python, pandas, numpy, matplotlib, sklearn, coursework SQL, and a TensorFlow image classifier.*
> 
> *Notice that we support free-form resumes, comma-separated skill lists, or PDF/TXT uploads. On the left sidebar, we select our target role—**Data Scientist**—and configure a realistic weekly study budget of **8 hours per week**."*
> 
*(Action: Click the vibrant **'Analyze Skill Gap'** button.)*

---

### [1:00 - 1:35] Phase 3: The 4-Tier Match Engine & Summary
*(Action: Point to the Readiness Score metric, verdict, and the 'Skill Comparison' tab.)*
> *"Instantly, our engine evaluates the profile against the role's required competencies. Look at the **Readiness Score**: 67.5%—verdict **'Almost there'**!*
> 
> *Instead of binary yes/no, our algorithm classifies every competency into one of four distinct tiers:*
> 1. ***EXISTING***: *Python and scikit-learn (correctly normalized from the alias 'sklearn').*
> 2. ***PARTIAL (level)***: *SQL—the user knows basic SQL from coursework, but the role requires intermediate execution.*
> 3. ***PARTIAL (equivalent)***: *Deep Learning—the candidate built a TensorFlow classifier, which transfers 80% of foundational neural network concepts.*
> 4. ***MISSING***: *Statistics—the candidate lacks formal statistical inference.*
> 
> *Notice the **Start Here** guidance: it doesn't overwhelm the student; it highlights the top 3 action items: **Statistics → SQL → Deep Learning**."*

---

### [1:35 - 2:05] Phase 4: Mathematical Prioritization & Factual Explanations
*(Action: Switch to the **'Priority Gaps'** tab and show the Plotly Radar & Bar charts.)*
> *"Why did Statistics rank as HIGH priority while Deep Learning is MEDIUM?*
> 
> *Our prioritization formula doesn't guess:*
> $$\text{Priority} = \text{Importance} \times \text{Gap} \times (1.5 \text{ if mandatory}) + 0.1 \times \text{Unlock Bonus}$$
> 
> *Statistics is mandatory, has a 100% gap, and unlocks downstream machine learning topics. Even more importantly, look at the explanation: every card gives a factual 'why' sentence:
> **'Statistics is HIGH priority: it is mandatory for Data Scientist (importance 0.9), you have no direct or equivalent background in it, and mastering it unlocks downstream areas such as Machine Learning.'***
> 
> *Judges, this total transparency builds immediate trust with the learner."*

---

### [2:05 - 2:35] Phase 5: Phased Learning Roadmap with Transfer Discounts
*(Action: Switch to the **'Learning Roadmap'** tab.)*
> *"Now comes the action plan. We don't just dump links. Our algorithm performs a **topological sort** over the skill prerequisite graph, grouping the learning journey into three logical phases:*
> - *Phase 1: Foundations (Statistics)*
> - *Phase 2: Core Role Skills (SQL level elevation)*
> - *Phase 3: Specialized & Transferred Competencies (Deep Learning)*
> 
> *Crucially: notice the time estimate for Deep Learning. Because the student already knows TensorFlow, our system automatically applies a **40% time discount**, reducing the course commitment from 50 hours down to 30 hours, translating directly into ~3.8 weeks instead of 6 weeks! Each skill links to verified, free, world-class resources from fast.ai, Coursera, Kaggle Learn, and MIT OpenCourseWare."*

---

### [2:35 - 3:00] Phase 6: Edge Cases & Multi-Role Fit
*(Action: Highlight the 'Detected Equivalent Skills' banner, paste an ambiguous JD term like 'cloud knowledge', and show the Multi-Role ranking table.)*
> *"Finally, let's look at real-world edge cases handled seamlessly in the UI:*
> 1. ***Equivalent Skill Synergy Banner:*** *Clearly alerts the user that their TensorFlow knowledge was credited towards Deep Learning.*
> 2. ***Ambiguous Job Requirements:*** *When a JD says 'cloud knowledge', our system detects the ambiguity, unpacks it into AWS, Azure, and GCP, and allows interactive toggle confirmation.*
> 3. ***Multi-Role Comparison:*** *With one click, candidates can benchmark their profile against all 10 roles in the database, revealing that while they are 67.5% ready for Data Scientist, they might be an 85% match for ML Engineer!*
> 
> *The entire system runs completely offline, requires zero paid API keys, passes all pytest suites, and exports downloadable JSON and Markdown audit reports.*
> 
> *Thank you! We're ready for your questions."*
