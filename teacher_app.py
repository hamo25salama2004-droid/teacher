import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="بوابة المعلم", page_icon="👨‍🏫")

# --- الاتصال ---
def get_database():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("School_System")

# --- تسجيل الدخول ---
if 'teacher_logged_in' not in st.session_state:
    st.session_state['teacher_logged_in'] = False

if not st.session_state['teacher_logged_in']:
    st.title("🔐 دخول المعلمين")
    with st.form("tech_login"):
        t_code = st.text_input("كود المعلم")
        t_pass = st.text_input("الباسوورد", type="password")
        btn = st.form_submit_button("دخول")
        
        if btn:
            sheet = get_database()
            ws = sheet.worksheet("Teachers")
            try:
                cell = ws.find(t_code)
                if cell:
                    row_vals = ws.row_values(cell.row)
                    # Teachers: ID, Name, Subject, Grade, Term, Password (col 6)
                    real_pass = row_vals[5]
                    if str(t_pass).strip() == str(real_pass).strip():
                        st.session_state['teacher_logged_in'] = True
                        st.session_state['teacher_data'] = row_vals
                        st.rerun()
                    else:
                        st.error("بيانات خاطئة")
                else:
                    st.error("الكود غير موجود")
            except:
                st.error("خطأ في الاتصال")

else:
    data = st.session_state['teacher_data']
    # [ID, Name, Subject, Grade, Term, Pass]
    
    st.title(f"أهلاً بك أستاذ/ة {data[1]}")
    st.info(f"المادة: {data[2]} | الصف: {data[3]} | الترم: {data[4]}")
    st.caption(f"وقت الدخول: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    st.divider()
    
    st.header("📝 رصد الدرجات")
    
    sheet = get_database()
    
    with st.form("grading_form"):
        st_id_input = st.text_input("كود الطالب")
        score = st.number_input("الدرجة", min_value=0, max_value=100)
        pass_mark = st.number_input("درجة النجاح من", min_value=0, max_value=100, value=50)
        
        submit_grade = st.form_submit_button("رصد الدرجة")
        
        if submit_grade and st_id_input:
            # التحقق من وجود الطالب أولاً
            ws_students = sheet.worksheet("Students")
            try:
                st_found = ws_students.find(st_id_input)
                if st_found:
                    status = "ناجح" if score >= pass_mark else "راسب"
                    
                    ws_grades = sheet.worksheet("Grades")
                    # Grades: StudentID, TeacherID, Subject, Score, Status, Date
                    ws_grades.append_row([
                        st_id_input,
                        data[0], # Teacher ID
                        data[2], # Subject
                        score,
                        status,
                        str(datetime.now().date())
                    ])
                    st.success(f"تم رصد الدرجة للطالب {st_id_input} -> {status}")
                else:
                    st.error("كود الطالب غير صحيح")
            except:
                st.error("حدث خطأ، تأكد من الكود")

    st.divider()
    st.subheader("سجل الدرجات التي قمت برصدها")
    ws_grades = sheet.worksheet("Grades")
    df = pd.DataFrame(ws_grades.get_all_records())
    
    # فلترة النتائج الخاصة بهذا المعلم فقط
    if not df.empty:
        # تحويل TeacherID لسترينج
        df['TeacherID'] = df['TeacherID'].astype(str)
        my_logs = df[df['TeacherID'] == str(data[0])]
        st.dataframe(my_logs)
