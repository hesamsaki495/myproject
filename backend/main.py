from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel, field_validator
import re

# ----------------- مدل Pydantic -----------------

class StudentBase(BaseModel):
    STID: str
    Fname: str
    Lname: str
    ids: str
    Borncity: str
    Father: str
    BIRTH: str
    Address: str
    Postalcode: str
    Cphone: str
    Hphone: str
    Department: str
    Major: str
    Id: str
    Married: str

    @field_validator("STID")
    def validate_stid(cls, v):
        if not re.fullmatch(r"\d{3}114150\d{2}", v):
            raise ValueError("شماره دانشجویی باید یک عدد ۱۱ رقمی معتبر مانند 40311415001 باشد.")
        return v

    @field_validator("Fname", "Lname", "Father")
    def validate_persian_names(cls, v):
        if len(v) > 10:
            raise ValueError("نام‌ها نباید بیشتر از ۱۰ کاراکتر باشند.")
        if not re.fullmatch(r"^[آ-ی\s]+$", v):
            raise ValueError("نام باید فقط شامل حروف فارسی باشد.")
        return v

    @field_validator("BIRTH")
    def validate_birth(cls, v):
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", v):
            raise ValueError("تاریخ تولد باید در قالب YYYY/MM/DD وارد شود.")
        year, month, day = map(int, v.split("/"))
        if not (1300 <= year <= 1404):
            raise ValueError("سال باید بین 1300 تا 1404 باشد.")
        if not (1 <= month <= 12):
            raise ValueError("ماه باید بین 1 تا 12 باشد.")
        if month <= 6 and not (1 <= day <= 31):
            raise ValueError("روز باید بین 1 تا 31 باشد.")
        elif month > 6 and not (1 <= day <= 30):
            raise ValueError("روز باید بین 1 تا 30 باشد.")
        return v

    @field_validator("ids")
    def validate_ids(cls, v):
        if not re.fullmatch(r"\d{6}[آ-ی]\d{2}", v):
            raise ValueError("شناسه باید شامل عدد ۶ رقمی، یک حرف فارسی، و عدد ۲ رقمی باشد.")
        return v

    @field_validator("Borncity")
    def validate_borncity(cls, v):
        provinces = ["تهران", "اصفهان", "مشهد", "شیراز", "تبریز", "کرمان", "اهواز", "کرج", "رشت", "یزد", "ارومیه",
                     "قم", "ساری", "بندرعباس", "زاهدان", "سنندج", "قزوین", "بوشهر","خرم آباد", "اردبیل", "همدان",
                     "گرگان", "ایلام", "یاسوج", "بجنورد", "زنجان"]
        if v not in provinces:
            raise ValueError("محل تولد باید یکی از مراکز استان کشور باشد.")
        return v

    @field_validator("Address")
    def validate_address(cls, v):
        if len(v) > 100:
            raise ValueError("آدرس نباید بیشتر از ۱۰۰ کاراکتر باشد.")
        return v

    @field_validator("Postalcode")
    def validate_postalcode(cls, v):
        if not re.fullmatch(r"\d{10}", v):
            raise ValueError("کد پستی باید یک عدد ۱۰ رقمی باشد.")
        return v

    @field_validator("Cphone")
    def validate_cphone(cls, v):
        if not re.fullmatch(r"98\d{10}", v):
            raise ValueError(".شماره موبایل باید با 98 شروع شود و بجز 98 شامل 10 رقم عددی باشد")
        return v

    @field_validator("Hphone")
    def validate_hphone(cls, v):
        if not re.fullmatch(r"0\d{2,3}\d{8}", v):
            raise ValueError("شماره تلفن ثابت باید با 0 شروع شود و شامل کد شهر (۲ یا ۳ رقمی) و شماره ۸ رقمی باشد.")
        return v

    @field_validator("Department")
    def validate_department(cls, v):
        valid_departments = ["علوم پایه","کشاورزی", "اقتصاد", "فنی و مهندسی"]
        if v not in valid_departments:
            raise ValueError("دانشکده باید یکی از موارد کشاورزی، اقتصاد، فنی و مهندسی ، علوم پایه باشد.")
        return v

    @field_validator("Major")
    def validate_major(cls, v, info):
        department = info.data.get("Department")
        if department == "فنی و مهندسی":
            valid_majors = ["مهندسی برق","مهندسی کامپیوتر", "مهندسی عمران", "مهندسی پلیمر", "مهندسی مکانیک", "مهندسی معدن"]
        elif department == "کشاورزی":
            valid_majors = ["باغبانی", "مهندسی کشاورزی", "علوم دام"]
        elif department == "اقتصاد":
            valid_majors = ["حسابداری", "مدیریت", "مدیریت مالی", "مدیریت بازرگانی"]
        elif department=="علوم پایه":
            valid_majors=["شیمی","زمین شناسی","علوم کامپیوتر","ریاضی","فیزیک"]
        else:
            raise ValueError("لطفاً ابتدا دانشکده معتبری وارد کنید.")
        if v not in valid_majors:
            raise ValueError(f"رشته وارد شده با دانشکده انتخاب‌شده مطابقت ندارد. رشته‌های مجاز: {', '.join(valid_majors)}")
        return v

    @field_validator("Married")
    def validate_married(cls, v):
        if v not in ["مجرد", "متاهل"]:
            raise ValueError("وضعیت تأهل فقط می‌تواند مجرد یا متاهل باشد.")
        return v

    @field_validator("Id")
    def validate_national_id(cls, v):
        if not re.fullmatch(r"\d{10}", v):
            raise ValueError("کد ملی باید ۱۰ رقمی باشد.")
        check = sum(int(v[i]) * (10 - i) for i in range(9)) % 11
        last_digit = int(v[9])
        if (check < 2 and last_digit != check) or (check >= 2 and last_digit != (11 - check)):
            raise ValueError("کد ملی نامعتبر است.")
        return v


