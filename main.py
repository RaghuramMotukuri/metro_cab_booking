import streamlit as st
import time
import qrcode
from io import BytesIO
import base64
import uuid
import urllib.parse

# ---------------- 1. PAGE CONFIGURATION ----------------
st.set_page_config(page_title="Metro Smart Book", page_icon="🎫", layout="centered")

# --- Initialize Session States ---
# This prevents the app from resetting when the user clicks buttons
if 'step' not in st.session_state:
    st.session_state.step = 'form'
if 'booking_data' not in st.session_state:
    st.session_state.booking_data = {}

# ---------------- 2. CUSTOM CSS ----------------
st.markdown("""
<style>
    /* Global Styles */
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { border-color: #28a745; color: #28a745; }
    
    /* Price Box */
    .price-box { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #28a745; 
        margin: 15px 0; 
    }

    /* Ticket Card */
    .ticket-card { 
        background-color: white; 
        border-radius: 15px; 
        padding: 25px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        border-top: 8px solid #28a745; 
        color: #333;
    }
    .ticket-header { 
        text-align: center; 
        color: #28a745; 
        font-weight: 800; 
        font-size: 20px;
        border-bottom: 2px dashed #eee; 
        padding-bottom: 10px; 
        margin-bottom: 15px; 
    }
    .ticket-row { 
        display: flex; 
        justify-content: space-between; 
        padding: 10px 0; 
        border-bottom: 1px solid #f9f9f9; 
    }
    .ticket-label { color: #888; font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .ticket-value { font-weight: 700; color: #111; }
    
    /* QR Container */
    .qr-container { 
        text-align: center; 
        background: white; 
        padding: 20px; 
        border-radius: 15px; 
        border: 2px solid #eee; 
        margin: 10px 0; 
    }
</style>
""", unsafe_allow_html=True)

# ---------------- 3. HELPER FUNCTIONS ----------------
def generate_qr_base64(data):
    """Generates a QR code and returns the base64 string for HTML rendering."""
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode(), buffer.getvalue()

def reset_app():
    """Clears session and returns to the home screen."""
    st.session_state.step = 'form'
    st.session_state.booking_data = {}
    st.rerun()

# ---------------- 4. APP LOGIC ----------------

