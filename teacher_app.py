import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="بوابة المعلم", page_icon="👨‍🏫")

# --- دالة الاتصال ---
def get_database():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("❌ خطأ في الإعدادات: لم يتم العثور على مفتاح الخدمة.")
            st.stop()
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        return client.open("School_System")
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بقاعدة البيانات. (الخطأ: {e})")
        st.stop()

# --- تسجيل الدخول ---
if 'teacher_logged_in' not in st.session_state:
    st.session_state['teacher_logged_in'] = False

if not st.session_state['teacher_logged_in']:
    st.title("🔐 دخول المعلمين")
    with st.form("tech_login"):
        t_code = st.text_input("كود المعلم").strip()
        t_pass = st.text_input("الباسوورد", type="password").strip()
        btn = st.form_submit_button("دخول")
        
        if btn:
            sheet = get_database()
            ws = sheet.worksheet("Teachers")
            
            try:
                cell = ws.find(t_code)
                if cell:
                    row_vals = ws.row_values(cell.row)
                    real_pass = row_vals[5]
                    
                    if t_pass == real_pass:
                        st.session_state['teacher_logged_in'] = True
                        st.session_state['teacher_data'] = row_vals
                        st.session_state['teacher_id'] = t_code
                        st.rerun()
                    else:
                        st.error("بيانات خاطئة")
                else:
                    st.error("الكود غير موجود")
            except Exception:
                st.error("حدث خطأ أثناء محاولة البحث.")

# --- لوحة التحكم ---
else:
    data = st.session_state['teacher_data']
    t_id = st.session_state['teacher_id']
    
    st.title(f"أهلاً بك أستاذ/ة {data[1]} 👋")
    st.info(f"المادة: {data[2]} | الصف: {data[3]} | الترم: {data[4]}")
    
    st.divider()
    
    st.header("📝 رصد الدرجات للطلاب")
    
    sheet = get_database()
    
    with st.form("grading_form"):
        st_id_input = st.text_input("كود الطالب").strip()
        
        # --- تعديل مدخلات الدرجات لضمان دقة حالة النجاح والرسوب ---
        score = st.number_input(f"الدرجة التي حصل عليها الطالب", min_value=0, step=1)
        max_score = st.number_input("الدرجة الكلية للامتحان/الواجب", min_value=1, value=50, step=1)
        # هنا يتم تحديد الحد الأدنى المطلوب للنجاح
        pass_mark = st.number_input("الحد الأدنى لدرجة النجاح", min_value=0, max_value=max_score, value=int(max_score * 0.6), step=1)
        
        submit_grade = st.form_submit_button("رصد الدرجة")
        
        if submit_grade and st_id_input:
            if score > max_score:
                st.error(f"الدرجة المُدخلة ({score}) لا يجب أن تتجاوز الدرجة الكلية ({max_score}).")
                st.stop()
                
            ws_students = sheet.worksheet("Students")
            try:
                st_found = ws_students.find(st_id_input)
                if st_found:
                    # منطق النجاح: إذا كانت درجة الطالب أكبر من أو تساوي درجة النجاح المطلوبة
                    status = "ناجح" if score >= pass_mark else "راسب"
                    
                    ws_grades = sheet.worksheet("Grades")
                    # Grades: StudentID, TeacherID, Subject, Score, Status, Date
                    ws_grades.append_row([
                        st_id_input,
                        t_id, 
                        data[2], 
                        f"{score}/{max_score}", # لحفظ الدرجة الكلية مع درجة الطالب
                        status,
                        str(datetime.now().date())
                    ])
                    st.success(f"✅ تم رصد الدرجة للطالب **{st_id_input}** في مادة {data[2]}. حالة الطالب: **{status}**")
                else:
                    st.error("❌ كود الطالب غير صحيح أو غير مسجل في النظام.")
            except Exception:
                st.error("حدث خطأ أثناء محاولة رصد الدرجة.")

    st.divider()
    st.subheader("سجل الدرجات التي قمت برصدها مؤخراً")
    
    @st.cache_data(ttl=5) # تحديث البيانات كل 5 ثواني
    def get_teacher_logs(t_id_val):
        ws_grades = sheet.worksheet("Grades")
        df = pd.DataFrame(ws_grades.get_all_records())
        if not df.empty:
            return df[df['TeacherID'].astype(str) == t_id_val].sort_values(by='Date', ascending=False)
        return pd.DataFrame()

    my_logs = get_teacher_logs(t_id)
    if not my_logs.empty:
        st.dataframe(my_logs)
    else:
        st.info("لم تقم برصد أي درجات بعد.")
