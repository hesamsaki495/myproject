import streamlit as st
import requests
import pandas as pd
import re

# تنظیمات صفحه
st.set_page_config(page_title="سامانه مدیریت دانشگاه", layout="centered")
st.markdown("""
    <style>
    body {
        direction: rtl;
        font-family: 'Vazir', sans-serif;
    }
    .stButton>button {
        width: 100%;
    }
    .stTextInput>div>input, .stTextArea>div>textarea {
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# تنظیمات API
BASE_URL = "http://nginx/api"

# مقادیر مجاز
VALID_DEPARTMENTS = ["علوم پایه", "کشاورزی", "اقتصاد", "فنی و مهندسی"]
VALID_CITIES = ["تهران", "اصفهان", "مشهد", "شیراز", "تبریز", "کرمان", "اهواز", "کرج", "رشت", "یزد", "ارومیه",
                "قم", "ساری", "بندرعباس", "زاهدان", "سنندج", "قزوین", "بوشهر", "خرم آباد", "اردبیل", "همدان",
                "گرگان", "ایلام", "یاسوج", "بجنورد", "زنجان"]
VALID_MAJORS = {
    "فنی و مهندسی": ["مهندسی برق", "مهندسی کامپیوتر", "مهندسی عمران", "مهندسی پلیمر", "مهندسی مکانیک", "مهندسی معدن"],
    "کشاورزی": ["باغبانی", "مهندسی کشاورزی", "علوم دام"],
    "اقتصاد": ["حسابداری", "مدیریت", "مدیریت مالی", "مدیریت بازرگانی"],
    "علوم پایه": ["شیمی", "زمین شناسی", "علوم کامپیوتر", "ریاضی", "فیزیک"]
}

# توابع اعتبارسنجی
def validate_persian_name(name, field_name):
    if len(name) > 10:
        return f"❌ {field_name} نباید بیشتر از ۱۰ کاراکتر باشد."
    if not re.fullmatch(r"^[آ-ی\s]+$", name):
        return f"❌ {field_name} باید فقط شامل حروف فارسی باشد."
    return None

def validate_birth_date(birth):
    if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", birth):
        return "❌ تاریخ تولد باید به صورت YYYY/MM/DD باشد."
    try:
        year, month, day = map(int, birth.split("/"))
        if not (1300 <= year <= 1404):
            return "❌ سال تولد باید بین 1300 تا 1404 باشد."
        if not (1 <= month <= 12):
            return "❌ ماه تولد باید بین 1 تا 12 باشد."
        if month <= 6 and not (1 <= day <= 31):
            return "❌ برای ماه‌های ۱ تا ۶، روز باید بین 1 تا 31 باشد."
        elif month > 6 and not (1 <= day <= 30):
            return "❌ برای ماه‌های ۷ تا ۱۲، روز باید بین 1 تا 30 باشد."
    except ValueError:
        return "❌ تاریخ تولد نامعتبر است."
    return None

def validate_national_id(id_code):
    if not re.fullmatch(r"\d{10}", id_code):
        return "❌ کد ملی باید ۱۰ رقمی و فقط عدد باشد."
    if len(set(id_code)) == 1:
        return "❌ کد ملی معتبر نیست."
    check = sum(int(id_code[i]) * (10 - i) for i in range(9)) % 11
    last_digit = int(id_code[9])
    if (check < 2 and last_digit != check) or (check >= 2 and last_digit != (11 - check)):
        return "❌ کد ملی معتبر نیست."
    return None

def validate_student_inputs(data):
    errors = []
    if not re.fullmatch(r"\d{3}114150\d{2}", data["STID"]):
        errors.append("❌ شماره دانشجویی باید مانند 40311415001 باشد.")
    if error := validate_persian_name(data["Fname"], "نام"):
        errors.append(error)
    if error := validate_persian_name(data["Lname"], "نام خانوادگی"):
        errors.append(error)
    if error := validate_persian_name(data["Father"], "نام پدر"):
        errors.append(error)
    if not re.fullmatch(r"\d{6}[آ-ی]\d{2}", data["ids"]):
        errors.append("❌ شماره شناسنامه باید شامل عدد ۶ رقمی، یک حرف فارسی و عدد ۲ رقمی باشد.")
    if data["Borncity"] not in VALID_CITIES:
        errors.append("❌ محل تولد باید یکی از مراکز استان باشد.")
    if error := validate_birth_date(data["BIRTH"]):
        errors.append(error)
    if len(data["Address"]) > 100:
        errors.append("❌ آدرس نباید بیشتر از ۱۰۰ کاراکتر باشد.")
    if not re.fullmatch(r"\d{10}", data["Postalcode"]):
        errors.append("❌ کد پستی باید ۱۰ رقمی باشد.")
    if not re.fullmatch(r"98\d{10}", data["Cphone"]):
        errors.append("❌ شماره موبایل باید با 98 شروع شده و ۱۲ رقمی باشد.")
    if not re.fullmatch(r"0\d{2,3}\d{8}", data["Hphone"]):
        errors.append("❌ شماره تلفن ثابت معتبر نیست.")
    if data["Department"] not in VALID_DEPARTMENTS:
        errors.append("❌ دانشکده معتبر نیست.")
    if data["Major"] not in VALID_MAJORS[data["Department"]]:
        errors.append("❌ رشته با دانشکده مطابقت ندارد.")
    if data["Married"] not in ["مجرد", "متاهل"]:
        errors.append("❌ وضعیت تأهل فقط می‌تواند مجرد یا متاهل باشد.")
    if error := validate_national_id(data["Id"]):
        errors.append(error)
    return errors

def validate_professor_inputs(data):
    errors = []
    if not re.fullmatch(r"\d{6}", data["LID"]):
        errors.append("❌ کد استاد باید یک عدد ۶ رقمی باشد.")
    if error := validate_persian_name(data["Fname"], "نام"):
        errors.append(error)
    if error := validate_persian_name(data["Lname"], "نام خانوادگی"):
        errors.append(error)
    if data["Department"] not in VALID_DEPARTMENTS:
        errors.append("❌ دانشکده معتبر نیست.")
    if data["Major"] not in VALID_MAJORS[data["Department"]]:
        errors.append("❌ رشته با دانشکده مطابقت ندارد.")
    if data["Borncity"] not in VALID_CITIES:
        errors.append("❌ محل تولد باید یکی از مراکز استان باشد.")
    if error := validate_birth_date(data["Birth"]):
        errors.append(error)
    if len(data["Address"]) > 100:
        errors.append("❌ آدرس نباید بیشتر از ۱۰۰ کاراکتر باشد.")
    if not re.fullmatch(r"\d{10}", data["Postalcode"]):
        errors.append("❌ کد پستی باید ۱۰ رقمی باشد.")
    if not re.fullmatch(r"98\d{10}", data["Cphone"]):
        errors.append("❌ شماره موبایل باید با 98 شروع شده و ۱۲ رقمی باشد.")
    if not re.fullmatch(r"0\d{2,3}\d{8}", data["Hphone"]):
        errors.append("❌ شماره تلفن ثابت معتبر نیست.")
    return errors

def validate_course_inputs(data):
    errors = []
    if not data["CID"].isdigit() or not (10000 <= int(data["CID"]) <= 99999):
        errors.append("❌ کد درس باید یک عدد ۵ رقمی باشد.")
    if len(data["CName"]) > 25:
        errors.append("❌ نام درس نباید بیشتر از ۲۵ کاراکتر باشد.")
    if not re.fullmatch(r"^[آ-ی\s]+$", data["CName"]):
        errors.append("❌ نام درس باید فقط شامل حروف فارسی باشد.")
    if data["Department"] not in VALID_DEPARTMENTS:
        errors.append("❌ دانشکده معتبر نیست.")
    if data["Credit"] not in ["1","2","3","4"]:
        errors.append("❌ تعداد واحد باید بین ۱ تا ۴ باشد.")
    return errors

# منوی کناری
st.sidebar.title("🎓 سامانه مدیریت دانشگاه")
menu = st.sidebar.selectbox("انتخاب عملیات", [
    "افزودن دانشجو", "نمایش همه دانشجویان", "جستجو با شماره دانشجویی", "ویرایش دانشجو", "حذف دانشجو",
    "افزودن استاد", "نمایش همه اساتید", "جستجو با کد استاد", "ویرایش استاد", "حذف استاد",
    "افزودن درس", "نمایش همه دروس", "جستجو با کد درس", "ویرایش درس", "حذف درس"
])

# توابع دریافت داده‌ها
def get_all_students():
    try:
        res = requests.get(f"{BASE_URL}/students/")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ خطا در دریافت داده‌ها: {e}")
        return []

def get_all_professors():
    try:
        res = requests.get(f"{BASE_URL}/professors/")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ خطا در دریافت داده‌ها: {e}")
        return []

def get_all_courses():
    try:
        res = requests.get(f"{BASE_URL}/courses/")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ خطا در دریافت داده‌ها: {e}")
        return []

# عملیات CRUD برای دانشجویان
if menu == "افزودن دانشجو":
    st.subheader("➕ افزودن دانشجو")
    data = {
        "STID": st.text_input("شماره دانشجویی", help="مانند 40311415001"),
        "Fname": st.text_input("نام"),
        "Lname": st.text_input("نام خانوادگی"),
        "Father": st.text_input("نام پدر"),
        "ids": st.text_input("شماره شناسنامه", help="۶ رقم، یک حرف فارسی، ۲ رقم"),
        "BIRTH": st.text_input("تاریخ تولد (YYYY/MM/DD)"),
        "Address": st.text_area("آدرس"),
        "Postalcode": st.text_input("کد پستی", help="۱۰ رقم"),
        "Cphone": st.text_input("شماره موبایل", help="مثال: 989121234567"),
        "Hphone": st.text_input("شماره تلفن ثابت", help="کد شهر + ۸ رقم"),
        "Id": st.text_input("کد ملی", help="۱۰ رقم"),
        "Borncity": st.selectbox("محل تولد", VALID_CITIES),
        "Department": st.selectbox("دانشکده", VALID_DEPARTMENTS),
    }
    data["Major"] = st.selectbox("رشته", VALID_MAJORS[data["Department"]])
    data["Married"] = st.selectbox("وضعیت تأهل", ["مجرد", "متاهل"])

    if st.button("ثبت"):
        errors = validate_student_inputs(data)
        if errors:
            for error in errors:
                st.warning(error)
        else:
            try:
                res = requests.post(f"{BASE_URL}/students/", json=data)
                res.raise_for_status()
                st.success("✅ دانشجو با موفقیت افزوده شد.")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 500:
                    st.error(f"❌ دانشجویی با شماره دانشجویی {data['STID']} قبلاً ثبت شده است.")
                else:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا در ارتباط با سرور: {e}")

elif menu == "نمایش همه دانشجویان":
    st.subheader("📋 لیست دانشجویان")
    data = get_all_students()
    if data:
        df = pd.DataFrame(data).sort_values(by="STID")
        df = df.rename(columns={
            "STID": "شماره دانشجویی",
            "Fname": "نام",
            "Lname": "نام خانوادگی",
            "Father": "نام پدر",
            "ids": "شماره شناسنامه",
            "BIRTH": "تاریخ تولد",
            "Id": "کد ملی",
            "Address": "آدرس",
            "Postalcode": "کد پستی",
            "Cphone": "شماره موبایل",
            "Hphone": "تلفن ثابت",
            "Borncity": "محل تولد",
            "Department": "دانشکده",
            "Major": "رشته",
            "Married": "وضعیت تأهل"
        })
        st.dataframe(
            df[["شماره دانشجویی", "نام", "نام خانوادگی", "نام پدر", "شماره شناسنامه", 
                "تاریخ تولد", "کد ملی", "آدرس", "کد پستی", "شماره موبایل", 
                "تلفن ثابت", "محل تولد", "دانشکده", "رشته", "وضعیت تأهل"]],
            use_container_width=True
        )
    else:
        st.info("هیچ دانشجویی ثبت نشده است.")

elif menu == "جستجو با شماره دانشجویی":
    st.subheader("🔍 جستجو دانشجو با شماره")
    stid = st.text_input("شماره دانشجویی")
    if st.button("جستجو"):
        if stid:
            try:
                res = requests.get(f"{BASE_URL}/students/{stid}")
                res.raise_for_status()
                student = res.json()
                df = pd.DataFrame([student])
                df = df.rename(columns={
                    "STID": "شماره دانشجویی",
                    "Fname": "نام",
                    "Lname": "نام خانوادگی",
                    "Father": "نام پدر",
                    "ids": "شماره شناسنامه",
                    "BIRTH": "تاریخ تولد",
                    "Id": "کد ملی",
                    "Address": "آدرس",
                    "Postalcode": "کد پستی",
                    "Cphone": "شماره موبایل",
                    "Hphone": "تلفن ثابت",
                    "Borncity": "محل تولد",
                    "Department": "دانشکده",
                    "Major": "رشته",
                    "Married": "وضعیت تأهل"
                })
                st.dataframe(
                    df[["شماره دانشجویی", "نام", "نام خانوادگی", "نام پدر", "شماره شناسنامه", 
                        "تاریخ تولد", "کد ملی", "آدرس", "کد پستی", "شماره موبایل", 
                        "تلفن ثابت", "محل تولد", "دانشکده", "رشته", "وضعیت تأهل"]],
                    use_container_width=True
                )
                st.markdown(f"""
                ### اطلاعات دانشجو
                - **شماره دانشجویی**: {student['STID']}
                - **نام**: {student['Fname']}
                - **نام خانوادگی**: {student['Lname']}
                - **نام پدر**: {student['Father']}
                - **شماره شناسنامه**: {student['ids']}
                - **تاریخ تولد**: {student['BIRTH']}
                - **کد ملی**: {student['Id']}
                - **آدرس**: {student['Address']}
                - **کد پستی**: {student['Postalcode']}
                - **شماره موبایل**: {student['Cphone']}
                - **تلفن ثابت**: {student['Hphone']}
                - **محل تولد**: {student['Borncity']}
                - **دانشکده**: {student['Department']}
                - **رشته**: {student['Major']}
                - **وضعیت تأهل**: {student['Married']}
                """)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    st.error("❌ دانشجویی با این شماره دانشجویی یافت نشد.")
                else:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا در ارتباط با سرور: {e}")
        else:
            st.warning("❌ لطفاً شماره دانشجویی را وارد کنید.")

elif menu == "ویرایش دانشجو":
    st.subheader("✏️ ویرایش اطلاعات دانشجو")
    data = get_all_students()
    if not data:
        st.info("فعلاً هیچ دانشجویی ثبت نشده است.")
    else:
        options = [f"{s['STID']} - {s['Fname']} {s['Lname']}" for s in data]
        selected = st.selectbox("یک دانشجو را انتخاب کنید", options)
        student = next(s for s in data if f"{s['STID']} - {s['Fname']} {s['Lname']}" == selected)
        updated = student.copy()

        updated["STID"] = st.text_input("شماره دانشجویی", updated["STID"])
        updated["Fname"] = st.text_input("نام", updated["Fname"])
        updated["Lname"] = st.text_input("نام خانوادگی", updated["Lname"])
        updated["Father"] = st.text_input("نام پدر", updated["Father"])
        updated["ids"] = st.text_input("شماره شناسنامه", updated["ids"])
        updated["BIRTH"] = st.text_input("تاریخ تولد (YYYY/MM/DD)", updated["BIRTH"])
        updated["Address"] = st.text_area("آدرس", updated["Address"])
        updated["Postalcode"] = st.text_input("کد پستی", updated["Postalcode"])
        updated["Cphone"] = st.text_input("شماره موبایل", updated["Cphone"])
        updated["Hphone"] = st.text_input("شماره تلفن ثابت", updated["Hphone"])
        updated["Id"] = st.text_input("کد ملی", updated["Id"])
        updated["Borncity"] = st.selectbox("محل تولد", VALID_CITIES, index=VALID_CITIES.index(updated["Borncity"]) if updated["Borncity"] in VALID_CITIES else 0)
        updated["Department"] = st.selectbox("دانشکده", VALID_DEPARTMENTS, index=VALID_DEPARTMENTS.index(updated["Department"]) if updated["Department"] in VALID_DEPARTMENTS else 0)
        updated["Major"] = st.selectbox("رشته", VALID_MAJORS[updated["Department"]], index=VALID_MAJORS[updated["Department"]].index(updated["Major"]) if updated["Major"] in VALID_MAJORS[updated["Department"]] else 0)
        updated["Married"] = st.selectbox("وضعیت تأهل", ["مجرد", "متاهل"], index=["مجرد", "متاهل"].index(updated["Married"]) if updated["Married"] in ["مجرد", "متاهل"] else 0)

        if st.button("ثبت تغییرات"):
            errors = validate_student_inputs(updated)
            if errors:
                for error in errors:
                    st.warning(error)
            else:
                try:
                    res = requests.put(f"{BASE_URL}/students/{student['STID']}", json=updated)
                    res.raise_for_status()
                    st.success("✅ اطلاعات دانشجو با موفقیت ویرایش شد.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")

elif menu == "حذف دانشجو":
    st.subheader("🗑️ حذف دانشجو")
    data = get_all_students()
    if not data:
        st.info("فعلاً هیچ دانشجویی ثبت نشده است.")
    else:
        options = [f"{s['STID']} - {s['Fname']} {s['Lname']}" for s in data]
        selected = st.selectbox("یک دانشجو را برای حذف انتخاب کنید", options)
        student = next(s for s in data if f"{s['STID']} - {s['Fname']} {s['Lname']}" == selected)
        if st.button("حذف"):
            try:
                res = requests.delete(f"{BASE_URL}/students/{student['STID']}")
                res.raise_for_status()
                st.success("✅ دانشجو حذف شد.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")

# عملیات CRUD برای اساتید
elif menu == "افزودن استاد":
    st.subheader("➕ افزودن استاد")
    data = {
        "LID": st.text_input("کد استاد", help="۶ رقم"),
        "Fname": st.text_input("نام"),
        "Lname": st.text_input("نام خانوادگی"),
        "Department": st.selectbox("دانشکده", VALID_DEPARTMENTS),
        "Major": None,
        "Borncity": st.selectbox("محل تولد", VALID_CITIES),
        "Birth": st.text_input("تاریخ تولد (YYYY/MM/DD)"),
        "Address": st.text_area("آدرس"),
        "Postalcode": st.text_input("کد پستی", help="۱۰ رقم"),
        "Cphone": st.text_input("شماره موبایل", help="مثال: 989121234567"),
        "Hphone": st.text_input("شماره تلفن ثابت", help="کد شهر + ۸ رقم")
    }
    data["Major"] = st.selectbox("رشته", VALID_MAJORS[data["Department"]])

    if st.button("ثبت"):
        errors = validate_professor_inputs(data)
        if errors:
            for error in errors:
                st.warning(error)
        else:
            try:
                res = requests.post(f"{BASE_URL}/professors/", json=data)
                res.raise_for_status()
                st.success("✅ استاد با موفقیت افزوده شد.")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 500:
                    st.error(f"❌ استادی با کد {data['LID']} قبلاً ثبت شده است.")
                else:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا در ارتباط با سرور: {e}")

elif menu == "نمایش همه اساتید":
    st.subheader("📋 لیست اساتید")
    data = get_all_professors()
    if data:
        df = pd.DataFrame(data).sort_values(by="LID")
        df = df.rename(columns={
            "LID": "کد استاد",
            "Fname": "نام",
            "Lname": "نام خانوادگی",
            "Department": "دانشکده",
            "Major": "رشته",
            "Borncity": "محل تولد",
            "Birth": "تاریخ تولد",
            "Address": "آدرس",
            "Postalcode": "کد پستی",
            "Cphone": "شماره موبایل",
            "Hphone": "تلفن ثابت"
        })
        st.dataframe(
            df[["کد استاد", "نام", "نام خانوادگی", "دانشکده", "رشته", "محل تولد", 
                "تاریخ تولد", "آدرس", "کد پستی", "شماره موبایل", "تلفن ثابت"]],
            use_container_width=True
        )
    else:
        st.info("هیچ استادی ثبت نشده است.")

elif menu == "جستجو با کد استاد":
    st.subheader("🔍 جستجو استاد با کد")
    lid = st.text_input("کد استاد")
    if st.button("جستجو"):
        if lid:
            try:
                res = requests.get(f"{BASE_URL}/professors/{lid}")
                res.raise_for_status()
                professor = res.json()
                df = pd.DataFrame([professor])
                df = df.rename(columns={
                    "LID": "کد استاد",
                    "Fname": "نام",
                    "Lname": "نام خانوادگی",
                    "Department": "دانشکده",
                    "Major": "رشته",
                    "Borncity": "محل تولد",
                    "Birth": "تاریخ تولد",
                    "Address": "آدرس",
                    "Postalcode": "کد پستی",
                    "Cphone": "شماره موبایل",
                    "Hphone": "تلفن ثابت"
                })
                st.dataframe(
                    df[["کد استاد", "نام", "نام خانوادگی", "دانشکده", "رشته", "محل تولد", 
                        "تاریخ تولد", "آدرس", "کد پستی", "شماره موبایل", "تلفن ثابت"]],
                    use_container_width=True
                )
                st.markdown(f"""
                ### اطلاعات استاد
                - **کد استاد**: {professor['LID']}
                - **نام**: {professor['Fname']}
                - **نام خانوادگی**: {professor['Lname']}
                - **دانشکده**: {professor['Department']}
                - **رشته**: {professor['Major']}
                - **محل تولد**: {professor['Borncity']}
                - **تاریخ تولد**: {professor['Birth']}
                - **آدرس**: {professor['Address']}
                - **کد پستی**: {professor['Postalcode']}
                - **شماره موبایل**: {professor['Cphone']}
                - **تلفن ثابت**: {professor['Hphone']}
                """)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    st.error("❌ استادی با این کد یافت نشد.")
                else:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا در ارتباط با سرور: {e}")
        else:
            st.warning("❌ لطفاً کد استاد را وارد کنید.")

elif menu == "ویرایش استاد":
    st.subheader("✏️ ویرایش اطلاعات استاد")
    data = get_all_professors()
    if not data:
        st.info("فعلاً هیچ استادی ثبت نشده است.")
    else:
        options = [f"{p['LID']} - {p['Fname']} {p['Lname']}" for p in data]
        selected = st.selectbox("یک استاد را انتخاب کنید", options)
        professor = next(p for p in data if f"{p['LID']} - {p['Fname']} {p['Lname']}" == selected)
        updated = professor.copy()

        updated["LID"] = st.text_input("کد استاد", updated["LID"])
        updated["Fname"] = st.text_input("نام", updated["Fname"])
        updated["Lname"] = st.text_input("نام خانوادگی", updated["Lname"])
        updated["Department"] = st.selectbox("دانشکده", VALID_DEPARTMENTS, index=VALID_DEPARTMENTS.index(updated["Department"]) if updated["Department"] in VALID_DEPARTMENTS else 0)
        updated["Major"] = st.selectbox("رشته", VALID_MAJORS[updated["Department"]], index=VALID_MAJORS[updated["Department"]].index(updated["Major"]) if updated["Major"] in VALID_MAJORS[updated["Department"]] else 0)
        updated["Borncity"] = st.selectbox("محل تولد", VALID_CITIES, index=VALID_CITIES.index(updated["Borncity"]) if updated["Borncity"] in VALID_CITIES else 0)
        updated["Birth"] = st.text_input("تاریخ تولد (YYYY/MM/DD)", updated["Birth"])
        updated["Address"] = st.text_area("آدرس", updated["Address"])
        updated["Postalcode"] = st.text_input("کد پستی", updated["Postalcode"])
        updated["Cphone"] = st.text_input("شماره موبایل", updated["Cphone"])
        updated["Hphone"] = st.text_input("شماره تلفن ثابت", updated["Hphone"])

        if st.button("ثبت تغییرات"):
            errors = validate_professor_inputs(updated)
            if errors:
                for error in errors:
                    st.warning(error)
            else:
                try:
                    res = requests.put(f"{BASE_URL}/professors/{professor['LID']}", json=updated)
                    res.raise_for_status()
                    st.success("✅ اطلاعات استاد با موفقیت ویرایش شد.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")

elif menu == "حذف استاد":
    st.subheader("🗑️ حذف استاد")
    data = get_all_professors()
    if not data:
        st.info("فعلاً هیچ استادی ثبت نشده است.")
    else:
        options = [f"{p['LID']} - {p['Fname']} {p['Lname']}" for p in data]
        selected = st.selectbox("یک استاد را برای حذف انتخاب کنید", options)
        professor = next(p for p in data if f"{p['LID']} - {p['Fname']} {p['Lname']}" == selected)
        if st.button("حذف"):
            try:
                res = requests.delete(f"{BASE_URL}/professors/{professor['LID']}")
                res.raise_for_status()
                st.success("✅ استاد حذف شد.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")

# عملیات CRUD برای دروس
elif menu == "افزودن درس":
    st.subheader("➕ افزودن درس")
    data = {
        "CID": st.text_input("کد درس", help="۵ رقم"),
        "CName": st.text_input("نام درس"),
        "Department": st.selectbox("دانشکده", VALID_DEPARTMENTS),
        "Credit": st.selectbox("تعداد واحد", ["1","2","3","4"])
    }

    if st.button("ثبت"):
        errors = validate_course_inputs(data)
        if errors:
            for error in errors:
                st.warning(error)
        else:
            try:
                res = requests.post(f"{BASE_URL}/courses/", json=data)
                res.raise_for_status()
                st.success("✅ درس با موفقیت افزوده شد.")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 500:
                    st.error(f"❌ درسی با کد {data['CID']} قبلاً ثبت شده است.")
                else:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا در ارتباط با سرور: {e}")


elif menu == "نمایش همه دروس":
    st.subheader("📋 لیست دروس")
    data = get_all_courses()
    if data:
        df = pd.DataFrame(data).sort_values(by="CID")
        df = df.rename(columns={
            "CID": "کد درس",
            "CName": "نام درس",
            "Department": "دانشکده",
            "Credit": "تعداد واحد"
        })
        st.dataframe(
            df[["کد درس", "نام درس", "دانشکده", "تعداد واحد"]],
            use_container_width=True
        )
    else:
        st.info("هیچ درسی ثبت نشده است.")

elif menu == "جستجو با کد درس":
    st.subheader("🔍 جستجو درس با کد")
    cid = st.text_input("کد درس")
    if st.button("جستجو"):
        if cid:
            try:
                res = requests.get(f"{BASE_URL}/courses/{cid}")
                res.raise_for_status()
                course = res.json()
                df = pd.DataFrame([course])
                df = df.rename(columns={
                    "CID": "کد درس",
                    "CName": "نام درس",
                    "Department": "دانشکده",
                    "Credit": "تعداد واحد"
                })
                st.dataframe(
                    df[["کد درس", "نام درس", "دانشکده", "تعداد واحد"]],
                    use_container_width=True
                )
                st.markdown(f"""
                ### اطلاعات درس
                - **کد درس**: {course['CID']}
                - **نام درس**: {course['CName']}
                - **دانشکده**: {course['Department']}
                - **تعداد واحد**: {course['Credit']}
                """)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    st.error("❌ درسی با این کد یافت نشد.")
                else:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا در ارتباط با سرور: {e}")
        else:
            st.warning("❌ لطفاً کد درس را وارد کنید.")

elif menu == "ویرایش درس":
    st.subheader("✏️ ویرایش اطلاعات درس")
    data = get_all_courses()
    if not data:
        st.info("فعلاً هیچ درسی ثبت نشده است.")
    else:
        options = [f"{c['CID']} - {c['CName']}" for c in data]
        selected = st.selectbox("یک درس را انتخاب کنید", options)
        course = next(c for c in data if f"{c['CID']} - {c['CName']}" == selected)
        updated = course.copy()

        updated["CID"] = st.text_input("کد درس", updated["CID"])
        updated["CName"] = st.text_input("نام درس", updated["CName"])
        updated["Department"] = st.selectbox("دانشکده", VALID_DEPARTMENTS, index=VALID_DEPARTMENTS.index(updated["Department"]) if updated["Department"] in VALID_DEPARTMENTS else 0)
        updated["Credit"] = st.selectbox("تعداد واحد", ["1", "2", "3", "4"], index=["1", "2", "3", "4"].index(updated["Credit"]) if updated["Credit"] in ["1", "2", "3", "4"] else 0)

        if st.button("ثبت تغییرات"):
            errors = validate_course_inputs(updated)
            if errors:
                for error in errors:
                    st.warning(error)
            else:
                try:
                    res = requests.put(f"{BASE_URL}/courses/{course['CID']}", json=updated)
                    res.raise_for_status()
                    st.success("✅ اطلاعات درس با موفقیت ویرایش شد.")

                except requests.exceptions.RequestException as e:
                    st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")

elif menu == "حذف درس":
    st.subheader("🗑️ حذف درس")
    data = get_all_courses()
    if not data:
        st.info("فعلاً هیچ درسی ثبت نشده است.")
    else:
        options = [f"{c['CID']} - {c['CName']}" for c in data]
        selected = st.selectbox("یک درس را برای حذف انتخاب کنید", options)
        course = next(c for c in data if f"{c['CID']} - {c['CName']}" == selected)
        if st.button("حذف"):
            try:
                res = requests.delete(f"{BASE_URL}/courses/{course['CID']}")
                res.raise_for_status()
                st.success("✅ درس حذف شد.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ خطا: {e.response.json()['detail'] if e.response else e}")