# --- STEP 1: BOOKING FORM ---
if st.session_state.step == 'form':
    st.title("🚇 Metro Smart Book")
    st.subheader("Hyderabad Metro Rail")
    
    with st.container(border=True):
        name = st.text_input("Passenger Name", placeholder="Enter full name")
        
        # Dynamic Menu: 'To' station cannot be the same as 'From' station
        stations = ["Ameerpet", "Hitech City", "Jubilee Hills", "Kukatpally", "Secunderabad", "Miyapur"]
        c1, c2 = st.columns(2)
        with c1:
            from_st = st.selectbox("From Station", stations)
        with c2:
            to_st = st.selectbox("To Station", [s for s in stations if s != from_st])

        tickets = st.number_input("Number of Passengers", min_value=1, max_value=10, value=1)
        
        st.markdown("---")
        cab_req = st.toggle("Add Last-Mile Cab 🚖", value=False)
        
        drop_loc = ""
        if cab_req:
            drop_loc = st.text_input("Cab Drop-off Location", placeholder="e.g., Mindspace Building 12")

        # Dynamic Pricing Logic
        base_fare = 45  # Standard fare
        cab_fare = 120 if cab_req else 0
        total_amt = (base_fare * tickets) + cab_fare

        st.markdown(f"""
        <div class="price-box">
            <small>PAYABLE AMOUNT</small>
            <h2 style='margin:0; color:#28a745;'>₹{total_amt}.00</h2>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Confirm & Pay", type="primary"):
            if not name:
                st.error("Please provide a passenger name.")
            elif cab_req and not drop_loc:
                st.error("Please enter a cab drop location.")
            else:
                # Save data and move to payment
                st.session_state.booking_data = {
                    "name": name, "from": from_st, "to": to_st,
                    "tickets": tickets, "cab": cab_req, "drop": drop_loc,
                    "total": total_amt, "id": str(uuid.uuid4())[:8].upper()
                }
                st.session_state.step = 'payment'
                st.rerun()

# --- STEP 2: PAYMENT GATEWAY (DYNAMIC QR) ---
elif st.session_state.step == 'payment':
    st.title("💳 Payment Gateway")
    d = st.session_state.booking_data
    
    # Real-world logic: Generate a UPI URI for GPay/PhonePe
    upi_id = "metro_merchant@upi" # Dummy merchant ID
    note = urllib.parse.quote(f"Ticket {d['id']}")
    upi_url = f"upi://pay?pa={upi_id}&pn=MetroSmartBook&am={d['total']}&tn={note}&cu=INR"
    
    payment_qr_b64, _ = generate_qr_base64(upi_url)

    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="qr-container">
            <p style="margin-bottom:15px; font-size:14px;">Scan with any UPI App to Pay</p>
            <img src="data:image/png;base64,{payment_qr_b64}" width="220">
            <h2 style="color:#28a745; margin-top:15px;">₹{d['total']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("### Trip Summary")
        st.write(f"**Route:** {d['from']} ➝ {d['to']}")
        st.write(f"**Passengers:** {d['tickets']}")
        if d['cab']:
            st.caption("✅ Includes Cab Drop-off")
        
        st.warning("Please do not refresh this page while payment is in progress.")
        
        if st.button("I Have Paid (Simulate Success)", type="primary"):
            with st.spinner("Verifying transaction with bank..."):
                time.sleep(2) 
                st.session_state.step = 'ticket'
                st.rerun()
        
        if st.button("Go Back / Cancel"):
            st.session_state.step = 'form'
            st.rerun()

# --- STEP 3: FINAL TICKET DISPLAY ---
elif st.session_state.step == 'ticket':
    st.balloons()
    st.title("🎟️ Ticket Issued")
    
    d = st.session_state.booking_data
    # Content of the gate-entry QR
    ticket_payload = f"METRO_V1|ID:{d['id']}|PAX:{d['tickets']}|ROUTE:{d['from']}-{d['to']}"
    ticket_qr_b64, raw_bytes = generate_qr_base64(ticket_payload)

    cab_info = f"""
    <div class="ticket-row">
        <span class="ticket-label">Cab Status</span>
        <span class="ticket-value">READY AT {d['to']}</span>
    </div>
    <div class="ticket-row">
        <span class="ticket-label">Cab Destination</span>
        <span class="ticket-value">{d['drop']}</span>
    </div>
    """ if d['cab'] else ""

    st.markdown(f"""
    <div class="ticket-card">
        <div class="ticket-header">HYDERABAD METRO BOARDING PASS</div>
        <div class="ticket-row"><span class="ticket-label">Passenger</span><span class="ticket-value">{d['name']}</span></div>
        <div class="ticket-row"><span class="ticket-label">Trip</span><span class="ticket-value">{d['from']} to {d['to']}</span></div>
        <div class="ticket-row"><span class="ticket-label">Fare Paid</span><span class="ticket-value">₹{d['total']}</span></div>
        {cab_info}
        <div style="text-align:center; margin-top:20px; background:#fdfdfd; padding:20px; border-radius:10px; border:1px solid #eee;">
            <img src="data:image/png;base64,{ticket_qr_b64}" width="180">
            <div style="font-family:monospace; margin-top:10px; color:#555; font-size:12px;">TXN REF: {d['id']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    # Download Button
    st.download_button(
        label="📥 Download Ticket as Image",
        data=raw_bytes,
        file_name=f"Metro_Ticket_{d['id']}.png",
        mime="image/png"
    )

    if st.button("Book New Journey", variant="secondary"):
        reset_app()
