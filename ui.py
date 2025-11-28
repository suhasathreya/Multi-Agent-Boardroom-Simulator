import streamlit as st
from boardroom_debate import run_debate

st.set_page_config(page_title="Boardroom Simulator", layout="wide")

# ---------------------------------------------
# STREAMLIT STATE
# ---------------------------------------------
if "state" not in st.session_state:
    st.session_state.state = "input"
if "debate_data" not in st.session_state:
    st.session_state.debate_data = None
if "pm_index" not in st.session_state:
    st.session_state.pm_index = 0
if "eng_index" not in st.session_state:
    st.session_state.eng_index = 0

# ---------------------------------------------
# CSS — FIX ALL UI PROBLEMS
# ---------------------------------------------
st.markdown("""
<style>

    /* Fix slider width */
    .stSlider {
    max-width: 280px !important;
    }       

    /* Aligned column cards */
    .bubble {
        padding: 18px;
        border-radius: 12px;
        height: 420px;              /* FIXED HEIGHT — prevents vertical collapse */
        overflow-y: auto;           /* scroll only inside the card */
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }

    .bubble-pm {
        background-color: #eef6ff;
        border-left: 6px solid #4a90e2;
    }

    .bubble-eng {
        background-color: #ffecec;
        border-left: 6px solid #d9534f;
    }

    .bubble-ceo {
        background-color: #fff9e6;
        border-left: 6px solid #e6b800;
    }

    /* Reduce column padding spacing */
    .block-container {
        padding-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------
# INPUT SCREEN
# ---------------------------------------------
if st.session_state.state == "input":

    st.title("🏢 Boardroom Simulator")
    st.subheader("PM vs Engineering vs CEO Debate Generator")

    product_idea = st.text_area(
        "Enter your product idea:",
        placeholder="e.g., AI tool that summarizes Zoom meetings automatically.",
        height=110,
    )

    auto_idea = st.checkbox("Generate an idea for me instead")

    rounds = st.slider("Debate Rounds", 1, 3, 1, key="round_slider")

    if st.button("Run Debate", type="primary"):
        if not auto_idea and not product_idea.strip():
            st.error("Please enter an idea or enable auto-generate.")
        else:
            idea = None if auto_idea else product_idea.strip()

            with st.spinner("Running debate..."):
                result = run_debate(idea, rounds)

            st.session_state.debate_data = result
            st.session_state.pm_index = 0
            st.session_state.eng_index = 0
            st.session_state.state = "debate"
            st.rerun()

# ---------------------------------------------
# DEBATE SCREEN
# ---------------------------------------------
else:
    data = st.session_state.debate_data

    # unzip messages
    pm_msgs = [msg for role, msg in data["transcript"] if role.startswith("PM_")]
    eng_msgs = [msg for role, msg in data["transcript"] if role.startswith("ENG_")]

    # aligned 3-column layout
    col_pm, col_ceo, col_eng = st.columns([4, 3, 4])

    # ---------------- PM Column ----------------
    with col_pm:
        st.header("🧑‍💼 Product Manager")

        pm_text = pm_msgs[st.session_state.pm_index]
        st.markdown(f'<div class="bubble bubble-pm">{pm_text}</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("◀ Prev PM", disabled=st.session_state.pm_index == 0):
                st.session_state.pm_index -= 1
                st.rerun()
        with c2:
            if st.button("Next PM ▶", disabled=st.session_state.pm_index == len(pm_msgs)-1):
                st.session_state.pm_index += 1
                st.rerun()

    # ---------------- CEO Column ----------------
    with col_ceo:
        st.header("🧑‍⚖️ CEO Decision")

        # Final verdict only — no summary!
        st.markdown(
            f"""
            <div class="bubble bubble-ceo" style="height:420px; overflow-y:auto;">
                {data["ceo_verdict"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🔄 Restart"):
            st.session_state.state = "input"
            st.session_state.debate_data = None
            st.rerun()
    # ---------------- Engineering Column ----------------
    with col_eng:
        st.header("🛠 Engineering Lead")

        eng_text = eng_msgs[st.session_state.eng_index]
        st.markdown(f'<div class="bubble bubble-eng">{eng_text}</div>', unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            if st.button("◀ Prev Eng", disabled=st.session_state.eng_index == 0):
                st.session_state.eng_index -= 1
                st.rerun()
        with c4:
            if st.button("Next Eng ▶", disabled=st.session_state.eng_index == len(eng_msgs)-1):
                st.session_state.eng_index += 1
                st.rerun()
