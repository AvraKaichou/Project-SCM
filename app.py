import streamlit as st
import pandas as pd
import datetime
import random
import plotly.express as px

# --- 1. CONFIG & INITIALIZATION ---
st.set_page_config(page_title="AutoChain SCM Enterprise", layout="wide", page_icon="🚛")

# Styling CSS Custom
st.markdown("""
<style>
    .main-header {font-size: 24px; font-weight: bold; color: #2E4053;}
    .metric-card {background-color: #F7F9F9; padding: 15px; border-radius: 10px; border-left: 5px solid #2874A6;}
    .stButton>button {width: 100%; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# Inisialisasi Database (Session State)
if 'db_initialized' not in st.session_state:
    # A. Inventory Awal
    st.session_state['inventory'] = pd.DataFrame([
        {"BatchID": "SN-RAW-001", "Item": "Bijih Besi (Iron Ore)", "Type": "Raw Material", "Qty": 5000, "Unit": "Ton", "Loc": "Gudang A (Inbound)"},
        {"BatchID": "SN-RAW-002", "Item": "Lithium Crude", "Type": "Raw Material", "Qty": 2000, "Unit": "Ton", "Loc": "Gudang B (Hazardous)"}
    ])
    
    # B. Transaksi Log
    st.session_state['logs'] = []
    
    # C. Master Data Partner
    st.session_state['partners'] = {
        "Vendors": ["Tambang Freeport", "Vale Mining", "Borneo Coal & Mineral"],
        "Customers": ["Toyota Manufacturing", "Hyundai Motor Plant", "Tesla Gigafactory Indo"]
    }
    
    # D. Resep Produksi
    st.session_state['bom'] = {
        "Bijih Besi (Iron Ore)": {"Output": "Baja Lembaran (Steel Sheet)", "Ratio": 0.6}, 
        "Lithium Crude": {"Output": "Katoda Baterai EV", "Ratio": 0.4}
    }
    
    st.session_state['db_initialized'] = True

# --- 2. CORE FUNCTIONS ---
def log_transaction(trans_type, ref, item, qty, partner, details):
    entry = {
        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Type": trans_type,
        "Ref": ref,
        "Item": item,
        "Qty": qty,
        "Partner": partner,
        "Details": details
    }
    st.session_state['logs'].insert(0, entry)

def generate_id(prefix):
    return f"{prefix}-{random.randint(1000, 9999)}"

# --- 3. LAYOUT & SIDEBAR ---
st.sidebar.title("🚛 AutoChain SCM")
st.sidebar.caption("Automotive Upstream ERP v1.1 (Fixed)")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Modul Operasional", 
    ["Dashboard Utama", "1. Procurement (Beli)", "2. Manufacturing (Olah)", "3. Sales (Jual)", "4. Inventory & Traceability"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** Mulai dari Procurement untuk isi stok, lalu Manufacturing, baru Sales.")

# --- 4. MODULES ---

# === DASHBOARD ===
if menu == "Dashboard Utama":
    st.title("📊 Executive Dashboard")
    inv = st.session_state['inventory']
    total_vol = inv['Qty'].sum()
    total_value_est = total_vol * 150 
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Material", f"{total_vol:,.0f}", "Ton/Unit")
    col2.metric("Valuasi Aset (Est)", f"${total_value_est:,.0f}", "+5%")
    col3.metric("Total Batch", len(inv), "Active Lots")
    col4.metric("Pending Orders", "0", "Low")
    
    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Komposisi Stok Gudang")
        if not inv.empty:
            fig = px.bar(inv, x="Item", y="Qty", color="Type", title="Level Inventaris per Material")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Aktivitas Terakhir")
        logs_df = pd.DataFrame(st.session_state['logs']).head(5)
        if not logs_df.empty:
            st.table(logs_df[['Type', 'Item', 'Qty']])
        else:
            st.text("Belum ada aktivitas.")

# === PROCUREMENT ===
elif menu == "1. Procurement (Beli)":
    st.title("🛒 Procurement (Inbound Mining)")
    tab1, tab2 = st.tabs(["Buat Purchase Order (PO)", "Riwayat Pembelian"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            vendor = st.selectbox("Vendor Tambang", st.session_state['partners']['Vendors'])
            item = st.selectbox("Material Tambang", ["Bijih Besi (Iron Ore)", "Lithium Crude", "Bauksit", "Karet Mentah"])
        with col2:
            qty = st.number_input("Jumlah Order (Ton)", min_value=10, value=100)
            loc = st.selectbox("Gudang Tujuan", ["Gudang A (Inbound)", "Gudang B (Hazardous)"])
        
        if st.button("Konfirmasi PO & Terima Barang"):
            batch_id = generate_id("SN-RAW")
            new_stock = {"BatchID": batch_id, "Item": item, "Type": "Raw Material", "Qty": qty, "Unit": "Ton", "Loc": loc}
            st.session_state['inventory'] = pd.concat([st.session_state['inventory'], pd.DataFrame([new_stock])], ignore_index=True)
            po_ref = generate_id("PO")
            log_transaction("INBOUND", po_ref, item, qty, vendor, f"Batch: {batch_id}")
            st.success(f"Sukses! PO {po_ref} diproses. Material masuk stok dengan Batch ID: **{batch_id}**")

    with tab2:
        logs = pd.DataFrame(st.session_state['logs'])
        if not logs.empty:
            st.dataframe(logs[logs['Type'] == "INBOUND"], use_container_width=True)

# === MANUFACTURING ===
elif menu == "2. Manufacturing (Olah)":
    st.title("🏭 Manufacturing (Smelting & Processing)")
    raw_mat = st.session_state['inventory'][st.session_state['inventory']['Type'] == "Raw Material"]
    
    if raw_mat.empty:
        st.warning("⚠️ Tidak ada Raw Material. Silakan lakukan Procurement dulu.")
    else:
        st.subheader("Work Order / Perintah Kerja")
        c1, c2 = st.columns(2)
        with c1:
            batch_input = st.selectbox("Pilih Batch Bahan Mentah", raw_mat['BatchID'].unique())
            curr_batch = raw_mat[raw_mat['BatchID'] == batch_input].iloc[0]
            st.info(f"Info Batch: {curr_batch['Item']} | Sisa: {curr_batch['Qty']} Ton")
            
        with c2:
            if curr_batch['Item'] in st.session_state['bom']:
                recipe = st.session_state['bom'][curr_batch['Item']]
                output_item = recipe['Output']
                ratio = recipe['Ratio']
                
                # FIX: Ensure qty_process doesn't crash if stock is 0 (though unlikely here due to filter)
                max_process = int(curr_batch['Qty'])
                if max_process > 0:
                    qty_process = st.number_input("Jumlah Diproses (Ton)", min_value=1, max_value=max_process)
                    est_result = qty_process * ratio
                    
                    st.success(f"♻️ Konversi: {curr_batch['Item']} -> {output_item}")
                    st.write(f"Estimasi Output: **{est_result} Unit/Roll**")
                    
                    if st.button("Jalankan Produksi"):
                        idx = st.session_state['inventory'].index[st.session_state['inventory']['BatchID'] == batch_input].tolist()[0]
                        st.session_state['inventory'].at[idx, 'Qty'] -= qty_process
                        
                        if st.session_state['inventory'].at[idx, 'Qty'] <= 0:
                             st.session_state['inventory'] = st.session_state['inventory'].drop(idx).reset_index(drop=True)
                        
                        new_batch_id = generate_id("SN-FIN")
                        new_stock = {
                            "BatchID": new_batch_id, 
                            "Item": output_item, 
                            "Type": "Finished Goods", 
                            "Qty": est_result, 
                            "Unit": "Unit/Roll", 
                            "Loc": "Gudang C (Outbound)"
                        }
                        st.session_state['inventory'] = pd.concat([st.session_state['inventory'], pd.DataFrame([new_stock])], ignore_index=True)
                        
                        mo_ref = generate_id("MO")
                        log_transaction("MANUFACTURING", mo_ref, output_item, est_result, "Internal", f"From {batch_input}")
                        st.balloons()
                        st.success(f"Produksi Selesai! Barang Jadi ID: {new_batch_id}")
                else:
                    st.error("Stok batch ini habis (0).")
            else:
                st.error("Resep BOM tidak ditemukan untuk material ini.")

# === SALES (BAGIAN YANG DIPERBAIKI) ===
elif menu == "3. Sales (Jual)":
    st.title("🚚 Distribution (Sales to Plant)")
    fg_mat = st.session_state['inventory'][st.session_state['inventory']['Type'] == "Finished Goods"]
    
    if fg_mat.empty:
        st.warning("⚠️ Gudang Barang Jadi kosong. Lakukan Manufacturing dulu.")
    else:
        with st.form("so_form"):
            col1, col2 = st.columns(2)
            customer = col1.selectbox("Customer (Pabrik Mobil)", st.session_state['partners']['Customers'])
            batch_select = col2.selectbox("Pilih Barang (Batch)", fg_mat['BatchID'].unique())
            
            # Detail Item
            curr_item = fg_mat[fg_mat['BatchID'] == batch_select].iloc[0]
            st.caption(f"Item: {curr_item['Item']} | Stok Tersedia: {curr_item['Qty']}")
            
            # === PERBAIKAN LOGIKA DISINI ===
            qty_avail = int(curr_item['Qty']) # Pastikan integer
            
            if qty_avail <= 0:
                st.error("Stok Habis (0). Tidak dapat membuat Delivery Order.")
                submit = st.form_submit_button("Tombol Dinonaktifkan", disabled=True)
            else:
                # Hanya munculkan input jika stok > 0
                qty_sell = st.number_input("Jumlah Kirim", min_value=1, max_value=qty_avail)
                submit = st.form_submit_button("Buat Delivery Order (DO)")
                
                if submit:
                    idx = st.session_state['inventory'].index[st.session_state['inventory']['BatchID'] == batch_select].tolist()[0]
                    st.session_state['inventory'].at[idx, 'Qty'] -= qty_sell
                    
                    if st.session_state['inventory'].at[idx, 'Qty'] <= 0:
                            st.session_state['inventory'] = st.session_state['inventory'].drop(idx).reset_index(drop=True)
                    
                    do_ref = generate_id("DO")
                    log_transaction("OUTBOUND", do_ref, curr_item['Item'], qty_sell, customer, f"Sold Batch {batch_select}")
                    st.success(f"Barang dikirim ke {customer}. DO Ref: {do_ref}")

# === INVENTORY & TRACEABILITY ===
elif menu == "4. Inventory & Traceability":
    st.title("📦 Warehouse Master Data")
    tab1, tab2 = st.tabs(["Stok Real-time", "Audit Trail (Log)"])
    
    with tab1:
        st.dataframe(st.session_state['inventory'], use_container_width=True)
        st.markdown("### 🔍 Serial Number Traceability")
        search_sn = st.text_input("Masukkan Batch ID / Serial Number untuk melacak:")
        if search_sn:
            res = st.session_state['inventory'][st.session_state['inventory']['BatchID'].str.contains(search_sn, case=False)]
            if not res.empty:
                st.write("Status Saat Ini:")
                st.dataframe(res)
            
            st.write("Riwayat Pergerakan:")
            logs = pd.DataFrame(st.session_state['logs'])
            hist = logs[logs['Details'].str.contains(search_sn, case=False) | logs['Ref'].str.contains(search_sn, case=False)]
            st.table(hist)

    with tab2:
        st.dataframe(pd.DataFrame(st.session_state['logs']), use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("© 2024 AutoChain SCM Systems v1.1")
