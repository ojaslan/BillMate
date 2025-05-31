import streamlit as st
import openai
import os
import json
from paymanai import Paymanai

# Setup from environment
openai.api_key = os.getenv(OPENAI_API_KEY)
payman_api_secret = os.getenv(PAYMAN_API_SECRET)

# Set Streamlit layout
st.set_page_config(page_title="SmartPay Bot 💸", layout="centered")
st.title("SmartPay Bot 💸")
st.caption("Extract + Pay bills using OpenAI and Payman APIs")

# User inputs
st.subheader("Enter or Paste Your Bill")
bill_text = st.text_area("Bill Details", placeholder="Paste your bill text or details here...")

if bill_text and st.button("Extract & Pay"):
    with st.spinner("🔍 Extracting payment fields using OpenAI..."):

        prompt = """
        Extract the following fields from this bill and return JSON:
        - name (payee)
        - account_number
        - routing_number
        - account_type (checking/savings)
        - amount
        - due_date (YYYY-MM-DD)
        """

        try:
            client = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": bill_text}
                ]
            )

            extracted = json.loads(client.choices[0].message["content"])
        except Exception as e:
            st.error(f"Extraction error: {e}")
            st.stop()

    # Show editable form
    st.subheader("📝 Confirm or Edit Payment Info")

    name = st.text_input("Payee Name", value=extracted.get("name", ""))
    account_number = st.text_input("Account Number", value=extracted.get("account_number", ""))
    routing_number = st.text_input("Routing Number", value=extracted.get("routing_number", ""))
    account_type = st.selectbox("Account Type", ["checking", "savings"], index=0)
    amount = st.number_input("Amount ($)", value=float(extracted.get("amount", 0)))
    due_date = st.date_input("Due Date")

    if st.button("💸 Send Payment"):
        with st.spinner("💳 Sending payment..."):
            try:
                payman = Paymanai(x_payman_api_secret=payman_api_secret)

                # Search or create payee
                existing = payman.payments.search_payees(name=name)
                payee_id = existing[0]["id"] if existing else None

                if not payee_id:
                    payee = payman.payments.create_payee(
                        type="US_ACH",
                        name=name,
                        account_holder_name=name,
                        account_number=account_number,
                        routing_number=routing_number,
                        account_type=account_type,
                        account_holder_type="individual"
                    )
                    payee_id = payee.id

                # Send payment
                payment = payman.payments.send_payment(
                    amount_decimal=amount,
                    payee_id=payee_id,
                    memo=f"Bill payment due on {due_date}"
                )

                st.success("✅ Payment Sent!")
                st.info(f"Reference: {payment.reference}")

            except Exception as e:
                st.error(f"Payment error: {e}")
