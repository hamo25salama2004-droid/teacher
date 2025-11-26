import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Student Portal", layout="centered", page_icon="🎓")

st.markdown("""
<style>
    body { direction: rtl; }
    .stMetric { background-color: #f0f8ff; border-radius: 10px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

SHEET_NAME = "users_database"

@st.cache_resource
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

def main():
    if 'student_user' not in st.session_state:
        st.markdown("<h1 style='text-align: center; color: #1abc9c;'>🎓 بوابة الطالب</h1>", unsafe_allow_html=True)
        with st.form("login"):
            c = st.text_input("كود الطالب")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                client = get_client()
                try:
                    ws = client.open(SHEET_NAME).worksheet("Students_Main")
                    df = pd.DataFrame(ws.get_all_records())
                    df['Code'] = df['Code'].astype(str).str.strip()
                    df['Password'] = df['Password'].astype(str).str.strip()
                    u = df[(df['Code']==str(c).strip()) & (df['Password']==str(p).strip())]
                    if not u.empty:
                        st.session_state['student_user'] = u.iloc[0].to_dict()
                        st.rerun()
                    else: st.error("بيانات غير صحيحة")
                except: st.error("خطأ اتصال")
    else:
        u = st.session_state['student_user']
        st.title(f"مرحباً، {u['Name']}")
        
        c1, c2 = st.columns(2)
        c1.metric("الفرقة الدراسية", u['Year'])
        c2.metric("التخصص", u['Major'])
        
        st.divider()
        st.subheader("📂 ملفك الأكاديمي")
        
        client = get_client()
        try:
            ws = client.open(SHEET_NAME).worksheet(str(u['Code']))
            data = ws.get_all_records()
            st.dataframe(
                pd.DataFrame(data), 
                column_config={"Link": st.column_config.LinkColumn("رابط", display_text="🔗 فتح")},
                use_container_width=True,
                hide_index=True
            )
        except: st.info("الملف قيد التجهيز...")

        if st.button("تسجيل خروج"):
            del st.session_state['student_user']
            st.rerun()

if __name__ == '__main__':
    main()