class Student(SQLModel, table=True):
    STID: str = Field(primary_key=True, index=True)
    Fname: str
    Lname: str
    ids: str
    Borncity: str
    Father: str
    BIRTH: str
    Address: str
    Postalcode: str
    Cphone: str
    Hphone: str
    Department: str
    Major: str
    Id: str
    Married: str

class ProfessorBase(BaseModel):
    LID: str
    Fname: str
    Lname: str
    Department: str
    Major: str
    Borncity: str
    Birth: str
    Address: str
    Postalcode: str
    Cphone: str
    Hphone: str

    @field_validator("LID")
    def validate_lid(cls, v):
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("کد استاد باید یک عدد ۶ رقمی باشد.")
        return v

    @field_validator("Fname", "Lname")
    def validate_persian_names(cls, v):
        if len(v) > 10:
            raise ValueError("نام‌ها نباید بیشتر از ۱۰ کاراکتر باشند.")
        if not re.fullmatch(r"^[آ-ی\s]+$", v):
            raise ValueError("نام باید فقط شامل حروف فارسی باشد.")
        return v

    @field_validator("Department")
    def validate_department(cls, v):
        valid_departments = ["علوم پایه","کشاورزی", "اقتصاد", "فنی و مهندسی"]
        if v not in valid_departments:
            raise ValueError("دانشکده باید یکی از موارد کشاورزی، اقتصاد، فنی و مهندسی ، علوم پایه باشد.")
        return v

    @field_validator("Major")
    def validate_major(cls, v, info):
        department = info.data.get("Department")
        if department == "فنی و مهندسی":
            valid_majors = ["مهندسی برق","مهندسی کامپیوتر", "مهندسی عمران", "مهندسی پلیمر", "مهندسی مکانیک", "مهندسی معدن"]
        elif department == "کشاورزی":
            valid_majors = ["باغبانی", "مهندسی کشاورزی", "علوم دام"]
        elif department == "اقتصاد":
            valid_majors = ["حسابداری", "مدیریت", "مدیریت مالی", "مدیریت بازرگانی"]
        elif department=="علوم پایه":
            valid_majors=["علوم کامپیوتر","شیمی","زمین شناسی","فیزیک","ریاضی"]
        else:
            raise ValueError("لطفاً ابتدا دانشکده معتبری وارد کنید.")

        if v not in valid_majors:
            raise ValueError(f"رشته وارد شده با دانشکده انتخاب‌شده مطابقت ندارد. رشته‌های مجاز: {', '.join(valid_majors)}")
        return v

    @field_validator("Borncity")
    def validate_borncity(cls, v):
        provinces = ["تهران", "اصفهان", "مشهد", "شیراز", "تبریز", "کرمان", "اهواز", "کرج", "رشت", "یزد", "ارومیه",
                     "قم", "ساری", "بندرعباس", "زاهدان", "سنندج", "قزوین", "بوشهر","خرم آباد", "اردبیل", "همدان",
                     "گرگان", "ایلام", "یاسوج", "بجنورد", "زنجان"]
        if v not in provinces:
            raise ValueError("محل تولد باید یکی از مراکز استان کشور باشد.")
        return v

    @field_validator("Birth")
    def validate_birth(cls, v):
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", v):
            raise ValueError("تاریخ تولد باید در قالب YYYY/MM/DD وارد شود.")
        year, month, day = map(int, v.split("/"))
        if not (1300 <= year <= 1404):
            raise ValueError("سال باید بین 1300 تا 1404 باشد.")
        if not (1 <= month <= 12):
            raise ValueError("ماه باید بین 1 تا 12 باشد.")
        if month <= 6 and not (1 <= day <= 31):
            raise ValueError("روز باید بین 1 تا 31 باشد.")
        elif month > 6 and not (1 <= day <= 30):
            raise ValueError("روز باید بین 1 تا 30 باشد.")
        return v

    @field_validator("Address")
    def validate_address(cls, v):
        if len(v) > 100:
            raise ValueError("آدرس نباید بیشتر از ۱۰۰ کاراکتر باشد.")
        return v

    @field_validator("Postalcode")
    def validate_postalcode(cls, v):
        if not re.fullmatch(r"\d{10}", v):
            raise ValueError("کد پستی باید یک عدد ۱۰ رقمی باشد.")
        return v

    @field_validator("Cphone")
    def validate_cphone(cls, v):
        if not re.fullmatch(r"98\d{10}", v):
            raise ValueError(".شماره موبایل باید با 98 شروع شود و بجز 98 شامل 10 رقم عددی باشد")
        return v

    @field_validator("Hphone")
    def validate_hphone(cls, v):
        if not re.fullmatch(r"0\d{2,3}\d{8}", v):
            raise ValueError("شماره تلفن ثابت باید با 0 شروع شود و شامل کد شهر (۲ یا ۳ رقمی) و شماره ۸ رقمی باشد.")
        return v
    

