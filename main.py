import streamlit as st
import time
import qrcode
from io import BytesIO
import base64
import uuid
import urllib.parse # Added for URL encoding

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Metro & Cab Booking", page_icon="🎫", layout="centered")

# --- Initialize Session States ---
if 'step' not in st.session_state:
    st.session_state.step = 'form'
if 'booking_data' not in st.session_state:
    st.session_state.booking_data = {}

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    .price-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 10px 0; }
    .ticket-card { background-color: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #28a745; }
    .ticket-header { text-align: center; color: #28a745; font-weight: 800; border-bottom: 2px dashed #eee; padding-bottom: 10px; margin-bottom: 15px; }
    .ticket-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f9f9f9; }
    .ticket-label { color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .ticket-value { font-weight: 700; color: #333; }
    .qr-container { text-align: center; background: white; padding: 20px; border-radius: 15px; border: 2px solid #eee; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def reset_app():
    st.session_state.step = 'form'
    st.session_state.booking_data = {}
    st.rerun()

# ---------------- APP LOGIC ----------------

# STEP 1: BOOKING FORM
if st.session_state.step == 'form':
    st.title("🚇 Metro Smart Book")
    
    with st.container(border=True):
        name = st.text_input("Passenger Name", placeholder="e.g. John Doe")
        
        c1, c2 = st.columns(2)
        stations = ["Ameerpet", "Hitech City", "Jubilee Hills", "Kukatpally", "Secunderabad", "Miyapur"]
        with c1:
            from_st = st.selectbox("From", stations)
        with c2:
            to_st = st.selectbox("To", [s for s in stations if s != from_st])

        tickets = st.number_input("Number of Tickets", min_value=1, max_value=10, value=1)
        
        st.markdown("---")
        cab_req = st.toggle("Include Connecting Cab 🚖", value=False)
        
        drop_loc = ""
        if cab_req:
            drop_loc = st.text_input("Final Drop Location", placeholder="Enter specific destination...")

        # Pricing
        base_fare = 40
        cab_fare = 150 if cab_req else 0
        total_amt = (base_fare * tickets) + cab_fare

        st.markdown(f"""
        <div class="price-box">
            <small>ESTIMATED TOTAL</small>
            <h2 style='margin:0; color:#28a745;'>₹{total_amt}</h2>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Proceed to Payment", type="primary"):
            if not name:
                st.error("Please enter passenger name.")
            elif cab_req and not drop_loc:
                st.error("Please specify cab drop location.")
            else:
                st.session_state.booking_data = {
                    "name": name, "from": from_st, "to": to_st,
                    "tickets": tickets, "cab": cab_req, "drop": drop_loc,
                    "total": total_amt, "id": str(uuid.uuid4())[:8].upper()
                }
                st.session_state.step = 'payment'
                st.rerun()

# STEP 2: PAYMENT GATEWAY (QR WORKING)
elif st.session_state.step == 'payment':
    st.title("💳 Scan to Pay")
    d = st.session_state.booking_data
    
    # Generate UPI URL (Standard Format)
    # Replace 'yourname@upi' with a real UPI ID to receive actual money
    upi_id = "merchant@upi" 
    transaction_note = urllib.parse.quote(f"Metro Ticket {d['id']}")
    upi_url = f"upi://pay?pa={upi_id}&pn=MetroSmartBook&am={d['total']}&tn={transaction_note}&cu=INR"
    
    payment_qr = generate_qr(upi_url)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="qr-container">
            <p style="margin-bottom:10px; font-weight:bold; color:#555;">Scan with GPay, PhonePe, or Paytm</p>
            <img src="data:image/png;base64,{payment_qr}" width="220">
            <h3 style="color:#28a745; margin-top:10px;">₹{d['total']}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("### Payment Summary")
        st.write(f"**Passenger:** {d['name']}")
        st.write(f"**Journey:** {d['from']} ➝ {d['to']}")
        st.info("After completing the payment in your app, click the button below to generate your ticket.")
        
        if st.button("Verify & Generate Ticket", type="primary"):
            with st.spinner("Confirming transaction..."):
                time.sleep(2) # Simulating bank verification
                st.session_state.step = 'ticket'
                st.rerun()
        
        if st.button("Cancel & Go Back"):
            st.session_state.step = 'form'
            st.rerun()

# STEP 3: FINAL TICKET
elif st.session_state.step == 'ticket':
    st.balloons()
    st.title("🎟️ Booking Confirmed!")
    
    d = st.session_state.booking_data
    qr_payload = f"TID:{d['id']}|PASS:{d['name']}|VALID:TRUE"
    ticket_qr = generate_qr(qr_payload)

    cab_html = f"""
    <div class="ticket-row">
        <span class="ticket-label">Cab Status</span>
        <span class="ticket-value">READY AT {d['to']}</span>
    </div>
    """ if d['cab'] else ""

    st.markdown(f"""
    <div class="ticket-card">
        <div class="ticket-header">BOARDING PASS</div>
        <div class="ticket-row"><span class="ticket-label">Passenger</span><span class="ticket-value">{d['name']}</span></div>
        <div class="ticket-row"><span class="ticket-label">Route</span><span class="ticket-value">{d['from']} ➝ {d['to']}</span></div>
        <div class="ticket-row"><span class="ticket-label">Qty</span><span class="ticket-value">{d['tickets']} Pax</span></div>
        {cab_html}
        <div style="text-align:center; margin-top:20px; background:#f8f9fa; padding:15px; border-radius:10px;">
            <img src="data:image/png;base64,{ticket_qr}" width="180">
            <div style="font-family:monospace; margin-top:10px; color:#888;">TXN: {d['id']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Book Another Journey"):
        reset_app()
