import streamlit as st
import time
import qrcode
from io import BytesIO
import base64
import uuid

# ---------------- CONFIGURATION ----------------
st.set_page_config(page_title="Metro & Cab Booking", page_icon="🎫", layout="centered")

# --- Initialize Session States ---
if 'step' not in st.session_state:
    st.session_state.step = 'form'
if 'booking_data' not in st.session_state:
    st.session_state.booking_data = {}

# ---------------- CUSTOM CSS (Enhanced) ----------------
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; }
    .price-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 10px 0; }
    .ticket-card { background-color: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 8px solid #28a745; }
    .ticket-header { text-align: center; color: #28a745; font-weight: 800; border-bottom: 2px dashed #eee; padding-bottom: 10px; margin-bottom: 15px; }
    .ticket-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #f9f9f9; }
    .ticket-label { color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .ticket-value { font-weight: 700; color: #333; }
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
    st.write("Plan your journey and connecting ride.")
    
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

        # Dynamic Pricing Logic
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

# STEP 2: PAYMENT GATEWAY
elif st.session_state.step == 'payment':
    st.title("💳 Secure Payment")
    data = st.session_state.booking_data
    
    st.info(f"Amount Payable: **₹{data['total']}**")
    
    pay_col1, pay_col2 = st.columns(2)
    with pay_col1:
        st.radio("Select Payment Method", ["UPI / QR", "Credit Card", "Net Banking"])
    
    with pay_col2:
        st.write("Summary:")
        st.caption(f"Tickets: {data['tickets']} x Metro Pass")
        if data['cab']: st.caption("Add-on: Connecting Cab")

    if st.button("Pay Now"):
        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            progress_bar.progress(percent_complete + 1)
        
        st.success("Payment Successful!")
        time.sleep(1)
        st.session_state.step = 'ticket'
        st.rerun()
    
    if st.button("Cancel", variant="secondary"):
        st.session_state.step = 'form'
        st.rerun()

# STEP 3: FINAL TICKET
elif st.session_state.step == 'ticket':
    st.balloons()
    st.title("🎟️ Your Digital Ticket")
    
    d = st.session_state.booking_data
    qr_payload = f"TID:{d['id']}|NAME:{d['name']}|FARE:{d['total']}"
    qr_img = generate_qr(qr_payload)

    cab_html = f"""
    <div class="ticket-row">
        <span class="ticket-label">Cab Status</span>
        <span class="ticket-value">READY AT {d['to']}</span>
    </div>
    <div class="ticket-row">
        <span class="ticket-label">Drop-off</span>
        <span class="ticket-value">{d['drop']}</span>
    </div>
    """ if d['cab'] else ""

    ticket_html = f"""
    <div class="ticket-card">
        <div class="ticket-header">OFFICIAL BOARDING PASS</div>
        <div class="ticket-row"><span class="ticket-label">Passenger</span><span class="ticket-value">{d['name']}</span></div>
        <div class="ticket-row"><span class="ticket-label">Journey</span><span class="ticket-value">{d['from']} ➝ {d['to']}</span></div>
        <div class="ticket-row"><span class="ticket-label">Qty</span><span class="ticket-value">{d['tickets']} Pax</span></div>
        {cab_html}
        <div style="text-align:center; margin-top:20px; background:#f8f9fa; padding:15px; border-radius:10px;">
            <img src="data:image/png;base64,{qr_img}" width="180">
            <div style="font-family:monospace; margin-top:10px;">TXN ID: {d['id']}</div>
        </div>
    </div>
    """
    st.markdown(ticket_html, unsafe_allow_html=True)
    
    st.write("")
    if st.button("Book Another Ticket"):
        reset_app()