class Professor(SQLModel, table=True):
    LID: str = Field(index=True, primary_key=True)
    Fname: str
    Lname: str
    Department: str
    Major: str
    Borncity: str
    Birth: str
    Address: str
    Postalcode: str
    Cphone: str
    Hphone: str
VALID_DEPARTMENTS = ["علوم پایه","کشاورزی", "اقتصاد", "فنی و مهندسی"]

# --------- اعتبارسنجی داده‌ها با Pydantic ---------
class CourseBase(BaseModel):
    CID: str
    CName: str
    Department: str
    Credit: str

    @field_validator("CID")
    def validate_cid(cls, v):
        if not v.isdigit():
            raise ValueError("کد درس باید فقط شامل ارقام باشد.")
        cid = int(v)
        if not (10000 <= cid <= 99999):
            raise ValueError("کد درس باید یک عدد ۵ رقمی باشد.")
        return v

    @field_validator("CName")
    def validate_cname(cls, v):
        if len(v) > 25:
            raise ValueError("نام درس نباید بیشتر از ۲۵ کاراکتر باشد.")
        if not re.fullmatch(r"^[آ-ی\s]+$", v):
            raise ValueError("نام درس باید فقط شامل حروف فارسی باشد.")
        return v

    @field_validator("Department")
    def validate_department(cls, v):
        if v not in VALID_DEPARTMENTS:
            raise ValueError("دانشکده باید یکی از موارد کشاورزی، اقتصاد، فنی و مهندسی ، علوم پایه باشد.")
        return v

    @field_validator("Credit")
    def validate_credit(cls, v):
        if not v.isdigit():
            raise ValueError("تعداد واحد باید عدد باشد.")
        credit = int(v)
        if credit not in [1, 2, 3, 4]:
            raise ValueError("تعداد واحد باید عددی بین ۱ تا ۴ باشد.")
        return v

