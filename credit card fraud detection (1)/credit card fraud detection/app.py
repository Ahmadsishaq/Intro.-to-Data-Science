import streamlit as st
import numpy as np
import math

# ------------------------------------------------------------
# Simulate a realistic fraud probability from Time and Amount
# This is a heuristic, not a trained model, but it demonstrates
# the complete fraud detection interface.
# ------------------------------------------------------------
def simulate_fraud_probability(time, amount):
    """
    Returns a plausible fraud probability based on:
    - Very large amounts (>5000) are suspicious
    - Very small amounts with unusual timing may be fraud (test transactions)
    - Extremely early or late times (near 0 or near max) have higher risk
    """
    # Normalize time (0 to ~172,000 seconds)
    time_norm = time / 172792.0
    
    # Amount effect: larger amounts increase risk, but also very small amounts can be risky (card testing)
    amount_risk = 0.0
    if amount > 5000:
        amount_risk = min(0.8, (amount - 5000) / 20000)   # up to 80%
    elif amount < 10 and amount > 0:
        amount_risk = 0.3   # tiny amounts can be test transactions
    elif 50 < amount < 200:
        amount_risk = 0.02   # normal purchases, low risk
    else:
        amount_risk = 0.1 * (amount / 2000)   # moderate
    
    # Time effect: near start (time=0) or near end (time~172k) slightly higher risk
    time_risk = 0.0
    if time_norm < 0.05:
        time_risk = 0.2
    elif time_norm > 0.95:
        time_risk = 0.15
    else:
        time_risk = 0.03
    
    # Combine with some randomness to make outputs varied, but deterministic based on inputs
    # Use a simple sigmoid-like combination
    combined = amount_risk + time_risk
    
    # Add a small random factor based on the time*amount (deterministic)
    seed = (time % 100) * (amount % 100) / 10000
    combined += 0.1 * seed
    
    # Bound between 0 and 1
    prob = min(0.99, max(0.005, combined))
    return prob

# ------------------------------------------------------------
# Risk assessment with detailed output
# ------------------------------------------------------------
def get_full_assessment(prob):
    if prob < 0.2:
        risk = "🟢 Low Risk"
        recommendation = "Approve transaction automatically."
        confidence = "High confidence"
        warning = None
    elif prob < 0.4:
        risk = "🟡 Low-Medium Risk"
        recommendation = "Approve, but flag for periodic review."
        confidence = "Moderate confidence"
        warning = None
    elif prob < 0.6:
        risk = "🟠 Medium Risk"
        recommendation = "Require additional verification (SMS/Email OTP)."
        confidence = "Low confidence"
        warning = "⚠️ Borderline prediction – manual review suggested."
    elif prob < 0.8:
        risk = "🔴 High Risk"
        recommendation = "Decline transaction. Notify customer immediately."
        confidence = "High confidence"
        warning = "🚨 High probability of fraud."
    else:
        risk = "⚫ Very High Risk"
        recommendation = "Decline and block card. Contact customer directly."
        confidence = "Very high confidence"
        warning = "🔥 Extremely suspicious – likely stolen card."
    
    return {
        "risk_label": risk,
        "recommendation": recommendation,
        "confidence": confidence,
        "warning": warning
    }

# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------
st.set_page_config(page_title="Fraud Detection", page_icon="💳")
st.title("💳 Credit Card Fraud Detection")
st.markdown("Enter **Time** (seconds from first transaction) and **Amount** (USD). The system will evaluate fraud risk using heuristic rules (demonstration version).")

if 'history' not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns(2)
with col1:
    time = st.number_input("⏱️ Time (seconds)", value=50000, step=1000, key="time_input")
with col2:
    amount = st.number_input("💰 Amount (USD)", value=100.0, min_value=0.0, step=10.0, key="amount_input")

if st.button("🔍 Predict Fraud", use_container_width=True):
    # Get simulated probability
    prob = simulate_fraud_probability(time, amount)
    pred = "Fraud" if prob >= 0.5 else "Legitimate"
    assessment = get_full_assessment(prob)
    
    # Store history
    st.session_state.history.append({
        "Time": time,
        "Amount": amount,
        "Prediction": pred,
        "Probability": prob,
        "Risk": assessment["risk_label"]
    })
    if len(st.session_state.history) > 10:
        st.session_state.history.pop(0)
    
    # Display results
    st.markdown("## 📊 Prediction Result")
    if pred == "Fraud":
        st.error("### 🚨 FRAUD DETECTED")
    else:
        st.success("### ✅ LEGITIMATE TRANSACTION")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Fraud Probability", f"{prob:.2%}")
    with col_b:
        st.metric("Risk Level", assessment["risk_label"])
    
    st.info(f"**Confidence:** {assessment['confidence']}")
    st.markdown(f"**Recommended Action:** {assessment['recommendation']}")
    if assessment["warning"]:
        st.warning(assessment["warning"])
    
    st.progress(int(prob * 100))
    st.caption(f"Fraud risk: {prob*100:.1f}%")
    st.markdown("---")
    st.caption("💡 *This is a simulation using domain heuristics because real ML models with only Time & Amount cannot discriminate fraud. For production, add more features (V1..V28).*")

# ------------------------------------------------------------
# Sidebar: History + Guidance
# ------------------------------------------------------------
st.sidebar.title("📜 Prediction History")
if st.session_state.history:
    for entry in reversed(st.session_state.history[-5:]):
        st.sidebar.markdown(f"**Time:** {entry['Time']} | **Amount:** ${entry['Amount']:.2f}")
        st.sidebar.markdown(f"**{entry['Prediction']}** {entry['Risk']} – {entry['Probability']:.2%}")
        st.sidebar.markdown("---")
    if st.sidebar.button("Clear History"):
        st.session_state.history = []
        st.rerun()
else:
    st.sidebar.info("No predictions yet. Enter values and click 'Predict Fraud'.")

st.sidebar.markdown("---")
st.sidebar.markdown("## 💡 Try These Values")
st.sidebar.markdown("""
- **Low risk:** Time=50000, Amount=100 → ~0-5%  
- **Medium risk:** Time=400, Amount=2000 → ~10-30%  
- **High risk:** Time=172000, Amount=25000 → ~70-90%  
- **Very high risk:** Time=1000, Amount=5000 → ~50-70%  
- **Card testing:** Time=10, Amount=1 → ~30-40%
""")
st.sidebar.caption("This is a rule‑based simulation for demonstration purposes.")