# --------- مدل پایگاه‌داده با SQLModel ---------
class Course(SQLModel, table=True):
    CID: str = Field(primary_key=True)
    CName: str = Field(index=True)
    Department: str
    Credit: str
sqlite_url = "sqlite:////app/univercity.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# ----------------- اپلیکیشن FastAPI -----------------

app = FastAPI(root_path="/api")


@app.on_event("startup")
def on_startup():
    create_db()
@app.post("/students/")
def create_student(student: StudentBase, session: Session = Depends(get_session)):
    db_student = Student(**student.dict())
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student

@app.get("/students/")
def get_students(session: Session = Depends(get_session)):
    return session.exec(select(Student)).all()

@app.get("/students/{student_id}")
def get_student(student_id: str, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}")
def update_student(student_id: str, new_data: StudentBase, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in new_data.dict(exclude_unset=True).items():
        setattr(student, field, value)
    session.commit()
    session.refresh(student)
    return student

@app.delete("/students/{student_id}")
def delete_student(student_id: str, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(student)
    session.commit()
    return {"message": "Student deleted successfully"}
@app.post("/professors/")
def create_professor(professor: ProfessorBase, session: Session = Depends(get_session)):
    db_professor = Professor(**professor.dict())
    session.add(db_professor)
    session.commit()
    session.refresh(db_professor)
    return db_professor

@app.get("/professors/")
def get_professors(session: Session = Depends(get_session)):
    return session.exec(select(Professor)).all()

@app.get("/professors/{professor_id}")
def get_professor(professor_id: str, session: Session = Depends(get_session)):
    professor = session.get(Professor, professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    return professor

@app.put("/professors/{professor_id}")
def update_professor(professor_id: str, new_data: ProfessorBase, session: Session = Depends(get_session)):
    professor = session.get(Professor, professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    for field, value in new_data.dict(exclude_unset=True).items():
        setattr(professor, field, value)
    session.commit()
    session.refresh(professor)
    return professor

@app.delete("/professors/{professor_id}")
def delete_professor(professor_id: str, session: Session = Depends(get_session)):
    professor = session.get(Professor, professor_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    session.delete(professor)
    session.commit()
    return {"message": "Professor deleted successfully"}
@app.post("/courses/")
def create_course(course: CourseBase, session: Session = Depends(get_session)):
    db_course = Course(**course.dict())
    session.add(db_course)
    session.commit()
    session.refresh(db_course)
    return db_course

# READ ALL
@app.get("/courses/")
def get_courses(session: Session = Depends(get_session)):
    return session.exec(select(Course)).all()

# READ ONE
@app.get("/courses/{course_id}")
def get_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

# UPDATE
@app.put("/courses/{course_id}")
def update_course(course_id: int, new_data: CourseBase, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for field, value in new_data.dict(exclude_unset=True).items():
        setattr(course, field, value)
    session.commit()
    session.refresh(course)
    return course

# DELETE
@app.delete("/courses/{course_id}")
def delete_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    session.delete(course)
    session.commit()
    return {"message": "Course deleted successfully"}